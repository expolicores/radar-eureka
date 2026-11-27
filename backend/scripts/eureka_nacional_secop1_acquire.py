"""EN-01 SECOP I stage 2: batch acquisition of the queued governing PDFs.

One manual login in a disposable context of the dedicated Edge, the passive preflight, one
operator confirmation bound to the batch digest, and at most `max_posts` POSTs: one per queued
document, each with its own exclusive attempt record, bounded streaming and receipt.
No retries, no feed, no inventory, no native downloads. Never calls browser.close().
"""

import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs

from eureka_nacional_cdp_stream import DEADLINE, DOCUMENT_BYTES, MARKER_NAME, RejectionError
from eureka_nacional_secop1_flow import RECEIPTS_FILE, load_queue, run_dir_name
from eureka_nacional_secop1_pdf import read_secop1_pdf
from eureka_nacional_secop1_preflight import (
    LANDING,
    PassivePreflight,
    closure_record,
    dedicated_browser_checks,
    is_contracts_url,
    is_provider,
    marker_release_allowed,
    read_closure,
)

CDP = "http://127.0.0.1:9232"
PORT = 9232
PROFILE_DIR = Path.home() / "AppData" / "Local" / "EurekaNacional" / "EdgeCDP"
VERDOCUMENTO = "https://www.contratos.gov.co/consultas/VerDocumento"
WORKDIR = "secop1_acquisition"
ATTEMPTS_DIR = "secop1_attempts"
CONSECUTIVE_FAILURE_LIMIT = 2
OPERATOR_FLAGS = ("operator-ready.flag", "stop.flag", "confirmed-batch.flag")
PROVIDER_HOSTS = re.compile(r"^https?://(?:[A-Za-z0-9-]+\.)*licitaciones\.info(?::\d+)?/")
OFFICIAL_HOSTS = re.compile(
    r"^https?://(?:[A-Za-z0-9-]+\.)*(?:contratos\.gov\.co|secop\.gov\.co)(?::\d+)?/"
)
FORM = """({target, ruta}) => {
   const f = document.createElement('form');
   f.method = 'POST'; f.action = target; f.target = '_self';
   const i = document.createElement('input'); i.type = 'hidden'; i.name = 'ruta'; i.value = ruta;
   f.append(i); document.body.append(f); setTimeout(() => f.submit(), 0);
}"""
PAGE_STATE = r"""() => ({url: location.href,
  password_field: !!document.querySelector('input[type=password]'),
  client: typeof window.axios?.request === 'function',
  download_control: typeof window.openDocumentoSecop1 === 'function',
  ready_state: document.readyState,
  text: (document.body?.innerText || '').slice(0, 20000)})"""


class UncertainCloseError(Exception):
    """A popup or stream could not be proven closed: the whole batch must stop."""


def now_iso():
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_json_atomic(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


# ---------------------------------------------------------------- attempts and receipts


def attempt_path(run, document_id):
    digest = hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:32]
    return run / ATTEMPTS_DIR / f"{digest}.json"


