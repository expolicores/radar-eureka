# Historia #031: Normalizar marca, tamaño y resolución al esquema común

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Normalizar Atributos al Esquema Común  
**Prioridad:** Crítica  
**FRs relacionados:** FR-035

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada televisor de SECOP II, TVEC o retail quede registrado en un esquema común con su marca, tamaño en pulgadas y resolución normalizados,  
**Para** que televisores descritos de formas distintas ("65 pulgadas, 4K", "GSF01-TELEVISOR SAMSUNG … 55\"", el nombre comercial de Alkosto) puedan compararse con criterios homogéneos y trazables.

## Descripción

Las tres fuentes describen el mismo tipo de bien de forma heterogénea: los ítems extraídos de documentos de SECOP II traen campos con texto libre ("Samsung", "65 pulg."), la TVEC solo trae un texto de descripción sin normalizar (mayúsculas, prefijos como `GSF01-`, códigos internos) y las observaciones retail traen nombre comercial, marca y, a veces, características.

Esta HU crea el **registro de producto normalizado** (esquema común de FR-035) para cada registro de origen y llena tres de sus atributos: **marca**, **tamaño en pulgadas** y **resolución**. Los demás atributos del esquema (tecnología, Smart, generación, modelo normalizado y EAN) se llenan con las reglas de otras HUs de esta épica; mientras no se procesen, quedan nulos con motivo `NO_PROCESADO`.

La normalización es **determinística** (reglas y tablas configurables, sin IA), conserva siempre el valor original y nunca inventa un valor: ante ausencia o ambigüedad deja el atributo nulo con un motivo explícito. Es un proceso de backend sin interfaz gráfica; los resultados se consultan por consulta a la base o por los servicios que los usen.

---

## Criterios de Aceptación

### Escenario 1: Normalización de un ítem TVEC desde su texto de descripción

- **Dado** que existe un ítem TVEC con clasificación "incluido" y descripción `GSF01-TELEVISOR SAMSUNG FLAT LED CRYSTAL UHD SMART TV 55"`
- **Cuando** se ejecuta la normalización
- **Entonces** se crea un único producto normalizado con `tipo_origen = TVEC`, el identificador del ítem TVEC, `categoria = televisor`, `marca = SAMSUNG`, `tamano_pulgadas = 55` y `resolucion = 4K`
- **Y** cada uno de los tres atributos guarda su valor original (`SAMSUNG`, `55"`, `CRYSTAL UHD`), el campo de origen (`descripcion_tvec`) y el identificador de la regla aplicada
- **Y** el prefijo `GSF01-` no forma parte de ningún valor normalizado, pero el texto original del ítem se conserva sin cambios

### Escenario 2: Normalización de un ítem SECOP II desde campos extraídos

- **Dado** que existe un ítem de televisor SECOP II con clasificación "incluido" y campos extraídos `marca = "lg"`, `tamaño = "65 pulg."` y `resolución = "Ultra HD 3840 x 2160"`
- **Cuando** se ejecuta la normalización
- **Entonces** el producto normalizado queda con `marca = LG`, `tamano_pulgadas = 65` y `resolucion = 4K`, con `campo_origen` igual al campo extraído correspondiente

### Escenario 3: Campo de marca estructurado con una marca no catalogada

- **Dado** que una observación retail trae en su campo estructurado de marca el valor `Exclusiv`, que no está en la tabla de alias de marcas
- **Cuando** se ejecuta la normalización
- **Entonces** `marca = EXCLUSIV` con el indicador `marca_no_catalogada = sí`

### Escenario 4: Marca no reconocida en texto libre

- **Dado** que un ítem TVEC tiene la descripción `TELEVISOR LED 43 PULGADAS FULL HD` y ninguna palabra coincide con la tabla de alias de marcas
- **Cuando** se ejecuta la normalización
- **Entonces** `marca` queda nula con motivo `MARCA_NO_RECONOCIDA`, `tamano_pulgadas = 43` y `resolucion = FHD`

