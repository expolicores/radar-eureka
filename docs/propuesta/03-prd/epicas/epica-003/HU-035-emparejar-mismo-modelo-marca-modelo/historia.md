# Historia #035: Emparejar como mismo modelo por marca y modelo normalizado

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Emparejar por Mismo Modelo  
**Prioridad:** Crítica  
**FRs relacionados:** FR-037

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada televisor comprado por una entidad se empareje como **mismo modelo** con otros televisores (compras públicas o retail) que tengan la misma marca y el mismo modelo normalizado,  
**Para** comparar el precio contra el mismo producto, que es la referencia de mayor confianza.

## Descripción

El emparejamiento se calcula para cada **ítem objetivo**: un producto normalizado activo de origen SECOP II o TVEC (una compra pública que puede analizarse). Sus **candidatos** son todos los demás productos normalizados activos de la misma categoría (ítems SECOP II, ítems TVEC y observaciones retail).

Un par es **mismo modelo** cuando la marca y el `modelo_normalizado` coinciden exactamente (el modelo normalizado solo corrige diferencias sintácticas y conserva sufijos como `PSA`/`PSB`). Como salvaguarda contra errores de extracción o normalización, si el par coincide en marca y modelo pero tiene atributos técnicos contradictorios (ej. 55" frente a 65"), no se acepta como mismo modelo y se registra como **insuficiente/no confiable** con el motivo.

Esta HU no aplica ventanas temporales, bases tributarias ni precios: esa selección la hace el cálculo de benchmarks. Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Mismo modelo entre un ítem TVEC y una observación retail

- **Dado** que el ítem objetivo TVEC-1301 tiene `marca = SAMSUNG`, `modelo_normalizado = UN55DU8000KXZL`, `tamano_pulgadas = 55` y la observación retail RET-3301 tiene los mismos marca, modelo y tamaño
- **Cuando** se ejecuta el emparejamiento
- **Entonces** se registra un par {TVEC-1301, RET-3301} con `tipo = MISMO_MODELO` y `criterio = MARCA_MODELO`, con los valores de marca y modelo de ambos lados

### Escenario 2: Mismo modelo entre dos compras públicas

- **Dado** que el ítem objetivo SEC-2301-I1 (SECOP II) y el ítem TVEC-1301 tienen marca `SAMSUNG` y modelo normalizado `UN55DU8000KXZL`
- **Cuando** se ejecuta el emparejamiento
- **Entonces** se registra el par como `MISMO_MODELO` y, como ambos son ítems objetivo, cada uno aparece como candidato del otro

### Escenario 3: Sufijo distinto no es mismo modelo

- **Dado** que el ítem objetivo tiene `LG` / `55UA7300PSB` y el candidato `LG` / `55UA7300PSA`
- **Cuando** se ejecuta el emparejamiento por mismo modelo
- **Entonces** no se registra un par `MISMO_MODELO` (los modelos no son exactamente iguales); el par solo podrá evaluarse como equivalente

### Escenario 4: Marca o modelo desconocidos

- **Dado** que el ítem objetivo tiene `modelo_normalizado = UN55DU8000KXZL` pero `marca` nula, o tiene marca y `modelo_normalizado` nulo
- **Cuando** se ejecuta el emparejamiento
- **Entonces** no se registra ningún par `MISMO_MODELO` por marca y modelo para ese ítem, y se registra el motivo `MARCA_O_MODELO_NULO` en su resultado de emparejamiento por mismo modelo

### Escenario 5: Marca distinta con el mismo código

- **Dado** que el objetivo tiene `SAMSUNG` / `UN55DU8000KXZL` y un candidato tiene `EXCLUSIV` / `UN55DU8000KXZL`
- **Cuando** se ejecuta el emparejamiento
- **Entonces** no se registra par `MISMO_MODELO`

### Escenario 6: Atributos contradictorios en un par con mismo marca y modelo

- **Dado** que el objetivo tiene `SAMSUNG` / `UN55DU8000KXZL` / 55" y un candidato tiene el mismo marca y modelo pero `tamano_pulgadas = 65`
- **Cuando** se ejecuta el emparejamiento
- **Entonces** se registra el par con `tipo = INSUFICIENTE_NO_CONFIABLE`, motivo `CONFLICTO_ATRIBUTOS` y el detalle `tamano_pulgadas: 55 vs 65`
- **Y** el par no se cuenta como mismo modelo

### Escenario 7: Atributos desconocidos no bloquean

- **Dado** que el objetivo y el candidato coinciden en marca y modelo, el objetivo tiene `resolucion = 4K` y el candidato tiene `resolucion` nula
- **Cuando** se ejecuta el emparejamiento
- **Entonces** el par es `MISMO_MODELO` y en sus criterios la resolución figura como `NO_EVALUADO`

### Escenario 8: Sin candidatos de mismo modelo

- **Dado** que ningún otro producto activo coincide en marca y modelo con el objetivo
- **Cuando** se ejecuta el emparejamiento
- **Entonces** no se registra ningún par `MISMO_MODELO` y el resultado de mismo modelo del ítem indica `SIN_CANDIDATOS_MISMO_MODELO`

