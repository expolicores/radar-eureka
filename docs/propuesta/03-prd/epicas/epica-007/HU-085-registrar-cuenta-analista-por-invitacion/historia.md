# Historia #085: Registrar cuenta de Analista mediante invitación con aceptación de términos y política de datos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Gestionar Acceso por Invitación  
**Prioridad:** Crítica  
**FRs relacionados:** FR-083, FR-087

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** analista invitado al piloto,  
**Quiero** crear mi cuenta con correo y contraseña desde el enlace de invitación, aceptando los términos de uso y la política de tratamiento de datos personales,  
**Para** acceder al producto y guardar mis investigaciones con la tranquilidad de saber cómo se tratan mis datos.

## Descripción

El registro está disponible **solo mediante invitación** (decisión P-12): no existe registro público. El analista recibe por correo un enlace con un token de invitación emitido por el Administrador. Al abrirlo, el sistema valida la invitación y presenta el formulario de registro con el correo de la invitación prellenado y no editable. El analista define su nombre visible y su contraseña, y acepta de forma expresa, con dos casillas separadas, los términos de uso y la política de tratamiento de datos personales conforme a la Ley 1581 de 2012 (FR-087, NFR-CUM-001). El sistema guarda la prueba de la aceptación con la versión de cada documento.

Al terminar, la cuenta queda activa con rol `Analista`, la invitación queda en estado `Usada` y el analista es dirigido al inicio de sesión.

---

## Criterios de Aceptación

### Escenario 1: Registro exitoso con invitación válida

- **Dado** que existe una invitación `Pendiente` y no vencida para `ana.rojas@ejemplo.org` y hay versiones vigentes publicadas de los términos de uso y de la política de tratamiento de datos
- **Cuando** la analista abre el enlace, ingresa nombre visible "Ana Rojas", una contraseña válida, la misma confirmación, marca ambas casillas de aceptación y pulsa "Crear cuenta"
- **Entonces** el sistema crea la cuenta activa con rol `Analista`, guarda la contraseña solo como hash adaptativo, registra la aceptación de cada documento con su versión y fecha y hora, cambia la invitación a `Usada` con su fecha de uso, y redirige al inicio de sesión con el mensaje: "Tu cuenta fue creada. Inicia sesión para continuar."

### Escenario 2: Correo prellenado y no editable

- **Dado** que la analista abre un enlace de invitación válido
- **Cuando** se muestra el formulario
- **Entonces** el campo correo muestra `ana.rojas@ejemplo.org` en modo solo lectura y el sistema usa siempre el correo de la invitación, aunque se envíe otro valor en la solicitud

### Escenario 3: Enlace de invitación inválido o inexistente

- **Dado** que el token del enlace no corresponde a ninguna invitación
- **Cuando** se abre el enlace
- **Entonces** el sistema no muestra el formulario y muestra: "El enlace de invitación no es válido."

### Escenario 4: Invitación vencida

- **Dado** que la invitación está `Pendiente` pero su fecha de vencimiento ya pasó, o está en estado `Vencida`
- **Cuando** se abre el enlace o se envía el formulario
- **Entonces** el sistema no crea la cuenta, persiste la invitación como `Vencida` y muestra: "Tu invitación venció. Solicita una nueva al administrador."

### Escenario 5: Invitación ya usada

- **Dado** que la invitación está en estado `Usada`
- **Cuando** se abre el enlace
- **Entonces** el sistema no muestra el formulario y muestra: "Esta invitación ya fue usada. Inicia sesión con tu cuenta.", con un enlace al inicio de sesión

### Escenario 6: Invitación reemplazada o revocada

- **Dado** que la invitación está en estado `Reemplazada` o `Revocada`
- **Cuando** se abre el enlace
- **Entonces** el sistema no muestra el formulario y muestra: "Esta invitación ya no está activa. Solicita una nueva al administrador."

### Escenario 7: Intento de registro sin invitación

- **Dado** que una persona accede a la página de registro sin token de invitación
- **Cuando** se carga la página
- **Entonces** el sistema no muestra el formulario y muestra: "El registro solo está disponible por invitación."

### Escenario 8: Nombre visible inválido

