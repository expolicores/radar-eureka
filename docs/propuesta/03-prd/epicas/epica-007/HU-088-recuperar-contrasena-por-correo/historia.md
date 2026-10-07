# Historia #088: Recuperar la contraseña por correo electrónico

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Autenticar y Proteger la Sesión  
**Prioridad:** Crítica  
**FRs relacionados:** FR-085

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que olvidó su contraseña,  
**Quiero** recibir en mi correo un enlace para definir una contraseña nueva,  
**Para** recuperar el acceso a mis casos sin depender del Administrador.

## Descripción

Cubre la solicitud de restablecimiento desde la página de inicio de sesión ("¿Olvidaste tu contraseña?"), el envío de un enlace de un solo uso y con vigencia limitada al correo de la cuenta, la definición de la contraseña nueva y el cierre de todas las sesiones abiertas de la cuenta. Las respuestas no revelan si un correo tiene cuenta. Aplica a cuentas de cualquier rol.

---

## Criterios de Aceptación

### Escenario 1: Solicitar el restablecimiento con un correo registrado

- **Dado** que existe la cuenta activa `ana.rojas@ejemplo.org`
- **Cuando** la analista ingresa su correo en "¿Olvidaste tu contraseña?" y pulsa "Enviar enlace"
- **Entonces** el sistema genera un enlace de restablecimiento con vigencia de 60 minutos (configurable), lo envía al correo de la cuenta y muestra: "Si el correo corresponde a una cuenta, te enviamos un enlace para restablecer tu contraseña. Revisa tu bandeja de entrada."

### Escenario 2: Solicitar con un correo sin cuenta

- **Dado** que no existe cuenta para `nadie@ejemplo.org`
- **Cuando** se solicita el restablecimiento para ese correo
- **Entonces** el sistema no envía correo y muestra exactamente el mismo mensaje del Escenario 1

### Escenario 3: Correo vacío o mal formado en la solicitud

- **Dado** que la persona está en la página de solicitud
- **Cuando** envía el correo vacío o sin formato de correo válido
- **Entonces** el sistema no procesa la solicitud y muestra: "Ingresa un correo electrónico válido."

### Escenario 4: Nueva solicitud invalida los enlaces anteriores

- **Dado** que la analista ya tiene un enlace de restablecimiento vigente
- **Cuando** solicita otro
- **Entonces** el enlace anterior deja de funcionar y solo el más reciente es válido

### Escenario 5: Límite de solicitudes

- **Dado** que para `ana.rojas@ejemplo.org` ya se enviaron 3 enlaces en la última hora (valores iniciales configurables)
- **Cuando** se hace una cuarta solicitud dentro de esa hora
- **Entonces** el sistema no envía correo ni invalida el último enlace, registra el evento en el log de aplicación y muestra el mismo mensaje del Escenario 1

### Escenario 6: Definir la contraseña nueva

- **Dado** que la analista abre un enlace vigente y no usado
- **Cuando** ingresa una contraseña nueva válida, la misma confirmación y pulsa "Guardar contraseña"
- **Entonces** el sistema reemplaza el hash de la contraseña, marca el enlace como usado, cierra todas las sesiones abiertas de la cuenta, reinicia el contador de intentos fallidos y cualquier bloqueo temporal, envía un correo de aviso de cambio de contraseña y dirige al inicio de sesión con: "Tu contraseña fue actualizada. Inicia sesión con tu nueva contraseña."

### Escenario 7: Enlace vencido, usado, reemplazado o inexistente

- **Dado** que el enlace pasó su vigencia, ya fue usado, fue reemplazado por uno más reciente o no existe
- **Cuando** se abre o se envía el formulario
- **Entonces** el sistema no cambia la contraseña y muestra: "El enlace para restablecer la contraseña no es válido o ya venció. Solicita uno nuevo.", con un enlace a la página de solicitud

### Escenario 8: Contraseña nueva inválida

- **Dado** que la analista está en el formulario con un enlace vigente
- **Cuando** la contraseña nueva tiene menos caracteres que el mínimo configurado (inicial 10) o más de 128, es igual a su correo, o la confirmación no coincide
- **Entonces** el sistema no cambia la contraseña, mantiene el enlace vigente y muestra según el caso: "La contraseña debe tener entre {mínimo} y 128 caracteres.", "La contraseña no puede ser igual a tu correo." o "Las contraseñas no coinciden."

### Escenario 9: Falla el servicio de correo

