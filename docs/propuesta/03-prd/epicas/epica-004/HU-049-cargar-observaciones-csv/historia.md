# Historia #049: Cargar observaciones de precio de forma semiautomática con un archivo CSV

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Cargar Observaciones Manual y Semiautomáticamente  
**Prioridad:** Crítica  
**FRs relacionados:** FR-052, FR-049, FR-050

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** cargar muchas observaciones de precio a la vez mediante un archivo CSV con sus evidencias, validado campo a campo,  
**Para** alimentar el Benchmark 2 con decenas o cientos de referencias manuales sin registrarlas una por una, conservando la misma trazabilidad que la carga individual.

## Descripción

La Adenda 2 acepta cargar a mano "50, 100 o N referencias" como mecanismo temporal del MVP. Esta HU implementa la **carga semiautomática por archivo**: el Administrador entrega un **paquete .zip** con un archivo CSV (una fila por observación) y los archivos de evidencia referenciados. El sistema valida el paquete, valida cada fila campo a campo con las mismas reglas del registro mínimo, guarda las filas válidas como observaciones manuales (`metodo_adquisicion = manual`, `canal_carga = archivo`) y entrega un **reporte de resultado** con cada error identificado por fila y columna.

Opcionalmente, varias filas pueden agruparse en una **búsqueda** (columnas `grupo_busqueda` y `terminos_busqueda`) para cumplir el protocolo contra el sesgo de selección; un grupo se acepta completo o se rechaza completo.

Criterio de la épica: una carga CSV de prueba con 100 observaciones se procesa con validación campo a campo.

---

## Criterios de Aceptación

### Escenario 1: Carga de 100 observaciones válidas

- **Dado** que el Administrador prepara un paquete .zip con un CSV de 100 filas válidas y sus 100 capturas de evidencia
- **Cuando** carga el paquete
- **Entonces** el sistema crea un lote con `id_lote`, crea 100 observaciones con `metodo_adquisicion = manual`, `canal_carga = archivo`, `id_contexto = id_lote`, `registrado_por` = el Administrador y `etiqueta_origen = "Observación manual"`, y devuelve el reporte `"Lote {id_lote}: 100 filas leídas, 100 aceptadas, 0 rechazadas."`

### Escenario 2: Carga con filas inválidas

- **Dado** que el CSV tiene 100 filas, de las cuales la fila 7 tiene precio "1.899.900", la fila 15 no tiene marca y la fila 40 referencia una evidencia que no está en el paquete
- **Cuando** el Administrador carga el paquete
- **Entonces** se guardan las 97 filas válidas, se rechazan las 3 inválidas y el reporte lista por cada error la fila, la columna, el valor recibido y el mensaje (ej. `Fila 8 | precio_efectivo | 1.899.900 | precio_efectivo debe ser un entero entre 1 y 999.999.999 COP.`), con resumen `"Lote {id_lote}: 100 filas leídas, 97 aceptadas, 3 rechazadas."`

### Escenario 3: Paquete inválido

- **Dado** que el Administrador carga un archivo que no es .zip, un .zip sin CSV, un .zip con dos CSV, un CSV vacío (solo encabezado) o un CSV con más de 1.000 filas
- **Cuando** el sistema valida el paquete
- **Entonces** no se procesa ninguna fila, no se crea lote y se devuelve, según el caso: `"El paquete debe ser un archivo .zip."`, `"El paquete debe contener exactamente un archivo .csv."`, `"El archivo CSV no tiene filas de datos."` o `"El archivo CSV supera el máximo de 1.000 filas."`

### Escenario 4: Encabezado inválido

- **Dado** que el CSV no tiene la columna obligatoria `precio_efectivo` o tiene una columna desconocida `precio_oferta`
- **Cuando** el sistema valida el encabezado
- **Entonces** no se procesa ninguna fila y se devuelve `"Falta la columna obligatoria: precio_efectivo."` o `"Columna no reconocida: precio_oferta."`

### Escenario 5: Codificación inválida

- **Dado** que el CSV está guardado en una codificación distinta de UTF-8 (ej. Windows-1252 con tildes)
- **Cuando** el sistema lo lee
- **Entonces** no se procesa ninguna fila y se devuelve `"El archivo CSV debe estar codificado en UTF-8."`

