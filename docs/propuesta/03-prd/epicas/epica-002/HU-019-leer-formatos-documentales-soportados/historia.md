# Historia #019: Leer los formatos documentales soportados y generar su representación con ubicaciones

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Preparar Documentos para la Lectura  
**Prioridad:** Crítica  
**FRs relacionados:** FR-022

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema abra los documentos seleccionados en PDF (con y sin capa de texto), XLSX/XLS, DOCX/DOC, JPG y PNG y genere de cada uno una representación legible dividida en páginas, u hojas y celdas,  
**Para** que la extracción reciba el contenido en un formato uniforme y cada dato extraído pueda ubicarse en la página, hoja o celda exacta del documento.

## Descripción

D4 encontró documentos PDF nativos y escaneados, hojas de cálculo con ofertas económicas, documentos de texto e imágenes. Esta HU convierte cada documento seleccionado y elegible en una representación legible con ubicaciones estables: páginas numeradas para PDF, documentos de texto e imágenes, y hojas con referencias de celda para hojas de cálculo. Usa solo lectura determinística del archivo (capa de texto, celdas, texto del documento); la detección de páginas que requieren lectura visual es HU-020 y la lectura con IA es HU-022.

Los archivos de formatos no soportados, dañados o protegidos con contraseña de apertura quedan no elegibles y liberan su cupo en la priorización. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: PDF con capa de texto

- **Dado** que el documento 600002 "Propuesta_economica_ganador.pdf" tiene 3 páginas con capa de texto
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** la representación tiene 3 unidades "página 1", "página 2" y "página 3", cada una con su texto en orden de lectura y con las filas de las tablas separadas por "|", y el documento queda "preparado"

### Escenario 2: PDF escaneado sin capa de texto

- **Dado** que el documento "Oferta economica firmada.pdf" tiene 4 páginas sin capa de texto
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** la representación tiene 4 páginas con texto vacío y la anotación "sin capa de texto", y el documento queda "preparado" (la necesidad de lectura visual la decide HU-020)

### Escenario 3: Hoja de cálculo XLSX o XLS

- **Dado** que "Anexo/precios.xlsx" tiene la hoja "Oferta" con "B5" = "Televisor 55 pulgadas", "C5" = 8, "D5" = fórmula que resulta en 2150000 y "E5" = fórmula que resulta en 17200000, y una hoja oculta "Base"
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** la representación contiene la hoja "Oferta" con cada celda con valor y su referencia (`Oferta!B5`, `Oferta!C5`, `Oferta!D5` = 2150000, `Oferta!E5` = 17200000, con el valor calculado y no la fórmula) y la hoja "Base" marcada "oculta"

### Escenario 4: Documento DOCX o DOC

- **Dado** que "Aceptacion de oferta.docx" tiene párrafos y una tabla de ítems
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** el documento se convierte a una representación paginada; cada página tiene su texto y sus tablas con filas separadas por "|", y la versión paginada se conserva junto al original para que la página citada sea reproducible

### Escenario 5: Imagen JPG o PNG

- **Dado** que el documento "Cotizacion.jpg" es una fotografía de una cotización
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** la representación tiene una única "página 1" sin texto y marcada "imagen", y el documento queda "preparado"

### Escenario 6: Formato no soportado

- **Dado** que el documento seleccionado es "Plano.dwg" o "Video.mp4"
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** queda "no elegible: formato no soportado" y se recalcula la priorización del proceso

### Escenario 7: Archivo dañado

- **Dado** que un PDF no se puede abrir porque su estructura está corrupta
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** queda "no elegible: archivo dañado" con el error de apertura y se recalcula la priorización

### Escenario 8: PDF protegido con contraseña de apertura

- **Dado** que un PDF exige contraseña para abrirse
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** queda "no elegible: archivo protegido", sin intentar contraseñas; si el PDF solo tiene restricciones de edición o impresión pero se abre sin contraseña, se lee normalmente

### Escenario 9: Extensión que no coincide con el contenido

- **Dado** que el archivo "oferta.pdf" es en realidad un XLSX
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** se lee como XLSX según su contenido y se anota "extensión no coincide con el contenido"

### Escenario 10: Documento que supera el máximo de páginas

- **Dado** que un estudio previo tiene 420 páginas y el máximo configurado es 300
- **Cuando** se ejecuta la preparación de documentos
- **Entonces** se preparan las páginas 1 a 300, el documento queda "preparado" con la anotación "truncado por límite de páginas: 300 de 420"

### Escenario 11: Todos los documentos del proceso preparados

