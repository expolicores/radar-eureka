## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Dependencias | `openapi-typescript` exige TypeScript 5 como *peer* y el proyecto usa TypeScript 6 | Se ejecuta con `npx --yes openapi-typescript@7` en el script `generate:api`, fuera de las dependencias del proyecto |
| 2 | Tests | `openapi-fetch` con `baseUrl: ""` crea `Request` con URL relativa, inválida en jsdom | `baseUrl = location.origin` (en el navegador es el mismo origen; en desarrollo el *proxy* de Vite lleva `/api` al backend) |
| 3 | Lint | `react-hooks/set-state-in-effect` al sincronizar el buscador con la URL | Estado derivado durante el render (patrón recomendado por React) |
| 4 | Entorno | Los procesos hijos de los servidores de prueba no mueren al terminar el job de bash | Detenidos por puerto de escucha (8000/5173) y verificado 0 escuchas |

### Completion Notes

- ⚡ Dev-Rápido: primera pantalla navegable. Marco de la aplicación con la cinta «datos ficticios», marca y navegación del mockup; «Explorar compras» con búsqueda (espera de 300 ms), filtros de fuente, modalidad, departamento, valor y orden, filtros en la URL, tabla con formatos colombianos, insignias del estado del análisis, paginación, fecha de corte en hora de Bogotá y estados cargando/vacío/error con «Reintentar». Cliente tipado generado desde el OpenAPI del backend (`backend/scripts/export_openapi.py` + `npm run generate:api`), TanStack Query y React Router. Secciones Señales, Mis casos, Administración y Ficha muestran «Disponible en un próximo incremento del MVP Beta».
- 📝 Decisiones autónomas: CSS propio con los tokens del mockup y **sin librería de componentes** (la elección de la librería accesible de LBC-FE-001 queda pendiente para el PO); rutas declaradas en `App.tsx` en lugar de un `routes.tsx` aparte (menos superficie).
- ✅ Verificado: ESLint, Prettier, `tsc`, **20 tests de Vitest**, build de Vite; de punta a punta con el backend real y la base de la demo a través del *proxy* de Vite (`/api/v1/purchases` y `/filters` responden por el puerto 5173).
- ⚠️ No verificado: revisión visual en navegador (el entorno no tiene navegador automatizable); CI sin remoto.
- 🧪 Cobertura QA: 8/8.

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/scripts/export_openapi.py` | Exporta el contrato OpenAPI al frontend |
| Creado | `frontend/src/api/{openapi.json,schema.ts}` | Contrato y tipos generados |
| Creado | `frontend/src/api/client.ts` | Cliente tipado y `ApiError` |
| Creado | `frontend/src/styles.css` | Tokens y estilos del mockup |
| Creado | `frontend/src/lib/{format.ts,format.test.ts}` | Formatos COP, fechas y hora de Bogotá |
| Creado | `frontend/src/app/AppShell.tsx`, `frontend/src/features/pending/PendingSection.tsx` | Marco y secciones pendientes |
| Creado | `frontend/src/components/{Badge,Pagination}.tsx` | Componentes compartidos |
| Creado | `frontend/src/features/explore/*` (7 archivos) | Pantalla Explorar y su test |
| Creado | `frontend/src/test/{render.tsx,api.ts}` | Proveedores y API simulada para tests |
| Modificado | `frontend/src/{App.tsx,App.test.tsx,main.tsx}` | Rutas, proveedores y test del marco |
| Modificado | `frontend/{package.json,package-lock.json,vite.config.ts,eslint.config.js,.prettierignore}` | Dependencias, script `generate:api`, *proxy*, archivos generados ignorados |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosos un test del marco con dos aserciones relacionadas y aserciones de precondición dentro del Arrange.

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | bug | El clic en el enlace de la compra también disparaba el de la fila (doble navegación) | `frontend/src/features/explore/PurchasesTable.tsx` | ✅ Aplicado (`stopPropagation`) |
| 2 | estandares | Tests de formatos sin patrón 3A y uno con dos conductas | `frontend/src/lib/format.test.ts` | ✅ Aplicado |

Revisar primero: `frontend/src/api/client.ts` (contrato consumido de la API)

### Métricas Dev-Rápido

- Tiempo sesión IA: 9 min
- Tareas manuales DoD: 0 min
- Tiempo total: 9 min
