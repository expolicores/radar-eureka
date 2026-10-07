# Historia #028: Validar, corregir o rechazar los datos extraídos de un ítem conservando el historial

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Controlar la Calidad de la Extracción  
**Prioridad:** Crítica  
**FRs relacionados:** FR-032

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador que actúa como Revisor en el MVP,  
**Quiero** validar, corregir o rechazar los datos extraídos de un ítem de televisor, conservando siempre el valor original, el valor corregido, el usuario y la fecha,  
**Para** que solo datos revisados lleguen a las comparaciones cuando la extracción automática no es confiable, y que cada corrección humana sea trazable.

## Descripción

Por la decisión P-08, en el MVP el Administrador (el PO) es también el Revisor: valida la extracción, corrige datos y gestiona los ítems de baja confianza o con inconsistencias. Los analistas piloto no corrigen datos (reportan errores por otro mecanismo, en la épica de señales).

Esta HU ofrece las operaciones de revisión sobre un ítem: **validar** (aceptarlo tal como está), **corregir** uno o varios campos (con evidencia opcional), **rechazar** (excluirlo del análisis con motivo), **reabrir** un ítem rechazado y **resolver una propuesta de reextracción**. Cada operación queda en un historial que no se puede modificar, y dispara la reevaluación de la base tributaria, el precio derivado, la suficiencia de información y la aritmética. Según la nota del Dominio 12 del PRD, las operaciones pueden ejecutarse sin interfaz gráfica (comando, consulta o vista administrativa mínima), siempre con trazabilidad. La cola priorizada de revisión y su vista son de la épica de operación.

---

## Criterios de Aceptación

### Escenario 1: Validar un ítem pendiente

- **Dado** que el ítem `CO1.PCCNTR.7654321-01` está "pendiente de revisión" con el motivo "umbral de aceptación no calibrado" y sin inconsistencias abiertas
- **Cuando** el Administrador lo valida
- **Entonces** el ítem queda "validado", disponible para comparación, y el historial registra la operación "validar", el usuario, la fecha y hora y el estado anterior

### Escenario 2: Corregir un campo con evidencia

- **Dado** que el ítem tiene cantidad 10 extraída y el Administrador verifica en "Contrato 045-2025.pdf", página 1, que la cantidad es 8
- **Cuando** corrige la cantidad a 8 indicando esa evidencia y el comentario "La oferta decía 10, el contrato fija 8"
- **Entonces** el valor vigente es 8 con la nueva evidencia; el historial conserva el valor original 10 con su evidencia, el valor corregido 8, el usuario, la fecha, el comentario y el origen "corrección manual"; se repiten la base tributaria, el precio derivado, la suficiencia y la aritmética; y el ítem queda "validado con correcciones" si queda suficiente y sin inconsistencias abiertas

### Escenario 3: Corregir un campo nulo

- **Dado** que la marca del ítem es nula
- **Cuando** el Administrador la corrige a "Samsung" con evidencia "Propuesta_economica_ganador.pdf, página 2"
- **Entonces** el valor original queda registrado como nulo y el corregido como "Samsung"

### Escenario 4: Corrección que deja el ítem aún pendiente

- **Dado** que el Administrador corrige el precio unitario a 2.150.000,00, pero el valor total sigue en 4.800.000,00 y la cantidad en 8
- **Cuando** guarda la corrección
- **Entonces** la nueva comprobación aritmética queda "inconsistente" y el ítem sigue "pendiente de revisión" con el motivo "inconsistencia aritmética"

### Escenario 5: Validar con una inconsistencia abierta

- **Dado** que el ítem tiene una "inconsistencia aritmética abierta"
- **Cuando** el Administrador intenta validarlo sin indicar que el error está en el documento
- **Entonces** la operación se rechaza con el mensaje "El ítem tiene inconsistencias aritméticas abiertas: corrija los valores o indique que el error está en el documento"; si indica "error del documento" con comentario, el ítem queda "validado" y la inconsistencia "resuelta" como "inconsistencia del documento"

### Escenario 6: Rechazar un ítem

- **Dado** que el ítem corresponde a un monitor de CCTV que la extracción tomó como televisor
- **Cuando** el Administrador lo rechaza con el motivo "no es un televisor del alcance"
- **Entonces** el ítem queda "rechazado", no disponible para comparación, con motivo, usuario y fecha; sus datos y evidencias se conservan

### Escenario 7: Rechazo con motivo "otro" sin comentario

- **Dado** que el Administrador rechaza un ítem con el motivo "otro"
- **Cuando** no escribe comentario
- **Entonces** la operación se rechaza con el mensaje "El comentario es obligatorio cuando el motivo es 'otro'"

### Escenario 8: Reabrir un ítem rechazado

