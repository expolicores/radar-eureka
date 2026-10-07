# PRD — Seguimiento Compras Públicas

**Fecha:** 2026-10-02  
**Autor:** Juan Camilo  
**Estado:** PRD aprobado conceptualmente — D4 completado; sujeto a validación de precisión D4-4 y validación de usuarios D5  
**Naturaleza:** MVP propio basado en la tesis, orientado a validar una hipótesis real de producto (no es una propuesta comercial).  
**Fuentes del MVP:** SECOP II + TVEC (públicas, API oficial) · Alkosto + Falabella (retail, adquisición progresiva)

---

## Documentos Relacionados

- **📄 Brief de Alcance (aprobado, con Adendas 1, 2 y 3)**: [`../02-brief-alcance/brief-alcance.md`](../02-brief-alcance/brief-alcance.md)
  - Para contexto completo: problemas, usuarios, objetivos, métricas de éxito
  - Este PRD **complementa** el Brief con requerimientos estructurados y épicas priorizadas
- **🔬 Spike D1 — SECOP II / datos.gov.co**: [`insumos/D1-spike-secop-datos-abiertos.md`](insumos/D1-spike-secop-datos-abiertos.md)
- **🔬 Spike D4 — Extracción documental**: [`insumos/D4-spike-extraccion-documental.md`](insumos/D4-spike-extraccion-documental.md)
- **🔬 Spike D6 — Fuentes de precios de mercado**: [`insumos/D6-spike-fuentes-precios-mercado.md`](insumos/D6-spike-fuentes-precios-mercado.md)
- **📥 Insumos de la iniciativa**: contexto y tesis base (`../01-insumos-cliente/`)

---

## Resumen del PRD

Este PRD documenta **100 Requerimientos Funcionales** organizados en **13 dominios**, con NFRs cuantificados, estructurados en **9 Épicas Funcionales priorizadas**.

**Actores:** **Analista** (usuario de diseño: investiga contratación pública) y **Administrador** (opera fuentes, calidad, revisión humana y carga manual; en el MVP es el PO).

**Unidad de análisis:** el **ítem de televisor** (un contrato puede tener varios bienes).

> 📖 Ver **Brief de Alcance** (sección arriba) para contexto completo de negocio, problemas, actores y objetivos.

---

## 1. Requerimientos Funcionales (FRs)

### Dominio 1: Ingesta de Fuentes Públicas

- **FR-001:** El sistema DEBE ingerir contratos de SECOP II desde el dataset oficial de Contratos Electrónicos (`jbjy-vk9h`) mediante la API de datos abiertos.
- **FR-002:** El sistema DEBE ingerir el histórico de contratos de SECOP II de los últimos 3 años contados desde la fecha de firma (ventana inicial: 2023-01-01 en adelante).
- **FR-003:** El sistema DEBE ejecutar cargas incrementales periódicas de SECOP II y TVEC usando la fecha de última actualización del registro, sin reprocesar todo el histórico. La frecuencia es configurable (configuración inicial: diaria; ver NFR-DAT-001). La ingesta de datos y el procesamiento o extracción documental DEBEN ser procesos separados: una ingesta NO DEBE disparar el reprocesamiento con IA de documentos ya procesados.
- **FR-004:** El sistema DEBE ingerir los ítems de órdenes de compra de la Tienda Virtual del Estado Colombiano (TVEC) desde los datasets oficiales de ítems (`usqp-5nsn` / `3hdv-smhz`) y de órdenes (`rgxm-mmea`).
- **FR-005:** El sistema DEBE relacionar cada ítem TVEC con su orden de compra, su entidad compradora y su fecha.
- **FR-006:** El sistema NO DEBE ingerir ni almacenar los campos de datos personales sensibles del dataset de contratos: banco, tipo y número de cuenta, y documentos de identidad de representantes legales, supervisores y ordenadores del gasto (Adenda 1, A1.4).
- **FR-007:** El sistema DEBE registrar por cada ejecución de ingesta: fuente, fecha y hora, registros leídos, nuevos, actualizados, rechazados y errores.
- **FR-008:** El sistema DEBE conservar el identificador de origen de cada registro (ej. `id_contrato`, `proceso_de_compra`, orden TVEC) y la URL pública del proceso, para trazabilidad a la fuente oficial.
- **FR-009:** El sistema DEBE marcar cada registro con la fecha de corte de los datos de la fuente.
- **FR-010:** El sistema DEBE aplicar validaciones de calidad en la ingesta (campos obligatorios, formatos de fecha y valor, duplicados) y registrar los registros que no las cumplen.

### Dominio 2: Identificación y Clasificación de Televisores

- **FR-011:** El sistema DEBE marcar como candidato todo contrato de SECOP II cuyo código UNSPSC principal sea `52161505` y/o cuyo objeto o descripción contenga los términos definidos ("televisor", "smart tv", "tv").
- **FR-012:** El sistema DEBE marcar como candidato todo ítem TVEC cuya descripción contenga los términos definidos.
- **FR-013:** El sistema DEBE confirmar o descartar cada candidato **a nivel de ítem** con una clasificación estricta contra el límite de categoría aprobado: incluye televisores LED/QLED/OLED de consumo, Smart y convencionales, de cualquier tamaño; excluye pantallas LED modulares, videowalls, señalización digital, monitores (incluidos los de CCTV), proyectores, pantallas interactivas o inflables, soluciones audiovisuales integrales, accesorios (soportes, cables, controles), **servicios de mantenimiento o instalación**, **comodatos y otros contratos que no son compras**, **lotes que no corresponden al televisor** en procesos por lotes y kits sin precio unitario determinable. La presencia del UNSPSC `52161505` no basta para confirmar un candidato (D4: 7 de 14 descartes lo tenían).
- **FR-014:** El sistema DEBE excluir los ítems de televisor cuyo precio sea inseparable de instalación, obra o servicios sin costo discriminable, y registrar el motivo de exclusión.
- **FR-015:** El sistema DEBE registrar para cada candidato el resultado de la clasificación (incluido / excluido / requiere revisión), el criterio aplicado y el método (regla o IA).
- **FR-016:** El Administrador (que actúa como Revisor en el MVP) DEBE PODER revisar y corregir manualmente la clasificación de un candidato, quedando registro del cambio, el usuario y la fecha.
- **FR-017:** El sistema DEBE soportar contratos mixtos: un contrato puede contener varios ítems, de los cuales solo los televisores entran al análisis.

### Dominio 3: Gestión de Documentos del Proceso

- **FR-018:** El sistema DEBE obtener la lista de documentos de cada proceso candidato desde los datasets oficiales de Archivos Descarga de SECOP II (desde 2025 e históricos por año).
- **FR-019:** El sistema DEBE priorizar los documentos a procesar según su nombre, descripción y contenido (ej. oferta o propuesta económica, anexos económicos y técnicos, evaluación económica, aceptación de oferta, cotizaciones —incluidas las contenidas en ZIP—, precios techo, contrato, estudios previos), con una **estrategia inicial de ~8 documentos relevantes por proceso, ajustable según evidencia** (no es una cantidad fija). DEBE **detectar y excluir formularios o documentos en blanco** (formatos sin diligenciar, archivos vacíos), **deduplicar documentos por hash** y, en procesos por lotes, seleccionar los documentos del lote correspondiente al televisor.
- **FR-020:** El sistema DEBE descargar los documentos priorizados usando la URL oficial publicada en el dataset, sin evadir CAPTCHA, autenticación ni bloqueos.
- **FR-021:** El sistema DEBE descomprimir archivos .zip y .rar y tratar cada archivo contenido como documento del proceso.
- **FR-022:** El sistema DEBE soportar al menos los formatos PDF (con y sin capa de texto), XLSX/XLS, DOCX/DOC e imágenes (JPG/PNG).
- **FR-023:** El sistema DEBE detectar si una página requiere OCR o lectura multimodal: páginas sin capa de texto utilizable **y páginas que contienen imágenes incrustadas** (ej. tablas de ítems como imagen) aunque también tengan texto.
- **FR-024:** El sistema DEBE registrar cada documento procesado con un identificador estable (`id_documento`), nombre, tipo, fecha de carga y URL de origen. Cuando de un documento se extraiga información usada en una señal, el sistema DEBE conservar además una **copia del archivo**, su **hash**, la URL original, la fuente, la fecha de descarga y la ubicación de la evidencia (página, hoja o celda), para que la señal sea reproducible aunque el documento original cambie o deje de estar disponible. La estrategia de almacenamiento se define en arquitectura.

