# Historia #069: Explorar el listado de compras públicas de televisores

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Búsqueda y Filtrado de Compras  
**Prioridad:** Crítica  
**FRs relacionados:** FR-071, FR-072

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** abrir una vista de exploración que liste los contratos de SECOP II, las órdenes de compra de la TVEC y sus ítems de televisor, con paginación, conteo de resultados y un panel donde se aplican y limpian los filtros,  
**Para** tener una puerta de entrada única al universo de compras de televisores y llegar desde ahí a la ficha de cualquier contrato.

## Descripción

Esta HU construye la **vista base de exploración** ("Exploración") sobre la que se montan los filtros (HU-070, HU-071, HU-072) y el ordenamiento configurable (HU-073). Es una capacidad determinística: funciona sin IA, sobre los datos estructurados ingeridos de SECOP II y TVEC y sobre los ítems ya extraídos, comparados y señalados por los procesos de otras épicas. Si alguno de esos datos aún no existe para un registro, la vista lo muestra como "Sin dato" o "Pendiente" sin bloquear el listado.

La vista ofrece dos modos de presentación del mismo universo: **por contratos** (un registro por contrato SECOP II u orden de compra TVEC) y **por ítems de televisor** (un registro por ítem, que es la unidad de análisis del producto). También define el mecanismo común de filtros: panel, etiquetas de filtros aplicados, combinación de criterios, botón "Limpiar filtros" y conservación del estado en la dirección (URL) de la página. Cada criterio de filtro concreto se especifica en su propia HU; esta HU entrega el panel con el espacio para ellos y la regla de combinación.

Las HUs de filtros y ordenamiento dependen de esta vista para mostrarse, pero pueden construirse en paralelo porque cada una define su criterio sobre el mismo conjunto de resultados descrito aquí.

---

## Criterios de Aceptación

### Escenario 1: Abrir la exploración en modo contratos (happy path)

- **Dado** que el Analista inició sesión y el universo contiene registros de SECOP II y TVEC
- **Cuando** abre la opción de menú "Exploración"
- **Entonces** ve el listado en modo "Contratos" seleccionado por defecto, ordenado por fecha de firma u orden de la más reciente a la más antigua, con 25 registros por página, el texto "Mostrando 1–25 de {total} contratos" y las columnas definidas en la regla RN-05

### Escenario 2: Cambiar al modo ítems de televisor

- **Dado** que el Analista está en la exploración en modo "Contratos"
- **Cuando** selecciona el modo "Ítems de televisor"
- **Entonces** el listado muestra un registro por ítem de televisor incluido, con las columnas de la regla RN-06, el texto "Mostrando 1–25 de {total} ítems de televisor", vuelve a la página 1 y conserva los filtros aplicados

### Escenario 3: Paginar los resultados

- **Dado** que el listado tiene más registros que el tamaño de página
- **Cuando** el Analista usa los controles "Anterior", "Siguiente" o un número de página, o cambia el tamaño de página a 50 o 100
- **Entonces** el listado muestra el bloque correspondiente, actualiza el texto "Mostrando {desde}–{hasta} de {total}" y conserva modo, filtros y orden; al cambiar el tamaño de página vuelve a la página 1

### Escenario 4: Abrir la ficha desde el listado

- **Dado** que el Analista ve un registro en el listado
- **Cuando** activa el registro (clic, toque o tecla Enter sobre la fila)
- **Entonces** se abre la ficha del contrato u orden correspondiente; si el registro era un ítem, la ficha se abre posicionada en ese ítem

### Escenario 5: Volver de la ficha conservando el estado

- **Dado** que el Analista aplicó filtros, eligió un orden y está en la página 3, y luego abrió una ficha
- **Cuando** usa la acción "Volver a la exploración" o el botón atrás del navegador
- **Entonces** la exploración se muestra con el mismo modo, filtros, orden, tamaño de página y página 3

### Escenario 6: Combinar filtros y ver etiquetas de filtros aplicados

