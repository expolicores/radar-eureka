## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: Casos de investigación mínimos y notas

**Arquitectura:** nuevo módulo `investigation` (esquema `investigation`) en la capa más alta de los módulos de dominio: lee señales por `comparison.services` y compras por `exploration.services`. Primer módulo con **escrituras desde la API** (rápidas y transaccionales: no son jobs).
**Feature análoga:** `market` (HU #5: repositorio de solo inserción, unidad de trabajo, servicio, migración) y `comparison/api.py` (HU #6/#7: router, `app.state`, *problem details*). Todas 2026-10-07; candidatas descartadas: ninguna.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Usuario actual | Dependencia `get_current_user` en `entrypoints/api/dependencies.py` que entrega el **usuario de demostración** (UUID fijo, «Analista demo»); los servicios reciben `owner_id` y filtran por dueño | Sin autenticación en el MVP Beta; reemplazable por `identity` sin tocar servicios |
| Instantáneas | `case_item.snapshot` JSONB de solo inserción armado en el servicio desde `comparison.services`/`exploration.services`; `UNIQUE(case_id, kind, reference)` | HU-096; ADR-012 |
| Notas | `case_note` de solo inserción, 1–5.000 caracteres | HU-093; edición/borrado diferidos |
| Última actividad | `case.last_activity_at` se actualiza al guardar un elemento o nota (metadato del caso, no hecho de negocio) | Orden de «Mis casos» |
| Errores | Caso o referencia inexistente → excepción → 404; duplicado → estado de negocio `SaveResult.ALREADY_SAVED` → 422 (ajustado en la revisión del diff) | Estándar §3 |
| Validación | Pydantic en la API (longitudes) y verificación en el dominio | Doble barrera |
| Guardar en caso (UI) | Selector desplegable con los casos y «+ Nuevo caso…» (título en línea), confirmación con mensaje | Mockup (toast) |

**Pasos**
1. Dominio y persistencia de `investigation` + migración `0005`.
2. Servicio (crear, listar, abrir, guardar elemento con instantánea, agregar nota) y API.
3. Dependencia del usuario actual y cableado; contratos import-linter.
4. Frontend: «Mis casos», «Guardar en caso» en detalle de señal y ficha.
5. Tests (dominio, API con doble, integración, Vitest).

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| Patrón de `market` (unidad de trabajo privada, `build_*`) | Se replica | Feature análoga |
| `comparison.services.SignalQueryService.get_signal` | Se reutiliza | Instantánea de la señal |
| `exploration.services.ExplorationService.get_purchase` | Se reutiliza | Instantánea de la compra |
| `entrypoints/api/errors.py` | Se reutiliza | 400/404/422 |
| `frontend` `Badge`, `format`, `client`, `test/{api,render}` | Se reutilizan | Compartidos |
| `SaveToCaseButton` | Se crea una vez | Detalle de señal y ficha |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Autorización por propietario: 404 a terceros | Convenciones de Tests, arquitectura | Servicio, repositorio, tests |
| 404/422/400 en *problem details* en español | §3 | API |
| Solo inserción para instantáneas y notas | §4 | Repositorio |
| Solo `<module>.services` entre módulos | §2, §4 | `investigation` |
| Datos L3 nunca en logs | §4 | Notas (texto libre): no se registran en logs |
| Estados de vista y textos en español | Patrones | Pantallas |
| pytest + builders + 3A; Vitest | §6 | Tests |

### Tareas de Implementación

#### Fase 1 — Backend
- [ ] **T1: Módulo `investigation`** — `investigation/{__init__,README.md,repositories,services,api}.py`, `investigation/domain/{__init__,case}.py`, `alembic/versions/0005_investigation_schema.py`, `alembic/env.py`
- [ ] **T2: Cableado** — `entrypoints/api/{dependencies,app}.py`, `backend/pyproject.toml` (capas y contratos)

#### Fase 2 — Frontend
- [ ] **T3: Pantallas** — `src/api/*`, `src/features/cases/{CasesPage,CaseDetail,useCases}.tsx`, `src/components/SaveToCaseButton.tsx`, integración en `SignalDetailPage` y `PurchaseDetailPage`, `src/App.tsx`, estilos

#### Fase 3 — Tests
- [ ] **T4: Tests** — `tests/unit/investigation/*`, `tests/integration/test_cases.py`, Vitest de «Mis casos» y «Guardar en caso»
- [ ] **T5: Verificación** — suites completas y API real

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
