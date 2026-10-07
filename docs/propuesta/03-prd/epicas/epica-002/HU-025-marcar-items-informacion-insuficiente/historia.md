# Historia #025: Marcar los ítems con información insuficiente indicando el motivo

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Extraer Datos de Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-030

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema marque como "información insuficiente" cada ítem de televisor del que no se logró obtener cantidad y precio unitario, con el motivo concreto,  
**Para** entender por qué un contrato no tiene comparación y distinguir cuándo la fuente no publica el dato de cuándo el producto no lo extrajo.

## Descripción

En D4, de 36 contratos en categoría, 20 no tenían precio unitario adjudicado en los documentos: valor global que mezcla el televisor con otros bienes o servicios (9), oferta del adjudicatario no publicada (5), formato de oferta en blanco o archivo vacío (3), tabla como imagen no procesada (2) y anexo con precios no seleccionado (1–2). Las primeras causas son de la **fuente**; las últimas, del **procesamiento**.

Esta HU evalúa cada ítem después de la extracción (HU-022), la base tributaria (HU-023) y el precio derivado (HU-024): si falta la cantidad o el precio unitario (explícito o derivado), o si el único precio es de presupuesto o cotización, el ítem queda "información insuficiente" con uno o más motivos de un catálogo cerrado, cada uno clasificado como causa de fuente o de procesamiento. El ítem no queda disponible para comparación. También resume por proceso los motivos por los que no hay ningún ítem comparable. La evaluación es determinística. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Ítem completo

- **Dado** que el ítem `CO1.PCCNTR.7654321-01` tiene cantidad 8 y precio unitario explícito 2.150.000 con etapa "adjudicado"
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el ítem queda "información suficiente" y disponible para comparación

### Escenario 2: Valor global que mezcla bienes o servicios

- **Dado** que el ítem tiene cantidad 2, sin precio unitario explícito, y el precio derivado no se calculó por "condiciones de precio derivado no cumplidas: 2, 4"
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el ítem queda "información insuficiente" con los motivos "valor global mezcla bienes o servicios" (causa: fuente) y "condiciones de precio derivado no cumplidas: 2, 4" (causa: fuente), y no queda disponible para comparación

### Escenario 3: Oferta adjudicada no identificable

- **Dado** que la extracción registró la observación "oferta adjudicada no identificable" y el precio unitario es nulo
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el motivo es "oferta del adjudicatario no publicada o no identificable" (causa: fuente)

### Escenario 4: Solo precio de presupuesto o cotización

- **Dado** que el único precio unitario del ítem tiene etapa "presupuesto o cotización"
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el ítem queda "información insuficiente" con el motivo "solo precio de presupuesto o cotización" (causa: fuente); el precio de presupuesto se conserva visible como dato, marcado con su etapa

### Escenario 5: Cantidad no documentada

- **Dado** que el ítem tiene precio unitario explícito pero cantidad nula
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el motivo es "cantidad no documentada" (causa: fuente)

### Escenario 6: Formato de oferta en blanco

- **Dado** que el ítem no tiene precio y al menos un documento económico del proceso fue marcado "formulario en blanco" o "archivo vacío"
- **Cuando** se evalúa la suficiencia de información
- **Entonces** entre los motivos aparece "formato de oferta en blanco o archivo vacío" (causa: fuente)

### Escenario 7: Causas de procesamiento

- **Dado** que el ítem no tiene precio, la extracción descartó un precio por "dato sin evidencia válida descartado" y el proceso tiene páginas con "lectura visual omitida por límite"
- **Cuando** se evalúa la suficiencia de información
- **Entonces** los motivos incluyen "dato descartado por falta de evidencia válida" y "páginas no leídas por límite de lectura visual", ambos con causa: procesamiento

### Escenario 8: Sin precio ni valor total publicados

- **Dado** que el ítem tiene cantidad 4 y ni precio unitario ni valor total del ítem
- **Cuando** se evalúa la suficiencia de información
- **Entonces** el motivo es "precio unitario no publicado" (causa: fuente)

### Escenario 9: Resumen por proceso sin ítems comparables

- **Dado** que el proceso `CO1.BDOS.5372563` quedó "sin documentos relevantes", y el proceso `CO1.BDOS.8234869` tiene 2 ítems, ambos con información insuficiente
- **Cuando** se consulta el resumen por proceso
- **Entonces** el primero muestra "proceso sin ítems comparables: sin documentos relevantes" y el segundo "proceso sin ítems comparables" con los motivos de sus ítems, sin repetir motivos iguales

### Escenario 10: Información completada por corrección humana

