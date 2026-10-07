# ÉPICA-006: Exploración y Ficha del Contrato

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Da al analista la puerta de entrada: buscar, filtrar y ordenar contratos e ítems de televisor, ver la **lista priorizada de señales** y abrir la **ficha del contrato** con sus datos, ítems extraídos, benchmarks, señales, documentos, estado de procesamiento y enlace a la fuente oficial. Es la base determinística del producto: funciona sin IA sobre los datos estructurados y los ya extraídos.

**Prioridad:** Crítica  
**FRs cubiertos:** FR-071, FR-072, FR-073, FR-074, FR-075, FR-076  
**Total HU:** 15 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Búsqueda y Filtrado de Compras

- [HU-069: Explorar el listado de compras públicas de televisores](./HU-069-explorar-compras-de-televisores/historia.md)
- [HU-070: Filtrar la exploración por entidad, proveedor y modalidad](./HU-070-filtrar-por-entidad-proveedor-modalidad/historia.md)
- [HU-071: Filtrar la exploración por fechas, rango de valor y UNSPSC](./HU-071-filtrar-por-fechas-valor-y-unspsc/historia.md)
- [HU-072: Filtrar la exploración por territorio, fuente y existencia de señal](./HU-072-filtrar-por-territorio-fuente-y-senal/historia.md)
- [HU-073: Ordenar los resultados de la exploración por desviación, valor, fecha o confianza](./HU-073-ordenar-resultados-de-exploracion/historia.md)

### Feature 2: Priorización de Señales

- [HU-074: Ver la lista priorizada de señales que merecen revisión](./HU-074-ver-lista-priorizada-de-senales/historia.md)
- [HU-075: Filtrar y ordenar la lista de señales que merecen revisión](./HU-075-filtrar-y-ordenar-lista-de-senales/historia.md)

### Feature 3: Consulta de la Ficha del Contrato

- [HU-076: Ver los datos clave del contrato y el enlace a la fuente oficial en la ficha](./HU-076-ver-datos-clave-de-la-ficha/historia.md)
- [HU-077: Ver los ítems de televisor extraídos en la ficha del contrato](./HU-077-ver-items-de-televisor-en-la-ficha/historia.md)
- [HU-078: Ver los benchmarks de cada ítem con la distribución de precios comparables en la ficha](./HU-078-ver-benchmarks-del-item-en-la-ficha/historia.md)
- [HU-079: Ver las señales que merecen revisión del contrato en la ficha](./HU-079-ver-senales-del-contrato-en-la-ficha/historia.md)
- [HU-080: Ver los documentos del proceso en la ficha del contrato](./HU-080-ver-documentos-del-proceso-en-la-ficha/historia.md)

### Feature 4: Seguimiento del Procesamiento y Frescura de Datos

- [HU-081: Ver el estado de procesamiento del contrato en la ficha](./HU-081-ver-estado-de-procesamiento/historia.md)
- [HU-082: Ver los motivos de información insuficiente del contrato en la ficha](./HU-082-ver-motivos-informacion-insuficiente/historia.md)
- [HU-083: Mostrar la fecha de actualización de los datos en la exploración y en la ficha](./HU-083-mostrar-fecha-de-actualizacion-datos/historia.md)

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-069 | FR-071, FR-072 | Analista | Puerta de entrada única al universo de compras de televisores (contratos e ítems) |
| HU-070 | FR-071 | Analista | Acotar la exploración por entidad, proveedor y modalidad |
| HU-071 | FR-071 | Analista | Acotar por período, tamaño de compra y UNSPSC |
| HU-072 | FR-071 | Analista | Acotar por territorio, fuente y existencia de señal |
| HU-073 | FR-072 | Analista | Ver primero los casos con mayor desviación o confianza |
| HU-074 | FR-073 | Analista | Iniciar la revisión desde las señales priorizadas, a ≤ 3 clics de la evidencia |
| HU-075 | FR-071, FR-072, FR-073 | Analista | Priorizar señales según territorio, período o actor |
| HU-076 | FR-074 | Analista | Contexto del contrato y verificación en la fuente oficial |
| HU-077 | FR-074 | Analista | Ver qué se compró, a qué precio unitario y con qué evidencia |
| HU-078 | FR-074 | Analista | Entender el Benchmark 1 con la distribución de precios y el estado del Benchmark 2 |
| HU-079 | FR-074 | Analista | Identificar los ítems del contrato que merecen revisión |
| HU-080 | FR-074 | Analista | Trazabilidad directa a los documentos oficiales y copias de evidencia |
| HU-081 | FR-075 | Analista | No interpretar como "sin señal" un contrato a medio procesar |
| HU-082 | FR-075 | Analista | Distinguir límites de la fuente de límites del procesamiento |
| HU-083 | FR-076 | Analista | Saber qué tan actual es la información y citarla |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