- **Dado** que los 8 documentos seleccionados del proceso `CO1.BDOS.1234567` quedaron "preparado" o "no elegible"
- **Cuando** termina la preparación del último
- **Entonces** el proceso pasa a "documentos preparados" con el número de documentos preparados; si ninguno quedó preparado, el proceso queda "sin documentos legibles"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO); el proceso es automático.
- **Permisos requeridos:** Rol Administrador para consultar las representaciones y los estados. El Analista no accede.
- **Valor de negocio:** Uniformiza documentos heterogéneos y garantiza ubicaciones estables para la evidencia (base de FR-027 y de la trazabilidad de las señales).

### Reglas de Negocio

- **RN-01 — Entrada:** documentos "seleccionado" y elegibles (descargados o internos de comprimidos) de la priorización vigente.
- **RN-02 — Formatos soportados:** PDF (con y sin capa de texto), XLSX, XLS, DOCX, DOC, JPG/JPEG y PNG. El formato se determina por la firma del contenido; si no coincide con la extensión, se usa el del contenido y se anota "extensión no coincide con el contenido". Cualquier otro formato: "no elegible: formato no soportado".
- **RN-03 — PDF:** una unidad por página, numerada desde 1 en el orden del archivo. Texto de la capa de texto en orden de lectura; filas de tablas reconocibles con celdas separadas por " | ". Página sin capa de texto: texto vacío con anotación "sin capa de texto".
- **RN-04 — Hojas de cálculo (XLSX/XLS):** una unidad por hoja, con su nombre; cada celda con valor se registra con su referencia `{hoja}!{columna}{fila}` y su valor calculado (nunca la fórmula; si la fórmula no tiene valor calculado guardado, se registra vacía con la anotación "fórmula sin valor calculado"). Las celdas combinadas se registran en la celda superior izquierda. Las hojas ocultas se incluyen marcadas "oculta". Números se conservan sin redondeo; fechas en formato AAAA-MM-DD.
- **RN-05 — Documentos de texto (DOCX/DOC):** se convierten a una representación paginada, numerada desde 1; cada página incluye su texto y sus tablas (celdas separadas por " | "). La versión paginada se conserva junto al original con el mismo identificador del documento, para que una cita "página N" sea reproducible.
- **RN-06 — Imágenes (JPG/PNG):** una única unidad "página 1", sin texto y marcada "imagen".
- **RN-07 — Imágenes incrustadas:** por cada página (PDF o representación paginada) se registra el número de imágenes incrustadas y el porcentaje del área de la página que ocupan, como insumo de HU-020.
- **RN-08 — Archivos dañados:** si el archivo no se puede abrir, queda "no elegible: archivo dañado" con el error. Si se abre pero una página falla, esa página queda con texto vacío y la anotación "página no legible", y el resto se prepara.
- **RN-09 — Protegidos:** un archivo que exige contraseña para abrirse queda "no elegible: archivo protegido"; nunca se prueban contraseñas. Las restricciones que no impiden abrir el archivo (edición, impresión, copia) no impiden la lectura.
- **RN-10 — Límites (configurables):** máximo de páginas por documento (configuración inicial: 300) y máximo de celdas con valor por hoja de cálculo (configuración inicial: 100.000). Al superarlos se preparan las primeras páginas o celdas (por hoja en orden, fila por fila) y se anota "truncado por límite de páginas: N de M" o "truncado por límite de celdas: N de M".
- **RN-11 — Texto:** se guarda en UTF-8, conservando tildes y "ñ"; se eliminan caracteres de control.
- **RN-12 — No elegibles:** "formato no soportado", "archivo dañado" y "archivo protegido" disparan el recalculo de la priorización del proceso (HU-015).
- **RN-13 — Estado del documento y del proceso:** cada documento queda "preparado" o "no elegible: {motivo}". Cuando todos los seleccionados del proceso están en uno de esos estados, el proceso pasa a "documentos preparados" (con el conteo) o, si ninguno quedó preparado, a "sin documentos legibles".
- **RN-14 — Sin IA:** esta HU no invoca servicios de IA; funciona aunque la extracción con IA esté desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. Representaciones y estados consultables por documento mediante consultas o registros.

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre archivos ya descargados.

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

**Historias relacionadas:** HU-015 (recalculo), HU-018 (archivos internos), HU-020 (detección de lectura visual), HU-021 (copia de evidencia), HU-022 (extracción).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- DOCX/DOC se convierten a representación paginada para poder citar "página N", y esa versión se conserva junto al original → RN-05.
- En hojas de cálculo se usa el valor calculado de las fórmulas, no la fórmula → RN-04.
- Límites iniciales de 300 páginas por documento y 100.000 celdas por hoja, con truncado anotado → RN-10.
- Las restricciones de PDF que no impiden abrir el archivo no impiden su lectura → RN-09.

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
