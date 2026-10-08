## Refinamiento Técnico (Developer)
**Autor**: Juan Camilo | **Fecha**: 2026-10-07

## Plan: Pantalla Explorar compras

**Arquitectura:** SPA React + TS estricto + Vite, sin reglas de negocio; consume `/api/v1` con un **cliente tipado generado desde OpenAPI**; estructura `src/features/<vista>/`.
**Feature análoga:** `frontend/src/App.tsx` y `App.test.tsx` (HU #1, 2026-10-07) — única UI existente; para la API, `backend/src/public_procurement/exploration/api.py` (HU #3, 2026-10-07). Candidatas descartadas: ninguna. El diseño visual sale del mockup.
**Medición:** sin Measurement Strategy aprobada → §2c y §7 omitidos (`STRATEGY_NOT_APPROVED`).

### Decisiones técnicas (modo autónomo, registradas)

| Tema | Decisión | Fundamento |
| ---- | -------- | ---------- |
| Cliente de API | `openapi-typescript` genera `src/api/schema.ts` desde `src/api/openapi.json`, que exporta `backend/scripts/export_openapi.py`; llamadas con `openapi-fetch` | Arquitectura: cliente tipado desde OpenAPI (LBC-FE-002) |
| Datos remotos | `@tanstack/react-query` (caché, reintento manual, estados) | LBC-FE-002 lo nombra |
| Rutas | `react-router` (rutas del marco y de la ficha) | Navegación del mockup |
| Estilos | CSS propio con los **tokens del mockup** (`src/styles.css`); **sin** librería de componentes por ahora | Prioridad del PO: cercanía al mockup. La librería accesible (LBC-FE-001) queda como decisión pendiente |
| Formatos | `src/lib/format.ts`: COP `$39.600.000`, fecha `14-ago-2026` (meses en español sin punto), fecha de corte en hora de Bogotá | Mockup |
| Estado en URL | Filtros, orden y página en `searchParams`; búsqueda con espera de 300 ms | Escenario 2 |
| Proxy de desarrollo | Vite `server.proxy['/api'] → http://localhost:8000` | Sin CORS en el backend |
| Estado del análisis | La SPA solo traduce el código a texto e insignia (mapa en `AnalysisStatusBadge`) | SPA sin reglas de negocio |

**Pasos**
1. Exportar OpenAPI y generar tipos — referencia: `exploration/api.py`.
2. Base del frontend: estilos del mockup, formatos, cliente, proveedores (Query + Router) — referencia: `main.tsx`.
3. Marco (cinta, encabezado, navegación) y secciones pendientes.
4. Pantalla Explorar: filtros, tabla, insignias, paginación, estados.
5. Tests Vitest con `fetch` simulado — cubre QA-01…QA-08.
6. Verificación manual en navegador contra la API con la base de la demo.

### Reutilización

| Componente | Decisión | Motivo |
|------------|----------|--------|
| `frontend/src/test/setup.ts` | Se reutiliza | Matchers de Testing Library |
| `frontend/src/App.tsx` / `App.test.tsx` | Se reemplazan por el marco con rutas | La página mínima de R0 deja de tener sentido |
| `src/lib/format.ts` | Se crea una vez | Lo usarán Explorar, Señales, ficha y casos |
| `src/api/client.ts` | Se crea una vez | Todas las vistas |
| `src/test/render.tsx` (`renderWithProviders`) | Se crea una vez | Todos los tests de vistas |
| `src/components/Badge.tsx` | Se crea una vez | Insignias de estado aquí y de señales/confianza después |

### Estándares aplicables

| Regla | Sección del estándar | Aplica a |
|-------|----------------------|----------|
| Componentes en PascalCase, hooks con `use`, `.tsx` en PascalCase en `src/features/<vista>/` | §1 | Todo el frontend |
| Campos del contrato de la API sin renombrar a mano (camelCase solo en variables propias) | §1 Variables y Funciones | Uso de `schema.ts` |
| SPA sin reglas de negocio | §4 | Estado del análisis viene de la API |
| Cada vista maneja cargando, vacío, error y resultado, con textos en español | Patrones de Código | Explorar |
| Cliente tipado generado del OpenAPI | Patrones de Código / Recomendaciones | `src/api` |
| Vitest + Testing Library, patrón 3A; `it(...)` en español | §6 | Tests |
| ESLint `recommended-type-checked` + `react-hooks`; TS `strict`; Prettier | Configuración de Herramientas | Todo |
| Textos de UI en español; sin términos acusatorios | §4 Reglas transversales | Copys |

### Tareas de Implementación

#### Fase 1 — Contrato de API
- [ ] **T1: OpenAPI y tipos** — `backend/scripts/export_openapi.py`, `frontend/src/api/openapi.json`, `frontend/src/api/schema.ts`, `frontend/package.json` (`generate:api`, dependencias)

#### Fase 2 — Base
- [ ] **T2: Estilos, formatos y cliente** — `frontend/src/styles.css`, `frontend/src/lib/format.ts`, `frontend/src/api/client.ts`, `frontend/src/main.tsx`, `frontend/vite.config.ts` (proxy)
- [ ] **T3: Marco y rutas** — `frontend/src/app/AppShell.tsx`, `frontend/src/app/routes.tsx`, `frontend/src/features/pending/PendingSection.tsx`, `frontend/src/App.tsx`, `frontend/src/components/Badge.tsx`

#### Fase 3 — Explorar
- [ ] **T4: Pantalla** — `frontend/src/features/explore/ExplorePage.tsx`, `ExploreFilters.tsx`, `PurchasesTable.tsx`, `AnalysisStatusBadge.tsx`, `usePurchases.ts`, `Pagination.tsx` (en `src/components/`)

#### Fase 4 — Tests y verificación
- [ ] **T5: Tests** — `frontend/src/test/render.tsx`, `frontend/src/test/api.ts` (respuestas simuladas), `frontend/src/lib/format.test.ts`, `frontend/src/features/explore/ExplorePage.test.tsx` (QA-01…QA-07), `frontend/src/App.test.tsx` (QA-08)
- [ ] **T6: Verificación** — lint, Prettier, `tsc`, Vitest, build; navegador contra la API real

### Checklist
☑ Feature análoga (la más reciente) leída completa | ☑ TODOS los artefactos identificados | ☑ Respeta arquitectura | ☑ Inventario de reutilización hecho | ☑ Estándares leídos y aplicables extraídos
