# Historia #032: Normalizar tecnología de pantalla, Smart y generación del televisor

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
**Quiero** que cada televisor normalizado indique su tecnología de pantalla, si es Smart y su año o generación aproximada, con un valor nulo explícito cuando no se puede determinar,  
**Para** que la equivalencia técnica entre televisores se base en características homogéneas y no en suposiciones.

## Descripción

Completa el esquema común de FR-035 con tres atributos: **tecnología de pantalla** (`LED`, `QLED`, `MINI_LED`, `OLED`), **Smart** (`SI` / `NO`) y **generación** (año aproximado del modelo). Opera sobre el producto normalizado ya creado para cada registro de origen (ítem SECOP II o TVEC con clasificación "incluido", u observación retail) y usa los mismos campos de origen.

Los textos de origen son heterogéneos ("FLAT LED CRYSTAL UHD SMART TV", "Neo QLED", "Android TV", "no smart"), por lo que la normalización usa tablas de sinónimos configurables, nunca asume un valor por defecto y deja cada atributo nulo con motivo cuando no hay evidencia o hay contradicción. La generación **no** se deduce de la fecha de la compra ni de la fecha de observación.

Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Tecnología, Smart y generación desde la descripción TVEC

- **Dado** que existe un producto normalizado de un ítem TVEC con descripción `GSF01-TELEVISOR SAMSUNG FLAT LED CRYSTAL UHD SMART TV 55" MODELO 2024`
- **Cuando** se ejecuta la normalización de estos atributos
- **Entonces** `tecnologia = LED`, `smart = SI` y `generacion = 2024`, cada uno con su valor original (`FLAT LED` / `CRYSTAL UHD`, `SMART TV`, `MODELO 2024`), campo de origen y regla aplicada

### Escenario 2: Tecnología específica que subsume "LED" genérico

- **Dado** que una observación retail se llama `Televisor Samsung 65" Neo QLED 4K Smart TV pantalla LED`
- **Cuando** se normaliza
- **Entonces** `tecnologia = MINI_LED` (el término `LED` genérico se subsume en la tecnología específica) y `smart = SI`

### Escenario 3: Tecnologías contradictorias

- **Dado** que una descripción contiene `OLED` y `QLED`
- **Cuando** se normaliza
- **Entonces** `tecnologia` queda nula con motivo `TECNOLOGIA_AMBIGUA`

### Escenario 4: Tecnología no encontrada

- **Dado** que una descripción es `TELEVISOR KALLEY 32" HD` sin términos de tecnología
- **Cuando** se normaliza
- **Entonces** `tecnologia` queda nula con motivo `TECNOLOGIA_NO_ENCONTRADA`

### Escenario 5: Televisor explícitamente no Smart

- **Dado** que una descripción es `TELEVISOR CHALLENGER 32" LED NO SMART`
- **Cuando** se normaliza
- **Entonces** `smart = NO` (la negación se evalúa antes que el término `SMART`)

### Escenario 6: Smart contradictorio o ausente

- **Dado** que una descripción contiene `SMART TV` y `SIN SMART`, y otra no contiene ningún término de Smart
- **Cuando** se normalizan
- **Entonces** la primera queda con `smart` nulo y motivo `SMART_AMBIGUO`, y la segunda con `smart` nulo y motivo `SMART_NO_ENCONTRADO` (nunca se asume `NO` por ausencia)

### Escenario 7: Campo extraído de funciones Smart en SECOP II

- **Dado** que un ítem SECOP II tiene el campo extraído de funciones Smart con valor `Sí, Android TV`
- **Cuando** se normaliza
- **Entonces** `smart = SI` con `campo_origen = smart_extraido`

### Escenario 8: Generación por tabla de reglas de código de modelo

- **Dado** que el Administrador cargó la regla {marca `SAMSUNG`, patrón sobre modelo normalizado, año `2024`} y un producto con `marca = SAMSUNG` tiene un `modelo_normalizado` que cumple el patrón y ningún año explícito
- **Cuando** se normaliza
- **Entonces** `generacion = 2024` con `regla_aplicada` igual al identificador de la regla de la tabla

### Escenario 9: Generación sin evidencia

- **Dado** que un producto no tiene año explícito con calificador ni regla de código aplicable
- **Cuando** se normaliza
- **Entonces** `generacion` queda nula con motivo `GENERACION_NO_DETERMINADA`
- **Y** no se usa la fecha de la compra, del contrato ni de la observación para llenarla

### Escenario 10: Año sin calificador, varios años o año fuera de rango