### Dominio 4: Extracción Inteligente (IA)

- **FR-025:** El sistema DEBE extraer de los documentos priorizados, por cada ítem de televisor: descripción, marca, modelo/referencia, tamaño, resolución, tecnología de pantalla, funciones Smart, cantidad, precio unitario, valor total del ítem e IVA, cuando estén disponibles, y registrar el **tipo de precio unitario**: `explicito` (publicado en el documento) o `derivado` (FR-099).
- **FR-026 (Candidata Post-MVP — pospuesta por D4):** El sistema DEBE extraer y comparar los precios unitarios de los distintos oferentes de un proceso e identificar el adjudicado. **Pospuesta fuera del core del MVP** (D4: solo ~10 % de los procesos publica precio unitario por oferente). Se reincorpora si aparece una fuente o tipo documental donde esta información sea sistemática. No bloquea el flujo SECOP/TVEC → extracción del bien adjudicado → normalización → benchmark → señal → evidencia.
- **FR-027:** El sistema DEBE registrar para cada dato extraído el documento de origen y la página (o la hoja y la celda) donde se encontró.
- **FR-028:** El sistema DEBE asignar un nivel de confianza a cada dato extraído y DEBE soportar un **umbral configurable de aceptación automática**. El valor del umbral se calibra con la muestra validada manualmente de D4-4, a partir de la relación observada entre la confianza del extractor y la corrección real; no se fija un valor arbitrario. El puntaje de confianza del modelo no se interpreta como probabilidad calibrada de corrección. Mientras no exista calibración, los datos críticos de confianza baja o incierta DEBEN poder dirigirse a revisión humana.
- **FR-029:** El sistema DEBE distinguir si un precio extraído es con IVA, sin IVA o de base indeterminada.
- **FR-030:** El sistema DEBE marcar un ítem como "información insuficiente" cuando no logre extraer cantidad y precio unitario, indicando el motivo.
- **FR-031:** El sistema DEBE detectar inconsistencias aritméticas (cantidad × precio unitario ≠ total del ítem; suma de ítems ≠ total esperado, cuando la información permita comprobarlo) y dirigirlas a la cola de revisión. Estas inconsistencias se tratan como **señales de revisión de calidad o evidencia, no como irregularidades**.
- **FR-032:** El Administrador (que actúa como Revisor en el MVP) DEBE PODER validar, corregir o rechazar los datos extraídos de un ítem, conservando el valor original, el valor corregido, el usuario y la fecha.
- **FR-033:** El sistema DEBE poder desactivar la extracción con IA sin afectar las funcionalidades determinísticas (ingesta, exploración, TVEC, comparación sobre datos ya extraídos).
- **FR-034:** El sistema DEBE registrar el costo estimado y el tiempo de procesamiento de la extracción por documento.
- **FR-099:** El sistema DEBE calcular un **precio unitario derivado** (`valor total del ítem / cantidad`) **solo** cuando pueda demostrarse que: (1) la cantidad está explícitamente documentada; (2) el valor usado corresponde exclusivamente a esos televisores; (3) todos los televisores incluidos son del mismo producto/modelo o de una referencia inequívocamente homogénea; (4) no hay otros bienes mezclados; (5) no hay instalación, transporte, soporte, obra, accesorios ni otros servicios incluidos sin discriminar; (6) la base tributaria no introduce una incompatibilidad conocida. NUNCA DEBE usar `valor total del contrato / cantidad` en un contrato mixto. El dato se guarda como `precio_unitario_tipo = derivado`, con el valor total usado, la cantidad usada, la fórmula, el documento fuente, la página/hoja/celda, el nivel de confianza (menor que el de un precio explícito) y el indicador de derivado.
- **FR-100:** El sistema NO DEBE usar el valor del contrato publicado en datos abiertos como sustituto del precio unitario ni del valor adjudicado documental del ítem (D4: no coincide necesariamente con la oferta aceptada); ese valor solo se muestra como dato de referencia del contrato.

### Dominio 5: Normalización y Emparejamiento de Productos

- **FR-035:** El sistema DEBE normalizar cada televisor (de SECOP II, TVEC o retail) a un esquema común: marca, modelo normalizado, tamaño en pulgadas, resolución, tecnología de pantalla, Smart (sí/no) y año o generación aproximada.
- **FR-036:** El sistema DEBE normalizar códigos de modelo corrigiendo solo diferencias sintácticas (espacios, guiones, mayúsculas/minúsculas y formatos equivalentes). NO DEBE eliminar componentes del código que puedan representar variantes técnicas (ej. sufijos regionales como `PSA`/`PSB`); referencias distintas no se tratan automáticamente como el mismo producto.
- **FR-037:** El sistema DEBE emparejar productos como **mismo modelo** cuando coincidan la marca y el modelo normalizado sintácticamente (FR-036), o el EAN/GTIN cuando exista en ambos lados.
- **FR-038:** El sistema DEBE emparejar productos como **equivalentes** cuando no exista mismo modelo y coincidan las características de equivalencia definidas (tamaño, resolución, tecnología, Smart, generación, marca cuando aplique). Dos referencias de modelo diferentes (ej. que solo difieren en el sufijo) solo pueden considerarse equivalentes si las características técnicas lo sustentan.
- **FR-039:** El sistema DEBE clasificar cada emparejamiento como *mismo modelo*, *producto equivalente* o *insuficiente/no confiable*, y mostrar los criterios usados.
- **FR-040:** El sistema NO DEBE relajar los criterios de equivalencia para forzar la existencia de una referencia (Adenda 2, A2.7).

### Dominio 6: Base de Observaciones de Precio de Mercado

- **FR-041:** El sistema DEBE almacenar observaciones de precio retail en una base propia, independiente del proceso de comparación.
- **FR-042:** El sistema DEBE registrar en cada observación como mínimo: producto, marca/modelo, SKU/EAN cuando exista, vendedor, precio efectivo, fuente, URL o referencia, fecha de observación, información disponible sobre IVA, evidencia y método de adquisición (API / dataset / feed / sitemap-datos estructurados / extracción web / manual).
- **FR-043:** El sistema DEBE soportar observaciones de precio provenientes de **Alkosto** (fuente principal) y **Falabella** (fuente secundaria). Cuando exista un mecanismo automatizado permitido y viable, PODRÁ obtenerlas por sitemap, datos estructurados u otros mecanismos aprobados; si una fuente no puede automatizarse, las observaciones ingresan por carga manual o semiautomática (FR-048, FR-052). La automatización completa de estas fuentes **no es condición de éxito del MVP** y su indisponibilidad **no bloquea el Benchmark 2**. Nunca se evaden CAPTCHA, bloqueos, autenticación ni restricciones de acceso (adquisición progresiva, Adenda 2).
- **FR-044:** El sistema DEBE aceptar solo observaciones en las que el vendedor sea directamente la tienda seleccionada, y descartar vendedores terceros de marketplace.
- **FR-045:** El sistema DEBE usar como precio de referencia el precio efectivo de venta, guardando el precio tachado o anterior solo como evidencia.
- **FR-046:** El sistema DEBE identificar y marcar los precios sujetos a condiciones especiales (tarjeta específica, cupón, financiación, membresía) y no tratarlos como precio general de mercado.
- **FR-047:** Cuando se use captura automática, el sistema DEBE suspenderla en una fuente al detectar CAPTCHA, bloqueo, requerimiento de autenticación o un cambio en `robots.txt` que la prohíba, y notificar al Administrador.
- **FR-048:** El Administrador DEBE PODER registrar manualmente una observación de precio con la trazabilidad mínima de FR-042 y una evidencia adjunta (captura de pantalla o archivo).
- **FR-049:** El sistema DEBE identificar explícitamente toda observación manual como tal, en la base y en cualquier evidencia mostrada al Analista.
- **FR-050:** El sistema DEBE registrar el usuario que creó cada observación manual.
- **FR-051:** El Administrador DEBE PODER registrar en una carga manual todas las ofertas comparables encontradas y los términos de búsqueda usados (protocolo contra el sesgo de selección).
- **FR-052:** El Administrador DEBE PODER cargar observaciones de forma semiautomática mediante un archivo estructurado (ej. CSV) que cumpla el registro mínimo.
- **FR-053:** El sistema DEBE conservar todas las observaciones históricas, sin sobrescribirlas, para construir el histórico propio de precios de mercado.

