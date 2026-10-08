## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Entorno | El equipo no tenía uv ni Python 3.12 (solo 3.14) | Con aprobación del PO: `pip install --user uv`; uv instaló Python 3.12.15 gestionado, sin tocar el Python del sistema |
| 2 | Lint | ruff trataba `alembic` como primera parte por la carpeta `backend/alembic/`, y marcaba `S105` en credenciales falsas de las pruebas | `known-third-party = ["alembic"]` y `S105` ignorado solo en `tests/**` |
| 3 | Config | import-linter exige `include_external_packages` en el nivel superior para prohibir `fastapi`/`starlette` | Se movió al nivel `[tool.importlinter]` |
| 4 | Tests | 5 tests de logs fallaban: el handler JSON se ata a `sys.stdout` al crear la app, antes de que `capsys` capture | El fixture `read_logs` agrega su propio handler con `JsonFormatter` al logger `public_procurement` (formatea al emitir, con el contexto de la solicitud) |
| 5 | Verificación | La primera verificación final falló en `npm ci` (EPERM): seguían vivos dos procesos Vite de la prueba manual de arranque | Se detuvieron esos dos procesos y se repitió la verificación completa: verde |
| 6 | Dependencias | Además de las del plan: `@testing-library/dom` (peer obligatorio de Testing Library) y `@types/node` (tipos de `vite.config.ts`) | Agregadas como devDependencies |

### Completion Notes

- ⚡ Dev-Rápido: scaffold técnico R0. Backend FastAPI (`public_procurement` con `shared/` y `entrypoints/api/`): configuración por ambiente (`DATABASE_URL` obligatoria; `APP_ENV` y `LOG_LEVEL` con defecto), logs JSON con `module`/`event`/`correlation_id`/`request_id`, cabeceras `X-Correlation-ID`/`X-Request-ID` reutilizadas o generadas, `GET /healthz` (200 con BD; 503 *problem details* en español sin ella), 500 *problem details* con traza solo en el log, SQLAlchemy 2 + psycopg 3, Alembic con migración inicial vacía. Frontend React 19 + TS strict + Vite 8 con Vitest, ESLint y Prettier. `docker-compose.yml` con PostgreSQL 16, CI de GitHub Actions y README.
- ✅ Verificado localmente (Python 3.12.15 vía uv, Node 24): ruff, `ruff format`, mypy, `lint-imports` (2 contratos), 30 tests unitarios del backend, ESLint, Prettier, `tsc`, Vitest (1) y build de Vite. Arranque real: el backend levanta con uvicorn y `/healthz` responde 503 *problem details* sin PostgreSQL, devolviendo `X-Correlation-ID`; sin `DATABASE_URL` el arranque falla con «Falta la variable de entorno obligatoria: DATABASE_URL.»; Vite sirve la página en español.
- ⚠️ **No verificado localmente** (sin Docker ni PostgreSQL en este equipo): migración contra PostgreSQL 16 y los 5 tests de integración (`-m integration`); CI de GitHub Actions (el repositorio no tiene remoto). Por decisión del PO quedan para la validación integral en otro entorno.
- 🧪 Cobertura QA: 10/14; pendientes: QA-01 (Alta): test de integración escrito, no ejecutado sin PostgreSQL · QA-02 (Media): ídem · QA-12 (Alta): CI escrito, sin remoto en GitHub para ejecutarlo · QA-11 (Alta): no automatizable, **verificado manualmente** (con un import prohibido temporal, `lint-imports` rompió los 2 contratos; revertido, 2 *kept*). QA-03 y QA-05 tienen cobertura unitaria ejecutada; su variante con PostgreSQL real (integración) queda pendiente.
- 🔍 QA-13: revisión de alcance hecha: no hay dispatcher, CLI, jobs, autenticación, IA, tablas de negocio ni módulos fuera de `shared/` y `entrypoints/api/`.

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Modificado | `.gitignore` | `.env`, cachés de Python, `node_modules/`, `dist/` |
| Creado | `README.md` | Alcance R0, requisitos, arranque local, configuración y comandos de calidad |
| Creado | `docker-compose.yml` | PostgreSQL 16 local |
| Creado | `.github/workflows/ci.yml` | CI backend (uv, Python 3.12, PostgreSQL 16) y frontend (Node 24) |
| Creado | `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version` | Proyecto, dependencias y configuración de ruff, mypy, pytest e import-linter |
| Creado | `backend/.env.example` | `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL` |
| Creado | `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_initial.py` | Alembic con URL de la configuración y revisión inicial vacía |
| Creado | `backend/src/public_procurement/__init__.py`, `py.typed` | Paquete |
| Creado | `backend/src/public_procurement/shared/{__init__,config,correlation,logging,database,problem_details}.py` | Núcleo compartido |
| Creado | `backend/src/public_procurement/entrypoints/__init__.py`, `entrypoints/api/{__init__,app,dependencies,errors,health,middleware}.py` | App FastAPI, `/healthz`, middleware de correlación, errores |
| Creado | `backend/tests/{__init__,builders,conftest,doubles}.py` | `SettingsBuilder`, dobles de BD y de logs, fixtures |
| Creado | `backend/tests/unit/**` (6 archivos de test + `__init__`) | Config, correlación, logging, `/healthz`, errores, `.env.example` |
| Creado | `backend/tests/integration/{__init__,conftest,test_migrations,test_healthz_database}.py` | Migraciones y `/healthz` contra PostgreSQL real |
| Creado | `frontend/package.json`, `package-lock.json`, `index.html`, `vite.config.ts`, `tsconfig*.json`, `eslint.config.js`, `.prettierrc`, `.prettierignore` | Proyecto frontend y herramientas |
| Creado | `frontend/src/{main.tsx,App.tsx,App.test.tsx,vite-env.d.ts,test/setup.ts}` | SPA mínima y su test |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor no reportó hallazgos; no revisó los lockfiles (generados) y descartó por dudosos `user_id` en logs (R0 sin usuarios) y `HealthStatus.status` como `str` (regla recomendada, no obligatoria).

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | bug | Ante un error 500 el log solo guardaba el tipo de excepción y se perdía la traza para diagnosticar | `backend/src/public_procurement/entrypoints/api/errors.py`, `shared/logging.py` | ✅ Aplicado (campo `exception` en el log JSON; test agregado) |
| 2 | limpieza | `/healthz` puede tardar ~6 s sin PostgreSQL cuando el host es `localhost` (el driver intenta IPv6 e IPv4, 3 s cada uno) | `backend/src/public_procurement/shared/database.py` | — No aplicado: depende del host configurado; en producción hay un solo host y el tope es de 3 s. Ajustar el timeout es decisión de despliegue |
| 3 | limpieza | `TestClient` de Starlette con `httpx` emite `StarletteDeprecationWarning` | `backend/tests/conftest.py` | — No aplicado: migrar exige una dependencia nueva (`httpx2`) no aprobada; hoy es solo una advertencia |

Revisar primero: `backend/alembic/versions/0001_initial.py` (migración de esquema, no ejecutada contra PostgreSQL) · `backend/src/public_procurement/shared/config.py` (configuración de entornos) · `.github/workflows/ci.yml` (configuración de CI, no ejecutada)

### Métricas Dev-Rápido

- Tiempo sesión IA: 31 min
- Tareas manuales DoD: 0 min
- Tiempo total: 31 min
