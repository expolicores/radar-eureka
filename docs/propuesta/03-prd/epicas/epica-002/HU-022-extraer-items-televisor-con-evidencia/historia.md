# Historia #022: Extraer con IA los datos de cada ítem de televisor con su evidencia de origen

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Extraer Datos de Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-025, FR-027, FR-100

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema extraiga de los documentos priorizados de cada proceso, por cada ítem de televisor, su descripción, marca, modelo, tamaño, resolución, tecnología, funciones Smart, cantidad, precio unitario, valor total e IVA, indicando para cada dato el documento y la página (u hoja y celda) donde se encontró,  
**Para** contar con el precio unitario y las características del televisor adjudicado, que en SECOP II solo existen dentro de los documentos, y poder verificar cada dato en su fuente.

## Descripción

Es el primer incremento de IA del producto. Para cada proceso con documentos preparados (HU-019) y páginas visuales detectadas (HU-020), el sistema envía al componente de extracción con IA el texto de los documentos priorizados, en orden de prioridad, con sus marcas de ubicación, y las imágenes de las páginas que requieren lectura visual (OCR o lectura multimodal). El componente devuelve los ítems de televisor dentro del límite de categoría, cada campo con su ubicación de evidencia y su nivel de confianza.

El sistema valida la respuesta: descarta cualquier dato sin evidencia o con una ubicación que no existe, nunca acepta valores inventados y nunca usa el valor del contrato publicado en datos abiertos como precio. Solo registra el bien del oferente adjudicado (los precios de los demás oferentes están fuera del MVP, FR-026). La base tributaria (HU-023), el precio derivado (HU-024), la marca de información insuficiente (HU-025), la confianza y el umbral (HU-026) y las inconsistencias (HU-027) se resuelven en sus propias HU sobre el resultado de esta. En D4, el 100 % de los campos extraídos tuvo evidencia y todas las imágenes fueron legibles.

---

## Criterios de Aceptación

### Escenario 1: Extracción de un ítem con precio unitario publicado

- **Dado** que el proceso `CO1.BDOS.1234567` (contrato `CO1.PCCNTR.7654321`) está en "documentos preparados" y la página 2 de "Propuesta_economica_ganador.pdf" (oferta del adjudicatario) contiene "1 | Televisor Smart TV Samsung UN55DU7000 55 pulgadas 4K LED | 8 | $ 2.150.000 | $ 17.200.000"
- **Cuando** se ejecuta la extracción
- **Entonces** se registra el ítem `CO1.PCCNTR.7654321-01` con descripción, marca "Samsung", modelo "UN55DU7000", tamaño 55 pulgadas, resolución "4K", tecnología "LED", Smart "sí", cantidad 8, precio unitario 2.150.000,00, valor total del ítem 17.200.000,00, etapa del precio "adjudicado", tipo de precio unitario `explicito`, y cada campo con la evidencia "Propuesta_economica_ganador.pdf, versión 1, página 2" y su confianza; el proceso queda "extraído" con 1 ítem

### Escenario 2: Dato en hoja de cálculo y dato leído de una imagen

- **Dado** que la cantidad está en la celda `Oferta!C5` de un XLSX y el precio unitario está en una tabla escaneada en la imagen de la página 3 de otro documento
- **Cuando** se ejecuta la extracción
- **Entonces** la evidencia de la cantidad es "hoja Oferta, celda C5" y la del precio unitario es "página 3 (lectura visual)"

### Escenario 3: Contrato mixto

- **Dado** que el contrato incluye 10 computadores portátiles, 2 televisores de 65 pulgadas y 2 soportes de pared
- **Cuando** se ejecuta la extracción
- **Entonces** solo se registra 1 ítem de televisor (cantidad 2); los computadores y los soportes no se registran como ítems

### Escenario 4: Varios ítems de televisor

- **Dado** que la oferta adjudicada tiene una línea de 4 televisores de 43 pulgadas y otra de 2 televisores de 65 pulgadas
- **Cuando** se ejecuta la extracción
- **Entonces** se registran 2 ítems (`-01` y `-02`), cada uno con sus datos y evidencias

### Escenario 5: Campo no presente en los documentos

