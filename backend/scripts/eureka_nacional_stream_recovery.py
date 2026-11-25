"""Reanudar PDF rectores de EN-01 con inventario local, sin discovery."""

import argparse
import asyncio
import json
import re
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import eureka_nacional_cdp_stream_lab as lab
import eureka_nacional_en01 as en
import eureka_nacional_manual_import as manual
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from spike_licitaciones_info import SpikeDocument

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.adapters.secop import RETRIEVE_PATH, SecopDownloader, validate_url
from public_procurement.documents.domain.document import AcquisitionError, StoredBinary

LOT_SIZE = 3
DIRECT_CREDITS = 6


def validate_target(document):
    url = document.source_url
    validate_url(url)
    parsed = urlsplit(url)
    if (
        not re.fullmatch(r"[0-9]{1,40}", document.document_id)
        or document.extension != "pdf"
        or parsed.path != RETRIEVE_PATH
        or parsed.fragment
        or parse_qs(parsed.query, keep_blank_values=True) != {"DocumentId": [document.document_id]}
    ):
        raise AcquisitionError("unverified_target", "Destino fuera del alcance de EN-01.")


def direct_worker():
    payload = json.load(sys.stdin)
    document = SpikeDocument(**payload["document"])
    validate_target(document)
    diagnostics = {}
    try:
        stored = SecopDownloader(lab.DEADLINE, en.DOCUMENT_BYTES).download(
            document, LocalBinaryStorage(Path(payload["staging"])), diagnostics=diagnostics
        )
        print(json.dumps({"stored": asdict(stored), "diagnostics": diagnostics}))
    except (AcquisitionError, OSError) as error:
        print(
            json.dumps(
                {"error": getattr(error, "code", type(error).__name__), "diagnostics": diagnostics}
            )
        )


def direct_pdf(document, storage):
    with tempfile.TemporaryDirectory(prefix="en01-direct-") as temporary:
        staging = LocalBinaryStorage(Path(temporary))
        try:
            worker = subprocess.run(  # noqa: S603
                [sys.executable, str(Path(__file__).resolve()), "--direct-worker"],
                input=json.dumps({"document": asdict(document), "staging": str(staging.root)}),
                capture_output=True,
                text=True,
                timeout=lab.DEADLINE,
                check=True,
            )
        except subprocess.TimeoutExpired:
            return None, {"error": "deadline"}
        except subprocess.CalledProcessError:
            return None, {"error": "worker_failed"}
        response = json.loads(worker.stdout)
        metadata = response.pop("stored", None)
        if metadata is None:
            return None, response
        result = StoredBinary(**metadata)
        en.verify_document_type(staging, result, document, en.DOCUMENT_BYTES)
        with staging.open_verified(
            result.storage_path, result.sha256, result.observed_size, en.DOCUMENT_BYTES
        ) as stream:
            stored = storage.store(
                iter(lambda: stream.read(lab.CHUNK), b""),
                original_name="document.pdf",
                content_type="application/pdf",
                expected_size=result.observed_size,
                max_bytes=en.DOCUMENT_BYTES,
            )
        return stored, response


def fallback_eligible(direct):
    trace = direct.get("diagnostics", {})
    return (
        direct.get("error") == "http_error"
        and trace.get("http_status") == 403
        and not trace.get("redirects")
    )


