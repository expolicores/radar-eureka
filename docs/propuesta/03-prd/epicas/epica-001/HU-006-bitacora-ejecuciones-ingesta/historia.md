# Historia #006: Bitácora de ejecuciones de ingesta

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Controlar Calidad y Trazabilidad de la Ingesta  
**Prioridad:** Crítica  
**FRs relacionados:** FR-007

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que cada ejecución de ingesta de SECOP II y de la TVEC quede registrada con su fuente, fecha y hora, registros leídos, nuevos, actualizados, rechazados y errores,  
**Para** saber en todo momento qué se cargó, cuándo, con qué resultado y qué falló, y poder explicar el estado del universo de datos.

## Descripción

Toda ejecución de las cargas de la épica (SECOP II contratos, TVEC ítems, TVEC órdenes; inicial, incremental programada o incremental manual) crea un **registro de ejecución** al iniciar y lo actualiza al terminar. El registro guarda contadores coherentes entre sí y la lista de errores técnicos (fallas de la API, reintentos, interrupciones), separada de los rechazos de calidad de datos.

El Administrador consulta la bitácora por consulta o script (no requiere interfaz gráfica). Las alertas automáticas y el tablero de estado de fuentes no forman parte de esta historia.

---

## Criterios de Aceptación

### Escenario 1: Registro de una ejecución exitosa

- **Dado** que inicia una carga incremental programada de SECOP II
- **Cuando** la carga termina sin errores técnicos
- **Entonces** existe un registro de ejecución con `id_ejecucion`, fuente "SECOP II contratos", dataset `jbjy-vk9h`, tipo "Incremental programada", fecha y hora de inicio y fin, duración, estado "Exitosa", marca de agua usada y resultante, fecha de corte, contadores leídos, nuevos, actualizados, sin cambios, rechazados y con advertencias, y lista de errores vacía

### Escenario 2: Registro al iniciar

- **Dado** que una carga acaba de iniciar
- **Cuando** se consulta la bitácora antes de que termine
- **Entonces** la ejecución aparece con estado "En curso", fecha y hora de inicio, contadores parciales actualizados al terminar cada página y sin fecha de fin

### Escenario 3: Coherencia de contadores

- **Dado** que una ejecución terminó en estado "Exitosa"
- **Cuando** se revisan sus contadores
- **Entonces** se cumple que leídos = nuevos + actualizados + sin cambios + rechazados; si no se cumple, la ejecución se marca con el error "Contadores inconsistentes: leídos {a} ≠ suma {b}"

### Escenario 4: Ejecución con errores técnicos recuperados

- **Dado** que durante la ejecución hubo 2 reintentos que luego se recuperaron
- **Cuando** termina la ejecución
- **Entonces** el estado es "Exitosa" y la lista de errores contiene 2 entradas con fecha y hora, página, tipo de error (tiempo de espera, HTTP {código}), número de intento y resultado "Recuperado"

### Escenario 5: Ejecución fallida

- **Dado** que una ejecución agotó los reintentos o recibió un error no recuperable
- **Cuando** termina
- **Entonces** el estado es "Fallida", la lista de errores contiene el error final con resultado "No recuperado" y el mensaje técnico (sin secretos ni datos sensibles), y los contadores reflejan lo procesado hasta la falla

### Escenario 6: Ejecución omitida

- **Dado** que una ejecución programada no se pudo ejecutar (otra en curso o sin carga inicial previa)
- **Cuando** se registra
- **Entonces** queda con estado "Omitida", el motivo, la fecha y hora y contadores en 0

### Escenario 7: Ejecución interrumpida

- **Dado** que el proceso se detuvo abruptamente y la ejecución quedó "En curso" sin actividad por más de 6 horas
- **Cuando** inicia una nueva ejecución de la misma fuente
- **Entonces** la ejecución anterior pasa a "Fallida" con el error "Ejecución interrumpida sin cierre" y fecha de fin igual a su última actividad

### Escenario 8: Consulta de la bitácora

- **Dado** que existen ejecuciones de varias fuentes
- **Cuando** el Administrador consulta filtrando por fuente, tipo, estado o rango de fechas
- **Entonces** obtiene las ejecuciones ordenadas de la más reciente a la más antigua con todos sus campos; si no hay resultados obtiene "No hay ejecuciones de ingesta para los filtros indicados."

### Escenario 9: Última ejecución por fuente