- **Dado** que los documentos no mencionan marca ni modelo del televisor
- **Cuando** se ejecuta la extracción
- **Entonces** marca y modelo quedan nulos, sin evidencia y sin confianza, y el resto de campos se registra normalmente

### Escenario 6: Dato devuelto sin evidencia o con ubicación inexistente

- **Dado** que el componente de IA devuelve la marca "LG" sin ubicación, y el precio unitario con la ubicación "página 9" de un documento que solo tiene 4 páginas
- **Cuando** el sistema valida la respuesta
- **Entonces** ambos campos quedan nulos y se registra para cada uno la observación "dato sin evidencia válida descartado" con el valor descartado

### Escenario 7: Varios oferentes en una evaluación económica

- **Dado** que el informe de evaluación económica muestra precios unitarios de 3 oferentes e indica que "COMERCIALIZADORA ABC SAS" fue adjudicada
- **Cuando** se ejecuta la extracción
- **Entonces** solo se registra el precio del oferente adjudicado; los precios de los otros oferentes no se registran

### Escenario 8: Oferta adjudicada no identificable

- **Dado** que la evaluación muestra precios de 3 oferentes pero ningún documento seleccionado indica cuál fue adjudicado
- **Cuando** se ejecuta la extracción
- **Entonces** precio unitario y valor total del ítem quedan nulos con la observación "oferta adjudicada no identificable"; los atributos comunes del pliego (tamaño, resolución, cantidad) sí se registran con su evidencia

### Escenario 9: Solo existe precio de presupuesto o cotización

- **Dado** que el único precio unitario está en el estudio previo (presupuesto) o en una cotización del análisis del sector
- **Cuando** se ejecuta la extracción
- **Entonces** el precio se registra con etapa "presupuesto o cotización", con su evidencia

### Escenario 10: Valores contradictorios entre documentos

- **Dado** que el contrato indica cantidad 8 y la oferta del adjudicatario indica cantidad 10
- **Cuando** se ejecuta la extracción
- **Entonces** se registra el valor del documento de mayor precedencia (contrato: 8), se anota el conflicto "valores distintos en documentos: 8 (contrato, página 1) / 10 (oferta, página 2)" y el ítem queda marcado con conflicto para revisión

### Escenario 11: El valor del contrato en datos abiertos no se usa como precio

- **Dado** que el contrato tiene `valor_del_contrato` = 89.800.000 en datos abiertos y los documentos no publican precio ni valor del ítem
- **Cuando** se ejecuta la extracción
- **Entonces** precio unitario y valor total del ítem quedan nulos; el valor 89.800.000 solo se muestra como "valor del contrato (datos abiertos, referencia)" y nunca se usa para calcular ni completar datos del ítem

### Escenario 12: Proceso sin ítems de televisor en los documentos

- **Dado** que los documentos solo describen un servicio de mantenimiento de televisores
- **Cuando** se ejecuta la extracción
- **Entonces** el proceso queda "extraído sin ítems de televisor" con la observación devuelta (ej. "los documentos describen un servicio de mantenimiento, no una compra")

### Escenario 13: Falla del servicio de IA o respuesta inválida

- **Dado** que el servicio de IA responde con error en el intento inicial y en los 3 reintentos, o devuelve dos veces una respuesta que no cumple el formato esperado
- **Cuando** se ejecuta la extracción
- **Entonces** el proceso queda "extracción fallida" con el motivo ("servicio de IA no disponible" o "respuesta inválida del extractor"), no se guarda ningún ítem parcial y el proceso puede reintentarse en la siguiente ejecución

### Escenario 14: La ingesta no dispara reextracción

- **Dado** que el proceso ya está "extraído" y una ingesta posterior actualiza el contrato o agrega documentos nuevos
- **Cuando** se ejecuta la siguiente extracción programada
- **Entonces** el proceso no se vuelve a extraer; solo se reextrae si el Administrador lo solicita explícitamente

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (consume los datos extraídos con su evidencia); el Administrador solicita reextracciones. La extracción es automática.
- **Permisos requeridos:** Analista y Administrador consultan ítems extraídos y su evidencia; solo el Administrador solicita reextracciones.
- **Valor de negocio:** Produce el precio unitario y las características que alimentan la normalización, los benchmarks y las señales; es el componente de mayor riesgo técnico del MVP.

