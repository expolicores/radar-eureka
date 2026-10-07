# Historia #100: Alertar al Administrador ante una ingesta o captura fallida o retrasada

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Operar Fuentes de Datos  
**Prioridad:** Alta  
**FRs relacionados:** FR-088 (relacionados: FR-007, FR-094; NFR-OBS-002)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** recibir una alerta por correo electrónico en menos de una hora cuando una ingesta o captura falle o no se ejecute a tiempo,  
**Para** enterarme de los errores de las fuentes sin tener que consultar su estado todos los días y actuar antes de que los datos queden desactualizados.

## Descripción

El estado de fuentes muestra los errores, pero solo si el Administrador lo consulta. El criterio de aceptación de la épica exige que **una ingesta fallida genere alerta en ≤ 1 hora** (NFR-OBS-002). Esta HU detecta dos tipos de falla en las fuentes automatizadas (SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes y, cuando tengan captura automática habilitada, Alkosto y Falabella):

1. **Ejecución fallida:** una ejecución terminó con resultado `fallida`.
2. **Ejecución retrasada:** la fuente no inició ninguna ejecución dentro de su frecuencia configurada más la tolerancia de retraso.

Por cada falla envía un correo a los destinatarios configurados y deja la alerta en una **bitácora de alertas** consultable. Cuando la fuente vuelve a tener una ejecución exitosa, envía un aviso de recuperación.

**Implementación sin UI permitida:** la configuración de destinatarios y la consulta de la bitácora pueden hacerse por configuración, comando, consulta o interfaz administrativa mínima.

---

## Criterios de Aceptación

### Escenario 1: Alerta por ejecución fallida

- **Dado** que la ejecución 812 de "SECOP II — Contratos" terminó `fallida` a las 2026-10-02 03:12 con el mensaje "Tiempo de espera agotado tras 3 reintentos"
- **Cuando** el sistema detecta la falla
- **Entonces** a más tardar a las 2026-10-02 04:12 se envía un correo a cada destinatario configurado con el asunto "[Compras Públicas] Falla en SECOP II — Contratos: ejecución fallida" y el contenido de RN-05, y la alerta queda en la bitácora con estado de envío "Enviada"

### Escenario 2: Alerta por ejecución retrasada

- **Dado** que "TVEC — Ítems" tiene frecuencia de 24 horas, tolerancia de 1 hora y su última ejecución inició a las 2026-10-01 05:00 sin otra posterior
- **Cuando** llegan las 2026-10-02 06:00 sin que haya iniciado ninguna ejecución
- **Entonces** a más tardar a las 2026-10-02 07:00 se envía un correo con el asunto "[Compras Públicas] Falla en TVEC — Ítems: ejecución retrasada" y la alerta queda en la bitácora

### Escenario 3: Una sola alerta de retraso por vencimiento

- **Dado** que ya se envió la alerta de retraso de "TVEC — Ítems" y la fuente sigue sin ejecutarse
- **Cuando** el sistema vuelve a verificar las fuentes en ciclos posteriores
- **Entonces** no envía una nueva alerta de retraso para el mismo vencimiento; solo vuelve a alertar si, después de iniciarse una ejecución, la fuente vuelve a retrasarse

### Escenario 4: Ejecuciones fallidas consecutivas

- **Dado** que "SECOP II — Archivos" tuvo dos ejecuciones fallidas seguidas (ids 901 y 902)
- **Cuando** el sistema detecta cada falla
- **Entonces** envía una alerta por cada ejecución, identificando su id; nunca dos alertas para la misma ejecución

### Escenario 5: Aviso de recuperación

- **Dado** que se envió una alerta por la ejecución fallida 812 de "SECOP II — Contratos"
- **Cuando** la siguiente ejecución de esa fuente termina `exitosa`
- **Entonces** se envía un correo con el asunto "[Compras Públicas] Fuente recuperada: SECOP II — Contratos" que indica la ejecución exitosa y la hora, y se registra en la bitácora como tipo "Recuperación"

### Escenario 6: Ejecución manual fallida

