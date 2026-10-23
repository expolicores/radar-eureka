"""Open a dedicated Edge profile for manual login; no Playwright launch."""

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from observe_licitaciones_cdp import validate_cdp_url

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / ".local" / "spike_licitaciones_info" / "edge-cdp-profile"
ENDPOINT = "http://127.0.0.1:9222"


def cdp_active():
    try:
        # Ignore proxy configuration for this strictly loopback probe.
        with build_opener(ProxyHandler({})).open(ENDPOINT + "/json/version", timeout=1) as response:
            body = json.loads(response.read(65536))
        websocket = body.get("webSocketDebuggerUrl", "")
        from urllib.parse import urlsplit

        parsed = urlsplit(websocket)
        return bool(
            body.get("Browser")
            and parsed.scheme == "ws"
            and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
            and parsed.port == 9222
        )
    except (URLError, TimeoutError, OSError, ValueError, TypeError):
        return False


def port_in_use():
    with socket.socket() as connection:
        connection.settimeout(1)
        return connection.connect_ex(("127.0.0.1", 9222)) == 0


def find_edge():
    for name in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        root = os.environ.get(name)
        if root:
            candidate = Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(
        "Edge no existe en las rutas habituales de Windows. Instala Edge antes de continuar."
    )


def main():
    validate_cdp_url(ENDPOINT)
    if cdp_active():
        print("CDP ya esta activo en localhost:9222. Se reutiliza; no se abre otra instancia.")
        return 0
    if port_in_use():
        print("El puerto 9222 esta ocupado pero no ofrece CDP valido. No se abre otra instancia.")
        return 1
    try:
        executable = find_edge()
        PROFILE.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(  # noqa: S603 -- fixed args; visible browser explicitly requested
            [
                str(executable),
                "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=9222",
                f"--user-data-dir={PROFILE}",
                "https://licitaciones.info/",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if cdp_active():
                print(
                    "Edge CDP listo en localhost:9222. "
                    "Haz login manual y abre Contratos desde la UI."
                )
                print("El perfil dedicado conserva la sesion entre ejecuciones; no se exporta.")
                return 0
            time.sleep(0.5)
        print(
            "Edge no habilito CDP. Si ese perfil estaba abierto sin debugging, "
            "cierra sus ventanas manualmente y reintenta."
        )
        return 1
    except FileNotFoundError as error:
        print(str(error))
        return 1
    except OSError:
        print("No se pudo abrir Edge con el perfil dedicado.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
