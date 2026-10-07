# Historia #080: Ver los documentos del proceso en la ficha del contrato

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
**Quiero** ver en la ficha la lista de documentos publicados del proceso, cuáles se priorizaron y procesaron, y abrir cada uno en la fuente oficial o en la copia conservada como evidencia,  
**Para** revisar por mí mismo los documentos que respaldan los datos extraídos y saber cuáles se tuvieron en cuenta.

## Descripción

Esta HU construye la sección **"Documentos"** de la ficha del contrato (HU-076). Para contratos de SECOP II lista los documentos publicados del proceso en los datasets oficiales de archivos, con su nombre, tipo, fecha de carga, si fue priorizado para la extracción y su estado de procesamiento (procesado, no priorizado, excluido por estar en blanco, duplicado, contenido en un comprimido). Cada documento enlaza a su URL oficial de descarga y, cuando se usó como evidencia de un dato, a la copia conservada.

Las órdenes de la TVEC se analizan con datos estructurados del dataset, por lo que no tienen documentos asociados en el MVP; la sección lo explica.

Esta HU solo presenta la información de documentos ya registrada por la plataforma; no descarga, prioriza ni procesa documentos.

---

## Criterios de Aceptación

### Escenario 1: Ver los documentos de un contrato SECOP II (happy path)

- **Dado** que el proceso del contrato tiene documentos registrados
- **Cuando** el Analista abre la sección "Documentos"
- **Entonces** ve el título "Documentos del proceso ({n})" y una fila por documento con nombre, tipo, fecha de carga, priorización, estado y acciones, con los documentos priorizados primero

### Escenario 2: Abrir un documento en la fuente oficial

- **Dado** que el documento tiene URL oficial de descarga
- **Cuando** el Analista activa "Abrir en SECOP II"
- **Entonces** el documento se abre desde la URL oficial en una pestaña nueva

### Escenario 3: Abrir la copia conservada de un documento usado como evidencia

- **Dado** que de un documento se extrajo información usada en un ítem o una señal
- **Cuando** el Analista activa "Ver copia conservada"
- **Entonces** se abre en una pestaña nueva la copia conservada por la plataforma y la fila muestra la marca "Usado como evidencia" y la fecha de descarga de la copia

### Escenario 4: Documento usado como evidencia que ya no está en la fuente

- **Dado** que la URL oficial de un documento usado como evidencia ya no responde o el documento cambió
- **Cuando** el Analista consulta la fila
- **Entonces** la copia conservada sigue disponible con la nota "La copia conservada corresponde a la versión descargada el {fecha}; puede diferir de la publicación actual."

### Escenario 5: Documentos excluidos por estar en blanco o duplicados

- **Dado** que algunos documentos se detectaron como formatos en blanco o como duplicados de otro documento
- **Cuando** se muestra la lista
- **Entonces** su estado aparece como "Excluido: documento en blanco o sin diligenciar" o "Excluido: duplicado de {nombre del documento}"

### Escenario 6: Archivos contenidos en un comprimido

- **Dado** que un documento publicado es un archivo .zip o .rar
- **Cuando** se muestra la lista
- **Entonces** el comprimido aparece como una fila con los archivos que contiene anidados debajo, cada uno con la indicación "Contenido en {nombre del comprimido}" y su propio estado; los archivos internos no tienen enlace propio a la fuente y se abren mediante la copia conservada cuando existe

### Escenario 7: Proceso sin documentos publicados

- **Dado** que el proceso no tiene documentos publicados en los datasets oficiales
- **Cuando** el Analista abre la sección
- **Entonces** ve "La fuente no ha publicado documentos para este proceso." y el enlace "Ver en SECOP II" del proceso

### Escenario 8: Documentos aún no obtenidos

- **Dado** que la plataforma todavía no ha consultado los documentos del proceso
- **Cuando** el Analista abre la sección
- **Entonces** ve "Los documentos de este proceso aún no se han obtenido. Revisa el estado de procesamiento."

### Escenario 9: Orden de compra TVEC

- **Dado** que la ficha es de una orden de compra TVEC
- **Cuando** el Analista abre la sección
- **Entonces** ve "Los datos de esta orden provienen del dataset estructurado de la Tienda Virtual del Estado; no se procesan documentos para las órdenes TVEC en el MVP."

### Escenario 10: Error al abrir la copia conservada