### Escenario 5: Marca de referencia del pliego ("o equivalente")

- **Dado** que un ítem SECOP II tiene como marca extraída el texto `Samsung o equivalente`
- **Cuando** se ejecuta la normalización
- **Entonces** `marca` queda nula con motivo `MARCA_REFERENCIAL` y el valor original se conserva

### Escenario 6: Varias marcas distintas en el texto

- **Dado** que una descripción contiene `TELEVISOR SAMSUNG O LG 50"`
- **Cuando** se ejecuta la normalización
- **Entonces** `marca` queda nula con motivo `MARCA_AMBIGUA`

### Escenario 7: Tamaño con decimales o en centímetros

- **Dado** que una descripción contiene `54,6"` y otra contiene `TV 139 CM` sin ningún valor en pulgadas
- **Cuando** se ejecuta la normalización
- **Entonces** la primera queda con `tamano_pulgadas = 55` y la segunda con `tamano_pulgadas = 55` (139 / 2,54 = 54,72 → 55), con la regla de conversión registrada

### Escenario 8: Tamaño ambiguo

- **Dado** que una descripción contiene dos tamaños nominales distintos, `TELEVISOR 50" Y 55" SMART`
- **Cuando** se ejecuta la normalización
- **Entonces** `tamano_pulgadas` queda nulo con motivo `TAMANO_AMBIGUO`

### Escenario 9: Tamaño fuera del rango configurado

- **Dado** que el rango válido configurado es 10 a 120 pulgadas y una descripción contiene `TELEVISOR 8"` o `TELEVISOR 150"`
- **Cuando** se ejecuta la normalización
- **Entonces** `tamano_pulgadas` queda nulo con motivo `TAMANO_FUERA_DE_RANGO`

### Escenario 10: Resolución ambigua o ausente

- **Dado** que una descripción contiene `FULL HD 4K` (dos resoluciones distintas) y otra no contiene ningún término de resolución
- **Cuando** se ejecuta la normalización
- **Entonces** la primera queda con `resolucion` nula y motivo `RESOLUCION_AMBIGUA`, y la segunda con `resolucion` nula y motivo `RESOLUCION_NO_ENCONTRADA`

### Escenario 11: Conflicto entre campo estructurado y texto libre

- **Dado** que una observación retail trae el campo estructurado `tamaño = 50` y su nombre comercial dice `Televisor 55"`
- **Cuando** se ejecuta la normalización
- **Entonces** `tamano_pulgadas = 50` (prevalece el campo estructurado), `conflicto_origen = sí` para ese atributo y se registran ambos valores originales

### Escenario 12: Registro sin atributos mínimos

- **Dado** que un ítem TVEC "incluido" tiene la descripción `TELEVISOR` sin marca, tamaño, resolución ni código de modelo
- **Cuando** se ejecuta la normalización
- **Entonces** se crea el producto normalizado con los atributos nulos y sus motivos, y `estado_normalizacion = SIN_ATRIBUTOS_MINIMOS`

### Escenario 13: Registros que no se normalizan y registros que dejan de ser televisores

- **Dado** que existe un ítem con clasificación "excluido" o "requiere revisión", y otro ítem ya normalizado cuya clasificación cambia de "incluido" a "excluido"
- **Cuando** se ejecuta la normalización
- **Entonces** el primero no genera producto normalizado
- **Y** el producto normalizado del segundo pasa a `activo = no`, con fecha y motivo `ORIGEN_NO_INCLUIDO`, sin borrarse

### Escenario 14: Reejecución sin cambios y cambio del dato de origen

