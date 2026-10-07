# Historia #015: Priorizar los documentos relevantes de cada proceso para la extracción

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Obtener y Priorizar Documentos del Proceso  
**Prioridad:** Crítica  
**FRs relacionados:** FR-019 (priorización por nombre, descripción y contenido; estrategia inicial de ~8 documentos; lote correcto)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema ordene los documentos de cada proceso según su probabilidad de contener precios y cantidades de televisores y seleccione solo los más relevantes, dentro de un límite configurable,  
**Para** extraer los datos del bien adjudicado sin procesar todos los documentos del proceso, reduciendo costo y ruido sin perder anexos, cotizaciones ni ofertas que sí traen el precio.

## Descripción

Un proceso de SECOP II publica en mediana 21 a 23 documentos (hasta 419), y la mayoría no sirve para extraer precios (CDP, pólizas, RUT, certificados). El spike D4 mostró que limitar la selección a 4 documentos dejó por fuera anexos con precios, y que en procesos por lotes se descargaban documentos de otro lote.

Esta HU clasifica cada documento del inventario (HU-014) en una **categoría documental** a partir de su nombre y descripción, lo ordena por la prioridad configurada de esa categoría y selecciona los primeros N (estrategia inicial: 8, ajustable según evidencia; no es una cantidad fija). Los archivos comprimidos no consumen cupo: se marcan para expandir y sus archivos internos compiten por los cupos con los demás. Cuando un documento resulta no elegible por su **contenido** (vacío, formulario en blanco, duplicado, descarga fallida, formato no soportado), la priorización se recalcula y el cupo pasa al siguiente documento. En procesos por lotes, se descartan los documentos de lotes que no corresponden al televisor.

No requiere interfaz gráfica: el resultado de la priorización se consulta por proceso mediante consultas o registros.

---

## Criterios de Aceptación

### Escenario 1: Selección de los 8 documentos más relevantes

- **Dado** que el proceso `CO1.BDOS.1234567` tiene 15 documentos válidos: "Informe de evaluación económica.pdf", "Propuesta_economica_ganador.pdf", "ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx", "Aceptacion de oferta.pdf", "Anexo tecnico.pdf", "Contrato 045-2025.pdf", "Estudio previo.pdf", "Oferta.pdf", "Invitacion publica.pdf", "Cotizaciones.zip", "CDP 123.pdf", "Poliza de cumplimiento.pdf", "RUT proveedor.pdf", "Garantia de seriedad de la oferta.pdf" y "foto1.jpg", y el límite configurado es 8
- **Cuando** se ejecuta la priorización
- **Entonces** quedan seleccionados, en este orden: evaluación económica, los dos de propuesta económica (el de fecha de carga más reciente primero), aceptación de oferta, anexo técnico, contrato, estudio previo y oferta; "Invitacion publica.pdf" queda "no seleccionado: fuera del límite (posición 9)"; "Cotizaciones.zip" queda "contenedor por expandir"; CDP, póliza, RUT y garantía de seriedad quedan "no seleccionado: categoría excluida"; "foto1.jpg" queda "no seleccionado: sin categoría relevante"

### Escenario 2: La categoría excluida prevalece sobre una relevante

- **Dado** que el documento "Garantia de seriedad de la oferta.pdf" coincide con la palabra clave "oferta" (relevante) y con "garantia" (excluida)
- **Cuando** se ejecuta la priorización
- **Entonces** el documento queda "no seleccionado: categoría excluida (póliza o garantía)"

### Escenario 3: Menos documentos relevantes que el límite

- **Dado** que el proceso `CO1.BDOS.6666666` solo tiene 3 documentos de categorías relevantes y 9 de categorías excluidas, con límite 8
- **Cuando** se ejecuta la priorización
- **Entonces** se seleccionan los 3 relevantes y ningún documento de categoría excluida o sin categoría ocupa los cupos restantes

### Escenario 4: Ningún documento relevante

- **Dado** que el proceso `CO1.BDOS.7777777` solo tiene CDP, pólizas y certificados
- **Cuando** se ejecuta la priorización
- **Entonces** el proceso queda en estado "sin documentos relevantes" con el motivo "ningún documento corresponde a las categorías relevantes"

### Escenario 5: Archivos internos de un comprimido compiten por los cupos

- **Dado** que "Cotizaciones.zip" fue expandido y contiene "Cotizacion Alkosto.pdf" y "Cotizacion proveedor 2.pdf" (categoría cotización), y el proceso ya tenía 8 seleccionados
- **Cuando** se recalcula la priorización del proceso
- **Entonces** las dos cotizaciones entran en la posición que les da su categoría (después de aceptación de oferta y antes de anexo técnico), y los dos documentos de menor prioridad ("Estudio previo.pdf" y "Oferta.pdf") pasan a "no seleccionado: fuera del límite"

### Escenario 6: Documento no elegible por contenido libera su cupo

