# Historia #068: Gestionar los reportes de error y registrar su resolución

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Validación Humana de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-070

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador (que actúa como Revisor en el MVP),  
**Quiero** consultar los reportes de error recibidos, cambiar su estado y registrar la resolución de cada uno,  
**Para** que cada reporte quede gestionado con trazabilidad y el Analista que lo envió conozca el resultado.

## Descripción

Los reportes que crean los Analistas (HU-067) llegan en estado "Recibido". El Administrador los consulta (los más antiguos primero), los pasa a "En revisión" y los cierra como **"Corregido"** o **"Descartado"**, siempre con una resolución escrita. Cada transición queda en el log de auditoría.

La corrección del dato en sí (cantidad, precio, clasificación, emparejamiento u observación) se hace con los mecanismos de revisión y corrección de datos existentes, que conservan el valor original y el corregido y disparan el recálculo de benchmarks y señales. Esta HU solo gestiona el ciclo del reporte. Por la nota de implementación del PRD para capacidades administrativas, puede implementarse **sin interfaz gráfica** (consulta, script o interfaz administrativa mínima), siempre que se cumplan las reglas y quede trazabilidad.

---

## Criterios de Aceptación

### Escenario 1: Consultar reportes pendientes

- **Dado** que existen los reportes RE-000001 (Recibido, 01/10/2026), RE-000002 (En revisión, 01/10/2026) y RE-000003 (Corregido, 30/09/2026)
- **Cuando** el Administrador consulta los reportes abiertos
- **Entonces** obtiene RE-000001 y RE-000002 ordenados del más antiguo al más reciente, cada uno con identificador, estado, fecha, usuario, señal y versión, ítem, objeto, valor mostrado, tipo, descripción y valor sugerido

### Escenario 2: Filtrar por estado y ver conteos

- **Dado** los reportes anteriores
- **Cuando** el Administrador consulta filtrando por "Corregido" y pide el conteo por estado
- **Entonces** obtiene RE-000003 y el conteo "Recibido: 1, En revisión: 1, Corregido: 1, Descartado: 0"

### Escenario 3: Pasar a "En revisión"

- **Dado** que RE-000001 está "Recibido"
- **Cuando** el Administrador lo pasa a "En revisión"
- **Entonces** el estado cambia, y el log de auditoría registra usuario, fecha-hora, reporte, estado anterior y nuevo

### Escenario 4: Cerrar como "Corregido"

- **Dado** que RE-000001 está "En revisión" y el Administrador ya corrigió la cantidad a 8 por el mecanismo de corrección de datos
- **Cuando** lo cierra como "Corregido" con la resolución "Cantidad corregida a 8 según página 4 de la oferta"
- **Entonces** el reporte queda "Corregido" con resolución y fecha de cierre, la auditoría registra el cambio, y el Analista lo ve en "Mis reportes en esta señal"

### Escenario 5: Cerrar como "Descartado"

- **Dado** que RE-000002 está "Recibido"
- **Cuando** el Administrador lo cierra como "Descartado" con la resolución "El comparable es de 55 pulgadas; el emparejamiento es correcto"
- **Entonces** el reporte queda "Descartado" con resolución y fecha de cierre

### Escenario 6: Cierre sin resolución válida

- **Dado** que el Administrador intenta cerrar un reporte sin resolución, con menos de 10 caracteres o con más de 1.000
- **Cuando** confirma el cierre
- **Entonces** la operación se rechaza con "La resolución es obligatoria y debe tener entre 10 y 1.000 caracteres." y el estado no cambia

### Escenario 7: Transición no permitida

- **Dado** que RE-000003 está "Corregido"
- **Cuando** el Administrador intenta pasarlo a "En revisión" o a "Descartado"
- **Entonces** la operación se rechaza con "El reporte ya está cerrado; no se puede cambiar su estado." y el estado no cambia

### Escenario 8: Usuario sin permiso

- **Dado** que un Analista intenta consultar todos los reportes o cambiar el estado de uno
- **Cuando** ejecuta la acción
- **Entonces** se rechaza con "Solo el Administrador puede gestionar reportes de error."