### Escenario 6: Grupo de búsqueda completo

- **Dado** que las filas 2 a 5 tienen `grupo_busqueda = G1`, la misma fuente, la misma fecha y `terminos_busqueda = "televisor lg 65|65UT8050"`, y el Administrador confirma la declaración de completitud de los grupos al cargar
- **Cuando** las 4 filas son válidas
- **Entonces** se crean 4 observaciones con `protocolo_busqueda = registrado`, vinculadas a una búsqueda del lote con esos términos

### Escenario 7: Grupo de búsqueda con una fila inválida

- **Dado** que el grupo G2 tiene 3 filas y una es inválida
- **Cuando** el sistema procesa el lote
- **Entonces** se rechazan las 3 filas del grupo; el reporte muestra el error de la fila inválida y, para las otras dos, `"Fila rechazada porque su grupo de búsqueda G2 tiene errores."`

### Escenario 8: Grupo inconsistente o sin declaración

- **Dado** que las filas de un grupo tienen distinta fuente, distinta fecha o distintos términos, o que el paquete tiene grupos y el Administrador no confirmó la declaración de completitud
- **Cuando** el sistema procesa el lote
- **Entonces** se rechazan las filas del grupo con `"Las filas del grupo {grupo} deben tener la misma fuente, fecha_observacion y terminos_busqueda."`, o se rechaza el paquete completo con `"Confirme que cada grupo de búsqueda incluye todas las ofertas comparables encontradas."`

### Escenario 9: Paquete ya cargado

- **Dado** que un paquete con el mismo hash SHA-256 se cargó antes con éxito
- **Cuando** el Administrador lo carga de nuevo
- **Entonces** no se crea lote ni observaciones y se devuelve `"Este paquete ya fue cargado el {fecha} (lote {id_lote})."`

### Escenario 10: URL repetida dentro del lote

- **Dado** que las filas 10 y 25 tienen la misma URL
- **Cuando** se procesa el lote
- **Entonces** la fila 10 se acepta (si es válida) y la fila 25 se rechaza con `"Observación duplicada en el contexto {id_lote}: {url}."`

### Escenario 11: Ninguna fila válida

- **Dado** que todas las filas del CSV son inválidas
- **Cuando** se procesa el lote
- **Entonces** el lote queda registrado con 0 aceptadas y el reporte completo de errores, sin crear observaciones

### Escenario 12: Usuario sin rol Administrador

- **Dado** que un Analista intenta cargar un paquete
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador autenticado.
- **Valor de negocio:** reduce el tiempo humano de la carga manual (factor crítico de la épica) sin perder trazabilidad.

### Reglas de Negocio

**RN-01 — Paquete.** Archivo .zip de máximo 100 MB (configurable) con exactamente un archivo .csv (en cualquier carpeta del paquete) y los archivos de evidencia. Se registra el hash SHA-256 del paquete. Mensajes: `"El paquete debe ser un archivo .zip."`, `"El paquete debe contener exactamente un archivo .csv."`, `"El paquete supera el tamaño máximo de 100 MB."`, `"El paquete está dañado y no se puede abrir."`

**RN-02 — Formato del CSV.** Codificación UTF-8 (con o sin BOM); separador coma; campos con comas, comillas o saltos de línea entre comillas dobles (RFC 4180); primera fila = encabezado; nombres de columna sin distinguir mayúsculas y en cualquier orden; de 1 a 1.000 filas de datos (configurable). Las filas completamente vacías se ignoran. La numeración de filas del reporte cuenta el encabezado como fila 1. Mensajes: `"El archivo CSV debe estar codificado en UTF-8."`, `"El archivo CSV no tiene filas de datos."`, `"El archivo CSV supera el máximo de 1.000 filas."`, `"Falta la columna obligatoria: {columna}."`, `"Columna no reconocida: {columna}."`, `"La fila {n} tiene un número de columnas distinto al encabezado."` (esta última rechaza solo la fila).

**RN-03 — Columnas.**