### Dominio 7: Comparación y Benchmarks

- **FR-054:** El sistema DEBE calcular para cada ítem de televisor con precio unitario el **Benchmark 1 – Contratación pública**: comparación contra la distribución de precios unitarios de otras compras públicas comparables (SECOP II y TVEC).
- **FR-055:** El sistema DEBE seleccionar las observaciones comparables del Benchmark 1 según el tipo de emparejamiento y una **ventana temporal configurable** (configuración inicial: ±6 meses desde la fecha de la compra, ampliable hasta ±12 meses cuando no existan comparables suficientes).
- **FR-056:** El sistema DEBE calcular el Benchmark 2 – Mercado solo con observaciones retail dentro de una **ventana temporal configurable** respecto a la fecha de la compra (configuración inicial: ±30 días); NO DEBE usar un precio actual para juzgar una compra antigua.
- **FR-057:** El sistema DEBE comparar valores solo en la misma base tributaria (precio final con IVA) y marcar la comparación como incompleta/no confiable cuando la base de algún valor no se pueda determinar.
- **FR-058:** El sistema DEBE calcular una referencia estadística agregada (ej. mediana) solo cuando se alcance un **mínimo configurable de observaciones** (configuración inicial: Benchmark 1 ≥ 5 observaciones comparables; Benchmark 2 ≥ 3 observaciones de al menos 2 fuentes), conservando el vínculo con cada observación.
- **FR-059:** Por debajo del mínimo de FR-058, el sistema DEBE mostrar las observaciones como "referencia disponible" o evidencia limitada (en el Benchmark 2: "referencia de mercado disponible", no "precio de mercado"), con el número de fuentes u observaciones y el nivel de confianza, sin presentarlas como referencia estadística robusta.
- **FR-060:** El sistema DEBE marcar el Benchmark 2 como "no disponible / evidencia insuficiente" cuando no exista referencia retail confiable, manteniendo disponible el Benchmark 1.
- **FR-061:** El sistema DEBE calcular la desviación porcentual del precio unitario contratado frente a cada referencia disponible.
- **FR-062:** El sistema DEBE identificar en cada observación si proviene de contratación pública (indicando SECOP II o TVEC) o de retail.

### Dominio 8: Señales y Trazabilidad

- **FR-063:** El sistema DEBE generar una "señal que merece revisión" solo por **desviaciones por encima** de la referencia, con estrategia híbrida configurable: (a) con muestra suficiente y homogénea de comparables, regla de valores atípicos (configuración inicial: Q3 + 1,5 × IQR); (b) en otro caso, umbrales porcentuales provisionales (configuración inicial: mismo modelo ≥ +30 %; producto equivalente ≥ +50 %). Estos umbrales sirven **exclusivamente para priorizar** casos que merecen revisión y se recalibran con evidencia real. Los precios **anormalmente bajos** NO generan señal en el MVP: se dirigen a la cola de revisión de calidad (posible error de extracción, cantidad, normalización, producto diferente o base tributaria distinta).
- **FR-064:** El sistema NO DEBE denominar una señal como sobreprecio, corrupción, fraude ni hallazgo fiscal, ni etiquetar a personas o empresas con esos términos.
- **FR-065:** El sistema DEBE asociar a cada señal: ítem, contrato, entidad, proveedor, benchmark usado, referencias y observaciones, fórmula, desviación, tipo de emparejamiento, base tributaria, métodos de adquisición, fecha de corte y nivel de confianza.
- **FR-066:** El Analista DEBE PODER navegar desde una señal hasta el contrato, el documento y la página de origen del precio, y hasta cada observación usada como referencia.
- **FR-067:** El sistema DEBE mostrar en cada señal la advertencia de que no constituye una conclusión ni una acusación.
- **FR-068:** El sistema DEBE calcular el nivel de confianza de la señal a partir del tipo de emparejamiento, la cantidad de observaciones, la base tributaria, la confianza de la extracción, el **tipo de precio unitario (un precio `derivado` reduce la confianza frente a uno `explicito`)** y el método de adquisición.
- **FR-069:** El Analista DEBE PODER calificar una señal como "suficientemente sustentada para merecer revisión" o no, con comentario opcional (insumo del KPI de validación humana).
- **FR-070:** El sistema DEBE permitir reportar un error en un dato o una señal (mecanismo de corrección) y registrar su gestión.

### Dominio 9: Exploración y Ficha de Contrato

- **FR-071:** El Analista DEBE PODER buscar y filtrar contratos e ítems de televisor por entidad, proveedor, modalidad, fechas, UNSPSC, departamento/municipio, rango de valor, fuente (SECOP II / TVEC) y existencia de señal.
- **FR-072:** El Analista DEBE PODER ordenar los resultados por desviación, valor, fecha o nivel de confianza.
- **FR-073:** El Analista DEBE PODER ver una lista priorizada de señales que merecen revisión.
- **FR-074:** El Analista DEBE PODER abrir la ficha de un contrato con: datos clave, entidad, proveedor, valor, modalidad, fechas, ítems de televisor extraídos, benchmarks, señales, documentos y enlace a la fuente oficial.
- **FR-075:** El Analista DEBE PODER ver en la ficha el estado de procesamiento del contrato (identificado, documentos obtenidos, extraído, revisado, comparado) y los motivos de información insuficiente.
- **FR-076:** El sistema DEBE mostrar la fecha de actualización de los datos en las vistas de exploración y ficha.

### Dominio 10: Espacio de Investigación

- **FR-077:** El Analista DEBE PODER crear un caso de investigación a partir de una señal o de un contrato.
- **FR-078:** El Analista DEBE PODER guardar en un caso varias señales, contratos y evidencias.
- **FR-079:** El Analista DEBE PODER agregar, editar y eliminar notas asociadas a un caso.
- **FR-080:** El Analista DEBE PODER listar, abrir y retomar sus casos guardados.
- **FR-081:** El sistema DEBE conservar en el caso una instantánea de las señales y evidencias guardadas, de modo que se mantengan aunque se recalculen los benchmarks.
- **FR-082:** El sistema DEBE restringir el acceso a un caso únicamente al Analista que lo creó.

### Dominio 11: Autenticación y Cuentas

- **FR-083:** El Analista DEBE PODER registrarse con correo electrónico y contraseña **mediante invitación** emitida por el Administrador. El registro público no se habilita durante discovery/piloto.
- **FR-084:** El Analista DEBE PODER iniciar y cerrar sesión.
- **FR-085:** El Analista DEBE PODER recuperar su contraseña por correo electrónico.
- **FR-086:** El sistema DEBE soportar al menos los roles Analista y Administrador, con permisos diferenciados.
- **FR-087:** El sistema DEBE solicitar aceptación de términos de uso y de política de tratamiento de datos en el registro.

### Dominio 12: Administración, Operación y Medición

> **Nota de implementación (MVP):** durante el MVP el PO es también Administrador y Revisor. Las capacidades administrativas de este dominio y las de FR-016, FR-032, FR-047, FR-048, FR-051 y FR-052 **no requieren necesariamente una interfaz gráfica**: pueden implementarse con configuración, logs, scripts, consultas, herramientas técnicas o interfaces administrativas mínimas, siempre que el requisito se cumpla y quede trazabilidad. La arquitectura y las HUs definen cuáles requieren UI. La interfaz de usuario se prioriza para el flujo que valida la hipótesis: *explorar → detectar señal → revisar comparación → revisar evidencia → guardar caso → continuar investigación*.