async def stream_pdf(url, result):
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(
            "http://127.0.0.1:9232", timeout=5000, no_defaults=True
        )
        pages = [
            p
            for ctx in browser.contexts
            for p in ctx.pages
            if urlsplit(p.url).scheme == "https"
            and urlsplit(p.url).hostname == "col.licitaciones.info"
            and urlsplit(p.url).path.rstrip("/") == "/cliente/contratos"
        ]
        if len(pages) != 1:
            raise lab.RejectionError("authorized_tab_unavailable")
        source = pages[0]
        async with asyncio.timeout(8):
            control = await browser.new_browser_cdp_session()
            async with source.context.expect_page(timeout=3500) as popup:
                opened = await source.evaluate(
                    """() => window.open('about:blank', '_blank') !== null"""
                )
                if not opened:
                    raise lab.RejectionError("popup_blocked")
            page = await popup.value
        result["tab_opened"] = True
        target_id = None
        chunks = None
        try:
            async with asyncio.timeout(8):
                result["stage"] = "preflight"
                if page.url != "about:blank" or await page.opener() != source:
                    raise lab.RejectionError("target_not_isolated")
                if not await page.evaluate(
                    """() => {
                        const expected = 'https://col.licitaciones.info';
                        return window.opener?.location?.origin === expected && origin === expected;
                    }"""
                ):
                    raise lab.RejectionError("authorized_origin_not_preserved")
                result["authorized_origin_preserved"] = True
                cdp = await source.context.new_cdp_session(page)
                target_id = (await cdp.send("Target.getTargetInfo"))["targetInfo"]["targetId"]
                frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]
                await cdp.send("Network.enable")
                await cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
                await cdp.send("Network.setBypassServiceWorker", {"bypass": True})
                queue = asyncio.Queue()
                cdp.on("Fetch.requestPaused", queue.put_nowait)
                await cdp.send(
                    "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}
                )
                await page.evaluate(
                    """href => {
                    const a=document.createElement('a');
                    a.id='en01-single-link';
                    a.href=href;
                    a.textContent='Documento SECOP';
                    document.body.append(a);
                }""",
                    url,
                )
            result["stage"] = "click"
            started = time.monotonic()
            try:
                async with asyncio.timeout(lab.DEADLINE):
                    await page.locator("#en01-single-link").click(
                        no_wait_after=True, timeout=lab.DEADLINE * 1000
                    )
                    while True:
                        event = await queue.get()
                        data = event["request"]
                        ident = (
                            data["url"] == url
                            and data["method"] == "GET"
                            and event["frameId"] == frame
                        )
                        rid = event["requestId"]
                        if "responseStatusCode" not in event and "responseErrorReason" not in event:
                            if not ident or result["requests_forwarded"]:
                                await cdp.send(
                                    "Fetch.failRequest",
                                    {"requestId": rid, "errorReason": "BlockedByClient"},
                                )
                                continue
                            result["requests_forwarded"] = 1
                            result["stage"] = "waiting_headers"
                            await cdp.send(
                                "Fetch.continueRequest",
                                {"requestId": rid, "interceptResponse": True},
                            )
                            continue
                        if not ident:
                            raise lab.RejectionError("response_identity_mismatch")
                        result["response_intercepted"] = True
                        result["http_status"] = event.get("responseStatusCode")
                        result["stage"] = "headers"
                        length = lab.response_length(event)
                        if not length:
                            raise lab.RejectionError("missing_declared_size")
                        result["declared_bytes"] = length
                        result["stage"] = "body"
                        chunks = await lab.read_stream(cdp, rid, length, result, "live")
                        if time.monotonic() - started >= lab.DEADLINE:
                            chunks = None
                            raise TimeoutError
                        result["body_complete"] = True
                        break
            finally:
                result["acquisition_seconds"] = round(time.monotonic() - started, 3)
        finally:
            cleanup = time.monotonic()
            if target_id is not None:
                result["target_closed"] = await lab.close_target(page, control, target_id)
            else:
                with suppress(PlaywrightError, TimeoutError), asyncio.timeout(lab.CLOSE_TIMEOUT):
                    await page.close()
                result["target_closed"] = page.is_closed()
            result["cleanup_seconds"] = round(time.monotonic() - cleanup, 3)
        return chunks


