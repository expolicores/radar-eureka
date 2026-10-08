## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: Modelo de compras de televisores y datos seed

**Arquitectura:** primer módulo de dominio del monolito modular: `public_procurement.ingestion` con capas `services → domain → adapters/repositories`, puerto `PublicDataSource` y esquema PostgreSQL propio (`ingestion`).
**Feature análoga:** `backend/src/public_procurement/shared/` y `entrypoints/api/` (HU #1, agregadas 2026-10-07; sin commit todavía) — candidatas descartadas por más antiguas: ninguna. Es el único código del producto. Da la convención de configuración, logging, motor de BD, tests con builders y dobles; no hay todavía un módulo de dominio que replicar, así que la estructura del módulo sigue `coding-standards.md` §1 «Archivos y Directorios».
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`preparacion_lanzada = false`, causa: compuerta cortada, `STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Identidad de la compra | Columnas `id_contrato` (SECOP II) e `identificador_de_la_orden` (TVEC) con su nombre y valor de origen; `UNIQUE(source, id_contrato)` y `UNIQUE(source, identificador_de_la_orden)`; `CHECK` de que solo la columna de su fuente tenga valor | CLAUDE.md: campos SECOP/TVEC sin transformar |
| Clasificación | Por **sustantivo principal** de la descripción: si la primera palabra es de servicio (mantenimiento, instalación…) → servicio; de accesorio (soporte, base, cable…) → accesorio; si menciona televisor/TV → incluido; si no → dudoso | HU Regla 2; evita excluir «Televisor… con soporte incluido» |
| Bitácora | `ingestion.ingestion_run` por fuente con leídos, nuevos, actualizados, estado y fecha de corte | HU-006, Escenario 1 |
| Actualización | Upsert por identidad: compara campos y cuenta `updated`; ítems por `(purchase_id, line_number)`. Las compras no son hechos de solo inserción (ADR-012 aplica a extracciones, señales…) | Escenario 3 |
| Seed | Generador determinístico (`random.Random(20261006)`) + registros fijos del mockup (compra `CO1.PCCNTR.0000142` y sus 14 comparables); ~355 contratos SECOP II y ~930 órdenes TVEC 2023–2026; fecha de corte 2026-10-06 03:10 (Bogotá) | Mockup, HU Escenario 1 |
| `source_url` | Vacío en el seed: un enlace real de SECOP con un identificador ficticio engañaría | No inventar evidencia |
| Carga | `entrypoints/cli` con **Typer** (stack ADR-009) y un solo comando `load-seed` que usa `ingestion.services` | ADR-008: CLI sin SQL directo |
| PostgreSQL local | `backend/scripts/local_postgres.py` (`start`/`stop`/`status`) con `pgserver` en el grupo de dependencias opcional `local-db` (no lo instala CI ni producción); `start` escribe `DATABASE_URL` en `backend/.env` | Decisión PO 2026-10-07 |
| Sesiones | `shared/persistence.py`: `Base` declarativa con convención de nombres y `create_session_factory(engine)`; una transacción por ejecución de ingesta | Reglas transversales |
| Fronteras | Contrato import-linter nuevo: `*.domain` no importa `sqlalchemy`, `fastapi`, `starlette`, `psycopg`, `httpx`; el contrato de capas suma `ingestion` debajo de `entrypoints` | Estándar §4 |

**Pasos**
1. Persistencia compartida (`Base`, sesiones) — componente: `shared/persistence.py` — referencia: `shared/database.py`.
2. Dominio de ingesta (entidades, enums, clasificación, construcción de la compra) — depende de nada — referencia: estándar §2/§3.
3. Puerto `PublicDataSource` + adaptador seed + generador — depende de 2.
4. Repositorio SQLAlchemy + migración `0002_ingestion_schema` — depende de 1, 2 — referencia: `alembic/versions/0001_initial.py`.
5. Servicio `IngestionService.run(source)` — depende de 2, 3, 4.
6. CLI `load-seed` y script de PostgreSQL local — depende de 5.
7. Tests unitarios (clasificación, seed, servicio con repositorio en memoria) e integración (repositorio + migración + carga real, privacidad) — cubre: QA-01…QA-06.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `shared/config.py` (`load_settings`) | Se reutiliza | CLI y script leen `DATABASE_URL` |
| `shared/database.py` (`create_db_engine`) | Se reutiliza | Motor de la CLI y de los tests de integración |
| `shared/logging.py` (`log_event`, `configure_logging`) | Se reutiliza | Eventos `ingestion_run_finished` |
| `tests/integration/conftest.py` (`database_settings`, `database_engine`) | Se reutiliza | Tests de integración del módulo |
| `tests/builders.py` | Se extiende | `SourcePurchaseBuilder`, `SourceItemBuilder` (nuevos, junto al existente) |
| `shared/persistence.py` | Se crea una vez | Lo usarán todos los módulos (ingestion ahora; comparison e investigation después) |
| `InMemoryPurchaseRepository` (test double) | Se crea | Prueba del servicio sin BD; no hay equivalente |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Módulo con `api.py`/`services.py`/`domain/`/`ports.py`/`adapters/`/`repositories.py`/`README.md` (solo los que se usan; `api.py` y `jobs.py` no aplican en este slice) | §1 Archivos y Directorios | T2–T6 |
| Identificadores en inglés; campos de la fuente sin transformar (`id_contrato`, `identificador_de_la_orden`, `proceso_de_compra`) | §1 Nomenclatura | Dominio, tablas |
| `domain/` sin ORM ni I/O; entidades no heredan de modelos SQLAlchemy; el repositorio mapea | §4 | T2, T4 |
| Dependencias externas solo por puertos (`PublicDataSource`) | §4 | T3, T5 |
| Montos COP `int`/`BIGINT`, nunca `float`; `Decimal` solo para cálculos intermedios | §2 | Dominio, seed, tablas |
| Falta de dato = estado explícito (enums `UnitPriceStatus`, `VatBasis`, `ItemClassification`); nunca IVA 19 % por defecto | §3 | Dominio, seed |
| Enums `StrEnum`, un miembro por línea | Patrones de Código | Dominio |
| Fechas `date`; marcas de tiempo con zona, UTC al guardar | §2 | `signed_on`, `cutoff_at`, bitácora |
| Migraciones Alembic compatibles hacia adelante; SQL parametrizado | §4 Reglas transversales | T4 |
| Campos sensibles excluidos no existen en ninguna tabla (documento de persona natural) | §4 Datos L3 | T3, T4, QA-06 |
| CLI usa servicios de aplicación, sin SQL directo | §4 | T6 |
| Logs JSON con `module` y `event`, sin datos L3 | §4 | T5 |
| pytest + Test Data Builder + 3A; `test_<behavior>_when_<condition>`; dobles en memoria para puertos; integración con PostgreSQL real, no SQLite | §6, Convenciones Complementarias | T7 |
| mypy strict en `ingestion.domain.*` y `ingestion.services` | Configuración de Herramientas | T2, T5 |
| Contratos import-linter por módulo (solo `services` desde otro módulo) | §4 | T8 |

### Tareas de Implementación

#### Fase 1 — Base compartida y dominio
- [ ] **T1: Persistencia compartida** — `backend/src/public_procurement/shared/persistence.py` (Base: `shared/database.py`)
- [ ] **T2: Dominio de ingesta** — `ingestion/__init__.py`, `ingestion/README.md`, `ingestion/domain/__init__.py`, `ingestion/domain/purchase.py` (enums `Source`, `ItemClassification`, `UnitPriceStatus`, `VatBasis`, `Resolution`, `Panel`; `TvAttributes`, `SourceItem`, `SourcePurchase`, `PurchaseItem`, `Purchase`, `IngestionRunResult`; `build_purchase()`), `ingestion/domain/classification.py` (`classify_item()`)

#### Fase 2 — Fuente seed
- [ ] **T3: Puerto y adaptador seed** — `ingestion/ports.py` (`PublicDataSource`), `ingestion/adapters/__init__.py`, `ingestion/adapters/seed.py` (`SeedPublicDataSource`), `ingestion/adapters/seed_data.py` (generador determinístico + registros fijos del mockup)

#### Fase 3 — Persistencia y servicio
- [ ] **T4: Repositorio y migración** — `ingestion/repositories.py` (modelos `PurchaseRecord`, `PurchaseItemRecord`, `IngestionRunRecord` en el esquema `ingestion`; `SqlPurchaseRepository`), `backend/alembic/versions/0002_ingestion_schema.py`, `backend/alembic/env.py` (metadata de los módulos)
- [ ] **T5: Servicio** — `ingestion/services.py` (`PurchaseRepository` Protocol, `IngestionService.run(source)`, `build_ingestion_service(session_factory)`)

#### Fase 4 — Entrypoints y entorno local
- [ ] **T6: CLI y PostgreSQL local** — `entrypoints/cli/__init__.py`, `entrypoints/cli/__main__.py` (Typer: `load-seed`), `backend/scripts/local_postgres.py`, `backend/pyproject.toml` (Typer; grupo `local-db` con `pgserver`; contratos), `README.md` (arranque con PostgreSQL embebido y carga seed)

#### Fase 5 — Tests y fronteras
- [ ] **T7: Tests** — `tests/builders.py` (builders de fuente), `tests/doubles.py` (`InMemoryPurchaseRepository`, `ListPublicDataSource`), `tests/unit/ingestion/test_classification.py` (QA-03), `tests/unit/ingestion/test_build_purchase.py` (QA-05, QA-06), `tests/unit/ingestion/test_seed_data.py` (QA-01, QA-02, QA-05, QA-06 sobre el dataset), `tests/unit/ingestion/test_ingestion_service.py` (QA-04 con repositorio en memoria), `tests/integration/test_ingestion_repository.py` (QA-01, QA-02, QA-04, QA-06 contra PostgreSQL)
- [ ] **T8: Contratos import-linter** — `backend/pyproject.toml`: capas `entrypoints → ingestion → shared`; `*.domain` sin ORM/web/driver
- [ ] **T9: Verificación** — suite completa con PostgreSQL embebido (incluidos los tests de integración de R0, que por fin se pueden correr aquí) y carga seed real

### Cobertura de `qa.md`

| Caso | Prioridad | Test |
| ---- | --------- | ---- |
| QA-01 | Alta | `test_seed_data.py` + `test_ingestion_repository.py` |
| QA-02 | Alta | `test_seed_data.py` + `test_ingestion_repository.py` |
| QA-03 | Alta | `test_classification.py` |
| QA-04 | Alta | `test_ingestion_service.py` + `test_ingestion_repository.py` |
| QA-05 | Alta | `test_build_purchase.py` + `test_seed_data.py` |
| QA-06 | Alta | `test_build_purchase.py` + `test_ingestion_repository.py` (columnas del esquema) |

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados (migración, configs, tests) | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