### Reglas de Negocio

- **RN-01 — Procesos a extraer:** procesos en "documentos preparados" sin extracción previa, cuando la extracción con IA está activa. Un proceso ya extraído solo se reextrae por solicitud explícita del Administrador; la ingesta de contratos o la aparición de documentos nuevos no dispara reextracción.
- **RN-02 — Entrada al extractor:** texto de los documentos preparados en el orden de prioridad, con marcas de ubicación "[documento | versión | página N]" o "[documento | versión | hoja H | celda C]", las imágenes de las páginas que requieren lectura visual con su número de página, el objeto del contrato, la marca "lote no determinado" si aplica, y el límite de categoría. **No** se entrega al extractor el `valor_del_contrato` de datos abiertos.
- **RN-03 — Límite de categoría:** se extraen solo ítems de televisor LED, QLED, OLED o equivalentes de consumo, Smart o convencionales, de cualquier tamaño. No son ítems de televisor: soportes, bases, cables, controles, instalación, mantenimiento, pantallas LED modulares, videowalls, señalización digital, monitores (incluidos los de CCTV), proyectores, pantallas interactivas o táctiles, pantallas inflables ni soluciones audiovisuales integrales.
- **RN-04 — Campos por ítem y formato:**
  - Descripción: texto tal como aparece, máximo 1.000 caracteres.
  - Marca y modelo/referencia: texto tal como aparece (sin normalizar; la normalización es de otra épica). Si el modelo va acompañado de "o equivalente", "o similar" o "tipo", se anota "referencia orientativa".
  - Tamaño: número decimal > 0 y unidad ("pulgadas" o "cm"), tal como aparece.
  - Resolución y tecnología de pantalla: texto tal como aparece (ej. "4K", "UHD", "Full HD"; "LED", "QLED", "OLED").
  - Smart: "sí", "no" o nulo.
  - Cantidad: entero > 0.
  - Precio unitario y valor total del ítem: pesos colombianos con 2 decimales, > 0. Los formatos colombianos se interpretan con punto como separador de miles y coma como separador decimal ("$ 2.150.000,00" = 2150000,00). Un valor en una moneda distinta del peso colombiano queda nulo con la observación "moneda distinta de COP".
  - Valor y tasa de IVA, si el documento los publica (la base tributaria la determina HU-023).
  - Etapa del precio: "adjudicado" (oferta del adjudicatario, aceptación de oferta, evaluación con adjudicatario identificado), "contratado" (contrato) o "presupuesto o cotización" (estudio previo, precios techo, cotizaciones).
  - Tipo de precio unitario: `explicito` cuando el precio unitario está publicado en el documento; `derivado` solo lo asigna HU-024.
