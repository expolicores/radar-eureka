# Historia #054: Seleccionar comparables públicos del Benchmark 1 con ventana temporal configurable

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Selección de Comparables  
**Prioridad:** Crítica  
**FRs relacionados:** FR-055, FR-062

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema seleccione, para cada ítem de televisor, las otras compras públicas comparables (SECOP II y TVEC) según el tipo de emparejamiento y una ventana temporal configurable,  
**Para** que el Benchmark 1 compare el precio contratado solo contra compras del mismo producto o de un producto equivalente realizadas en un período cercano, con el origen de cada observación identificado.

## Descripción

El Benchmark 1 – Contratación pública es la referencia principal del MVP (la TVEC es su base principal). Esta HU define **qué observaciones entran** en el conjunto de comparables de un ítem; el cálculo de la referencia estadística, de la desviación y de la señal se hace en otras HUs de esta épica que consumen este conjunto.

La selección es escalonada: primero se busca el **mismo modelo** en la ventana inicial (configuración inicial: ±6 meses desde la fecha de la compra); si no alcanza el mínimo configurado de comparables, se amplía la ventana hasta la ventana máxima (configuración inicial: ±12 meses) y luego se incorporan **productos equivalentes**. Nunca se usan emparejamientos clasificados como *insuficiente/no confiable* ni se relajan los criterios de equivalencia para forzar una referencia (Adenda 2, A2.7). Cada observación seleccionada queda identificada como contratación pública de **SECOP II** o de **TVEC** (FR-062).

Los valores de ventana y mínimo son **parámetros configurables** (P-01, P-02); no son reglas estadísticas universales y se recalibran con evidencia real.

---

## Criterios de Aceptación

### Escenario 1: Selección con mismo modelo suficiente en la ventana inicial

- **Dado** que existe un ítem objetivo elegible con fecha de compra 2025-06-15 y hay 6 ítems públicos de **mismo modelo** con fechas entre 2024-12-15 y 2025-12-15 (ventana inicial ±6 meses)
- **Cuando** el sistema ejecuta la selección de comparables del Benchmark 1
- **Entonces** el conjunto contiene esos 6 ítems, el tipo de emparejamiento del conjunto es "Mismo modelo", la ventana aplicada es "±6 meses", y cada observación registra su origen ("Contratación pública – SECOP II" o "Contratación pública – TVEC")

### Escenario 2: Ampliación de la ventana cuando faltan comparables de mismo modelo

- **Dado** que el ítem objetivo tiene 3 comparables de mismo modelo en ±6 meses y 5 en ±12 meses, con mínimo configurado de 5
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto contiene los 5 comparables de mismo modelo en ±12 meses, la ventana aplicada es "±12 meses (ampliada)" y el tipo es "Mismo modelo"

### Escenario 3: Incorporación de productos equivalentes cuando el mismo modelo no alcanza el mínimo

- **Dado** que el ítem objetivo tiene 2 comparables de mismo modelo en ±12 meses y, sumando productos equivalentes, 4 en ±6 meses y 7 en ±12 meses, con mínimo 5
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto contiene los 7 comparables (mismo modelo + equivalentes) de la ventana ±12 meses, la ventana aplicada es "±12 meses (ampliada)" y el tipo de emparejamiento del conjunto es "Producto equivalente"

### Escenario 4: Ningún paso alcanza el mínimo pero hay comparables

- **Dado** que el ítem objetivo tiene 2 comparables de mismo modelo en ±12 meses y 4 (mismo modelo + equivalentes) en ±12 meses, con mínimo 5
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto contiene los 2 comparables de mismo modelo en ±12 meses, el tipo es "Mismo modelo", la ventana aplicada es "±12 meses (ampliada)" y el conjunto queda marcado "Por debajo del mínimo configurado (2 de 5)"

### Escenario 5: Sin comparables

- **Dado** que el ítem objetivo no tiene ningún ítem público de mismo modelo ni equivalente en ±12 meses
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto queda vacío, con estado "Sin comparables públicos en la ventana máxima (±12 meses)", y no se produce ningún error de proceso

### Escenario 6: Exclusión del propio ítem y de su mismo contrato u orden

- **Dado** que el contrato SECOP II del ítem objetivo contiene otro ítem de televisor del mismo modelo
- **Cuando** el sistema ejecuta la selección
- **Entonces** ni el ítem objetivo ni ningún otro ítem del mismo contrato (o de la misma orden de compra TVEC) aparece en el conjunto de comparables