- **Dado** que la analista está en el formulario con invitación válida
- **Cuando** envía el nombre vacío, con menos de 2 o más de 80 caracteres, o con caracteres distintos de letras (incluidas tildes y ñ), espacios, apóstrofo, punto o guion
- **Entonces** el sistema no crea la cuenta y muestra junto al campo: "Ingresa un nombre de 2 a 80 caracteres, solo con letras, espacios, apóstrofo, punto o guion."

### Escenario 9: Contraseña que no cumple la política

- **Dado** que la analista está en el formulario con invitación válida
- **Cuando** envía una contraseña con menos caracteres que el mínimo configurado (inicial 10) o con más de 128, o igual a su correo
- **Entonces** el sistema no crea la cuenta y muestra según el caso: "La contraseña debe tener entre {mínimo} y 128 caracteres." o "La contraseña no puede ser igual a tu correo."

### Escenario 10: Confirmación de contraseña distinta

- **Dado** que la analista está en el formulario con invitación válida
- **Cuando** la confirmación no coincide exactamente con la contraseña
- **Entonces** el sistema no crea la cuenta y muestra junto a la confirmación: "Las contraseñas no coinciden."

### Escenario 11: Términos o política sin aceptar

- **Dado** que la analista está en el formulario con invitación válida
- **Cuando** envía el formulario sin marcar una o ambas casillas de aceptación
- **Entonces** el sistema no crea la cuenta y muestra junto a cada casilla no marcada: "Debes aceptar los términos de uso para crear tu cuenta." y/o "Debes aceptar la política de tratamiento de datos personales para crear tu cuenta."

### Escenario 12: No hay versión vigente publicada de los términos o de la política

- **Dado** que no existe versión vigente publicada de los términos de uso o de la política de tratamiento de datos
- **Cuando** se abre un enlace de invitación válido
- **Entonces** el sistema no muestra el formulario, registra el evento en el log de aplicación y muestra: "El registro no está disponible en este momento. Intenta más tarde o contacta al administrador."

### Escenario 13: Doble envío del formulario

- **Dado** que la analista pulsa "Crear cuenta" dos veces seguidas o reenvía la solicitud
- **Cuando** el sistema procesa la segunda solicitud
- **Entonces** existe una sola cuenta para ese correo, la invitación queda `Usada` una sola vez y la segunda solicitud recibe: "Esta invitación ya fue usada. Inicia sesión con tu cuenta."

### Escenario 14: Conservar datos ante errores de validación

- **Dado** que el formulario tiene uno o más errores de validación
- **Cuando** el sistema muestra los errores
- **Entonces** conserva el nombre visible y el estado de las casillas, y borra los campos de contraseña y confirmación

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** analista invitado (sin cuenta, sin sesión)
- **Permisos requeridos:** ninguno; basta con una invitación `Pendiente` y vigente
- **Valor de negocio:** habilita el acceso controlado de los 3–5 analistas piloto y cumple la Ley 1581 de 2012 al obtener autorización expresa y verificable para el tratamiento de sus datos

### Reglas de Negocio

