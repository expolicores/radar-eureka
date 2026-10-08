## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: R0 – Scaffold técnico mínimo

**Arquitectura:** monolito modular `public_procurement` (`docs/architecture/index.md`), capas `api → services → domain → adapters/repositories`. En R0 no existe ningún módulo de dominio: solo `shared/` (núcleo transversal sin lógica de negocio) y `entrypoints/api/` (app FastAPI), como dicta el Escenario 5 de la HU.

**Feature análoga:** ninguna. El proyecto es greenfield (único commit `60f9b56 chore: baseline project artifacts`, sin código de producto). Los scripts de los spikes en `docs/propuesta/03-prd/insumos/d*-scripts/` quedan descartados por mandato explícito de `index.md` y `coding-standards.md` §7 («no son referencia de arquitectura ni de estilo»). La referencia de estructura es `coding-standards.md` (§1 «Archivos y Directorios», «Organización de Archivos», «Configuración de Herramientas») y las tareas técnicas LBC-BE-001/002/003/004, LBC-FE-001, PIP-BE-001, PIP-FE-001 y AMB-001 de `docs/propuesta/04-arquitectura/tareas-tecnicas-arquitectura.md`, **recortadas al alcance de R0**.

**Medición:** no existe `docs/cosmic/measurement-strategy.json` → §2c y §7 omitidos (`preparacion_lanzada = false`, causa: compuerta cortada — sin Measurement Strategy aprobada). Se intentará al cierre.

### Archivos relevantes estudiados

- `docs/architecture/index.md` — R0, stack, patrones, `/healthz`, fuera del MVP.
- `docs/architecture/coding-standards.md` — nomenclatura, estructura, errores RFC 9457, logs JSON, secretos, herramientas y configuración literal de ruff/mypy/import-linter/Prettier/ESLint.
- `docs/propuesta/04-arquitectura/tareas-tecnicas-arquitectura.md` — LBC-BE-001…004, LBC-FE-001, PIP-BE-001, PIP-FE-001, AMB-001 (criterios de aceptación de origen).
- `docs/propuesta/04-arquitectura/arquitectura-solucion-comercial.md` — `/healthz` verifica BD (l. 1007), campos del log (l. 1174), ambiente local con Compose (l. 1000).
- `.gitignore` raíz existente (se extiende, no se reemplaza).

### Decisiones técnicas que fija este plan (dentro del alcance de la HU)

| Tema | Decisión |
| ---- | -------- |
| Driver PostgreSQL | `psycopg` 3 (síncrono) con SQLAlchemy 2; URL `postgresql+psycopg://…` |
| Configuración | `pydantic-settings` (`Settings`: `database_url` obligatoria, `app_env` ∈ {`local`,`ci`,`production`} por defecto `local`, `log_level` por defecto `INFO`); lee variables de entorno y, en local, `backend/.env` |
| Validez de `X-Correlation-ID` / `X-Request-ID` | Válido = 1 a 128 caracteres de `[A-Za-z0-9._:-]`. Vacío, más largo o con otros caracteres (espacios, saltos de línea) → se genera un UUID4. Evita inyección en logs |
| Respuesta 200 de `/healthz` | `{"status": "ok", "database": "ok"}` |
| Timeout de la verificación de BD | `connect_timeout=3` s y `SELECT 1`, para que `/healthz` no se cuelgue |
| Logging | `logging` de la stdlib con un *formatter* JSON propio (sin `structlog`): `timestamp`, `level`, `module`, `event`, `correlation_id`, `request_id`, `duration_ms` cuando aplica |
| Errores no controlados | *Handler* global → 500 *problem details* en español sin traza, con las cabeceras de correlación |
| Migración inicial | `0001_initial` sin operaciones (`upgrade`/`downgrade` vacíos) |
| Frontend | Plantilla mínima Vite React + TS strict; una página `App` en español; sin router, sin librería de componentes, sin cliente OpenAPI (llegan con el primer *slice*) |
| Node | 24 (versión local actual; LTS activo) |
| PostgreSQL local | `docker-compose.yml` solo con `postgres:16` (sin MinIO ni imagen de la app) |

**Pasos**