def recover_pdf(document, storage, marker, trace):
    started = time.monotonic()
    stored, trace["direct"] = direct_pdf(document, storage)
    trace["direct_seconds"] = round(time.monotonic() - started, 3)
    trace["credits"] = DIRECT_CREDITS
    if stored:
        return stored, "urllib"
    if not fallback_eligible(trace["direct"]):
        return None, None
    time.sleep(2.1)
    edge = trace["edge"] = {"stream_bytes": 0, "requests_forwarded": 0}
    with marker.open("x", encoding="utf-8") as lock:
        lock.write(document.document_id + "\n")
    try:
        chunks = asyncio.run(stream_pdf(document.source_url, edge))
        if not all(edge.get(key) for key in ("io_closed", "navigation_abort_ack", "target_closed")):
            raise lab.RejectionError("unverified_close")
        if not next((chunk for chunk in chunks if chunk), b"").startswith(b"%PDF-"):
            raise lab.RejectionError("invalid_pdf_signature")
        stored = storage.store(
            chunks,
            original_name="document.pdf",
            content_type="application/pdf",
            expected_size=edge["stream_bytes"],
            max_bytes=en.DOCUMENT_BYTES,
        )
        en.verify_document_type(storage, stored, document, en.DOCUMENT_BYTES)
        return stored, "edge_cdp_stream"
    except TimeoutError:
        edge["error"] = "deadline"
    except lab.RejectionError as error:
        edge["error"] = str(error)
    except PlaywrightError as error:
        edge.update(error="protocol_error", exception_type=type(error).__name__)
    except (AcquisitionError, OSError) as error:
        edge["error"] = getattr(error, "code", type(error).__name__)
    finally:
        trace["credits"] += edge["requests_forwarded"]
        edge["session_blocked"] = bool(edge.get("tab_opened") and not edge.get("target_closed"))
        if not edge["session_blocked"]:
            marker.unlink()
    return None, None


def saved_or_pending(source, previous, state):
    processes, inventories, _ = manual.archived_inventory(source)
    candidates, plan = {}, []
    for reference, process in processes.items():
        code = process["codigo_proceso"]
        rows = inventories.get(reference, [])
        entries = [row for row in rows if row["role"] == "primary" and row["extension"] == "pdf"]
        status, candidate = "no_unique_archived_pdf", None
        if len(entries) == 1:
            entry = entries[0]
            document = SpikeDocument(
                entry["name"], "pdf", entry.get("url") or "", entry["document_id"]
            )
            try:
                validate_target(document)
            except AcquisitionError:
                status = "unverified_target"
            else:
                if state.cached(document, en.DOCUMENT_BYTES) or any(
                    item.cached(document, en.DOCUMENT_BYTES) for item in previous
                ):
                    status = "already_verified"
                elif state.key(document) in state.receipts:
                    status = "stored_copy_unavailable"
                else:
                    status, candidate = "eligible", document
        if candidate:
            candidates[code] = (reference, candidate, rows)
        plan.append({"process": code, "status": status})
    return candidates, plan


def analyze(reference, document, rows, stored, route, storage, settings):
    entries = []
    for row in rows:
        role = en.document_role(row["name"])
        entry = {
            "document_id": row["document_id"],
            "name": row["name"],
            "role": role,
            "role_hint": en.document_role_hint(row["name"], role),
            "extension": row["extension"],
            "complete": False,
            "status": "not_recovered",
        }
        entries.append(entry)
        if stored and row["document_id"] == document.document_id:
            entry.update(provenance=route, bytes=stored.observed_size, sha256=stored.sha256)
            try:
                en.extract_document(document, stored, storage, settings, entry)
            except (AcquisitionError, OSError, en.spike.SpikeError) as error:
                entry.update(
                    status="extraction_failed",
                    error_code=getattr(error, "code", type(error).__name__),
                )
    result = en.classify_experience(entries, inventory_complete=bool(rows))
    for entry in entries:
        entry.pop("fragments", None)
    return {"process_reference": reference, "documents": entries, **result}