- **RN-05 — Evidencia obligatoria (FR-027):** todo campo no nulo debe tener documento, versión y ubicación ("página N", "hoja H, celda C" u "hoja H, imagen N") existente en la representación del documento. Un campo sin ubicación, con un documento no enviado o con una ubicación inexistente se deja nulo y se registra "dato sin evidencia válida descartado" con el valor descartado.
- **RN-06 — No inventar:** un dato que no está en los documentos queda nulo. Ningún campo se completa con valores por defecto ni con inferencias externas a los documentos.
- **RN-07 — Confianza:** cada campo no nulo registra el nivel de confianza devuelto por el extractor como número entre 0,00 y 1,00 (si el extractor devuelve niveles "alta", "media" o "baja", se registran como 0,90, 0,60 y 0,30). Una confianza fuera del rango 0,00–1,00 o ausente en un campo no nulo hace que ese campo se deje nulo con la observación "valor fuera de rango descartado". No se interpreta como probabilidad de acierto; su uso es de HU-026.
- **RN-08 — Solo el adjudicatario:** si los documentos contienen precios de varios oferentes, solo se registran los del oferente identificado como adjudicado. Si no se puede identificar, precio unitario y valor total del ítem quedan nulos con la observación "oferta adjudicada no identificable". Los precios de los demás oferentes no se registran (FR-026 fuera del MVP).
- **RN-09 — Precedencia entre documentos:** ante valores distintos del mismo campo: contrato > aceptación de oferta > oferta del adjudicatario > evaluación económica (fila del adjudicatario) > cotizaciones y presupuesto. Se registra el de mayor precedencia y se anota el conflicto con ambos valores y sus ubicaciones; el ítem queda marcado "con conflicto entre documentos".
- **RN-10 — Valor de datos abiertos (FR-100):** el `valor_del_contrato` de datos abiertos nunca se usa como precio unitario, como valor total del ítem, ni para calcular o completar datos del ítem. Se conserva y se muestra solo como "valor del contrato (datos abiertos, referencia)".
- **RN-11 — Lote:** si el proceso tiene "lote no determinado", cada ítem extraído queda marcado igual para revisión.
- **RN-12 — Identificador del ítem:** `{id_contrato}-{NN}`, con NN consecutivo de 01 a 99 en el orden en que aparecen en el documento de mayor precedencia.
- **RN-13 — Datos no permitidos:** solo se guardan los campos de RN-04, las evidencias y las observaciones. Cualquier otro dato devuelto (ej. números de cuenta, documentos de identidad) se descarta sin almacenarse.
- **RN-14 — Validación de la respuesta:** la respuesta debe cumplir el formato esperado (ítems, campos, tipos y rangos de RN-04). Si no lo cumple, se repite la solicitud una vez; si vuelve a fallar: "extracción fallida: respuesta inválida del extractor". Un campo con tipo o rango inválido (ej. cantidad 0 o negativa) se deja nulo con la observación "valor fuera de rango descartado".
- **RN-15 — Falla del servicio:** error o tiempo de espera del servicio de IA (configuración inicial: 300 segundos por solicitud) se reintenta con espera exponencial (configuración inicial: 3 reintentos). Agotados: "extracción fallida: servicio de IA no disponible". En cualquier falla no se guardan ítems parciales.
- **RN-16 — Resultado del proceso:** "extraído" (con número de ítems), "extraído sin ítems de televisor" (con la observación del extractor) o "extracción fallida" (con motivo). Las fallas se reintentan en la siguiente ejecución, hasta 3 ejecuciones (configurable); después el proceso queda "extracción fallida: requiere intervención".
- **RN-17 — Reextracción:** al reextraer, la extracción anterior se conserva como versión previa. Los campos ya validados o corregidos por el Administrador no se sobrescriben: si el nuevo valor difiere, se registra como "propuesta de reextracción" y el ítem pasa a revisión.
- **RN-18 — Efectos posteriores:** al registrar los datos se dispara la conservación de evidencia (HU-021), y se entregan a la determinación de base tributaria (HU-023), precio derivado (HU-024), información insuficiente (HU-025), confianza (HU-026) e inconsistencias (HU-027). El costo y el tiempo se registran según HU-030.

### Interfaz

Sin interfaz gráfica obligatoria en esta HU. Los ítems extraídos y su evidencia quedan disponibles para consultas del Administrador y para las vistas de ficha y señal de otras épicas.

### Sistemas Externos (Si aplica)

- **Componente de extracción con IA multimodal** (modelo y servicio de OCR o lectura multimodal definidos en arquitectura). Credenciales en gestor de secretos o variables de entorno cifradas.

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

**Historias relacionadas:** HU-019, HU-020 (entrada), HU-021 (evidencia), HU-023 (IVA), HU-024 (precio derivado), HU-025 (información insuficiente), HU-026 (confianza y umbral), HU-027 (inconsistencias), HU-029 (desactivación de IA), HU-030 (costo y tiempo).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Se registra la etapa del precio (adjudicado, contratado, presupuesto o cotización), como en D4, para no confundir presupuesto con precio pagado → RN-04.
- Precedencia entre documentos ante valores distintos: contrato > aceptación > oferta del adjudicatario > evaluación > cotización/presupuesto → RN-09.
- Una extracción por proceso con el paquete priorizado completo, como en D4 → RN-02.
- Escala de confianza 0,00–1,00; los niveles cualitativos se mapean a 0,90 / 0,60 / 0,30 → RN-07.
- El valor de datos abiertos no se entrega al extractor → RN-02, RN-10.
- Tiempo de espera inicial de 300 s por solicitud, 3 reintentos y 3 ejecuciones antes de requerir intervención → RN-15, RN-16.
- Los campos validados por el Administrador no se sobrescriben en una reextracción → RN-17.

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