- **Dado** que un registro de origen ya tiene producto normalizado
- **Cuando** la normalización se ejecuta otra vez sin cambios en el origen ni en las reglas
- **Entonces** no se crea un segundo producto normalizado ni una nueva versión
- **Y cuando** el dato de origen cambia (ej. el Revisor corrige el tamaño extraído de 56 a 65) o cambia la versión de las reglas, **entonces** se genera una nueva versión del producto normalizado, la anterior se conserva como histórica con su fecha y versión de reglas, y solo la nueva queda vigente

### Escenario 15: Cambio de las tablas de configuración

- **Dado** que el Administrador agrega el alias `EXCLUSIV` a la tabla de marcas
- **Cuando** guarda el cambio
- **Entonces** se registra quién lo hizo, cuándo, el valor anterior y el nuevo, se incrementa la versión de reglas y los productos normalizados afectados se recalculan en la siguiente ejecución

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario de los datos normalizados); Administrador (mantiene las tablas de configuración). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** solo el rol Administrador puede modificar tablas y parámetros de normalización. El proceso no requiere intervención del Analista.
- **Valor de negocio:** sin atributos homogéneos no hay emparejamiento ni benchmark confiable; es la base para reducir falsos positivos (riesgo R2).

### Reglas de Negocio

**RN-01 — Registros de entrada.** Se normalizan: (a) ítems de televisor de SECOP II y de la TVEC con clasificación de categoría `incluido`; (b) observaciones de precio retail registradas en la base de observaciones de mercado. Los ítems con clasificación `excluido` o `requiere revisión` no se normalizan. Si un ítem normalizado pasa a una clasificación distinta de `incluido`, su producto normalizado pasa a `activo = no` con motivo `ORIGEN_NO_INCLUIDO` y fecha; nunca se borra. Si vuelve a `incluido`, se reactiva con una nueva normalización.

**RN-02 — Esquema común (registro de producto normalizado).** Un producto normalizado vigente por registro de origen, con los campos:

| Campo | Formato | Nulo permitido |
|---|---|---|
| `id_producto_normalizado` | Identificador único estable | No |
| `tipo_origen` | `SECOP_II` · `TVEC` · `RETAIL` | No |
| `id_origen` | Identificador del registro de origen (ítem SECOP II, ítem TVEC u observación retail) | No |
| `categoria` | Texto; en el MVP siempre `televisor` | No |
| `marca` | Texto en mayúsculas sin tildes | Sí, con motivo |
| `marca_no_catalogada` | sí / no | No (por defecto no) |
| `tamano_pulgadas` | Entero | Sí, con motivo |
| `resolucion` | `HD` · `FHD` · `4K` · `8K` | Sí, con motivo |
| `tecnologia`, `smart`, `generacion`, `modelo_original`, `modelo_normalizado`, `ean` | Definidos en otras HUs de esta épica | Sí; `NO_PROCESADO` hasta que se apliquen sus reglas |
| `estado_normalizacion` | `COMPLETA` · `PARCIAL` · `SIN_ATRIBUTOS_MINIMOS` | No |
| `activo` | sí / no | No |
| `version_reglas` | Entero creciente | No |
| `fecha_normalizacion` | Fecha y hora ISO 8601 (zona America/Bogota) | No |

**RN-03 — Trazabilidad por atributo.** Para `marca`, `tamano_pulgadas` y `resolucion` se guarda: `valor_original` (texto exacto encontrado; nulo si no se encontró), `campo_origen` (ej. `marca_extraida`, `descripcion_tvec`, `nombre_retail`, `marca_retail`), `regla_aplicada` (identificador de la regla, ej. `RN-07-cm`), `motivo_nulo` (cuando el valor es nulo) y `conflicto_origen` (sí/no). Los valores de origen nunca se modifican.

**RN-04 — Origen de cada atributo y prioridad.**
- SECOP II: primero el campo extraído específico (marca, tamaño, resolución); si es nulo, la descripción extraída del ítem.
- TVEC: el texto de descripción del ítem.
- Retail: primero los campos estructurados de la observación (marca, características); si son nulos, el nombre del producto.
- Si el campo específico y el texto libre producen valores normalizados distintos, prevalece el **campo específico** y se marca `conflicto_origen = sí` guardando ambos valores originales.