def run_lot(candidates, selected, state, marker, settings):
    ledger_path = state.output / "transfers.json"
    ledger = manual.read_json(ledger_path) if ledger_path.is_file() else {}
    if marker.exists():
        raise ValueError("Cierre sin verificar. Recuperar el estado de Edge antes de continuar.")
    seen = set(ledger)
    success, failed, used = 0, 0, 0
    deadline = time.monotonic() + en.EXPLORATORY_DURATION_SECONDS
    case_path = state.output / "recovery_results.json"
    cases = manual.read_json(case_path) if case_path.is_file() else {}
    for code in selected:
        reference, document, rows = candidates[code]
        key = state.key(document)
        if key in seen:
            continue
        if time.monotonic() + 2 * lab.DEADLINE + en.START_EXTRACTION_MARGIN >= deadline:
            break
        if used:
            time.sleep(2.1)
        trace = ledger[key] = {
            "process": code,
            "document_id": document.document_id,
            "status": "started",
        }
        en.write_json(ledger_path, ledger)
        used += 1
        try:
            stored, route = recover_pdf(document, state.storage, marker, trace)
        except (AcquisitionError, OSError, ValueError) as error:
            trace["error"] = getattr(error, "code", type(error).__name__)
            stored, route = None, None
        if stored:
            state.remember(document, stored)
            success += 1
            trace.update(
                status="verified", mechanism=route, sha256=stored.sha256, bytes=stored.observed_size
            )
            state.failed_processes.clear()
        else:
            failed += 1
            trace["status"] = "failed"
        en.write_json(ledger_path, ledger)
        cases[reference] = analyze(
            reference, document, rows, stored, route, state.storage, settings
        )
        en.write_json(case_path, cases)
        if marker.exists() or (not stored and state.record_failure(reference)):
            break
    print(
        json.dumps(
            {
                "processed": used,
                "verified": success,
                "failed": failed,
                "session_blocked": marker.exists(),
            },
            ensure_ascii=True,
        )
    )
    return 0 if success == len(selected) else 2


def work_path(name):
    if not re.fullmatch(r"en01-[a-z0-9_-]+", name):
        raise ValueError("Predicado de nombre local inválido.")
    path = en.OUTPUT_ROOT / name
    if path.resolve() != path:
        raise ValueError("Directorio fuera del almacenamiento experimental.")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-inventory-from", required=True)
    parser.add_argument("--process", action="append", default=[])
    parser.add_argument(
        "--execute", action="store_true", help="Autorizar ejecución del lote indicado."
    )
    parser.add_argument("--tesseract", default="tesseract")
    args = parser.parse_args(argv)
    if len(args.process) != len(set(args.process)) or len(args.process) > LOT_SIZE:
        parser.error("Seleccionar hasta tres referencias de proceso distintas.")
    if args.execute and not args.process:
        parser.error("--execute requiere una selección explícita mediante --process.")
    try:
        source = work_path(args.resume_inventory_from)
        output = work_path(f"en01-stream_{source.name[5:]}")
        previous = [
            en.DownloadState(path, LocalBinaryStorage(path / "binaries"))
            for receipt in en.OUTPUT_ROOT.glob("en01-*/download_receipts.json")
            if receipt.parent != output
            for path in [work_path(receipt.parent.name)]
        ]
        state = en.DownloadState(output, LocalBinaryStorage(output / "binaries"))
        candidates, plan = saved_or_pending(source, previous, state)
        ledger_path = output / "transfers.json"
        attempted = manual.read_json(ledger_path) if ledger_path.is_file() else {}
        for row in plan:
            if (
                row["process"] in candidates
                and state.key(candidates[row["process"]][1]) in attempted
            ):
                row["status"] = "already_attempted"
                del candidates[row["process"]]
        print(json.dumps({"archive": source.name, "plan": plan}, ensure_ascii=True))
        if not args.execute:
            return 0
        if any(code not in candidates for code in args.process):
            raise ValueError("La selección incluye un proceso sin rector elegible.")
        output.mkdir(exist_ok=True)
        with manual.exclusive_import(output):
            state = en.DownloadState(output, state.storage)
            settings = en.settings_for_run(output, args.tesseract, None)
            marker = en.OUTPUT_ROOT / "cdp-stream-live-uncertain.lock"
            return run_lot(candidates, args.process, state, marker, settings)
    except (AcquisitionError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"EN-01 recuperacion: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--direct-worker"]:
        direct_worker()
    else:
        raise SystemExit(main())
