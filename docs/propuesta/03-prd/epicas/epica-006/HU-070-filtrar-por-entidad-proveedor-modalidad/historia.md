# Historia #070: Filtrar la exploración por entidad, proveedor y modalidad

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Búsqueda y Filtrado de Compras  
**Prioridad:** Crítica  
**FRs relacionados:** FR-071

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** buscar y seleccionar entidades compradoras y proveedores por nombre o NIT, y elegir una o varias modalidades de contratación,  
**Para** concentrar la exploración en las compras de televisores de los actores o modalidades que estoy investigando.

## Descripción

Esta HU agrega al panel de filtros de la vista "Exploración" (HU-069) tres criterios: **Entidad**, **Proveedor** y **Modalidad**. Los filtros funcionan en los dos modos de la vista ("Contratos" e "Ítems de televisor") y se combinan con el resto de criterios según la regla común: Y entre criterios distintos, O entre valores del mismo criterio.

Entidad y Proveedor se buscan escribiendo parte del nombre o del NIT y eligiendo una sugerencia; solo se sugieren actores presentes en el universo de compras de televisores. Por protección de datos personales (Ley 1581 de 2012, decisión PO 2026-10-05), el documento de un proveedor **persona natural** nunca se muestra ni se puede buscar: ese proveedor se encuentra solo por su nombre y se presenta con la leyenda "Persona natural — documento no visible". Modalidad se elige en una lista de casillas con las modalidades presentes en el universo y su número de registros.

Esta HU no incluye fichas de entidad ni de proveedor (excluidas de la épica); seleccionar una entidad o un proveedor solo filtra el listado.

---

## Criterios de Aceptación

### Escenario 1: Filtrar por una entidad buscada por nombre (happy path)

- **Dado** que el Analista está en la exploración
- **Cuando** escribe "tunja" en el campo "Entidad" y elige la sugerencia "Alcaldía de Tunja"
- **Entonces** el listado muestra solo los registros cuya entidad compradora es la Alcaldía de Tunja, aparece la etiqueta "Entidad: Alcaldía de Tunja" y el conteo se recalcula

### Escenario 2: Buscar entidad o proveedor por NIT

- **Dado** que el Analista está en la exploración
- **Cuando** escribe "891800846" o "891.800.846-1" en el campo "Entidad" (o el NIT de un proveedor persona jurídica en "Proveedor")
- **Entonces** las sugerencias incluyen el actor cuyo NIT coincide con los dígitos escritos, mostrando nombre y NIT

### Escenario 3: Seleccionar varias entidades o proveedores

- **Dado** que el Analista ya seleccionó una entidad
- **Cuando** selecciona una segunda entidad desde las sugerencias
- **Entonces** el listado muestra los registros de cualquiera de las dos entidades y se muestra una etiqueta por entidad

### Escenario 4: Límite de selección alcanzado

- **Dado** que el Analista ya seleccionó 10 entidades (o 10 proveedores)
- **Cuando** intenta seleccionar una más
- **Entonces** la selección no se agrega y se muestra junto al campo "Puedes seleccionar hasta 10 valores en este filtro."

### Escenario 5: Texto con menos de 3 caracteres

- **Dado** que el Analista está escribiendo en "Entidad" o "Proveedor"
- **Cuando** el texto tiene menos de 3 caracteres (sin contar espacios)
- **Entonces** no se muestran sugerencias y se muestra la ayuda "Escribe al menos 3 caracteres del nombre o del NIT."

### Escenario 6: Sin coincidencias en las sugerencias

- **Dado** que el Analista escribió 3 o más caracteres
- **Cuando** ningún actor del universo coincide
- **Entonces** se muestra "No hay entidades con ese nombre o NIT en el universo de televisores." (o "No hay proveedores con ese nombre o NIT en el universo de televisores.") y el listado no cambia

### Escenario 7: Pulsar Enter sin elegir una sugerencia

- **Dado** que el Analista escribió texto en "Entidad" o "Proveedor" pero no eligió ninguna sugerencia
- **Cuando** pulsa Enter o sale del campo
- **Entonces** no se aplica ningún filtro, el listado no cambia y se muestra "Selecciona una opción de la lista de sugerencias."

### Escenario 8: Filtrar por una o varias modalidades

- **Dado** que el Analista abre la sección "Modalidad"
- **Cuando** marca "Mínima cuantía" y "Subasta inversa"
- **Entonces** el listado muestra los registros de cualquiera de esas dos modalidades, cada casilla muestra el número de registros del universo con esa modalidad y aparecen las etiquetas correspondientes

### Escenario 9: Modalidad de órdenes TVEC y registros sin modalidad

- **Dado** que el universo incluye órdenes TVEC sin modalidad publicada y contratos SECOP II sin modalidad
- **Cuando** el Analista abre la sección "Modalidad"
- **Entonces** las órdenes TVEC sin modalidad aparecen agrupadas en la opción "Tienda Virtual del Estado (TVEC)" y los contratos SECOP II sin modalidad en la opción "Sin modalidad registrada", ambas seleccionables

