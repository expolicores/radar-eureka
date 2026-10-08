## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: Detalle de la señal y ficha de la compra

**Arquitectura:** `comparison` expone el detalle reproducible de una señal (`SignalQueryService.get_signal`) leyendo compras por `ingestion.services` y observaciones por `market.services`; `exploration` agrega el resultado vigente por ítem en la ficha vía `comparison.services`. SPA: `features/signal-detail` y `features/purchase`.
**Feature análoga:** `comparison/api.py` + `SignalQueryService` (HU #6) y `exploration` (HU #3); pantallas `features/signals` (HU #6). Todas 2026-10-07; candidatas descartadas: ninguna.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Detalle | Lee la fila vigente por `signal_code` y sus vínculos (`item_comparable`, `item_market_observation`); las observaciones se completan con `market.services.get_many` | FR-065: reproducible desde lo guardado, no recalculado |
| Gráfico | Franja de puntos en SVG propio (sin librería): SECOP II círculo `#2a78d6`, TVEC rombo `#1baf7a`, compra analizada `#eb6834` con anillo blanco de 2 px; caja Q1–Q3, mediana y umbral (línea discontinua); *tooltip* por punto con área de impacto ≥ 24 px; leyenda; `role="img"` + `aria-label`; alternativa «Ver como tabla» | Mockup; guía de visualización: paleta validada (`validate_palette.js`: PASS; WARN de contraste del verde compensado con forma, leyenda y tabla) |
| Evidencia | Tarjeta «Evidencia de origen» con el texto de pendiente; sin documentos simulados | Escenario 5: no inventar evidencia |
| Resultado por ítem en la ficha | `ComparisonQueryService.item_results(purchase_id)` → resultado y código por línea | La ficha muestra la señal del ítem (mockup) |
| 404 | `HTTPException(404, "Señal no encontrada")` → *problem details* por el *handler* global | Estándar §3 |

**Pasos**
1. `comparison`: consultas del detalle y de resultados por ítem; servicio y API.
2. `exploration`: resultado por ítem en la ficha.
3. Frontend: `StripPlot`, detalle de señal, ficha de la compra, rutas.
4. Tests y verificación.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `SignalQueryService`, `_signal_row`, `_required` | Se reutilizan y extienden | La fila de la señal es la cabecera del detalle |
| `market.services.MarketQueryService.get_many` | Se reutiliza | Ya existe |
| `ConfidenceBadge`, `Badge`, `lib/format`, `lib/labels`, `test/api` | Se reutilizan | Compartidos |
| `StripPlot` | Se crea una vez | Detalle de señal (y ficha en el futuro) |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Solo `<module>.services` entre módulos | §2, §4 | `comparison` → `ingestion`/`market`; `exploration` → `comparison` |
| RFC 9457 en español (404) | §3 | API |
| SPA sin reglas de negocio: muestra lo que entrega la API | §4 | Detalle y ficha |
| Estados cargando/vacío/error/resultado | Patrones | Pantallas |
| Textos sin términos acusatorios; aviso de no conclusión | §4 | API y pantallas |
| COP `int`; formatos colombianos | §2 | Esquemas y UI |
| pytest + builders + 3A; Vitest 3A | §6 | Tests |

### Tareas de Implementación

#### Fase 1 — Backend
- [ ] **T1: Detalle de señal** — `comparison/repositories.py` (`current_by_code`, `links_of`, `item_results`), `comparison/services.py` (`SignalDetail`, `get_signal`, `ComparisonQueryService.item_results`), `comparison/api.py` (`GET /api/v1/signals/{code}`)
- [ ] **T2: Ficha** — `exploration/services.py` y `exploration/api.py` (resultado y código por ítem)

#### Fase 2 — Frontend
- [ ] **T3: Pantallas** — `src/components/StripPlot.tsx`, `src/features/signal-detail/{SignalDetailPage,BenchmarkOneCard,BenchmarkTwoCard,ConfidenceCard,useSignal}.tsx`, `src/features/purchase/{PurchaseDetailPage,usePurchase}.tsx`, `src/App.tsx`, estilos

#### Fase 3 — Tests
- [ ] **T4: Tests** — `tests/unit/comparison/test_signal_detail_api.py`, `tests/integration/test_signal_detail.py`, `tests/unit/exploration/test_purchases_api.py`, Vitest de detalle y ficha
- [ ] **T5: Verificación** — suites completas, API real

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