- **Dado** que el Administrador relanzó "TVEC — Órdenes" y esa ejecución terminó `fallida`
- **Cuando** el sistema detecta la falla
- **Entonces** envía la alerta igual que para una ejecución programada, indicando origen `manual` y el usuario que la lanzó

### Escenario 7: Fuentes que no generan alerta de retraso

- **Dado** que "Alkosto" está suspendida y "Falabella" no tiene captura automática habilitada
- **Cuando** pasan más de 8 días sin ejecuciones de esas fuentes
- **Entonces** no se envía alerta de retraso para ninguna de las dos

### Escenario 8: Falla en el envío del correo

- **Dado** que el servicio de correo no está disponible
- **Cuando** el sistema intenta enviar una alerta
- **Entonces** reintenta el envío dentro de la ventana de 1 hora (RN-07); si todos los intentos fallan, la alerta queda en la bitácora con estado de envío "No entregada" y el último error del servicio de correo

### Escenario 9: Configurar destinatarios válidos

- **Dado** que el Administrador está autenticado
- **Cuando** configura como destinatarios "po@comprastv.co" y "operacion@comprastv.co"
- **Entonces** la configuración se guarda, las siguientes alertas se envían a esas dos direcciones y se registra un evento de auditoría de cambio de configuración con valor anterior y nuevo

### Escenario 10: Destinatarios inválidos

- **Dado** que el Administrador está autenticado
- **Cuando** intenta guardar una lista vacía, una dirección sin formato de correo ("po@comprastv") o más de 5 direcciones
- **Entonces** la configuración no cambia y recibe, respectivamente, "Debe configurar al menos un destinatario de alertas.", "La dirección 'po@comprastv' no tiene un formato de correo válido." o "Se permiten como máximo 5 destinatarios de alertas."

### Escenario 11: Consultar la bitácora de alertas

- **Dado** que existen 3 alertas registradas en los últimos 7 días
- **Cuando** el Administrador consulta la bitácora
- **Entonces** obtiene las 3 alertas, de la más reciente a la más antigua, con los campos de RN-08

### Escenario 12: Bitácora vacía

- **Dado** que no hay alertas registradas en el rango consultado
- **Cuando** el Administrador consulta la bitácora
- **Entonces** recibe el mensaje "No hay alertas registradas en el período consultado."

### Escenario 13: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta consultar la bitácora o cambiar los destinatarios
- **Entonces** no obtiene datos ni cambia nada y recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador para configurar destinatarios y consultar la bitácora. La detección y el envío son automáticos.
- **Valor de negocio:** cumple el criterio de épica y NFR-OBS-002 (alerta en ≤ 1 hora) y protege la frescura de datos (NFR-DAT-002).

### Reglas de Negocio

- **RN-01 — Fuentes vigiladas:** SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes y las fuentes retail (Alkosto, Falabella) solo mientras tengan captura automática habilitada y no estén suspendidas. La suspensión de una fuente retail se notifica por la regla de suspensión (FR-047), no por esta HU.
- **RN-02 — Ejecución fallida:** toda ejecución que termine con resultado `fallida`, sea de origen `programada` o `manual`, genera exactamente una alerta, identificada por el id de la ejecución.
- **RN-03 — Ejecución retrasada:** una fuente vigilada está retrasada cuando la hora actual supera el inicio de su última ejecución + frecuencia configurada + tolerancia de retraso (configuración inicial: frecuencia pública 24 horas, frecuencia retail 7 días, tolerancia 1 hora). Si la fuente nunca se ha ejecutado, no se evalúa retraso (su estado es "Sin ejecuciones"). Se envía una sola alerta por vencimiento; la condición se reinicia cuando inicia una nueva ejecución.
- **RN-04 — Plazo de la alerta:** el correo debe enviarse en un tiempo máximo configurable desde el momento de la falla (fin de la ejecución fallida o vencimiento del plazo de retraso). Rango: 5 a 60 minutos; **configuración inicial: 60 minutos**. La verificación periódica de fuentes debe ejecutarse con una frecuencia que permita cumplir ese plazo.
- **RN-05 — Contenido del correo de falla:**
  - Asunto: "[Compras Públicas] Falla en {fuente}: ejecución fallida" o "[Compras Públicas] Falla en {fuente}: ejecución retrasada".
  - Cuerpo: fuente; tipo de falla; fecha y hora de la falla (`AAAA-MM-DD HH:MM`, UTC−05:00); id de la ejecución (en retraso: id e inicio de la última ejecución); origen (`programada` / `manual`) y usuario si es manual; registros leídos, nuevos, actualizados, rechazados y errores (solo fallida); mensaje de error principal (máximo 500 caracteres); próxima ejecución esperada (solo retraso); y el texto fijo "Revise el estado de fuentes y relance la fuente si corresponde."
  - Nunca incluye credenciales, tokens de API ni datos personales.
