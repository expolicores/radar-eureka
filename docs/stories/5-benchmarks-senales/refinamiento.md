## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: Benchmarks simulados y generación de señales

**Arquitectura:** dos módulos nuevos del monolito: `market` (observaciones retail, esquema `market`, puerto `RetailObservationSource`) y `comparison` (benchmarks, señales y confianza, esquema `comparison`). `comparison` lee compras por `ingestion.services` y observaciones por `market.services`; `exploration` lee resultados por `comparison.services`. Núcleo determinístico en `comparison/domain`, sin I/O.
**Feature análoga:** módulo `ingestion` (HU #2/#3, 2026-10-07): puerto + adaptador seed + repositorio + unidad de trabajo + servicio + migración + CLI. Candidatas descartadas por más antiguas: ninguna.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Configuración analítica | `AnalysisConfig` inmutable en el dominio con id `analitica-v1` y los valores iniciales del PRD; cada resultado guarda `config_version_id` | HU-101 en versión mínima; P-01…P-04 |
| «Muestra suficiente y homogénea» | ≥ 10 comparables y RIC/mediana ≤ 0,5 (parámetros de la configuración) | FR-063 no la cuantifica; valores provisionales, recalibrables |
| Precios bajos | Por debajo de Q1 − 1,5 × RIC (regla IQR) o de 50 % de la mediana (regla porcentual) → `quality_review_low_price` | P-04 |
| Cuartiles | Interpolación lineal (`(n − 1) · q`), en `Decimal`; referencias guardadas como COP enteros redondeados | Reproduce el mockup; estándar: nada de `float` |
| Persistencia | `comparison.comparison_run`, `comparison.item_comparison` (solo inserción, `is_current`), `comparison.item_comparable` y `comparison.item_market_observation` (vínculos) | ADR-012, FR-058 |
| Vigencia | Al cerrar un recálculo se marca `is_current = false` en los anteriores (metadato de versión, no valor de negocio) dentro de la misma transacción | Patrón `version/is_current` del estándar |
| Mercado simulado | `market.observation` de solo inserción; seed determinístico por perfil de TV y tienda («Alkosto (simulado)», «Falabella (simulado)»), cada ~12 días con huecos, ~5 % vendedor tercero y ~5 % con condición especial (que se descartan) | FR-042…FR-046, FR-053 |
| Lectura masiva | `PurchaseQueryService.all_purchases()` y `MarketQueryService.all_observations()` (volumen del MVP: ~1.300 compras, ~3.000 observaciones) | Sencillo y suficiente; se optimiza al crecer |
| Código de señal | Calculado en el dominio a partir de la compra (ver historia) | Estable entre recálculos |
| Exploración | Estados `with_signal`, `compared_no_signal`, `insufficient_comparables` y filtro `has_signal` (los ids salen de `comparison.services` y se pasan como criterio a `ingestion`) | Escenario 7 |
| Disparo | CLI `recalculate-signals`; `load-seed` carga compras, mercado y recalcula | ADR-008; el job del worker llega después |

**Pasos**
1. Módulo `market` (dominio, puerto, seed, repositorio, servicio, migración).
2. Dominio de `comparison` (configuración, selección, estadísticos, regla, B2, confianza, código).
3. Persistencia y servicio de `comparison` (recálculo y consultas de resultados vigentes) + migración.
4. Integración en `exploration` (estados y filtro) y en `ingestion` (lectura masiva, filtro por ids).
5. CLI, contratos import-linter, frontend (insignias y filtro «Con señal»).
6. Tests unitarios del dominio (QA-01…QA-09, QA-12), integración (QA-10, QA-11) y frontend.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| Patrón de `ingestion` (puerto, seed, `SqlUnitOfWork`, servicio, `build_*`) | Se replica | Feature análoga |
| `ingestion.services` (`PurchaseQueryService`, tipos) | Se reutiliza y se extiende (`all_purchases`, `purchase_ids`/`exclude_purchase_ids` en criterios) | Única puerta de entrada |
| `shared/persistence.Base`, `create_session_factory` | Se reutiliza | Tablas y sesiones |
| `ingestion/adapters/seed_data.TV_PROFILES` | **No** se importa desde `market` (frontera entre módulos): el seed de mercado define sus propios perfiles de precio | Los módulos solo comparten por `services`; los valores de referencia del mercado son otra fuente |
| `exploration/domain/analysis` | Se extiende (`SignalState`) | Estados nuevos |
| `tests/integration/conftest.load_seed` | Se extiende (mercado + recálculo) | Mismo flujo que la CLI |
| `frontend/.../AnalysisStatusBadge`, `ExploreFilters` | Se extienden | Insignias y filtro nuevos |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Dominio puro, sin ORM ni I/O; cálculos que reciben la versión de configuración en lugar de leer un global | §2 Estructura de Funciones, §4 | `comparison/domain` |
| `Decimal` para intermedios, COP `int`, nunca `float` | §2 | Estadísticos, desviaciones, confianza |
| Falta de información = estado explícito (`Deviation.undetermined`, `insufficient_comparables`…) | §3 | Resultados |
| Solo inserción + `config_version_id` + `is_current` | §4 Reglas transversales | `item_comparison` |
| Nunca asumir IVA 19 %; comparar solo en la misma base | §3, §4 | Selección |
| Textos sin «sobreprecio», «corrupción», «fraude», «hallazgo fiscal» | §4 | Código, comentarios y UI |
| Desde otro módulo solo `<module>.services`; contratos import-linter | §2, §4 | `comparison`, `market`, `exploration` |
| Dependencias externas por puertos (`RetailObservationSource`) | §4 | `market` |
| Enums `StrEnum` | Patrones | Resultados, estados B2, niveles |
| README por módulo | §1 | `market`, `comparison` |
| pytest + builders + 3A; PostgreSQL real en integración | §6 | Tests |

### Tareas de Implementación

#### Fase 1 — Mercado
- [ ] **T1: Módulo `market`** — `market/{__init__,README.md,ports,repositories,unit_of_work,services}.py`, `market/domain/{__init__,observation}.py`, `market/adapters/{__init__,seed}.py`, `alembic/versions/0003_market_schema.py`

#### Fase 2 — Comparación
- [ ] **T2: Dominio** — `comparison/domain/{__init__,config,statistics,benchmarks,confidence,signal_code,evaluation}.py`
- [ ] **T3: Persistencia y servicio** — `comparison/{__init__,README.md,repositories,unit_of_work,services}.py`, `alembic/versions/0004_comparison_schema.py`, `alembic/env.py`

#### Fase 3 — Integración
- [ ] **T4: Ingestion y exploración** — `ingestion/domain/search.py` y `repositories.py` (`purchase_ids`, `exclude_purchase_ids`, `all_purchases`), `ingestion/services.py`, `exploration/domain/analysis.py`, `exploration/services.py`, `exploration/api.py` (`has_signal`), `entrypoints/api/app.py`
- [ ] **T5: CLI y fronteras** — `entrypoints/cli/__main__.py` (`load-seed` ampliado, `recalculate-signals`), `backend/pyproject.toml` (capas y contratos), `README.md`
- [ ] **T6: Frontend** — `frontend/src/api/{openapi.json,schema.ts}`, `AnalysisStatusBadge.tsx`, `ExploreFilters.tsx`, `ExplorePage.tsx`, tests

#### Fase 4 — Tests
- [ ] **T7: Tests** — `tests/builders.py` (`CandidateBuilder`, `MarketObservationBuilder`), `tests/unit/comparison/*` (QA-01…QA-09, QA-12), `tests/unit/market/test_seed.py`, `tests/integration/test_comparison_recalculation.py` (QA-10, QA-11), `tests/unit/exploration/*` (estados nuevos), frontend
- [ ] **T8: Verificación** — suite completa, `alembic check`, recálculo sobre la base de la demo

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
