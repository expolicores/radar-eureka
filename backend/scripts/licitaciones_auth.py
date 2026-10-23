"""Sesión experimental Playwright; ningún acceso a DB ni lógica comercial."""

import json
import os
import subprocess
from contextlib import suppress
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local" / "spike_licitaciones_info"
ORIGIN = "https://col.licitaciones.info"
ENDPOINT = "/cliente/contratos/get-info/MP?perfiles=1086005"
HEADERS = (
    "Cookie",
    "Origin",
    "Referer",
    "X-Requested-With",
    "Accept",
    "Content-Type",
    "X-CSRF-TOKEN",
    "X-XSRF-TOKEN",
)
REUSABLE = {name.lower() for name in HEADERS if name not in ("Cookie", "Content-Type")}


def local_path(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(LOCAL.resolve()):
        raise ValueError("El estado de sesión debe permanecer en el directorio local del spike.")
    result = subprocess.run(  # noqa: S603
        ["git", "check-ignore", "--quiet", "--", str(path)],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("El archivo de sesión no está ignorado por Git.")
    return path


def write_local(path: Path, payload) -> None:
    path = local_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def safe_location(location: str | None) -> str | None:
    if not location:
        return None
    try:
        parsed = urlsplit(urljoin(ORIGIN, location))
        origin = ORIGIN if parsed.hostname == "col.licitaciones.info" else "[external-origin]"
        public_segments = {"login", "cliente", "auth", "contratos", "iniciar-sesion", "logout"}
        path = "/".join(
            segment if segment.lower() in public_segments else "[redacted]"
            for segment in parsed.path.split("/")
            if segment
        )
        query = urlencode([(key, "[redacted]") for key, _ in parse_qsl(parsed.query)])
        return origin + "/" + path + ("?" + query if query else "")
    except ValueError:
        return "[invalid-location]"


def presence(headers) -> dict[str, bool]:
    lowered = {name.lower() for name in headers}
    return {name: name.lower() in lowered for name in HEADERS}


def compare_headers(browser_headers, script_headers):
    browser, script = presence(browser_headers), presence(script_headers)
    return [
        {"header": name, "browser_200": browser[name], "script": script[name]} for name in HEADERS
    ]


def capture_headers(headers):
    # Cookies quedan exclusivamente en storage_state, nunca en este archivo.
    selected = {key.lower(): value for key, value in headers.items() if key.lower() in REUSABLE}
    selected["origin"] = ORIGIN
    selected["referer"] = ORIGIN + "/cliente/contratos"
    return selected


def http_event(url, method, status, location=None):
    """Solo rutas públicas reconocidas; nunca query, fragment, cuerpos o headers."""
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if host != "licitaciones.info" and not host.endswith(".licitaciones.info"):
        return None
    relevant = any(
        route in parsed.path
        for route in (
            "/cliente/contratos/get-info/MP",
            "/cliente/contratos/get-conteo/MP",
            "/cliente/contratos/get-filtro",
        )
    )
    if not relevant and status is not None and status < 300:
        return None
    public = {
        "cliente",
        "contratos",
        "get-info",
        "get-conteo",
        "get-filtro",
        "MP",
        "login",
        "auth",
        "logout",
    }
    endpoint = "/" + "/".join(
        segment if segment in public else "[redacted]"
        for segment in parsed.path.split("/")
        if segment
    )
    return {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "location": safe_location(location),
    }


def save_authenticated_snapshot(context, headers, browser_headers, stamp):
    """Un estado canónico existente nunca se reemplaza, ni tras una nueva validación."""
    suffix = f".candidate-{stamp}" if (LOCAL / "storage_state.json").exists() else ""
    files = {
        "state": LOCAL / f"storage_state{suffix}.json",
        "headers": LOCAL / f"request_headers{suffix}.json",
        "presence": LOCAL / f"browser_header_presence{suffix}.json",
    }
    if any(path.exists() for path in files.values()):
        raise ValueError("El snapshot ya existe; no se sobrescribe.")
    write_local(files["state"], context.storage_state())
    write_local(files["headers"], headers)
    write_local(files["presence"], presence(browser_headers))
    return {key: str(value) for key, value in files.items()}


def validation_report(response, browser_headers, script_headers):
    valid_json = False
    if response.status == 200 and "json" in response.headers.get("content-type", "").lower():
        with suppress(ValueError):
            valid_json = isinstance(response.json(), (dict, list))
    return {
        "status": response.status,
        "json": valid_json,
        "accepted": response.status == 200 and valid_json,
        "location": safe_location(response.headers.get("location")),
        "redirects_followed": False,
        "headers": compare_headers(browser_headers, script_headers),
    }


def validate_context(context, headers, browser_presence, payload):
    observed = dict(headers)
    observed["content-type"] = "application/json"
    if context.cookies(ORIGIN):
        observed["cookie"] = "managed-by-browser"
    response = context.request.post(
        ORIGIN + ENDPOINT,
        data=payload,
        headers=headers,
        max_redirects=0,
        max_retries=0,
        timeout=20_000,
        fail_on_status_code=False,
    )
    try:
        return validation_report(response, browser_presence, observed)
    finally:
        response.dispose()


class BrowserSession:
    """Interfaz HTTP mínima para el spike, cookies gestionadas por BrowserContext."""

    def __init__(self, state: Path, header_file: Path):
        from playwright.sync_api import sync_playwright

        state, header_file = local_path(state), local_path(header_file)
        if not state.is_file() or not header_file.is_file():
            raise ValueError("Falta sesión Playwright; ejecutar login_licitaciones_info.py.")
        self.headers = capture_headers(json.loads(header_file.read_text(encoding="utf-8")))
        self.manager = sync_playwright().start()
        try:
            self.browser = self.manager.chromium.launch(channel="msedge", headless=True)
            self.context = self.browser.new_context(storage_state=str(state))
        except Exception:
            self.manager.stop()
            raise

    def post(self, path, *, json):
        if not path.startswith("/cliente/contratos/") or path.startswith("//"):
            raise ValueError("Endpoint fuera del alcance del spike.")
        response = self.context.request.post(
            ORIGIN + path,
            data=json,
            headers=self.headers,
            max_redirects=0,
            max_retries=0,
            timeout=20_000,
            fail_on_status_code=False,
        )
        try:
            return httpx.Response(
                response.status,
                content=response.body(),
                headers={
                    key: value
                    for key, value in response.headers.items()
                    if key in ("content-type", "location")
                },
                request=httpx.Request("POST", ORIGIN + path),
            )
        finally:
            response.dispose()

    def close(self):
        self.context.close()
        self.browser.close()
        self.manager.stop()
