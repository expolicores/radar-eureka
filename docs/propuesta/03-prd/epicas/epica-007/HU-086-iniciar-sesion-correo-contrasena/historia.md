# Historia #086: Iniciar sesión con correo y contraseña

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Autenticar y Proteger la Sesión  
**Prioridad:** Crítica  
**FRs relacionados:** FR-084

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista registrado,  
**Quiero** iniciar sesión con mi correo y mi contraseña,  
**Para** acceder a las señales, contratos y a mis casos de investigación.

## Descripción

El producto requiere login (decisión de acceso del Brief): ninguna vista del producto, salvo las páginas públicas de inicio de sesión, registro por invitación, recuperación de contraseña y documentos legales, se muestra sin sesión. Esta HU cubre el inicio de sesión con correo y contraseña para cualquier cuenta activa (rol `Analista` o `Administrador`), la protección contra intentos repetidos y la redirección a la página que el usuario intentaba abrir. El cierre de sesión y la expiración por inactividad se cubren en HU-087; la recuperación de contraseña en HU-088.

---

## Criterios de Aceptación

### Escenario 1: Inicio de sesión exitoso

- **Dado** que existe la cuenta activa `ana.rojas@ejemplo.org` con contraseña `Televisor-2026`
- **Cuando** ingresa `Ana.Rojas@Ejemplo.org ` y `Televisor-2026` y pulsa "Iniciar sesión"
- **Entonces** el sistema normaliza el correo, valida la contraseña contra su hash, crea una sesión nueva, registra la fecha y hora del último acceso y dirige al usuario a la página de inicio del producto (lista priorizada de señales)

### Escenario 2: Redirección a la página solicitada

- **Dado** que el usuario sin sesión intentó abrir una página protegida del producto (por ejemplo, la ficha de un contrato o "Mis casos")
- **Cuando** el sistema lo dirige al inicio de sesión y el usuario inicia sesión correctamente
- **Entonces** el sistema lo lleva a la página que había solicitado

### Escenario 3: Acceso a página protegida sin sesión

- **Dado** que no hay sesión iniciada
- **Cuando** se intenta abrir cualquier página o recurso protegido
- **Entonces** el sistema no muestra ningún dato y dirige al inicio de sesión con el mensaje: "Inicia sesión para continuar."

### Escenario 4: Credenciales incorrectas

- **Dado** que el correo no corresponde a ninguna cuenta, o la contraseña no coincide
- **Cuando** el usuario intenta iniciar sesión
- **Entonces** el sistema no crea sesión, muestra el mismo mensaje en ambos casos: "Correo o contraseña incorrectos." y conserva el correo ingresado, borrando la contraseña

### Escenario 5: Campos vacíos

- **Dado** que el usuario está en la página de inicio de sesión
- **Cuando** pulsa "Iniciar sesión" con el correo o la contraseña vacíos
- **Entonces** el sistema no intenta autenticar y muestra: "Ingresa tu correo y tu contraseña."

### Escenario 6: Bloqueo temporal por intentos fallidos

- **Dado** que para el correo `ana.rojas@ejemplo.org` se han registrado 5 intentos fallidos dentro de los últimos 15 minutos (valores iniciales configurables)
- **Cuando** se intenta iniciar sesión otra vez con ese correo, aunque la contraseña sea correcta
- **Entonces** el sistema no crea sesión y muestra: "Demasiados intentos fallidos. Intenta de nuevo en {minutos restantes} minutos o recupera tu contraseña."

### Escenario 7: Fin del bloqueo temporal

- **Dado** que pasaron los 15 minutos de bloqueo
- **Cuando** el usuario inicia sesión con la contraseña correcta
- **Entonces** el sistema crea la sesión y reinicia el contador de intentos fallidos

### Escenario 8: Usuario con sesión activa abre el inicio de sesión

- **Dado** que el usuario ya tiene una sesión activa
- **Cuando** abre la página de inicio de sesión
- **Entonces** el sistema lo dirige a la página de inicio del producto sin pedir credenciales

### Escenario 9: Redirección a una dirección externa

