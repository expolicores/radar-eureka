# Historia #033: Identificar el código de modelo en el registro de origen

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Normalizar Códigos de Modelo  
**Prioridad:** Crítica  
**FRs relacionados:** FR-035, FR-036

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema identifique el código de modelo del fabricante en la descripción o en el campo de modelo de cada televisor, y lo deje nulo cuando no sea un modelo confiable,  
**Para** que el emparejamiento por mismo modelo solo use códigos reales y no códigos internos, referencias del pliego ni fragmentos de texto.

## Descripción

Solo el 36 % de las líneas TVEC traen un código de modelo, siempre dentro del texto libre de la descripción; en SECOP II el modelo aparece en el 22 % de los ítems extraídos y a veces es la referencia "o equivalente" del pliego; en retail el modelo viene en un campo o en el nombre comercial. Además, algunos "modelos" de la TVEC son códigos internos del catálogo (ej. `AMEPIE0377`), no modelos del fabricante.

Esta HU identifica el **modelo original** (`modelo_original`) de cada producto normalizado: el texto exacto que se considera el código de modelo, con su origen y regla. La normalización sintáctica de ese código (espacios, guiones, mayúsculas) la hace HU-034. Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Código de modelo en la descripción TVEC

- **Dado** que un producto normalizado de TVEC tiene la descripción `GSF01-TELEVISOR SAMSUNG UN55DU8000KXZL CRYSTAL UHD 55"`
- **Cuando** se ejecuta la identificación del modelo
- **Entonces** `modelo_original = UN55DU8000KXZL`, `campo_origen = descripcion_tvec` y `regla_aplicada = RN-04-token`
- **Y** no se toman como modelo `GSF01-`, `55"` ni `UHD`

### Escenario 2: Modelo con calificador en el texto

- **Dado** que una descripción contiene `TELEVISOR LG REF: 55UA7300PSB SMART 4K 3840X2160`
- **Cuando** se identifica el modelo
- **Entonces** `modelo_original = 55UA7300PSB` con `regla_aplicada = RN-05-calificador`, y `3840X2160` se descarta por ser una resolución

### Escenario 3: Campo estructurado de modelo

- **Dado** que un ítem SECOP II tiene el campo extraído de modelo `UN 55DU8000 KXZL` y una observación retail tiene el campo modelo `55UA7300PSA`
- **Cuando** se identifica el modelo
- **Entonces** el modelo original es el valor completo del campo (`UN 55DU8000 KXZL` y `55UA7300PSA`), incluidos sus espacios, con `campo_origen` del campo específico

### Escenario 4: Campo de modelo sin valor real

- **Dado** que el campo de modelo trae `N/A`, `No aplica`, `Genérico` o está vacío, y el texto libre no tiene un código candidato
- **Cuando** se identifica el modelo
- **Entonces** `modelo_original` queda nulo con motivo `MODELO_NO_INFORMADO`

### Escenario 5: Referencia del pliego ("o equivalente")

- **Dado** que el modelo extraído de un ítem SECOP II es `UN55DU8000 o equivalente`
- **Cuando** se identifica el modelo
- **Entonces** `modelo_original` queda nulo con motivo `MODELO_REFERENCIAL`, conservando el texto encontrado

### Escenario 6: Código interno del catálogo

- **Dado** que una descripción TVEC contiene `AMEPIE0377 TELEVISOR LG 43"` y el patrón de códigos internos configurado incluye los códigos que empiezan por `AMEPIE` seguidos de dígitos
- **Cuando** se identifica el modelo
- **Entonces** `AMEPIE0377` se registra como `codigo_interno_detectado`, no como modelo; si no hay otro candidato, `modelo_original` queda nulo con motivo `MODELO_CODIGO_INTERNO`

### Escenario 7: Varios candidatos distintos

- **Dado** que una descripción contiene dos candidatos distintos `UN55DU8000KXZL` y `UN50DU7000KXZL` sin calificador
- **Cuando** se identifica el modelo
- **Entonces** `modelo_original` queda nulo con motivo `MODELO_AMBIGUO` y se registran ambos candidatos
- **Y si** solo uno de ellos va precedido por un calificador (`MODELO`, `REF`…), **entonces** se toma ese candidato

### Escenario 8: Sin candidatos en el texto

- **Dado** que una descripción es `TELEVISOR SAMSUNG LED 50 PULGADAS SMART`
- **Cuando** se identifica el modelo
- **Entonces** `modelo_original` queda nulo con motivo `MODELO_NO_ENCONTRADO`

### Escenario 9: Tokens que parecen códigos pero no lo son

- **Dado** que una descripción contiene `120HZ`, `HDMI2.1`, `DVB-T2`, `7702040123456` (EAN) y `2160P`
- **Cuando** se identifica el modelo
- **Entonces** ninguno se toma como modelo

### Escenario 10: Cambio en el origen o en la configuración

- **Dado** que el Revisor corrige el modelo extraído de un ítem SECOP II, o el Administrador agrega un patrón de código interno
- **Cuando** se ejecuta la identificación
- **Entonces** los productos afectados obtienen una nueva versión con el modelo recalculado, la anterior se conserva como histórica y el cambio de configuración queda registrado con usuario, fecha y hora, valor anterior y nuevo

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); Administrador (mantiene listas y patrones). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** solo el Administrador modifica la configuración.
- **Valor de negocio:** un código de modelo erróneo produce un "mismo modelo" falso, que es el emparejamiento de mayor confianza y por tanto el más dañino si falla.

