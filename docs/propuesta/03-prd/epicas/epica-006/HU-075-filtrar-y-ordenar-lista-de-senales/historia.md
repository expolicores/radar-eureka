# Historia #075: Filtrar y ordenar la lista de señales que merecen revisión

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Priorización de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-071, FR-072, FR-073

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** filtrar la lista de señales por entidad, proveedor, modalidad, fechas, UNSPSC, territorio, valor y fuente, y ordenarla por desviación, valor, fecha o nivel de confianza,  
**Para** revisar primero las señales del territorio, período o actores que investigo, en el orden que más me sirve.

## Descripción

Esta HU agrega a la vista "Señales" (HU-074) un panel de filtros y un control de orden. Los criterios de filtro son los mismos de la exploración (entidad, proveedor, modalidad, fechas, UNSPSC, departamento/municipio, rango de valor y fuente), aplicados a los datos del contrato u orden al que pertenece el ítem de cada señal. El criterio "existencia de señal" no aplica porque todas las filas son señales. El orden configurable reemplaza la prioridad por defecto; el Analista puede volver a ella con la opción "Prioridad (por defecto)".

Para que esta HU sea auto-contenida, las reglas de cada criterio se describen completas aquí. Por protección de datos personales (Ley 1581 de 2012, decisión PO 2026-10-05), el documento de un proveedor **persona natural** nunca se muestra ni se puede buscar: ese proveedor se encuentra solo por su nombre y se presenta con la leyenda "Persona natural — documento no visible" (RN-16).

El recorrido típico: el Analista filtra por un departamento y por los últimos 12 meses, ordena por desviación y abre la primera señal.

---

## Criterios de Aceptación

### Escenario 1: Filtrar por departamento y últimos 12 meses, y ordenar por desviación (happy path)

- **Dado** que el Analista está en la lista de señales
- **Cuando** marca el departamento "Santander", elige "Últimos 12 meses" y ordena por "Desviación — Mayor a menor"
- **Entonces** la lista muestra solo las señales de compras de entidades de Santander con fecha de compra en los últimos 12 meses, de la mayor a la menor desviación, con las etiquetas "Departamento: Santander" y "Fechas: Últimos 12 meses ({desde} – {hasta})", en la página 1

### Escenario 2: Filtrar por entidad, proveedor o modalidad

- **Dado** que el Analista está en la lista de señales
- **Cuando** escribe al menos 3 caracteres del nombre o NIT en "Entidad" o "Proveedor" y elige una sugerencia, o marca una modalidad
- **Entonces** la lista muestra solo las señales de los contratos u órdenes que cumplen el criterio, con su etiqueta

### Escenario 3: Filtrar por rango de valor y UNSPSC

- **Dado** que el Analista está en la lista de señales
- **Cuando** aplica un valor mínimo/máximo del contrato u orden o agrega un código UNSPSC de 8 dígitos
- **Entonces** la lista muestra solo las señales que cumplen el criterio; con UNSPSC activo se muestra la nota "Los registros de la TVEC no publican código UNSPSC y no aparecen cuando este filtro está activo."

### Escenario 4: Filtrar por fuente

- **Dado** que "SECOP II" y "TVEC" están marcadas por defecto
- **Cuando** el Analista desmarca una de ellas
- **Entonces** la lista muestra solo las señales de la fuente marcada; no se permite desmarcar la última ("Debe quedar al menos una fuente seleccionada.")

### Escenario 5: Validaciones de los filtros

- **Dado** que el Analista ingresa un dato inválido (fecha inicial posterior a la final, fecha inexistente o futura, valor mínimo mayor que el máximo, valor no entero o de más de 12 dígitos, UNSPSC que no tiene 8 dígitos, texto de entidad/proveedor sin elegir sugerencia)
- **Cuando** intenta aplicarlo
- **Entonces** el filtro no se aplica, la lista no cambia y se muestra el mensaje correspondiente de RN-10

### Escenario 6: Ordenar por valor, fecha o confianza

- **Dado** que el Analista está en la lista de señales
- **Cuando** elige "Valor", "Fecha" o "Nivel de confianza" y un sentido
- **Entonces** la lista se ordena por precio unitario contratado, fecha de compra o nivel de confianza (Alta > Media > Baja) en el sentido elegido, con desempate por fecha más reciente y luego por identificador

### Escenario 7: Volver a la prioridad por defecto

- **Dado** que el Analista eligió un orden distinto
- **Cuando** elige "Prioridad (por defecto)"
- **Entonces** la lista vuelve a ordenarse por confianza descendente, luego desviación descendente, luego fecha más reciente, luego identificador

### Escenario 8: Sin señales para los filtros

