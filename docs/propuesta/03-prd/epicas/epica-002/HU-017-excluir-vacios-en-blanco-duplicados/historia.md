# Historia #017: Excluir documentos vacíos, formularios en blanco y duplicados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Obtener y Priorizar Documentos del Proceso  
**Prioridad:** Crítica  
**FRs relacionados:** FR-019 (detectar y excluir formularios o documentos en blanco y archivos vacíos; deduplicar por hash)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema detecte y excluya de la extracción los archivos vacíos, los formatos de oferta sin diligenciar y los documentos repetidos de un mismo proceso,  
**Para** que los cupos de documentos priorizados se usen en documentos que sí pueden contener precios y cantidades, y que el motivo de la ausencia de datos quede registrado.

## Descripción

El spike D4 encontró formatos de "propuesta económica" publicados por la entidad sin diligenciar (parecen ofertas pero no tienen valores), un PDF de 130 bytes y el mismo documento cargado varias veces en un proceso. Esta HU evalúa cada documento descargado (HU-016) y cada archivo interno de un comprimido (HU-018) y lo marca, si aplica, como "archivo vacío", "formulario en blanco" o "duplicado de {id_documento}". Un documento marcado deja de ser elegible y la priorización del proceso se recalcula para que otro documento ocupe su cupo (HU-015).

La detección es determinística (no usa IA) y se basa en el tamaño, la estructura y el texto ya disponible del documento. Cuando un documento no tiene texto legible sin lectura visual (escaneado), no se marca como "formulario en blanco": sigue elegible y su contenido lo evalúa la extracción. El Administrador puede revertir una marca equivocada. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Archivo vacío por tamaño

- **Dado** que el documento 600020 "Oferta economica.pdf" del proceso `CO1.BDOS.9640674` se descargó con 130 bytes y el mínimo configurado es 1.024 bytes
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento queda "no elegible: archivo vacío" y se recalcula la priorización del proceso

### Escenario 2: Archivo sin contenido estructural

- **Dado** que un PDF de 3.000 bytes tiene 0 páginas, o un XLSX tiene todas sus hojas sin celdas con valor, o un DOCX no tiene texto ni imágenes
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento queda "no elegible: archivo vacío"

### Escenario 3: Formato de propuesta económica sin diligenciar

- **Dado** que el documento "ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx" (categoría "oferta o propuesta económica") tiene 1.450 caracteres de texto con encabezados "ÍTEM | DESCRIPCIÓN | CANTIDAD | VALOR UNITARIO | VALOR TOTAL" y ningún valor monetario
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento queda "no elegible: formulario en blanco" y se recalcula la priorización del proceso

### Escenario 4: Propuesta económica diligenciada

- **Dado** que el documento "Propuesta_economica_ganador.pdf" tiene capa de texto con "8 | Televisor 55 pulgadas 4K | $ 2.150.000 | $ 17.200.000"
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento sigue elegible

### Escenario 5: Documento escaneado sin texto

- **Dado** que el documento "Oferta economica firmada.pdf" (categoría "oferta o propuesta económica") tiene 4 páginas y ninguna con capa de texto utilizable
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento no se marca como "formulario en blanco", sigue elegible y queda anotado "en blanco no determinable sin lectura visual"

### Escenario 6: Formulario de una categoría no económica

- **Dado** que el documento "Estudio previo.pdf" (categoría "estudios previos") no contiene valores monetarios
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento sigue elegible, porque la regla de formulario en blanco solo aplica a las categorías económicas

### Escenario 7: Documentos duplicados en el mismo proceso

- **Dado** que en el proceso `CO1.BDOS.9691113` los documentos 610001 (posición 2), 610005 (posición 6) y el archivo interno "oferta.pdf" del comprimido 610009 tienen el mismo hash SHA-256
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** 610001 sigue elegible como original, y 610005 y el archivo interno quedan "no elegible: duplicado de 610001"; se recalcula la priorización

### Escenario 8: Mismo archivo en procesos distintos

- **Dado** que el mismo archivo (mismo hash) está publicado en los procesos `CO1.BDOS.1111111` y `CO1.BDOS.2222222`
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** el documento sigue elegible en ambos procesos

### Escenario 9: Archivos vacíos con el mismo hash

- **Dado** que dos documentos del mismo proceso tienen 0 bytes (mismo hash)
- **Cuando** se ejecuta la evaluación de elegibilidad
- **Entonces** ambos quedan "no elegible: archivo vacío" (la regla de vacío se evalúa antes que la de duplicado)

### Escenario 10: Reversión manual de una marca

