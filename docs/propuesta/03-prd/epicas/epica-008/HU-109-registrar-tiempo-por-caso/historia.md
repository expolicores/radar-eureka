# Historia #109: Registrar el tiempo que el Analista dedica a cada señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-093 (relacionados: FR-069, FR-091; NFR-CAL-008, NFR-SEG-003)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** que el sistema registre automáticamente cuánto tiempo dedica cada Analista a una señal, desde que la abre hasta que la califica, descontando las pausas largas,  
**Para** medir el KPI de eficiencia (reducción ≥ 70 % del tiempo humano por caso frente a la línea base manual) con datos reales de uso y no con estimaciones.

## Descripción

FR-093 exige registrar el tiempo que el Analista dedica a cada caso, **desde que abre la señal hasta que la califica** como "suficientemente sustentada para merecer revisión" o no (FR-069). Es el insumo del KPI de eficiencia (NFR-CAL-008), cuya línea base manual se mide en el discovery (D2). El procesamiento automático no cuenta como tiempo humano.

La medición es invisible para el Analista: no le agrega pasos ni pantallas. El sistema registra eventos de actividad del Analista (abrir la señal, navegar a contrato, documento, página u observación, calificar) y calcula dos tiempos por par Analista–señal: **bruto** (calificación − primera apertura) y **activo** (bruto sin las pausas mayores que un umbral de inactividad). El KPI usa el tiempo activo.

**Implementación sin UI permitida:** la consulta de mediciones para el Administrador puede ser comando, consulta o exportación CSV.

---

## Criterios de Aceptación

### Escenario 1: Medición completa sin pausas largas

- **Dado** que la Analista `analista1@prueba.co` abre la señal SEN-0101 a las 09:00:00, navega a su contrato a las 09:02:00, al documento de origen a las 09:05:30, a una observación a las 09:09:00 y califica la señal a las 09:12:40
- **Cuando** el sistema registra la calificación
- **Entonces** queda una medición "completa" con primera apertura 09:00:00, calificación 09:12:40, tiempo bruto 12:40 (760 s), tiempo activo 12:40 (760 s), 1 apertura y 0 pausas excluidas

### Escenario 2: Pausa mayor que el umbral

- **Dado** que el umbral de inactividad es 30 minutos y la Analista abre SEN-0102 a las 10:00, navega al documento a las 10:04, no tiene actividad hasta las 10:50 (vuelve a abrir la señal) y califica a las 10:56
- **Cuando** el sistema registra la calificación
- **Entonces** el tiempo bruto es 56:00 y el tiempo activo es 10:00 (se excluye el intervalo de 46 minutos entre 10:04 y 10:50), con 2 aperturas y 1 pausa excluida

### Escenario 3: Pausa igual al umbral

- **Dado** que entre dos eventos consecutivos atribuidos a la misma señal pasan exactamente 30:00 minutos
- **Cuando** se calcula el tiempo activo
- **Entonces** ese intervalo se cuenta completo (solo se excluyen intervalos mayores que el umbral)

### Escenario 4: Señales intercaladas

- **Dado** que la Analista abre SEN-0103 a las 11:00, abre SEN-0104 a las 11:05, vuelve a SEN-0103 a las 11:15 y la califica a las 11:20, y califica SEN-0104 a las 11:30 tras abrirla de nuevo a las 11:22
- **Cuando** se calculan los tiempos
- **Entonces** cada evento se atribuye a la señal abierta más recientemente: SEN-0103 suma 11:00–11:05 y 11:15–11:20 (activo 10:00); SEN-0104 suma 11:05–11:15 y 11:22–11:30 (activo 18:00)

### Escenario 5: Señal abierta y no calificada

- **Dado** que la Analista abrió SEN-0105 y no la ha calificado
- **Cuando** el Administrador consulta las mediciones
- **Entonces** SEN-0105 aparece con estado "sin calificar", sin tiempo bruto ni activo, y no entra al KPI de eficiencia

### Escenario 6: Recalificación

- **Dado** que la Analista calificó SEN-0101 a las 09:12:40 y la vuelve a calificar el día siguiente
- **Cuando** se registra la segunda calificación
- **Entonces** la medición no cambia: se mide hasta la primera calificación

### Escenario 7: Calificación sin apertura registrada

- **Dado** que existe una calificación de SEN-0106 sin ningún evento de apertura de esa Analista
- **Cuando** se procesa la medición
- **Entonces** queda con estado "incompleta" y motivo "No hay apertura registrada para la señal." y no entra al KPI

### Escenario 8: Falla al registrar un evento

- **Dado** que el registro de eventos de medición no está disponible
- **Cuando** la Analista abre o califica una señal
- **Entonces** la Analista completa su acción sin error ni demora visible; la medición afectada queda "incompleta" con motivo "Eventos de medición perdidos." y no entra al KPI

### Escenario 9: Solo se mide al rol Analista

- **Dado** que el Administrador abre y califica una señal para probarla
- **Cuando** se procesan las mediciones
- **Entonces** no se crea medición para el Administrador

### Escenario 10: Consultar y exportar mediciones

