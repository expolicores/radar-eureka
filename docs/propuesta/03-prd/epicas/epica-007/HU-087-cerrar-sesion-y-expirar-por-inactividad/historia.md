# Historia #087: Cerrar sesión y expirar la sesión por inactividad

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Autenticar y Proteger la Sesión  
**Prioridad:** Crítica  
**FRs relacionados:** FR-084

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista con sesión iniciada,  
**Quiero** cerrar mi sesión cuando termino y que el sistema la cierre solo si la dejo inactiva,  
**Para** que nadie más pueda ver mis casos y notas desde el equipo que usé.

## Descripción

Cubre el cierre de sesión voluntario (FR-084) y la expiración automática de la sesión tras un tiempo de inactividad configurable, con valor inicial de 30 minutos (NFR-SEG-003, decisión P-12). Antes de expirar, el sistema avisa al usuario para que pueda seguir conectado y no pierda lo que está escribiendo. Aplica a cualquier cuenta (Analista o Administrador). El inicio de sesión está en HU-086.

---

## Criterios de Aceptación

### Escenario 1: Cerrar sesión

- **Dado** que la analista tiene una sesión activa
- **Cuando** pulsa "Cerrar sesión" en el menú de usuario
- **Entonces** el sistema invalida la sesión en el servidor, elimina la referencia de sesión del navegador y muestra la página de inicio de sesión con el mensaje: "Cerraste sesión."

### Escenario 2: Volver atrás después de cerrar sesión

- **Dado** que la analista cerró sesión
- **Cuando** usa el botón "atrás" del navegador o abre una dirección protegida que tenía abierta
- **Entonces** el sistema no muestra datos protegidos (ni desde la caché del navegador) y dirige al inicio de sesión con: "Inicia sesión para continuar."

### Escenario 3: Uso de un identificador de sesión cerrado

- **Dado** que una sesión fue cerrada
- **Cuando** llega una solicitud con el identificador de esa sesión
- **Entonces** el sistema la rechaza como no autenticada y no ejecuta ninguna acción

### Escenario 4: Aviso previo a la expiración

- **Dado** que la analista no ha realizado ninguna acción durante 28 minutos (tiempo de inactividad configurado 30, aviso configurado 2 minutos antes)
- **Cuando** se cumple el minuto 28 de inactividad
- **Entonces** el sistema muestra un aviso: "Tu sesión se cerrará en 2 minutos por inactividad." con el botón "Seguir conectado"

### Escenario 5: Seguir conectado desde el aviso

- **Dado** que se muestra el aviso de expiración
- **Cuando** la analista pulsa "Seguir conectado" antes de que se cumplan los 30 minutos
- **Entonces** el sistema reinicia el contador de inactividad, oculta el aviso y la analista continúa donde estaba, sin perder lo escrito en la página

### Escenario 6: Expiración por inactividad

- **Dado** que la analista no realizó ninguna acción durante 30 minutos
- **Cuando** se cumple el tiempo de inactividad
- **Entonces** el sistema invalida la sesión en el servidor y la página abierta pasa al inicio de sesión con el mensaje: "Tu sesión expiró por inactividad. Inicia sesión de nuevo."; al volver a iniciar sesión, la analista regresa a la página donde estaba

### Escenario 7: Acción enviada con la sesión ya expirada

- **Dado** que la sesión expiró (por ejemplo, con el equipo suspendido, sin que la página mostrara el aviso)
- **Cuando** la analista intenta guardar o consultar algo
- **Entonces** el sistema no ejecuta la acción, no guarda datos parciales y dirige al inicio de sesión con el mensaje: "Tu sesión expiró por inactividad. Inicia sesión de nuevo."

### Escenario 8: La actividad reinicia el contador

- **Dado** que la analista lleva 25 minutos sin actividad
- **Cuando** abre una ficha, aplica un filtro, guarda una nota o realiza cualquier otra acción propia
- **Entonces** el contador de inactividad vuelve a cero