1. Estructura raíz y ambiente local — componente: raíz — referencia: `coding-standards.md` «Organización de Archivos», AMB-001.
2. Proyecto backend (`pyproject.toml`, herramientas) — depende de 1 — referencia: `coding-standards.md` «Configuración de Herramientas».
3. Núcleo `shared/` (config, correlación, logging, *problem details*, base de datos) — depende de 2 — referencia: LBC-BE-002, `coding-standards.md` §3 y reglas transversales.
4. Alembic + migración vacía — depende de 3 (reutiliza `Settings`) — referencia: LBC-BE-003.
5. App FastAPI (`create_app`, middleware de correlación, `/healthz`, *handlers* de error) — depende de 3 — referencia: LBC-BE-004.
6. Tests backend unitarios e integración — depende de 3, 4, 5 — referencia: `coding-standards.md` §6 y «Convenciones Complementarias» — cubre: QA-01…QA-09, QA-14.
7. Frontend Vite + React + TS + Vitest + ESLint + Prettier — depende de 1 — referencia: LBC-FE-001, `coding-standards.md` «Linter»/«Formatter» — cubre: QA-04.
8. CI GitHub Actions (backend con PostgreSQL 16, frontend) — depende de 2–7 — referencia: PIP-BE-001, PIP-FE-001 — cubre: QA-10, QA-12.
9. Verificación local y revisión de alcance — depende de 1–8 — cubre: QA-08, QA-10, QA-11, QA-13.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `.gitignore` raíz | Se reutiliza (se extiende) | Ya existe con entradas del Método Ceiba y `.venv`; se agregan `.env`, `node_modules/`, `dist/`, `__pycache__/`, cachés de herramientas |
| `.github/` | Se reutiliza | Ya existe; se agrega solo `.github/workflows/ci.yml` |
| Código de producto | — | No existe ninguno en el repositorio (greenfield): todo lo demás se crea |
| `shared/config.py` → `Settings`, `get_settings()` | Se crea una vez | Lo usan la app (T7), la base de datos (T6), `alembic/env.py` (T9) y el test de `.env.example` (T13) |
| `shared/correlation.py` (contextvars + validación + generación) | Se crea una vez | Lo usan el middleware (T8), el *formatter* de logs (T5) y los *handlers* de error (T8) |
| `shared/problem_details.py` → `ProblemDetails` | Se crea una vez | Lo usan `/healthz` 503 (T8) y el *handler* global 500 (T8) |
| `shared/database.py` → `create_db_engine()`, `check_database()` | Se crea una vez | Lo usan `/healthz` (T8) y los tests de integración (T12) |
| `tests/builders.py` → `SettingsBuilder` | Se crea una vez | Test Data Builder que usan los tests de config, app y salud (T10–T12) |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Identificadores en inglés; documentación, UI, mensajes y *problem details* en español | §1 Nomenclatura | Todo el código; textos de error, README, página del frontend |
| `.py` en snake_case; componentes `.tsx` en PascalCase; hooks con `use` | §1 Archivos y Directorios | Backend y frontend |
| Paquete `backend/src/public_procurement/`, `entrypoints/{api}/`, `shared/` sin lógica de negocio; `tests/{unit,integration}/` | Organización de Archivos | T2–T12 |
| Orden de imports stdlib → externos → relativos → otro módulo solo `<module>.services` (ruff `I`) | §2 Organización de Imports | Todo el backend |
| Tipado obligatorio en firmas públicas | §2 Estructura de Funciones | Todo el backend |
| Errores de API en *problem details* RFC 9457 con `title`/`detail` en español, sin trazas; 503 = dependencia degradada | §3 Manejo de Errores | `/healthz`, *handler* global (T8) |
| Nunca tragar excepciones (`except Exception: pass`); falta de dato = estado explícito | §3 | `check_database()`, middleware |
| Capas y fronteras verificadas con `import-linter` en CI | §4 Respeto de Capas | T3 (contratos), T15 |
| La API nunca llama a terceros dentro del request (la BD propia sí) | §4 / index.md | `/healthz` solo hace `SELECT 1` a PostgreSQL |
| Migraciones con Alembic, compatibles hacia adelante; SQL parametrizado | §4 Reglas transversales | T9 |
| Logs JSON con `module`, `event`, `correlation_id`, `request_id`; nunca correos ni datos L3; nunca la contraseña de la URL | §4 Reglas transversales | T5, T8 |
| Secretos solo en variables de entorno; nunca en el repositorio | §4 Reglas transversales | `.env.example`, `.gitignore`, CI |
| pytest + Test Data Builder + patrón 3A; nombre `test_<behavior>_when_<condition>`; integración con PostgreSQL real (no SQLite); en CI sin red externa | §6, Convenciones Complementarias | T10–T12 |
| Vitest + Testing Library, patrón 3A; `it(...)` puede ir en español | §6 | T14 |
| ruff (`py312`, línea 100, reglas E,F,W,I,N,UP,B,S,SIM,RUF,DTZ,PT), `ruff format` comillas dobles | Configuración de Herramientas | `pyproject.toml` (T2); `S101` ignorado solo en `tests/` |
| mypy con plugin pydantic, `check_untyped_defs`, strict en `*.domain.*` y `*.services` | Configuración de Herramientas | `pyproject.toml` (T2) |
| `eslint.config.js` con typescript-eslint `recommended-type-checked` + `react-hooks`; `tsconfig` `strict: true`; `.prettierrc` `{printWidth:100, singleQuote:false, trailingComma:"all"}` | Configuración de Herramientas | T14 |
| Comandos: `ruff check . && mypy src && lint-imports`, `pytest`, `npm run lint`, `npm test` | Comandos | `README.md`, CI (T15) |
| Fechas con zona: `datetime` con zona, UTC al guardar | §2 | `timestamp` del log en UTC (regla ruff `DTZ`) |
| **Choque 1:** LBC-BE-001/003 piden 10 módulos y 9 esquemas en la migración inicial → se sigue la HU (R0 sin módulos de dominio, migración vacía) | HU Escenario 5 / decisión PO | T2, T9 |
| **Choque 2:** el comando de build del estándar es `docker build .`, pero el `Dockerfile` no está en el alcance de R0 → build de R0 = `npm run build`; el `Dockerfile` llega con el despliegue | Comandos / HU «No incluye» | T15 |
| **Choque 3:** la arquitectura nombra los campos del log en español (`modulo`, `evento`); prevalece el estándar en inglés (`module`, `event`) | §4 Reglas transversales | T5 |
| **Choque 4:** el estándar lista `prompts/`, `tests/e2e`, `tests/golden`; no se crean (sin consumidor en R0) | Organización de Archivos / HU Escenario 5 | T2 |

