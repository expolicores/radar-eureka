# Historia #093: Agregar notas a un caso

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Espacio de Investigación del Analista](../../../epicas.md#épica-007-espacio-de-investigación-del-analista)  
**Feature:** Documentar Casos con Notas  
**Prioridad:** Crítica  
**FRs relacionados:** FR-079

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista,  
**Quiero** escribir notas en mis casos,  
**Para** registrar mis hipótesis, hallazgos de revisión y próximos pasos mientras investigo.

## Descripción

Un caso admite varias notas de texto libre escritas por su autor (FR-079). Las notas se muestran en el detalle del caso, de la más reciente a la más antigua, con su fecha. Esta HU cubre agregar notas y el estado vacío; editar y eliminar están en HU-094. Las notas son privadas del autor del caso (NFR-SEG-004, HU-097).

---

## Criterios de Aceptación

### Escenario 1: Agregar una nota

- **Dado** que la analista está en el detalle de su caso "Compra TV 65 Gobernación"
- **Cuando** escribe "Pedir a la entidad el estudio de mercado del proceso." en "Nueva nota" y pulsa "Guardar nota"
- **Entonces** el sistema guarda la nota con su fecha y hora de creación, la muestra primera en la lista de notas, vacía el campo, actualiza la fecha de última actualización del caso y muestra: "Nota guardada."

### Escenario 2: Caso sin notas

- **Dado** que el caso no tiene notas
- **Cuando** la analista abre el detalle del caso
- **Entonces** la sección de notas muestra: "Aún no hay notas en este caso." y el campo "Nueva nota"

### Escenario 3: Nota vacía

- **Dado** que la analista está en el campo "Nueva nota"
- **Cuando** pulsa "Guardar nota" con el campo vacío o solo con espacios y saltos de línea
- **Entonces** el sistema no guarda nada y muestra: "Escribe el texto de la nota."

### Escenario 4: Nota demasiado larga

- **Dado** que la analista escribe una nota
- **Cuando** el texto supera 5.000 caracteres
- **Entonces** el contador muestra el exceso y, al intentar guardar, el sistema no guarda y muestra: "La nota admite máximo 5.000 caracteres."

### Escenario 5: Formato del texto

- **Dado** que la analista escribe una nota con varios párrafos, tildes, signos y texto con apariencia de código (por ejemplo `<b>urgente</b>`)
- **Cuando** la guarda
- **Entonces** el sistema la conserva como texto plano, mantiene los saltos de línea y la muestra literalmente, sin interpretar formato ni ejecutar código

### Escenario 6: Máximo de notas por caso

- **Dado** que el caso ya tiene 200 notas (valor inicial configurable)
- **Cuando** la analista intenta agregar otra
- **Entonces** el sistema no la guarda y muestra: "El caso alcanzó el máximo de 200 notas."

### Escenario 7: Salir con una nota sin guardar

- **Dado** que la analista escribió texto en "Nueva nota" sin guardarlo
- **Cuando** intenta salir del caso o cerrar la pestaña
- **Entonces** el sistema pide confirmación: "Tienes una nota sin guardar. ¿Deseas salir sin guardarla?"; si confirma, sale sin guardar; si cancela, permanece con el texto intacto

### Escenario 8: Falla al guardar o doble envío

- **Dado** que la analista pulsa "Guardar nota"
- **Cuando** ocurre un error interno o la solicitud se envía dos veces
- **Entonces** ante error no se guarda nada, el texto permanece en el campo, el error se registra en el log de aplicación y se muestra "No pudimos guardar la nota. Intenta de nuevo."; ante doble envío se guarda una sola nota

### Escenario 9: Nota en un caso ajeno

- **Dado** que el caso pertenece a otro usuario
- **Cuando** se intenta agregar una nota mediante una solicitud directa
- **Entonces** el sistema no guarda nada y responde: "No encontramos este caso."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa y ser autor del caso
- **Valor de negocio:** convierte el caso en un cuaderno de investigación que el analista retoma después (Journeys 1 y 2)

### Reglas de Negocio

- **RN-01 — Datos de la nota:** identificador no secuencial; caso al que pertenece; autor (el autor del caso); texto; fecha y hora de creación; fecha y hora de última edición (vacía al crear).
- **RN-02 — Texto:** obligatorio; se eliminan espacios y saltos de línea al inicio y al final para validar y guardar; longitud de 1 a 5.000 caracteres tras ese recorte; texto plano con saltos de línea; cualquier carácter Unicode imprimible.
- **RN-03 — Presentación segura:** la nota siempre se muestra como texto literal; nunca se interpreta como formato ni se ejecuta.
- **RN-04 — Orden:** las notas se listan por fecha de creación descendente, cada una con "Creada el dd/mm/aaaa hh:mm" (hora de Colombia).
- **RN-05 — Máximo de notas:** parámetro configurable `max_notas_por_caso`, inicial **200**, rango 10 a 1.000. Si se reduce por debajo de las notas de un caso, el caso conserva sus notas pero no admite nuevas.
- **RN-06 — Fecha de última actualización del caso:** se actualiza al agregar una nota.
- **RN-07 — Atomicidad e idempotencia:** la nota se guarda completa o no se guarda; un doble envío produce una sola nota.
- **RN-08 — Privacidad:** solo el autor del caso puede agregar y ver sus notas; ningún otro usuario, incluido el Administrador.
- **RN-09 — Lenguaje:** la restricción de términos prohibidos aplica a los textos generados por el sistema, no al texto que escribe el analista en sus notas privadas.

### Interfaz

- Sección "Notas" en el detalle del caso: campo multilínea "Nueva nota" con contador "{n}/5.000", botón "Guardar nota" (deshabilitado mientras se procesa) y lista de notas con su fecha.
- Estado vacío del Escenario 2; mensajes junto al campo; confirmación del Escenario 7.
- WCAG 2.1 AA (campo etiquetado, mensajes anunciados); funcional en 768 px y 360 px.

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

**Historias relacionadas:** HU-094 (editar y eliminar notas), HU-096 (detalle del caso), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Las notas son de texto plano, hasta 5.000 caracteres, con máximo configurable de 200 por caso (RN-02, RN-05).
- Las notas pertenecen al caso, no a un elemento específico del caso.

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