- **Dado** que el Analista aplicó dos o más criterios de filtro desde el panel
- **Cuando** el listado se actualiza
- **Entonces** solo aparecen los registros que cumplen **todos** los criterios aplicados, se muestra una etiqueta por cada criterio sobre el listado con la forma "{Nombre del filtro}: {valor}" y el conteo total se recalcula

### Escenario 7: Quitar un filtro o limpiar todos

- **Dado** que hay filtros aplicados
- **Cuando** el Analista quita una etiqueta con su botón "Quitar" o usa "Limpiar filtros"
- **Entonces** se elimina ese criterio (o todos), el listado se recalcula, vuelve a la página 1 y el orden elegido se conserva

### Escenario 8: Compartir o recargar la URL de la exploración

- **Dado** que el Analista tiene modo, filtros, orden y página aplicados
- **Cuando** recarga la página o abre la misma URL en otra pestaña con su sesión activa
- **Entonces** la exploración se muestra con exactamente el mismo estado

### Escenario 9: Universo vacío

- **Dado** que todavía no se ha cargado ningún registro del universo de televisores
- **Cuando** el Analista abre la exploración
- **Entonces** ve el mensaje "Aún no hay compras de televisores disponibles. Los datos aparecerán cuando termine la primera carga de SECOP II y TVEC." y no se muestran tabla, paginación ni panel de filtros activo

### Escenario 10: Sin resultados para los filtros

- **Dado** que el Analista aplicó filtros que ningún registro cumple
- **Cuando** el listado se actualiza
- **Entonces** ve el mensaje "No encontramos resultados con los filtros aplicados." junto con las etiquetas de filtros y el botón "Limpiar filtros", y el conteo muestra "0 resultados"

### Escenario 11: Estado de carga

- **Dado** que el Analista abrió la exploración o cambió modo, filtro, orden o página
- **Cuando** la respuesta aún no ha llegado
- **Entonces** se muestra un indicador de carga sobre el área del listado, los controles que lanzarían una nueva consulta quedan deshabilitados y un lector de pantalla anuncia "Cargando resultados"

### Escenario 12: Error al cargar resultados

- **Dado** que la consulta de resultados falla o no responde en 15 segundos
- **Cuando** el Analista espera el listado
- **Entonces** ve el mensaje "No fue posible cargar los resultados. Intenta de nuevo en unos minutos." con el botón "Reintentar", se conservan los filtros y el orden elegidos, y al usar "Reintentar" se repite la misma consulta una sola vez por clic

### Escenario 13: Acceso sin sesión

- **Dado** que una persona sin sesión iniciada abre la URL de la exploración
- **Cuando** el sistema procesa la solicitud
- **Entonces** no muestra ningún dato del universo y la redirige a la pantalla de inicio de sesión; después de iniciar sesión vuelve a la URL de exploración solicitada con su estado

### Escenario 14: Sesión expirada durante la exploración

- **Dado** que la sesión del Analista expiró por inactividad
- **Cuando** intenta cambiar de página, de modo o un filtro
- **Entonces** el sistema muestra "Tu sesión expiró. Inicia sesión de nuevo para continuar." y lo redirige al inicio de sesión, conservando la URL de exploración para retomar el estado

### Escenario 15: Registros con datos faltantes

- **Dado** que un registro no tiene proveedor, modalidad, valor o fecha publicados, o aún no tiene ítems extraídos ni desviación calculada
- **Cuando** aparece en el listado
- **Entonces** cada celda sin dato muestra "Sin dato" y las columnas de análisis pendientes muestran "Pendiente", sin ocultar el registro

### Escenario 16: Vista en tablet y móvil

- **Dado** que el Analista abre la exploración en un ancho de pantalla entre 360 px y 1365 px
- **Cuando** la vista se adapta
- **Entonces** en anchos desde 768 px el panel de filtros se pliega detrás del botón "Filtros ({n})", y en anchos menores a 768 px cada registro se presenta como tarjeta con las mismas columnas en forma de lista etiqueta–valor, sin perder ninguna acción disponible en escritorio

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública (usuario de diseño del MVP). El Administrador también puede usar la vista con las mismas capacidades.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador. Sin sesión no hay acceso (la exploración pública anónima está excluida del MVP).
- **Valor de negocio:** Es la puerta de entrada del flujo *explorar → detectar señal → revisar comparación → revisar evidencia → guardar caso*; sin ella el analista no puede llegar a los contratos ni a las señales.

