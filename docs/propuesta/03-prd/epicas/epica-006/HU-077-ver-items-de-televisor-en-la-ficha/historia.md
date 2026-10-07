# Historia #077: Ver los ítems de televisor extraídos en la ficha del contrato

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Consulta de la Ficha del Contrato  
**Prioridad:** Crítica  
**FRs relacionados:** FR-074

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la ficha cada ítem de televisor del contrato con sus características, cantidad, precio unitario, base tributaria, origen del dato y estado de validación,  
**Para** saber exactamente qué se compró, a qué precio unitario y con qué respaldo documental, antes de revisar cualquier comparación.

## Descripción

Esta HU construye la sección **"Ítems de televisor"** de la ficha del contrato (HU-076). Muestra una tarjeta por ítem de televisor con los datos extraídos de los documentos (SECOP II) o publicados de forma estructurada (TVEC), su producto normalizado, el tipo de precio unitario (explícito o derivado, con su fórmula), la base tributaria, la ubicación de la evidencia (documento y página, u hoja y celda) y el estado de validación del dato.

Un contrato puede ser mixto (por ejemplo, computadores y un televisor): solo los televisores entran al análisis. Los demás ítems candidatos que fueron excluidos se listan aparte, plegados, con su motivo de exclusión, para que el Analista entienda por qué no se analizan.

Esta HU solo presenta datos ya extraídos, normalizados y validados por otros procesos de la plataforma; no extrae, corrige ni reclasifica. Los benchmarks de cada ítem se muestran en HU-078, las señales en HU-079 y los motivos de información insuficiente en detalle en HU-082.

---

## Criterios de Aceptación

### Escenario 1: Ver los ítems de un contrato SECOP II (happy path)

- **Dado** que el contrato tiene ítems de televisor con clasificación "incluido" extraídos de documentos
- **Cuando** el Analista abre la sección "Ítems de televisor"
- **Entonces** ve una tarjeta por ítem con los campos de RN-02, la marca del tipo de precio, la base tributaria, el estado de validación y la acción "Ver evidencia", y el título "Ítems de televisor ({n})"

### Escenario 2: Ver la evidencia de un dato extraído

- **Dado** que un ítem SECOP II tiene evidencia registrada
- **Cuando** el Analista activa "Ver evidencia"
- **Entonces** se abre en una pestaña nueva la copia conservada del documento en la página (o la hoja y celda) indicada, y la tarjeta muestra el texto "Fuente: {nombre del documento}, página {n}" (o "hoja {nombre}, celda {ref}")

### Escenario 3: Precio unitario derivado

- **Dado** que el precio unitario del ítem es derivado
- **Cuando** se muestra la tarjeta
- **Entonces** el precio aparece con la marca "Derivado" y el detalle "Calculado como valor total del ítem ({valor}) / cantidad ({cantidad})", junto con la nota "Un precio derivado tiene menor confianza que un precio publicado en el documento."

### Escenario 4: Base tributaria del precio

- **Dado** que el precio extraído tiene base "con IVA", "sin IVA" o "indeterminada"
- **Cuando** se muestra la tarjeta
- **Entonces** aparece "IVA: incluido", "IVA: no incluido" o "IVA: base indeterminada" respectivamente; si es indeterminada, se agrega "Las comparaciones de este ítem se marcan como incompletas."

### Escenario 5: Ítems de una orden TVEC

- **Dado** que la ficha es de una orden de compra TVEC
- **Cuando** el Analista abre la sección
- **Entonces** cada ítem muestra los datos publicados por la TVEC (descripción, cantidad, precio unitario, total), la marca "Explícito", el origen "Dato estructurado publicado por la TVEC (orden {número})" y no muestra la acción "Ver evidencia" de documento

### Escenario 6: Dato corregido por el revisor

- **Dado** que el revisor corrigió un dato de un ítem (ej. la cantidad)
- **Cuando** se muestra la tarjeta
- **Entonces** el campo muestra el valor corregido con la marca "Corregido por revisión humana el {fecha}" y la opción "Ver valor original", que muestra el valor extraído originalmente

### Escenario 7: Ítem pendiente de revisión humana

- **Dado** que un ítem tiene clasificación "requiere revisión" o datos críticos pendientes de revisión por baja confianza o inconsistencia aritmética
- **Cuando** se muestra la sección
- **Entonces** la tarjeta aparece con la marca "Pendiente de revisión" y la nota "Este dato aún no ha sido validado; puede cambiar después de la revisión."; si la inconsistencia es aritmética, la nota agrega "Cantidad × precio unitario no coincide con el total del ítem: se revisa como posible error de lectura, no como irregularidad."

### Escenario 8: Ítem con información insuficiente

- **Dado** que un ítem quedó marcado como "información insuficiente" porque no se lograron extraer cantidad y precio unitario
- **Cuando** se muestra la tarjeta
- **Entonces** aparece la marca "Información insuficiente", los campos faltantes muestran "No disponible" y el enlace "Ver motivo" lleva a la sección de motivos de información insuficiente

### Escenario 9: Ítems excluidos del análisis en contratos mixtos

- **Dado** que el contrato tiene ítems candidatos excluidos (ej. un monitor o un servicio de instalación)
- **Cuando** el Analista despliega "Otros ítems excluidos del análisis ({n})"
- **Entonces** ve cada ítem excluido con su descripción y su motivo de exclusión, sin precio ni comparación

### Escenario 10: Contrato sin ítems extraídos todavía

- **Dado** que el contrato aún no tiene ítems extraídos
- **Cuando** el Analista abre la sección
- **Entonces** ve "Todavía no hay ítems de televisor extraídos para este contrato. Revisa el estado de procesamiento para conocer en qué etapa está."