### Escenario 7: Exclusión de emparejamientos insuficientes y de ítems no confirmados

- **Dado** que existen ítems públicos en la ventana cuyo emparejamiento con el ítem objetivo es "Insuficiente/no confiable", ítems con clasificación "excluido" o "requiere revisión", e ítems con datos extraídos "pendientes de revisión" o "rechazados"
- **Cuando** el sistema ejecuta la selección
- **Entonces** ninguno de esos ítems entra al conjunto, y el registro de la selección indica cuántos se descartaron por cada motivo

### Escenario 8: Ítem objetivo no elegible

- **Dado** que el ítem objetivo no tiene precio unitario, tiene precio unitario menor o igual a 0, no tiene fecha de compra, tiene datos pendientes de revisión, o su producto normalizado está marcado como "Insuficiente/no confiable" para emparejamiento
- **Cuando** el sistema intenta la selección
- **Entonces** no se construye conjunto y el ítem queda con el estado "Benchmark 1 no calculado" y el motivo exacto: "Sin precio unitario", "Precio unitario inválido", "Sin fecha de compra", "Datos pendientes de revisión" o "Emparejamiento insuficiente"

### Escenario 9: Cambio de parámetros de ventana o mínimo

- **Dado** que el Administrador cambió la ventana inicial de 6 a 4 meses y el mínimo de 5 a 6
- **Cuando** se ejecuta el siguiente recálculo
- **Entonces** la selección usa los nuevos valores y el registro de la selección guarda los parámetros vigentes usados (ventana inicial, ventana máxima, mínimo)

### Escenario 10: Comparable en el límite exacto de la ventana

- **Dado** que el ítem objetivo tiene fecha de compra 2025-06-15 y existe un comparable con fecha 2024-12-15 y otro con fecha 2024-12-14
- **Cuando** el sistema aplica la ventana ±6 meses
- **Entonces** el comparable del 2024-12-15 entra (límite inclusivo) y el del 2024-12-14 no entra en ese paso

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). La selección es un proceso automático del sistema; no requiere acción del usuario.
- **Permisos requeridos:** Ninguno para la ejecución automática. Los parámetros los modifica únicamente el rol Administrador mediante la configuración analítica.
- **Valor de negocio:** Sin un conjunto de comparables correcto, la referencia y la señal pierden sustento; esta selección es la base de la credibilidad del Benchmark 1 (riesgo de falsos positivos R2).

### Reglas de Negocio

**RN-01 – Ítem objetivo elegible.** Un ítem de televisor es elegible para el Benchmark 1 solo si cumple todas estas condiciones:
1. Clasificación "incluido" (confirmado como televisor dentro del límite de categoría).
2. Precio unitario no nulo y mayor que 0 COP, de tipo `explicito` o `derivado`.
3. Datos del ítem en estado "aceptado automáticamente", "validado por revisor" o "corregido por revisor" (o estructurados de origen en la TVEC). Ítems "pendientes de revisión" o "rechazados" no son elegibles.
4. Fecha de compra no nula.
Si no cumple, se registra el estado "Benchmark 1 no calculado" con el primer motivo que aplique, en este orden: "Sin precio unitario" (nulo o ítem marcado "información insuficiente"), "Precio unitario inválido" (≤ 0), "Datos pendientes de revisión", "Sin fecha de compra", "Emparejamiento insuficiente" (el producto normalizado del ítem objetivo está marcado por el módulo de emparejamiento como "insuficiente/no confiable", es decir, sin atributos mínimos para emparejarse con ningún otro producto).

**RN-02 – Fecha de la compra.** Para SECOP II es la `fecha_de_firma` del contrato; para TVEC es la fecha de la orden de compra. Formato AAAA-MM-DD. No se usa ninguna otra fecha como sustituto.

**RN-03 – Universo de comparables.** Son candidatos los ítems públicos de SECOP II y TVEC que cumplen RN-01 (puntos 1 a 4), distintos del ítem objetivo y que no pertenecen al mismo contrato SECOP II ni a la misma orden TVEC del ítem objetivo.

**RN-04 – Tipo de emparejamiento.** Se usa la clasificación de emparejamiento entre productos normalizados (mismo modelo / producto equivalente / insuficiente-no confiable) que produce el módulo de normalización y emparejamiento. Esta HU no recalcula ni relaja esa clasificación. Los pares "insuficiente/no confiable" nunca entran.

**RN-05 – Parámetros configurables** (leídos de la configuración analítica en cada ejecución):