- **FR-088:** El Administrador DEBE PODER conocer el estado de las fuentes (última ingesta, errores, fuentes suspendidas) y relanzar una ingesta o captura.
- **FR-089:** El Administrador DEBE PODER configurar los parámetros analíticos y operativos: términos de búsqueda, ventanas temporales de comparación, mínimos de observaciones, regla de atípicos y umbrales porcentuales de señal, umbral de aceptación automática de extracción y frecuencias de ingesta y captura.
- **FR-090:** El Administrador DEBE PODER ver la cola de ítems pendientes de revisión humana (clasificación dudosa, extracción de baja confianza, inconsistencias).
- **FR-091:** El sistema DEBE calcular y poner a disposición del Administrador los KPIs del MVP: precisión de extracción (global y **por campo**: marca, modelo/referencia, tamaño, cantidad, precio unitario), **disponibilidad en la fuente**, **cobertura de extracción** y **cobertura efectiva end-to-end** (sobre los contratos SECOP II del alcance; TVEC se reporta aparte; ver NFR-CAL-003), trazabilidad, clasificación de comparabilidad y porcentaje de señales calificadas como sustentadas.
- **FR-092:** El Administrador DEBE PODER marcar contratos o documentos como parte de la muestra de validación manual de extracción.
- **FR-093:** El sistema DEBE registrar el tiempo que el Analista dedica a cada caso (desde que abre la señal hasta que la califica), como insumo del KPI de eficiencia.
- **FR-094:** El sistema DEBE registrar en un log de auditoría las acciones de corrección, clasificación manual, carga manual y cambios de configuración.

### Dominio 13: Candidatas a Validar (no core salvo que el PRD las requiera)

- **FR-095 (Candidata):** El Analista DEBE PODER ver una ficha de entidad con su contratación de televisores e indicadores agregados.
- **FR-096 (Candidata):** El Analista DEBE PODER ver una ficha de proveedor con sus contratos de televisores e indicadores agregados.
- **FR-097 (Candidata):** El sistema DEBE calcular señales que no son de precio: concentración de contratos en un proveedor, peso de la contratación directa y diferencia entre presupuesto y valor contratado.
- **FR-098 (Candidata):** El Analista DEBE PODER exportar un expediente de caso (resumen, datos, señales y enlaces a evidencia).

**TOTAL: 100 FRs en 13 dominios** (95 del MVP y 5 candidatas Post-MVP: FR-026, pospuesta por D4, y FR-095 a FR-098 del Dominio 13).

---

## 2. Requerimientos No Funcionales (NFRs)

> **Nota**: Solo se documentan las categorías de NFRs que están explícitamente mencionadas en el Brief de Alcance o en los insumos de la iniciativa (contexto, tesis, spikes D1, D4 y D6). No se incluyen categorías con "N/A" o placeholders genéricos.

> **Nivel de certeza de los valores.** **[Meta del Brief]** = criterio de éxito aprobado por el PO. **[Decisión PRD]** = resuelto por el PO en la revisión del PRD. *[Valor inicial de diseño — configurable / sujeto a validación]* y *[Objetivo inicial de ingeniería del piloto]* = número propuesto para arrancar, que se recalibra con evidencia y no es una verdad de negocio ni un requisito contractual. La **capacidad** descrita sí es requisito.

### Calidad Analítica y Explicabilidad (específica del proyecto)

*Evidencia: KPIs aprobados en el Brief.*

- **NFR-CAL-001:** La extracción DEBE alcanzar **≥ 90 % de precisión** en campos críticos (marca, modelo/referencia, tamaño, cantidad, precio unitario, cuando estén disponibles) sobre una muestra **diversa de ≥ 50 contratos/documentos** validados manualmente. **[Meta del Brief]** La validación manual (D4-4) prioriza: precio unitario, cantidad, tamaño, modelo/referencia, marca y demás atributos.
- **NFR-CAL-002:** Metodología de precisión **[Decisión PRD — P-06]**: `precisión = campos extraídos correctamente / campos realmente presentes según la validación manual`. Campo ausente en el documento y no extraído → no cuenta; presente y bien extraído → correcto; presente y mal extraído → error; ausente pero inventado o "extraído" → error. Se reporta **precisión global** y **precisión por campo** (marca, modelo/referencia, tamaño, cantidad, precio unitario); una buena precisión global **no puede esconder** bajo desempeño en un campo crítico.
- **NFR-CAL-003:** Cobertura **[Decisión D4-1 — reemplaza la definición anterior del Brief]**, medida sobre los contratos/ítems candidatos de **SECOP II** del alcance (TVEC se reporta aparte), con tres indicadores:
  - **(a) Disponibilidad en la fuente** = % de contratos/ítems candidatos cuyos documentos publicados contienen la información mínima para intentar el análisis (cantidad + precio unitario explícito o derivable según FR-099). **Se reporta, sin meta de producto inicial**: mide el límite que impone la fuente (D4: ~44–50 % de los contratos en categoría).
  - **(b) Cobertura de extracción** = contratos elegibles extraídos correctamente y llevados automáticamente hasta información suficiente para comparar / contratos elegibles con información realmente disponible en la fuente. **Meta inicial ≥ 80 %**, provisional y sujeta a calibración con D4-4. Si la evidencia demuestra que 80 % no es técnicamente razonable, se propone una recalibración explícita; no se reduce automáticamente.
  - **(c) Cobertura efectiva end-to-end** = % del universo total de contratos/ítems candidatos que llega automáticamente a una comparación utilizable. **Se reporta siempre**, aunque la pérdida se deba a la fuente.
  Así se distingue *la fuente no publica el dato* de *el producto no extrae un dato que sí estaba publicado*.
- **NFR-CAL-004:** **100 %** de las señales DEBEN permitir regresar al contrato, al documento o dato de origen y a cada referencia usada. **[Meta del Brief]**
- **NFR-CAL-005:** **100 %** de las comparaciones DEBEN estar clasificadas como *mismo modelo*, *producto equivalente* o *insuficiente/no confiable*. **[Meta del Brief]**
- **NFR-CAL-006:** **0 %** de las comparaciones pueden mezclar valores con y sin IVA sin marcarlas como incompletas/no confiables. **[Meta del Brief]**
- **NFR-CAL-007:** **≥ 70 %** de las señales presentadas para validación DEBEN ser calificadas por al menos 3 usuarios del perfil de diseño como "suficientemente sustentadas para merecer revisión". **[Meta del Brief]**
- **NFR-CAL-008:** El tiempo humano promedio por caso (contrato → comparación revisable) DEBE reducirse **≥ 70 %** frente a la línea base manual medida en discovery (meta provisional; se recalibra con la línea base). **[Meta del Brief]**

### Seguridad y Privacidad

*Evidencia: registro/login, roles, Ley 1581/2012, datos personales en datasets (Adenda 1).*

- **NFR-SEG-001:** El **100 %** del tráfico DEBE usar HTTPS (TLS 1.2 o superior).
- **NFR-SEG-002:** Las contraseñas DEBEN almacenarse con hash adaptativo (bcrypt, scrypt o Argon2), nunca en texto plano. Longitud mínima de 10 caracteres *[Valor inicial de diseño — configurable / sujeto a validación]*.
- **NFR-SEG-003:** La sesión DEBE expirar tras un tiempo de inactividad configurable (valor inicial: **30 minutos**) *[Valor inicial de diseño — configurable / sujeto a validación]*.
- **NFR-SEG-004:** Los casos y notas de un Analista DEBEN ser accesibles solo por su autor. Se verifica con pruebas de autorización en el **100 %** de los endpoints de casos.
- **NFR-SEG-005:** **0** campos de datos personales sensibles excluidos (banco, cuenta, documentos de identidad de representantes, supervisores y ordenadores del gasto) almacenados en ninguna capa (validación automática en la ingesta).
- **NFR-SEG-006:** Las credenciales y llaves de servicios (IA, app token de datos.gov.co) DEBEN guardarse en un gestor de secretos o variables de entorno cifradas, nunca en el repositorio.
- **NFR-SEG-007:** El log de auditoría (FR-094) DEBE conservarse durante un período configurable (valor inicial: **12 meses**) *[Valor inicial de diseño — configurable / sujeto a validación]*.
- **NFR-SEG-008:** La aplicación DEBE pasar una revisión contra **OWASP Top 10 (2021)** sin hallazgos de severidad alta o crítica abiertos antes de abrir el registro a usuarios piloto.

