"""Exporta el contrato OpenAPI de la API al frontend (fuente del cliente tipado).

Uso (desde backend/): `uv run python scripts/export_openapi.py`
Luego, en frontend/: `npm run generate:api`. No necesita base de datos.
"""

import json
from pathlib import Path

from public_procurement.entrypoints.api.app import create_app
from public_procurement.shared.config import Settings

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "openapi.json"
# URL sin uso: la exportación no abre conexiones.
PLACEHOLDER_URL = "postgresql+psycopg://openapi@localhost:5432/openapi"


def main() -> None:
    app = create_app(Settings(_env_file=None, database_url=PLACEHOLDER_URL))  # type: ignore[call-arg]
    OUTPUT.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OpenAPI exportado en {OUTPUT}")


if __name__ == "__main__":
    main()
