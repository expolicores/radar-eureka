# Seguimiento Compras Públicas

Convierte los datos y documentos públicos de contratación colombiana (SECOP II y TVEC) en señales explicables y trazables que indican qué compras merecen revisión humana. La arquitectura está en [docs/architecture/index.md](docs/architecture/index.md) y los estándares de código en [docs/architecture/coding-standards.md](docs/architecture/coding-standards.md).

## Estado: MVP Beta (demo con datos simulados)

Plataforma navegable que simula el flujo principal del producto: *explorar → detectar señal → revisar comparación → guardar en un caso → continuar la investigación*. Los servicios, la persistencia, los modelos y la API se construyen como producto real; **todo lo externo es simulado** y reemplazable por su adaptador real sin cambiar el dominio:

| Módulo (`backend/src/public_procurement/`) | Qué hace | Fuente en el MVP Beta |
| ------------------------------------------ | -------- | --------------------- |
| `ingestion` | Compras SECOP II / TVEC, ítems clasificados por reglas, bitácora | Seed **ficticio** (puerto `PublicDataSource`) |
| `market` | Observaciones de precio retail (solo inserción) | Observaciones **simuladas** (puerto `RetailObservationSource`) |
| `comparison` | Benchmark 1 y 2, señales que merecen revisión, confianza (configuración `analitica-v1`, resultados versionados) | Determinístico, sin IA |
| `exploration` | Búsqueda, filtros y ficha de la compra | — |
| `investigation` | Casos privados con instantáneas y notas | Usuario de demostración (sin autenticación) |

Otras piezas: `shared/` (configuración, logs JSON, errores RFC 9457, persistencia), `entrypoints/api` (FastAPI, `/healthz`, `/api/v1/...`), `entrypoints/cli` (Typer), `frontend/` (React + TypeScript + Vite, cliente tipado generado desde OpenAPI), `docker-compose.yml` (PostgreSQL 16) y `.github/workflows/ci.yml`.

**Todavía no incluye:** conectores reales (Socrata, retail, documentos), extracción documental, autenticación y roles, dispatcher y cola de jobs, IA (Azure AI Foundry), administración en la UI ni `Dockerfile`.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose
- [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por su cuenta)
- Node.js 24

## Arranque local

```bash
# 1. Base de datos
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m public_procurement.entrypoints.cli load-seed   # datos ficticios + señales
uv run uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload
# http://localhost:8000/healthz · documentación de la API: http://localhost:8000/docs

# 3. Frontend (en otra terminal)
cd frontend
npm install
npm run dev
# http://localhost:5173 (el proxy de Vite lleva /api al backend)
```

### Sin Docker: PostgreSQL embebido (solo desarrollo)

En equipos sin Docker, el paso 1 se reemplaza por un PostgreSQL embebido (`pgserver`, grupo de dependencias `local-db`). `start` crea las bases `public_procurement` y `public_procurement_test` y deja `DATABASE_URL` en `backend/.env`:

```bash
cd backend
uv run --group local-db python scripts/local_postgres.py start
```

No trae extensiones contrib (`pg_trgm`, `unaccent`) y acepta cualquier contraseña (autenticación `trust`): un test de integración se omite por eso. Detenerlo con `scripts/local_postgres.py stop`.

## Recorrido de la demo

1. **Señales** (inicio): indicadores, aviso «una señal no es una conclusión» y lista priorizada (confianza → desviación) con filtros.
2. **Detalle de la señal** (`SG-2026-0142`): Benchmark 1 con distribución y tabla de comparables, Benchmark 2 de mercado, confianza con penalizaciones; «★ Guardar en caso».
3. **Ficha de la compra**: datos clave e ítems con su resultado.
4. **Explorar compras**: búsqueda sin tildes, filtros (fuente, modalidad, departamento, valor, con señal) y estado del análisis.
5. **Mis casos**: instantáneas guardadas y notas.

### Datos de la demo

- `load-seed` carga ~1.280 compras **ficticias** de televisores (2023–2026), observaciones de mercado **simuladas** y recalcula las señales. Se puede relanzar: no duplica (las observaciones son de solo inserción).
- `recalculate-signals` vuelve a calcular con la configuración vigente y deja una nueva versión de los resultados (las anteriores se conservan).
- **Reiniciar la demo desde cero** (borra todos los datos, incluidos los casos): `uv run alembic downgrade base && uv run alembic upgrade head && uv run python -m public_procurement.entrypoints.cli load-seed`.

## Configuración

| Variable | Obligatoria | Por defecto | Descripción |
| -------- | ----------- | ----------- | ----------- |
| `DATABASE_URL` | Sí | — | Conexión a PostgreSQL (`postgresql+psycopg://usuario:clave@host:puerto/base`) |
| `APP_ENV` | No | `local` | Ambiente: `local`, `ci` o `production` |
| `LOG_LEVEL` | No | `INFO` | Nivel de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Los secretos van solo en variables de entorno; `backend/.env` no se versiona.

## Calidad

| Acción | Backend (`backend/`) | Frontend (`frontend/`) |
| ------ | -------------------- | ---------------------- |
| Lint y tipado | `uv run ruff check . && uv run mypy src && uv run lint-imports` | `npm run lint && npm run typecheck` |
| Formato | `uv run ruff format .` | `npm run format` |
| Pruebas unitarias | `uv run pytest -m "not integration"` | `npm test` |
| Pruebas de integración (requiere PostgreSQL; **borran la base**) | `DATABASE_URL=<base de pruebas> uv run pytest -m integration` | — |
| Contrato de la API → cliente TS | `uv run python scripts/export_openapi.py` | `npm run generate:api` |

### Fronteras de importación

`lint-imports` verifica las capas (`entrypoints` → `investigation` → `exploration` → `comparison` → `ingestion | market` → `shared`), que entre módulos solo se use `<module>.services`, que ningún `domain/` importe ORM, framework web ni drivers, y que `shared/` no dependa del framework web.
