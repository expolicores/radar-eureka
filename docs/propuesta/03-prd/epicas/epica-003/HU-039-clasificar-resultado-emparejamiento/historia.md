# Historia #039: Clasificar el resultado de emparejamiento de cada ítem

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Clasificar y Explicar el Emparejamiento  
**Prioridad:** Crítica  
**FRs relacionados:** FR-039

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada televisor comprado tenga una clasificación de emparejamiento única —*mismo modelo*, *producto equivalente* o *insuficiente/no confiable*— con un resumen de los criterios usados,  
**Para** saber de inmediato qué tan comparable es el ítem antes de mirar cualquier referencia de precio.

## Descripción

FR-039 y NFR-CAL-005 exigen que el 100 % de las comparaciones estén clasificadas en una de tres categorías. Los pares individuales ya tienen tipo (`MISMO_MODELO`, `EQUIVALENTE`, `INSUFICIENTE_NO_CONFIABLE`). Esta HU consolida, para cada **ítem objetivo** (producto normalizado activo de SECOP II o TVEC), su **resultado de emparejamiento**: la clasificación de mayor confianza disponible, los conteos por tipo, los motivos cuando es insuficiente y un resumen de criterios en texto legible.

Este resultado es el que consumen el cálculo de benchmarks, la ficha del contrato y las señales; ninguna comparación debe usar un ítem sin clasificación vigente. Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Ítem con pares de mismo modelo

- **Dado** que el ítem objetivo TVEC-1601 tiene 3 pares vigentes `MISMO_MODELO` y 12 pares `EQUIVALENTE`
- **Cuando** se calcula su resultado de emparejamiento
- **Entonces** `clasificacion = MISMO_MODELO`, etiqueta "Mismo modelo", conteos `mismo_modelo = 3`, `equivalente = 12`, `conflicto = 0`, y el resumen "Mismo modelo: 3 productos con la misma marca y modelo (SAMSUNG · UN55DU8000KXZL)"

### Escenario 2: Ítem solo con equivalentes

- **Dado** que el ítem SEC-2601-I1 no tiene pares `MISMO_MODELO` y tiene 8 pares `EQUIVALENTE`
- **Cuando** se calcula su resultado
- **Entonces** `clasificacion = EQUIVALENTE`, etiqueta "Producto equivalente", y el resumen lista los criterios cumplidos y los no evaluados de la versión de reglas vigente (ej. "Producto equivalente: 8 productos con tamaño 65", resolución 4K, tecnología LED y Smart; no evaluados: marca, generación")

### Escenario 3: Ítem sin pares válidos

- **Dado** que un ítem no tiene pares `MISMO_MODELO` ni `EQUIVALENTE`
- **Cuando** se calcula su resultado
- **Entonces** `clasificacion = INSUFICIENTE_NO_CONFIABLE`, etiqueta "Insuficiente / no confiable", con uno o más motivos de la lista cerrada y su texto legible

### Escenario 4: Ítem con solo pares en conflicto

- **Dado** que un ítem solo tiene pares `INSUFICIENTE_NO_CONFIABLE` por conflicto de atributos
- **Cuando** se calcula su resultado
- **Entonces** `clasificacion = INSUFICIENTE_NO_CONFIABLE` con motivo `SOLO_PARES_EN_CONFLICTO` y el número de pares en conflicto

### Escenario 5: Ítem sin atributos mínimos

- **Dado** que un ítem tiene `estado_normalizacion = SIN_ATRIBUTOS_MINIMOS`
- **Cuando** se calcula su resultado
- **Entonces** `clasificacion = INSUFICIENTE_NO_CONFIABLE` con motivo `SIN_ATRIBUTOS_MINIMOS`

### Escenario 6: Cobertura del 100 %

- **Dado** que existen N ítems objetivo activos tras una ejecución completa
- **Cuando** se consulta el indicador de cobertura de clasificación
- **Entonces** el número de ítems con resultado vigente es N, cada resultado tiene exactamente uno de los tres valores y no hay valores nulos
- **Y si** algún ítem queda sin resultado (error de cálculo), **entonces** el indicador lo reporta con su `id_origen` y el ítem queda con `clasificacion_pendiente = sí`, lo que impide usarlo en comparaciones hasta que se calcule

### Escenario 7: Recalcular al cambiar los pares

- **Dado** que un ítem con `clasificacion = EQUIVALENTE` obtiene un nuevo par `MISMO_MODELO`, o pierde todos sus pares
- **Cuando** se recalcula su resultado
- **Entonces** se genera un nuevo resultado vigente (`MISMO_MODELO` o `INSUFICIENTE_NO_CONFIABLE`), el anterior se conserva como histórico con su fecha y versión de reglas, y sin cambios no se crea un nuevo resultado

### Escenario 8: Ítem que deja de estar activo

- **Dado** que un ítem objetivo pasa a `activo = no`
- **Cuando** se recalcula
- **Entonces** su resultado vigente pasa a `vigente = no` y el ítem deja de contar en el indicador de cobertura

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); Administrador (consulta el indicador de cobertura). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** ninguno para el proceso; el indicador es consultable por el Administrador.
- **Valor de negocio:** hace explícita la comparabilidad de cada ítem (KPI de comparabilidad, NFR-CAL-005).

