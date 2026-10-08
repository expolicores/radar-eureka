## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: API de exploración y filtros de compras

**Arquitectura:** nuevo módulo `exploration` (solo lectura) por encima de `ingestion`; consume compras **solo por `ingestion.services`**. API REST en `exploration/api.py` montada por la *app factory*.
**Feature análoga:** módulo `ingestion` (HU #2, agregado 2026-10-07; sin commit) para la estructura del módulo, repositorio y servicio; `entrypoints/api/health.py` y `errors.py` (HU #1) para routers y *problem details*. Candidatas descartadas por más antiguas: ninguna.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Lectura entre módulos | `ingestion.services` agrega `PurchaseQueryService` (búsqueda, ficha, opciones) y reexporta los tipos que otros módulos necesitan | Estándar §4: solo `services` desde otro módulo |
| Estado del análisis | En `exploration/domain/analysis.py` con un tipo propio `ItemState` (booleanos), sin importar el dominio de `ingestion` | Dominio sin dependencias de otro módulo; el slice 4 suma el estado de señal |
| Inyección en la API | La raíz de composición (`create_app`) deja `app.state.exploration_service`; el router lo lee con `Depends`. Los tests lo reemplazan por un doble | El módulo no importa `entrypoints` (contrato de capas) |
| Búsqueda sin tildes | `translate(lower(col), 'áéíóúüñ', 'aeiouun')` + `contains(..., autoescape=True)`; texto normalizado con `normalize_text` del dominio de ingesta | Sin `unaccent` en el PostgreSQL embebido; SQL parametrizado |
| Errores de validación | *Handler* de `RequestValidationError` → **400** *problem details* «Solicitud inválida», detalle en español con el parámetro; 404 «Compra no encontrada» | Estándar §3 (400 para solicitudes inválidas) |
| Paginación | `page` ≥ 1, `page_size` 1–100 (25 por defecto); orden estable (`signed_on DESC, id`) | HU Regla |
| Fecha de corte | `max(cutoff_at)` de `ingestion_run`, nula si no hay ingesta | HU-083, Escenario 6 |

**Pasos**
1. Consultas de compras en `ingestion` (repositorio + servicio + criterios en el dominio) — referencia: `ingestion/repositories.py`.
2. Dominio de `exploration` (estado del análisis) — referencia: `ingestion/domain/classification.py`.
3. Servicio de `exploration` (vistas tipadas, *tool-ready*) — referencia: `ingestion/services.py`.
4. API (`exploration/api.py`), *handler* de validación, cableado en `create_app` — referencia: `entrypoints/api/health.py`, `errors.py`.
5. Contratos import-linter — referencia: `pyproject.toml`.
6. Tests unitarios (estado del análisis, API con servicio doble, errores) e integración (búsqueda y filtros en PostgreSQL) — cubre QA-01…QA-09.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `ingestion/domain/classification.normalize_text` | Se reutiliza | Normalizar el texto de búsqueda igual que la clasificación |
| `ingestion/repositories.PurchaseRecord`, `to_domain_purchase` | Se reutilizan | Consultas sobre las mismas tablas, dentro del módulo dueño |
| `shared/persistence.create_session_factory` | Se reutiliza | Sesiones de consulta |
| `entrypoints/api/errors.problem_response` | Se reutiliza | 400 y 404 |
| `shared/problem_details.ProblemDetails` | Se reutiliza | Cuerpos de error |
| `tests/integration/test_ingestion_repository` (`migrated_engine`, `_load_seed`) | Se reutiliza moviendo `migrated_engine` y la carga seed a `tests/integration/conftest.py` | Lo usan los tests de ingesta y de exploración |
| `PurchaseQueryService` | Se crea | No existe lectura de compras |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Desde otro módulo solo se importa `<module>.services`; verificado con import-linter | §2 Organización de Imports, §4 | `exploration` |
| `domain/` sin ORM ni I/O | §4 | `exploration/domain` |
| `api.py` solo entrada/salida; servicios de aplicación como puerta | §1 Archivos y Directorios | `exploration/api.py` |
| Errores RFC 9457 con `title`/`detail` en español: 400, 404; sin trazas | §3 | API |
| Inyección con `Depends` en la API | Patrones de Código | API |
| SQL parametrizado | §4 | Búsqueda |
| Montos COP `int` en las respuestas | §2 | Esquemas de respuesta |
| Enums `StrEnum` para estados y catálogos | Patrones de Código | `AnalysisStatus`, `ValueRange`, `PurchaseSort` |
| Campos del contrato de la API en snake_case; la SPA no los renombra | §1 | Esquemas Pydantic |
| Tests pytest + builders + 3A; integración con PostgreSQL real | §6 | Tests |
| README obligatorio por módulo | §1 | `exploration/README.md` |

### Tareas de Implementación

#### Fase 1 — Lectura en `ingestion`
- [ ] **T1: Criterios y consultas** — `ingestion/domain/search.py` (`ValueRange`, `PurchaseSort`, `PurchaseSearchCriteria`, `StoredPurchase`, `PurchasePage`, `PurchaseFilterOptions`), `ingestion/repositories.py` (`SqlPurchaseQueries`), `ingestion/services.py` (`PurchaseQueryService`, `build_purchase_query_service`, reexportes)

#### Fase 2 — Módulo `exploration`
- [ ] **T2: Dominio** — `exploration/__init__.py`, `exploration/README.md`, `exploration/domain/__init__.py`, `exploration/domain/analysis.py` (`AnalysisStatus`, `ItemState`, `derive_analysis_status`)
- [ ] **T3: Servicio** — `exploration/services.py` (`ExplorationService`, vistas `PurchaseSummaryView`, `PurchaseDetailView`, `PurchaseItemView`, `PurchaseListView`, `build_exploration_service`)
- [ ] **T4: API** — `exploration/api.py` (router `/api/v1/purchases`, esquemas Pydantic), `entrypoints/api/errors.py` (400 por validación), `entrypoints/api/app.py` (sesiones, servicio y router)

#### Fase 3 — Fronteras y tests
- [ ] **T5: Contratos** — `backend/pyproject.toml`: capas `entrypoints → exploration → ingestion → shared`; `exploration` no importa internos de `ingestion`
- [ ] **T6: Tests** — `tests/unit/exploration/test_analysis.py` (QA-08), `tests/unit/exploration/test_purchases_api.py` (QA-01, QA-05, QA-06 con servicio doble), `tests/integration/conftest.py` (fixtures compartidas), `tests/integration/test_exploration_queries.py` (QA-01…QA-04, QA-06, QA-07, QA-09 contra PostgreSQL)
- [ ] **T7: Verificación** — suite completa, `alembic check`, prueba manual del API con la base de la demo

### Cobertura de `qa.md`

| Caso | Prioridad | Test |
| ---- | --------- | ---- |
| QA-01 | Alta | `test_exploration_queries.py` + `test_purchases_api.py` |
| QA-02, QA-03 | Alta | `test_exploration_queries.py` |
| QA-04 | Media | `test_exploration_queries.py` |
| QA-05 | Alta | `test_purchases_api.py` |
| QA-06 | Media | `test_exploration_queries.py` + `test_purchases_api.py` |
| QA-07 | Alta | `test_exploration_queries.py` |
| QA-08 | Alta | `test_analysis.py` |
| QA-09 | Media | `test_exploration_queries.py` |

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