**RN-05 — Preprocesamiento del texto (solo para buscar; no altera el original).** Convertir a mayúsculas, quitar tildes, reemplazar comillas tipográficas (`”`, `“`) por `"`, colapsar espacios múltiples y eliminar los prefijos de la lista configurable de prefijos de catálogo. **Configuración inicial:** patrón "tres letras + dos dígitos + guion al inicio del texto" (ej. `GSF01-`).

**RN-06 — Marca.**
- Se usa una **tabla configurable de alias → marca canónica**. **Configuración inicial:** SAMSUNG; LG (alias `LG ELECTRONICS`); TCL; KALLEY; CHALLENGER; HISENSE; SONY; PHILIPS; XIAOMI; PANASONIC; JVC; HYUNDAI; AIWA. La tabla es configuración de normalización, no un catálogo maestro de fabricantes ni de productos.
- La coincidencia es por **palabra completa** (ej. `LG` no coincide dentro de `ALGODON`).
- Si el valor viene de un **campo estructurado de marca** (SECOP II extraído o retail) y no está en la tabla, se guarda el texto preprocesado como marca con `marca_no_catalogada = sí`.
- Si el valor viene de **texto libre** y ningún alias coincide → nulo, `MARCA_NO_RECONOCIDA`.
- Si en el texto coinciden dos o más marcas canónicas distintas → nulo, `MARCA_AMBIGUA`.
- Si junto a la marca aparece una expresión de referencia (lista configurable; **configuración inicial:** `O EQUIVALENTE`, `O SIMILAR`, `TIPO`, `REFERENCIA`, `SIMILAR A`) → nulo, `MARCA_REFERENCIAL`.
- Si no hay ningún dato de marca → nulo, `MARCA_NO_ENCONTRADA`.

**RN-07 — Tamaño en pulgadas.**
- Patrón en pulgadas: número entero o decimal (separador `,` o `.`) seguido, con o sin espacio, de `"`, `''`, `PULGADAS`, `PULGADA`, `PULG`, `PULG.`, `IN`, `INCH` o `INCHES`.
- Patrón en centímetros: número seguido de `CM`; solo se usa si no hay ningún valor en pulgadas. Conversión: `cm / 2,54`.
- El valor se lleva a **tamaño nominal entero** con redondeo al entero más cercano (0,5 sube): 54,6 → 55; 64,5 → 65; 42,4 → 42.
- No se infiere el tamaño a partir del código de modelo.
- Campo estructurado numérico (SECOP II extraído o retail): se aplica el mismo redondeo y rango.
- **Rango válido configurable. Configuración inicial: 10 a 120 pulgadas, inclusive.** Fuera del rango → nulo, `TAMANO_FUERA_DE_RANGO`.
- Dos o más tamaños nominales distintos en el mismo origen → nulo, `TAMANO_AMBIGUO`. El mismo tamaño repetido no es ambigüedad.
- Sin coincidencias → nulo, `TAMANO_NO_ENCONTRADO`.

**RN-08 — Resolución.**
- Catálogo cerrado: `HD`, `FHD`, `4K`, `8K`.
- **Tabla configurable de sinónimos. Configuración inicial:** HD ← `HD`, `HD READY`, `1366X768`, `1280X720`, `720P`; FHD ← `FULL HD`, `FHD`, `1920X1080`, `1080P`; 4K ← `4K`, `UHD`, `ULTRA HD`, `CRYSTAL UHD`, `3840X2160`, `2160P`; 8K ← `8K`, `7680X4320`, `4320P`.
- Antes de comparar, se eliminan los espacios alrededor de la `X` en resoluciones numéricas (`3840 x 2160` → `3840X2160`).
- Se evalúan primero los sinónimos más largos (ej. `FULL HD` antes que `HD`; `ULTRA HD` antes que `HD`) y por palabra completa (`HD` no coincide dentro de `UHD`).
- Si coinciden sinónimos de dos resoluciones distintas → nulo, `RESOLUCION_AMBIGUA`. Varios sinónimos de la misma resolución (ej. `4K UHD`) no son ambigüedad.
- Sin coincidencias → nulo, `RESOLUCION_NO_ENCONTRADA`.