| Columna | Obligatoria | Formato |
|---|---|---|
| `fuente` | Sí | Fuente del catálogo con carga manual habilitada |
| `producto_descripcion` | Sí | 3 a 300 caracteres |
| `marca` | Sí | 1 a 60 caracteres |
| `modelo_referencia` | Sí | 2 a 60 caracteres |
| `sku` | No (columna opcional) | 1 a 64 caracteres |
| `ean_gtin` | No (columna opcional) | 8, 12, 13 o 14 dígitos con dígito de control válido |
| `tamano_pulgadas` | No (columna opcional) | 10 a 120, punto como separador decimal, máximo 1 decimal |
| `resolucion` | No (columna opcional) | HD, Full HD, 4K UHD, 8K, desconocida |
| `tecnologia_pantalla` | No (columna opcional) | LED, QLED, OLED, Mini LED, otra, desconocida |
| `smart` | No (columna opcional) | sí, no, desconocido |
| `vendedor` | Sí | 1 a 100 caracteres; vendedor aceptado de la fuente |
| `precio_efectivo` | Sí | Solo dígitos, entero de 1 a 999.999.999 (sin puntos, comas, espacios ni "$") |
| `precio_anterior` | No (columna opcional) | Solo dígitos, mayor que `precio_efectivo` |
| `condicion_especial` | Sí | ninguna, tarjeta_especifica, cupon, financiacion, membresia, otra |
| `condicion_especial_detalle` | Si condición ≠ ninguna | 3 a 300 caracteres |
| `tipo_referencia` | Sí | url, texto |
| `referencia_origen` | Sí | URL http/https ≤ 2.048 caracteres, o texto de 5 a 300 caracteres |
| `fecha_observacion` | Sí | `AAAA-MM-DD HH:MM` o ISO 8601, hora de Colombia; no futura respecto al momento de carga; antigüedad máxima de la carga manual (inicial: 7 días, configurable) |
| `iva_condicion` | Sí | incluido, no_incluido, indeterminado |
| `archivos_evidencia` | Sí | 1 a 5 rutas de archivos dentro del paquete separadas por `\|`; PNG, JPG/JPEG o PDF de máximo 10 MB cada uno |
| `precio_por_unidad` | Sí | Debe ser `sí` (el precio corresponde a una unidad, sin combos ni accesorios) |
| `grupo_busqueda` | No (columna opcional) | 1 a 40 caracteres (letras, dígitos, guion, guion bajo) |
| `terminos_busqueda` | Si hay `grupo_busqueda` | 1 a 10 términos separados por `\|`, cada uno de 2 a 200 caracteres |

Las columnas obligatorias deben existir en el encabezado; las opcionales pueden omitirse. Una celda vacía en columna opcional se guarda como nula.

**RN-04 — Validación por fila.** Cada fila se valida campo a campo con los mensajes del registro mínimo de la base (ej. `"Campo obligatorio ausente: {campo}."`, `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."`, `"ean_gtin no es un GTIN válido."`, `"El precio anterior debe ser mayor que el precio efectivo."`, `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda {fuente}. Vendedor recibido: {vendedor}."`, `"La fecha de observación no puede ser futura."`, `"La fecha de observación no puede tener más de {N} días de antigüedad."`) más: `"Archivo de evidencia no encontrado en el paquete: {ruta}."`, `"Formato de evidencia no permitido: use PNG, JPG o PDF."`, `"La evidencia supera el tamaño máximo de 10 MB."`, `"Se admiten máximo 5 evidencias por observación."`, `"precio_por_unidad debe ser sí."` y `"terminos_busqueda es obligatorio cuando hay grupo_busqueda."` Se reportan todos los errores de la fila, no solo el primero. Una fila con cualquier error se rechaza completa; las filas válidas sin grupo se guardan.

