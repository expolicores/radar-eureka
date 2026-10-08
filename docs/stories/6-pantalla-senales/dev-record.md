## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Diseño | Armar la fila de una señal con `or 0` habría ocultado datos corruptos (mismo patrón que marcó el revisor en el slice 4) | `_required()`: una señal sin precio, referencia o confianza lanza un error de integridad |
| 2 | Lint | Aserción de tipo innecesaria en la consulta de señales del frontend | Eliminada |
| 3 | Herramienta | `ruff` no marca líneas largas que terminan en un comentario *pragma* (`# fmt: skip`) | Test reescrito con un *helper*; barrido por caracteres: sin líneas > 100 salvo las que terminan en `noqa`/`type: ignore` |

### Completion Notes

- ⚡ Dev-Rápido: API de señales (`GET /api/v1/signals` con filtros de texto sin tildes, departamento, fuente, confianza y año; orden por prioridad —confianza y luego desviación—, desviación, valor o fecha; paginación; `GET /api/v1/signals/summary` con compras de TV analizadas por fuente, señales por confianza, comparaciones incompletas y sin información en la fuente). Pantalla «Señales que merecen revisión» del mockup como inicio de la demo: aviso de no conclusión, 4 indicadores, filtros en la URL, tabla con código, ítem, entidad, proveedor, precio, mediana, desviación, emparejamiento, confianza (barras + texto) y fecha; estados cargando/vacío/error. `normalize_text` se movió a `shared/text.py` (lo usan `ingestion` y `comparison`).
- ✅ Verificado: ruff, mypy, 5 contratos; **181 tests de backend (1 omitido)** y **28 de Vitest**; ESLint, Prettier, `tsc` y build. API real sobre la demo: 42 señales; 1.267 compras de TV (335 SECOP II, 932 TVEC); 16 alta, 26 media; 40 incompletas; 112 sin información; «san rafael» → `SG-2026-0142`.
- 🧪 Cobertura QA: 9/9 (incluidas pruebas automáticas de términos prohibidos en API y pantalla).
- 📝 Decisión autónoma: filtrado y orden en memoria sobre las señales vigentes (decenas en el MVP), enriquecidas por `ingestion.services`; pasar a SQL o vista materializada cuando crezca.

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/src/public_procurement/shared/text.py` | Normalización compartida |
| Creado | `backend/src/public_procurement/comparison/{domain/signals.py,api.py}` | Lista priorizada y API |
| Modificado | `backend/src/public_procurement/comparison/{repositories,services}.py` | Señales vigentes, conteos, `SignalQueryService` |
| Modificado | `backend/src/public_procurement/ingestion/{repositories,services,domain/classification}.py` | `get_many`, `tv_purchase_counts`, normalización compartida |
| Modificado | `backend/src/public_procurement/entrypoints/api/app.py` | Cableado de señales |
| Modificado | `backend/tests/builders.py`, `backend/tests/integration/test_exploration_queries.py` | `SignalRowBuilder`; import de normalización |
| Creado | `backend/tests/unit/comparison/{test_signal_listing,test_signals_api}.py`, `backend/tests/integration/test_signal_queries.py` | Tests |
| Creado | `frontend/src/components/ConfidenceBadge.tsx`, `frontend/src/features/signals/*` (5), `frontend/src/lib/labels.ts` (movido desde `features/explore`) | Pantalla Señales |
| Modificado | `frontend/src/{App.tsx,App.test.tsx,styles.css,api/client.ts,lib/format.ts,test/api.ts}`, `frontend/src/api/{openapi.json,schema.ts}`, `frontend/src/features/explore/{ExploreFilters,PurchasesTable}.tsx` | Rutas, estilos, tipos, `formatPercent`, *fixtures* |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosos `source`/`match_type` como `str` (convención recomendada), años fijos en la SPA y el import de `usePurchaseFilters` entre vistas.

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | estandares | Cuatro líneas de más de 100 caracteres ocultas por `# fmt: skip` | `backend/tests/unit/comparison/test_signal_listing.py` | ✅ Aplicado |
| 2 | estandares | Valores por defecto (`or 0`) al construir la fila de una señal | `backend/src/public_procurement/comparison/services.py` | ✅ Aplicado (`_required`) |
| 3 | limpieza | Años del filtro y rango «2023–2026» fijos en la SPA | `frontend/src/features/signals/{SignalsPage,SignalsKpis}.tsx` | — No aplicado: el rango de datos del MVP es fijo; se deriva de la API cuando la ingesta real amplíe el rango |

Revisar primero: `backend/src/public_procurement/comparison/api.py` (contrato expuesto) · `backend/src/public_procurement/comparison/domain/signals.py` (prioridad)

### Métricas Dev-Rápido

- Tiempo sesión IA: 12 min
- Tareas manuales DoD: 0 min
- Tiempo total: 12 min
