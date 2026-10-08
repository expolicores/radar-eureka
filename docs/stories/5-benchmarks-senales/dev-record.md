## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Bug | Violación de llave foránea: sin `relationship`, el ORM insertaba los vínculos antes que la comparación | Inserción en dos fases (comparaciones, *flush*, vínculos) |
| 2 | Datos seed | El mercado simulado era tan denso que el Benchmark 2 casi siempre tenía referencia (1.059 de 1.111) | Cadencia de 14–28 días y huecos de 35 % / 65 %: referencia 442, evidencia limitada 624, no disponible 45 |
| 3 | Datos demo | Las observaciones son de solo inserción: la base de demo conservaba las densas | Base local de demo reconstruida (`downgrade base` + `upgrade head` + `load-seed`); es la base local creada en esta sesión |
| 4 | Bug de dominio | Compras con IVA **excluido** quedaban «pendientes de comparación» en la exploración (solo se miraba «indeterminado») | El estado pasa a `vat_incomplete` («IVA no comparable · comparación incompleta») para toda base distinta de IVA incluido; renombrado `vat_undetermined` → `vat_incomplete` en API, SPA y tests |
| 5 | Test | `dict(result.tuples())` falla porque el resultado de SQLAlchemy expone `.keys()` y `dict` lo trata como *mapping* | Comprensión de diccionario |
| 6 | Test | Un builder mutable compartido entre casos parametrizados los contaminaba | Fábrica `_high()` por caso |

### Completion Notes

