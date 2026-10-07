# Historia #112: Registrar el log de auditoría y aplicar la retención de logs

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Auditar Acciones Administrativas  
**Prioridad:** Alta  
**FRs relacionados:** FR-094 (relacionados: FR-016, FR-032, FR-048, FR-051, FR-052, FR-089; NFR-SEG-007, NFR-OBS-003)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** que toda corrección de datos, clasificación manual, carga manual de observaciones y cambio de configuración quede registrada automáticamente en un log de auditoría inmutable, con su retención configurada,  
**Para** poder explicar en cualquier momento quién cambió qué, cuándo, desde qué valor y por qué, y defender la trazabilidad de las señales ante analistas, proveedores o entidades.

## Descripción

FR-094 exige registrar en un log de auditoría las acciones de **corrección, clasificación manual, carga manual y cambios de configuración**. El criterio de aceptación de la épica pide que **cada cambio de configuración quede en el log con usuario, fecha y valor anterior**. NFR-SEG-007 fija una retención configurable de **12 meses** para la auditoría y NFR-OBS-003 una retención configurable de **30 días** para los logs de aplicación.

En el MVP el Administrador puede operar con scripts o comandos en lugar de pantallas. Por eso la regla clave es que **toda vía** (interfaz, comando, script o carga de archivo) que ejecute una acción auditable pase por el mismo mecanismo que escribe el evento, y que la acción no se aplique si el evento no se puede registrar.

La consulta del log se cubre en HU-113.

---

## Criterios de Aceptación

### Escenario 1: Corrección de un dato extraído

- **Dado** que el Revisor corrige la cantidad del ítem 1 del contrato CO1.PCCNTR.5030063 de 80 a 8 con el comentario "Se leyó 80 por un error de OCR"
- **Cuando** se guarda la corrección
- **Entonces** se registra un evento de tipo "Corrección de dato extraído" con id consecutivo, fecha y hora con segundos (UTC−05:00), usuario, rol, entidad "ítem" e identificador, campo "cantidad", valor anterior 80, valor nuevo 8, comentario y origen

### Escenario 2: Clasificación manual de un candidato

- **Dado** que el Revisor cambia la clasificación de un ítem candidato de "requiere revisión" a "excluido" con el motivo "Comodato, no es compra"
- **Cuando** se guarda
- **Entonces** se registra un evento "Clasificación manual" con valor anterior "requiere revisión", valor nuevo "excluido" y el motivo

### Escenario 3: Carga manual y semiautomática de observaciones

- **Dado** que el Administrador registra manualmente una observación de Alkosto y luego carga un CSV con 12 observaciones válidas
- **Cuando** se guardan
- **Entonces** se registra un evento "Carga manual de observación" para la primera y 12 eventos "Carga semiautomática de observación", uno por observación, que comparten el mismo id de operación y llevan el nombre y el hash del archivo

### Escenario 4: Cambio de configuración

- **Dado** que el Administrador cambia el umbral de mismo modelo de 30 % a 25 % con motivo, creando la versión 4
- **Cuando** se guarda
- **Entonces** se registra un evento "Cambio de configuración" con parámetro, valor anterior 30, valor nuevo 25, versión 4 y motivo

### Escenario 5: La acción no se aplica sin auditoría

- **Dado** que el almacenamiento del log de auditoría no está disponible
- **Cuando** el Revisor intenta corregir un dato extraído
- **Entonces** la corrección no se aplica y recibe "No fue posible registrar la auditoría; la acción no se aplicó. Intente de nuevo."

### Escenario 6: Acción ejecutada por script

- **Dado** que el Administrador ejecuta un comando o script administrativo que corrige 3 precios unitarios
- **Cuando** el script termina
- **Entonces** existen 3 eventos "Corrección de dato extraído" con origen "comando o script" y el usuario que ejecutó el script

### Escenario 7: Inmutabilidad

- **Dado** que existe el evento 1520
- **Cuando** cualquier usuario, incluido el Administrador, intenta modificarlo o borrarlo por los mecanismos de la aplicación
- **Entonces** la operación se rechaza con "El log de auditoría no admite modificaciones ni borrados." y el evento no cambia

### Escenario 8: Valores extensos y datos sensibles

- **Dado** que una acción tiene un valor anterior de 6.000 caracteres y otra cambia un parámetro que contiene una credencial
- **Cuando** se registran los eventos
- **Entonces** el primero guarda los primeros 4.000 caracteres seguidos de "[truncado]" y el hash del valor completo, y el segundo guarda "****" en lugar de la credencial

### Escenario 9: Depuración por retención de la auditoría

- **Dado** que la retención de auditoría es 12 meses y hoy es 2027-10-02
- **Cuando** corre la depuración diaria
- **Entonces** se eliminan los eventos con fecha anterior a 2026-10-02 00:00:00, se conservan los demás y se registra un evento "Depuración de auditoría" con número de eventos eliminados y rango de fechas

### Escenario 10: Retención de logs de aplicación

- **Dado** que la retención de logs de aplicación es 30 días
- **Cuando** corre la depuración diaria
- **Entonces** se eliminan los logs de aplicación con más de 30 días y se conservan los recientes; la depuración no afecta el log de auditoría

### Escenario 11: Cambiar la retención

- **Dado** que el Administrador está autenticado
- **Cuando** fija la retención de auditoría en 24 meses, o intenta fijarla en 0 o 121 meses, o la de logs de aplicación en 0 o 366 días
- **Entonces** el valor válido se guarda como cambio de configuración auditado; los inválidos se rechazan con "La retención de auditoría debe ser un número entero entre 1 y 120 meses." o "La retención de logs de aplicación debe ser un número entero entre 1 y 365 días."

