# Historia #041: Verificar que ningún emparejamiento use criterios relajados

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Clasificar y Explicar el Emparejamiento  
**Prioridad:** Crítica  
**FRs relacionados:** FR-040, FR-039

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador (PO),  
**Quiero** una verificación periódica que compruebe que todos los emparejamientos vigentes cumplen exactamente los criterios configurados, retire los que no, y me entregue una muestra para revisión manual,  
**Para** demostrar que nunca se relajaron criterios para forzar una referencia (Adenda 2, A2.7) y medir la exactitud real de los emparejamientos.

## Descripción

FR-040 prohíbe relajar los criterios de equivalencia para forzar una referencia, y la épica exige que "ningún emparejamiento use criterios por debajo de los configurados" y que, en una muestra de 50 emparejamientos revisados a mano, ≥ 95 % de los "mismo modelo" y ≥ 90 % de los "equivalentes" sean correctos.

Esta HU agrega un **control de verificación** independiente del proceso que genera los pares: reevalúa cada par vigente contra sus reglas, cuenta y retira las violaciones, detecta pares calculados con reglas obsoletas y produce una **muestra de verificación** con registro del veredicto del Administrador y cálculo de exactitud. Capacidad administrativa: puede implementarse con script, consulta o reporte; no requiere pantalla.

---

## Criterios de Aceptación

### Escenario 1: Verificación sin violaciones

- **Dado** que todos los pares vigentes cumplen sus criterios
- **Cuando** se ejecuta la verificación
- **Entonces** se genera un reporte con fecha y hora, pares verificados por tipo, `violaciones = 0`, `pares_desactualizados = 0` y resultado "Conforme"

### Escenario 2: Par equivalente que no cumple un criterio obligatorio

- **Dado** que existe un par vigente `EQUIVALENTE` en el que un criterio obligatorio de su versión de reglas no se cumple (ej. 55" vs 58" con tamaño exacto) o tiene un dato desconocido
- **Cuando** se ejecuta la verificación
- **Entonces** el reporte lo lista como violación con el criterio, los valores y la versión de reglas; el par pasa a `vigente = no` con motivo `RETIRADO_POR_VERIFICACION`; el ítem se marca para recálculo de su clasificación; resultado "No conforme" y se genera una alerta al Administrador

### Escenario 3: Par evaluado con tolerancia mayor que la configurada

- **Dado** que un par `EQUIVALENTE` tiene una diferencia de generación de 2 años y su versión de reglas tiene tolerancia 1
- **Cuando** se ejecuta la verificación
- **Entonces** se registra como violación y se retira igual que en el Escenario 2

### Escenario 4: Par mismo modelo sin igualdad exacta

- **Dado** que un par vigente `MISMO_MODELO` no tiene igualdad exacta de marca y modelo normalizado ni de EAN, o tiene atributos de control contradictorios
- **Cuando** se ejecuta la verificación
- **Entonces** se registra como violación, el par se retira y el ítem se marca para recálculo

### Escenario 5: Pares calculados con reglas o productos obsoletos

- **Dado** que existen pares vigentes calculados con una versión de reglas anterior a la vigente o con una versión no vigente de alguno de sus productos
- **Cuando** se ejecuta la verificación
- **Entonces** se cuentan como `pares_desactualizados`, se listan y se marcan para recálculo (no se cuentan como violación)

### Escenario 6: Generar muestra de verificación manual

- **Dado** que hay al menos 25 pares vigentes `MISMO_MODELO` y 25 `EQUIVALENTE`
- **Cuando** el Administrador solicita una muestra de 50
- **Entonces** recibe 25 pares de cada tipo elegidos al azar, cada uno con la descripción original y los atributos de ambos productos, su tipo y sus criterios, y la muestra queda registrada con identificador, fecha y semilla aleatoria

### Escenario 7: Muestra con pocos pares de un tipo

- **Dado** que solo hay 10 pares vigentes `MISMO_MODELO`
- **Cuando** el Administrador solicita una muestra de 50
- **Entonces** la muestra incluye los 10 `MISMO_MODELO` y 40 `EQUIVALENTE` (o todos los disponibles si son menos), y el reporte indica "Muestra de mismo modelo menor a 25: {n}"

### Escenario 8: Registrar veredictos y calcular exactitud

- **Dado** que el Administrador registra para cada par de la muestra el veredicto "Correcto" o "Incorrecto" con comentario opcional
- **Cuando** consulta el resultado de la muestra
- **Entonces** obtiene la exactitud por tipo (correctos / revisados, 2 decimales) comparada con las metas configurables (mismo modelo ≥ 95 %, equivalente ≥ 90 %) y la indicación "Cumple" o "No cumple" por tipo
- **Y si** faltan veredictos, **entonces** el resultado indica "Muestra incompleta: {n} pares sin veredicto" y no calcula el cumplimiento

### Escenario 9: Permisos