- **Dado** que la solicitud de inicio de sesión trae como página de destino una dirección de otro sitio
- **Cuando** el usuario inicia sesión correctamente
- **Entonces** el sistema ignora ese destino y lo lleva a la página de inicio del producto

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista o Administrador con cuenta activa
- **Permisos requeridos:** ninguno para la página de inicio de sesión; una cuenta en estado `Activa` para autenticarse
- **Valor de negocio:** habilita el acceso con login, requisito para que cada analista tenga su espacio privado de investigación (Journeys 1 y 2)

### Reglas de Negocio

- **RN-01 — Credenciales:** correo (se eliminan espacios al inicio y al final y se convierte a minúsculas) y contraseña (se usa tal cual, sin recortar). Ambos obligatorios (Escenario 5).
- **RN-02 — Verificación:** la contraseña se compara contra el hash adaptativo almacenado. Nunca se registra la contraseña en logs ni se devuelve en respuestas.
- **RN-03 — Mensaje genérico:** el error de credenciales es idéntico para correo inexistente y contraseña errada, para no revelar qué correos tienen cuenta.
- **RN-04 — Bloqueo temporal:** parámetros configurables `max_intentos_fallidos` (inicial **5**, rango 3 a 20), `ventana_intentos_minutos` (inicial **15**, rango 5 a 60) y `duracion_bloqueo_minutos` (inicial **15**, rango 5 a 60). Al alcanzar el máximo de intentos fallidos para un mismo correo dentro de la ventana, ese correo queda bloqueado durante la duración configurada. Los intentos con correo inexistente también cuentan, con el mismo mensaje, para no revelar si existe la cuenta. Los minutos restantes se muestran redondeados hacia arriba (mínimo 1). Un inicio de sesión exitoso reinicia el contador.
- **RN-05 — Sesión:** al autenticarse se crea un identificador de sesión nuevo (nunca se reutiliza uno previo), transmitido solo por HTTPS y no accesible desde scripts de la página. Se permiten sesiones simultáneas del mismo usuario en distintos dispositivos. La expiración por inactividad se rige por HU-087 (inicial 30 minutos, configurable).
- **RN-06 — Página de inicio por defecto:** la lista priorizada de señales, para cualquier rol.
- **RN-07 — Destino seguro:** solo se redirige a rutas internas del propio producto; cualquier otro destino se ignora (Escenario 9).
- **RN-08 — Páginas públicas:** sin sesión solo son accesibles: inicio de sesión, registro por invitación, solicitud y restablecimiento de contraseña, términos de uso y política de tratamiento de datos. Todo lo demás exige sesión (Escenario 3).
- **RN-09 — Registro de eventos:** cada intento (exitoso o fallido) se registra en el log de aplicación con correo normalizado, resultado, fecha y hora, sin contraseña. El último acceso exitoso se guarda en la cuenta.
- **RN-10 — Sin registro público:** la página no ofrece enlace de "registrarse"; muestra el texto "El acceso es por invitación."

### Interfaz

Página "Iniciar sesión" con: campo Correo, campo Contraseña (enmascarado, con opción de mostrar), botón "Iniciar sesión" (deshabilitado mientras se procesa), enlace "¿Olvidaste tu contraseña?" (HU-088) y texto "El acceso es por invitación.". Enlaces a términos de uso y política de tratamiento de datos al pie. Mensajes de error sobre el formulario. Desktop-first desde 1366 × 768 px, funcional en 768 px y 360 px; navegación por teclado y contraste WCAG 2.1 AA.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-085 (registro), HU-087 (cierre de sesión y expiración), HU-088 (recuperación de contraseña), HU-089 (roles)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD no define protección ante intentos repetidos; se incluye un bloqueo temporal configurable (5 intentos / 15 minutos / 15 minutos de bloqueo) como control mínimo para la revisión OWASP Top 10 exigida por NFR-SEG-008 (RN-04).
- La página de inicio por defecto es la lista priorizada de señales, primer paso del Journey 1 (RN-06).
- Se permiten sesiones simultáneas del mismo usuario (RN-05).

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
