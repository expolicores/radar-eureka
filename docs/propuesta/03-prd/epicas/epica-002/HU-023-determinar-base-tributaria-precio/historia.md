# Historia #023: Determinar si cada precio extraído es con IVA, sin IVA o de base indeterminada

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Extraer Datos de Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-029

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada precio unitario y cada valor total extraído indique si es con IVA, sin IVA o de base indeterminada, con la evidencia de esa determinación,  
**Para** que nunca se comparen en silencio valores con y sin IVA y pueda ver por qué un precio quedó con base indeterminada.

## Descripción

En D4 el IVA fue indeterminado en 10 de 19 ítems con precio (53 %), y hubo casos especiales: precio unitario sin IVA con total con IVA, y exención de IVA en San Andrés. La regla del producto es no asumir: la base solo se determina con una declaración explícita en el documento; si no la hay, es "indeterminada", y la comparación posterior se marcará como incompleta (épica de señales).

Esta HU toma cada valor monetario de los ítems extraídos (HU-022) y la declaración tributaria que el extractor encontró para ese valor (texto y ubicación), y clasifica la base con reglas determinísticas y configurables. Cada valor tiene su propia base: un precio unitario puede ser sin IVA y el total con IVA. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Declaración explícita de IVA incluido

- **Dado** que el precio unitario 2.150.000 del ítem `CO1.PCCNTR.7654321-01` tiene como declaración "Valor unitario IVA incluido" en el encabezado de la columna, página 2 de la oferta
- **Cuando** se determina la base tributaria
- **Entonces** el precio unitario queda con base `con_iva` y evidencia "Propuesta_economica_ganador.pdf, versión 1, página 2: 'Valor unitario IVA incluido'"

### Escenario 2: Precio unitario sin IVA y total con IVA

- **Dado** que la tabla muestra "Valor unitario antes de IVA: $ 1.806.723", "IVA 19 %: $ 2.747.000" y "Valor total con IVA: $ 17.200.000"
- **Cuando** se determina la base tributaria
- **Entonces** el precio unitario queda `sin_iva`, el valor total del ítem queda `con_iva`, y se registran el valor de IVA 2.747.000 y la tasa 19 % con su evidencia

### Escenario 3: Estructura subtotal, IVA y total

- **Dado** que la oferta presenta "Subtotal $ 14.453.782 / IVA $ 2.746.218 / Total $ 17.200.000" y el valor total del ítem extraído es 17.200.000
- **Cuando** se determina la base tributaria
- **Entonces** el valor total del ítem queda `con_iva` por la regla de estructura subtotal-IVA-total

### Escenario 4: Sin declaración tributaria

- **Dado** que el documento muestra "Valor unitario $ 2.150.000" sin ninguna mención de IVA
- **Cuando** se determina la base tributaria
- **Entonces** el precio queda `indeterminada` con el motivo "sin declaración tributaria en el documento"

### Escenario 5: Coincidencia aritmética sin declaración

- **Dado** que 8 × 1.806.723 × 1,19 ≈ 17.200.000, pero ningún texto menciona IVA
- **Cuando** se determina la base tributaria
- **Entonces** ambos valores quedan `indeterminada`, con la observación "coincidencia aritmética con IVA 19 % sin declaración explícita"

### Escenario 6: Bien exento o excluido de IVA

- **Dado** que la oferta de un contrato en San Andrés dice "Bienes exentos de IVA - Ley 1607 de 2012" junto al precio unitario
- **Cuando** se determina la base tributaria
- **Entonces** el precio queda `sin_iva` con el indicador "exento o excluido de IVA: sí", y la anotación "el precio final al comprador coincide con este valor"

### Escenario 7: Declaración general del documento

- **Dado** que la página 1 de la oferta dice "Todos los precios de la presente oferta incluyen IVA" y la tabla de la página 2 no menciona IVA
- **Cuando** se determina la base tributaria
- **Entonces** los valores extraídos de ese documento quedan `con_iva` con evidencia en la página 1

### Escenario 8: Declaraciones contradictorias

- **Dado** que para el mismo precio unitario la columna dice "valor con IVA" y la nota al pie de la misma tabla dice "valores antes de IVA"
- **Cuando** se determina la base tributaria
- **Entonces** el precio queda `indeterminada` con el motivo "declaraciones tributarias contradictorias" y ambas evidencias registradas

### Escenario 9: Declaración devuelta sin evidencia

- **Dado** que el extractor indica "con IVA" para un precio pero no entrega el texto ni la ubicación de la declaración
- **Cuando** se determina la base tributaria
- **Entonces** el precio queda `indeterminada` con el motivo "declaración tributaria sin evidencia"

### Escenario 10: Precio nulo

