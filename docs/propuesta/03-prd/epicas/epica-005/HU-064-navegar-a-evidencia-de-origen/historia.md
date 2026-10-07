# Historia #064: Navegar desde la señal hasta el contrato, el documento y la página de origen, y cada observación de referencia

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Presentación de Evidencia Trazable  
**Prioridad:** Crítica  
**FRs relacionados:** FR-066

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ir con un clic desde el detalle de una señal al documento y la página exacta de donde salió el precio, al contrato en la fuente oficial y a la evidencia de cada observación usada como referencia,  
**Para** verificar por mí mismo cada dato antes de decidir si el caso merece revisión.

## Descripción

Desde el detalle de la señal, el Analista accede a:
1. **Evidencia del precio contratado:** para SECOP II, la **copia conservada** del documento (no solo el enlace original, que puede cambiar o desaparecer), abierta en la página, o en la hoja y celda, donde está el precio; para la TVEC, el registro estructurado de la orden.
2. **Contrato:** su ficha en el sistema y la URL pública del proceso en la fuente oficial.
3. **Cada observación de referencia:** su registro y su evidencia (documento o registro público; o para retail, la URL, la fecha, el método de adquisición y la evidencia adjunta).

Se cumple NFR-USA-003: de la lista de señales a la evidencia de origen en **≤ 3 clics** (1: abrir la señal; 2: "Ver evidencia"; la evidencia se abre ya posicionada en la página o celda).

---

## Criterios de Aceptación

### Escenario 1: Documento de origen en la página exacta

- **Dado** que el precio de la señal SG-1 se extrajo de la página 4 de "Oferta económica.pdf" (copia conservada con hash)
- **Cuando** el Analista pulsa "Ver evidencia" junto al precio contratado
- **Entonces** se abre el visor de la copia conservada en la página 4, con un panel que muestra nombre del documento, ubicación "Página 4", fecha de descarga, hash, URL original (enlace) y el aviso "Estás viendo la copia conservada por el sistema el {DD/MM/AAAA}"

### Escenario 2: Hoja de cálculo

- **Dado** que el precio derivado se tomó de la hoja "Económica", celdas F12 (valor total) y D12 (cantidad) de "Anexo 3.xlsx"
- **Cuando** el Analista pulsa "Ver evidencia"
- **Entonces** el panel muestra "Hoja Económica, celdas F12 y D12", la fórmula del precio derivado y el botón "Descargar copia conservada"

### Escenario 3: Archivo dentro de un comprimido

- **Dado** que el documento de origen es "Cotizacion.pdf" dentro de "Anexos.zip"
- **Cuando** el Analista abre la evidencia
- **Entonces** el panel muestra la ruta "Anexos.zip › Cotizacion.pdf" y el visor abre la página indicada de la copia conservada de "Cotizacion.pdf"

### Escenario 4: Ítem de la TVEC

- **Dado** que el precio de la señal proviene de la TVEC
- **Cuando** el Analista pulsa "Ver evidencia"
- **Entonces** ve el registro de la orden (número de orden, línea, descripción del ítem, precio unitario, cantidad, total, fecha, entidad, dataset de origen y fecha de corte) y el enlace "Ver en datos abiertos"

### Escenario 5: Contrato y fuente oficial

- **Dado** que el Analista está en el detalle de la señal
- **Cuando** pulsa "Ver ficha del contrato" o "Ver en la fuente oficial"
- **Entonces** el primero abre la ficha del contrato en el sistema y el segundo abre la URL pública del proceso en SECOP II en una pestaña nueva

### Escenario 6: Evidencia de una observación retail

- **Dado** que una observación de referencia es de Alkosto con método manual y captura de pantalla adjunta
- **Cuando** el Analista pulsa "Ver evidencia" en esa fila
- **Entonces** ve tienda, producto, SKU/EAN, precio efectivo, precio anterior (si existe, rotulado "Precio anterior – solo evidencia"), fecha de observación, método "Manual", etiqueta "Observación manual", la captura adjunta, el enlace a la URL de la tienda y el aviso "La página de la tienda puede haber cambiado desde el {DD/MM/AAAA}; la evidencia conservada es la de esa fecha"

### Escenario 7: Evidencia de una observación pública

- **Dado** que una observación del Benchmark 1 es un ítem SECOP II con precio extraído
- **Cuando** el Analista pulsa "Ver evidencia" en esa fila
- **Entonces** se abre la copia conservada del documento de esa observación en su página, con el mismo panel del escenario 1

### Escenario 8: Copia no disponible