### Cumplimiento (Normativo y de Fuentes)

*Evidencia: Ley 1581/2012, principio "mostrar hechos, no acusar", reglas de adquisición de la Adenda 2.*

- **NFR-CUM-001:** El sistema DEBE publicar una política de tratamiento de datos personales conforme a la Ley 1581 de 2012 antes de abrir el registro a usuarios piloto.
- **NFR-CUM-002:** La captura retail DEBE respetar el `robots.txt` vigente de cada fuente, verificado en **cada ejecución** de captura.
- **NFR-CUM-003:** La captura retail automática DEBE operar con **límites de ritmo y volumen configurables por fuente** (valores iniciales: 1 solicitud cada 2 segundos y 2.000 solicitudes por semana) *[Valor inicial de diseño — configurable / sujeto a validación]*. Los límites se ajustan según términos de uso, `robots.txt`, comportamiento de la fuente y validación técnica; ante restricciones o bloqueos la fuente se suspende (FR-047).
- **NFR-CUM-004:** Las solicitudes a fuentes comerciales DEBEN identificarse con un User-Agent propio del producto, con contacto.
- **NFR-CUM-005:** **0** mecanismos de evasión de CAPTCHA, bloqueo o autenticación en el código (revisión de código obligatoria).
- **NFR-CUM-006:** Los términos de uso de cada fuente comercial DEBEN revisarse y documentarse **antes del paso a producción**.
- **NFR-CUM-007:** **0** textos de la interfaz generados por el sistema con los términos "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal" aplicados a un contrato, persona o empresa (verificable con lista de términos prohibidos en pruebas).

### Frescura de Datos e Ingesta

*Evidencia: datasets de datos.gov.co actualizados a diario (D1); captura retail con baja frecuencia (D6).*

- **NFR-DAT-001:** La ingesta incremental de SECOP II y TVEC DEBE tener frecuencia configurable (configuración inicial **[Decisión PRD — P-13]**: **diaria**). La ingesta NO se acopla al reprocesamiento con IA de documentos (FR-003).
- **NFR-DAT-002:** Un contrato nuevo publicado en datos abiertos DEBE estar disponible en el sistema en **≤ 48 horas**, y sus ítems extraídos en **≤ 72 horas** cuando no requiera revisión humana *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-DAT-003:** La captura retail automática, cuando exista, DEBE tener frecuencia configurable (configuración inicial **[Decisión PRD — P-14]**: **semanal** por fuente).
- **NFR-DAT-004:** La carga inicial del histórico de 3 años (≈ 355 contratos SECOP II y ≈ 1.150 líneas TVEC) DEBE completarse en **≤ 7 días** de procesamiento, incluida la extracción *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*; se valida en D4.
- **NFR-DAT-005:** El sistema DEBE tolerar caídas o tiempos de espera de la API de datos.gov.co con reintentos con espera exponencial (valor inicial: **3** reintentos) *[Valor inicial de diseño — configurable / sujeto a validación]*, sin perder ni duplicar registros.

### Performance

*Evidencia indirecta: volumen del MVP (D1) y usuarios piloto (3–5). **[Decisión PRD — P-09]** Objetivos iniciales de diseño para el piloto, no requerimientos contractuales; se recalibran.*

- **NFR-PER-001:** Búsquedas y filtros de exploración DEBEN responder en **≤ 3 segundos (p95)** con el volumen del MVP *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-PER-002:** La ficha de contrato y el detalle de una señal DEBEN cargar en **≤ 3 segundos (p95)** *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-PER-003:** El sistema DEBE soportar una capacidad inicial de **20 usuarios concurrentes** sin degradar los tiempos anteriores *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-PER-004:** La extracción de un documento DEBE ejecutarse de forma asíncrona, sin bloquear al usuario, con un objetivo inicial de **≤ 5 minutos (p95)** por documento *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*; se mide en D4.

### Disponibilidad y Respaldo

*Evidencia indirecta: MVP desplegado para usuarios piloto; sin SLA en el Brief. **[Decisión PRD — P-10]** Objetivos iniciales de ingeniería del MVP, sin SLA contractual.*

- **NFR-DIS-001:** Disponibilidad objetivo de **99 % mensual** para la aplicación web *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-DIS-002:** Respaldo de la base de datos **diario**, con retención inicial de **30 días**; RPO ≤ 24 h y RTO ≤ 24 h *[Objetivo inicial de ingeniería del piloto — sin SLA contractual; recalibrable]*.
- **NFR-DIS-003:** La base de observaciones de mercado, las validaciones humanas y las **copias de documentos usados como evidencia** (FR-024) DEBEN incluirse en el respaldo, porque no se pueden reconstruir desde las fuentes.

### Usabilidad

*Evidencia: desktop-first + responsive (Brief).*

- **NFR-USA-001:** Diseño optimizado para escritorio desde **1366 × 768 px**; funcional (sin pérdida de capacidades) en tablet desde **768 px** y móvil desde **360 px** *[Valor inicial de diseño — configurable / sujeto a validación]*.
- **NFR-USA-002:** Compatibilidad con las **2 últimas versiones** de Chrome, Edge, Firefox y Safari.
- **NFR-USA-003:** Un Analista nuevo DEBE poder ir de la lista de señales a la evidencia de origen de una señal en **≤ 3 clics**.
- **NFR-USA-004:** Contraste de color y navegación por teclado según **WCAG 2.1 nivel AA** en las vistas principales (exploración, ficha, señal, caso) *[Valor inicial de diseño — configurable / sujeto a validación]*.

### Observabilidad y Costos

*Evidencia: "identificar los principales drivers de costo" (Brief); FR-007, FR-034.*

- **NFR-OBS-001:** El sistema DEBE registrar el costo estimado por documento procesado con IA y el costo mensual acumulado por componente (IA, almacenamiento, cómputo, búsqueda), consultables por el Administrador (UI, consulta o reporte).
- **NFR-OBS-002:** Una ingesta o captura fallida DEBE generar alerta al Administrador en **≤ 1 hora** *[Valor inicial de diseño — configurable / sujeto a validación]*.
- **NFR-OBS-003:** Los logs de aplicación DEBEN conservarse durante un período configurable (valor inicial: **30 días**) *[Valor inicial de diseño — configurable / sujeto a validación]*.

### Evolutividad

*Evidencia: arquitectura evolutiva; adquisición de precios desacoplada (Adenda 2, A2.3 y A2.8).*

- **NFR-EVO-001:** Agregar una nueva fuente retail DEBE requerir **solo** un nuevo conector de adquisición, sin modificar los módulos de normalización, comparación ni señales.
- **NFR-EVO-002:** Agregar una nueva categoría de bien DEBE requerir configuración de reglas de identificación y de equivalencia, sin rediseñar el modelo de datos de ítems, observaciones y señales.
- **NFR-EVO-003:** La desactivación de la extracción con IA DEBE ser una opción de configuración, sin redespliegue.

---

## 3. User Journeys Principales

### Journey 1: Del universo de contratos a una señal con evidencia (Analista)