- **Dado** que el Administrador revisa el documento marcado "formulario en blanco" y confirma que sí contiene precios (expresados como "dos millones ciento cincuenta mil pesos")
- **Cuando** lo marca como "elegible por revisión manual" con un comentario
- **Entonces** el documento vuelve a ser elegible, se registran usuario, fecha, marca anterior y comentario, la marca automática no se vuelve a aplicar a ese documento y se recalcula la priorización

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO); el proceso es automático y el Administrador puede revertir marcas.
- **Permisos requeridos:** Rol Administrador para consultar resultados y revertir marcas. El Analista no accede.
- **Valor de negocio:** Evita gastar cupos y costo de extracción en documentos sin datos, y registra "formato de oferta en blanco" como causa de ausencia del dato en la fuente (insumo del indicador de disponibilidad en la fuente).

### Reglas de Negocio

- **RN-01 — Entrada:** documentos en estado "descargado" (HU-016) y archivos internos expandidos de comprimidos (HU-018) que aún no tengan evaluación de elegibilidad.
- **RN-02 — Orden de evaluación:** 1) archivo vacío, 2) duplicado, 3) formulario en blanco. Un documento marcado en un paso no se evalúa en los siguientes.
- **RN-03 — Archivo vacío:** el documento es "archivo vacío" si su tamaño es menor que el mínimo configurable (configuración inicial: 1.024 bytes), o si es un PDF con 0 páginas, una hoja de cálculo sin ninguna celda con valor en ninguna hoja, un documento de texto sin texto ni imágenes, o una imagen de 0 × 0 píxeles. Un archivo que no se puede abrir no se evalúa aquí (lo marca HU-019 como "archivo dañado").
- **RN-04 — Duplicado:** dos documentos son duplicados si tienen el mismo hash SHA-256 de contenido y pertenecen al mismo proceso (incluidos archivos internos de comprimidos del proceso). El original es el de mejor posición en la priorización vigente; si ninguno está seleccionado, el de fecha de carga más antigua; luego el `id_documento` menor. Los demás quedan "no elegible: duplicado de {id del original}". Documentos idénticos en procesos distintos no se marcan como duplicados.
- **RN-05 — Formulario en blanco (alcance):** solo se evalúa en documentos de las categorías económicas de HU-015: evaluación económica, oferta o propuesta económica, anexo económico, aceptación de oferta, cotización y precios techo.
- **RN-06 — Formulario en blanco (condición):** el documento es "formulario en blanco" si su texto disponible sin lectura visual (capa de texto del PDF, contenido de celdas o texto del documento) tiene al menos 200 caracteres utilizables (letras o dígitos, sin contar espacios) y contiene 0 valores monetarios. Valor monetario: número precedido de "$" o "COP", o número con separadores de miles (punto o coma) cuyo valor sea ≥ 10.000. No cuentan como valores monetarios: años (1990–2100 sin separadores), números de página, números de 1 a 9.999, ni celdas con 0.
- **RN-07 — Sin texto suficiente:** si el documento tiene menos de 200 caracteres utilizables sin lectura visual (ej. escaneado), no se marca como formulario en blanco: sigue elegible con la anotación "en blanco no determinable sin lectura visual".
- **RN-08 — Efecto de la marca:** "archivo vacío", "duplicado" y "formulario en blanco" hacen al documento no elegible y disparan el recalculo de la priorización del proceso (HU-015). El documento no se borra: conserva su registro, hash y marca.
- **RN-09 — Causa registrada:** cada marca guarda motivo, regla aplicada, fecha y la categoría de causa: "formulario en blanco" y "archivo vacío" se registran como causa de **fuente** (la entidad publicó el documento sin datos); "duplicado" como causa de **procesamiento** (no afecta la disponibilidad).
- **RN-10 — Reversión manual:** el Administrador puede marcar un documento como "elegible por revisión manual", con comentario obligatorio (1 a 500 caracteres). Se registran usuario, fecha, marca anterior y comentario; la marca automática no se vuelve a aplicar a ese documento y se recalcula la priorización. Sin comentario, la reversión se rechaza con el mensaje "El comentario es obligatorio para revertir una marca automática". Un documento sin marca no se puede revertir: mensaje "El documento no tiene una marca automática que revertir".
- **RN-11 — Contadores por proceso:** número de documentos vacíos, en blanco y duplicados, disponibles para los indicadores de calidad.

### Interfaz

Sin interfaz gráfica obligatoria. Resultados y reversión mediante consultas, comandos o una vista administrativa mínima. Los mensajes de RN-10 se devuelven en la respuesta de la operación.

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre el contenido ya descargado.

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

**Historias relacionadas:** HU-015 (recalculo de priorización), HU-016 (descarga y hash), HU-018 (archivos internos), HU-019 (archivos dañados).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Tamaño mínimo inicial de 1.024 bytes para "archivo vacío" (D4 encontró un PDF de 130 bytes) → RN-03.
- "Formulario en blanco" se detecta de forma determinística: documento económico con ≥ 200 caracteres utilizables y 0 valores monetarios (≥ 10.000 o con símbolo de moneda) → RN-05, RN-06.
- Los documentos sin texto legible sin lectura visual no se marcan como en blanco → RN-07.
- La deduplicación por hash se hace dentro de cada proceso → RN-04.
- El Administrador puede revertir una marca automática con comentario obligatorio → RN-10.

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
