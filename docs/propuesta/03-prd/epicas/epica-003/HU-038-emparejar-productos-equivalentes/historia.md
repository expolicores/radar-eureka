# Historia #038: Emparejar productos equivalentes por características técnicas

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Emparejar por Equivalencia Técnica  
**Prioridad:** Crítica  
**FRs relacionados:** FR-038, FR-040

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que, cuando no exista el mismo modelo, cada televisor comprado se empareje como **producto equivalente** con los televisores que cumplen todas las características de equivalencia configuradas,  
**Para** contar con referencias comparables en compras especificadas por características ("65 pulgadas, 4K, Smart"), sin que el sistema rebaje los criterios para encontrar una referencia.

## Descripción

En SECOP II predomina la especificación por características y la marca y el modelo aparecen en solo ~22–28 % de los ítems (D4), así que la equivalencia es la vía principal de comparación para esa fuente. Esta HU evalúa cada par {ítem objetivo, candidato} que **no** es mismo modelo contra el conjunto de reglas de equivalencia vigente de su categoría y registra como `EQUIVALENTE` solo los pares que cumplen **todos** los criterios aplicables.

Dos referencias de modelo distintas (ej. `55UA7300PSA` y `55UA7300PSB`) solo pueden ser equivalentes si sus características técnicas lo sustentan, y el par lo indica explícitamente. Si no hay equivalentes, el resultado es cero: **nunca** se reintenta con criterios menos estrictos, tolerancias mayores ni ignorando valores desconocidos (FR-040, Adenda 2 A2.7).

Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Par equivalente que cumple todos los criterios

- **Dado** que las reglas vigentes de `televisor` son: tamaño, resolución, tecnología y Smart exactos y obligatorios; generación ±1 año y marca exacta solo si ambos se conocen
- **Y** el ítem objetivo SEC-2501-I1 tiene 65" / 4K / LED / Smart SI / marca nula / generación nula, y el candidato TVEC-1501 tiene 65" / 4K / LED / Smart SI / SAMSUNG / 2024
- **Cuando** se ejecuta el emparejamiento de equivalentes
- **Entonces** se registra el par con `tipo = EQUIVALENTE`, `version_reglas` vigente y los criterios: tamaño, resolución, tecnología y Smart `CUMPLE`; generación y marca `NO_EVALUADO`

### Escenario 2: Un criterio obligatorio no coincide

- **Dado** que el objetivo tiene 65" y el candidato 55", con las demás características iguales
- **Cuando** se evalúa el par
- **Entonces** no se registra par `EQUIVALENTE` y el candidato se cuenta como descartado por `tamano_pulgadas`

### Escenario 3: Un criterio obligatorio es desconocido

- **Dado** que el candidato tiene `tecnologia` nula y el criterio de tecnología es obligatorio
- **Cuando** se evalúa el par
- **Entonces** no se registra par `EQUIVALENTE` y el candidato se cuenta como descartado por `tecnologia (desconocido)`

### Escenario 4: Criterio "solo si ambos conocidos" que no cumple

- **Dado** que ambos productos tienen marca y son distintas (`SAMSUNG` vs `LG`), o ambos tienen generación y difieren en 2 años con tolerancia 1
- **Cuando** se evalúa el par
- **Entonces** no se registra par `EQUIVALENTE` y se cuenta el descarte por `marca` o `generacion`

### Escenario 5: Generación en el límite de la tolerancia

- **Dado** que la tolerancia de generación es 1 año y los productos tienen 2023 y 2024
- **Cuando** se evalúa el par
- **Entonces** el criterio de generación es `CUMPLE`

### Escenario 6: Referencias de modelo distintas

- **Dado** que el objetivo es `LG` / `55UA7300PSB` y el candidato `LG` / `55UA7300PSA`, ambos 55" / 4K / LED / Smart SI
- **Cuando** se evalúa el par
- **Entonces** se registra como `EQUIVALENTE` (no como mismo modelo) con `modelos_distintos = sí` y ambos modelos en sus criterios

### Escenario 7: Objetivo sin los atributos obligatorios

- **Dado** que el objetivo tiene `tamano_pulgadas` nulo
- **Cuando** se ejecuta el emparejamiento de equivalentes
- **Entonces** no se evalúa ningún candidato y el resultado de equivalencia del objetivo registra `ATRIBUTOS_OBLIGATORIOS_FALTANTES: tamano_pulgadas`

### Escenario 8: Sin equivalentes no se relajan los criterios

- **Dado** que ningún candidato cumple todos los criterios
- **Cuando** se ejecuta el emparejamiento de equivalentes
- **Entonces** el objetivo queda con 0 pares `EQUIVALENTE`, motivo `SIN_CANDIDATOS_QUE_CUMPLAN` y el conteo de descartes por criterio
- **Y** el sistema no repite la evaluación con menos criterios, mayores tolerancias ni tratando desconocidos como coincidencias

### Escenario 9: Par que ya es mismo modelo o está en conflicto

- **Dado** que un par ya tiene registro vigente `MISMO_MODELO` o `INSUFICIENTE_NO_CONFIABLE` por conflicto de atributos
- **Cuando** se ejecuta el emparejamiento de equivalentes
- **Entonces** ese par no se evalúa como equivalente

### Escenario 10: Categoría sin reglas vigentes

- **Dado** que el objetivo pertenece a una categoría sin reglas de equivalencia vigentes
- **Cuando** se ejecuta el emparejamiento
- **Entonces** no se generan equivalentes y se registra `SIN_REGLAS_EQUIVALENCIA`

### Escenario 11: Recalculo con nueva versión de reglas o de producto