- **Dado** que el Administrador corrige la cantidad nula de un ítem a 6, con evidencia
- **Cuando** se guarda la corrección
- **Entonces** se repite la evaluación, el ítem pasa a "información suficiente" si ya tenía precio unitario, y la marca anterior y sus motivos quedan en el historial con fecha y usuario

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (ve el estado y los motivos en la ficha del contrato); Administrador (usa las causas para los indicadores de calidad). La evaluación es automática.
- **Permisos requeridos:** Analista y Administrador consultan.
- **Valor de negocio:** Separa la disponibilidad en la fuente de la cobertura de extracción (NFR-CAL-003) y evita comparaciones con datos incompletos.

### Reglas de Negocio

- **RN-01 — Momento de evaluación:** se evalúa cada ítem al terminar la extracción del proceso y después de la base tributaria y el precio derivado, y de nuevo después de cada corrección humana del ítem.
- **RN-02 — Condición de insuficiencia:** un ítem es "información insuficiente" si se cumple al menos una de: a) cantidad nula; b) precio unitario nulo (ni explícito ni derivado); c) el único precio unitario disponible tiene etapa "presupuesto o cotización". En otro caso es "información suficiente". La base tributaria `indeterminada` **no** hace insuficiente al ítem (se trata en la comparación).
- **RN-03 — Catálogo de motivos (cerrado) y causa:**

  | Motivo | Se asigna cuando | Causa |
  | ------ | ---------------- | ----- |
  | cantidad no documentada | cantidad nula sin observación de descarte | fuente |
  | precio unitario no publicado | precio unitario y valor total nulos, sin otro motivo de precio | fuente |
  | valor global mezcla bienes o servicios | precio derivado no calculado con la condición 2, 4 o 5 en "no cumple" | fuente |
  | condiciones de precio derivado no cumplidas: {números} | precio derivado no calculado (se copia el texto de HU-024) | fuente |
  | oferta del adjudicatario no publicada o no identificable | observación "oferta adjudicada no identificable" | fuente |
  | solo precio de presupuesto o cotización | condición c) de RN-02 | fuente |
  | formato de oferta en blanco o archivo vacío | precio nulo y algún documento económico del proceso marcado "formulario en blanco" o "archivo vacío" | fuente |
  | moneda distinta de COP | observación "moneda distinta de COP" en precio o total | fuente |
  | dato descartado por falta de evidencia válida | observación "dato sin evidencia válida descartado" o "valor fuera de rango descartado" en cantidad, precio o total | procesamiento |
  | páginas no leídas por límite de lectura visual | el proceso tiene páginas "lectura visual omitida por límite" | procesamiento |
  | documentos económicos no legibles | algún documento económico seleccionado quedó "archivo dañado", "archivo protegido", "descarga bloqueada" o "descarga fallida definitiva" | procesamiento |

- **RN-04 — Varios motivos:** se registran todos los motivos aplicables, sin duplicados. Si ningún motivo del catálogo aplica, se registra "motivo no identificado" (causa: procesamiento), para que ningún ítem insuficiente quede sin motivo.
- **RN-05 — Efecto:** un ítem "información insuficiente" no queda disponible para comparación ni para señales. Sus datos parciales (incluido un precio de presupuesto) se conservan y se muestran con su etapa y evidencia.
- **RN-06 — Resumen por proceso:** un proceso está "sin ítems comparables" cuando no tiene ningún ítem "información suficiente". El resumen muestra el estado del proceso si no tiene ítems ("sin documentos publicados", "sin documentos relevantes", "sin documentos legibles", "extraído sin ítems de televisor" o "extracción fallida"), o la unión sin repeticiones de los motivos de sus ítems.
- **RN-07 — Historial:** cada cambio de estado de suficiencia guarda estado anterior, motivos anteriores, fecha y usuario (o "sistema").
- **RN-08 — Indicadores:** por proceso y en total se cuentan los ítems por estado y por motivo y causa, como insumo de los indicadores de disponibilidad en la fuente y cobertura de extracción (que calcula otra épica).
- **RN-09 — Sin IA:** la evaluación es determinística y funciona con la extracción con IA desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. Estado, motivos y resumen quedan disponibles para la ficha del contrato (otra épica) y para consultas del Administrador.

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

**Historias relacionadas:** HU-017 (formularios en blanco), HU-020 (lectura visual omitida), HU-022 (observaciones de extracción), HU-024 (condiciones del derivado), HU-028 (correcciones).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Un ítem con solo precio de presupuesto o cotización se marca como información insuficiente, porque el análisis compara precio adjudicado o contratado → RN-02.
- La base tributaria indeterminada no hace insuficiente al ítem; se trata en la comparación → RN-02.
- Catálogo cerrado de motivos con causa "fuente" o "procesamiento", derivado de las causas de D4 → RN-03.
- Resumen por proceso sin ítems comparables, como insumo de la ficha → RN-06.

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