### Escenario 10: Combinar entidad, proveedor y modalidad

- **Dado** que el Analista seleccionó una entidad, un proveedor y una modalidad
- **Cuando** el listado se actualiza
- **Entonces** solo aparecen los registros que cumplen los tres criterios a la vez, en la página 1; si ninguno cumple, se muestra el estado "No encontramos resultados con los filtros aplicados."

### Escenario 11: Registro sin proveedor publicado

- **Dado** que un contrato no tiene proveedor publicado
- **Cuando** el Analista aplica cualquier filtro de proveedor
- **Entonces** ese contrato no aparece en los resultados

### Escenario 12: Error al consultar sugerencias

- **Dado** que la consulta de sugerencias falla
- **Cuando** el Analista escribe en "Entidad" o "Proveedor"
- **Entonces** se muestra "No fue posible cargar las sugerencias. Intenta de nuevo." debajo del campo, los filtros ya aplicados se conservan y el listado no cambia

### Escenario 13: Proveedor persona natural buscado por nombre

- **Dado** que el universo incluye un contrato cuyo proveedor es "María Fernanda Ríos Peña" con tipo de documento "Cédula de Ciudadanía"
- **Cuando** el Analista escribe "fernanda rios" en "Proveedor" y elige la sugerencia
- **Entonces** la sugerencia se muestra como "María Fernanda Ríos Peña — Persona natural — documento no visible", el listado muestra los registros de ese proveedor, la etiqueta es "Proveedor: María Fernanda Ríos Peña" y el número de documento no aparece en sugerencias, etiquetas, listado ni URL

### Escenario 14: Escribir el número de cédula de un proveedor persona natural

- **Dado** que el proveedor "María Fernanda Ríos Peña" (Cédula de Ciudadanía) está en el universo
- **Cuando** el Analista escribe su número de cédula, completo o como prefijo, en "Proveedor"
- **Entonces** ese proveedor no se sugiere por coincidencia de documento, el número no se revela en ningún elemento de la pantalla y, si ningún NIT de persona jurídica ni nombre coincide, se muestra "No hay proveedores con ese nombre o NIT en el universo de televisores." y el listado no cambia

### Escenario 15: Proveedor sin tipo de documento o con tipo desconocido

- **Dado** que un contrato tiene documento de proveedor publicado pero el tipo de documento está vacío o no es reconocido
- **Cuando** el Analista busca ese proveedor
- **Entonces** se trata como persona natural: solo se encuentra por nombre, la sugerencia muestra "Persona natural — documento no visible" y escribir su número no lo sugiere

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador puede usar los mismos filtros.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Permite pasar del universo completo a las compras de una entidad, proveedor o modalidad, que es la forma natural en que el analista acota una investigación.

### Reglas de Negocio

