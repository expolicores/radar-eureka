# Historia #097: Restringir el acceso a casos, elementos y notas únicamente a su autor

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Consultar y Retomar Casos Propios  
**Prioridad:** Crítica  
**FRs relacionados:** FR-082

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** que solo yo pueda ver y modificar mis casos, sus elementos y mis notas,  
**Para** investigar con confidencialidad, sin que otros usuarios, ni siquiera el Administrador, conozcan mis hipótesis o lo que estoy revisando.

## Descripción

FR-082 y NFR-SEG-004 exigen que los casos y notas sean accesibles solo por su autor, verificado con pruebas de autorización en el **100 %** de los puntos de acceso a casos. Esta HU establece la regla transversal de privacidad para toda operación sobre casos, elementos guardados (instantáneas) y notas, la respuesta uniforme que no revela la existencia de casos ajenos, la imposibilidad de adivinar identificadores, el registro de intentos denegados y la suite automática de pruebas de autorización. El MVP no tiene casos compartidos ni colaboración (exclusión de la épica).

---

## Criterios de Aceptación

### Escenario 1: El autor accede a sus casos

- **Dado** que la analista `ana.rojas@ejemplo.org` es autora del caso "Compra TV 65 Gobernación"
- **Cuando** lista, abre, guarda elementos o gestiona notas de ese caso
- **Entonces** el sistema permite cada operación

### Escenario 2: Otro Analista intenta acceder a un caso ajeno

- **Dado** que `luis.mora@ejemplo.org` conoce o adivina el identificador del caso de Ana
- **Cuando** intenta abrirlo, ver sus elementos o notas, guardar un elemento, o agregar, editar o eliminar una nota
- **Entonces** el sistema no ejecuta nada, no devuelve ningún dato del caso y responde "No encontramos este caso.", igual que para un caso inexistente

### Escenario 3: El Administrador intenta acceder a un caso de un Analista

- **Dado** que el Administrador `admin.po@ejemplo.org` tiene sesión activa
- **Cuando** intenta cualquier operación sobre el caso de Ana desde el producto
- **Entonces** el sistema responde igual que en el Escenario 2; el rol `Administrador` no otorga acceso a casos ajenos

### Escenario 4: Recursos derivados del caso

- **Dado** que existen la instantánea de una señal guardada en el caso de Ana y una nota de ese caso
- **Cuando** otro usuario solicita directamente la instantánea o la nota por su propio identificador
- **Entonces** el sistema responde "No encontramos este caso." sin revelar datos

### Escenario 5: Sin sesión

- **Dado** que no hay sesión iniciada
- **Cuando** llega cualquier solicitud sobre casos, elementos o notas
- **Entonces** el sistema no ejecuta nada y dirige al inicio de sesión con "Inicia sesión para continuar."

### Escenario 6: Los casos ajenos no aparecen en ningún listado ni conteo

- **Dado** que Luis tiene 2 casos
- **Cuando** Ana usa "Mis casos" o el selector de "Guardar en caso"
- **Entonces** no aparece ningún caso de Luis ni se cuenta en los totales

### Escenario 7: Registro de intentos denegados

- **Dado** que un usuario autenticado intenta acceder a un caso que no es suyo
- **Cuando** el sistema deniega la solicitud
- **Entonces** registra en el log de aplicación: usuario solicitante, operación, identificador solicitado, fecha y hora, sin incluir contenido del caso

### Escenario 8: Suite automática de autorización

- **Dado** que existe la suite de pruebas de autorización de casos
- **Cuando** se ejecuta en cada entrega
- **Entonces** recorre el 100 % de las operaciones sobre casos, elementos y notas con tres perfiles (autor, otro Analista, Administrador no autor) además de sin sesión, y falla si algún perfil no autor obtiene datos o produce efectos

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); cualquier usuario (sujeto al control)
- **Permisos requeridos:** ser autor del caso para cualquier operación sobre él
- **Valor de negocio:** confidencialidad de las investigaciones, condición para que analistas reales usen el piloto; cumple NFR-SEG-004 y uno de los criterios de aceptación de la épica

### Reglas de Negocio

- **RN-01 — Regla de autoría:** el autor de un caso es el usuario que lo creó y no cambia nunca. Toda operación sobre un caso, sus elementos o sus notas exige que el usuario de la sesión sea el autor. No hay excepciones por rol.
- **RN-02 — Operaciones cubiertas:** listar casos; abrir el detalle; ver el contenido de una instantánea; abrir la copia de un documento desde un caso; crear caso; guardar elementos; agregar, editar y eliminar notas; y cualquier operación futura sobre casos.
- **RN-03 — Control en el servidor:** la verificación de autoría se hace en el servidor en cada operación, a partir de la sesión, y nunca a partir de datos enviados por el navegador (como un parámetro de autor).
- **RN-04 — Respuesta uniforme:** para un caso ajeno o inexistente (y sus elementos y notas) la respuesta es idéntica: "No encontramos este caso.", con el mismo código de respuesta y sin datos parciales, de modo que no pueda inferirse si el caso existe.
- **RN-05 — Identificadores:** los identificadores de casos, elementos y notas son aleatorios (al menos 122 bits), no secuenciales ni derivados de datos del caso.
- **RN-06 — Sin efectos:** una operación denegada no deja ningún cambio, ni parcial.
- **RN-07 — Registro:** los intentos denegados de usuarios autenticados se registran según el Escenario 7. Los logs no contienen títulos, descripciones, notas ni contenido de instantáneas.
- **RN-08 — Acceso técnico:** fuera del producto, el acceso a los datos de casos queda limitado a la operación técnica (respaldos y recuperación); no existe consulta ni reporte de casos de analistas en las funciones del Administrador.
- **RN-09 — Indicadores agregados:** si alguna función calcula indicadores sobre casos (por ejemplo, para KPIs), solo usa conteos agregados sin títulos, notas ni contenido.
- **RN-10 — Verificación:** la suite de autorización del Escenario 8 es obligatoria y debe pasar al 100 % antes de cada entrega a usuarios piloto.

### Interfaz

No agrega pantallas. Usa la página "No encontramos este caso." con enlace a "Mis casos" para las respuestas denegadas en vistas, y el mismo mensaje en operaciones.

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

**Historias relacionadas:** HU-089 (roles), HU-090 a HU-096 (operaciones sobre casos y notas)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El Administrador tampoco accede a casos ajenos desde el producto (RN-01, RN-08).
- La respuesta a casos ajenos es idéntica a la de casos inexistentes para no revelar su existencia (RN-04).
- Los indicadores sobre casos, si existen, solo usan conteos agregados (RN-09).

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