- **Dado** que ninguna señal cumple los filtros aplicados
- **Cuando** la lista se actualiza
- **Entonces** se muestra "No hay señales que merezcan revisión con los filtros aplicados." con el botón "Limpiar filtros", y el conteo "0 señales"

### Escenario 9: Quitar o limpiar filtros

- **Dado** que hay filtros aplicados
- **Cuando** el Analista quita una etiqueta o usa "Limpiar filtros"
- **Entonces** la lista se recalcula, vuelve a la página 1 y el orden elegido se conserva

### Escenario 10: Persistencia de filtros y orden

- **Dado** que el Analista aplicó filtros y un orden
- **Cuando** recarga la página, abre una señal o una ficha y vuelve, o comparte la URL con otra sesión activa
- **Entonces** la lista se muestra con los mismos filtros, orden y página

### Escenario 11: Proveedor persona natural buscado por nombre

- **Dado** que hay señales de un contrato cuyo proveedor es "María Fernanda Ríos Peña" con tipo de documento "Cédula de Ciudadanía"
- **Cuando** el Analista escribe "fernanda rios" en "Proveedor" y elige la sugerencia
- **Entonces** la sugerencia se muestra como "María Fernanda Ríos Peña — Persona natural — documento no visible", la lista muestra solo esas señales con la etiqueta "Proveedor: María Fernanda Ríos Peña" y el número de documento no aparece en sugerencias, etiquetas, lista ni URL

### Escenario 12: Escribir el número de documento de un proveedor persona natural o sin tipo

- **Dado** que hay señales de proveedores persona natural y de proveedores con documento publicado pero tipo vacío o desconocido
- **Cuando** el Analista escribe el número de documento de alguno de ellos, completo o como prefijo, en "Proveedor"
- **Entonces** ese proveedor no se sugiere por coincidencia de documento, el número no se revela y, si ningún NIT de persona jurídica ni nombre coincide, se muestra "No hay proveedores con ese nombre o NIT entre las señales vigentes." y la lista no cambia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador puede usar los mismos controles.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Permite que cada analista priorice las señales según su foco (territorio, período, actor) sin recorrer toda la lista.

### Reglas de Negocio