### Dependencias nuevas (todas exigidas por el stack de la HU)

- **Backend runtime:** `fastapi`, `uvicorn[standard]`, `pydantic` v2, `pydantic-settings` (LBC-BE-002), `sqlalchemy` 2, `alembic`, `psycopg[binary]` 3 (driver PostgreSQL).
- **Backend dev:** `pytest`, `httpx` (requerido por `TestClient`), `ruff`, `mypy`, `import-linter`.
- **Frontend runtime:** `react`, `react-dom`.
- **Frontend dev:** `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `eslint`, `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals`, `prettier`, `@types/react`, `@types/react-dom`.

### Tareas de Implementación

#### Fase 1 — Raíz y ambiente local
- [x] **T1: Raíz del repositorio** — `docker-compose.yml` (solo `postgres:16`, usuario/clave locales de ejemplo, puerto 5432, volumen nombrado, *healthcheck* `pg_isready`), `.gitignore` (extender), `README.md` (en español: requisitos —Docker, uv, Node 24—, arranque local, comandos de calidad, alcance R0 y lo que no incluye) (Base: AMB-001, «Organización de Archivos»)

#### Fase 2 — Backend: proyecto y núcleo `shared/`
- [x] **T2: Proyecto backend** — `backend/pyproject.toml` (`requires-python = ">=3.12,<3.13"`, dependencias de arriba, `[dependency-groups] dev`, configuración literal de ruff/mypy del estándar, `[tool.pytest.ini_options]` con marcador `integration`, `[tool.importlinter]`), `backend/.python-version` (`3.12`), `backend/uv.lock`, `backend/.env.example` (`DATABASE_URL`, `APP_ENV`, `LOG_LEVEL` con descripción en español y valores de ejemplo no reales), `backend/src/public_procurement/__init__.py`, `backend/src/public_procurement/py.typed`
- [x] **T3: Contratos de `import-linter`** — `backend/pyproject.toml`: contrato *layers* `public_procurement.entrypoints` → `public_procurement.shared` (shared nunca importa entrypoints) y contrato *forbidden* `public_procurement.shared` no importa `fastapi`/`starlette` (el núcleo no depende del framework web). Los contratos por módulo se agregan con cada módulo (se documenta en el README, sin contratos sin consumidor)
- [x] **T4: Configuración** — `backend/src/public_procurement/shared/config.py`: `AppEnvironment` (StrEnum), `Settings` (pydantic-settings), `MissingConfigurationError` con el mensaje exacto «Falta la variable de entorno obligatoria: DATABASE_URL.» (ausente o vacía), `load_settings()` (cubre: QA-06, QA-07)
- [x] **T5: Correlación y logging** — `shared/correlation.py` (contextvars `correlation_id`/`request_id`, `resolve_identifier(header_value) -> str` con la regla de validez, `CORRELATION_HEADER`/`REQUEST_HEADER`), `shared/logging.py` (`JsonFormatter`, `configure_logging(level)`, `log_event(logger, event, **fields)`; inyecta `correlation_id`/`request_id` desde contextvars; `timestamp` UTC) (cubre: QA-03, QA-09, QA-14)
- [x] **T6: Base de datos** — `shared/database.py`: `create_db_engine(settings)` (`pool_pre_ping`, `connect_timeout=3`), `DatabaseStatus` (StrEnum `ok`/`unavailable`), `check_database(engine) -> DatabaseStatus` (captura solo `sqlalchemy.exc.SQLAlchemyError`, registra `database_unavailable` con el tipo de error, sin la URL ni la contraseña) (cubre: QA-03, QA-05)
- [x] **T7: *Problem details*** — `shared/problem_details.py`: `ProblemDetails` (Pydantic, `type`=`about:blank`, `title`, `status`, `detail`), constante `PROBLEM_JSON_MEDIA_TYPE` = `application/problem+json`

#### Fase 3 — Backend: API y migraciones
- [x] **T8: App FastAPI** — `backend/src/public_procurement/entrypoints/api/app.py` (`create_app(settings: Settings | None = None)`: valida la configuración al construir —falla rápido—, `configure_logging`, crea el *engine* en `app.state`, registra middleware, router y *handlers*; log `app_started` con `app_env`), `entrypoints/api/middleware.py` (`CorrelationMiddleware`: resuelve las dos cabeceras, fija contextvars, las devuelve en toda respuesta incluso de error, log `request_completed` con método, ruta, estado y `duration_ms`), `entrypoints/api/health.py` (`GET /healthz`: 200 `{"status":"ok","database":"ok"}`; 503 *problem details* «Servicio no disponible» / «No fue posible verificar la conexión con la base de datos.»), `entrypoints/api/errors.py` (*handler* global de excepciones no controladas → 500 *problem details* en español, sin traza, con log `unhandled_error`), `entrypoints/api/dependencies.py` (`get_engine` vía `Depends`, sustituible en tests). Arranque local: `uv run uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload` (cubre: QA-03, QA-05, QA-09, QA-14)
- [x] **T9: Alembic** — `backend/alembic.ini`, `backend/alembic/env.py` (URL tomada de `load_settings()`, no de `alembic.ini`; sin `target_metadata` de negocio), `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_initial.py` (revisión vacía) (cubre: QA-01, QA-02)

#### Fase 4 — Backend: tests
- [x] **T10: Builders y fixtures** — `backend/tests/builders.py` (`SettingsBuilder` con `with_database_url`, `with_app_env`, `with_log_level`), `backend/tests/conftest.py` (fixture `client` con `create_app` y `get_engine` sustituido por un doble; captura de logs JSON)
- [x] **T11: Tests unitarios** — `backend/tests/unit/shared/test_config.py` (QA-06 ausente/vacía con mensaje exacto; QA-07 defaults `local`/`INFO`), `tests/unit/shared/test_correlation.py` (QA-09 reutiliza válidos; QA-14 genera si falta, vacío, >128 o con salto de línea; dos generaciones distintas), `tests/unit/shared/test_logging.py` (línea JSON con `module`, `event`, `correlation_id`, `request_id`, `timestamp` UTC), `tests/unit/entrypoints/test_healthz.py` (QA-03 200 con doble de BD ok; QA-05 503 con `application/problem+json`, `title`/`detail` exactos, sin trazas, cabeceras devueltas; QA-09/QA-14 cabeceras en respuesta y log), `tests/unit/entrypoints/test_errors.py` (500 *problem details* sin traza con cabeceras), `tests/unit/test_env_example.py` (QA-08: los campos de `Settings` = las variables de `.env.example`, sin variables de IA, correo ni *storage*)
- [x] **T12: Tests de integración** (marcador `integration`, requieren PostgreSQL real vía `DATABASE_URL`; corren en CI) — `backend/tests/integration/test_migrations.py` (QA-01: `upgrade head` deja una fila en `alembic_version` y ninguna otra tabla; QA-02: segunda ejecución sin cambios), `backend/tests/integration/test_healthz_database.py` (QA-03 200 contra PostgreSQL real; QA-05 503 con el puerto 5499 sin servicio y con contraseña `clave_incorrecta`; el log no contiene la contraseña)

#### Fase 5 — Frontend
- [x] **T13: Proyecto frontend** — `frontend/package.json` (scripts `dev`, `build`, `typecheck`, `lint`, `format`, `format:check`, `test`; `engines.node >=24`), `frontend/package-lock.json`, `frontend/index.html` (`lang="es"`), `frontend/vite.config.ts` (Vitest con `jsdom` y `setupFiles`), `frontend/tsconfig.json` + `tsconfig.app.json` + `tsconfig.node.json` (`strict: true`), `frontend/eslint.config.js` (`recommended-type-checked` + `react-hooks`), `frontend/.prettierrc` (literal del estándar), `frontend/.prettierignore`, `frontend/src/main.tsx`, `frontend/src/App.tsx` (texto en español: «Seguimiento Compras Públicas» y «La aplicación arrancó correctamente.»), `frontend/src/vite-env.d.ts`, `frontend/src/test/setup.ts`
- [x] **T14: Test frontend** — `frontend/src/App.test.tsx` (QA-04: muestra el título y el mensaje en español; patrón 3A)

#### Fase 6 — CI y verificación
- [x] **T15: CI** — `.github/workflows/ci.yml`, disparado en `pull_request` y `push`: job `backend` (`astral-sh/setup-uv`, Python 3.12, *service* `postgres:16` con *healthcheck*, `uv sync --locked`, `ruff check .`, `ruff format --check .`, `mypy src`, `lint-imports`, `alembic upgrade head`, `pytest`), job `frontend` (Node 24, `npm ci`, `lint`, `format:check`, `typecheck`, `test`, `build`). Sin secretos: `DATABASE_URL` del *service container* (cubre: QA-12)
- [x] **T16: Verificación local** — correr todas las verificaciones disponibles en este equipo (QA-10), comprobar manualmente el contrato de `import-linter` con un import temporal prohibido y revertirlo (QA-11) y revisar el diff contra el Escenario 5 (QA-13)

### Cobertura de `qa.md`

| Caso | Prioridad | Test / verificación |
| ---- | --------- | ------------------- |
| QA-01, QA-02 | Alta / Media | `tests/integration/test_migrations.py` (CI) |
| QA-03 | Alta | `tests/unit/entrypoints/test_healthz.py` + `tests/integration/test_healthz_database.py` |
| QA-04 | Alta | `frontend/src/App.test.tsx` |
| QA-05 | Alta | `test_healthz.py` (unidad) + `test_healthz_database.py` (integración) |
| QA-06, QA-07 | Alta / Media | `tests/unit/shared/test_config.py` |
| QA-08 | Media | `tests/unit/test_env_example.py` |
| QA-09, QA-14 | Alta / Media | `test_correlation.py` + `test_healthz.py` |
| QA-10 | Alta | Los comandos de calidad mismos (T16) |
| QA-11 | Alta | **No automatizable como test**: probar que `lint-imports` falla exige introducir código prohibido. Se verifica manualmente en T16 y queda en `dev-record.md` |
| QA-12 | Alta | El propio CI (T15). **Requiere un remoto en GitHub**: hoy el repositorio no tiene `origin`, así que se valida al primer *push* |
| QA-13 | Media | Revisión del diff (T16) |

### Limitaciones de validación local (decisión PO del 2026-10-07)

- Este equipo tiene Python 3.14, sin uv ni Docker. Sin uv no se puede generar `uv.lock` ni crear el entorno 3.12; sin Docker no corren la migración ni los tests de integración.
- Lo que no se pueda ejecutar aquí se valida en CI y queda declarado como **no verificado localmente** en `dev-record.md`, sin darlo por bueno.

### Checklist
☑ Feature análoga: no existe (greenfield, justificado) | ☑ TODOS los artefactos identificados (SQL/migración, configs, CI, tests) | ☑ Respeta arquitectura (sin capas inventadas; solo `shared/` y `entrypoints/api/`) | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
