## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: API y pantalla de Señales

**Arquitectura:** `comparison` expone la lectura de señales (`SignalQueryService`) y su router (`comparison/api.py`); los datos de la compra se obtienen por `ingestion.services`. La SPA agrega la vista `features/signals`.
**Feature análoga:** `exploration` (API + servicio de vistas, HU #3) y `features/explore` (pantalla, HU #4), ambos 2026-10-07. Candidatas descartadas por más antiguas: ninguna.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Filtrado y orden | En memoria sobre las señales vigentes (decenas en el MVP), enriquecidas con la compra vía `ingestion.services` (`get_many`) | Volumen del MVP; evita leer tablas de otro módulo. Se pasa a SQL o vista materializada cuando crezca |
| Indicadores | `comparison` cuenta resultados vigentes por resultado y confianza; `ingestion.services.tv_purchase_counts()` da el desglose por fuente | Cada módulo cuenta lo suyo |
| Descripción del ítem | `ingestion` la entrega; la API arma «TV 65" 4K ×8» con los atributos del ítem | Mockup |
| Ruta inicial | `/` → `/senales` | Mockup: la demo empieza en Señales |
| Confianza visual | Componente `ConfidenceBadge` (barras + texto) reutilizable en el detalle | Mockup |

**Pasos**
1. `ingestion`: `get_many(ids)` y `tv_purchase_counts()`.
2. `comparison`: consultas de señales vigentes y conteos; `SignalQueryService` con filtros, prioridad y paginación; `api.py` y cableado.
3. Frontend: contrato, `features/signals` (página, filtros, tabla, indicadores), `ConfidenceBadge`, rutas.
4. Tests: unitarios del orden y filtros, API con doble, integración, Vitest.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `exploration/api.py` (patrón `app.state` + `Depends`) | Se replica | Feature análoga |
| `entrypoints/api/errors.py` | Se reutiliza | 400/404 |
| `frontend/src/components/{Badge,Pagination}.tsx`, `lib/format.ts`, `api/client.ts`, `test/{render,api}.ts` | Se reutilizan | Compartidos |
| `features/explore/labels.ts` (`SOURCE_LABELS`) | Se mueve a `src/lib/labels.ts` | Lo usan Explorar y Señales |
| `ConfidenceBadge` | Se crea una vez | Lista y detalle |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Solo `<module>.services` entre módulos | §2, §4 | `comparison` → `ingestion` |
| `api.py` solo entrada/salida; RFC 9457 en español | §1, §3 | `comparison/api.py` |
| Textos sin términos acusatorios; prueba automática sobre las respuestas | §4, Convenciones de Tests | API y pantalla |
| COP `int`; desviación como decimal con un dígito | §2 | Esquemas |
| SPA sin reglas de negocio (prioridad la calcula la API) | §4 | `features/signals` |
| Estados cargando/vacío/error/resultado en español | Patrones de Código | Pantalla |
| pytest + builders + 3A; Vitest 3A | §6 | Tests |

### Tareas de Implementación

#### Fase 1 — Backend
- [ ] **T1: Lectura en `ingestion`** — `ingestion/repositories.py`, `ingestion/services.py` (`get_many`, `tv_purchase_counts`)
- [ ] **T2: Lectura de señales** — `comparison/domain/signals.py` (orden de prioridad, filtros puros), `comparison/repositories.py` (señales vigentes, conteos), `comparison/services.py` (`SignalQueryService`, vistas), `comparison/api.py`, `entrypoints/api/app.py`, `backend/pyproject.toml` (capas: `exploration | comparison.api`)

#### Fase 2 — Frontend
- [ ] **T3: Pantalla Señales** — `src/api/*` (regenerado), `src/lib/labels.ts`, `src/components/ConfidenceBadge.tsx`, `src/features/signals/{SignalsPage,SignalsFilters,SignalsTable,SignalsKpis,useSignals}.tsx`, `src/App.tsx`, estilos (KPI, confianza)

#### Fase 3 — Tests
- [ ] **T4: Tests** — `tests/unit/comparison/test_signal_listing.py`, `tests/unit/comparison/test_signals_api.py`, `tests/integration/test_signal_queries.py`, `frontend/src/features/signals/SignalsPage.test.tsx`
- [ ] **T5: Verificación** — suites completas y API real

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
