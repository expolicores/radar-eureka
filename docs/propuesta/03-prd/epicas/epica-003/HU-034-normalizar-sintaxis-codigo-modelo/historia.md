# Historia #034: Normalizar sintácticamente el código de modelo

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Normalizar Códigos de Modelo  
**Prioridad:** Crítica  
**FRs relacionados:** FR-036, FR-035

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que los códigos de modelo se normalicen corrigiendo solo diferencias de escritura (espacios, guiones, mayúsculas y formatos equivalentes) sin eliminar ninguna parte del código,  
**Para** que `UN 55DU8000 KXZL` y `un55du8000kxzl` se reconozcan como el mismo código, pero `55UA7300PSA` y `55UA7300PSB` sigan siendo referencias distintas.

## Descripción

FR-036 exige una normalización **solo sintáctica**: el mismo código escrito de formas distintas debe producir el mismo `modelo_normalizado`, pero ningún componente que pueda representar una variante técnica (sufijos regionales como `PSA`/`PSB`, `KXZL`, códigos de año o de serie) puede eliminarse. Dos referencias distintas nunca se convierten en una por efecto de la normalización.

Esta HU toma el `modelo_original` identificado para cada producto normalizado y calcula `modelo_normalizado`, que es el valor usado para el emparejamiento por mismo modelo. Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Diferencias de espacios, guiones y mayúsculas

- **Dado** que tres productos tienen como modelo original `UN 55DU8000 KXZL`, `un55du8000kxzl` y `UN-55DU8000-KXZL`
- **Cuando** se ejecuta la normalización del modelo
- **Entonces** los tres quedan con `modelo_normalizado = UN55DU8000KXZL`

### Escenario 2: Sufijos regionales y variantes se conservan

- **Dado** que dos productos tienen como modelo original `55UA7300PSA` y `55UA7300PSB`
- **Cuando** se normalizan
- **Entonces** quedan con `modelo_normalizado` `55UA7300PSA` y `55UA7300PSB` respectivamente, que son distintos
- **Y** ningún carácter alfanumérico del código original se elimina, reemplaza ni reordena

### Escenario 3: Formatos equivalentes con separadores y etiquetas

- **Dado** que los modelos originales son `55.UA7300.PSB`, `55UA7300/PSB`, `55UA7300_PSB` y `Modelo: 55UA7300PSB`
- **Cuando** se normalizan
- **Entonces** todos quedan con `modelo_normalizado = 55UA7300PSB`

### Escenario 4: Marca antepuesta al código

- **Dado** que un producto con `marca = SAMSUNG` tiene el modelo original `SAMSUNG UN55DU8000KXZL`
- **Cuando** se normaliza
- **Entonces** `modelo_normalizado = UN55DU8000KXZL`
- **Y si** la marca aparece sin separador y pegada al código (`SAMSUNGUN55DU8000`), **entonces** no se elimina y `modelo_normalizado = SAMSUNGUN55DU8000`

### Escenario 5: Caracteres que no son separadores

- **Dado** que un modelo original contiene caracteres distintos de letras, dígitos y separadores reconocidos (ej. `55UA7300(PSB)` o `55UA7300+`)
- **Cuando** se normaliza
- **Entonces** `modelo_normalizado` queda nulo con motivo `MODELO_CARACTERES_NO_VALIDOS` y el original se conserva

### Escenario 6: Caracteres parecidos no se sustituyen

- **Dado** que dos modelos originales son `55UA73OOPSB` (con letra O) y `55UA7300PSB` (con dígito cero)
- **Cuando** se normalizan
- **Entonces** sus `modelo_normalizado` son distintos; el sistema no convierte `O`↔`0`, `I`↔`1` ni `S`↔`5`

### Escenario 7: Longitud fuera de rango tras normalizar

- **Dado** que un modelo original queda con menos de 4 o más de 25 caracteres tras normalizar
- **Cuando** se normaliza
- **Entonces** `modelo_normalizado` queda nulo con motivo `MODELO_LONGITUD_INVALIDA`

### Escenario 8: Sin modelo original

- **Dado** que un producto tiene `modelo_original` nulo con un motivo (ej. `MODELO_NO_ENCONTRADO`)
- **Cuando** se normaliza
- **Entonces** `modelo_normalizado` queda nulo y hereda el mismo motivo