### Escenario 12: Verificación de integridad

- **Dado** que existen los eventos 1 a 2.000
- **Cuando** el Administrador ejecuta la verificación de integridad
- **Entonces** recibe "Log de auditoría íntegro: 2000 eventos, sin saltos de numeración fuera de las depuraciones registradas." o, si falta algún id no explicado por una depuración, "Se detectaron saltos de numeración: {ids}."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador / Revisor (en el MVP, el PO). La auditoría registra también las acciones de cualquier otro usuario que ejecute acciones auditables.
- **Permisos requeridos:** el registro es automático; cambiar la retención y ejecutar la verificación de integridad requieren rol Administrador.
- **Valor de negocio:** trazabilidad de cada intervención humana sobre datos y parámetros; soporte ante reclamos (riesgo legal y reputacional) y reproducibilidad de las señales.

### Reglas de Negocio

- **RN-01 — Tipos de evento auditados:**

  | Tipo | Acción |
  |---|---|
  | Corrección de dato extraído | validar, corregir o rechazar un dato extraído (FR-032) |
  | Clasificación manual | confirmar o cambiar la clasificación de un candidato (FR-016) |
  | Carga manual de observación | registro manual de una observación de precio, incluidas ofertas y términos de búsqueda (FR-048, FR-051) |
  | Carga semiautomática de observación | cada observación cargada por archivo estructurado (FR-052) |
  | Cambio de configuración | cada parámetro cambiado en la configuración versionada, la retención o los destinatarios de alertas (FR-089) |
  | Reactivación de fuente | reactivación de una fuente retail suspendida |
  | Marcado de muestra de validación / Retiro de muestra de validación | cambios en la muestra de validación |
  | Carga de resultados de validación | cada carga de la plantilla de validación |
  | Depuración de auditoría | cada ejecución de depuración por retención |

- **RN-02 — Campos de cada evento:** id entero consecutivo; fecha y hora con segundos (UTC−05:00); usuario (correo) o "sistema"; rol; tipo; entidad afectada (tipo e identificador); campo o parámetro ("—" si no aplica); valor anterior ("—" si no existía); valor nuevo; motivo o comentario ("—" si la acción no lo exige); origen (`interfaz`, `comando o script`, `carga de archivo`, `sistema`); id de operación (agrupa los eventos de una misma acción masiva); referencias adicionales (ej. versión de configuración, nombre y hash del archivo).
- **RN-03 — Un evento por registro afectado:** una acción que afecta varios registros genera un evento por registro, todos con el mismo id de operación.
- **RN-04 — Atomicidad:** la acción auditable y su evento se confirman juntos. Si el evento no se puede registrar, la acción no se aplica y se responde "No fue posible registrar la auditoría; la acción no se aplicó. Intente de nuevo."
- **RN-05 — Todas las vías:** interfaz, comandos, scripts administrativos y cargas de archivo ejecutan las acciones auditables por el mismo mecanismo que registra el evento. Ninguna herramienta administrativa del producto puede modificar estos datos sin generar el evento.
- **RN-06 — Inmutabilidad:** el log es de solo adición. Ningún rol puede modificar ni borrar eventos por los mecanismos de la aplicación ("El log de auditoría no admite modificaciones ni borrados."). Solo la depuración por retención elimina eventos.
- **RN-07 — Tamaño y datos sensibles:** cada valor se guarda hasta 4.000 caracteres; si es más largo, se guardan los primeros 4.000 seguidos de "[truncado]" y el hash SHA-256 del valor completo. Contraseñas, tokens, llaves de servicio y los campos personales excluidos de la ingesta nunca se guardan: se reemplazan por "****".
- **RN-08 — Retención de auditoría:** configurable, entero de 1 a 120 meses; **configuración inicial: 12 meses** (NFR-SEG-007). Una depuración diaria elimina los eventos con fecha anterior a (hoy − retención) a las 00:00:00 y registra un evento "Depuración de auditoría" con cantidad y rango eliminado. Si no hay eventos que eliminar, no registra evento.
- **RN-09 — Retención de logs de aplicación:** configurable, entero de 1 a 365 días; **configuración inicial: 30 días** (NFR-OBS-003). Depuración diaria de los logs de aplicación más antiguos que la retención. Los logs de aplicación tampoco contienen contraseñas, tokens ni campos personales excluidos.
- **RN-10 — Cambios de retención:** se hacen como cambio de configuración (versionado, motivo de 10 a 500 caracteres, evento de auditoría). Reducir la retención aplica en la siguiente depuración diaria.
- **RN-11 — Verificación de integridad:** comprueba que la secuencia de ids no tenga saltos fuera de los rangos eliminados por depuraciones registradas; responde con los mensajes del Escenario 12. Requiere rol Administrador.
- **RN-12 — Mensajes:** los de RN-04, RN-06, el Escenario 11 y el Escenario 12, y "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica: el registro es automático. Mínimo aceptable para el Administrador: parámetros de retención en la configuración y un comando de verificación de integridad. La consulta del log está en HU-113.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-113 (consultar el log), HU-099, HU-100, HU-101, HU-102, HU-104, HU-105 (acciones de esta épica que generan eventos).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Además de las 4 acciones de FR-094, se auditan las acciones administrativas de esta épica que alteran datos de medición o fuentes (reactivación, muestra, resultados de validación) → resuelto en RN-01.
- Ninguna acción auditable se aplica si su evento no se registra → resuelto en RN-04.
- Acciones masivas generan un evento por registro con id de operación común → resuelto en RN-03.
- Los valores largos se truncan a 4.000 caracteres con hash y los secretos se enmascaran → resuelto en RN-07.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-008 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
