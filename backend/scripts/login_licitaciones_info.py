"""Login manual visible y validación get-info solamente; nunca ejecuta el funnel."""

import argparse
import json
import time
from datetime import UTC, datetime
from uuid import uuid4

from licitaciones_auth import (
    ENDPOINT,
    LOCAL,
    ORIGIN,
    capture_headers,
    compare_headers,
    http_event,
    local_path,
    save_authenticated_snapshot,
    validate_context,
    write_local,
)
from spike_licitaciones_info import build_process_payload


def run_visible(playwright, context, browser, payload, minutes, stamp):
    trace = local_path(LOCAL / f"browser-network-{stamp}.jsonl")
    trace.parent.mkdir(parents=True, exist_ok=True)
    pending = []

    def record(data):
        if data is not None:
            with trace.open("a", encoding="utf-8") as file:
                file.write(json.dumps(data, ensure_ascii=True) + "\n")
            print(json.dumps(data, ensure_ascii=True), flush=True)

    def observe(response):
        record(
            http_event(
                response.url,
                response.request.method,
                response.status,
                response.headers.get("location"),
            )
        )
        if (
            response.url.split("?")[0] == ORIGIN + ENDPOINT.split("?")[0]
            and response.request.method == "POST"
            and response.status == 200
            and "json" in response.headers.get("content-type", "").lower()
        ):
            try:
                if isinstance(response.json(), (dict, list)):
                    pending.append(response.request.all_headers())
            except Exception as error:
                record({"event": "response_capture_error", "type": type(error).__name__})

    context.on("response", observe)
    context.on(
        "requestfailed", lambda request: record(http_event(request.url, request.method, None))
    )
    page = context.new_page()
    print(
        "Navegador visible: inicia sesión y navega manualmente. "
        "La ventana permanece abierta incluso después de validar. "
        "Cierra la ventana para terminar; timeout máximo: " + str(minutes) + " minutos.",
        flush=True,
    )
    try:
        page.goto(ORIGIN + "/cliente/contratos#/", timeout=30_000, wait_until="domcontentloaded")
    except Exception as error:
        record(
            {"event": "navigation_error", "type": type(error).__name__, "browser_kept_open": True}
        )
    deadline = time.monotonic() + minutes * 60
    attempted = False
    accepted = False
    while browser.is_connected() and context.pages and time.monotonic() < deadline:
        if pending and not attempted:
            attempted = True  # Un único POST de validación; sin reintentos automáticos.
            browser_names = pending[-1]
            headers = capture_headers(browser_names)
            try:
                report = validate_context(context, headers, browser_names, payload)
                legacy_file = LOCAL / "legacy_auth_diagnostic.json"
                if legacy_file.exists():
                    legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                    names = {key: True for key, value in legacy["header_presence"].items() if value}
                    report["legacy_script_comparison"] = compare_headers(browser_names, names)
                accepted = report["accepted"]
                if accepted:
                    report["snapshot"] = save_authenticated_snapshot(
                        context, headers, browser_names, stamp
                    )
                write_local(LOCAL / f"auth_validation.{stamp}.json", report)
                record({"event": "context_validation", **report, "browser_kept_open": True})
            except Exception as error:
                record(
                    {
                        "event": "validation_error",
                        "type": type(error).__name__,
                        "browser_kept_open": True,
                    }
                )
        try:
            pages = [item for item in context.pages if not item.is_closed()]
            if not pages:
                break
            pages[0].wait_for_timeout(500)
        except Exception as error:
            if not browser.is_connected() or not context.pages:
                break
            record({"event": "page_wait_error", "type": type(error).__name__})
            time.sleep(0.5)
    reason = "timeout" if time.monotonic() >= deadline else "closed_manually"
    record(
        {
            "event": "helper_finished",
            "reason": reason,
            "get_info_captured": bool(pending),
            "context_200_json": accepted,
        }
    )
    return 0 if accepted else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--timeout-minutes", type=int, choices=range(1, 481), default=120)
    args = parser.parse_args()
    state = local_path(LOCAL / "storage_state.json")
    headers_file = local_path(LOCAL / "request_headers.json")
    comparison_file = LOCAL / "browser_header_presence.json"
    ids = (
        (LOCAL.parents[1] / "scripts/.local/licitaciones_boyaca_ids.txt")
        .read_text(
            encoding="utf-8-sig",
        )
        .strip()
    )
    payload = build_process_payload(ids, "refrigerio", 30)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=args.validate_only)
        try:
            if args.validate_only and not all(
                path.exists() for path in (state, headers_file, comparison_file)
            ):
                raise ValueError("Falta completar primero el login manual visible.")
            context = browser.new_context(storage_state=str(state) if state.exists() else None)
            if not args.validate_only:
                return run_visible(
                    playwright, context, browser, payload, args.timeout_minutes, stamp
                )
            if args.validate_only:
                headers = json.loads(headers_file.read_text(encoding="utf-8"))
                browser_presence = json.loads(comparison_file.read_text(encoding="utf-8"))
                browser_names = {key: True for key, value in browser_presence.items() if value}
            report = validate_context(context, headers, browser_names, payload)
            legacy_file = LOCAL / "legacy_auth_diagnostic.json"
            if legacy_file.exists():
                legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                legacy_names = {
                    key: True for key, present in legacy["header_presence"].items() if present
                }
                report["legacy_script_comparison"] = compare_headers(browser_names, legacy_names)
            write_local(LOCAL / f"auth_validation.{stamp}.json", report)
            print(json.dumps(report, ensure_ascii=True), flush=True)
            if report["accepted"]:
                print(
                    "Validado 200 JSON con context.request. No se ejecutó el resto del spike.",
                    flush=True,
                )
            return 0 if report["accepted"] else 1
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Nunca volcar excepciones Playwright: pueden contener headers y trazas HTTP.
        print(
            f"Validación detenida: {type(error).__name__}. "
            "Revisa el login manual y los archivos locales.",
            flush=True,
        )
        raise SystemExit(1) from None
