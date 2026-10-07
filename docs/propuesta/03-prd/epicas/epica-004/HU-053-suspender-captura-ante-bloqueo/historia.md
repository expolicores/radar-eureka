# Historia #053: Suspender la captura automática y notificar ante CAPTCHA, bloqueo, autenticación o cambio de robots.txt

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Capturar Precios Automáticamente con Salvaguardas  
**Prioridad:** Alta  
**FRs relacionados:** FR-047

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que la captura automática de una fuente se suspenda sola en cuanto detecte un CAPTCHA, un bloqueo, un requerimiento de autenticación o un cambio de `robots.txt` que la prohíba, y que se me notifique,  
**Para** que el producto nunca insista ni evada restricciones de una fuente comercial y yo pueda decidir qué hacer, mientras el Benchmark 2 continúa con carga manual.

## Descripción

**Prioridad Alta (no Crítica):** solo aplica cuando existe captura automática, que no es condición de éxito del MVP. Sin embargo, es **condición obligatoria** para habilitar la captura contra cualquier fuente real.

La Adenda 2 prohíbe evadir CAPTCHA, bloqueos, autenticación u otras restricciones. Esta HU define qué condiciones se detectan durante una ejecución de captura (HU-050), qué hace el sistema al detectarlas (detener de inmediato, sin reintentos, y suspender la fuente), cómo se notifica al Administrador y cómo se reactiva una fuente suspendida. El criterio de la épica es verificable: la captura se suspende sola en una prueba que simula bloqueo o cambio de `robots.txt`.

---

## Criterios de Aceptación

### Escenario 1: Suspensión por CAPTCHA

- **Dado** que hay una ejecución de captura de Alkosto en curso
- **Cuando** una respuesta contiene un desafío CAPTCHA (ej. el texto "g-recaptcha" o "verifica que eres humano")
- **Entonces** la ejecución se detiene sin hacer ninguna otra solicitud ni reintentar, termina con estado `suspendida`, la fuente queda con `estado_captura = suspendida` y motivo `captcha`, y se notifica al Administrador

### Escenario 2: Suspensión por bloqueo

- **Dado** que hay una ejecución en curso
- **Cuando** la fuente responde 403 o 429 a cualquier solicitud
- **Entonces** se aplica la suspensión con motivo `bloqueo` y el código recibido, sin reintentos

### Escenario 3: Suspensión por requerimiento de autenticación

- **Dado** que hay una ejecución en curso
- **Cuando** la fuente responde 401 o redirige a una URL de inicio de sesión (ej. `/login`)
- **Entonces** se aplica la suspensión con motivo `autenticacion`; el sistema no intenta iniciar sesión

### Escenario 4: Suspensión por cambio de robots.txt

- **Dado** que la ejecución anterior encontró `robots.txt` permitiendo las rutas requeridas por el conector
- **Cuando** al iniciar una nueva ejecución el `robots.txt` prohíbe alguna ruta requerida (ej. `Disallow: /p/`), o responde 401 o 403
- **Entonces** no se solicita ninguna página, se aplica la suspensión con motivo `robots_txt` y se guarda el contenido y el hash del nuevo `robots.txt` como evidencia

### Escenario 5: Notificación al Administrador

- **Dado** que una fuente se suspendió
- **Cuando** se genera la notificación
- **Entonces** en un máximo de 1 hora los Administradores configurados reciben un correo con asunto `"Captura suspendida: {fuente} — {motivo}"` y cuerpo con fuente, motivo, fecha y hora, URL, código de respuesta, `id_ejecucion` y la indicación `"La carga manual y por archivo siguen disponibles. La captura no se reanudará hasta que un Administrador la reactive."`; la alerta queda además registrada y consultable en el estado de la fuente

### Escenario 6: Falla en el envío de la notificación

- **Dado** que el envío del correo falla
- **Cuando** el sistema intenta notificar
- **Entonces** reintenta cada 15 minutos hasta 4 veces; si todos fallan, la alerta queda con estado `no_entregada`, visible en el estado de la fuente, y la suspensión se mantiene

### Escenario 7: Fuente suspendida no se ejecuta

- **Dado** que Alkosto está suspendida
- **Cuando** llega la siguiente hora programada
- **Entonces** no se hace ninguna solicitud a Alkosto y se registra una ejecución `omitida` con motivo `"fuente suspendida"`; la carga manual de Alkosto sigue funcionando

### Escenario 8: Reactivación por el Administrador

- **Dado** que Alkosto está suspendida
- **Cuando** el Administrador la reactiva con la nota "Revisado: el bloqueo fue temporal; se mantiene ritmo de 1 solicitud cada 2 s"
- **Entonces** la fuente vuelve a `estado_captura = activa`, se responde `"Captura de Alkosto reactivada; se verificará robots.txt en la próxima ejecución."`, no se inicia una ejecución inmediata y la siguiente ejecución programada empieza verificando `robots.txt`; si la condición persiste, se suspende de nuevo

### Escenario 9: Reactivación inválida