- **Dado** que el ítem está "rechazado"
- **Cuando** el Administrador lo reabre con un comentario
- **Entonces** el ítem vuelve a "pendiente de revisión" con el motivo "reabierto por el Revisor"; validarlo o corregirlo directamente sin reabrir se rechaza con "Reabra el ítem antes de validarlo o corregirlo"

### Escenario 9: Valor de corrección inválido

- **Dado** que el Administrador intenta corregir la cantidad a 0, o el precio unitario a "dos millones", o el tamaño a 300 pulgadas, o la evidencia a la página 9 de un documento de 4 páginas
- **Cuando** guarda la corrección
- **Entonces** la operación se rechaza con el mensaje del campo correspondiente (ver RN-05) y no cambia ningún valor

### Escenario 10: Resolver una propuesta de reextracción

- **Dado** que una reextracción propuso precio unitario 2.090.000,00 para un ítem ya validado con 2.150.000,00
- **Cuando** el Administrador acepta la propuesta, o la descarta
- **Entonces** al aceptarla el valor vigente pasa a 2.090.000,00 con origen "reextracción aceptada" y el valor anterior en el historial; al descartarla el valor sigue en 2.150.000,00 y la propuesta queda "descartada" con usuario y fecha; en ambos casos el ítem deja de tener el motivo "propuesta de reextracción"

### Escenario 11: Modificación concurrente

- **Dado** que el Administrador consultó el ítem en su versión 3 y, antes de guardar su corrección, una reevaluación automática lo llevó a la versión 4
- **Cuando** guarda la corrección
- **Entonces** la operación se rechaza con "El ítem fue modificado por otra operación; vuelva a consultarlo" y no cambia nada

### Escenario 12: El Analista no puede revisar

- **Dado** que un usuario con rol Analista intenta validar, corregir o rechazar un ítem
- **Cuando** ejecuta la operación
- **Entonces** recibe acceso denegado y el ítem no cambia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador que actúa como Revisor (en el MVP es el PO).
- **Permisos requeridos:** Solo el rol Administrador ejecuta operaciones de revisión. El Analista puede consultar el estado y el historial de un ítem, pero no modificarlo.
- **Valor de negocio:** Garantiza que el 100 % de las correcciones humanas conserve valor original, usuario y fecha (criterio de la épica) y permite llevar a comparación los ítems que la extracción automática no pudo aceptar.

### Reglas de Negocio

- **RN-01 — Operaciones:** consultar (ítems de un contrato o ítems en un estado dado, con datos, evidencias, confianzas, motivos e historial), validar, corregir, rechazar, reabrir y resolver propuesta de reextracción. Toda operación de cambio exige la versión del ítem consultada; si el ítem cambió desde entonces: "El ítem fue modificado por otra operación; vuelva a consultarlo".
- **RN-02 — Estados y transiciones válidas:**
  - "aceptado automáticamente", "pendiente de revisión" o "no comparable: información insuficiente" → validar → "validado"; → corregir → "validado con correcciones" o "pendiente de revisión" (RN-07); → rechazar → "rechazado".
  - "validado" o "validado con correcciones" → corregir (nuevo resultado según RN-07) o rechazar.
  - "rechazado" → reabrir → "pendiente de revisión" (motivo "reabierto por el Revisor"). Validar o corregir un ítem rechazado: "Reabra el ítem antes de validarlo o corregirlo".
- **RN-03 — Validar:** acepta los valores vigentes. Requisitos: el ítem tiene información suficiente (si no, mensaje "El ítem no tiene cantidad y precio unitario suficientes; corríjalo o rechácelo") y no tiene inconsistencias aritméticas abiertas, salvo que el Administrador indique "error del documento" con comentario (1 a 500 caracteres), en cuyo caso la inconsistencia queda "resuelta" como "inconsistencia del documento". Si no se cumple: "El ítem tiene inconsistencias aritméticas abiertas: corrija los valores o indique que el error está en el documento". Validar también confirma las marcas "lote no determinado" y "conflicto entre documentos".
- **RN-04 — Corregir:** uno o varios campos en una misma operación: descripción, marca, modelo/referencia, tamaño y unidad, resolución, tecnología, Smart, cantidad, precio unitario explícito, valor total del ítem, base tributaria de cada valor, valor y tasa de IVA, etapa del precio, y resultado de cada condición del precio derivado. Por campo: valor nuevo (puede ser nulo para eliminar un dato mal extraído), evidencia opcional (documento del mismo proceso, versión y ubicación) y comentario opcional (máximo 500 caracteres). Sin evidencia nueva, el valor corregido conserva la evidencia original con la anotación "corrección manual".
- **RN-05 — Validaciones de la corrección (mensaje por campo):**
  - Cantidad: entero de 1 a 999.999 → "La cantidad debe ser un entero entre 1 y 999.999".
  - Precio unitario y valor total: número mayor que 0 y hasta 10.000.000.000, máximo 2 decimales → "El valor debe ser mayor que 0 y hasta 10.000.000.000, con máximo 2 decimales".
  - Tamaño: mayor que 0 y hasta 150 si la unidad es "pulgadas", hasta 381 si es "cm" → "El tamaño debe ser mayor que 0 y hasta 150 pulgadas (381 cm)".
  - Base tributaria: `con_iva`, `sin_iva` o `indeterminada`; tasa de IVA 0 a 100 → "Valor no permitido para {campo}".
  - Smart: "sí", "no" o nulo; etapa: "adjudicado", "contratado" o "presupuesto o cotización"; condición del derivado: "cumple", "no cumple" o "no determinable" → "Valor no permitido para {campo}".
  - Marca, modelo, resolución y tecnología: hasta 200 caracteres; descripción: hasta 1.000 → "Texto demasiado largo para {campo} (máximo {n} caracteres)".
  - Evidencia: el documento debe pertenecer al proceso del ítem y la ubicación debe existir en su representación → "La ubicación de evidencia no existe en el documento indicado".
  Si un campo no es válido, la operación completa se rechaza y no cambia ningún valor.