### Escenario 9: Sin reportes abiertos

- **Dado** que no hay reportes en estado "Recibido" ni "En revisión"
- **Cuando** el Administrador consulta los abiertos
- **Entonces** obtiene el resultado vacío con el texto "No hay reportes de error abiertos."

### Escenario 10: Reporte inexistente

- **Dado** el identificador RE-999999 que no existe
- **Cuando** el Administrador intenta cambiar su estado
- **Entonces** se rechaza con "El reporte RE-999999 no existe."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador / Revisor (en el MVP, el PO).
- **Permisos requeridos:** Rol Administrador.
- **Valor de negocio:** Cierra el ciclo del mecanismo de corrección (FR-070) con trazabilidad; reduce el riesgo legal y reputacional.

### Reglas de Negocio

**RN-01 – Estados.** Recibido, En revisión, Corregido, Descartado. Abiertos: Recibido y En revisión. Cerrados: Corregido y Descartado.

**RN-02 – Transiciones permitidas.** Recibido → En revisión; Recibido → Corregido; Recibido → Descartado; En revisión → Corregido; En revisión → Descartado. Cualquier otra se rechaza con "El reporte ya está cerrado; no se puede cambiar su estado." (desde un estado cerrado) o "Transición no permitida de {estado actual} a {estado nuevo}." (otros casos, ej. En revisión → Recibido). Un reporte cerrado no se reabre: si el problema persiste, el Analista crea un reporte nuevo.

**RN-03 – Resolución.** Obligatoria al cerrar (Corregido o Descartado): 10 a 1.000 caracteres tras recortar espacios. Se guarda con la fecha-hora de cierre y el usuario que cerró.

**RN-04 – Consulta.** Permite: listar abiertos (por defecto) o por estado; orden por fecha de creación ascendente; ver todos los campos registrados del reporte (identificador, estado, fecha, usuario creador, señal y versión, ítem, objeto, valor mostrado, tipo, descripción, valor sugerido, resolución, fechas de cambio); conteo por estado. Resultado vacío: "No hay reportes de error abiertos." (o "No hay reportes en estado {estado}." al filtrar).

**RN-05 – Auditoría.** Cada cambio de estado registra en el log de auditoría: usuario, fecha-hora, identificador del reporte, estado anterior, estado nuevo y resolución si aplica.

**RN-06 – Independencia de la corrección.** Cambiar el estado de un reporte no modifica ningún dato, benchmark ni señal. La corrección se hace con los mecanismos de corrección de datos existentes; "Corregido" indica que la corrección ya se hizo por esa vía.

**RN-07 – Visibilidad para el Analista.** El estado, la fecha de cierre y la resolución quedan visibles para el usuario que creó el reporte en "Mis reportes en esta señal"; el aviso de reportes abiertos de la señal se actualiza al cerrar.

**RN-08 – Permisos.** Solo el rol Administrador consulta todos los reportes y cambia estados. Otro rol → "Solo el Administrador puede gestionar reportes de error."

**RN-09 – Concurrencia.** Si dos cambios de estado llegan sobre el mismo reporte, se aplica el primero; el segundo se evalúa contra el estado resultante según RN-02.

### Interfaz

Sin interfaz gráfica obligatoria: puede implementarse con consulta, script o interfaz administrativa mínima, que ofrezca las operaciones de RN-02 a RN-04 y muestre los mensajes definidos.

### Sistemas Externos (Si aplica)

No aplica. No se envían notificaciones por correo en el MVP; el Analista ve el resultado en la señal.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-067 (creación de reportes).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Ciclo de estados del reporte** (Recibido, En revisión, Corregido, Descartado; sin reapertura): resuelto en RN-01/RN-02.
- **Sin notificación por correo en el MVP**; el resultado se ve en la señal: resuelto en Sistemas Externos y RN-07.
- **Gestión sin interfaz gráfica obligatoria** (nota del Dominio 12 aplicada a capacidades administrativas): resuelto en Interfaz.

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-005 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