### Escenario 9: Cambio del tiempo de inactividad configurado

- **Dado** que el Administrador cambia `tiempo_inactividad_sesion_minutos` de 30 a 60
- **Cuando** se evalúa la inactividad de cualquier sesión después del cambio
- **Entonces** se aplica el nuevo valor, también a las sesiones ya abiertas

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista o Administrador con sesión activa
- **Permisos requeridos:** sesión activa
- **Valor de negocio:** protege los casos y notas privados (NFR-SEG-003, NFR-SEG-004) en equipos compartidos o desatendidos

### Reglas de Negocio

- **RN-01 — Cierre de sesión:** invalida en el servidor solo la sesión actual; las sesiones del mismo usuario en otros dispositivos siguen activas.
- **RN-02 — Páginas protegidas sin caché:** las respuestas con datos protegidos se marcan para que el navegador no las guarde ni las muestre desde caché tras cerrar o expirar la sesión.
- **RN-03 — Tiempo de inactividad:** parámetro configurable `tiempo_inactividad_sesion_minutos`, valor inicial **30**, rango permitido 5 a 480. Los valores fuera de rango se rechazan al configurar y se conserva el valor anterior.
- **RN-04 — Aviso previo:** parámetro configurable `aviso_expiracion_minutos`, valor inicial **2**, rango 1 a 10 y siempre menor que el tiempo de inactividad. El aviso indica los minutos restantes con el texto "Tu sesión se cerrará en {n} minutos por inactividad."
- **RN-05 — Qué es actividad:** cualquier acción iniciada por el usuario que llegue al servidor (navegar, buscar, filtrar, abrir, guardar, pulsar "Seguir conectado"). Las consultas automáticas de fondo que la página haga sin intervención del usuario no reinician el contador.
- **RN-06 — Expiración:** al cumplirse el tiempo de inactividad la sesión se invalida en el servidor, aunque el navegador esté cerrado. Cualquier solicitud posterior con esa sesión se trata como no autenticada (Escenario 7).
- **RN-07 — Contenido no guardado:** lo escrito y no guardado antes de la expiración no se conserva; el aviso previo (RN-04) es el mecanismo para evitarlo. Una acción de guardar que llega con la sesión expirada no guarda nada (ni parcialmente).
- **RN-08 — Regreso tras expiración:** tras iniciar sesión de nuevo, el usuario vuelve a la página interna donde estaba cuando expiró la sesión.
- **RN-09 — Cambio de parámetros:** los cambios en RN-03 y RN-04 se aplican desde la siguiente evaluación a todas las sesiones, incluidas las abiertas.
- **RN-10 — Registro de eventos:** cierres de sesión y expiraciones se registran en el log de aplicación con usuario, tipo de evento (`cierre` o `expiracion`), fecha y hora.

### Interfaz

- Menú de usuario visible en todas las páginas protegidas con el nombre visible del usuario y la opción "Cerrar sesión".
- Aviso de expiración modal, accesible por teclado y anunciado por lectores de pantalla, con el texto de RN-04 y el botón "Seguir conectado".
- Mensajes en la página de inicio de sesión: "Cerraste sesión." y "Tu sesión expiró por inactividad. Inicia sesión de nuevo."
- Configuración de los parámetros por el Administrador mediante configuración técnica o interfaz administrativa mínima (no requiere pantalla).

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

**Historias relacionadas:** HU-086 (inicio de sesión), HU-088 (recuperación de contraseña, que cierra todas las sesiones)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD fija 30 minutos configurables, pero no el rango ni el aviso previo → resuelto: rango 5 a 480 minutos y aviso configurable de 2 minutos (RN-03, RN-04) para no perder notas en edición.
- Qué cuenta como actividad no estaba definido → resuelto en RN-05.
- Cerrar sesión no afecta otras sesiones del mismo usuario (RN-01).

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