**RN-05 — Grupos de búsqueda.** Las filas con el mismo `grupo_busqueda` forman una búsqueda del lote. Todas deben tener la misma `fuente`, `fecha_observacion` y `terminos_busqueda`; si no: todas las filas del grupo se rechazan con `"Las filas del grupo {grupo} deben tener la misma fuente, fecha_observacion y terminos_busqueda."` Si una fila del grupo es inválida, se rechazan todas, y las válidas con `"Fila rechazada porque su grupo de búsqueda {grupo} tiene errores."` Si el paquete contiene al menos un grupo, la operación de carga exige la declaración "Cada grupo de búsqueda incluye todas las ofertas comparables encontradas, no solo la de mayor o menor precio"; sin ella el paquete se rechaza con `"Confirme que cada grupo de búsqueda incluye todas las ofertas comparables encontradas."` Observaciones de un grupo: `protocolo_busqueda = registrado` y vínculo a la búsqueda del lote (identificador `{id_lote}-{grupo}`, con sus términos). Filas sin grupo: `protocolo_busqueda = no_registrado`.

**RN-06 — Evidencias.** Una misma evidencia puede ser referenciada por varias filas. Cada evidencia se guarda como copia con su hash SHA-256. Archivos del paquete no referenciados por ninguna fila no se guardan y se informan como advertencia `"Archivo de evidencia no referenciado: {ruta}."`

**RN-07 — Duplicados.** Paquete con el mismo hash que uno cargado con al menos una fila aceptada: `"Este paquete ya fue cargado el {fecha} (lote {id_lote})."` (se puede volver a cargar un paquete cuyo lote anterior tuvo 0 filas aceptadas). Dentro del lote, la segunda fila con la misma URL se rechaza con `"Observación duplicada en el contexto {id_lote}: {url}."`

**RN-08 — Lote y reporte.** El lote registra `id_lote`, nombre y hash del paquete, `cargado_por` (usuario autenticado), fecha y hora, filas leídas, aceptadas y rechazadas. El reporte (consultable por `id_lote` y descargable como CSV con columnas `fila, columna, valor, mensaje`) contiene un renglón por error y las advertencias. Resumen: `"Lote {id_lote}: {leídas} filas leídas, {aceptadas} aceptadas, {rechazadas} rechazadas."` El valor de una celda mostrado en el reporte se trunca a 100 caracteres.

**RN-09 — Campos asignados (FR-049, FR-050).** Cada observación: `metodo_adquisicion = manual`, `canal_carga = archivo`, `id_contexto = id_lote`, `registrado_por` = usuario que carga el paquete, `fecha_registro`, `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `estado = vigente`, `apta_para_referencia` (sí solo si condición = ninguna), `vendedor_es_tienda = sí`.

**RN-10 — Evento auditable.** Cada lote genera el evento `carga_manual_archivo` con usuario, fecha y hora, `id_lote` y conteos.

**RN-11 — Tiempo de procesamiento.** El procesamiento de un paquete de 1.000 filas no bloquea al Administrador: si toma más de 30 segundos, la operación devuelve `"Lote {id_lote} en proceso."` y el reporte queda disponible al terminar.

### Interfaz

Puede implementarse como carga en una interfaz administrativa mínima o como comando/script que recibe la ruta del paquete y la declaración de grupos (nota del Dominio 12 del PRD). Debe existir una plantilla CSV descargable o documentada con el encabezado exacto de RN-03 y una fila de ejemplo.

### Sistemas Externos (Si aplica)

No hay integración: el archivo lo prepara el Administrador.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (base y registro mínimo), HU-043 (duplicados en contexto, anulación), HU-044, HU-045, HU-046 (reglas de precio), HU-047 (carga individual), HU-048 (búsqueda manual).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Evidencia en la carga por archivo:** como el registro mínimo incluye evidencia, el CSV se entrega en un paquete .zip con los archivos referenciados por fila. Resuelta (RN-01, RN-03).
2. **Aceptación parcial por fila** con reporte de errores, salvo en grupos de búsqueda, que son todo o nada. Resuelta (RN-04, RN-05).
3. **Formato CSV:** UTF-8, coma, RFC 4180, precios enteros sin separadores, máximo 1.000 filas y 100 MB (configurables). Resuelta (RN-01 a RN-03).
4. **Canal archivo = método manual:** la carga semiautomática se identifica como observación manual con `canal_carga = archivo`. Resuelta (RN-09).
5. **Procesamiento asíncrono** a partir de 30 segundos. Resuelta (RN-11).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-004 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
