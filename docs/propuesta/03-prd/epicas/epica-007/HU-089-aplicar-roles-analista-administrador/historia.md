# Historia #089: Aplicar los roles Analista y Administrador con permisos diferenciados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Autenticar y Proteger la Sesión  
**Prioridad:** Crítica  
**FRs relacionados:** FR-086

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que cada cuenta tenga un rol (Analista o Administrador) y que el sistema permita o niegue cada operación según ese rol,  
**Para** que los analistas piloto usen el producto sin acceder a la operación, la configuración ni la revisión humana de datos.

## Descripción

El PRD define dos actores: **Analista** (investiga contratación pública) y **Administrador** (opera fuentes, calidad, revisión humana y carga manual; en el MVP es el PO, que también actúa como Revisor, decisión P-08). Esta HU establece el modelo de roles, la matriz de permisos por grupo de funciones, el aprovisionamiento de cuentas de Administrador por configuración técnica y el control de autorización en el servidor para toda operación. Las funciones administrativas concretas se construyen en sus propias historias; esta HU garantiza que solo el rol `Administrador` pueda ejecutarlas.

Los casos y notas son privados de su autor (FR-082); ningún rol, ni siquiera `Administrador`, accede a casos ajenos. Esa regla se detalla en HU-097.

---

## Criterios de Aceptación

### Escenario 1: Toda cuenta tiene exactamente un rol

- **Dado** que se crea una cuenta por invitación o por aprovisionamiento técnico
- **Cuando** queda registrada
- **Entonces** tiene exactamente un rol: `Analista` (cuentas creadas por invitación) o `Administrador` (cuentas aprovisionadas como tales); nunca queda sin rol ni con ambos

### Escenario 2: Analista usa las funciones de investigación

- **Dado** que la analista `ana.rojas@ejemplo.org` tiene rol `Analista` y sesión activa
- **Cuando** busca y filtra contratos, abre fichas y señales, califica una señal, reporta un error o gestiona sus casos y notas
- **Entonces** el sistema permite cada operación

### Escenario 3: Analista intenta una función administrativa

- **Dado** que la analista tiene rol `Analista`
- **Cuando** intenta, desde la interfaz o con una solicitud directa, ejecutar una función administrativa (por ejemplo, emitir una invitación, cambiar un parámetro de configuración, relanzar una ingesta, corregir un dato extraído en la cola de revisión, registrar una observación manual de precio o consultar KPIs o el log de auditoría)
- **Entonces** el sistema rechaza la operación sin ningún efecto, responde "No tienes permisos para realizar esta acción." y registra el intento denegado en el log de aplicación

### Escenario 4: La interfaz del Analista no muestra opciones administrativas

- **Dado** que la analista tiene rol `Analista`
- **Cuando** navega por el producto
- **Entonces** no ve menús, botones ni enlaces hacia funciones administrativas

### Escenario 5: Administrador usa funciones administrativas y de investigación

- **Dado** que `admin.po@ejemplo.org` tiene rol `Administrador` y sesión activa
- **Cuando** ejecuta una función administrativa o una de investigación (explorar, abrir señales, crear sus propios casos)
- **Entonces** el sistema permite la operación

### Escenario 6: Administrador intenta abrir el caso de un Analista

- **Dado** que la analista `ana.rojas@ejemplo.org` tiene un caso
- **Cuando** el Administrador intenta consultarlo o modificarlo
- **Entonces** el sistema lo trata como inexistente para él y responde "No encontramos este caso." sin revelar ningún dato

### Escenario 7: Aprovisionar o cambiar el rol de una cuenta por configuración técnica

- **Dado** que una persona con acceso técnico a la operación del sistema ejecuta el procedimiento de aprovisionamiento
- **Cuando** crea una cuenta de Administrador o cambia el rol de una cuenta existente
- **Entonces** el cambio se aplica desde la siguiente solicitud de esa cuenta (incluidas sus sesiones abiertas) y queda en el log de auditoría con cuenta, rol anterior, rol nuevo, responsable, fecha y hora

### Escenario 8: No se puede dejar el sistema sin Administrador

- **Dado** que existe una sola cuenta con rol `Administrador`
- **Cuando** se intenta cambiar su rol a `Analista`
- **Entonces** el procedimiento rechaza el cambio con el mensaje "Debe existir al menos una cuenta con rol Administrador." y el rol no cambia

### Escenario 9: Solicitud sin sesión a una función protegida