- **Dado** que una descripción contiene `CONTRATO 2023 TELEVISOR 50"` (año sin calificador), otra `MODELO 2022 MODELO 2023` y otra `MODELO 2005`
- **Cuando** se normalizan
- **Entonces** la primera queda con `generacion` nula y motivo `GENERACION_NO_DETERMINADA`; la segunda con `GENERACION_AMBIGUA`; la tercera con `GENERACION_FUERA_DE_RANGO`

### Escenario 11: Conflicto entre año explícito y regla de código

- **Dado** que un producto tiene `MODELO 2023` en el texto y una regla de código que indica `2024`
- **Cuando** se normaliza
- **Entonces** `generacion` queda nula con motivo `GENERACION_EN_CONFLICTO` y se registran ambos valores

### Escenario 12: Recalcular el estado de normalización

- **Dado** que un producto tenía `estado_normalizacion = PARCIAL` y, tras esta normalización, sus 7 atributos del esquema quedan no nulos
- **Cuando** termina el proceso
- **Entonces** `estado_normalizacion = COMPLETA`

### Escenario 13: Cambio de configuración y reejecución

- **Dado** que el Administrador agrega el sinónimo `QNED` a la tecnología `QLED`
- **Cuando** guarda el cambio y se ejecuta la normalización
- **Entonces** se registra el cambio (usuario, fecha y hora, valor anterior y nuevo), se incrementa la versión de reglas y los productos con `QNED` en su origen obtienen una nueva versión con `tecnologia = QLED`
- **Y** una reejecución sin cambios no crea versiones nuevas

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); Administrador (mantiene las tablas). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** solo el Administrador modifica tablas y parámetros.
- **Valor de negocio:** la equivalencia técnica (FR-038) depende de estos atributos; un valor asumido produciría falsos positivos.

### Reglas de Negocio

**RN-01 — Registros de entrada.** Se procesan los productos normalizados vigentes y activos (un producto por registro de origen: ítem SECOP II o TVEC con clasificación `incluido`, u observación retail). Los productos con `activo = no` no se procesan.

**RN-02 — Origen y prioridad.** SECOP II: primero el campo extraído específico (tecnología de pantalla, funciones Smart); si es nulo, la descripción extraída del ítem. TVEC: texto de descripción. Retail: primero campos estructurados (características), luego nombre del producto. Si el campo específico y el texto producen valores distintos, prevalece el campo específico y se marca `conflicto_origen = sí` con ambos valores originales.

**RN-03 — Preprocesamiento (solo para buscar).** Mayúsculas, sin tildes, guiones reemplazados por espacio, espacios colapsados. Los sinónimos se evalúan del más largo al más corto, por palabra completa, y el texto que coincide con un sinónimo no vuelve a usarse para otro (ej. `NEO QLED` no cuenta además como `QLED`). El texto original no se modifica.

**RN-04 — Tecnología de pantalla.**
- Catálogo cerrado: `LED`, `QLED`, `MINI_LED`, `OLED`.
- **Tabla configurable de sinónimos. Configuración inicial:** OLED ← `OLED`, `QD OLED`; MINI_LED ← `MINI LED`, `MINILED`, `NEO QLED`; QLED ← `QLED`; LED ← `LED`, `FLAT LED`, `LCD LED`, `LED LCD`, `CRYSTAL UHD`, `NANOCELL`, `DLED`, `D LED`, `DIRECT LED`.
- Si coinciden `LED` y una tecnología específica de la familia LED (`QLED` o `MINI_LED`), se asigna la específica.
- Cualquier otra combinación de tecnologías distintas → nulo, `TECNOLOGIA_AMBIGUA`.
- Sin coincidencias → nulo, `TECNOLOGIA_NO_ENCONTRADA`.

**RN-05 — Smart.**
- Valores: `SI`, `NO`.
- **Tabla configurable. Configuración inicial:** NO ← `NO SMART`, `NO SMART TV`, `NO ES SMART`, `SIN SMART`, `TV CONVENCIONAL`, `TELEVISOR CONVENCIONAL`; SI ← `SMART`, `SMART TV`, `SMARTTV`, `ANDROID TV`, `GOOGLE TV`, `WEBOS`, `TIZEN`, `ROKU TV`, `VIDAA`, `FIRE TV`.
- Los términos de negación (`NO`) se evalúan primero y consumen su texto.
- Campo extraído o estructurado con valor booleano: `SI`, `SÍ`, `YES`, `TRUE`, `1` → `SI`; `NO`, `FALSE`, `0` → `NO`; si es texto, se aplica la tabla.
- Si coinciden términos `SI` y `NO` → nulo, `SMART_AMBIGUO`.
- Sin coincidencias → nulo, `SMART_NO_ENCONTRADO`. Nunca se asume `NO` por ausencia.

