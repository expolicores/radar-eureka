# ÉPICA-008: Operación, Calidad y Medición del MVP

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Da al Administrador (el PO en el MVP, que también actúa como Revisor) el control para operar y **medir** el MVP: estado de las fuentes, relanzamiento de ingestas, alertas de fallas, parámetros analíticos y operativos versionados, cola de revisión humana, muestra de validación manual y KPIs (precisión global y por campo, los tres indicadores de cobertura de D4-1 con TVEC aparte, trazabilidad, comparabilidad, base tributaria, señales sustentadas, eficiencia por caso y costos), además del log de auditoría.

Todas las historias pueden implementarse **sin interfaz gráfica** (configuración, comandos, scripts, consultas, archivos CSV/XLSX o interfaz administrativa mínima), según la nota del Dominio 12 del PRD. Los valores numéricos se presentan como **configuración inicial configurable**.

**Prioridad:** Alta  
**FRs cubiertos:** FR-088, FR-089, FR-090, FR-091, FR-092, FR-093, FR-094  
**Total HU:** 16 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Operar Fuentes de Datos

- [HU-098: Consultar el estado de las fuentes de datos](./HU-098-consultar-estado-fuentes/historia.md)
- [HU-099: Relanzar una ingesta o captura y reactivar una fuente suspendida](./HU-099-relanzar-ingesta-o-captura/historia.md)
- [HU-100: Alertar al Administrador ante una ingesta o captura fallida o retrasada](./HU-100-alertar-fallas-ingesta-captura/historia.md)

### Feature 2: Configurar Parámetros del Análisis

- [HU-101: Configurar y versionar los parámetros de comparación y señal](./HU-101-configurar-parametros-comparacion-senal/historia.md)
- [HU-102: Configurar términos de búsqueda, umbral de aceptación de extracción y frecuencias](./HU-102-configurar-parametros-operativos/historia.md)

### Feature 3: Gestionar Revisión y Muestra de Validación

- [HU-103: Consultar la cola de revisión humana](./HU-103-consultar-cola-revision-humana/historia.md)
- [HU-104: Marcar contratos y documentos de la muestra de validación manual](./HU-104-marcar-muestra-validacion/historia.md)
- [HU-105: Generar la plantilla de validación y cargar los resultados verificados](./HU-105-registrar-resultados-validacion/historia.md)

### Feature 4: Medir KPIs del MVP

- [HU-106: Calcular la precisión de la extracción, global y por campo](./HU-106-calcular-precision-extraccion/historia.md)
- [HU-107: Calcular los tres indicadores de cobertura sobre SECOP II, con TVEC aparte](./HU-107-calcular-indicadores-cobertura/historia.md)
- [HU-108: Verificar trazabilidad de señales, clasificación de comparaciones y base tributaria](./HU-108-calcular-kpis-trazabilidad-comparabilidad/historia.md)
- [HU-109: Registrar el tiempo que el Analista dedica a cada señal](./HU-109-registrar-tiempo-por-caso/historia.md)
- [HU-110: Calcular los KPIs de señales sustentadas y de eficiencia por caso](./HU-110-calcular-kpis-validacion-eficiencia/historia.md)
- [HU-111: Consultar el costo por documento procesado con IA y el costo mensual por componente](./HU-111-consultar-costos-operacion/historia.md)

### Feature 5: Auditar Acciones Administrativas

- [HU-112: Registrar el log de auditoría y aplicar la retención de logs](./HU-112-registrar-log-auditoria/historia.md)
- [HU-113: Consultar y exportar el log de auditoría](./HU-113-consultar-log-auditoria/historia.md)

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-098 | FR-088 | Administrador | Detectar rápido fuentes fallidas, retrasadas o suspendidas |
| HU-099 | FR-088 | Administrador | Recuperar la frescura de datos tras una falla sin evadir restricciones |
| HU-100 | FR-088 (NFR-OBS-002) | Administrador | Alerta de ingesta o captura fallida en ≤ 1 hora |
| HU-101 | FR-089 | Administrador | Recalibrar umbrales sin redespliegue y reproducir señales pasadas |
| HU-102 | FR-089 | Administrador | Ajustar identificación, carga de revisión y frescura de datos |
| HU-103 | FR-090 | Administrador / Revisor | Organizar la revisión humana semanal sin elementos olvidados |
| HU-104 | FR-092 | Administrador | Construir una muestra diversa de ≥ 50 elementos sin sesgo de selección |
| HU-105 | FR-092, FR-091 | Administrador / Revisor | Verdad verificada independiente del extractor para precisión y cobertura |
| HU-106 | FR-091 (NFR-CAL-001, 002) | Administrador | Precisión global y por campo; evidencia para calibrar el umbral |
| HU-107 | FR-091 (NFR-CAL-003) | Administrador | Separar el límite de la fuente del desempeño de la extracción |
| HU-108 | FR-091 (NFR-CAL-004, 005, 006) | Administrador | Garantizar trazabilidad, clasificación y coherencia tributaria |
| HU-109 | FR-093 | Administrador | Medir el tiempo humano real por caso |
| HU-110 | FR-091, FR-093 (NFR-CAL-007, 008) | Administrador | Validar la hipótesis de valor: señales sustentadas y eficiencia |
| HU-111 | FR-091 (NFR-OBS-001) | Administrador | Identificar los drivers de costo del MVP |
| HU-112 | FR-094 (NFR-SEG-007, NFR-OBS-003) | Administrador | Trazabilidad inmutable de cada intervención humana y de configuración |
| HU-113 | FR-094 | Administrador | Responder con evidencia quién cambió qué, cuándo y por qué |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