- **Dado** que la copia conservada del documento no se puede abrir en ese momento
- **Cuando** el Analista pulsa "Ver evidencia"
- **Entonces** ve "La copia del documento no está disponible en este momento. Puedes consultar el original en la fuente oficial." con el enlace a la URL original, y el sistema registra el incidente en el log con la señal, el documento y la fecha-hora

### Escenario 9: Página que no se puede mostrar

- **Dado** que el visor no puede mostrar la página (formato no visualizable, ej. DOC antiguo)
- **Cuando** el Analista abre la evidencia
- **Entonces** el panel muestra la ubicación ("Página 4") y el botón "Descargar copia conservada"

### Escenario 10: Volver al detalle

- **Dado** que el Analista abrió una evidencia desde la versión 1 de una señal
- **Cuando** pulsa "Volver a la señal"
- **Entonces** regresa al detalle en la misma versión 1

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (principal); Administrador también puede consultar.
- **Permisos requeridos:** Sesión iniciada (Analista o Administrador). Sin sesión → inicio de sesión y regreso al destino.
- **Valor de negocio:** Trazabilidad 100 % navegable (NFR-CAL-004) y evidencia verificable en ≤ 3 clics (NFR-USA-003).

### Reglas de Negocio

**RN-01 – Versión.** Todos los enlaces usan los datos de la instantánea de la versión de la señal que se está viendo: el documento se identifica por el hash registrado en esa instantánea. Si el sistema tiene una copia más reciente del mismo documento con otro hash, se muestra la del hash de la instantánea.

**RN-02 – Ubicación.** PDF e imágenes: se abre en la página indicada. XLSX/XLS: se muestran hoja y celda(s) y se ofrece descarga. DOCX/DOC: se abre en la página si el visor lo permite; si no, ubicación + descarga. Comprimidos: se muestra la ruta "comprimido › archivo" y se abre el archivo contenido.

**RN-03 – Panel de evidencia documental.** Nombre, tipo, ruta en comprimido si aplica, ubicación (página u hoja/celda), fecha de descarga (DD/MM/AAAA), hash, URL original (enlace en pestaña nueva) y aviso "Estás viendo la copia conservada por el sistema el {DD/MM/AAAA}". Para precio derivado: fórmula con valor total y cantidad.

**RN-04 – Evidencia TVEC.** Registro con orden, línea, descripción, precio unitario, cantidad, total, fecha, entidad, dataset y fecha de corte; enlace "Ver en datos abiertos" al dataset oficial.

**RN-05 – Evidencia retail.** Tienda, producto, SKU/EAN, precio efectivo, precio anterior rotulado "Precio anterior – solo evidencia", indicación de precio condicionado si existiera, fecha de observación, método de adquisición, etiqueta "Observación manual" si aplica, evidencia adjunta (captura o archivo) visualizable, URL de la tienda en pestaña nueva y el aviso "La página de la tienda puede haber cambiado desde el {DD/MM/AAAA}; la evidencia conservada es la de esa fecha". No se muestra el usuario que registró la observación manual.

**RN-06 – Clics.** Desde la lista de señales: clic 1 abre la señal; clic 2 en "Ver evidencia" abre la evidencia ya posicionada. No se requieren pasos intermedios.

**RN-07 – Errores.** Copia no disponible: mensaje del escenario 8, enlace a la URL original y registro en log (señal, documento, fecha-hora). Evidencia retail adjunta no disponible: "La evidencia adjunta no está disponible en este momento." y el resto de datos de la observación. Página no visualizable: ubicación + descarga.

**RN-08 – Rendimiento.** La apertura de la evidencia muestra el panel en ≤ 3 s (p95) con el volumen del MVP (objetivo inicial de ingeniería); el documento puede terminar de cargarse después, mostrando "Cargando documento…".

### Interfaz

- En el detalle de la señal: "Ver evidencia" (precio contratado y cada observación), "Ver ficha del contrato", "Ver en la fuente oficial".
- Vista de evidencia: visor del documento o registro + panel de metadatos + "Volver a la señal" + "Descargar copia conservada" (cuando aplique).

### Sistemas Externos (Si aplica)

- URL pública del proceso SECOP II y URL original del documento: solo como enlaces externos en pestaña nueva.
- Página de la tienda: solo enlace externo. El sistema no consulta ni captura estas páginas al navegar.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-062 (instantánea), HU-063 (detalle de la señal).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Mostrar la copia conservada por hash de la instantánea** y no la versión actual del documento: resuelto en RN-01.
- **No mostrar al Analista el usuario que registró una observación manual** (minimización): resuelto en RN-05.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-005 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