| Parámetro | Configuración inicial | Rango permitido |
|---|---|---|
| `b1_ventana_inicial_meses` | 6 | 1 a 24, entero |
| `b1_ventana_maxima_meses` | 12 | ≥ ventana inicial y ≤ 36, entero |
| `b1_minimo_observaciones` | 5 | 1 a 50, entero |

Si un parámetro falta o está fuera de rango, se usa la configuración inicial y se registra una advertencia en el log de la ejecución ("Parámetro {nombre} inválido; se usó el valor inicial {valor}").

**RN-06 – Ventana temporal.** Ventana de N meses = intervalo cerrado [fecha de compra − N meses calendario, fecha de compra + N meses calendario]. Incluye comparables anteriores y posteriores. Si el día no existe en el mes destino (ej. 31), se usa el último día de ese mes.

**RN-07 – Selección escalonada.** Se evalúan los pasos en este orden y se usa el **primero** cuyo conjunto alcance `b1_minimo_observaciones`:
1. Mismo modelo, ventana inicial.
2. Mismo modelo, ventana máxima.
3. Mismo modelo + producto equivalente, ventana inicial.
4. Mismo modelo + producto equivalente, ventana máxima.
Si ningún paso alcanza el mínimo: se usa el paso 2 si tiene al menos 1 observación; si no, el paso 4 si tiene al menos 1 observación; si ambos están vacíos, el conjunto queda vacío con estado "Sin comparables públicos en la ventana máxima (±{N} meses)".

**RN-08 – Tipo de emparejamiento del conjunto.** "Mismo modelo" si todas las observaciones son de mismo modelo; "Producto equivalente" si al menos una es equivalente. Cada observación conserva además su propio tipo.

**RN-09 – Origen de cada observación (FR-062).** Cada observación del conjunto registra: origen = "Contratación pública – SECOP II" o "Contratación pública – TVEC"; identificador de origen (`id_contrato` o número de orden TVEC y línea), entidad, fecha de compra, precio unitario, tipo de precio unitario (`explicito`/`derivado`), base tributaria declarada y tipo de emparejamiento con el ítem objetivo.

**RN-10 – Ponderación.** Cada línea de ítem es una observación, independientemente de la cantidad comprada. No se pondera por cantidad ni por valor.

**RN-11 – Registro de la selección.** Por cada ítem objetivo se guarda: paso usado (1–4), ventana aplicada (texto "±N meses" y si fue ampliada), mínimo configurado, número de observaciones, si quedó por debajo del mínimo, parámetros usados, conteo de descartes por motivo (emparejamiento insuficiente, no incluido, pendiente/rechazado, fuera de ventana, mismo contrato/orden) y fecha-hora de la ejecución.

**RN-12 – Recalculo.** La selección se recalcula para todos los ítems elegibles después de: (a) cada ciclo de ingesta o extracción que agregue o modifique ítems; (b) cada corrección validada de un dato de ítem o de un emparejamiento; (c) cada cambio de los parámetros de RN-05; (d) una ejecución manual lanzada por el Administrador. La selección más reciente reemplaza a la anterior para el cálculo vigente; las señales ya emitidas conservan su propia evidencia (se gestiona en la HU de registro de evidencia).

**RN-13 – Base tributaria.** Esta HU no filtra por base tributaria; la homologación de IVA y el marcado de comparaciones incompletas se aplican después sobre el conjunto seleccionado (HU-056).

### Interfaz

Sin interfaz propia: es un proceso automático. El resultado (conjunto, ventana, tipo y origen de cada observación) se muestra al Analista en el detalle de la señal (HU-063).

### Sistemas Externos (Si aplica)

No consume sistemas externos en tiempo de ejecución. Usa los datos ya ingeridos de SECOP II (`jbjy-vk9h`) y TVEC (`usqp-5nsn` / `3hdv-smhz` / `rgxm-mmea`), los ítems extraídos y la clasificación de emparejamiento almacenados en el sistema.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-056 (homologación de base tributaria), HU-057 (cálculo del Benchmark 1), HU-063 (detalle de la señal).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Orden de la selección escalonada** (primero mismo modelo y ventana, luego equivalentes): resuelto en RN-07, coherente con la prioridad de emparejamiento del Brief (mismo modelo antes que equivalente).
- **Exclusión del mismo contrato/orden** para evitar autocomparación: resuelto en RN-03.
- **Sin ponderación por cantidad**: resuelto en RN-10.
- **Fecha de compra** (firma en SECOP II, orden en TVEC): resuelto en RN-02.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-005 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
