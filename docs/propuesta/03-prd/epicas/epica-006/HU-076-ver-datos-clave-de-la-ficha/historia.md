# Historia #076: Ver los datos clave del contrato y el enlace a la fuente oficial en la ficha

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
**Quiero** abrir la ficha de un contrato SECOP II u orden de compra TVEC y ver sus datos clave (entidad, proveedor, valor, modalidad, fechas, objeto) con un enlace a la fuente oficial,  
**Para** entender el contexto de la compra y poder verificarla directamente en la publicación oficial.

## Descripción

Esta HU construye la **ficha del contrato**: su estructura general (encabezado, navegación por secciones, estados de carga, error y no encontrado, control de acceso) y la sección **"Datos clave"** con el enlace a la fuente oficial. Las demás secciones de la ficha se especifican en sus propias HUs: ítems de televisor (HU-077), benchmarks (HU-078), señales (HU-079), documentos (HU-080), estado de procesamiento (HU-081), motivos de información insuficiente (HU-082) y fecha de actualización (HU-083). Esta HU deja el espacio y el índice de navegación para ellas.

La ficha sirve tanto para contratos de SECOP II como para órdenes de compra de la TVEC; la orden TVEC se presenta como registro de compra equivalente a un contrato, con su etiqueta de fuente. Solo muestra datos públicos ingeridos; no muestra los campos personales sensibles excluidos de la ingesta (banco, tipo y número de cuenta, documentos de identidad de representantes legales, supervisores y ordenadores del gasto). Además, por decisión del PO (2026-10-05, Ley 1581 de 2012), el documento del proveedor solo se muestra cuando es un NIT de persona jurídica; si el proveedor es persona natural, la ficha muestra la leyenda "Persona natural — documento no visible" en lugar del número (RN-13).

---

## Criterios de Aceptación

### Escenario 1: Abrir la ficha de un contrato SECOP II (happy path)

- **Dado** que el Analista inició sesión y activa un contrato SECOP II desde la exploración, la lista de señales o una URL directa
- **Cuando** se carga la ficha
- **Entonces** ve el encabezado con la etiqueta "SECOP II", el ID del contrato y el objeto, y la sección "Datos clave" con los campos de RN-02 y el enlace "Ver en SECOP II"

### Escenario 2: Abrir la ficha de una orden de compra TVEC

- **Dado** que el Analista activa una orden de compra TVEC
- **Cuando** se carga la ficha
- **Entonces** ve el encabezado con la etiqueta "TVEC", el título "Orden de compra {número}" y la sección "Datos clave" con los campos de RN-03

### Escenario 3: Abrir el enlace a la fuente oficial

- **Dado** que la ficha tiene URL pública del proceso
- **Cuando** el Analista activa "Ver en SECOP II" o "Ver en la Tienda Virtual"
- **Entonces** la publicación oficial se abre en una pestaña nueva y la ficha permanece abierta

### Escenario 4: Registro sin URL pública

- **Dado** que la fuente no publicó la URL del proceso u orden
- **Cuando** se muestra la sección "Datos clave"
- **Entonces** en lugar del enlace aparece "Enlace a la fuente oficial no disponible. Identificador en la fuente: {identificador}."

### Escenario 5: Valor del contrato como dato de referencia

- **Dado** que la ficha muestra el valor del contrato u orden publicado en datos abiertos
- **Cuando** el Analista lo ve
- **Entonces** junto al valor aparece la nota "Valor publicado en datos abiertos. Es un dato de referencia del contrato: no se usa como precio unitario ni como valor adjudicado de los ítems."

### Escenario 6: Campos sin dato

- **Dado** que la fuente no publicó alguno de los campos de datos clave
- **Cuando** se muestra la sección
- **Entonces** el campo aparece con el texto "Sin dato en la fuente"

### Escenario 7: Navegar por las secciones de la ficha

- **Dado** que la ficha está cargada
- **Cuando** el Analista usa el índice de secciones ("Datos clave", "Estado de procesamiento", "Ítems de televisor", "Benchmarks", "Señales", "Documentos")
- **Entonces** la vista se desplaza a la sección elegida y el foco del teclado pasa a su título

### Escenario 8: Abrir la ficha posicionada en un ítem

- **Dado** que el Analista llega desde un ítem o una señal
- **Cuando** se carga la ficha
- **Entonces** la vista se posiciona en ese ítem dentro de la sección "Ítems de televisor" y lo resalta; si el ítem ya no existe en la ficha, se muestra la ficha desde el inicio con el aviso "El ítem solicitado ya no está disponible en esta ficha."

### Escenario 9: Contrato inexistente

