"""Passive CDP observation of an already authenticated, manually opened tab."""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4


LOCAL = Path(__file__).resolve().parents[1] / ".local" / "spike_licitaciones_info"
CONTRACT_HOSTS = {"col.licitaciones.info", "mcol.licitaciones.info"}


def validate_cdp_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("CDP debe ser un endpoint HTTP localhost con puerto explicito.")
    return value


def is_contracts_tab(url):
    parsed = urlsplit(url)
    return parsed.hostname in CONTRACT_HOSTS and parsed.path.rstrip("/") == "/cliente/contratos"


def is_get_info(url, method):
    parsed = urlsplit(url)
    return (
        parsed.hostname in CONTRACT_HOSTS
        and parsed.path == "/cliente/contratos/get-info/MP"
        and method == "POST"
    )


def summarize(body):
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise ValueError("Respuesta sin contrato count/data reconocido.")
    rows = body["data"]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Filas no reconocidas.")
    fields = ("CodigoProceso", "TextoDepartamento", "Objeto", "FechaPublicacion", "id_fuente_contract", "key_config")
    return {
        "count": body.get("count"),
        "rows_received": len(rows),
        "first_five": [{key: row.get(key) for key in fields} for row in rows[:5]],
        "enriched_fields_present": {
            key: sum(key in row for row in rows)
            for key in ("id_fuente_contract", "key_config")
        },
        "generic_count_warning": str(body.get("count")) == "1337370",
        "requires_manual_comparison": True,
    }


def observe(playwright, endpoint, minutes):
    # Never launch/create a context/page, navigate, request, or export browser state.
    browser = playwright.chromium.connect_over_cdp(endpoint)
    pages = [page for context in browser.contexts for page in context.pages if is_contracts_tab(page.url)]
    if len(pages) != 1:
        raise ValueError("Debe haber exactamente una pestana Contratos abierta; no se navegara automaticamente.")
    page = pages[0]
    output = LOCAL / ("cdp-observe-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=False)
    report = {"mode": "passive_existing_page", "captures": []}

    def save():
        temporary = output / "observation.tmp"
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(output / "observation.json")

    def response_received(response):
        if not is_get_info(response.url, response.request.method):
            return
        capture = {
            "observed_at": datetime.now(UTC).isoformat(),
            "host": urlsplit(response.url).hostname,
            "method": "POST", "path": "/cliente/contratos/get-info/MP",
            "status": response.status,
            "content_type": response.headers.get("content-type", ""),
        }
        report["captures"].append(capture)
        try:
            if response.status == 200 and "json" in capture["content_type"].lower():
                capture["summary"] = summarize(response.json())
            else:
                capture["warning"] = "expected_200_json_not_received"
        except Exception as error:
            capture["error_type"] = type(error).__name__
        save()
        print(json.dumps(capture, ensure_ascii=True), flush=True)

    page.on("response", response_received)
    save()
    print("OUTPUT=" + str(output), flush=True)
    print("Conectado a pestana existente. Observador pasivo: inicia una accion desde la UI para capturar get-info. Ctrl+C desconecta sin cerrar Edge.", flush=True)
    deadline = time.monotonic() + minutes * 60
    try:
        while browser.is_connected() and not page.is_closed() and time.monotonic() < deadline:
            page.wait_for_timeout(250)
    finally:
        page.remove_listener("response", response_received)
        save()
        # Do not browser.close(): this is the user's externally started browser.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--minutes", type=int, default=60)
    args = parser.parse_args()
    endpoint = validate_cdp_url(args.cdp_url)
    if args.minutes <= 0:
        parser.error("--minutes debe ser positivo")
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as playwright:
            observe(playwright, endpoint, args.minutes)
    except KeyboardInterrupt:
        print("Observacion terminada; navegador externo no cerrado.")
    except Exception as error:
        # Connection errors can include sensitive browser internals: do not dump them.
        print("No se pudo observar: " + type(error).__name__ + ". Verifica CDP local y una unica pestana Contratos.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
