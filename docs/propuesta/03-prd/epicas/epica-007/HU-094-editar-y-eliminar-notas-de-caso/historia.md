# Historia #094: Editar y eliminar notas de un caso

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
**Quiero** editar o eliminar las notas de mis casos,  
**Para** mantener mis apuntes al día cuando cambia mi entendimiento del caso o cuando una nota ya no sirve.

## Descripción

Completa FR-079: además de agregar notas (HU-093), el autor del caso puede editar el texto de una nota existente o eliminarla de forma definitiva, con confirmación. Las notas editadas muestran la fecha de su última edición. Solo el autor del caso puede hacerlo (NFR-SEG-004). Las notas son apuntes privados del analista; no forman parte de las instantáneas de evidencia, que nunca se modifican.

---

## Criterios de Aceptación

### Escenario 1: Editar una nota

- **Dado** que la analista tiene en su caso la nota "Pedir el estudio de mercado." creada el 01/10/2026 09:00
- **Cuando** pulsa "Editar" en esa nota, cambia el texto a "Estudio de mercado solicitado el 02/10." y pulsa "Guardar cambios"
- **Entonces** el sistema reemplaza el texto, conserva la fecha de creación, registra la fecha y hora de edición, muestra en la nota "Creada el 01/10/2026 09:00 · Editada el 02/10/2026 11:00", mantiene la posición de la nota en la lista, actualiza la fecha de última actualización del caso y muestra: "Nota actualizada."

### Escenario 2: Cancelar la edición

- **Dado** que la analista está editando una nota
- **Cuando** pulsa "Cancelar"
- **Entonces** la nota conserva su texto y sus fechas originales

### Escenario 3: Edición inválida

- **Dado** que la analista está editando una nota
- **Cuando** deja el texto vacío (o solo espacios y saltos de línea) o supera 5.000 caracteres
- **Entonces** el sistema no guarda los cambios y muestra según el caso: "Escribe el texto de la nota." o "La nota admite máximo 5.000 caracteres."

### Escenario 4: Guardar sin cambios

- **Dado** que la analista abrió la edición de una nota
- **Cuando** pulsa "Guardar cambios" sin modificar el texto
- **Entonces** el sistema cierra la edición sin registrar fecha de edición ni actualizar el caso

### Escenario 5: Eliminar una nota con confirmación

- **Dado** que la analista tiene una nota en su caso
- **Cuando** pulsa "Eliminar" y confirma en el diálogo "¿Eliminar esta nota? Esta acción no se puede deshacer."
- **Entonces** el sistema elimina la nota de forma definitiva, la quita de la lista, actualiza la fecha de última actualización del caso y muestra: "Nota eliminada."

### Escenario 6: Cancelar la eliminación

- **Dado** que se muestra el diálogo de confirmación de eliminación
- **Cuando** la analista pulsa "Cancelar"
- **Entonces** la nota no se elimina

### Escenario 7: Eliminar la última nota

- **Dado** que el caso tiene una sola nota
- **Cuando** la analista la elimina
- **Entonces** la sección de notas muestra: "Aún no hay notas en este caso."

### Escenario 8: La nota cambió en otra pestaña o dispositivo

- **Dado** que la analista abrió la edición de una nota y, mientras tanto, la editó o eliminó desde otra sesión
- **Cuando** guarda los cambios o intenta eliminarla
- **Entonces** el sistema no sobrescribe ni elimina, y muestra: "Esta nota cambió o fue eliminada desde que la abriste. Recarga el caso para ver la versión actual."; el texto que estaba editando permanece en el campo para que pueda copiarlo

### Escenario 9: Editar o eliminar una nota de un caso ajeno

- **Dado** que la nota pertenece a un caso de otro usuario
- **Cuando** se intenta editarla o eliminarla mediante una solicitud directa
- **Entonces** el sistema no hace ningún cambio y responde: "No encontramos este caso."

### Escenario 10: Falla al guardar o eliminar

- **Dado** que la analista guarda una edición o confirma una eliminación
- **Cuando** ocurre un error interno
- **Entonces** la nota queda como estaba, el error se registra en el log de aplicación y se muestra "No pudimos guardar los cambios. Intenta de nuevo." o "No pudimos eliminar la nota. Intenta de nuevo."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (también el Administrador, sobre sus propios casos)
- **Permisos requeridos:** sesión activa y ser autor del caso
- **Valor de negocio:** mantiene el caso como un registro vigente y útil de la investigación (Journey 2)

### Reglas de Negocio

- **RN-01 — Texto editado:** mismas reglas que al crear: se eliminan espacios y saltos de línea al inicio y al final; 1 a 5.000 caracteres; texto plano con saltos de línea; se muestra siempre de forma literal, sin interpretar formato ni ejecutar código.
- **RN-02 — Fechas:** la edición conserva la fecha de creación y registra la fecha y hora de última edición; se muestra "Editada el dd/mm/aaaa hh:mm" (hora de Colombia) solo si la nota fue editada. El orden de la lista sigue siendo por fecha de creación descendente.
- **RN-03 — Sin cambios:** si el texto recortado es idéntico al guardado, no se registra edición (Escenario 4).
- **RN-04 — Historial:** no se conservan versiones anteriores del texto; la edición reemplaza el texto.
- **RN-05 — Eliminación definitiva:** previa confirmación, la nota se elimina y no puede recuperarse desde la aplicación (salvo restauración técnica de respaldos).
- **RN-06 — Control de concurrencia:** la edición y la eliminación solo se aplican si la nota no cambió desde que se abrió; en otro caso aplica el Escenario 8.
- **RN-07 — Fecha de última actualización del caso:** se actualiza al editar (con cambios) o eliminar una nota.
- **RN-08 — Privacidad:** solo el autor del caso puede editar o eliminar sus notas; ningún otro usuario, incluido el Administrador.
- **RN-09 — Alcance:** editar y eliminar aplica solo a notas; las instantáneas de señales, contratos y evidencias del caso no se editan.

### Interfaz

- En cada nota: acciones "Editar" y "Eliminar".
- Edición en el mismo lugar de la nota: campo multilínea con el texto actual, contador "{n}/5.000", botones "Guardar cambios" y "Cancelar".
- Diálogo de confirmación con "Eliminar" y "Cancelar"; foco inicial en "Cancelar".
- WCAG 2.1 AA y navegación por teclado; funcional en 768 px y 360 px.

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

**Historias relacionadas:** HU-093 (agregar notas), HU-096 (detalle del caso), HU-097 (privacidad)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La eliminación de notas es definitiva, con confirmación, y no se guarda historial de versiones (RN-04, RN-05).
- Se protege contra sobrescrituras entre sesiones simultáneas (RN-06).

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
