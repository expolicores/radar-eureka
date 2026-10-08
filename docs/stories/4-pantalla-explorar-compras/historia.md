# Historia de Usuario

**Como** Analista,
**Quiero** una pantalla «Explorar compras» donde buscar, filtrar, ordenar y paginar las compras de televisores, y ver su estado del análisis,
**Para** encontrar en segundos las compras que me interesa revisar, sin depender de consultas técnicas

## Descripción

Tercer *vertical slice* del MVP Beta y primera pantalla navegable. Crea el **marco de la aplicación** según el mockup (cinta «datos ficticios», encabezado con marca y navegación Señales / Explorar compras / Mis casos / Administración) y la vista **Explorar compras** conectada a la API del slice 2 mediante un **cliente tipado generado desde OpenAPI**. Las secciones que aún no existen se muestran como «Disponible en un próximo incremento», sin datos inventados.

HUs del backlog tomadas como referencia: HU-069 (listado), HU-070/071/072 (filtros), HU-083 (fecha de actualización).

**No incluye:** ficha de la compra (slice 6; las filas quedan enlazadas a la ruta de la ficha), señales y filtro «con señal» (slices 4–5), login y roles (la autenticación se difiere), selección de librería de componentes.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** la API con las compras seed
- **Cuando** el Analista abre «Explorar compras»
- **Entonces** ve el título y la descripción del mockup, la fecha «Datos actualizados al 06-oct-2026 03:10», el contador de compras y una tabla con Compra, Fuente, Entidad, Proveedor, Objeto, Valor (COP con separador de miles), Estado del análisis (insignia con texto) y Fecha (dd-mmm-aaaa), ordenada por fecha descendente y paginada de a 25

### Escenario 2: Validaciones

- **Dado** la pantalla abierta
- **Cuando** el Analista escribe en el buscador (entidad, proveedor por nombre o NIT, objeto o referencia) o elige Fuente, Modalidad, Departamento, Valor (`< $20 M`, `$20 M – $100 M`, `> $100 M`) u Orden
- **Entonces** la tabla y el contador se actualizan con los resultados de la API, la página vuelve a 1 y los filtros quedan en la URL (se puede compartir o recargar sin perderlos)

### Escenario 3: Casos Extremos

- **Dado** una búsqueda sin coincidencias, la API caída o una respuesta lenta
- **Cuando** se carga la tabla
- **Entonces** se muestra el estado correspondiente en español: «No hay compras que coincidan con los filtros» (vacío), «No fue posible cargar las compras. Intenta de nuevo.» con botón «Reintentar» (error) o «Cargando compras…» (cargando)

### Escenario 4: Paginación

- **Dado** más de 25 resultados
- **Cuando** el Analista usa «Anterior» / «Siguiente»
- **Entonces** cambia de página, ve «Página N de M · X compras» y los botones se deshabilitan en los extremos

### Escenario 5: Navegación del marco

- **Dado** el marco de la aplicación
- **Cuando** el Analista navega a Señales, Mis casos o Administración
- **Entonces** ve el título de la sección y el aviso «Disponible en un próximo incremento del MVP Beta», y la opción activa queda resaltada; la ruta raíz lleva a «Explorar compras» mientras no exista «Señales»

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista.
- **Permisos requeridos:** ninguno en el MVP Beta (sin login).
- **Valor de negocio:** primera pantalla de la demo; base visual y técnica de las siguientes.

### Reglas de Negocio

- Textos de UI en español; la SPA no contiene reglas de negocio: el estado del análisis viene calculado de la API.
- Insignias del estado del análisis (texto del mockup): `pending_comparison` «Pendiente de comparación», `no_unit_price` «ⓘ Sin precio unitario · limitación de la fuente», `quality_review` «◐ En revisión de calidad», `vat_undetermined` «IVA indeterminado · comparación incompleta», `excluded` «Excluido · no es compra de televisores».
- Montos en COP sin decimales con separador de miles colombiano; fechas `dd-mmm-aaaa` en español; la fecha de corte en hora de Bogotá.
- La cinta superior advierte que todos los datos son ficticios.

### Interfaz

- Rutas: `/explorar` (por defecto), `/senales`, `/casos`, `/admin`, `/compras/:id` (ficha, slice 6).
- Diseño: tokens de color, tipografía, tabla, insignias, filtros y chip del mockup (`docs/propuesta/06-mockups/mockup-demo-seguimiento-compras-publicas.html`).
- Búsqueda con espera de 300 ms tras la última tecla.

### Sistemas Externos

API propia (`/api/v1/purchases`, `/api/v1/purchases/filters`) vía *proxy* de Vite en desarrollo.

### Disparadores

- El Analista abre la pantalla.
- El Analista cambia un filtro, la búsqueda, el orden o la página (relanzable).
- El Analista pulsa «Reintentar» tras un error.

### Entidades del Dominio

- Compra

### Alcance y Continuidad

El slice 5 agrega «Señales» y el filtro «Con señal»; el slice 6 la ficha. La autenticación y los roles se difieren.

### Preview de Interfaz

Mockup, sección «Explorar compras de televisores».

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md` (SPA sin reglas de negocio, cliente tipado desde OpenAPI), `docs/architecture/coding-standards.md` §1, §5, Patrones de Código (estados cargando/vacío/error/resultado).
**Historias relacionadas:** #3 (API de exploración). Backlog: HU-069…HU-072, HU-083
**Lecciones aprendidas:** detener los servidores de desarrollo que se arranquen para probar (un Vite huérfano bloqueó `npm ci`)

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