1. El Analista inicia sesión y abre la **lista priorizada de señales** de televisores.
2. Filtra por departamento y por los últimos 12 meses, y ordena por desviación.
3. Abre una señal: un contrato de mínima cuantía con 8 televisores de 65" a un precio unitario por encima de la distribución de compras públicas comparables.
4. Revisa el **Benchmark 1**: distribución de precios SECOP II + TVEC para televisores equivalentes en una ventana cercana, mediana, número de observaciones y tipo de emparejamiento.
5. Revisa el **Benchmark 2**: "referencia de mercado disponible" (2 observaciones Alkosto, 1 manual), o "no disponible" si es un contrato antiguo.
6. Navega a la **evidencia de origen**: documento y página donde se extrajo el precio unitario, y cada observación de referencia con su fuente, fecha y método de adquisición.
7. Califica la señal como "suficientemente sustentada para merecer revisión".
8. Crea un **caso**, guarda la señal y escribe una nota.

**Duración esperada**: 10–15 minutos por señal (meta: ≥ 70 % menos que la línea base manual, que se mide en D2).  
**FRs involucrados**: FR-054 a FR-069, FR-071 a FR-074, FR-077 a FR-079, FR-084  
**NFRs críticos**: NFR-CAL-004, NFR-CAL-006, NFR-CUM-007, NFR-PER-002, NFR-USA-003

### Journey 2: Retomar una investigación (Analista)

1. El Analista inicia sesión y abre **Mis casos**.
2. Abre un caso creado días atrás; la evidencia guardada se conserva como instantánea.
3. Agrega un contrato relacionado encontrado en la exploración y actualiza sus notas.
4. Reporta un error en un dato extraído (ej. cantidad mal leída) mediante el mecanismo de corrección.

**Duración esperada**: 5–10 minutos  
**FRs involucrados**: FR-070, FR-071, FR-074, FR-077 a FR-082, FR-084  
**NFRs críticos**: NFR-SEG-004, NFR-PER-001

### Journey 3: Operar la calidad de datos y referencias (Administrador)

> En el MVP estas tareas pueden hacerse con interfaz mínima, scripts, consultas o logs (ver nota del Dominio 12).

1. El Administrador revisa el **estado de las fuentes**: última ingesta de SECOP II y TVEC, y el estado de la captura de Alkosto y Falabella cuando esté automatizada (ej. una suspendida por un cambio de `robots.txt`).
2. Atiende la **cola de revisión humana**: confirma la clasificación de un candidato dudoso y corrige un precio unitario extraído con baja confianza.
3. Registra **manualmente** 3 observaciones de mercado para un modelo sin captura automática, con evidencia, todas las ofertas encontradas y los términos de búsqueda.
4. Marca 10 documentos nuevos para la **muestra de validación** y consulta los **KPIs** (precisión, cobertura, señales sustentadas, costo por documento).

**Duración esperada**: 30–60 minutos por sesión semanal  
**FRs involucrados**: FR-016, FR-032, FR-047 a FR-052, FR-088 a FR-094  
**NFRs críticos**: NFR-CUM-002, NFR-OBS-001, NFR-OBS-002, NFR-CAL-001, NFR-CAL-003

---

## 4. Épicas Funcionales

Este proyecto se estructura en **9 épicas funcionales** priorizadas. 

📋 **Ver detalles completos en**: [`epicas.md`](./epicas.md)

### Tabla Resumen de Épicas

| # | Nombre | Prioridad | FRs Cubiertos |
|---|--------|-----------|---------------|
| ÉPICA-001 | Universo de Compras Públicas de Televisores | Crítica | FR-001 a FR-017 |
| ÉPICA-002 | De Documentos a Datos Comparables | Crítica | FR-018 a FR-025, FR-027 a FR-034, FR-099, FR-100 |
| ÉPICA-003 | Normalización y Emparejamiento de Televisores | Crítica | FR-035 a FR-040 |
| ÉPICA-004 | Referencias de Mercado Trazables | Crítica | FR-041 a FR-053 |
| ÉPICA-005 | Señales que Merecen Revisión, con Evidencia | Crítica | FR-054 a FR-070 |
| ÉPICA-006 | Exploración y Ficha del Contrato | Crítica | FR-071 a FR-076 |
| ÉPICA-007 | Espacio de Investigación del Analista | Crítica | FR-077 a FR-087 |
| ÉPICA-008 | Operación, Calidad y Medición del MVP | Alta | FR-088 a FR-094 |
| ÉPICA-009 | Contexto Ampliado y Capacidades Pospuestas | Media (Post-MVP) | FR-026, FR-095 a FR-098 |

---

## 5. Exclusiones y Fuera de Alcance

### Fuera de Alcance - Fase 1

- **ÉPICA-009 completa (Post-MVP):** fichas de entidad y de proveedor, señales que no son de precio, exportación del expediente (se reevalúa con D5) y **extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4)**.
- **Agente de investigación** (siguiente incremento agéntico): preguntas en lenguaje natural, tool calling y MCP.
- **Base de conocimiento RAG** con informes de Contraloría, Transparencia por Colombia, Monitor Ciudadano y prensa.
- **Detección proactiva** con alertas automáticas de nuevas señales.
- **Otras categorías** de bienes (computadores, kits alimentarios, refrigerios y demás).
- **SECOP I** y **ciclo de vida del contrato** (adiciones, modificaciones, ejecución, liquidación).
- **Mercado Libre y Éxito** como fuentes automáticas, y **vendedores terceros** de marketplace.
- **Fuentes externas de precios históricos** de mercado.
- **Exploración pública anónima**, publicación abierta de investigaciones, rankings de riesgo y conclusiones sobre personas naturales.
- **Colaboración entre analistas** (casos compartidos), login social y SSO.
- **Canal de denuncia** directa a entes de control.
- **Plan de capacitación** de la tesis; solo onboarding mínimo en producto.
- **Modelo de monetización**, facturación y planes.

### Exclusiones Técnicas Explícitas

- NO aplicación móvil nativa (iOS/Android); solo web responsive.
- NO soporte para Internet Explorer ni navegadores con más de 2 versiones de antigüedad.
- NO scraping del portal transaccional de SECOP ni de rutas prohibidas por `robots.txt` (ej. `/api/` de Éxito, búsqueda de Alkosto).
- NO evasión ni resolución automatizada de CAPTCHA, bloqueos o autenticación.
- NO uso de la API de búsqueda de Mercado Libre (bloqueada) ni de la API VTEX de Éxito.
- NO acoplamiento funcional con Express App (producto independiente).
- NO stack obligatorio de la tesis (Python/Dash/Selenium/AWS EC2): la arquitectura se define en la fase de arquitectura.
- NO selección de Azure/Foundry sin justificación técnica por componente.
- NO almacenamiento de campos personales sensibles del dataset de contratos.

### Supuestos Críticos

1. **APIs de datos.gov.co disponibles y estables** (SECOP II, archivos, TVEC), con la estructura observada en D1 el 2026-10-01. Si cambian los esquemas o se restringe el acceso, se afecta la ÉPICA-001 y la ÉPICA-002.
2. **URLs oficiales de descarga de documentos accesibles sin CAPTCHA** (validado en muestra de 39 documentos). Si SECOP restringe la descarga, la extracción se reduce a la TVEC y a documentos ya descargados.
3. **La extracción con IA alcanza las metas de precisión (≥ 90 %) y de cobertura de extracción (≥ 80 % sobre lo disponible en la fuente).** D4 confirmó la viabilidad técnica (evidencia 100 %, imágenes legibles, multimodal necesario en ~52 % de los contratos); la precisión y el umbral se confirman con la validación manual **D4-4**. La disponibilidad en la fuente (~44–50 %) es un límite externo que se reporta.
4. **Volumen suficiente:** ~355 contratos SECOP II y ~1.150 líneas TVEC de televisores (2023–2026). D4 indica que ~28 % de los candidatos SECOP II no son compras de TV y que ~44–50 % de los que sí lo son publican precio unitario: el aporte efectivo de SECOP II al Benchmark 1 es del orden de ~110–130 contratos, por lo que **la TVEC es la base principal del Benchmark 1**.
5. **Observaciones de Alkosto y Falabella disponibles** por captura automática permitida o por carga manual o semiautomática. La automatización completa no es condición de éxito del MVP; sin ella, el Benchmark 2 sigue con carga manual (Adenda 2).
6. **El PO actúa como Administrador y Revisor** durante el MVP **[Decisión PRD — P-08]** y dedica tiempo a la revisión humana y la carga manual. Los analistas piloto no hacen limpieza sistemática de datos: evalúan el producto y las señales, y reportan errores (FR-070).
7. **Se consiguen 3–5 analistas** del perfil de diseño para D5 y para la validación humana de señales antes de cerrar el alcance para desarrollo.
8. **D3 (análisis competitivo)** no revela una solución existente que haga innecesario el MVP; si la revela, se replantea el diferenciador.