- **RN-06 — Aviso de recuperación:** si una fuente tuvo alerta de falla (fallida o retrasada) y luego termina una ejecución `exitosa`, se envía un único correo "[Compras Públicas] Fuente recuperada: {fuente}" con el id y la hora de fin de la ejecución exitosa. Sin alerta de falla previa no se envía aviso de recuperación.
- **RN-07 — Reintentos de envío:** si el servicio de correo falla, se reintenta hasta 3 veces dentro del plazo de RN-04. Si se agotan, la alerta queda "No entregada" con el último error del servicio de correo y no se reintenta después. Cada destinatario tiene su propio estado de envío.
- **RN-08 — Bitácora de alertas:** cada alerta se registra con: id de alerta; tipo (Ejecución fallida / Ejecución retrasada / Recuperación); fuente; id de ejecución relacionada; fecha y hora de la falla; fecha y hora de envío; destinatarios; estado de envío por destinatario (Enviada / No entregada) y último error de envío. La consulta filtra por rango de fechas (por defecto, últimos 7 días; máximo 365 días), fuente y tipo, y ordena de la más reciente a la más antigua. La bitácora se conserva el mismo período que los logs de aplicación (configuración inicial: 30 días).
- **RN-09 — Destinatarios:** lista de 1 a 5 direcciones de correo con formato `usuario@dominio.tld`, sin duplicados (sin distinguir mayúsculas). **Configuración inicial:** el correo de la cuenta del Administrador. Todo cambio de la lista registra un evento de auditoría de cambio de configuración con usuario, fecha y hora, valor anterior y valor nuevo.
- **RN-10 — Mensajes:**
  - "Debe configurar al menos un destinatario de alertas."
  - "La dirección '{direccion}' no tiene un formato de correo válido."
  - "Se permiten como máximo 5 destinatarios de alertas."
  - "La dirección '{direccion}' está repetida."
  - "No hay alertas registradas en el período consultado."
  - "El rango de consulta no puede superar 365 días."
  - "El plazo de alerta debe ser un número entero entre 5 y 60 minutos." (el plazo vigente no cambia)
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: parámetro de configuración con la lista de destinatarios y el plazo de alerta; comando o consulta "bitácora de alertas" con filtros de RN-08; y correos de texto con el formato de RN-05 y RN-06.

### Sistemas Externos (Si aplica)

- **Servicio de envío de correo electrónico** (el mismo que use la plataforma para la recuperación de contraseña): envío exitoso → "Enviada"; servicio no disponible o rechazo → reintentos (RN-07) y luego "No entregada".

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-098 (estado de fuentes), HU-099 (relanzar), HU-102 (frecuencias), HU-112 (auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El canal de alerta es el correo electrónico, con bitácora consultable como respaldo → resuelto en RN-05, RN-08 y RN-09.
- Además de la ejecución fallida, se alerta la ejecución retrasada (la ingesta que no corrió), con una alerta por vencimiento → resuelto en RN-03.
- Se envía un aviso de recuperación después de una alerta de falla → resuelto en RN-06.
- Las suspensiones retail se notifican por FR-047 y no se duplican aquí → resuelto en RN-01.

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