- **Dado** que existen ejecuciones de SECOP II contratos, TVEC ítems y TVEC órdenes
- **Cuando** el Administrador consulta el resumen por fuente
- **Entonces** obtiene, por cada fuente, la última ejecución, la última ejecución "Exitosa", su marca de agua y su fecha de corte; una fuente sin ejecuciones aparece como "Sin ejecuciones"

### Escenario 10: Acceso restringido

- **Dado** que un usuario con rol Analista intenta consultar la bitácora
- **Cuando** ejecuta la consulta
- **Entonces** el acceso se deniega y no se devuelve información

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** da trazabilidad operativa del universo de datos y es el insumo del estado de fuentes y alertas de la operación del MVP.

### Reglas de Negocio

- **RN-01 Alcance:** se registra toda ejecución de las fuentes "SECOP II contratos", "TVEC ítems" y "TVEC órdenes", de tipo "Inicial", "Incremental programada" o "Incremental manual".
- **RN-02 Campos del registro:** `id_ejecucion` (único), `fuente`, `dataset`, `tipo`, `estado` ("En curso", "Exitosa", "Fallida", "Omitida"), `motivo_omision` (solo en "Omitida"), `inicio` y `fin` (fecha y hora America/Bogota), `duracion_segundos`, `ultima_actividad`, `marca_agua_usada`, `marca_agua_resultante`, `fecha_corte`, `fecha_corte_aproximada`, `ejecutada_sin_token` (sí/no), `leidos`, `nuevos`, `actualizados`, `sin_cambios`, `rechazados`, `con_advertencias`, `errores` (lista), `usuario` (identificador del Administrador en ejecuciones manuales; "sistema" en programadas).
- **RN-03 Definición de contadores:** `leidos` = registros recibidos de la API después de aplicar el prefiltro, antes de las validaciones; `nuevos`, `actualizados`, `sin_cambios` y `rechazados` son excluyentes entre sí; `con_advertencias` es independiente (un registro nuevo puede tener advertencias). Invariante: `leidos = nuevos + actualizados + sin_cambios + rechazados`.
- **RN-04 Entrada de error:** `fecha_hora`, `pagina` (o lote), `tipo` (Tiempo de espera, HTTP {código}, Respuesta no interpretable, Interrupción, Contadores inconsistentes), `intento` (1 a 4), `resultado` ("Recuperado" o "No recuperado"), `mensaje` (texto truncado a 1.000 caracteres). El mensaje nunca incluye el app token, credenciales ni valores de campos no permitidos.
- **RN-05 Actualización durante la ejecución:** el registro se crea al iniciar (estado "En curso") y se actualiza al terminar cada página: contadores parciales y `ultima_actividad`.
- **RN-06 Interrupción:** una ejecución "En curso" con `ultima_actividad` de más de 6 horas (configurable, entero de 1 a 48) se cierra como "Fallida" al iniciar otra de la misma fuente (Escenario 7).
- **RN-07 Separación errores / rechazos:** los rechazos de calidad de datos no son errores de la ejecución; se cuentan en `rechazados` y se detallan en el registro de rechazos de calidad.
- **RN-08 Conservación:** los registros de ejecución no se modifican después de cerrados (salvo el cierre por interrupción de RN-06) y no se eliminan automáticamente durante el MVP.
- **RN-09 Orden y filtros de consulta:** orden por `inicio` descendente; filtros combinables por fuente, tipo, estado y rango de fechas de inicio (ambos extremos inclusive). Rango con fecha inicial posterior a la final → "El rango de fechas no es válido: la fecha inicial es posterior a la final."
- **RN-10 Permisos:** solo el rol Administrador consulta la bitácora.

### Interfaz

No requiere interfaz gráfica. Consultas o scripts del Administrador: (a) listado filtrable (Escenario 8); (b) resumen por fuente (Escenario 9). Salida en tabla o JSON.

### Sistemas Externos (Si aplica)

No aplica: registra la actividad de las cargas que consumen la API de datos.gov.co.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-001, HU-002, HU-003, HU-004 (cargas que registran ejecuciones), HU-005 (registro de rechazos de calidad).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- FR-007 no define qué es "error" frente a "rechazado" → resuelto: errores técnicos de la ejecución vs. rechazos de calidad de datos (RN-07).
- Se agregan los contadores "sin cambios" y "con advertencias" para que los contadores cuadren → resuelto en RN-03 con invariante explícita.
- Las alertas y el tablero de estado de fuentes pertenecen a la operación del MVP, fuera de esta épica → eliminado del alcance de esta historia.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