- **RN-01 — Solo por invitación:** el formulario de registro solo se presenta con un token que corresponda a una invitación `Pendiente` cuya fecha de vencimiento no haya pasado. No existe ninguna otra vía de alta de Analistas.
- **RN-02 — Validación del token:** el token del enlace se compara contra el hash almacenado. Resultado según estado: inexistente → Escenario 3; vencida → Escenario 4; `Usada` → Escenario 5; `Reemplazada` o `Revocada` → Escenario 6. La validación se repite al enviar el formulario, no solo al abrir el enlace.
- **RN-03 — Correo:** se toma de la invitación (ya normalizado en minúsculas). No es editable y cualquier valor de correo recibido en la solicitud se ignora.
- **RN-04 — Nombre visible:** obligatorio; se eliminan espacios al inicio y al final y los espacios internos repetidos se reducen a uno; longitud de 2 a 80 caracteres tras normalizar; caracteres permitidos: letras Unicode (incluye tildes y ñ), espacio, apóstrofo (`'`), punto (`.`) y guion (`-`).
- **RN-05 — Contraseña:** longitud mínima configurable `longitud_minima_contrasena`, valor inicial **10** (rango configurable 10 a 64); longitud máxima 128 caracteres; se permiten espacios y cualquier carácter imprimible; no puede ser igual al correo (comparación sin distinguir mayúsculas y minúsculas). No se exigen reglas adicionales de composición.
- **RN-06 — Almacenamiento de la contraseña (NFR-SEG-002):** solo se guarda el hash con un algoritmo adaptativo (bcrypt, scrypt o Argon2); nunca en texto plano ni en logs.
- **RN-07 — Confirmación:** debe ser idéntica carácter por carácter a la contraseña.
- **RN-08 — Aceptación expresa (FR-087):** dos casillas independientes, desmarcadas por defecto: "Acepto los términos de uso" y "Autorizo el tratamiento de mis datos personales según la política de tratamiento de datos". Cada una enlaza al documento de su versión vigente, que se abre sin perder lo diligenciado en el formulario. Ambas son obligatorias.
- **RN-09 — Versiones vigentes:** términos de uso y política de tratamiento de datos se manejan como documentos versionados configurados (identificador de versión, fecha de publicación, texto o URL). Debe existir exactamente una versión vigente publicada de cada uno; si falta alguna, aplica el Escenario 12 (NFR-CUM-001).
- **RN-10 — Prueba de la aceptación:** por cada documento aceptado se guarda: usuario, tipo de documento (`terminos_uso` o `politica_datos`), identificador de versión, fecha y hora de aceptación y medio (`registro_por_invitacion`). Estos registros no se modifican ni se eliminan desde la aplicación.
- **RN-11 — Datos mínimos de la cuenta:** solo se almacenan correo, nombre visible, hash de contraseña, rol, estado (`Activa`), fecha de registro y los registros de aceptación. No se piden otros datos personales.
- **RN-12 — Rol:** la cuenta recibe el rol de la invitación, que siempre es `Analista`.
- **RN-13 — Atomicidad e idempotencia:** creación de la cuenta, registros de aceptación y cambio de la invitación a `Usada` ocurren juntos o no ocurren. Si dos solicitudes llegan con la misma invitación, solo una crea la cuenta (Escenario 13).
- **RN-14 — Después del registro:** no se inicia sesión automáticamente; se redirige al inicio de sesión con el mensaje del Escenario 1.
- **RN-15 — Auditoría:** se registra en el log de auditoría el uso de la invitación (correo, fecha y hora).
- **RN-16 — Transporte:** el formulario y el enlace solo operan sobre HTTPS (NFR-SEG-001).

### Interfaz

Página pública de registro accesible solo desde el enlace de invitación, con:
- Título "Crea tu cuenta" y texto breve: "Acceso por invitación al piloto de Seguimiento Compras Públicas."
- Campos: Correo (solo lectura), Nombre visible, Contraseña (con indicación "Mínimo {mínimo} caracteres"), Confirmar contraseña.
- Dos casillas de aceptación con enlaces a los documentos vigentes.
- Botón "Crear cuenta", que se deshabilita mientras se procesa la solicitud.
- Errores junto a cada campo; páginas de error para los Escenarios 3 a 7 y 12 con el mensaje correspondiente.
- Diseño desktop-first desde 1366 × 768 px, funcional en tablet (768 px) y móvil (360 px); etiquetas asociadas a cada campo, navegación por teclado y contraste WCAG 2.1 AA.

### Sistemas Externos (Si aplica)

No aplica. El correo de invitación se envía en HU-084.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-084 (emisión de la invitación), HU-086 (inicio de sesión), HU-089 (roles)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD solo fija la longitud mínima de contraseña → resuelto: máximo 128, sin reglas de composición, distinta del correo (RN-05).
- Se pide un nombre visible para identificar al usuario en la interfaz, sin otros datos personales (minimización, RN-04 y RN-11).
- La aceptación se registra con versión del documento para que sea demostrable (RN-10); la reaceptación ante nuevas versiones no está en FR-087 y queda fuera de esta HU.
- Tras el registro no hay inicio de sesión automático (RN-14).

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