- ⚡ Dev-Rápido: módulo `market` (observaciones **simuladas** de solo inserción, puerto `RetailObservationSource`, migración `0003`) y módulo `comparison` (configuración `analitica-v1`; comparables equivalentes o del mismo modelo, IVA incluido, ±6 meses ampliable a ±12, mínimo 5; cuartiles con interpolación lineal en `Decimal`; señal por Q3 + 1,5 × RIC con muestra homogénea o por +30 %/+50 % en otro caso; precios bajos a calidad; Benchmark 2 con ±30 días, ≥ 3 observaciones de ≥ 2 tiendas, solo vendedor = tienda y sin condiciones especiales; confianza 100 − penalizaciones; código `SG-<año>-<número>`; resultados versionados de solo inserción con `config_version_id`, `is_current` y vínculo con cada comparable y observación; migración `0004`). La exploración muestra «⚑ Con señal», «✓ Comparado · sin señal», «Comparables insuficientes» y filtra por señal (API `has_signal` y selector en la SPA). CLI: `load-seed` carga compras, mercado y recalcula; `recalculate-signals`.
- ✅ Verificado con PostgreSQL embebido: ruff, mypy (strict en dominio y servicios), 5 contratos import-linter, `alembic check`; **161 tests de backend pasan (1 omitido)**; Vitest 23. Recálculo real: 1.267 ítems en ~5 s → 42 señales (16 alta, 26 media), 1.066 sin señal, 112 sin precio, 38 IVA no comparable, 4 en revisión, 3 precio bajo, 2 comparables insuficientes. Los valores del mockup (Q1 2.630.000, mediana 2.860.000, Q3 3.125.000, umbral 3.867.500, +73,1 %) se reproducen en un test.
- 🧪 Cobertura QA: 12/12.
- 📝 Decisiones autónomas en `refinamiento.md` (muestra homogénea = ≥ 10 y RIC/mediana ≤ 0,5; precio bajo; unidad de trabajo privada en `services.py` de `market` y `comparison` en vez de archivo propio; nombres «(simulado)» se muestran en la UI con el método `simulated`).
- ⚠️ TVEC: la base tributaria real está en validación (INV-01); el seed declara IVA incluido de forma explícita.

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/src/public_procurement/market/**` (9 archivos) | Módulo de mercado |
| Creado | `backend/src/public_procurement/comparison/**` (13 archivos) | Módulo de comparación |
| Creado | `backend/src/public_procurement/shared/text.py` | Normalización de texto (usada por el listado de señales del slice 5) |
| Creado | `backend/alembic/versions/{0003_market_schema,0004_comparison_schema}.py` | Esquemas `market` y `comparison` |
| Modificado | `backend/alembic/env.py` | Metadata de los módulos nuevos |
| Modificado | `backend/src/public_procurement/ingestion/{domain/purchase.py,domain/search.py,repositories.py,services.py}` | `display_reference`, filtros por ids, `all_purchases` |
| Modificado | `backend/src/public_procurement/exploration/{domain/analysis.py,services.py,api.py}` | Estados de comparación y filtro `has_signal` |
| Modificado | `backend/src/public_procurement/entrypoints/cli/__main__.py` | `load-seed` ampliado, `recalculate-signals` |
| Modificado | `backend/pyproject.toml` | Capas y contratos entre módulos |
| Modificado | `backend/tests/{builders.py,integration/conftest.py}` y tests de exploración | Builders de comparación; seed con mercado y recálculo |
| Creado | `backend/tests/unit/comparison/*` (8), `backend/tests/unit/market/*` (2), `backend/tests/integration/test_comparison_recalculation.py` | Tests |
| Modificado | `frontend/src/api/{openapi.json,schema.ts}`, `frontend/src/features/explore/{AnalysisStatusBadge,ExploreFilters,ExplorePage,ExplorePage.test}.tsx` | Insignias y filtro «Con señal» |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosos el `ValueError` de `deviation_pct` con referencia ≤ 0 (invariante), la actualización de `is_current` (metadato permitido) y la mención de términos prohibidos en el README (no es texto al usuario).

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | estandares | `unit_price_cop or 0`: un precio faltante se habría guardado como 0 | `backend/src/public_procurement/comparison/repositories.py` | ✅ Aplicado (sin valor por defecto; los comparables siempre tienen precio y los que no, no se vinculan) |
| 2 | estandares | La precedencia del resultado de la compra no tenía prueba unitaria | `backend/src/public_procurement/comparison/domain/summary.py` | ✅ Aplicado (`test_summary.py`) |
| 3 | estandares | La regla del sufijo `-<línea>` del código no tenía prueba unitaria | `backend/src/public_procurement/comparison/services.py` | ✅ Aplicado (`test_assign_signal_codes.py`) |
| 4 | estandares | `resolution`, `panel`, `source`, `store` como `str` (convención recomendada: enums) | `backend/src/public_procurement/comparison/domain/facts.py` | Parcial: ✅ `source` → `PurchaseSource`; — `resolution`/`panel`/`store` no aplicado: son códigos de catálogos que pertenecen a `ingestion`/`market`; replicarlos como enums en cada módulo duplicaría el catálogo |
| 5 | estandares | Literal suelto `"tvec"` en el código de señal | `backend/src/public_procurement/comparison/domain/signal_code.py` | ✅ Aplicado (`PurchaseSource.TVEC`) |
| 6 | estandares | `resolution`/`panel` como `str` en la observación | `backend/src/public_procurement/market/domain/observation.py` | — No aplicado: mismo motivo del #4 |
| 7 | bug | Compras con IVA excluido quedaban «pendientes» | `backend/src/public_procurement/exploration/services.py` | ✅ Aplicado (ver Debug Log #4) |
| 8 | bug | Dos televisores con especificación incompleta se habrían considerado equivalentes | `backend/src/public_procurement/comparison/domain/benchmarks.py` | ✅ Aplicado (`spec.is_complete`) |

Revisar primero: `backend/src/public_procurement/comparison/domain/evaluation.py` (regla de señal) · `backend/src/public_procurement/comparison/domain/config.py` (parámetros provisionales) · `backend/alembic/versions/0004_comparison_schema.py` (migración)

### Métricas Dev-Rápido

- Tiempo sesión IA: 18 min
- Tareas manuales DoD: 0 min
- Tiempo total: 18 min