### Reglas de Negocio

**RN-01 — Registros de entrada.** Productos normalizados vigentes y activos (ítems SECOP II o TVEC con clasificación `incluido`, observaciones retail).

**RN-02 — Origen y prioridad.**
1. Campo estructurado de modelo: modelo/referencia extraído (SECOP II) o campo modelo de la observación retail.
2. Si el campo es nulo, vacío o no tiene valor real (RN-03): texto libre (descripción extraída del ítem SECOP II, descripción TVEC, nombre del producto retail).
- Si el campo estructurado tiene valor real, se usa ese valor completo y no se busca en el texto.

**RN-03 — Valores que no son modelo.** Lista configurable de no-valores, comparada sin distinguir mayúsculas ni tildes y sin espacios al inicio o al final. **Configuración inicial:** `N/A`, `NA`, `NO APLICA`, `NO INFORMA`, `SIN MODELO`, `GENERICO`, `GENERICA`, `-`, `0`. Un campo con un no-valor se trata como vacío.

**RN-04 — Candidatos en texto libre.** Sobre el texto preprocesado (mayúsculas, sin tildes, espacios colapsados, sin el prefijo de catálogo configurado —inicial: tres letras + dos dígitos + guion al inicio, ej. `GSF01-`), un candidato es una secuencia sin espacios que:
- tras quitar guiones, puntos y barras internas tiene **entre 6 y 20 caracteres** (configurable);
- contiene **al menos 2 letras y al menos 2 dígitos**;
- no es igual a la marca del producto;
- no coincide con ningún patrón de exclusión configurable. **Configuración inicial:** tamaños (número seguido de `"`, `PULGADAS`, `PULG`, `IN`, `CM`), resoluciones numéricas (`dddXddd`, `dddP`), frecuencias (`ddHZ`, `dddHZ`), solo dígitos (EAN u otros números), y los términos `HDMI…`, `USB…`, `DVB…`, `ATSC…`, `WIFI…`, `BLUETOOTH…`.

**RN-05 — Calificador.** Si un candidato va precedido (con o sin espacio, dos puntos o punto) por un calificador de la lista configurable (**configuración inicial:** `MODELO`, `MOD`, `REF`, `REFERENCIA`, `MODEL`), tiene prioridad sobre los demás candidatos.

**RN-06 — Selección.**
- Un solo candidato → es el modelo original.
- Varios candidatos iguales → se toma uno.
- Varios candidatos distintos: si exactamente uno tiene calificador → ese; en otro caso → nulo, `MODELO_AMBIGUO`, con la lista de candidatos registrada.
- Ningún candidato → nulo, `MODELO_NO_ENCONTRADO`.
- Campo estructurado vacío o no-valor y ningún candidato en texto → nulo, `MODELO_NO_INFORMADO`.

**RN-07 — Referencia del pliego.** Si el valor del campo estructurado, o el texto que rodea al candidato (hasta 3 palabras después), contiene una expresión de referencia configurable (**configuración inicial:** `O EQUIVALENTE`, `O SIMILAR`, `SIMILAR A`, `TIPO`) → nulo, `MODELO_REFERENCIAL`, conservando el texto.

**RN-08 — Códigos internos.** Lista configurable de patrones de códigos que no son modelos del fabricante. **Configuración inicial:** códigos que empiezan por `AMEPIE` seguidos solo de dígitos (observado en D6). Un candidato que cumple un patrón se registra en `codigo_interno_detectado` y se descarta como modelo; si no queda otro candidato → nulo, `MODELO_CODIGO_INTERNO`. Esta lista no es un catálogo de productos.

**RN-09 — Registro.** Se guarda `modelo_original` (texto exacto, sin modificar espacios ni guiones), `campo_origen`, `regla_aplicada`, `motivo_nulo`, `candidatos_descartados` (lista con el motivo de cada uno) y `codigo_interno_detectado`. Nunca se inventa ni se completa un código.

**RN-10 — Versiones y configuración.** Igual origen y versión de reglas → mismo resultado, sin nuevas versiones. Un cambio de origen (incluida una corrección del Revisor) o de versión de reglas genera nueva versión vigente; la anterior queda histórica. Solo el Administrador cambia listas y patrones; cada cambio registra usuario, fecha y hora, valor anterior y nuevo, e incrementa la versión de reglas. Se rechaza con "Configuración inválida: {detalle}" un patrón que no se pueda interpretar o una longitud mínima mayor que la máxima.

**RN-11 — Sin IA y tolerancia a errores.** Proceso determinístico. Un error en un registro no detiene el lote; se registra y se reintenta en la siguiente ejecución.

### Interfaz

Sin interfaz gráfica. Configuración por archivo, parametrización o interfaz administrativa mínima; resultados consultables por consulta a la base.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-031 (producto normalizado y marca), HU-034 (normalización sintáctica del modelo original), HU-035 (emparejamiento por mismo modelo).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-04):** la forma de un candidato a modelo (6–20 caracteres, ≥ 2 letras y ≥ 2 dígitos, sin espacios en texto libre) y los patrones de exclusión son valores iniciales configurables. Un modelo escrito con espacios en texto libre no se reconoce; en campos estructurados sí.
- **S-02 (Resuelto → RN-08):** los códigos internos se detectan con patrones configurables; el inicial (`AMEPIE` + dígitos) proviene de D6.
- **S-03 (Resuelto → RN-07):** un modelo acompañado de "o equivalente" es una referencia del pliego y no se usa como modelo.

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
