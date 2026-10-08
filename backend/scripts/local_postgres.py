"""PostgreSQL embebido para desarrollo local en equipos sin Docker (solo desarrollo).

Uso (desde backend/):
    uv run --group local-db python scripts/local_postgres.py start   # arranca o reutiliza
    uv run --group local-db python scripts/local_postgres.py status
    uv run --group local-db python scripts/local_postgres.py stop

Los tests de integración usan la base `public_procurement_test` (la URL la imprime `start`).

`start` deja `DATABASE_URL` en `backend/.env` (no se versiona). En los demás entornos se usa
PostgreSQL 16 (docker-compose.yml o gestionado): este script no aplica allí.
Limitación conocida: no trae extensiones contrib (`pg_trgm`, `unaccent`).
"""

import re
import subprocess
import sys
from pathlib import Path

import pgserver  # type: ignore[import-untyped]
import psycopg
from pgserver._commands import POSTGRES_BIN_PATH  # type: ignore[import-untyped]
from psycopg import sql

BACKEND_DIR = Path(__file__).resolve().parents[1]
PGDATA = BACKEND_DIR / ".local" / "pgdata"
ENV_FILE = BACKEND_DIR / ".env"
DATABASE = "public_procurement"
# Base aparte para los tests de integración: hacen downgrade/upgrade y borran los datos.
TEST_DATABASE = "public_procurement_test"


def _write_database_url(url: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    lines = [line for line in lines if not re.match(r"\s*DATABASE_URL\s*=", line)]
    lines.insert(0, f"DATABASE_URL={url}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def start() -> None:
    PGDATA.parent.mkdir(parents=True, exist_ok=True)
    server = pgserver.get_server(PGDATA, cleanup_mode=None)  # sigue corriendo al salir
    # Sin `server.psql`: falla cuando la ruta del proyecto tiene espacios.
    with psycopg.connect(server.get_uri(), autocommit=True) as connection:
        for database in (DATABASE, TEST_DATABASE):
            exists = connection.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
            ).fetchone()
            if exists is None:
                connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    url = server.get_uri(DATABASE).replace("postgresql://", "postgresql+psycopg://", 1)
    test_url = server.get_uri(TEST_DATABASE).replace("postgresql://", "postgresql+psycopg://", 1)
    _write_database_url(url)
    print(f"PostgreSQL embebido listo: {url}")
    print(f"DATABASE_URL escrita en {ENV_FILE}")
    print(f'Tests de integración: DATABASE_URL="{test_url}" uv run pytest -m integration')


def status() -> None:
    pg_ctl = POSTGRES_BIN_PATH / "pg_ctl"
    subprocess.run([str(pg_ctl), "status", "-D", str(PGDATA)], check=False)  # noqa: S603


def stop() -> None:
    pg_ctl = POSTGRES_BIN_PATH / "pg_ctl"
    subprocess.run([str(pg_ctl), "stop", "-D", str(PGDATA), "-m", "fast"], check=False)  # noqa: S603


COMMANDS = {"start": start, "status": status, "stop": stop}

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in COMMANDS:
        print("Uso: local_postgres.py start|status|stop")
        sys.exit(2)
    COMMANDS[command]()