- **Dado** que un Analista intenta ejecutar la verificación, generar una muestra o registrar veredictos
- **Cuando** lo intenta
- **Entonces** se rechaza por falta de permiso

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador para ejecutar la verificación, generar muestras y registrar veredictos.
- **Valor de negocio:** evidencia verificable de que las referencias no se fuerzan y medición de la exactitud del emparejamiento (criterios de aceptación de la épica, riesgo R2).

### Reglas de Negocio

**RN-01 — Alcance de la verificación.** Todos los pares vigentes `MISMO_MODELO` y `EQUIVALENTE` de todas las categorías con reglas.

**RN-02 — Reevaluación independiente.** Cada par se reevalúa con los valores de los productos en las versiones registradas en el par y con la versión de reglas registrada en el par:
- `EQUIVALENTE`: todo criterio `OBLIGATORIO` debe tener ambos valores conocidos y cumplir (igualdad en `EXACTO`; `|a − b| ≤ tolerancia` en `TOLERANCIA`); todo criterio `SI_AMBOS_CONOCIDOS` con ambos valores conocidos debe cumplir. Cualquier otro caso es violación.
- `MISMO_MODELO`: marca y `modelo_normalizado` no nulos y exactamente iguales, o `ean` no nulo y exactamente igual; y sin atributos de control (configuración inicial: tamaño, resolución, tecnología) conocidos y distintos; con criterio EAN, marcas conocidas iguales. Cualquier otro caso es violación.

**RN-03 — Tratamiento de violaciones.** Cada violación se registra (par, tipo, criterio, valores, versión de reglas, fecha) y el par pasa a `vigente = no` con motivo `RETIRADO_POR_VERIFICACION`; el ítem objetivo se marca para recalcular su clasificación en el siguiente emparejamiento. Si hay ≥ 1 violación, el resultado es "No conforme" y se genera una alerta al Administrador por el canal de alertas operativas configurado.

**RN-04 — Desactualizados.** Un par vigente cuya `version_reglas` no es la vigente de su categoría, o que referencia una versión no vigente de un producto, se cuenta como desactualizado, se lista y se marca para recálculo; no es violación.

**RN-05 — Reporte.** Fecha y hora de inicio y fin, pares verificados por tipo, violaciones (número y lista), desactualizados (número y lista), resultado ("Conforme" si violaciones = 0, si no "No conforme"). Los reportes se conservan y no se modifican.

**RN-06 — Frecuencia.** Se ejecuta automáticamente después de cada emparejamiento completo y a demanda por el Administrador.

**RN-07 — Muestra de verificación.** Tamaño configurable (**configuración inicial: 50**, mínimo 2, máximo 500), repartido en partes iguales entre `MISMO_MODELO` y `EQUIVALENTE` (con tamaño impar, el par extra va a `EQUIVALENTE`). Selección aleatoria simple sin reemplazo entre pares vigentes; si un tipo no alcanza su parte, se incluyen todos los de ese tipo, el faltante se completa con el otro tipo y se informa "Muestra de {tipo} menor a {parte}: {n}". Se registra identificador de muestra, fecha, usuario, semilla y lista de pares, con una copia de los datos mostrados de cada par en ese momento.

**RN-08 — Veredictos y exactitud.** Veredicto por par: "Correcto" o "Incorrecto", comentario opcional de hasta 500 caracteres, usuario y fecha. Un veredicto puede cambiarse; se conserva el historial. Exactitud por tipo = correctos / pares con veredicto del tipo, con 2 decimales. **Metas configurables: mismo modelo ≥ 95 %, equivalente ≥ 90 %.** Con pares sin veredicto: "Muestra incompleta: {n} pares sin veredicto", sin cálculo de cumplimiento. Un veredicto "Incorrecto" no modifica el par automáticamente; el Administrador decide el ajuste de reglas por el proceso de configuración.

**RN-09 — Validaciones.** Se rechaza con "Parámetro inválido: {detalle}": tamaño de muestra fuera de 2–500; metas fuera de 0–100 %; comentario de más de 500 caracteres; veredicto distinto de "Correcto"/"Incorrecto"; veredicto sobre un par que no pertenece a la muestra. Si no hay pares vigentes, la muestra no se genera y se informa "No hay emparejamientos vigentes para muestrear".

**RN-10 — Auditoría.** Ejecuciones de verificación, retiros de pares, generación de muestras y veredictos quedan registrados con usuario (o "sistema"), fecha y hora.

### Interfaz

Sin interfaz gráfica obligatoria: script, consulta o reporte (archivo o tabla) con los campos indicados; los veredictos pueden registrarse mediante archivo estructurado o interfaz mínima.

### Sistemas Externos (Si aplica)

No aplica. La alerta usa el canal de alertas operativas del sistema.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-035, HU-036 y HU-038 (pares verificados), HU-037 (reglas), HU-039 (recálculo de la clasificación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-03):** un par que viola los criterios se retira automáticamente (no se borra) y genera alerta; no se corrige "a mano".
- **S-02 (Resuelto → RN-07, RN-08):** la muestra de 50 del criterio de aceptación de la épica se reparte 25/25 entre tipos, con metas configurables ≥ 95 % y ≥ 90 %; un veredicto "Incorrecto" no cambia el par por sí solo.

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