### Escenario 11: Evidencia no disponible

- **Dado** que la copia conservada del documento no está disponible o falla al abrirse
- **Cuando** el Analista activa "Ver evidencia"
- **Entonces** ve "No fue posible abrir la evidencia en este momento. Puedes consultar el documento en la fuente oficial." con el enlace a la URL original del documento si existe

### Escenario 12: Posicionamiento en un ítem

- **Dado** que el Analista llegó a la ficha desde un ítem o una señal
- **Cuando** se carga la sección
- **Entonces** la tarjeta de ese ítem queda visible, resaltada y con el foco del teclado

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** El ítem es la unidad de análisis; ver sus datos con evidencia y estado de validación permite al analista juzgar si la comparación posterior es confiable.

### Reglas de Negocio

- **RN-01 Ítems mostrados:** tarjetas para los ítems con clasificación "incluido" y para los de "requiere revisión" (con su marca). Los "excluido" van solo en el bloque plegado "Otros ítems excluidos del análisis". El conteo del título cuenta solo los "incluido".
- **RN-02 Campos de la tarjeta:** descripción original del ítem; producto normalizado (marca, modelo normalizado, tamaño en pulgadas, resolución, tecnología de pantalla, Smart sí/no, año o generación aproximada); cantidad; precio unitario; valor total del ítem; base tributaria; tipo de precio unitario; origen del dato; estado de validación. Campo no extraído o no publicado → "No disponible".
- **RN-03 Tipo de precio unitario:** "Explícito" = publicado en el documento o en el dataset TVEC; "Derivado" = valor total del ítem / cantidad, calculado por la plataforma bajo sus reglas estrictas. Para "Derivado" se muestran el valor total usado, la cantidad usada y la fórmula (Escenario 3).
- **RN-04 Base tributaria:** valores "con IVA", "sin IVA" o "indeterminada", tal como los registró la extracción. Indeterminada → nota de comparación incompleta.
- **RN-05 Origen y evidencia:** SECOP II: nombre del documento, página (PDF, DOCX, imagen) u hoja y celda (XLSX/XLS) donde se encontró el dato; "Ver evidencia" abre la copia conservada del documento en esa ubicación. TVEC: "Dato estructurado publicado por la TVEC (orden {número})", sin acción de evidencia documental.
- **RN-06 Estado de validación del ítem:** "Aceptado automáticamente" (datos críticos aceptados según el umbral configurable de aceptación de la extracción), "Validado por revisión humana", "Corregido por revisión humana" o "Pendiente de revisión". El puntaje numérico de confianza del extractor no se muestra, porque no es una probabilidad calibrada de corrección.
- **RN-07 Valor corregido:** se muestra el valor corregido y la fecha de la corrección; "Ver valor original" muestra el valor extraído inicialmente. No se muestra el nombre del revisor al Analista.
- **RN-08 Inconsistencias aritméticas:** se presentan como señales de revisión de calidad de la evidencia, con el texto del Escenario 7, nunca como irregularidades.
- **RN-09 Información insuficiente:** marca "Información insuficiente" y enlace "Ver motivo"; el detalle de motivos está en la sección correspondiente de la ficha.
- **RN-10 Ítems excluidos:** se muestran descripción y motivo de exclusión registrado por la clasificación (ej. "Monitor, fuera del límite de categoría", "Precio inseparable de instalación"); sin precio ni comparación. Si no hay excluidos, el bloque no se muestra.
- **RN-11 Orden de las tarjetas:** según el orden del ítem en el documento o en la orden TVEC; si no existe, por descripción alfabética.
- **RN-12 Formatos:** precios `$ 2.862.500`; cantidades enteras; tamaño `65"`; fechas `DD/MM/AAAA`.
- **RN-13 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-14 Rendimiento:** la sección carga dentro del objetivo de la ficha completa de ≤ 3 segundos (p95) con 20 usuarios concurrentes (objetivo inicial de diseño); la copia del documento se abre bajo demanda y no cuenta en ese tiempo.
- **RN-15 Accesibilidad y responsive (valores iniciales de diseño):** WCAG 2.1 AA; las marcas ("Explícito", "Derivado", "Pendiente de revisión", "Corregido…", "Información insuficiente") son texto y no solo color; el bloque plegado se abre con teclado y anuncia su estado; en móvil desde 360 px las tarjetas ocupan el ancho completo sin perder campos.

### Interfaz

- Sección "Ítems de televisor ({n})" con tarjetas por ítem: encabezado con producto normalizado (o descripción), lista etiqueta–valor de los campos de RN-02, marcas, línea "Fuente: …" y acción "Ver evidencia".
- Opción "Ver valor original" en campos corregidos.
- Enlace "Ver motivo" en ítems con información insuficiente.
- Bloque plegado "Otros ítems excluidos del análisis ({n})".
- Estados: sin ítems extraídos; evidencia no disponible.

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real. Usa los ítems, normalización, clasificación, validaciones y copias de evidencia ya almacenados por la plataforma; el enlace alternativo lleva a la URL original del documento en SECOP II.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-076 (estructura de la ficha), HU-078 (benchmarks del ítem), HU-079 (señales), HU-080 (documentos), HU-082 (motivos de información insuficiente)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-06):** al Analista se le muestra el estado de validación del dato, no el puntaje numérico de confianza del extractor.
- **Resuelto (RN-07):** el Analista ve el valor corregido, la fecha y el valor original, pero no la identidad del revisor.
- **Resuelto (RN-01, RN-10):** los ítems excluidos de contratos mixtos se muestran plegados con su motivo, sin precio ni comparación.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-006 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
