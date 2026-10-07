# Historia #084: Emitir invitación de registro para un Analista

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Gestionar Acceso por Invitación  
**Prioridad:** Crítica  
**FRs relacionados:** FR-083, FR-086

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** emitir, consultar y revocar invitaciones de registro dirigidas al correo de un analista,  
**Para** que durante el discovery y el piloto solo puedan crear cuenta las personas que yo autorice, sin habilitar un registro público.

## Descripción

Durante el discovery y el piloto el registro público está deshabilitado (decisión P-12). La única forma de crear una cuenta de Analista es mediante una invitación emitida por el Administrador. Esta HU cubre el ciclo de vida de la invitación del lado del Administrador: emitirla para un correo, enviar el enlace por correo electrónico, consultar el estado de las invitaciones y revocar una invitación pendiente. El uso de la invitación para crear la cuenta (formulario de registro, contraseña y aceptación de términos y política) se cubre en HU-085.

Según la nota de implementación del Dominio 12 del PRD, esta capacidad administrativa **no requiere interfaz gráfica**: puede implementarse con una interfaz administrativa mínima, un comando o un script, siempre que se cumplan las reglas y quede trazabilidad.

---

## Criterios de Aceptación

### Escenario 1: Emitir una invitación para un correo nuevo

- **Dado** que el Administrador está autenticado, existe una versión vigente publicada de la política de tratamiento de datos y no existe cuenta ni invitación pendiente para `ana.rojas@ejemplo.org`
- **Cuando** emite una invitación para `ana.rojas@ejemplo.org`
- **Entonces** el sistema crea la invitación en estado `Pendiente`, con rol `Analista`, fecha de emisión, fecha de vencimiento (emisión + vigencia configurada, inicial 7 días) y el Administrador emisor; envía el correo de invitación con el enlace de registro; y confirma: "Invitación enviada a ana.rojas@ejemplo.org. Vence el {fecha de vencimiento}."

### Escenario 2: Correo con formato inválido o vacío

- **Dado** que el Administrador está autenticado
- **Cuando** intenta emitir una invitación con el correo vacío, sin `@`, sin dominio o con más de 254 caracteres
- **Entonces** el sistema no crea la invitación ni envía correo y muestra: "Ingresa un correo electrónico válido."

### Escenario 3: Ya existe una cuenta con ese correo

- **Dado** que existe una cuenta registrada con el correo `luis.mora@ejemplo.org`
- **Cuando** el Administrador intenta emitir una invitación para `Luis.Mora@Ejemplo.org`
- **Entonces** el sistema compara el correo normalizado, no crea la invitación ni envía correo y muestra: "Ya existe una cuenta registrada con este correo."

### Escenario 4: Reemitir una invitación a un correo con invitación pendiente

- **Dado** que existe una invitación `Pendiente` y no vencida para `ana.rojas@ejemplo.org`
- **Cuando** el Administrador emite una nueva invitación para el mismo correo
- **Entonces** el sistema cambia la invitación anterior a estado `Reemplazada` (su enlace deja de funcionar), crea una nueva invitación `Pendiente` con nueva fecha de vencimiento, envía el nuevo correo y muestra: "Invitación enviada a ana.rojas@ejemplo.org. La invitación pendiente anterior quedó reemplazada."

### Escenario 5: Falla el envío del correo

- **Dado** que el servicio de envío de correo no está disponible o rechaza el envío
- **Cuando** el Administrador emite una invitación
- **Entonces** el sistema no deja ninguna invitación nueva en estado `Pendiente` (si se iba a reemplazar una anterior, la anterior conserva su estado), registra el error en el log de aplicación y muestra: "No fue posible enviar el correo de invitación. La invitación no quedó activa; intenta de nuevo más tarde."

### Escenario 6: No hay política de tratamiento de datos publicada

- **Dado** que no existe una versión vigente publicada de la política de tratamiento de datos personales (Ley 1581 de 2012)
- **Cuando** el Administrador intenta emitir una invitación
- **Entonces** el sistema no crea la invitación y muestra: "No hay una política de tratamiento de datos publicada. Publícala antes de invitar analistas."

### Escenario 7: Consultar invitaciones

- **Dado** que existen invitaciones en distintos estados
- **Cuando** el Administrador consulta las invitaciones
- **Entonces** obtiene, ordenadas por fecha de emisión descendente, por cada invitación: correo, estado (`Pendiente`, `Usada`, `Vencida`, `Reemplazada`, `Revocada`), fecha de emisión, fecha de vencimiento, Administrador emisor y fecha de uso o revocación cuando aplique; una invitación `Pendiente` cuya fecha de vencimiento ya pasó se muestra como `Vencida`

### Escenario 8: Consultar invitaciones sin registros

- **Dado** que no se ha emitido ninguna invitación
- **Cuando** el Administrador consulta las invitaciones
- **Entonces** el sistema indica: "No hay invitaciones emitidas."

### Escenario 9: Revocar una invitación pendiente

- **Dado** que existe una invitación `Pendiente` y no vencida para `pedro.gil@ejemplo.org`
- **Cuando** el Administrador la revoca
- **Entonces** la invitación pasa a `Revocada`, su enlace deja de funcionar, se registra la fecha de revocación y el Administrador, y se muestra: "Invitación revocada." No se envía correo al invitado.

### Escenario 10: Revocar una invitación que no está pendiente

- **Dado** que una invitación está en estado `Usada`, `Vencida`, `Reemplazada` o `Revocada`
- **Cuando** el Administrador intenta revocarla
- **Entonces** el sistema no cambia su estado y muestra: "Solo se pueden revocar invitaciones pendientes."

### Escenario 11: Un usuario sin rol Administrador intenta gestionar invitaciones