**RN-09 — Estado de normalización.** Se calcula sobre los 7 atributos de FR-035 (marca, modelo normalizado, tamaño, resolución, tecnología, Smart, generación):
- `COMPLETA`: los 7 no nulos.
- `PARCIAL`: algún atributo nulo, pero `tamano_pulgadas` no es nulo **o** `marca` y `modelo_normalizado` no son nulos.
- `SIN_ATRIBUTOS_MINIMOS`: en otro caso.
- Un atributo con motivo `NO_PROCESADO` cuenta como nulo.

**RN-10 — Determinismo, idempotencia y versiones.** Con el mismo origen y la misma `version_reglas`, el resultado es idéntico y la reejecución no crea registros ni versiones nuevas. Se genera una nueva versión cuando cambia algún valor de origen usado (incluida una corrección del Revisor) o cuando cambia `version_reglas`. La versión anterior se conserva como histórica (`vigente = no`, fecha de reemplazo); solo una versión está vigente por registro de origen.

**RN-11 — Sin IA.** Esta normalización no usa IA y funciona aunque la extracción con IA esté desactivada.

**RN-12 — Cambios de configuración.** Las tablas de prefijos, alias de marca, expresiones de referencia, sinónimos de resolución y el rango de tamaño solo las modifica el Administrador. Cada cambio registra usuario, fecha y hora, valor anterior y valor nuevo, e incrementa `version_reglas` en 1. Un cambio que deje una tabla vacía o un rango con mínimo mayor que el máximo se rechaza con el mensaje "Configuración inválida: {detalle}" y no se aplica.

**RN-13 — Ejecución.** La normalización se ejecuta para los registros nuevos o modificados desde la última ejecución y para todos los registros activos cuando cambia `version_reglas`. Un error al procesar un registro no detiene el lote: se registra el `id_origen` y el error, y el registro se reintenta en la siguiente ejecución.

### Interfaz

Sin interfaz gráfica. Las tablas de configuración se mantienen por archivo de configuración, parametrización o interfaz administrativa mínima, según defina la arquitectura. Los productos normalizados, sus atributos con trazabilidad y los errores de ejecución se consultan por consulta a la base de datos o por los servicios que los consumen.

### Sistemas Externos (Si aplica)

No consume sistemas externos. Usa como entrada registros ya almacenados por el sistema: ítems SECOP II con campos extraídos, ítems TVEC ingeridos y observaciones retail de la base de observaciones de mercado.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-032 (tecnología, Smart y generación), HU-033 y HU-034 (código de modelo), HU-036 (EAN/GTIN), HU-035 y HU-038 (emparejamientos que usan estos atributos).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-01):** solo se normalizan ítems con clasificación `incluido`; los dudosos esperan la revisión humana.
- **S-02 (Resuelto → RN-06, RN-07, RN-08):** las tablas iniciales de alias de marca, sinónimos de resolución, expresiones de referencia y el rango de tamaño 10–120" son valores iniciales configurables propuestos a partir de D1 y D4, no verdades fijas.
- **S-03 (Resuelto → RN-07):** el tamaño no se infiere del código de modelo, para no introducir errores.
- **S-04 (Resuelto → RN-04):** ante conflicto prevalece el campo estructurado específico sobre el texto libre, con marca de conflicto.
- **S-05 (Resuelto → RN-11):** la normalización es determinística y no usa IA.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-003 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