- **Dado** que existen mediciones de 3 Analistas
- **Cuando** el Administrador consulta filtrando por Analista, rango de fechas de calificación y estado, o exporta a CSV
- **Entonces** obtiene las mediciones con los campos de RN-07, ordenadas por fecha de calificación descendente

### Escenario 11: Sin mediciones

- **Dado** que no hay mediciones en el rango consultado
- **Cuando** el Administrador consulta
- **Entonces** recibe "No hay mediciones de tiempo en el período consultado."

### Escenario 12: Un Analista no puede consultar mediciones

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar mediciones, incluidas las suyas
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (consulta); el Analista es el sujeto medido, sin interacción adicional.
- **Permisos requeridos:** rol Administrador para consultar y exportar. El registro de eventos es automático.
- **Valor de negocio:** sin esta medición no se puede demostrar la hipótesis de valor del MVP (identificar casos que merecen revisión con mucho menos esfuerzo que el análisis manual).

### Reglas de Negocio

- **RN-01 — Unidad de medición:** par (Analista, señal). Una medición por par.
- **RN-02 — Eventos de actividad registrados:** apertura del detalle de una señal; navegación desde la señal a contrato, documento, página/evidencia u observación de referencia; consulta de benchmarks de la señal; calificación de la señal. Cada evento guarda Analista, señal en foco, tipo de evento y fecha y hora con precisión de segundos (UTC−05:00).
- **RN-03 — Atribución:** cada evento se atribuye a la señal abierta más recientemente por ese Analista (señal en foco). La apertura de una señal cambia el foco a esa señal.
- **RN-04 — Inicio y fin:** inicio = primera apertura de la señal por el Analista; fin = primera calificación de esa señal por el Analista. Recalificaciones posteriores no modifican la medición.
- **RN-05 — Tiempos:** tiempo bruto = fin − inicio. Tiempo activo: se ordenan todos los eventos del Analista; cada intervalo entre un evento y el siguiente evento del mismo Analista (de cualquier señal) se atribuye a la señal del evento que lo inicia; el tiempo activo de la señal es la suma de sus intervalos dentro de [inicio, fin] que sean ≤ umbral de inactividad; los intervalos mayores se excluyen completos y se cuentan como "pausas excluidas". El tiempo después de la calificación no se cuenta. Se almacenan en segundos y se muestran como `mm:ss` (o `h:mm:ss` desde 1 hora).
- **RN-06 — Umbral de inactividad:** configurable, entero de 5 a 120 minutos; **configuración inicial: 30 minutos** (igual al cierre de sesión por inactividad, NFR-SEG-003). El umbral vigente al momento de la calificación se guarda con la medición; cambiarlo no recalcula mediciones anteriores.
- **RN-07 — Campos de la medición:** id; Analista; señal; contrato u orden; primera apertura; primera calificación; calificación otorgada (sustentada / no sustentada); tiempo bruto; tiempo activo; número de aperturas; número de pausas excluidas; umbral usado; estado; motivo (si es incompleta).
- **RN-08 — Estados:** "completa" (tiene inicio y fin, y todos sus eventos se registraron); "sin calificar" (tiene apertura, no calificación); "incompleta" (calificación sin apertura, o eventos perdidos) con motivo "No hay apertura registrada para la señal." o "Eventos de medición perdidos.". Solo las "completa" alimentan el KPI de eficiencia.
- **RN-09 — Roles medidos:** solo usuarios con rol Analista. Acciones de usuarios Administrador no generan mediciones.
- **RN-10 — No interferencia:** el registro de eventos no puede bloquear, demorar de forma perceptible ni hacer fallar la acción del Analista; si falla, la acción continúa y la medición queda "incompleta".
- **RN-11 — Consulta:** filtros por Analista, rango de fechas de calificación (`AAAA-MM-DD`, extremos incluidos, máximo 365 días) y estado; orden por fecha de calificación descendente (las "sin calificar" por fecha de primera apertura); exportación CSV UTF-8 con los campos de RN-07.
- **RN-12 — Privacidad:** las mediciones solo se usan para el KPI de eficiencia; el Analista no ve tiempos propios ni ajenos. No se registra contenido de notas ni comentarios.
- **RN-13 — Mensajes:** "No hay mediciones de tiempo en el período consultado."; "El umbral de inactividad debe ser un número entero entre 5 y 120 minutos." (el umbral vigente no cambia); "El rango de consulta no puede superar 365 días."; "La fecha inicial no puede ser posterior a la fecha final."; "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

Sin cambios visibles para el Analista. Para el Administrador, mínimo aceptable: comando o consulta "mediciones de tiempo" con filtros y exportación CSV.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-110 (KPIs de validación humana y eficiencia).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El KPI usa el tiempo activo, que descuenta pausas mayores que un umbral de inactividad (inicial 30 minutos, igual a la expiración de sesión) → resuelto en RN-05 y RN-06.
- Con señales intercaladas, cada evento se atribuye a la señal abierta más recientemente → resuelto en RN-03.
- Se mide hasta la primera calificación; las recalificaciones no cambian la medición → resuelto en RN-04.
- Solo se registran los eventos necesarios para el KPI; no es analítica de uso (excluida por la épica) → resuelto en RN-02 y RN-12.

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