### Reglas de Negocio

- **RN-01 Universo visible en modo "Contratos":** se listan los contratos de SECOP II y las órdenes de compra de la TVEC marcados como candidatos de televisor que **no** fueron descartados por completo en la clasificación. Un registro se muestra si tiene al menos un ítem con clasificación "incluido", o si su clasificación aún no ha concluido (candidato identificado sin ítems clasificados, o con ítems en "requiere revisión"). No se muestran los registros cuyos ítems candidatos quedaron todos "excluidos".
- **RN-02 Universo visible en modo "Ítems de televisor":** se listan solo los ítems con clasificación "incluido". Los ítems en "requiere revisión" o "excluido" no aparecen en este modo (se consultan en la ficha del contrato).
- **RN-03 Orden de compra TVEC como "contrato":** en esta vista y en la ficha, una orden de compra de la TVEC se trata como un registro de compra equivalente a un contrato; se identifica con la etiqueta de fuente "TVEC" y su número de orden.
- **RN-04 Orden por defecto:** fecha de la compra (fecha de firma en SECOP II; fecha de la orden en TVEC) de la más reciente a la más antigua; empates por identificador del registro en orden alfabético ascendente. Los registros sin fecha van al final. El orden configurable lo define HU-073.
- **RN-05 Columnas del modo "Contratos":** Fuente ("SECOP II" o "TVEC"), Identificador (ID del contrato `CO1.PCCNTR.…` en SECOP II; número de orden en TVEC), Entidad, Proveedor, Modalidad, Fecha, Valor del contrato u orden, N.º de ítems de televisor (cantidad de ítems "incluido"; "Pendiente" si aún no hay ítems clasificados), Señal ("Merece revisión ({n})" si al menos un ítem tiene señal vigente; "Sin señal" en otro caso), Mayor desviación (la mayor desviación porcentual calculada entre los ítems del registro; "Pendiente" si no hay ninguna) y Nivel de confianza (el mayor nivel de confianza entre las señales vigentes del registro; "—" si no tiene señal).
- **RN-06 Columnas del modo "Ítems de televisor":** Fuente, Descripción del ítem (marca + modelo normalizado + tamaño en pulgadas cuando existan; si no, la descripción original del ítem, truncada a 80 caracteres con "…" y texto completo disponible al pasar el foco o el cursor), Entidad, Proveedor, Fecha, Cantidad, Precio unitario (con la marca "Explícito" o "Derivado" según el tipo de precio unitario), Desviación (mayor desviación porcentual del ítem frente a sus referencias disponibles), Nivel de confianza (de la señal vigente del ítem; "—" si no tiene) y Señal ("Merece revisión" o "Sin señal").
- **RN-07 Paginación:** tamaño por defecto 25 registros; opciones 25, 50 y 100. Página mínima 1; si la URL pide una página mayor que la última existente, se muestra la última página. Un valor de tamaño de página distinto de 25, 50 o 100 en la URL se reemplaza por 25.
- **RN-08 Combinación de filtros:** entre criterios distintos se aplica Y (todos deben cumplirse); entre varios valores del mismo criterio se aplica O (basta uno). Cualquier cambio de filtro devuelve el listado a la página 1. El conteo total siempre refleja los filtros aplicados.
- **RN-09 Estado en la URL:** modo, filtros, orden, tamaño de página y página se representan en la URL. Un parámetro desconocido o con valor inválido se ignora sin mostrar error, y se aplica el valor por defecto de ese parámetro.
- **RN-10 Formatos de presentación:** fechas en `DD/MM/AAAA` (hora de Colombia, UTC−5); valores en pesos colombianos con el formato `$ 2.490.000` (sin decimales, punto como separador de miles); desviaciones con signo, una cifra decimal y coma decimal: `+35,2 %`; cantidades como enteros con separador de miles.
- **RN-11 Datos faltantes:** campo no publicado por la fuente → "Sin dato". Dato analítico aún no calculado por los procesos de extracción, comparación o señales → "Pendiente". Nunca se deja una celda vacía.
- **RN-12 Lenguaje:** ningún texto de la vista usa los términos "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal" aplicados a un contrato, persona o empresa; las señales se nombran siempre "señal que merece revisión" o "Merece revisión".
- **RN-13 Tiempo de respuesta:** objetivo inicial de diseño, configurable y recalibrable: la carga inicial y cada cambio de modo, filtro, orden o página responden en ≤ 3 segundos (p95) con el volumen del MVP (~355 contratos SECOP II y ~1.150 líneas TVEC) y 20 usuarios concurrentes. El tiempo máximo de espera antes de mostrar error es 15 segundos (valor inicial configurable).
- **RN-14 Reintento:** cada clic en "Reintentar" lanza una sola consulta; mientras está en curso, el botón queda deshabilitado para evitar consultas duplicadas.
- **RN-15 Accesibilidad (valor inicial de diseño, WCAG 2.1 AA):** todos los controles son operables con teclado y tienen foco visible; contraste mínimo 4,5:1 para texto y 3:1 para componentes; las marcas de señal y de tipo de precio usan texto además del color; la tabla usa encabezados de columna asociados; el conteo de resultados se anuncia a lectores de pantalla cuando cambia.
- **RN-16 Diseño responsive (valor inicial de diseño):** optimizado para escritorio desde 1366 × 768 px; funcional sin pérdida de capacidades en tablet desde 768 px y en móvil desde 360 px; compatible con las 2 últimas versiones de Chrome, Edge, Firefox y Safari.