- **Dado** que el servicio de envío de correo no está disponible
- **Cuando** se solicita el restablecimiento para un correo con cuenta
- **Entonces** el sistema registra el error en el log de aplicación, no deja un enlace utilizable sin enviar y muestra el mismo mensaje del Escenario 1

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** usuario con cuenta (Analista o Administrador), sin sesión
- **Permisos requeridos:** ninguno para solicitar; un enlace vigente para restablecer
- **Valor de negocio:** evita que un analista piloto pierda acceso a sus casos y reduce la carga operativa del Administrador

### Reglas de Negocio

- **RN-01 — Correo de la solicitud:** obligatorio; se eliminan espacios al inicio y al final y se convierte a minúsculas; máximo 254 caracteres; formato `parte-local@dominio.tld` (una sola `@`, dominio con al menos un punto, sin espacios).
- **RN-02 — Respuesta neutral:** las solicitudes válidas en formato reciben siempre el mismo mensaje (Escenario 1), exista o no la cuenta, se alcance o no el límite y falle o no el envío.
- **RN-03 — Enlace:** token aleatorio de al menos 128 bits, de un solo uso; se guarda solo su hash. Vigencia configurable `vigencia_enlace_restablecimiento_minutos`, inicial **60**, rango 15 a 1.440.
- **RN-04 — Un enlace vigente por cuenta:** cada nueva solicitud enviada con éxito invalida todos los enlaces anteriores de la cuenta.
- **RN-05 — Límite de solicitudes:** configurable `max_solicitudes_restablecimiento_por_hora`, inicial **3**, rango 1 a 10, contado por correo en una ventana móvil de 60 minutos. Por encima del límite no se envía correo (Escenario 5).
- **RN-06 — Contraseña nueva:** misma política del registro: mínimo configurable `longitud_minima_contrasena` (inicial **10**), máximo 128, cualquier carácter imprimible incluido el espacio, distinta del correo (sin distinguir mayúsculas). La confirmación debe ser idéntica. Se guarda solo como hash adaptativo (bcrypt, scrypt o Argon2).
- **RN-07 — Efectos del cambio:** al guardar la contraseña nueva, en una sola operación: se reemplaza el hash, el enlace pasa a usado, se invalidan todas las sesiones de la cuenta, se reinician los intentos fallidos y cualquier bloqueo temporal. No se inicia sesión automáticamente.
- **RN-08 — Correo de restablecimiento:** asunto "Restablece tu contraseña — Seguimiento Compras Públicas"; cuerpo con enlace, vigencia en minutos y el texto "Si no solicitaste este cambio, ignora este correo; tu contraseña no cambiará."
- **RN-09 — Correo de aviso de cambio:** asunto "Tu contraseña fue cambiada — Seguimiento Compras Públicas"; cuerpo con fecha y hora del cambio (hora de Colombia, `dd/mm/aaaa hh:mm`) y "Si no fuiste tú, contacta al administrador del piloto." Si su envío falla, el cambio de contraseña se mantiene y el error se registra en el log de aplicación.
- **RN-10 — Falla del envío del enlace:** si el servicio de correo no acepta el envío, el enlace generado se invalida (Escenario 9) y no se invalidan enlaces anteriores.
- **RN-11 — Registro de eventos:** solicitudes, envíos, límites alcanzados y cambios de contraseña se registran en el log de aplicación con correo normalizado, fecha y hora, sin tokens ni contraseñas.

### Interfaz

- Página "Recuperar contraseña" (pública): campo Correo, botón "Enviar enlace", enlace "Volver a iniciar sesión".
- Página "Define tu nueva contraseña" (desde el enlace): Contraseña nueva (indicación "Mínimo {mínimo} caracteres"), Confirmar contraseña, botón "Guardar contraseña".
- Mensajes según escenarios. Desktop-first, funcional en 768 px y 360 px, WCAG 2.1 AA.

### Sistemas Externos (Si aplica)

- **Servicio de envío de correo transaccional** (proveedor definido en arquitectura): envío del enlace (RN-08) y del aviso de cambio (RN-09). Respuesta aceptada → envío exitoso; error, rechazo o tiempo de espera agotado → RN-09 o RN-10 según el correo.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-086 (inicio de sesión y bloqueo temporal), HU-087 (sesiones), HU-085 (política de contraseña)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Vigencia del enlace y límite de solicitudes no estaban definidos → resueltos como parámetros configurables (60 minutos; 3 por hora) (RN-03, RN-05).
- Cerrar todas las sesiones y avisar por correo tras el cambio se adoptan como medidas de seguridad mínimas (RN-07, RN-09).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-007 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