- **Dado** que un usuario con rol `Analista` está autenticado, o que no hay sesión iniciada
- **Cuando** intenta emitir, consultar o revocar invitaciones
- **Entonces** el sistema rechaza la operación sin efectos; al Analista le muestra "No tienes permisos para realizar esta acción." y a quien no tiene sesión lo dirige al inicio de sesión

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO)
- **Permisos requeridos:** rol `Administrador` con sesión activa
- **Valor de negocio:** controla quién accede al producto durante el piloto (decisión P-12), protege a los analistas piloto y cumple la decisión de acceso con login sin abrir un registro público

### Reglas de Negocio

- **RN-01 — Autorización:** solo un usuario autenticado con rol `Administrador` puede emitir, consultar y revocar invitaciones.
- **RN-02 — Correo:** obligatorio; se eliminan espacios al inicio y al final y se convierte a minúsculas antes de validar y comparar; longitud máxima 254 caracteres; formato `parte-local@dominio.tld` (una sola `@`, parte local no vacía, dominio con al menos un punto y sin espacios). Si no cumple: "Ingresa un correo electrónico válido."
- **RN-03 — Cuenta existente:** si el correo normalizado ya pertenece a una cuenta registrada, no se emite la invitación ("Ya existe una cuenta registrada con este correo.").
- **RN-04 — Una invitación pendiente por correo:** emitir una invitación para un correo que ya tiene una `Pendiente` no vencida cambia la anterior a `Reemplazada` y crea una nueva. En todo momento hay como máximo una invitación `Pendiente` por correo.
- **RN-05 — Rol asignado:** toda invitación asigna el rol `Analista`. Esta HU no permite invitar Administradores; las cuentas de Administrador se aprovisionan por configuración técnica (ver HU-089).
- **RN-06 — Vigencia:** parámetro configurable `vigencia_invitacion_dias`, valor inicial **7 días**, rango permitido 1 a 30 días. La fecha de vencimiento se calcula al emitir (fecha y hora de emisión + vigencia) y no cambia si luego se modifica el parámetro.
- **RN-07 — Enlace:** el enlace contiene un token aleatorio de al menos 128 bits, no secuencial y de un solo uso. El sistema guarda solo el hash del token, nunca el token en claro. El enlace se envía únicamente por correo y no se muestra en la consulta de invitaciones.
- **RN-08 — Estados y transiciones:** `Pendiente → Usada` (al completar el registro, HU-085), `Pendiente → Vencida` (al pasar la fecha de vencimiento, evaluado al consultar o usar), `Pendiente → Reemplazada` (RN-04), `Pendiente → Revocada` (Escenario 9). `Usada`, `Vencida`, `Reemplazada` y `Revocada` son estados finales; ninguna transición sale de ellos.
- **RN-09 — Correo de invitación:** asunto "Invitación a Seguimiento Compras Públicas". Cuerpo en español con: nombre del producto, explicación breve de que es un piloto de acceso por invitación, enlace de registro, fecha y hora de vencimiento (zona horaria de Colombia, UTC−5, formato `dd/mm/aaaa hh:mm`) y el texto "Si no esperabas esta invitación, ignora este correo." No incluye datos de otros usuarios.
- **RN-10 — Atomicidad con el envío:** la invitación nueva solo queda `Pendiente` si el servicio de correo acepta el envío. Si el envío falla, no queda invitación activa y, en caso de reemisión, la invitación anterior conserva su estado.
- **RN-11 — Precondición legal (NFR-CUM-001):** no se emiten invitaciones si no existe una versión vigente publicada de la política de tratamiento de datos personales. La versión vigente es un registro configurado con identificador de versión, fecha de publicación y texto o URL del documento.
- **RN-12 — Consulta:** la lista muestra los campos del Escenario 7, ordenada por fecha de emisión descendente. Una `Pendiente` cuya fecha de vencimiento ya pasó se presenta y persiste como `Vencida`.
- **RN-13 — Auditoría:** se registran en el log de auditoría la emisión, la reemisión (con el reemplazo), la revocación y el uso de cada invitación: acción, correo invitado, Administrador que actúa (o el sistema), fecha y hora.
- **RN-14 — Fechas:** todas las fechas se almacenan con zona horaria y se muestran en hora de Colombia (UTC−5) con formato `dd/mm/aaaa hh:mm`.

### Interfaz

No requiere pantalla. Puede resolverse con una interfaz administrativa mínima, un comando o un script que permita: (1) emitir invitación indicando el correo; (2) consultar invitaciones; (3) revocar una invitación pendiente por correo o identificador. Las respuestas al Administrador son los mensajes definidos en los escenarios.

### Sistemas Externos (Si aplica)

- **Servicio de envío de correo transaccional** (proveedor definido en arquitectura): recibe destinatario, asunto y cuerpo. Respuesta aceptada → la invitación queda `Pendiente`. Error, rechazo o tiempo de espera agotado → Escenario 5.

---

## Contexto y Referencias

**Épica origen:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)

**Exclusiones de la Épica:**
- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

**Historias relacionadas:** HU-085 (registro mediante invitación), HU-089 (roles y aprovisionamiento del Administrador)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La vigencia de la invitación no estaba definida → resuelto como parámetro configurable con valor inicial de 7 días (RN-06).
- No estaba definido qué pasa al reinvitar un correo con invitación pendiente → resuelto: la nueva reemplaza a la anterior (RN-04).
- La revocación de invitaciones no estaba explícita → incluida como parte del control de la invitación por el Administrador (Escenario 9), sin agregar otras capacidades.
- Las invitaciones solo crean Analistas; el Administrador se aprovisiona por configuración (RN-05).

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