- **Dado** que el identificador de la URL no corresponde a ningún registro
- **Cuando** el Analista abre la ficha
- **Entonces** ve "No encontramos este contrato. Revisa el enlace o búscalo en Exploración." con el botón "Ir a Exploración"

### Escenario 10: Registro descartado del universo

- **Dado** que el registro existe pero todos sus ítems candidatos fueron excluidos en la clasificación
- **Cuando** el Analista abre su ficha por URL directa
- **Entonces** ve "Este registro no forma parte del universo de compras de televisores analizado: fue descartado en la clasificación." con el botón "Ir a Exploración", sin datos del registro

### Escenario 11: Error al cargar la ficha

- **Dado** que la consulta de la ficha falla o no responde en 15 segundos
- **Cuando** el Analista espera la ficha
- **Entonces** ve "No fue posible cargar la ficha. Intenta de nuevo en unos minutos." con el botón "Reintentar" (una consulta por clic)

### Escenario 12: Acceso sin sesión o con sesión expirada

- **Dado** que una persona sin sesión, o con la sesión expirada, abre la URL de una ficha
- **Cuando** el sistema procesa la solicitud
- **Entonces** no muestra datos y redirige al inicio de sesión; tras iniciar sesión vuelve a la misma ficha

### Escenario 13: Volver al origen

- **Dado** que el Analista abrió la ficha desde la exploración o la lista de señales
- **Cuando** activa "Volver"
- **Entonces** regresa a la vista de origen con su estado (filtros, orden y página); si llegó por URL directa, "Volver" lleva a "Exploración" sin filtros

### Escenario 14: Proveedor persona jurídica con NIT

- **Dado** que el contrato SECOP II tiene un proveedor con tipo de documento NIT
- **Cuando** se muestra la sección "Datos clave"
- **Entonces** el campo "Proveedor" muestra el nombre del proveedor y "NIT {número}" tal como se publica

### Escenario 15: Proveedor persona natural

- **Dado** que el contrato SECOP II tiene un proveedor con tipo de documento cédula de ciudadanía, cédula de extranjería, pasaporte u otro tipo distinto de NIT
- **Cuando** se muestra la sección "Datos clave"
- **Entonces** el campo "Proveedor" muestra el nombre del proveedor y la leyenda "Persona natural — documento no visible"; el número de documento no aparece en la ficha ni en la respuesta enviada al navegador

### Escenario 16: Proveedor sin tipo de documento o con tipo desconocido

- **Dado** que el contrato tiene documento de proveedor publicado pero el tipo de documento está vacío o no es reconocido
- **Cuando** se muestra la sección "Datos clave"
- **Entonces** el proveedor se trata como persona natural: se muestra su nombre con la leyenda "Persona natural — documento no visible" y el número no aparece

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la ficha.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** La ficha concentra el contexto del contrato y permite verificarlo en la fuente oficial, lo que sustenta la revisión de cualquier señal.

### Reglas de Negocio