---

## 6. Riesgos y Factores de Complejidad

### Factores de Complejidad Alta

> Los porcentajes de esfuerzo son **estimaciones preliminares del consultor**, sujetas a D4 y a la estimación técnica posterior.

- **Extracción documental heterogénea** (PDF nativos, 34,9 % de páginas escaneadas en D4, imágenes incrustadas, XLSX, DOCX, ZIP, formatos en blanco, duplicados): sigue siendo el componente de mayor esfuerzo; puede representar **25–35 % del esfuerzo total** del MVP. Vinculado a NFR-CAL-001, NFR-CAL-003 y NFR-PER-004.
- **Normalización y emparejamiento de productos** con datos incompletos (solo 36 % de líneas TVEC con modelo; modelos con sufijos regionales): **10–15 % del esfuerzo**. Vinculado a NFR-CAL-005.
- **Motor de comparación con reglas de temporalidad, IVA, confianza y degradación** (dos benchmarks, múltiples fuentes, nivel de confianza compuesto): **10–15 % del esfuerzo**. Vinculado a NFR-CAL-004 y NFR-CAL-006.
- **Integraciones externas:** 3 grupos de datasets oficiales (SECOP II contratos, archivos por año, TVEC) + 2 fuentes retail con captura controlada. Cada fuente retail adicional suma un estimado de **+3–5 % de esfuerzo**.
- **Revisión humana y trazabilidad total** (historial de correcciones, instantáneas en casos, auditoría): transversal; suma un estimado de **+10 %** sobre las épicas afectadas.
- **Cumplimiento** (Ley 1581/2012, reglas de captura, lenguaje no acusatorio verificable): transversal; bajo esfuerzo de construcción, pero condiciona el paso a producción.

### Riesgos Técnicos Identificados

1. **Disponibilidad limitada del dato en SECOP II**: Riesgo ALTO (confirmado por D4)
   - Impacto: ~50–56 % de los contratos en categoría no publica precio unitario (valores globales, oferta ganadora no publicada, formatos en blanco); el aporte de SECOP II al análisis es menor que el universo identificado.
   - Mitigación: separar disponibilidad en la fuente, cobertura de extracción y cobertura end-to-end (NFR-CAL-003); selección de ~8 documentos con anexos y ZIP; detección de imágenes incrustadas; precio derivado bajo reglas estrictas (FR-099); la TVEC como base principal del Benchmark 1.
2. **Falsos positivos por emparejamiento o referencia inadecuada**: Riesgo ALTO
   - Impacto: señales sin sustento destruyen la credibilidad (KPI ≥ 70 % de señales sustentadas) y aumentan el riesgo legal.
   - Mitigación: reglas de equivalencia validadas por el PO; no relajar criterios; nivel de confianza visible; umbrales distintos para mismo modelo y equivalente; validación con 3 o más analistas.
3. **IVA indeterminado en la TVEC**: Riesgo MEDIO
   - Impacto: si no se determina la base tributaria de los precios TVEC, gran parte del Benchmark 1 queda marcado como incompleto o no confiable.
   - Mitigación: tarea de verificación **INV-01** (documentación oficial de Colombia Compra Eficiente / TVEC) antes de cerrar la arquitectura analítica. Hasta verificarlo: IVA indeterminado → comparación incompleta/no confiable. No se asume la respuesta.
4. **Cambios o bloqueo en fuentes retail**: Riesgo MEDIO
   - Impacto: la captura automática de Alkosto o Falabella deja de funcionar sin aviso.
   - Mitigación: la automatización no es condición de éxito; suspensión automática con alerta; carga manual o semiautomática; base de observaciones desacoplada; revisión de términos de uso antes de producción.
5. **Costo de IA por documento**: Riesgo MEDIO
   - Impacto: la extracción multimodal de documentos largos (estudios previos de 30–50 páginas) puede tener costos altos.
   - Mitigación: procesar solo documentos priorizados y solo las páginas relevantes; medir el costo por documento en D4; registro de costos por componente (NFR-OBS-001).
6. **Cambios de esquema o caídas de la API de datos.gov.co**: Riesgo MEDIO
   - Impacto: ingesta incompleta o detenida.
   - Mitigación: app token, carga incremental, reintentos, validaciones de calidad y alertas.
7. **Usuario de diseño no validado**: Riesgo ALTO (de producto)
   - Impacto: se construye un flujo que los analistas no adoptan.
   - Mitigación: D5 (mockups) con 3–5 analistas antes de cerrar el alcance para desarrollo; la búsqueda de usuarios corre en paralelo.
8. **Riesgo legal y reputacional por proveedores nombrados en señales**: Riesgo MEDIO
   - Impacto: reclamos de proveedores o entidades.
   - Mitigación: lenguaje no acusatorio verificable; solo datos públicos; mecanismo de corrección; acceso con login; publicación abierta fuera del MVP.

---

## 7. Próximos Pasos

Este PRD está **aprobado conceptualmente**. D4 completó la medición técnica (decisiones D4-1 a D4-3 incorporadas); la precisión por campo y el umbral de aceptación se cierran con **D4-4**, y el alcance de experiencia con **D5**.

**Secuencia de producto:**

1. **Validaciones pendientes** (ver tabla abajo): **D4-4** e **INV-01** en paralelo con la arquitectura.
2. **Arquitectura del sistema:** stack, separación ingesta / extracción documental, almacenamiento de evidencia, conectores de adquisición y qué capacidades administrativas requieren UI.
3. **Refinamiento de Historias de Usuario** desde las épicas, con trazabilidad a FRs y NFRs.
4. **Mockups y validación con usuarios (D5)** con 3–5 analistas del perfil de diseño; incluye la línea base manual de D2.
5. **Estimación técnica** del esfuerzo con los resultados de D4 y la arquitectura.
6. **Desarrollo del MVP** por incrementos, priorizando el flujo *explorar → detectar señal → revisar comparación → revisar evidencia → guardar caso → continuar investigación*.
7. **Pruebas y validación** contra los KPIs del Brief y los NFRs.

Este orden no reemplaza la secuencia propia de los workflows del Método Ceiba cuando estos la requieran.

### Validaciones Técnicas Pendientes

| # | Validación | Qué debe determinar | Bloquea |
|---|---|---|---|
| **D4** | Spike de extracción sobre documentos SECOP II reales | ✅ **Completado** (2026-10-02): disponibilidad, campos, evidencia, OCR/multimodal, costo, FR-026 ([informe](insumos/D4-spike-extraccion-documental.md)). Decisiones D4-1 a D4-3 incorporadas. | — |
| **D4-4** | Validación manual de la extracción (228 filas) | Precisión global y por campo, falsos positivos, campos no encontrados, cobertura real y **calibración del umbral de aceptación** (FR-028). | Cierre de la meta de cobertura de extracción y del umbral P-15 |
| **INV-01** | Base tributaria de precios TVEC | Verificar con documentación oficial de Colombia Compra Eficiente / TVEC si los precios incluyen IVA. Hasta verificarlo: IVA indeterminado → comparación incompleta/no confiable. | Cierre de la arquitectura analítica del Benchmark 1 |
| **D5** | Validación de mockups con usuarios | Si el flujo resuelve la tarea del analista; reevaluar la exportación del expediente (ÉPICA-009). | Cierre del alcance de experiencia para desarrollo |
| **D2** | Discovery con analistas | Frecuencia del problema y **línea base manual** del KPI de eficiencia. | Medición de NFR-CAL-008 |
| **D3** | Análisis competitivo | Capacidades existentes y vacío real; confirma el diferenciador. | Ninguno para la arquitectura; sí para el posicionamiento |
| **ToS** | Términos de uso de Alkosto y Falabella | Si permiten la captura automática. | Paso a producción de la captura automática (no bloquea el MVP: existe carga manual) |