- **RN-01 Evaluación de filtros:** todos los criterios se evalúan sobre el contrato u orden al que pertenece el ítem de la señal. Y entre criterios distintos; O entre valores del mismo criterio; cada cambio vuelve a la página 1.
- **RN-02 Entidad y proveedor:** búsqueda desde 3 caracteres distintos de espacio (máximo 100), por nombre (coincidencia parcial sin distinguir mayúsculas ni tildes) o por NIT (solo dígitos, por prefijo, ignorando puntos, guiones y dígito de verificación separado por guion); en "Proveedor" la búsqueda por número solo aplica a proveedores persona jurídica (RN-16). Formato de sugerencia: "{Nombre} — NIT {número}" para entidades y proveedores persona jurídica, "{Nombre} — Persona natural — documento no visible" para proveedores persona natural; sin número publicado, solo el nombre. Sin coincidencias: "No hay entidades con ese nombre o NIT entre las señales vigentes." o "No hay proveedores con ese nombre o NIT entre las señales vigentes.". Hasta 10 sugerencias, solo de actores con señales vigentes, ordenadas por número de señales y luego por nombre. Se aplica solo al elegir una sugerencia; máximo 10 valores por filtro. Origen SECOP II: `nombre_entidad`/`nit_entidad` y `proveedor_adjudicado`/`documento_proveedor`/`tipodocproveedor`; TVEC: datos de la orden.
- **RN-03 Modalidad:** casillas con las modalidades presentes entre las señales vigentes y su número de señales; órdenes TVEC sin modalidad → "Tienda Virtual del Estado (TVEC)"; contratos sin modalidad → "Sin modalidad registrada".
- **RN-04 Fechas:** fecha de compra (fecha de firma SECOP II; fecha de la orden TVEC), formato `DD/MM/AAAA`, rango inclusivo, "Hasta" ≤ hoy, se puede usar solo un extremo. Rangos predefinidos: "Últimos 30 días" (hoy − 29 días a hoy), "Últimos 6 meses" y "Últimos 12 meses" (hoy − N meses + 1 día a hoy) y "Año en curso" (01/01 a hoy), recalculados cada día.
- **RN-05 Valor:** valor del contrato (`valor_del_contrato` de SECOP II) o valor total de la orden TVEC, publicado en datos abiertos y usado solo como dato de referencia del contrato; enteros ≥ 0, máximo 12 dígitos, rango inclusivo.
- **RN-06 UNSPSC:** 8 dígitos (se acepta el prefijo "V1."), comparado con el código de categoría principal SECOP II; hasta 5 códigos combinados con O; las órdenes TVEC no tienen UNSPSC y quedan fuera con el filtro activo.
- **RN-07 Territorio:** departamento y municipio de la entidad compradora publicados por la fuente, agrupados sin distinguir mayúsculas, tildes ni puntuación; municipio identificado como "municipio (departamento)" y habilitado solo con departamentos elegidos; si hay municipios elegidos, se incluyen esos municipios y los departamentos elegidos sin municipios elegidos; opción "Sin información territorial" para registros sin departamento.
- **RN-08 Fuente:** "SECOP II" y "TVEC" marcadas por defecto; al menos una debe quedar marcada.
- **RN-09 Nulos:** con un filtro activo, se excluyen las señales cuyo contrato u orden no tiene el dato del criterio.
- **RN-10 Mensajes de validación:** "Escribe al menos 3 caracteres del nombre o del NIT."; "Selecciona una opción de la lista de sugerencias."; "Puedes seleccionar hasta 10 valores en este filtro."; "La fecha inicial no puede ser posterior a la fecha final."; "Ingresa una fecha válida con formato DD/MM/AAAA."; "La fecha no puede ser posterior a hoy."; "El valor mínimo no puede ser mayor que el valor máximo."; "Ingresa un valor en pesos, solo con números enteros (máximo 12 dígitos)."; "Ingresa un código UNSPSC de 8 dígitos (ej. 52161505)."; "Puedes agregar hasta 5 códigos UNSPSC."; "Debe quedar al menos una fuente seleccionada."
- **RN-11 Orden:** opciones "Prioridad (por defecto)", "Desviación", "Valor" (precio unitario contratado del ítem), "Fecha" y "Nivel de confianza" (Alta > Media > Baja). Sentidos: "Mayor a menor"/"Menor a mayor" (o "Más reciente primero"/"Más antigua primero" para fecha). Desempate: fecha más reciente, luego identificador del contrato u orden ascendente. Las señales sin el dato del criterio quedan al final. La prioridad por defecto es: confianza descendente, desviación descendente, fecha más reciente, identificador ascendente.
- **RN-12 Persistencia:** filtros, orden, tamaño de página y página en la URL; valores inválidos se reemplazan por los valores por defecto sin error. Un proveedor persona natural se representa en la URL con un identificador interno que no contiene su número de documento.
- **RN-13 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-14 Tiempo de respuesta:** aplicar filtros u orden responde en ≤ 3 segundos (p95) con el volumen del MVP y 20 usuarios concurrentes (objetivo inicial de diseño, configurable y recalibrable).
- **RN-15 Accesibilidad y responsive (valores iniciales de diseño):** WCAG 2.1 AA (teclado, foco visible, etiquetas, mensajes anunciados); en anchos menores a 1366 px el panel se pliega detrás del botón "Filtros ({n})" sin perder criterios.
- **RN-16 Visibilidad del documento del proveedor (decisión PO 2026-10-05, Ley 1581 de 2012):** el tipo se toma de `tipodocproveedor`. Si es NIT (persona jurídica), el NIT se muestra y es buscable (RN-02). Si es cédula de ciudadanía, cédula de extranjería, pasaporte o cualquier otro tipo distinto de NIT, o si el tipo está vacío o es desconocido (se trata como persona natural por seguridad), el número de documento nunca se muestra en sugerencias, etiquetas, lista, URL ni mensajes, no se compara con el texto escrito y no permite filtrar; en su lugar se muestra "Persona natural — documento no visible". El nombre del proveedor sigue visible y buscable. El valor almacenado solo es accesible al Administrador por medios técnicos o administrativos, fuera de esta interfaz.

### Interfaz

- Panel de filtros de la vista "Señales" con las secciones Entidad, Proveedor, Modalidad, Fechas de compra (con rangos predefinidos), Valor del contrato u orden, UNSPSC, Territorio y Fuente, y el botón "Limpiar filtros".
- Etiquetas de filtros aplicados sobre la lista con botón "Quitar".
- Control "Ordenar por" con las opciones de RN-11 y selector de sentido; encabezados ordenables con indicador de orden.
- Estado "sin señales para los filtros" con "Limpiar filtros".

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa las señales vigentes calculadas por la plataforma y los datos de contrato u orden ingeridos de SECOP II (`jbjy-vk9h`) y TVEC.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-074 (lista priorizada de señales), HU-070, HU-071, HU-072, HU-073 (mismos criterios en la exploración)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-01):** en la lista de señales, los filtros de FR-071 se evalúan con el contrato u orden del ítem de la señal; el filtro "existencia de señal" no aplica.
- **Resuelto (RN-11):** "Valor" en la lista de señales es el precio unitario contratado del ítem.
- **Resuelto (RN-16):** el documento del proveedor persona natural (tipo distinto de NIT, vacío o desconocido) no se muestra ni es buscable; decisión PO 2026-10-05 (Ley 1581).

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