- **RN-01 Identificación:** la ficha se identifica en la URL por la fuente y el identificador de origen: `id_contrato` (formato `CO1.PCCNTR.…`) para SECOP II y número de orden para TVEC.
- **RN-02 Datos clave SECOP II:** ID del contrato (`id_contrato`); proceso de compra (`proceso_de_compra`, formato `CO1.BDOS.…`); objeto del contrato (`objeto_del_contrato`, texto completo); descripción del proceso (`descripcion_del_proceso`, mostrada colapsada a 300 caracteres con "Ver más"); entidad (`nombre_entidad` y NIT `nit_entidad`); proveedor (`proveedor_adjudicado`, con el NIT `documento_proveedor` solo si `tipodocproveedor` es NIT; en otro caso, la leyenda de RN-13); valor del contrato (`valor_del_contrato`); modalidad (`modalidad_de_contratacion`); fecha de firma (`fecha_de_firma`); estado del contrato (`estado_contrato`); UNSPSC principal (`codigo_de_categoria_principal`, mostrado como 8 dígitos sin el prefijo "V1."); departamento y municipio de la entidad; enlace "Ver en SECOP II" (`urlproceso`).
- **RN-03 Datos clave TVEC:** número de orden; entidad compradora; proveedor (si la fuente publica su documento, se aplica RN-13); valor total de la orden; fecha de la orden; modalidad tal como la publica la fuente o "Tienda Virtual del Estado (TVEC)" si no se publica; departamento y municipio de la entidad cuando se publiquen; enlace "Ver en la Tienda Virtual" cuando la fuente publique la URL de la orden.
- **RN-04 Datos personales:** la ficha nunca muestra banco, tipo o número de cuenta, ni documentos de identidad de representantes legales, supervisores u ordenadores del gasto. El documento del proveedor persona natural tampoco se muestra (RN-13).
- **RN-05 Valor de referencia:** el valor del contrato u orden se muestra siempre con la nota del Escenario 5; ninguna otra sección de la ficha lo usa como precio unitario.
- **RN-06 Formatos:** fechas `DD/MM/AAAA` (hora de Colombia); valores `$ 22.900.000`; NIT tal como se publica.
- **RN-07 Nulos:** campo no publicado → "Sin dato en la fuente". Si hay proveedor publicado pero falta su tipo de documento, aplica RN-13 (se trata como persona natural). Si falta el objeto del contrato, el encabezado muestra solo la fuente y el identificador.
- **RN-08 Enlaces externos:** se abren en pestaña nueva, con el texto que indica la fuente; el ícono de enlace externo tiene texto alternativo "se abre en una pestaña nueva".
- **RN-09 Universo:** solo se muestran fichas de registros visibles en el universo de televisores (con al menos un ítem "incluido" o clasificación sin concluir); los descartados por completo muestran el mensaje del Escenario 10.
- **RN-10 Lenguaje:** la ficha no usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal" aplicados al contrato, la entidad, el proveedor o personas.
- **RN-11 Tiempo de carga:** la ficha completa carga en ≤ 3 segundos (p95) con 20 usuarios concurrentes (objetivo inicial de diseño, configurable y recalibrable); error a los 15 segundos sin respuesta (valor inicial configurable).
- **RN-12 Accesibilidad y responsive (valores iniciales de diseño):** WCAG 2.1 AA en la ficha (teclado, foco visible, contraste, títulos de sección jerárquicos); escritorio desde 1366 × 768 px (datos clave en dos columnas), tablet desde 768 px y móvil desde 360 px (una columna; índice de secciones como menú desplegable "Ir a sección"); 2 últimas versiones de Chrome, Edge, Firefox y Safari.
- **RN-13 Visibilidad del documento del proveedor (decisión PO 2026-10-05, Ley 1581 de 2012):** el tipo se toma de `tipodocproveedor`. Si es NIT (persona jurídica), se muestra "{Nombre} — NIT {número}". Si es cédula de ciudadanía, cédula de extranjería, pasaporte o cualquier otro tipo distinto de NIT, o si el tipo está vacío o es desconocido (se trata como persona natural por seguridad), se muestra "{Nombre}" con la leyenda "Persona natural — documento no visible" y el número no se incluye en la ficha, en la respuesta enviada al navegador, en el título de la página ni en textos para lectores de pantalla. El nombre del proveedor siempre se muestra. El valor almacenado solo es accesible al Administrador por medios técnicos o administrativos, fuera de la interfaz del analista.

### Interfaz

- Encabezado: etiqueta de fuente ("SECOP II" / "TVEC"), identificador, objeto (o "Orden de compra {número}"), acción "Volver".
- Índice de secciones: "Datos clave", "Estado de procesamiento", "Ítems de televisor", "Benchmarks", "Señales", "Documentos".
- Sección "Datos clave": lista etiqueta–valor con los campos de RN-02 / RN-03, nota del valor de referencia y enlace a la fuente oficial; el proveedor se muestra con su NIT (persona jurídica) o con la leyenda "Persona natural — documento no visible" (RN-13).
- Espacio para la fecha de actualización de los datos (HU-083).
- Estados: carga (indicador sobre la ficha), no encontrado, descartado, error con "Reintentar".

### Sistemas Externos (Si aplica)

- Datos ya ingeridos de SECOP II (`jbjy-vk9h`) y TVEC (`rgxm-mmea`, `usqp-5nsn` / `3hdv-smhz`).
- Enlace de salida a la publicación oficial (`urlproceso` de SECOP II o URL de la orden TVEC); la ficha no consulta esas páginas, solo enlaza a ellas.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (exploración), HU-074 (lista de señales), HU-077 a HU-082 (secciones de la ficha), HU-083 (fecha de actualización)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-03):** la ficha de una orden TVEC usa los campos de la orden; si la fuente no publica URL, se muestra el identificador con el aviso del Escenario 4.
- **Resuelto (RN-09, Escenario 10):** la ficha de un registro descartado no muestra datos e informa que fue descartado.
- **Resuelto (Escenario 13):** "Volver" restaura la vista de origen; por URL directa lleva a Exploración.
- **Resuelto (RN-13):** el documento del proveedor persona natural (tipo distinto de NIT, vacío o desconocido) no se muestra; decisión PO 2026-10-05 (Ley 1581).

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
| 2026-10-05 | 1.1 | Regla de visibilidad del documento del proveedor persona natural (decisión PO, Ley 1581) | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