- **Dado** que el Administrador intenta reactivar una fuente que no está suspendida, o sin nota válida
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"La captura de {fuente} no está suspendida."` o `"La nota de reactivación debe tener entre 10 y 500 caracteres."`

### Escenario 10: Observaciones previas a la suspensión

- **Dado** que la ejecución creó 40 observaciones antes de recibir un 429
- **Cuando** se suspende la fuente
- **Entonces** las 40 observaciones se conservan sin cambios y la ejecución registra cuántas URLs quedaron sin procesar

### Escenario 11: Usuario sin rol Administrador

- **Dado** que un Analista intenta reactivar una fuente
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (recibe la notificación y decide la reactivación).
- **Permisos requeridos:** rol Administrador para reactivar y para configurar destinatarios y marcadores.
- **Valor de negocio:** cumplimiento verificable de "cero evasión" y reducción del riesgo legal y reputacional frente a las fuentes comerciales.

### Reglas de Negocio

**RN-01 — Condiciones de suspensión.** Durante cualquier solicitud de una ejecución de captura:

| Motivo | Condición detectada |
|---|---|
| `captcha` | El cuerpo de cualquier respuesta contiene alguno de los marcadores configurables (inicial: "captcha", "recaptcha", "g-recaptcha", "hcaptcha", "cf-challenge", "challenge-platform", "verifica que eres humano", "are you a robot"), sin distinguir mayúsculas |
| `bloqueo` | Respuesta 403 o 429 |
| `autenticacion` | Respuesta 401, o redirección a una URL que coincide con los patrones de inicio de sesión configurables (inicial: "/login", "/signin", "/iniciar-sesion", "/account/login", "/my-account") |
| `robots_txt` | `robots.txt` responde 401 o 403, o prohíbe al User-Agent del producto (o al grupo `*` si no hay grupo específico) alguna ruta requerida por el conector |

Se evalúan en el orden de la tabla y se registra el primer motivo detectado.

**RN-02 — Acción inmediata.** Al detectar una condición: no se hace ninguna otra solicitud a la fuente en esa ejecución (sin reintentos, sin cambiar User-Agent, dirección, cookies ni ruta); la ejecución termina con estado `suspendida`; la fuente pasa a `estado_captura = suspendida` con `motivo_suspension`, `fecha_suspension`, `id_ejecucion`, URL y código de respuesta. Evidencia: cabeceras de la respuesta (sin cookies), los primeros 2 KB del cuerpo y, si el motivo es `robots_txt`, el contenido completo y el hash del `robots.txt`. Las observaciones creadas antes en la misma ejecución se conservan.

**RN-03 — Notificación.** Destinatarios: lista configurable de 1 a 5 correos de Administradores (inicial: el correo del PO). Plazo: entrega en ≤ 1 hora desde la suspensión (NFR-OBS-002). Asunto y cuerpo según el Escenario 5. Reintentos: cada 15 minutos, hasta 4 veces; si fallan, alerta `no_entregada`. Estados de la alerta: `pendiente` → `entregada` | `no_entregada`. Se envía una sola notificación por suspensión (no se repite por ejecuciones omitidas posteriores). La notificación no usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

**RN-04 — Persistencia de la suspensión.** Una fuente suspendida no se ejecuta en ninguna hora programada (ejecución `omitida`, motivo `"fuente suspendida"`) hasta que un Administrador la reactive. La suspensión no afecta la carga manual, la búsqueda manual ni la carga por archivo de esa fuente.

**RN-05 — Reactivación.** Solo el Administrador; requiere nota de 10 a 500 caracteres; solo sobre fuentes `suspendida`. Efecto: `estado_captura = activa`, registro de `reactivada_por`, fecha y nota; no inicia una ejecución inmediata. La siguiente ejecución programada verifica `robots.txt` antes de cualquier otra solicitud. Mensajes: `"Captura de {fuente} reactivada; se verificará robots.txt en la próxima ejecución."`, `"La captura de {fuente} no está suspendida."`, `"La nota de reactivación debe tener entre 10 y 500 caracteres."`

**RN-06 — Historial y auditoría.** Cada suspensión y reactivación queda en el historial de la fuente (motivo, fechas, usuario, nota, `id_ejecucion`, estado de la alerta) y genera un evento auditable (`suspension_captura` | `reactivacion_captura`).

**RN-07 — Configuración.** Solo el Administrador modifica marcadores de CAPTCHA (0 a 30, de 3 a 60 caracteres), patrones de inicio de sesión (0 a 20, de 2 a 100 caracteres) y destinatarios (1 a 5 correos válidos; `"Indique entre 1 y 5 correos válidos de Administradores."`). Los cambios son auditables.

**RN-08 — Prueba obligatoria.** Antes de habilitar la captura contra una fuente real, debe pasar la prueba de suspensión contra una fuente simulada para los cuatro motivos (criterio de aceptación de la épica).

### Interfaz

No requiere pantalla propia (nota del Dominio 12 del PRD). La notificación es por correo; el estado de la fuente, el historial de suspensiones y la reactivación se exponen como operaciones administrativas o consultas. El panel de estado de fuentes y el relanzamiento manual de capturas pertenecen a la épica de operación.

### Sistemas Externos (Si aplica)

- **Fuentes retail** (Alkosto, Falabella): respuestas HTTP y contenido analizados según RN-01.
- **Servicio de correo** de la plataforma: entrega correcta → `entregada`; no disponible o rechazo → reintentos y `no_entregada`.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-050 (marco de captura que invoca la suspensión), HU-051 y HU-052 (conectores y rutas requeridas), HU-047, HU-048, HU-049 (carga manual que sigue disponible).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Detección de CAPTCHA y autenticación** por marcadores y patrones configurables con valores iniciales. Resuelta (RN-01).
2. **Un solo 403 o 429 basta** para suspender (criterio conservador). Resuelta (RN-01).
3. **Canal de notificación:** correo electrónico a destinatarios configurables, con reintentos y alerta consultable. Resuelta (RN-03).
4. **Reactivación manual** con nota obligatoria y verificación de `robots.txt` en la siguiente ejecución, sin ejecución inmediata. Resuelta (RN-05).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-004 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