- **Dado** que "ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx" fue marcado como "formulario en blanco" después de descargarlo
- **Cuando** se recalcula la priorización del proceso
- **Entonces** ese documento queda "no seleccionado: formulario en blanco" y el siguiente documento en orden ("Invitacion publica.pdf") ocupa el cupo liberado

### Escenario 7: Proceso por lotes con lote del televisor determinado

- **Dado** que el objeto del contrato es "Adquisición de elementos para el LOTE 2 - televisores" y el proceso tiene "Oferta economica lote 1.pdf", "Oferta economica lote 2.pdf" y "Estudio previo.pdf"
- **Cuando** se ejecuta la priorización
- **Entonces** "Oferta economica lote 1.pdf" queda "no seleccionado: lote no corresponde al televisor"; "Oferta economica lote 2.pdf" y "Estudio previo.pdf" (sin referencia a lote) siguen elegibles

### Escenario 8: Proceso por lotes sin lote del televisor determinable

- **Dado** que los documentos mencionan "lote 1" y "lote 3", pero ni el objeto ni la descripción del contrato mencionan un lote
- **Cuando** se ejecuta la priorización
- **Entonces** no se descarta ningún documento por lote y el proceso queda marcado "lote no determinado", marca que acompaña al proceso en la extracción y en la revisión humana

### Escenario 9: Cambio del límite de documentos

- **Dado** que el Administrador cambia el límite de 8 a 10 y el proceso `CO1.BDOS.1234567` aún no ha sido extraído, mientras que `CO1.BDOS.8888888` ya fue extraído
- **Cuando** se ejecuta la siguiente priorización
- **Entonces** `CO1.BDOS.1234567` se prioriza con 10 cupos y `CO1.BDOS.8888888` conserva su priorización anterior

### Escenario 10: Límite fuera de rango

- **Dado** que el Administrador intenta configurar el límite en 0 o en 51
- **Cuando** guarda la configuración
- **Entonces** el cambio se rechaza con el mensaje "El número de documentos por proceso debe ser un entero entre 1 y 50" y se conserva el valor anterior

### Escenario 11: Nombres con tildes, mayúsculas y separadores

- **Dado** que un documento se llama "EVALUACIÓN_ECONÓMICA-DEFINITIVA.PDF" y otro tiene nombre "doc_17.pdf" con descripción "Propuesta económica del adjudicatario"
- **Cuando** se ejecuta la priorización
- **Entonces** el primero se clasifica como "evaluación económica" y el segundo como "oferta o propuesta económica" a partir de su descripción

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO); configura categorías y límite, y consulta resultados. El proceso es automático.
- **Permisos requeridos:** Rol Administrador para configurar y consultar. El Analista no accede.
- **Valor de negocio:** Selecciona los documentos donde está el precio del bien adjudicado; D4 estimó que corregir la selección sube la cobertura de precio adjudicado de ~44 % a ~47–53 % de los contratos en categoría.

### Reglas de Negocio

- **RN-01 — Entrada:** documentos registrados y no rechazados en el listado (HU-014) de procesos en estado "documentos listados".
- **RN-02 — Normalización del texto:** nombre y descripción se comparan en minúsculas, sin tildes ni diéresis, y con `_`, `-`, `.` y espacios múltiples convertidos en un espacio. Se ignora la extensión del archivo.
- **RN-03 — Categorías relevantes (configurables: palabras clave y orden).** Configuración inicial, de mayor a menor prioridad:
  1. Evaluación económica: "evaluacion economica", "informe de evaluacion", "verificacion economica", "consolidado de ofertas".
  2. Oferta o propuesta económica: "propuesta economica", "oferta economica", "formulario de precios".
  3. Anexo económico: "anexo economico", "anexo de precios", "cuadro de precios", "lista de precios".
  4. Aceptación de oferta: "aceptacion de oferta", "aceptacion oferta".
  5. Cotización: "cotizacion", "cotizaciones", "estudio de mercado", "analisis del sector".
  6. Precios techo: "precio techo", "precios techo", "presupuesto oficial".
  7. Anexo técnico: "anexo tecnico", "ficha tecnica", "especificaciones tecnicas".
  8. Contrato: "contrato", "minuta".
  9. Estudios previos: "estudio previo", "estudios previos".
  10. Oferta o propuesta general: "oferta", "propuesta".
  11. Invitación o pliego: "invitacion", "pliego".