- **Dado** que el ítem no tiene precio unitario extraído
- **Cuando** se determina la base tributaria
- **Entonces** el precio unitario no tiene base tributaria (nula) y no se genera motivo

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (ve la base de cada precio y su evidencia); Administrador (mantiene las expresiones configurables). La determinación es automática.
- **Permisos requeridos:** Analista y Administrador consultan; solo el Administrador modifica la configuración.
- **Valor de negocio:** Cumple NFR-CAL-006 (0 % de comparaciones que mezclan valores con y sin IVA sin marcarse) desde el origen del dato.

### Reglas de Negocio

- **RN-01 — Alcance:** se determina la base de cada valor monetario no nulo de cada ítem: precio unitario y valor total del ítem. Cada valor tiene su propia base (`con_iva`, `sin_iva` o `indeterminada`), su evidencia y, si aplica, su motivo. Un valor nulo no tiene base.
- **RN-02 — Entrada:** por cada valor, las declaraciones tributarias devueltas por el extractor (texto literal, documento, versión y ubicación) y la estructura de la tabla (encabezados, filas de subtotal, IVA y total) cuando exista.
- **RN-03 — Expresiones `con_iva` (configurables; se comparan en minúsculas y sin tildes):** "iva incluido", "incluye iva", "con iva", "valor con iva", "precio final con iva", "valor total con iva", "incluido iva".
- **RN-04 — Expresiones `sin_iva` (configurables):** "sin iva", "antes de iva", "mas iva", "+ iva", "no incluye iva", "valor antes de impuestos", "iva no incluido".
- **RN-05 — Expresiones de exención o exclusión (configurables):** "exento de iva", "excluido de iva", "no causa iva", "bienes exentos", "bienes excluidos". El valor queda `sin_iva` con el indicador "exento o excluido de IVA: sí" y la anotación "el precio final al comprador coincide con este valor".
- **RN-06 — Estructura subtotal-IVA-total:** si la tabla presenta una fila o columna "subtotal" (o "valor antes de IVA"), una de "IVA" y una de "total", el valor extraído del subtotal queda `sin_iva` y el extraído del total queda `con_iva`. Una columna "IVA" separada en la misma fila de un valor hace que ese valor quede `sin_iva`, salvo que su encabezado diga lo contrario.
- **RN-07 — Alcance de una declaración y prioridad:** de más a menos específica: 1) misma celda o fila del valor; 2) encabezado de la columna del valor; 3) encabezado, pie o nota de la tabla; 4) declaración general del documento (ej. "todos los precios incluyen IVA"). Se aplica la declaración más específica. Solo se usan declaraciones del mismo documento del que se extrajo el valor.
- **RN-08 — Contradicción:** si dos declaraciones del mismo nivel de especificidad indican bases distintas para el mismo valor, la base es `indeterminada` con el motivo "declaraciones tributarias contradictorias" y ambas evidencias.
- **RN-09 — Sin declaración:** sin ninguna declaración aplicable, la base es `indeterminada` con el motivo "sin declaración tributaria en el documento". Una coincidencia aritmética con una tasa de IVA no determina la base: si cantidad × precio unitario × 1,19 está dentro del 0,5 % del total, se agrega la observación "coincidencia aritmética con IVA 19 % sin declaración explícita".
- **RN-10 — Evidencia obligatoria:** una base `con_iva` o `sin_iva` requiere texto y ubicación de la declaración; si el extractor indica una base sin evidencia, la base es `indeterminada` con el motivo "declaración tributaria sin evidencia".
- **RN-11 — Valor y tasa de IVA:** si el documento publica el valor del IVA o la tasa para el ítem, se registran con su evidencia. Tasa válida: 0 % a 100 %; fuera de rango se descarta con la observación "tasa de IVA fuera de rango".
- **RN-12 — Precio derivado:** un precio unitario derivado (HU-024) hereda la base del valor total usado para calcularlo.
- **RN-13 — Nunca se asume:** la base no se infiere de la modalidad, la entidad, el proveedor, la fuente ni de valores de otros contratos.
- **RN-14 — Cambios de configuración:** los cambios en las expresiones aplican a las determinaciones siguientes; para recalcular ítems ya procesados, el Administrador solicita la redeterminación de un proceso. Cada cambio registra usuario, fecha, valor anterior y nuevo.
- **RN-15 — Sin IA en la clasificación:** la clasificación de la base es determinística sobre las declaraciones ya extraídas; puede ejecutarse aunque la extracción con IA esté desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. La base, su evidencia y su motivo quedan disponibles para las vistas de ficha y señal y para consultas del Administrador.

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

**Historias relacionadas:** HU-022 (valores y declaraciones extraídas), HU-024 (herencia de base en precio derivado), HU-027 (comprobación aritmética con IVA), HU-028 (corrección manual de la base).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La base se determina por valor (precio unitario y total por separado), según el caso observado en D4 → RN-01.
- Los bienes exentos o excluidos se registran `sin_iva` con un indicador explícito y la nota de que el precio final coincide → RN-05.
- La coincidencia aritmética con 19 % no determina la base; solo se anota (tolerancia 0,5 %) → RN-09.
- Prioridad de declaraciones por especificidad (celda/fila > columna > tabla > documento) → RN-07.

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