### Escenario 9: Cambio del modelo original

- **Dado** que el `modelo_original` de un producto cambia (por corrección del origen o nueva versión de reglas)
- **Cuando** se ejecuta la normalización
- **Entonces** se genera una nueva versión vigente con el nuevo `modelo_normalizado` y la anterior se conserva como histórica; si no hubo cambios, no se crea versión

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** solo el Administrador modifica la lista de separadores y etiquetas.
- **Valor de negocio:** evita que diferencias de escritura oculten un mismo modelo, sin fusionar referencias distintas que pueden tener precios distintos (riesgo R2).

### Reglas de Negocio

**RN-01 — Entrada.** `modelo_original` de los productos normalizados vigentes y activos.

**RN-02 — Pasos de normalización, en este orden:**
1. Quitar espacios al inicio y al final.
2. Convertir a mayúsculas y quitar tildes.
3. Quitar al inicio una etiqueta de la lista configurable, seguida o no de `:`, `.` o espacio. **Configuración inicial:** `MODELO`, `MOD`, `REF`, `REFERENCIA`, `MODEL`.
4. Quitar al inicio la `marca` canónica del producto **solo si** va seguida de un separador (espacio, guion, punto, barra o guion bajo). Si la marca es nula, este paso no aplica.
5. Eliminar todos los separadores de la lista configurable. **Configuración inicial:** espacio, guion (`-`), guion bajo (`_`), punto (`.`), barra (`/`) y barra invertida (`\`).
6. Validar: el resultado solo puede contener `A–Z` y `0–9`. Si contiene otro carácter → nulo, `MODELO_CARACTERES_NO_VALIDOS`.
7. Validar longitud: **configuración inicial 4 a 25 caracteres**, inclusive. Fuera → nulo, `MODELO_LONGITUD_INVALIDA`.

**RN-03 — Prohibiciones (FR-036).** La normalización NUNCA: elimina, recorta ni reordena caracteres alfanuméricos; elimina sufijos (regionales, de año, de serie o de color); sustituye caracteres parecidos (`O`/`0`, `I`/`1`, `S`/`5`, `B`/`8`); aplica coincidencia aproximada o por prefijo. Dos `modelo_normalizado` se consideran el mismo código solo si son **exactamente iguales**.

**RN-04 — Nulos.** Si `modelo_original` es nulo, `modelo_normalizado` es nulo con el mismo motivo.

**RN-05 — Trazabilidad.** Se guarda `modelo_original`, `modelo_normalizado`, la lista de pasos aplicados (ej. `mayusculas`, `quitar_marca`, `quitar_separadores`) y `motivo_nulo`.

**RN-06 — Versiones e idempotencia.** Con el mismo `modelo_original`, `marca` y versión de reglas, el resultado es idéntico y no se crea versión. Un cambio en cualquiera de ellos genera nueva versión vigente y conserva la anterior como histórica. Aplicar la normalización a un `modelo_normalizado` produce el mismo valor.

**RN-07 — Configuración.** Solo el Administrador modifica etiquetas, separadores y límites de longitud. Cada cambio registra usuario, fecha y hora, valor anterior y nuevo, e incrementa la versión de reglas. Se rechaza con "Configuración inválida: {detalle}": agregar como separador una letra o un dígito; una longitud mínima mayor que la máxima o menor que 1.

**RN-08 — Sin IA y tolerancia a errores.** Proceso determinístico; un error en un registro no detiene el lote, se registra y se reintenta.

### Interfaz

Sin interfaz gráfica. Resultados consultables por consulta a la base.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-033 (identifica el modelo original), HU-035 (usa el modelo normalizado para mismo modelo), HU-038 (referencias distintas que solo pueden ser equivalentes).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-02, RN-03):** "formatos equivalentes" se limita a separadores (espacio, guion, guion bajo, punto, barras), etiquetas iniciales y la marca antepuesta con separador. El spike D6 hablaba de "tolerar sufijos regionales"; prevalece FR-036 del PRD: los sufijos se conservan y las referencias con sufijo distinto solo pueden ser equivalentes.
- **S-02 (Resuelto → RN-02):** la longitud válida 4–25 caracteres es un valor inicial configurable.

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