### Interfaz

- Opción de menú "Exploración", accesible para usuarios con sesión.
- Selector de modo con dos opciones: "Contratos" (por defecto) e "Ítems de televisor".
- Panel lateral de filtros (escritorio) con las secciones que aportan HU-070, HU-071 y HU-072, y el botón "Limpiar filtros" (deshabilitado si no hay filtros).
- Barra de etiquetas de filtros aplicados sobre el listado, cada una con botón "Quitar".
- Texto de conteo "Mostrando {desde}–{hasta} de {total} {contratos | ítems de televisor}".
- Tabla de resultados con las columnas de RN-05 o RN-06; filas activables para abrir la ficha.
- Controles de paginación "Anterior", números de página, "Siguiente" y selector "Resultados por página: 25 / 50 / 100".
- Espacio para la indicación de fecha de actualización de los datos (definida en HU-083) y para el control de orden (HU-073).
- Estados: carga (indicador), vacío del universo, sin resultados, error con "Reintentar".

### Sistemas Externos (Si aplica)

No consume sistemas externos en tiempo real. Lee los datos ya almacenados por la plataforma: contratos SECOP II (dataset `jbjy-vk9h`) y órdenes e ítems TVEC (`usqp-5nsn` / `3hdv-smhz` / `rgxm-mmea`) ingeridos previamente, y los resultados de clasificación, extracción, comparación y señales generados por otros procesos de la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-070, HU-071, HU-072 (filtros), HU-073 (ordenamiento), HU-076 (ficha del contrato), HU-083 (fecha de actualización)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01, RN-02):** el universo visible excluye los registros descartados por completo y el modo ítems muestra solo ítems "incluido".
- **Resuelto (RN-03):** la orden de compra TVEC se trata como "contrato" en exploración y ficha.
- **Resuelto (RN-07):** paginación de 25 registros por defecto con opciones 25/50/100.
- **Resuelto (RN-09):** el estado de la exploración se conserva en la URL y al volver de la ficha.
- **Resuelto (RN-10):** formatos de fecha, moneda y porcentaje, en hora de Colombia.
- **Resuelto (RN-05, RN-06):** la "desviación" del registro es la mayor desviación porcentual calculada entre sus referencias o ítems; la confianza del contrato es la mayor entre sus señales vigentes.

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