- **RN-01 Origen de los datos:** SECOP II: entidad = `nombre_entidad` + `nit_entidad`; proveedor = `proveedor_adjudicado` + `documento_proveedor` + tipo de documento `tipodocproveedor`; modalidad = `modalidad_de_contratacion`, tal como se publican. TVEC: entidad, proveedor y modalidad tal como los publica el encabezado de la orden de compra; si la orden no publica modalidad, se agrupa como "Tienda Virtual del Estado (TVEC)".
- **RN-02 Búsqueda por nombre:** coincidencia parcial ("contiene"), sin distinguir mayúsculas, minúsculas ni tildes, e ignorando espacios repetidos. Ej.: "tunja", "TUNJÁ" y "alcaldia de  tunja" encuentran "Alcaldía de Tunja".
- **RN-03 Búsqueda por NIT:** se comparan solo los dígitos del texto escrito contra los dígitos del NIT publicado, ignorando puntos, guiones, espacios y el dígito de verificación separado por guion. La coincidencia es por prefijo: "891800" encuentra "891800846". En "Proveedor" solo participan en la búsqueda por número los proveedores persona jurídica (RN-17); el documento de un proveedor persona natural nunca se compara con el texto escrito.
- **RN-04 Activación de sugerencias:** a partir de 3 caracteres distintos de espacio; máximo 100 caracteres en el campo (los caracteres adicionales no se aceptan). Se muestran hasta 10 sugerencias, ordenadas por número de registros del actor en el universo de mayor a menor y, en empate, por nombre alfabético.
- **RN-05 Formato de sugerencia:** "{Nombre} — NIT {número}" para entidades y proveedores persona jurídica; "{Nombre} — Persona natural — documento no visible" para proveedores persona natural (RN-17); si no hay NIT/documento publicado, solo el nombre.
- **RN-06 Solo actores del universo:** las sugerencias y las opciones de modalidad se construyen únicamente con los registros visibles del universo de televisores (los mismos que lista la exploración en modo "Contratos").
- **RN-07 Identidad del actor:** una entidad o proveedor con NIT/documento publicado se identifica por ese número; registros con el mismo número y nombres escritos distinto se agrupan bajo el nombre más frecuente. Sin número publicado, se identifica por el nombre normalizado (RN-02). Para proveedores persona natural la agrupación por número es interna y el número nunca se expone (RN-17).
- **RN-08 Límite de selección:** hasta 10 entidades y hasta 10 proveedores seleccionados al mismo tiempo. Modalidad no tiene límite (se pueden marcar todas las opciones).
- **RN-09 Solo selección explícita:** los filtros de entidad y proveedor se aplican únicamente al elegir una sugerencia; el texto libre sin selección no filtra.
- **RN-10 Combinación:** O entre valores del mismo criterio; Y entre criterios distintos y con los demás filtros de la exploración. Todo cambio devuelve el listado a la página 1.
- **RN-11 Nulos:** registros sin proveedor publicado no cumplen ningún filtro de proveedor; registros sin entidad publicada no cumplen ningún filtro de entidad. Contratos SECOP II sin modalidad se agrupan en "Sin modalidad registrada".
- **RN-12 Modo ítems:** en modo "Ítems de televisor" el filtro se evalúa con la entidad, proveedor y modalidad del contrato u orden al que pertenece el ítem.
- **RN-13 Conteo por modalidad:** el número junto a cada modalidad es la cantidad de registros del universo con esa modalidad, sin aplicar los demás filtros, para que el Analista conozca el tamaño de cada grupo.
- **RN-14 Persistencia:** los valores seleccionados se representan en la URL de la exploración y se restauran al recargar o volver de la ficha. Un proveedor persona natural se representa en la URL con un identificador interno que no contiene ni deriva visiblemente su número de documento.
- **RN-15 Tiempo de respuesta:** las sugerencias aparecen en ≤ 1 segundo después de dejar de escribir durante 300 milisegundos, y la aplicación del filtro responde en ≤ 3 segundos (p95) con el volumen del MVP y 20 usuarios concurrentes (objetivos iniciales de diseño, configurables y recalibrables).
- **RN-16 Accesibilidad (WCAG 2.1 AA, valor inicial de diseño):** los campos tienen etiqueta visible; las sugerencias se recorren con flechas y se eligen con Enter; Escape cierra la lista; las casillas de modalidad se marcan con barra espaciadora; los mensajes de ayuda y error se anuncian a lectores de pantalla.
- **RN-17 Visibilidad del documento del proveedor (decisión PO 2026-10-05, Ley 1581 de 2012):** el tipo se toma de `tipodocproveedor`. Si es NIT (persona jurídica), el NIT se muestra y es buscable (RN-03). Si es cédula de ciudadanía, cédula de extranjería, pasaporte o cualquier otro tipo distinto de NIT, o si el tipo está vacío o es desconocido (se trata como persona natural por seguridad), el número de documento: (a) nunca se muestra en sugerencias, etiquetas, listado, URL, mensajes ni exportaciones; (b) no se compara con el texto escrito ni permite filtrar. En su lugar se muestra la leyenda "Persona natural — documento no visible". El nombre del proveedor sigue visible y buscable (RN-02). El valor almacenado solo es accesible al Administrador por medios técnicos o administrativos, fuera de esta interfaz.

### Interfaz

- Sección "Entidad" del panel de filtros: campo de texto con marcador "Nombre o NIT de la entidad", lista de sugerencias y lista de entidades seleccionadas con botón "Quitar" por cada una.
- Sección "Proveedor": campo con marcador "Nombre o NIT del proveedor", mismo comportamiento; los proveedores persona natural se muestran con la leyenda "Persona natural — documento no visible" en lugar del número.
- Sección "Modalidad": lista de casillas "{Modalidad} ({n})", ordenada por número de registros de mayor a menor; "Tienda Virtual del Estado (TVEC)" y "Sin modalidad registrada" al final.
- Etiquetas sobre el listado: "Entidad: {nombre}", "Proveedor: {nombre}", "Modalidad: {modalidad}".
- Mensajes: ayuda de 3 caracteres, sin coincidencias, límite de 10, selección explícita y error de sugerencias, con los textos de los escenarios.
- En tablet y móvil las secciones están dentro del panel plegable "Filtros ({n})".

### Sistemas Externos (Si aplica)

No consulta sistemas externos en tiempo real. Usa los datos de entidad, proveedor y modalidad ya ingeridos de SECOP II (`jbjy-vk9h`) y de la TVEC (`rgxm-mmea` y datasets de ítems).

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-069 (vista de exploración y regla de combinación), HU-071, HU-072 (otros filtros), HU-075 (filtros en la lista de señales)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01):** las órdenes TVEC sin modalidad publicada se agrupan en "Tienda Virtual del Estado (TVEC)".
- **Resuelto (RN-04, RN-08, RN-09):** entidad y proveedor se filtran solo eligiendo sugerencias (mínimo 3 caracteres, máximo 10 valores por filtro).
- **Resuelto (RN-07):** el actor se identifica por NIT/documento publicado y, en su defecto, por nombre normalizado.
- **Resuelto (RN-17):** el documento del proveedor persona natural (tipo distinto de NIT, vacío o desconocido) no se muestra ni es buscable; decisión PO 2026-10-05 (Ley 1581).

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