**RN-06 — Generación (año aproximado del modelo).**
- Formato: año entero de 4 dígitos.
- **Fuente 1 — año explícito:** año de 4 dígitos precedido, con o sin espacio o dos puntos, por un calificador de la lista configurable (**configuración inicial:** `MODELO`, `MOD`, `MOD.`, `AÑO`, `ANO`, `GENERACION`, `LINEA`), o el campo estructurado "año del modelo" de una observación retail. Un año sin calificador no se usa.
- **Fuente 2 — tabla configurable de reglas por código de modelo:** filas {identificador, marca canónica, patrón sobre `modelo_normalizado`, año}. **Configuración inicial: vacía**; el Administrador carga las filas que valide. Solo se aplica si `marca` y `modelo_normalizado` del producto no son nulos. Si dos filas aplican con años distintos → nulo, `GENERACION_AMBIGUA`.
- Rango válido configurable: **configuración inicial: 2010 hasta el año actual + 1**, inclusive. Fuera → nulo, `GENERACION_FUERA_DE_RANGO`.
- Dos o más años explícitos distintos → nulo, `GENERACION_AMBIGUA`.
- Año explícito y regla de código con años distintos → nulo, `GENERACION_EN_CONFLICTO`, registrando ambos valores. Si coinciden, se guarda ese año con ambas reglas registradas.
- Sin evidencia → nulo, `GENERACION_NO_DETERMINADA`.
- Nunca se usan la fecha de compra, de firma, de la orden ni de la observación para determinar la generación.

**RN-07 — Trazabilidad por atributo.** Para cada atributo se guarda `valor_original`, `campo_origen`, `regla_aplicada`, `motivo_nulo` (si es nulo) y `conflicto_origen`.

**RN-08 — Estado de normalización.** Se recalcula sobre los 7 atributos de FR-035 (marca, modelo normalizado, tamaño, resolución, tecnología, Smart, generación): `COMPLETA` si los 7 son no nulos; `PARCIAL` si alguno es nulo pero el tamaño no es nulo, o marca y modelo normalizado no son nulos; `SIN_ATRIBUTOS_MINIMOS` en otro caso.

**RN-09 — Versiones e idempotencia.** Con el mismo origen y la misma versión de reglas el resultado es idéntico y no se crean versiones. Un cambio en un valor de origen usado, en `modelo_normalizado` o en la versión de reglas genera una nueva versión vigente; la anterior se conserva como histórica con fecha de reemplazo.

**RN-10 — Configuración.** Las tablas de sinónimos de tecnología y Smart, calificadores de año, reglas de generación y el rango de años solo las modifica el Administrador. Cada cambio registra usuario, fecha y hora, valor anterior y nuevo, e incrementa la versión de reglas en 1. Se rechaza con "Configuración inválida: {detalle}" un cambio que: deje vacía la tabla de tecnología o de Smart; asigne el mismo sinónimo a dos valores distintos; cargue una regla de generación sin marca, sin patrón o con año fuera del rango; o defina un rango con inicio mayor que el fin.

**RN-11 — Sin IA y tolerancia a errores.** El proceso es determinístico y no usa IA. Un error en un registro no detiene el lote: se registra el `id_origen` y el error, y se reintenta en la siguiente ejecución.

### Interfaz

Sin interfaz gráfica. Tablas mantenidas por configuración o interfaz administrativa mínima; resultados consultables por consulta a la base o por los servicios que los consumen.

### Sistemas Externos (Si aplica)

No aplica. Usa los registros de origen ya almacenados y el producto normalizado del esquema común.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-031 (crea el producto normalizado), HU-034 (modelo normalizado usado por la regla de generación), HU-038 (equivalencia que usa estos atributos).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-04):** el catálogo de tecnologías (`LED`, `QLED`, `MINI_LED`, `OLED`) y sus sinónimos iniciales son una propuesta configurable; los términos no incluidos (ej. `QNED`) quedan sin tecnología hasta que el Administrador los mapee.
- **S-02 (Resuelto → RN-05):** la ausencia de un término Smart no implica "no Smart"; queda nulo.
- **S-03 (Resuelto → RN-06):** la generación solo se toma de un año explícito con calificador o de reglas por código de modelo cargadas y validadas por el Administrador (tabla inicial vacía); nunca de las fechas de compra u observación.

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
