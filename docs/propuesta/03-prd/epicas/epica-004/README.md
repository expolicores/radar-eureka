# ÉPICA-004: Referencias de Mercado Trazables

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Implementa la **base propia de observaciones de precio de mercado** (Adenda 2), separando cómo se consigue un precio de cómo se usa. Cada observación guarda su registro mínimo y su **método de adquisición**; las observaciones manuales se identifican siempre como tales. Las observaciones de Alkosto (principal) y Falabella (secundaria) pueden llegar por carga manual individual, búsqueda manual con todas las ofertas (protocolo contra sesgo), carga por archivo CSV o, cuando exista un mecanismo permitido y viable, por captura automática desde sitemaps y datos estructurados. **La automatización no es condición de éxito del MVP**: el Benchmark 2 funciona solo con carga manual. La captura automática nunca evade CAPTCHA, bloqueos ni autenticación y se suspende sola ante ellos.

**Prioridad:** Crítica (las HUs de captura automática T409–T412 son Alta, porque la automatización no es condición de éxito del MVP)  
**FRs cubiertos:** FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053  
**Total HU:** 12 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Gestionar Base de Observaciones de Mercado

- [HU-042: Almacenar observaciones de precio de mercado con registro mínimo trazable](./HU-042-almacenar-observaciones-mercado/historia.md)
- [HU-043: Conservar el histórico inmutable de observaciones de mercado](./HU-043-conservar-historico-observaciones/historia.md)

### Feature 2: Aplicar Reglas de Precio de Referencia

- [HU-044: Aceptar solo observaciones cuyo vendedor sea directamente la tienda](./HU-044-filtrar-vendedor-tienda/historia.md)
- [HU-045: Usar el precio efectivo de venta y conservar el precio anterior solo como evidencia](./HU-045-registrar-precio-efectivo/historia.md)
- [HU-046: Identificar y marcar precios sujetos a condiciones especiales](./HU-046-marcar-precios-condicionados/historia.md)

### Feature 3: Cargar Observaciones Manual y Semiautomáticamente

- [HU-047: Registrar manualmente una observación de precio con evidencia adjunta](./HU-047-registrar-observacion-manual/historia.md)
- [HU-048: Registrar una búsqueda manual con todas las ofertas comparables y sus términos](./HU-048-registrar-busqueda-manual-completa/historia.md)
- [HU-049: Cargar observaciones de precio de forma semiautomática con un archivo CSV](./HU-049-cargar-observaciones-csv/historia.md)

### Feature 4: Capturar Precios Automáticamente con Salvaguardas

- [HU-050: Ejecutar la captura automática controlada de una fuente retail](./HU-050-ejecutar-captura-automatica-controlada/historia.md)
- [HU-051: Capturar observaciones de Alkosto desde su sitemap y datos estructurados](./HU-051-capturar-precios-alkosto/historia.md)
- [HU-052: Capturar observaciones de Falabella con vendedor = Falabella desde sitemaps y datos estructurados](./HU-052-capturar-precios-falabella/historia.md)
- [HU-053: Suspender la captura automática y notificar ante CAPTCHA, bloqueo, autenticación o cambio de robots.txt](./HU-053-suspender-captura-ante-bloqueo/historia.md)

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-042 | FR-041, FR-042, FR-049 | Administrador | Base propia e independiente con registro mínimo y método de adquisición; habilita el Benchmark 2 sin API comercial |
| HU-043 | FR-053 | Administrador | Histórico propio de precios de mercado, reproducible y auditable |
| HU-044 | FR-044 | Administrador | Excluye vendedores terceros y reduce falsos positivos |
| HU-045 | FR-045 | Administrador | Referencia basada en el precio realmente pagado, no en precios "antes" inflados |
| HU-046 | FR-046 | Administrador | Evita referencias artificialmente bajas por precios condicionados |
| HU-047 | FR-048, FR-049, FR-050 | Administrador | Benchmark 2 operable solo con carga manual, con evidencia y usuario registrado |
| HU-048 | FR-051, FR-049, FR-050 | Administrador | Protocolo contra el sesgo de selección en la carga manual |
| HU-049 | FR-052, FR-049, FR-050 | Administrador | Carga masiva validada campo a campo con menos tiempo humano |
| HU-050 | FR-043 | Administrador | Captura programada con `robots.txt`, ritmo, volumen y User-Agent controlados |
| HU-051 | FR-043, FR-044, FR-045 | Administrador | Observaciones automáticas de la fuente principal (Alkosto) |
| HU-052 | FR-043, FR-044, FR-045, FR-046 | Administrador | Observaciones automáticas de la fuente secundaria solo con vendedor = Falabella |
| HU-053 | FR-047 | Administrador | Cumplimiento verificable de cero evasión y continuidad con carga manual |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