def reserve_attempt(run, item, batch_sha256):
    """Exclusive record created before any POST; an existing record forbids a new attempt."""
    path = attempt_path(run, item["document_id"])
    path.parent.mkdir(exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(
                {
                    "document_id": item["document_id"],
                    "process_reference": item["process_reference"],
                    "batch_sha256": batch_sha256,
                    "state": "reserved",
                    "reserved_at": now_iso(),
                },
                handle,
            )
    except FileExistsError:
        return None
    return path


def finish_attempt(path, outcome):
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(state="finished", finished_at=now_iso(), **outcome)
    write_json_atomic(path, record)


def plan_batch(queue, run):
    """Pending items within the confirmed maximum; recorded attempts are never repeated."""
    recorded = [i for i in queue["items"] if attempt_path(run, i["document_id"]).exists()]
    allowed = max(0, queue["max_posts"] - len(recorded))
    pending = [i for i in queue["items"] if i not in recorded]
    return pending[:allowed], len(recorded)


def confirmation_valid(path, queue):
    try:
        return path.read_text(encoding="utf-8").strip() == queue["batch_sha256"]
    except OSError:
        return False


def write_receipt(run, item, outcome):
    """Same record shape the runner's DownloadState reads."""
    path = run / RECEIPTS_FILE
    receipts = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    key = f"{item['document_id']}:{item['extension']}"
    if key in receipts:
        raise RejectionError("receipt_already_present")
    receipts[key] = {
        "storage_path": outcome["storage_path"],
        "sha256": outcome["sha256"],
        "observed_size": outcome["received_bytes"],
        "content_type": "application/pdf",
    }
    write_json_atomic(path, receipts)


def store_pdf(storage, pdf, trace):
    """Written only after acceptance; removed if the stored copy does not match."""
    staged = storage.store(
        [pdf],
        original_name="secop1.pdf",
        content_type="application/pdf",
        expected_size=trace["received_bytes"],
        max_bytes=DOCUMENT_BYTES,
    )
    try:
        if staged.sha256 != trace["sha256"] or staged.observed_size != trace["received_bytes"]:
            raise RejectionError("staged_hash_mismatch")
        with storage.open_verified(
            staged.storage_path, staged.sha256, staged.observed_size, DOCUMENT_BYTES
        ) as stream:
            if stream.read(5) != b"%PDF-":
                raise RejectionError("invalid_pdf_signature")
    except Exception:
        (storage.root / staged.storage_path).unlink(missing_ok=True)
        raise
    return staged


# ---------------------------------------------------------------- one document


async def acquire_one(guard, item, storage, *, target=VERDOCUMENTO):
    """Single prearmed POST for one queued document. Returns (outcome, pdf_or_None).

    Raises UncertainCloseError when the popup cannot be proven closed.
    """
    trace = {"stream_bytes": 0, "io_closed": False, "navigation_abort_ack": False}
    route = item["relative_path"]
    popup = await guard.open_blank()
    queue = asyncio.Queue()
    cdp, frame = await guard.prepare(popup, queue.put_nowait)
    await cdp.send("Network.enable")
    await cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
    await cdp.send("Network.setBypassServiceWorker", {"bypass": True})
    started = time.monotonic()
    outcome = {"posts_forwarded": 0, "http_status": None}
    pdf = None
    try:
        async with asyncio.timeout(DEADLINE):
            await popup.evaluate(FORM, {"target": target, "ruta": route})
            request = None
            while True:
                event = await queue.get()
                req = event["request"]
                ident = (
                    req.get("url") == target
                    and req.get("method") == "POST"
                    and event.get("frameId") == frame
                    and event.get("resourceType") == "Document"
                )
                rid = event["requestId"]
                if "responseStatusCode" in event or "responseErrorReason" in event:
                    if not ident or request != rid:
                        raise RejectionError("response_identity_mismatch")
                    outcome["http_status"] = event.get("responseStatusCode")
                    pdf = await read_secop1_pdf(cdp, rid, event, trace, started=started)
                    break
                if not ident or request is not None:
                    await cdp.send(
                        "Fetch.failRequest", {"requestId": rid, "errorReason": "BlockedByClient"}
                    )
                    raise RejectionError("unexpected_document_request")
                body = req.get("postData", "")
                if len(body) > 4096 or parse_qs(body, strict_parsing=True) != {"ruta": [route]}:
                    raise RejectionError("form_payload_mismatch")
                request = rid
                outcome["posts_forwarded"] = 1
                await cdp.send(
                    "Fetch.continueRequest", {"requestId": rid, "interceptResponse": True}
                )
        staged = store_pdf(storage, pdf, trace)
        outcome.update(
            outcome="stored",
            storage_path=staged.storage_path,
            sha256=staged.sha256,
            received_bytes=staged.observed_size,
            size_origin=trace["size_origin"],
            pdf_signature=True,
            pdf_eof_marker=True,
        )
    except (RejectionError, TimeoutError) as error:
        pdf = None
        outcome.update(
            outcome="rejected",
            reason="acquisition_timeout" if isinstance(error, TimeoutError) else str(error),
        )
    finally:
        outcome["acquisition_seconds"] = round(time.monotonic() - started, 3)
        outcome["stream_bytes"] = trace["stream_bytes"]
        try:
            async with asyncio.timeout(3):
                await popup.close()
        except Exception as error:
            raise UncertainCloseError("popup_close_failed") from error
        if not popup.is_closed():
            raise UncertainCloseError("popup_close_unverified")
    return outcome, pdf


async def run_batch(guard, items, run, storage, batch_sha256, *, target=VERDOCUMENTO, log=None):
    """Sequential batch; stops on two consecutive failures or any uncertain close."""
    report = {"attempted": 0, "stored": 0, "rejected": 0, "skipped_recorded": 0, "items": []}
    consecutive = 0
    for item in items:
        path = reserve_attempt(run, item, batch_sha256)
        if path is None:
            report["skipped_recorded"] += 1
            continue
        report["attempted"] += 1
        try:
            outcome, _pdf = await acquire_one(guard, item, storage, target=target)
        except UncertainCloseError as error:
            finish_attempt(path, {"outcome": "uncertain_close", "reason": str(error)})
            report["items"].append({"document_id": item["document_id"], "outcome": "uncertain"})
            report["stop_reason"] = "uncertain_close"
            raise
        except Exception as error:
            # Unexpected state before or around the POST: record it and stop the batch.
            finish_attempt(path, {"outcome": "error", "reason": type(error).__name__})
            report["stop_reason"] = "unexpected_error"
            raise
        if outcome["outcome"] == "stored":
            write_receipt(run, item, outcome)
            report["stored"] += 1
            consecutive = 0
        else:
            report["rejected"] += 1
            consecutive += 1
        finish_attempt(path, outcome)
        report["items"].append({"document_id": item["document_id"], **outcome})
        if log:
            log()
        if consecutive >= CONSECUTIVE_FAILURE_LIMIT:
            report["stop_reason"] = "consecutive_failures"
            break
    report.setdefault("stop_reason", "batch_complete")
    return report


# ---------------------------------------------------------------- live worker


def listener_info():
    script = (
        f"$c=Get-NetTCPConnection -State Listen -LocalPort {PORT} -ErrorAction Stop;"
        "$o=@($c|Select-Object -ExpandProperty OwningProcess -Unique);"
        '$p=Get-CimInstance Win32_Process -Filter "ProcessId=$($o[0])";'
        "@{owners=$o.Count;addresses=@($c.LocalAddress);name=$p.Name;command_line=$p.CommandLine}"
        "|ConvertTo-Json -Compress"
    )
    out = subprocess.run(  # noqa: S603 -- fixed local OS query, no external input
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    info = json.loads(out.stdout)
    if not isinstance(info.get("addresses"), list):
        info["addresses"] = [info.get("addresses")]
    return info


async def worker(run, marker, profile_id_resolver):
    from eureka_nacional_secop1_popup import Secop1PopupGuard
    from playwright.async_api import async_playwright

    from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

    work = run / WORKDIR
    trace_path, closure = work / "result.json", work / "closure.json"
    trace = {"stage": "start", "posts_forwarded": 0, "inventory_requests": 0}
    state = {"marker_owned": False, "context_closed": False, "disconnected": False}

    def log():
        write_json_atomic(trace_path, trace)

    try:
        queue = load_queue(run)
        items, recorded = plan_batch(queue, run)
        trace.update(batch_sha256=queue["batch_sha256"], planned=len(items), recorded=recorded)
        if not items:
            trace.update(stage="aborted", reason="nothing_to_acquire")
            return
        try:
            preflight = PassivePreflight(expected_profile_id=profile_id_resolver())
        except Exception as error:
            trace.update(
                stage="aborted", reason="profile_id_unavailable", error_type=type(error).__name__
            )
            return
        ok, checks = dedicated_browser_checks(listener_info(), port=PORT, profile_dir=PROFILE_DIR)
        trace["dedicated_browser"] = checks
        if not ok:
            trace.update(stage="aborted", reason="not_dedicated_browser")
            return
        storage = LocalBinaryStorage(run / "binaries")
        async with async_playwright() as playwright:
            guard = Secop1PopupGuard(marker)
            aborted = set()
            browser = await playwright.chromium.connect_over_cdp(
                CDP, timeout=5000, no_defaults=True
            )
            habitual = [p for c in browser.contexts for p in c.pages]
            try:
                source = await guard.start(browser)
                context = guard.context

                async def restrict(route):
                    request = route.request
                    body = (
                        request.post_data
                        if request.method == "POST" and is_provider(request.url)
                        else None
                    )
                    decision = preflight.observe_request(request.url, body)
                    del body
                    if decision != "allowed":
                        aborted.add(request)
                        return await route.abort("blockedbyclient")
                    return await route.continue_()

                def on_response(response):
                    if is_provider(response.url):
                        preflight.observe_response(
                            response.url,
                            method=response.request.method,
                            resource_type=response.request.resource_type,
                            status=response.status,
                            json="json" in response.headers.get("content-type", ""),
                        )

                def on_failed(request):
                    if request.resource_type in ("document", "xhr", "fetch"):
                        preflight.observe_failure(request.url, blocked_by_us=request in aborted)

                await context.route(PROVIDER_HOSTS, restrict)
                await context.route(OFFICIAL_HOSTS, restrict)
                context.on("response", on_response)
                context.on("requestfailed", on_failed)
                preflight.record_own_navigation(LANDING)
                try:
                    await source.goto(LANDING, wait_until="domcontentloaded", timeout=20000)
                except Exception as error:
                    trace["landing_navigation_error"] = type(error).__name__
                trace.update(
                    stage="awaiting_manual_login",
                    native_downloads_denied=guard.native_downloads_denied,
                )
                log()
                print("manual_login_window_ready=true; posts=0", flush=True)
                async with asyncio.timeout(1800):
                    while not (work / "operator-ready.flag").is_file():
                        if (work / "stop.flag").is_file():
                            trace["stage"] = "manual_login_stopped"
                            return
                        await asyncio.sleep(0.5)
                await asyncio.sleep(3)
                tabs = [p for p in context.pages if not p.is_closed() and is_contracts_url(p.url)]
                if len(tabs) == 1:
                    async with asyncio.timeout(5):
                        preflight.observe_page(await tabs[0].evaluate(PAGE_STATE))
                verdict = preflight.verdict()
                if len(tabs) != 1:
                    verdict["ready_for_acquisition"] = False
                    verdict["reasons"].append("contracts_tab_missing_or_ambiguous")
                write_json_atomic(work / "preflight.json", verdict)
                trace.update(stage="preflight_done", preflight=verdict)
                if not verdict["ready_for_acquisition"]:
                    trace["reason"] = "preflight_not_ready"
                    return
                if not confirmation_valid(work / "confirmed-batch.flag", queue):
                    trace["reason"] = "batch_confirmation_missing_or_mismatch"
                    return
                await context.unroute(OFFICIAL_HOSTS, restrict)
                guard.source = tabs[0]
                trace["stage"] = "batch"
                report = await run_batch(guard, items, run, storage, queue["batch_sha256"], log=log)
                trace.update(
                    stage="batch_done",
                    batch=report,
                    posts_forwarded=sum(i.get("posts_forwarded", 0) for i in report["items"]),
                )
            except UncertainCloseError as error:
                trace.update(reason="uncertain_close", error_code=str(error))
            except Exception as error:
                trace["error_type"] = type(error).__name__
                if code := getattr(error, "code", None):
                    trace["error_code"] = code
            finally:
                state["marker_owned"] = guard._owns_marker is True
                if guard.context is not None:
                    state["context_closed"] = await guard.close() is True
                trace["context_closed"] = state["context_closed"]
                trace["habitual_pages_untouched"] = all(not p.is_closed() for p in habitual)
                log()
        state["disconnected"] = True
    finally:
        evidence = closure_record(**state)
        for name in OPERATOR_FLAGS:
            (work / name).unlink(missing_ok=True)
        trace["closure"] = evidence
        log()
        write_json_atomic(closure, evidence)


def main(argv=None):
    import argparse

    from public_procurement.licitaciones_cdp.configuration import resolve_profile_id

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="Corrida de la etapa 1 (en01-...).")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2] / ".local" / "eureka-nacional-spike"
    run = root / run_dir_name(args.run)
    if run.resolve() != run or not (run / "secop1_queue.json").is_file():
        print("EN-01 SECOP I: corrida o cola inexistente.")
        return 1
    marker = root / MARKER_NAME
    work = run / WORKDIR
    work.mkdir(exist_ok=True)
    if args.worker:
        asyncio.run(worker(run, marker, resolve_profile_id))
        return 0
    queue = load_queue(run)
    items, recorded = plan_batch(queue, run)
    print(
        json.dumps(
            {
                "batch_sha256": queue["batch_sha256"],
                "planned": len(items),
                "recorded": recorded,
                "documents": [[i["constancia"], i["name"]] for i in items],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    # Stale evidence from an earlier invocation must never authorize a release.
    (work / "closure.json").unlink(missing_ok=True)
    result = subprocess.run(  # noqa: S603 -- this script, validated run name
        [sys.executable, str(Path(__file__).resolve()), args.run, "--worker"], check=False
    )
    marker_text = marker.read_text(encoding="utf-8") if marker.is_file() else None
    released = marker_text is not None and marker_release_allowed(
        read_closure(work / "closure.json"),
        worker_exit_code=result.returncode,
        marker_text=marker_text,
    )
    if released:
        marker.unlink()
    trace_path = work / "result.json"
    if trace_path.is_file():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        trace.update(
            worker_exited=True,
            worker_exit_code=result.returncode,
            marker_released=released,
            session_blocked=marker.exists(),
        )
        write_json_atomic(trace_path, trace)
        print(json.dumps(trace, ensure_ascii=False), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