- **RN-06 — Prioridad de la corrección manual:** un valor corregido manualmente (incluida la base tributaria) prevalece sobre la determinación automática y no se recalcula; los demás valores sí se recalculan.
- **RN-07 — Efecto de una corrección:** se repiten, en este orden, la base tributaria de los valores no corregidos (HU-023), el precio derivado (HU-024), la suficiencia (HU-025) y la comprobación aritmética (HU-027). Si el ítem queda con información suficiente y sin inconsistencias abiertas: "validado con correcciones"; si no, "pendiente de revisión" con los motivos vigentes.
- **RN-08 — Rechazar:** motivo obligatorio de la lista: "no es un televisor del alcance", "lote no corresponde al televisor", "datos no verificables en el documento", "duplicado de otro ítem", "otro". Con "otro" el comentario es obligatorio: "El comentario es obligatorio cuando el motivo es 'otro'". Un motivo fuera de la lista: "Valor no permitido para motivo de rechazo". Un ítem rechazado no está disponible para comparación; sus datos, evidencias e historial se conservan.
- **RN-09 — Reabrir:** comentario obligatorio (1 a 500 caracteres): "El comentario es obligatorio para reabrir un ítem".
- **RN-10 — Propuesta de reextracción:** aceptar → el valor propuesto pasa a vigente con origen "reextracción aceptada" y su evidencia; descartar → la propuesta queda "descartada". En ambos casos se registra usuario y fecha, se elimina el motivo "propuesta de reextracción" y se aplica RN-07.
- **RN-13 — Disponibilidad:** "validado" y "validado con correcciones" quedan disponibles para comparación.
- **RN-11 — Historial inmutable:** cada operación agrega una entrada con: operación, campo(s), valor original (el extraído o el anterior vigente) con su evidencia, valor nuevo con su evidencia, origen ("extracción", "corrección manual", "reextracción aceptada"), estado anterior y nuevo, motivo y comentario, usuario y fecha y hora. Las entradas no se pueden modificar ni eliminar; el valor extraído original siempre puede consultarse.
- **RN-12 — Auditoría:** cada operación de corrección, rechazo o reapertura se registra además como evento de auditoría (usuario, fecha, ítem, operación), para el log de auditoría de la épica de operación.

### Interfaz

Sin interfaz gráfica obligatoria (nota del Dominio 12): las operaciones pueden ejecutarse por comando, consulta o una vista administrativa mínima, siempre que devuelvan los mensajes de RN-03, RN-05, RN-08 y RN-09 y dejen la trazabilidad de RN-11. La vista de cola priorizada de revisión es de la épica de operación.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)

**Exclusiones de la Épica:**
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Historias relacionadas:** HU-022 (datos y propuestas de reextracción), HU-023, HU-024, HU-025, HU-027 (reevaluaciones), HU-026 (estados de aceptación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La revisión no crea ítems nuevos: solo valida, corrige, rechaza o reabre ítems extraídos (alcance de FR-032) → RN-01.
- Rangos de validación de las correcciones (cantidad 1–999.999; valores hasta 10.000 millones; tamaño hasta 150 pulgadas) → RN-05.
- Catálogo cerrado de motivos de rechazo con "otro" y comentario obligatorio → RN-08.
- Control de versión para evitar sobrescribir cambios concurrentes → RN-01.
- La corrección manual prevalece sobre las determinaciones automáticas → RN-06.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-002 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