- **Dado** que existe una nueva versión de reglas o de alguno de los productos
- **Cuando** se ejecuta el emparejamiento
- **Entonces** los pares afectados se recalculan, los anteriores quedan `vigente = no` con su versión de reglas, y una reejecución sin cambios no crea pares duplicados

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** ninguno para el proceso; las reglas las mantiene el Administrador (HU-037).
- **Valor de negocio:** habilita el Benchmark 1 para la mayoría de compras SECOP II sin generar falsos positivos por equivalencias laxas (riesgo R2).

### Reglas de Negocio

**RN-01 — Objetivos y candidatos.** Objetivo: producto normalizado vigente y activo `SECOP_II` o `TVEC`. Candidato: otro producto vigente y activo de la **misma categoría** (`SECOP_II`, `TVEC` o `RETAIL`) con `id_origen` distinto. Se excluyen los pares que ya tienen registro vigente `MISMO_MODELO` o `INSUFICIENTE_NO_CONFIABLE` por conflicto.

**RN-02 — Reglas aplicables.** Se usa el conjunto de reglas de equivalencia **vigente** de la categoría al momento del cálculo. Cada criterio tiene `atributo`, `modo` (`EXACTO` o `TOLERANCIA`), `tolerancia` y `obligatoriedad` (`OBLIGATORIO`, `SI_AMBOS_CONOCIDOS`, `NO_EVALUADO`). **Configuración inicial `televisor`:** tamaño, resolución, tecnología y Smart `EXACTO` + `OBLIGATORIO`; generación `TOLERANCIA` 1 año + `SI_AMBOS_CONOCIDOS`; marca `EXACTO` + `SI_AMBOS_CONOCIDOS`. Sin conjunto vigente → sin equivalentes, `SIN_REGLAS_EQUIVALENCIA`.

**RN-03 — Evaluación de cada criterio.**
- `OBLIGATORIO`: si algún valor es nulo → `NO_CUMPLE (desconocido)`; si ambos se conocen → `CUMPLE` cuando coinciden (EXACTO) o `|a − b| ≤ tolerancia` (TOLERANCIA), si no `NO_CUMPLE`.
- `SI_AMBOS_CONOCIDOS`: si algún valor es nulo → `NO_EVALUADO`; si ambos se conocen, igual que el anterior.
- `NO_EVALUADO`: no se evalúa ni se muestra como cumplido.
- La comparación de texto es exacta sobre valores normalizados.

**RN-04 — Decisión.** Un par es `EQUIVALENTE` solo si ningún criterio queda en `NO_CUMPLE`. No existe coincidencia parcial ni puntaje que compense un criterio no cumplido.

**RN-05 — Prerrequisito del objetivo.** Si el objetivo tiene nulo algún atributo con criterio `OBLIGATORIO`, no se evalúan candidatos y se registra `ATRIBUTOS_OBLIGATORIOS_FALTANTES` con la lista de atributos.

**RN-06 — Prohibición de relajación (FR-040).** El sistema nunca: reevalúa con menos criterios, mayores tolerancias u otra obligatoriedad cuando no encuentra equivalentes; trata un valor desconocido como coincidencia en un criterio obligatorio; usa una versión de reglas distinta de la vigente; ni completa atributos faltantes con supuestos. La ausencia de equivalentes es un resultado válido.

**RN-07 — Referencias distintas.** Si ambos productos tienen `modelo_normalizado` no nulo y distinto, el par puede ser `EQUIVALENTE` solo si cumple RN-04, y se registra `modelos_distintos = sí` con ambos modelos.

**RN-08 — Registro del par.** `id_emparejamiento`, objetivo, candidato, `tipo = EQUIVALENTE`, `criterios_evaluados` (por criterio: atributo, modo, tolerancia, obligatoriedad, valor objetivo, valor candidato, resultado), `modelos_distintos`, versiones de ambos productos, `version_reglas`, `fecha_calculo`, `vigente`. Un solo par vigente por {objetivo, candidato}. Los pares descartados no se guardan uno a uno.

**RN-09 — Resultado de equivalencia del ítem.** Por objetivo: número de pares `EQUIVALENTE`, número de candidatos evaluados, conteo de descartes por atributo (ej. `tamano_pulgadas: 120`, `tecnologia (desconocido): 14`) y, si hay 0 equivalentes, motivo `SIN_CANDIDATOS_QUE_CUMPLAN`, `ATRIBUTOS_OBLIGATORIOS_FALTANTES` o `SIN_REGLAS_EQUIVALENCIA`.

**RN-10 — Independencia de precio y fecha.** No se usan precio, fecha, fuente ni base tributaria; esos filtros pertenecen a los benchmarks.

**RN-11 — Recálculo, idempotencia y errores.** Se recalcula al cambiar la versión de reglas, la versión de un producto o su estado activo. Los pares reemplazados quedan `vigente = no` (no se borran). Reejecutar sin cambios no crea registros. Un error en un objetivo no detiene el lote; se registra y se reintenta.

### Interfaz

Sin interfaz gráfica. Consultable por consulta a la base; visualización para el Analista en HU-040.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-037 (reglas de equivalencia), HU-035 y HU-036 (mismo modelo, que tiene precedencia), HU-039 (clasificación), HU-040 (consulta de criterios), HU-041 (verificación de no relajación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-03):** un valor desconocido en un criterio obligatorio cuenta como no cumplido; en un criterio "solo si ambos conocidos" queda no evaluado.
- **S-02 (Resuelto → RN-04, RN-06):** no hay puntaje parcial ni reintento con criterios menores; cero equivalentes es un resultado válido.
- **S-03 (Resuelto → RN-08, RN-09):** los candidatos descartados no se guardan uno a uno; se guarda el conteo por criterio para explicar el resultado.

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