- **Dado** que la copia conservada no puede abrirse en ese momento
- **Cuando** el Analista activa "Ver copia conservada"
- **Entonces** ve "No fue posible abrir la copia conservada en este momento. Intenta de nuevo en unos minutos." y, si existe, la opción "Abrir en SECOP II"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Da trazabilidad directa al documento oficial, condición para que el analista confíe en los datos y lleve la evidencia a una veeduría, medio u organismo de control.

### Reglas de Negocio

- **RN-01 Origen:** documentos del proceso registrados desde los datasets oficiales de Archivos Descarga de SECOP II (desde 2025 e históricos por año), relacionados por el proceso de compra del contrato. Campos: `nombre_archivo`, `descripci_n`, `extensi_n`, `tamanno_archivo`, `fecha_carga`, `url_descarga_documento`, `id_documento`.
- **RN-02 Columnas:** Nombre (con la descripción publicada debajo, si existe), Tipo (extensión en mayúsculas: PDF, XLSX, XLS, DOCX, DOC, JPG, PNG, ZIP, RAR u otra tal como se publica), Tamaño (en KB o MB con una decimal), Fecha de carga (`DD/MM/AAAA`), Priorizado ("Sí" / "No"), Estado y Acciones.
- **RN-03 Estados del documento:** "Procesado" (priorizado y extraído); "Pendiente de procesamiento" (priorizado, aún no extraído); "No priorizado"; "Excluido: documento en blanco o sin diligenciar"; "Excluido: duplicado de {nombre}" (mismo hash); "Error al procesar" (con el texto "No se pudo leer el documento"); "No soportado" (formato fuera de PDF, XLSX/XLS, DOCX/DOC, JPG/PNG, ZIP/RAR).
- **RN-04 Orden:** priorizados primero; dentro de cada grupo, por fecha de carga de la más reciente a la más antigua; luego por nombre alfabético. Los archivos de un comprimido se listan bajo él en orden alfabético. El conteo del título cuenta solo los documentos publicados; los archivos internos de un comprimido no suman.
- **RN-05 Evidencia:** la marca "Usado como evidencia" aparece cuando la plataforma conservó copia del documento por haber extraído de él información usada en un ítem o señal; muestra la fecha de descarga de la copia. "Ver copia conservada" solo aparece en esos documentos.
- **RN-06 Enlaces:** "Abrir en SECOP II" usa `url_descarga_documento` y abre en pestaña nueva; se muestra solo si la URL fue publicada. La plataforma no evade CAPTCHA, autenticación ni bloqueos: si la fuente los exige, el enlace simplemente lleva a la fuente.
- **RN-07 Nulos:** campo no publicado → "Sin dato"; sin descripción no se muestra la línea de descripción.
- **RN-08 Volumen:** si hay más de 50 documentos, se muestran los 50 primeros según RN-04 y el botón "Mostrar todos ({n})".
- **RN-09 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-10 Rendimiento y accesibilidad (valores iniciales de diseño):** la sección carga dentro del objetivo de la ficha de ≤ 3 segundos (p95) con 20 usuarios concurrentes; los documentos solo se abren bajo demanda. WCAG 2.1 AA (teclado, foco visible, enlaces externos anunciados como "se abre en una pestaña nueva", jerarquía de comprimidos anunciada); en móvil desde 360 px cada documento es una tarjeta con todos sus campos y acciones.

### Interfaz

- Sección "Documentos del proceso ({n})" con tabla (escritorio) o tarjetas (móvil).
- Por documento: columnas de RN-02, marca "Usado como evidencia", acciones "Abrir en SECOP II" y "Ver copia conservada".
- Filas anidadas para archivos contenidos en comprimidos.
- Botón "Mostrar todos ({n})" cuando aplique.
- Mensajes de los Escenarios 4, 7, 8, 9 y 10.

### Sistemas Externos (Si aplica)

- Datasets oficiales de Archivos Descarga de SECOP II (`dmgg-8hin` desde 2025 e históricos por año), ya ingeridos.
- Enlace de salida a la URL oficial de descarga del documento (`community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=…`); la ficha no descarga el documento, solo enlaza.
- Copias conservadas de documentos usados como evidencia, almacenadas por la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-076 (estructura de la ficha), HU-077 (evidencia de los ítems), HU-081 (estado de procesamiento)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (Escenario 9):** las órdenes TVEC no tienen documentos en el MVP; la sección lo informa.
- **Resuelto (RN-03):** catálogo de estados de documento (procesado, pendiente, no priorizado, en blanco, duplicado, error, no soportado).
- **Resuelto (RN-08):** se muestran 50 documentos y el resto bajo "Mostrar todos".

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