### Escenario 9: Un producto no se empareja consigo mismo ni con inactivos

- **Dado** que existen el propio objetivo, otra versión histórica de él y un candidato con `activo = no` que coincide en marca y modelo
- **Cuando** se ejecuta el emparejamiento
- **Entonces** ninguno de ellos genera par

### Escenario 10: Recalcular al cambiar un producto

- **Dado** que existe un par `MISMO_MODELO` vigente y el candidato obtiene una nueva versión con otro `modelo_normalizado`
- **Cuando** se ejecuta el emparejamiento
- **Entonces** el par anterior pasa a `vigente = no` con fecha y se recalculan los pares de ambos productos; una reejecución sin cambios no crea pares duplicados

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** solo el Administrador modifica la lista de atributos de control de conflicto.
- **Valor de negocio:** el mismo modelo es la comparación más defendible; según D1 y D6 proviene sobre todo de la TVEC y de Alkosto.

### Reglas de Negocio

**RN-01 — Ítems objetivo y candidatos.** Ítem objetivo: producto normalizado vigente y activo con `tipo_origen` `SECOP_II` o `TVEC`. Candidato: cualquier otro producto normalizado vigente y activo de la **misma categoría** (`SECOP_II`, `TVEC` o `RETAIL`), con `id_origen` distinto al del objetivo. Nunca se emparejan productos de categorías distintas, versiones históricas ni productos con `activo = no`.

**RN-02 — Condición de mismo modelo por marca y modelo (FR-037).** `marca` no nula en ambos, `modelo_normalizado` no nulo en ambos, y ambos valores **exactamente iguales** (comparación de texto exacta; sin coincidencia aproximada, por prefijo ni por raíz del código).

**RN-03 — Control de conflicto.** Lista configurable de atributos de control. **Configuración inicial:** `tamano_pulgadas`, `resolucion`, `tecnologia`. Si un par cumple RN-02 y algún atributo de control es no nulo en ambos lados y distinto → el par se registra con `tipo = INSUFICIENTE_NO_CONFIABLE`, motivo `CONFLICTO_ATRIBUTOS` y el detalle de cada atributo en conflicto (`atributo: valor objetivo vs valor candidato`). Si el atributo es nulo en alguno de los lados → `NO_EVALUADO` y no bloquea.

**RN-04 — Registro del par.** Campos: `id_emparejamiento`, `id_producto_objetivo`, `id_producto_candidato`, `tipo` (`MISMO_MODELO` o `INSUFICIENTE_NO_CONFIABLE`), `criterio` (`MARCA_MODELO`), `criterios_evaluados` (lista: atributo, valor objetivo, valor candidato, resultado `CUMPLE` / `NO_CUMPLE` / `NO_EVALUADO`), `motivo` (si aplica), versiones de los dos productos usadas, `version_reglas`, `fecha_calculo`, `vigente`. Un solo par vigente por combinación {objetivo, candidato}.

**RN-05 — Resultado de mismo modelo del ítem.** Para cada ítem objetivo se registra: número de pares `MISMO_MODELO`, número de pares en conflicto y, si no hay pares `MISMO_MODELO`, el motivo: `MARCA_O_MODELO_NULO` (el objetivo no tiene marca o modelo) o `SIN_CANDIDATOS_MISMO_MODELO`.

**RN-06 — Independencia de precio y fecha.** El emparejamiento no usa precio, fecha, base tributaria ni fuente; esos filtros pertenecen al cálculo de benchmarks.

**RN-07 — Recalculo e idempotencia.** Se recalculan los pares de un producto cuando obtiene una nueva versión, cuando se inactiva o cuando cambia la versión de reglas. Los pares reemplazados pasan a `vigente = no` con fecha (no se borran). Reejecutar sin cambios no crea pares ni versiones.

**RN-08 — Configuración.** Solo el Administrador cambia la lista de atributos de control; cada cambio registra usuario, fecha y hora, valor anterior y nuevo, e incrementa la versión de reglas. Se rechaza con "Configuración inválida: {detalle}" un atributo que no pertenezca al esquema común. Una lista vacía es válida (sin control de conflicto) solo si se registra una justificación de al menos 10 caracteres.

**RN-09 — Tolerancia a errores.** Un error al emparejar un objetivo no detiene el lote; se registra y se reintenta en la siguiente ejecución.

### Interfaz

Sin interfaz gráfica en esta HU. Los pares se consultan por consulta a la base; su visualización para el Analista se cubre en HU-040.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-031 a HU-034 (atributos normalizados), HU-036 (mismo modelo por EAN), HU-038 (equivalencia), HU-039 (clasificación del resultado), HU-040 (consulta de criterios).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-01):** los ítems objetivo son las compras públicas (SECOP II y TVEC); las observaciones retail solo actúan como candidatos.
- **S-02 (Resuelto → RN-03):** un par con misma marca y modelo pero tamaño, resolución o tecnología contradictorios se clasifica como insuficiente/no confiable (salvaguarda contra errores de extracción); la lista de atributos de control es configurable.
- **S-03 (Resuelto → RN-06):** las ventanas temporales y la base tributaria no forman parte del emparejamiento; se aplican en los benchmarks.

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