No se reabren el Brief ni D1/D6 salvo que D4 encuentre evidencia que contradiga una decisión existente.
---

## 📝 Preguntas y Decisiones Pendientes

| # | Categoría | Pregunta | Respuesta | Estado |
|---|-----------|----------|-----------|--------|
| P-01 | Arquitectura analítica | Ventana temporal de comparables. | ✅ **Decisión:** configurable. **Configuración inicial:** Benchmark 1 ±6 meses (ampliable a ±12 si faltan comparables); Benchmark 2 ±30 días. No son reglas estadísticas universales. **Sujeto a:** recalibración con evidencia real. → FR-055, FR-056 | ✅ Respondida |
| P-02 | Arquitectura analítica | Mínimo de observaciones para referencia agregada. | ✅ **Decisión:** configurable. **Configuración inicial:** Benchmark 1 ≥ 5 comparables; Benchmark 2 ≥ 3 observaciones de ≥ 2 fuentes. Por debajo: "referencia disponible" / evidencia limitada. **Sujeto a:** recalibración. → FR-058, FR-059 | ✅ Respondida |
| P-03 | Arquitectura analítica | Umbral para generar una señal. | ✅ **Decisión:** estrategia híbrida configurable. **Configuración inicial:** Q3 + 1,5 × IQR con muestra suficiente y homogénea; si no, mismo modelo ≥ +30 % y equivalente ≥ +50 %. Solo **priorizan** revisión; no significan sobreprecio ni irregularidad. **Sujeto a:** recalibración con evidencia real. → FR-063 | ✅ Respondida |
| P-04 | Alcance | ¿Señal también por precio anormalmente bajo? | ✅ **Decisión:** en el MVP solo desviaciones por encima generan señal. Precios anormalmente bajos → revisión de calidad (posible error de extracción, cantidad, normalización, producto o base tributaria). **Sujeto a:** evaluación posterior como otro tipo de señal. → FR-063 | ✅ Respondida |
| P-05 | KPIs | Denominador del KPI de cobertura. | ✅ **Decisión (actualizada por D4-1):** cobertura sobre SECOP II, separada en disponibilidad en la fuente (se reporta), cobertura de extracción (meta ≥ 80 %, provisional) y cobertura end-to-end (se reporta); TVEC aparte. → NFR-CAL-003, FR-091 | ✅ Respondida |
| P-06 | KPIs | Metodología de precisión. | ✅ **Decisión:** correctos / realmente presentes según validación manual, con las reglas de NFR-CAL-002. Se reporta global **y por campo** (marca, modelo, tamaño, cantidad, precio unitario). **Sujeto a:** medición en D4. → NFR-CAL-002, FR-091 | ✅ Respondida |
| P-07 | Supuestos | IVA en precios TVEC. | 🔬 **No es decisión del PO: es un hecho externo.** Se convierte en la tarea **INV-01**: verificar con documentación oficial de Colombia Compra Eficiente / TVEC la base tributaria de los precios, antes de cerrar la arquitectura analítica. **Hasta verificarlo:** IVA indeterminado → comparación incompleta/no confiable. No se asume la respuesta. → FR-057 | 🔄 En validación (INV-01) |
| P-08 | FRs | Rol Revisor. | ✅ **Decisión:** Administrador/PO = Revisor (valida extracción, corrige datos, revisa clasificación, gestiona la cola de baja confianza). Los analistas piloto evalúan producto y señales y reportan errores (FR-070). → FR-016, FR-032 | ✅ Respondida |
| P-09 | NFR-Performance | Tiempos y concurrencia. | ✅ **Decisión:** búsqueda/filtros ≤ 3 s p95, ficha/señal ≤ 3 s p95, 20 usuarios concurrentes. **Naturaleza:** objetivos iniciales de diseño del piloto, no contractuales; recalibrables. → NFR-PER-001 a 003 | ✅ Respondida |
| P-10 | NFR-Disponibilidad | Disponibilidad y respaldo. | ✅ **Decisión:** 99 % mensual, backup diario, retención 30 días, RPO y RTO ≤ 24 h. **Naturaleza:** objetivos iniciales de ingeniería, sin SLA contractual. → NFR-DIS-001, 002 | ✅ Respondida |
| P-11 | NFR-Datos | Conservación de evidencia documental. | ✅ **Decisión:** se conserva copia de todo documento del que se extraiga información usada en una señal, con hash, URL original, fuente, fecha de descarga, identificador y página/hoja/celda. **Sujeto a:** estrategia de almacenamiento en arquitectura. → FR-024, NFR-DIS-003 | ✅ Respondida |
| P-12 | FRs / Seguridad | Modo de registro en el piloto. | ✅ **Decisión:** registro **por invitación** durante discovery/piloto; sin registro público. **Configuración inicial:** sesión de 30 min de inactividad, configurable. → FR-083, NFR-SEG-003 | ✅ Respondida |
| P-13 | NFR-Datos | Frecuencia de ingesta pública. | ✅ **Decisión:** SECOP II y TVEC con ingesta incremental **diaria** (configurable). Ingesta y extracción documental separadas: la ingesta no dispara reprocesamiento con IA. **Sujeto a:** arquitectura. → FR-003, NFR-DAT-001 | ✅ Respondida |
| P-14 | NFR-Datos | Frecuencia y límites de captura retail. | ✅ **Decisión:** captura automática **semanal** (configurable). **Configuración inicial:** 1 solicitud cada 2 s y 2.000 por semana, como parámetros sujetos a términos de uso, `robots.txt`, comportamiento de la fuente y validación técnica; suspensión ante restricciones. → NFR-CUM-003, NFR-DAT-003, FR-047 | ✅ Respondida |
| P-15 | FRs | Confianza mínima para aceptar un dato extraído. | ✅ **Decisión:** no se fija 0,9. El sistema soporta un **umbral configurable** de aceptación automática; el puntaje del modelo no se interpreta como probabilidad calibrada. **Sujeto a:** calibración con la validación manual **D4-4** (relación confianza ↔ corrección real). Sin calibración, los datos críticos de confianza baja o incierta van a revisión humana. → FR-028 | ✅ Respondida (valor sujeto a D4) |
| D4-1 | KPIs | Cobertura frente a límite de la fuente. | ✅ **Decisión:** tres indicadores (NFR-CAL-003). Meta solo para cobertura de extracción: ≥ 80 % provisional; recalibración explícita si la evidencia lo exige. | ✅ Respondida |
| D4-2 | Alcance | FR-026 múltiples oferentes. | ✅ **Decisión:** pospuesto fuera del core del MVP; capacidad futura en ÉPICA-009. | ✅ Respondida |
| D4-3 | FRs | Precio unitario derivado. | ✅ **Decisión:** permitido con las 6 condiciones de FR-099; nunca en contratos mixtos ni con el valor de datos abiertos (FR-100); `precio_unitario_tipo = derivado` con menor confianza propagada a la señal (FR-068). | ✅ Respondida |
| D4-4 | KPIs | Precisión y calibración del umbral. | 🔄 **En ejecución:** validación manual de 228 filas, priorizando precio unitario, cantidad, tamaño, modelo, marca. Alimenta precisión global y por campo, falsos positivos, campos no encontrados, cobertura real y umbral P-15. | 🔄 En validación (D4-4) |

---

**Estado del Documento**: PRD aprobado conceptualmente — D4 completado; sujeto a validación de precisión D4-4 y validación de usuarios D5  
**Última actualización**: 2026-10-02

---

> **Método Ceiba generar prd** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