- **RN-04 — Categorías excluidas (configurables; nunca se seleccionan):** CDP o registro presupuestal ("cdp", "disponibilidad presupuestal", "registro presupuestal"); póliza o garantía ("poliza", "garantia"); RUT ("rut"); existencia y representación ("camara de comercio", "existencia y representacion"); identidad ("cedula", "documento de identidad"); antecedentes ("antecedentes", "procuraduria", "contraloria", "policia"); certificado bancario ("certificacion bancaria", "certificado bancario"); seguridad social ("seguridad social", "parafiscales"); hoja de vida y experiencia ("hoja de vida", "experiencia"). Las palabras clave se comparan como palabras completas (ej. "rut" no coincide dentro de "ruta").
- **RN-05 — Asignación de categoría:** si el texto coincide con una categoría excluida, el documento queda "no seleccionado: categoría excluida ({categoría})", aunque coincida también con una relevante. Si coincide con varias relevantes, se asigna la de mayor prioridad. Si no coincide con ninguna, queda "no seleccionado: sin categoría relevante". El nombre y la descripción se evalúan juntos.
- **RN-06 — Orden y desempate:** por prioridad de categoría; dentro de la misma categoría, fecha de carga más reciente primero (fecha nula al final); luego `id_documento` ascendente. El resultado es determinístico: misma entrada y misma configuración producen la misma selección.
- **RN-07 — Límite (configurable):** número de documentos seleccionados por proceso. Configuración inicial: 8. Rango válido: entero entre 1 y 50; fuera de rango → mensaje "El número de documentos por proceso debe ser un entero entre 1 y 50" y se conserva el valor anterior. Si hay menos documentos relevantes que el límite, se seleccionan todos los relevantes y los cupos restantes quedan vacíos.
- **RN-08 — Comprimidos:** los archivos .zip y .rar que no estén en una categoría excluida quedan "contenedor por expandir" y no consumen cupo; máximo de contenedores por proceso configurable (configuración inicial: 10, elegidos por prioridad de su nombre y luego por RN-06). Los archivos internos, una vez expandidos (HU-018), se clasifican con estas mismas reglas usando su propio nombre y compiten por los cupos.
- **RN-09 — Recalculo por elegibilidad de contenido:** la priorización del proceso se recalcula cuando un documento pasa a no elegible — "archivo vacío", "formulario en blanco", "duplicado", "descarga fallida definitiva", "descarga bloqueada", "formato no soportado", "archivo protegido" o "archivo dañado" — o cuando entran archivos internos de un comprimido. El documento no elegible queda "no seleccionado: {motivo}" y su cupo pasa al siguiente en orden.
- **RN-10 — Lotes:** un proceso es "por lotes" cuando al menos dos documentos mencionan lotes con números distintos (patrones "lote N", "lote no. N", "lote nº N", con N arábigo de 1 a 99 o romano de I a X, que se convierte a arábigo). El lote del televisor se toma del objeto o la descripción del contrato con el mismo patrón. Si hay un único lote del televisor: los documentos que mencionan otro número de lote quedan "no seleccionado: lote no corresponde al televisor", y los que no mencionan lote siguen elegibles. Si el contrato no menciona lote o menciona más de uno: no se descarta ningún documento por lote y el proceso queda marcado "lote no determinado".
- **RN-11 — Resultado registrado por documento:** estado ("seleccionado" con posición y categoría, "no seleccionado" con motivo, o "contenedor por expandir"), categoría asignada, fecha de la priorización y versión de la configuración usada.
- **RN-12 — Estado del proceso:** "documentos priorizados" (con número de seleccionados) o "sin documentos relevantes" (0 seleccionados y 0 contenedores) con el motivo "ningún documento corresponde a las categorías relevantes".
- **RN-13 — Cambios de configuración:** aplican a los procesos aún no extraídos en la siguiente ejecución. Los procesos ya extraídos conservan su priorización; solo se reprioriza si el Administrador solicita explícitamente reprocesar ese proceso. Cada cambio de configuración registra usuario, fecha, valor anterior y valor nuevo.

### Interfaz

Sin interfaz gráfica obligatoria. La configuración (categorías, palabras clave, orden, límite, máximo de contenedores) se mantiene mediante archivo o tabla de configuración o una vista administrativa mínima; el resultado se consulta por proceso mediante consultas o registros.

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre el inventario documental ya registrado y sobre los datos del contrato (objeto y descripción) ya ingeridos.

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

**Historias relacionadas:** HU-014 (inventario documental), HU-016 (descarga), HU-017 (vacíos, en blanco y duplicados), HU-018 (comprimidos), HU-022 (extracción).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El orden y las palabras clave iniciales de categorías relevantes y excluidas se toman del orden usado en D4 ampliado con las categorías que D4 recomendó agregar; son configurables → RN-03, RN-04.
- "Priorizar por contenido" se resuelve con el recalculo cuando un documento resulta no elegible por su contenido (vacío, en blanco, duplicado) → RN-09.
- Los comprimidos no consumen cupo y sus archivos internos compiten por los cupos; máximo inicial de 10 contenedores por proceso → RN-08.
- El rango válido del límite es 1 a 50 → RN-07.
- El lote del televisor se determina por el objeto o la descripción del contrato; si no se puede, no se descarta por lote y se marca "lote no determinado" → RN-10.
- Los procesos ya extraídos no se repriorizan automáticamente al cambiar la configuración → RN-13.

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