- **Dado** que no hay sesión iniciada
- **Cuando** llega una solicitud a cualquier función de investigación o administrativa
- **Entonces** el sistema no ejecuta nada y dirige al inicio de sesión con "Inicia sesión para continuar."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (configura); Analista y Administrador (sujetos al control)
- **Permisos requeridos:** acceso técnico a la operación del sistema para aprovisionar o cambiar roles
- **Valor de negocio:** separa la operación y la revisión de datos (PO) del uso del producto por los analistas piloto, y protege la integridad de los datos y la configuración

### Reglas de Negocio

- **RN-01 — Roles:** valores permitidos `Analista` y `Administrador`. Un rol por cuenta, obligatorio.
- **RN-02 — Matriz de permisos:**

  | Grupo de funciones | Analista | Administrador |
  |---|---|---|
  | Exploración, búsqueda y filtros de contratos e ítems; lista de señales; ficha de contrato; detalle de señal y evidencia | Sí | Sí |
  | Calificar una señal; reportar un error en un dato o señal | Sí | Sí |
  | Casos y notas **propios** (crear, guardar elementos, notas, listar, abrir) | Sí | Sí |
  | Casos y notas de **otros usuarios** | No | No |
  | Invitaciones de registro | No | Sí |
  | Estado de fuentes y relanzar ingestas o capturas | No | Sí |
  | Configuración de parámetros analíticos y operativos (incluidos los de sesión, contraseña e invitación) | No | Sí |
  | Cola de revisión humana; corrección de clasificación y de datos extraídos; gestión de errores reportados | No | Sí |
  | Registro manual y carga semiautomática de observaciones de precio | No | Sí |
  | Muestra de validación, KPIs y log de auditoría | No | Sí |

- **RN-03 — Control en el servidor:** toda operación verifica en el servidor la sesión y el rol antes de ejecutarse; ocultar opciones en la interfaz no sustituye este control. Una operación denegada no produce ningún efecto (ni parcial).
- **RN-04 — Respuesta a operación no permitida:** con sesión y sin el rol requerido → "No tienes permisos para realizar esta acción."; sin sesión → inicio de sesión con "Inicia sesión para continuar."; recursos de casos y notas ajenos → "No encontramos este caso." (no se revela su existencia).
- **RN-05 — Funciones nuevas:** toda función que se agregue debe declarar su grupo en la matriz de RN-02; una función sin grupo declarado se trata como administrativa (solo `Administrador`).
- **RN-06 — Aprovisionamiento:** las cuentas de Administrador se crean y los roles se cambian solo mediante un procedimiento técnico (script, comando o configuración) ejecutado por quien opera la infraestructura; no existe pantalla para ello ni se puede hacer por invitación. La cuenta de Administrador aprovisionada cumple la misma política de contraseña del producto (mínimo configurable, inicial 10 caracteres; máximo 128; hash adaptativo).
- **RN-07 — Mínimo de Administradores:** siempre debe existir al menos una cuenta con rol `Administrador` (Escenario 8).
- **RN-08 — Vigencia del cambio de rol:** se aplica desde la siguiente solicitud de la cuenta, sin necesidad de que cierre sesión.
- **RN-09 — Auditoría:** cambios de rol y aprovisionamiento de Administradores se registran en el log de auditoría (RN del Escenario 7). Los intentos denegados se registran en el log de aplicación con usuario, operación, fecha y hora.
- **RN-10 — Verificación automática:** existen pruebas automáticas de autorización que recorren todas las funciones del producto con los tres perfiles (sin sesión, `Analista`, `Administrador`) y verifican el resultado esperado de la matriz.

### Interfaz

- El menú de usuario muestra el rol de la cuenta ("Analista" o "Administrador") junto al nombre visible.
- Las opciones administrativas que tengan interfaz solo se muestran al rol `Administrador`.
- El aprovisionamiento y cambio de rol no tiene pantalla (RN-06).

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

**Historias relacionadas:** HU-084 (invitaciones, solo Administrador), HU-085 (registro con rol Analista), HU-097 (privacidad de casos)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El Administrador también puede usar las funciones de investigación (el PO actúa como analista al probar), pero no ve casos ajenos (RN-02).
- El aprovisionamiento de Administradores y el cambio de rol se hacen por procedimiento técnico, sin pantalla (RN-06), conforme a la nota del Dominio 12.
- Se exige al menos un Administrador (RN-07) y las funciones no clasificadas se tratan como administrativas (RN-05).

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