### Reglas de Negocio

**RN-01 — Alcance.** Se calcula un resultado vigente por cada ítem objetivo: producto normalizado vigente y activo con `tipo_origen` `SECOP_II` o `TVEC`.

**RN-02 — Valores y etiquetas.** Lista cerrada:

| Valor | Etiqueta para el usuario |
|---|---|
| `MISMO_MODELO` | Mismo modelo |
| `EQUIVALENTE` | Producto equivalente |
| `INSUFICIENTE_NO_CONFIABLE` | Insuficiente / no confiable |

Ningún resultado puede ser nulo ni tener otro valor.

**RN-03 — Precedencia.** ≥ 1 par vigente `MISMO_MODELO` → `MISMO_MODELO`; si no, ≥ 1 par vigente `EQUIVALENTE` → `EQUIVALENTE`; si no → `INSUFICIENTE_NO_CONFIABLE`. Un mismo par nunca cuenta en dos tipos.

**RN-04 — Motivos de insuficiencia (lista cerrada, uno o varios).**

| Código | Texto legible |
|---|---|
| `SIN_ATRIBUTOS_MINIMOS` | No hay datos suficientes del televisor (tamaño, o marca y modelo) para compararlo. |
| `ATRIBUTOS_OBLIGATORIOS_FALTANTES` | Faltan características obligatorias para buscar equivalentes: {lista}. |
| `SIN_CANDIDATOS_QUE_CUMPLAN` | Ningún otro televisor cumple todos los criterios de equivalencia configurados. |
| `SOLO_PARES_EN_CONFLICTO` | Hay {n} productos con la misma marca y modelo pero con características contradictorias; requieren revisión. |
| `SIN_REGLAS_EQUIVALENCIA` | No hay reglas de equivalencia vigentes para esta categoría. |

Los motivos provienen de los resultados de mismo modelo y de equivalencia del ítem; se registran todos los que apliquen. En {lista} los atributos se muestran con su etiqueta legible, separados por coma: `tamano_pulgadas` → tamaño, `resolucion` → resolución, `tecnologia` → tecnología, `smart` → Smart, `generacion` → generación, `marca` → marca.

**RN-05 — Contenido del resultado.** `id_resultado`, `id_producto_objetivo`, `clasificacion`, `etiqueta`, conteos (`mismo_modelo`, `equivalente`, `conflicto`, `candidatos_evaluados`), `motivos` (códigos y textos), `resumen_criterios` (texto legible según RN-06), `version_reglas`, versión del producto, `fecha_calculo`, `vigente`, `clasificacion_pendiente`.

**RN-06 — Resumen de criterios.**
- `MISMO_MODELO`: "Mismo modelo: {n} productos con la misma marca y modelo ({marca} · {modelo})" y, si hay pares por EAN, "; {k} por código EAN/GTIN".
- `EQUIVALENTE`: "Producto equivalente: {n} productos con {criterios obligatorios y sus valores}; no evaluados: {lista o "ninguno"}". Si algún par tiene referencias de modelo distintas, se agrega "; incluye referencias de modelo distintas".
- `INSUFICIENTE_NO_CONFIABLE`: los textos de los motivos.
- El lenguaje es descriptivo y no acusatorio: describe comparabilidad de productos, nunca una conclusión sobre el contrato, la entidad o el proveedor.

**RN-07 — Cobertura (NFR-CAL-005).** Indicador consultable: ítems objetivo activos, ítems con resultado vigente, porcentaje (2 decimales) y lista de ítems sin resultado. Meta: 100 %. Un ítem sin resultado vigente queda `clasificacion_pendiente = sí` y no debe usarse en comparaciones.

**RN-08 — Recálculo e idempotencia.** Se recalcula cuando cambian los pares vigentes del ítem, su versión, su estado activo o la versión de reglas. El resultado anterior queda histórico (`vigente = no`, fecha). Sin cambios no se crea resultado nuevo. Un ítem inactivo deja su resultado como no vigente.

**RN-09 — Errores.** Un error al calcular un ítem no detiene el lote; se registra con su `id_origen`, el ítem queda `clasificacion_pendiente = sí` y se reintenta en la siguiente ejecución.

### Interfaz

Sin interfaz gráfica. Resultado e indicador consultables por consulta a la base o por los servicios que los consumen; la visualización para el Analista está en HU-040.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-035, HU-036 y HU-038 (generan los pares), HU-040 (muestra el resultado), HU-041 (verificación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-03):** la clasificación del ítem es la de mayor confianza disponible (mismo modelo > equivalente > insuficiente); qué pares usa cada benchmark se decide en el cálculo de benchmarks.
- **S-02 (Resuelto → RN-07):** un ítem sin clasificación vigente queda marcado como pendiente y no se usa en comparaciones, para garantizar el 100 % de NFR-CAL-005.

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
