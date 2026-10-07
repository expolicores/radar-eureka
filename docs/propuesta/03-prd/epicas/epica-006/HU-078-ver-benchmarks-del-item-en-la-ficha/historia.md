# Historia #078: Ver los benchmarks de cada ítem con la distribución de precios comparables en la ficha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Consulta de la Ficha del Contrato  
**Prioridad:** Crítica  
**FRs relacionados:** FR-074

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la ficha, para cada ítem de televisor, el Benchmark 1 (compras públicas) con una visualización de la distribución de precios comparables y el Benchmark 2 (mercado) con su estado,  
**Para** entender dónde se ubica el precio contratado frente a otras compras públicas y frente al mercado, y con cuánta evidencia.

## Descripción

Esta HU construye la sección **"Benchmarks"** de la ficha del contrato (HU-076). Para cada ítem de televisor con precio unitario muestra:

- **Benchmark 1 – Compras públicas:** referencia estadística (mediana) cuando hay suficientes observaciones comparables, o "Referencia disponible" con evidencia limitada; número de observaciones por fuente (SECOP II / TVEC), ventana temporal usada, tipo de emparejamiento, base tributaria, desviación porcentual y una **visualización de la distribución** de precios unitarios comparables con el precio contratado marcado, acompañada de una tabla equivalente.
- **Benchmark 2 – Mercado:** referencia de mercado agregada, "Referencia de mercado disponible" o "No disponible / evidencia insuficiente", con número de observaciones y fuentes, métodos de adquisición y marca de observaciones manuales.

Los benchmarks los calcula el proceso de comparación de la plataforma con parámetros configurables (valores iniciales: ventana del Benchmark 1 de ±6 meses ampliable a ±12 meses; ventana del Benchmark 2 de ±30 días; mínimos de 5 observaciones para el Benchmark 1 y de 3 observaciones de al menos 2 fuentes para el Benchmark 2). Esta HU solo presenta esos resultados y los parámetros con que se calcularon; no calcula ni cambia parámetros.

---

## Criterios de Aceptación

### Escenario 1: Benchmark 1 con referencia estadística (happy path)

- **Dado** que un ítem tiene un Benchmark 1 calculado con un número de observaciones comparables igual o superior al mínimo configurado
- **Cuando** el Analista abre la sección "Benchmarks"
- **Entonces** ve para el ítem: "Benchmark 1 – Compras públicas", la mediana de referencia, el número de observaciones ("{n} observaciones: {a} SECOP II, {b} TVEC"), la ventana usada ("±6 meses desde la fecha de compra"), el tipo de emparejamiento, la base tributaria, la desviación del precio contratado ("+35,2 % frente a la mediana") y la visualización de la distribución

### Escenario 2: Visualización de la distribución

- **Dado** que el Benchmark 1 del ítem tiene observaciones comparables
- **Cuando** se muestra la visualización
- **Entonces** cada observación aparece como un punto sobre un eje de precio unitario en pesos, se marcan la mediana y el rango intercuartílico (Q1–Q3) cuando hay referencia estadística, y el precio contratado aparece con una marca distinta y la etiqueta "Precio contratado: {valor}"

### Escenario 3: Alternativa textual de la visualización

- **Dado** que la visualización está en pantalla
- **Cuando** el Analista activa "Ver como tabla" o usa un lector de pantalla
- **Entonces** dispone de una tabla con cada observación (fuente, entidad, fecha, precio unitario, tipo de emparejamiento) y de un resumen textual "Precio contratado {valor}; mediana {valor}; {n} observaciones entre {mínimo} y {máximo}"

### Escenario 4: Ventana ampliada

- **Dado** que el Benchmark 1 se calculó ampliando la ventana porque no había comparables suficientes en la ventana inicial
- **Cuando** se muestra el benchmark
- **Entonces** la ventana aparece como "±12 meses (ampliada por falta de comparables en ±6 meses)"

### Escenario 5: Benchmark 1 con evidencia limitada

- **Dado** que el número de observaciones comparables es menor que el mínimo configurado, pero mayor que cero
- **Cuando** se muestra el benchmark
- **Entonces** aparece "Referencia disponible — evidencia limitada ({n} de {mínimo} observaciones requeridas para una referencia estadística)", sin mediana ni rango intercuartílico, con las observaciones como puntos y en la tabla, y la desviación se muestra frente a cada observación en la tabla

### Escenario 6: Sin comparables en compras públicas

- **Dado** que no hay ninguna observación comparable en la ventana máxima
- **Cuando** se muestra el benchmark
- **Entonces** aparece "Benchmark 1 – Compras públicas: sin observaciones comparables en la ventana de ±12 meses." y no se muestra visualización

### Escenario 7: Comparación incompleta por base tributaria

- **Dado** que la base tributaria del precio contratado o de alguna observación usada es indeterminada
- **Cuando** se muestra el benchmark
- **Entonces** aparece la marca "Comparación incompleta / no confiable: base tributaria (IVA) indeterminada" junto al benchmark afectado

### Escenario 8: Benchmark 2 con referencia agregada de mercado

- **Dado** que el ítem tiene observaciones retail en la ventana configurada que cumplen el mínimo de observaciones y de fuentes
- **Cuando** se muestra el Benchmark 2
- **Entonces** aparece "Benchmark 2 – Mercado", la referencia agregada (mediana), "{n} observaciones de {f} fuentes", la ventana ("±30 días desde la fecha de compra"), la desviación y la lista de observaciones con fuente (Alkosto, Falabella), fecha de observación, precio efectivo y método de adquisición

### Escenario 9: Referencia de mercado disponible (evidencia limitada)

- **Dado** que hay observaciones retail válidas pero por debajo del mínimo
- **Cuando** se muestra el Benchmark 2
- **Entonces** aparece "Referencia de mercado disponible — evidencia limitada ({n} observaciones de {f} fuentes)", nunca "precio de mercado", con las observaciones listadas

### Escenario 10: Benchmark 2 no disponible

- **Dado** que no existe referencia retail confiable para el ítem (por ejemplo, una compra antigua)
- **Cuando** se muestra el Benchmark 2
- **Entonces** aparece "Benchmark 2 – Mercado: no disponible / evidencia insuficiente. No se usan precios actuales para juzgar compras antiguas." y el Benchmark 1 se muestra igual

### Escenario 11: Observaciones manuales y con condiciones especiales

- **Dado** que una observación de mercado se registró manualmente o tiene un precio sujeto a condiciones especiales
- **Cuando** se lista
- **Entonces** la observación manual muestra la marca "Observación manual" y la de condición especial la marca "Precio con condición especial ({condición})"

### Escenario 12: Ítem sin comparación calculada

- **Dado** que el ítem no tiene precio unitario o su comparación aún no se ha calculado
- **Cuando** se muestra la sección
- **Entonces** para ese ítem aparece "Comparación pendiente" o "Sin comparación: el ítem no tiene precio unitario disponible.", según el caso

### Escenario 13: Navegar a la observación de referencia

- **Dado** que una observación de la tabla tiene origen consultable
- **Cuando** el Analista activa la observación
- **Entonces** si es de compras públicas se abre la ficha del contrato u orden de origen, y si es de mercado se abre su detalle de evidencia (fuente, URL o referencia, fecha, captura)

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Ver la distribución de precios comparables es clave para entender el Benchmark 1 y juzgar si la desviación de un ítem merece revisión.

### Reglas de Negocio

- **RN-01 Datos mostrados:** se muestran los resultados del último cálculo de comparación de cada ítem, junto con los parámetros con que se calcularon (ventana, mínimo de observaciones). Los valores iniciales de esos parámetros son configurables y recalibrables; la ficha muestra los valores realmente usados.
- **RN-02 Referencia estadística del Benchmark 1:** mediana de las observaciones comparables, solo cuando el número de observaciones es ≥ al mínimo configurado (valor inicial 5). Q1 y Q3 se muestran en la visualización solo en ese caso.
- **RN-03 Evidencia limitada del Benchmark 1:** con 1 a (mínimo − 1) observaciones se muestra "Referencia disponible — evidencia limitada", sin mediana; la desviación se muestra por observación en la tabla.
- **RN-04 Ventana del Benchmark 1:** se muestra la ventana usada: "±6 meses desde la fecha de compra" (valor inicial) o "±12 meses (ampliada por falta de comparables en ±6 meses)" (ampliación inicial), según el cálculo.
- **RN-05 Benchmark 2:** referencia agregada solo con ≥ 3 observaciones de al menos 2 fuentes (valor inicial configurable) dentro de la ventana de ±30 días (valor inicial configurable); por debajo, "Referencia de mercado disponible — evidencia limitada"; sin referencia confiable, "no disponible / evidencia insuficiente". Nunca se usa el texto "precio de mercado" para evidencia limitada.
- **RN-06 Origen de cada observación:** compras públicas: fuente "SECOP II" o "TVEC", entidad, fecha de compra, precio unitario y tipo de emparejamiento. Mercado: fuente (Alkosto o Falabella), vendedor = la tienda, fecha de observación, precio efectivo, método de adquisición (API / dataset / feed / sitemap-datos estructurados / extracción web / manual) y marcas de RN-08.
- **RN-07 Tipo de emparejamiento:** "Mismo modelo" o "Producto equivalente", con los criterios usados (ej. "65", 4K UHD, LED, Smart"); las comparaciones "Insuficiente / no confiable" se muestran como tales y sin desviación.
- **RN-08 Marcas:** "Observación manual" para observaciones registradas manualmente; "Precio con condición especial ({tarjeta | cupón | financiación | membresía})", con la nota "No se usa como precio general de mercado" (estas observaciones se listan como evidencia pero no entran en la referencia agregada); "Comparación incompleta / no confiable: base tributaria (IVA) indeterminada" cuando corresponda.
- **RN-09 Desviación:** porcentaje con signo y una decimal frente a la referencia: `(precio contratado − referencia) / referencia × 100`, tal como lo calcula la plataforma. Se muestra la fórmula con los valores al activar "Ver fórmula".
- **RN-10 Visualización:** gráfico de puntos sobre un eje horizontal de precio unitario en pesos con escala que incluye el mínimo, el máximo y el precio contratado; marca de mediana y banda Q1–Q3 solo con referencia estadística; marca distintiva para el precio contratado; el color no es el único medio para distinguir marcas (forma y etiqueta). Con más de 200 observaciones, los puntos se superponen con transparencia sin ocultar la tabla.
- **RN-11 Tabla equivalente:** siempre disponible con "Ver como tabla"; ordenada por precio unitario ascendente; incluye la desviación del precio contratado frente a cada observación.
- **RN-12 Nulos:** observación sin entidad o fecha → "Sin dato"; ítem sin precio unitario → "Sin comparación: el ítem no tiene precio unitario disponible."; comparación no calculada aún → "Comparación pendiente".
- **RN-13 Lenguaje:** la desviación se presenta como dato; ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-14 Formatos y rendimiento:** pesos `$ 2.884.000`; porcentajes `+35,2 %`; fechas `DD/MM/AAAA`. La sección carga dentro del objetivo de la ficha de ≤ 3 segundos (p95) con 20 usuarios concurrentes (objetivo inicial de diseño).
- **RN-15 Accesibilidad y responsive (valores iniciales de diseño):** WCAG 2.1 AA; la visualización tiene título, resumen textual y tabla equivalente; contraste ≥ 3:1 para marcas gráficas; en móvil desde 360 px la visualización se ajusta al ancho y la tabla se desplaza horizontalmente sin perder columnas.

### Interfaz

- Sección "Benchmarks" con un bloque por ítem (encabezado con el producto normalizado).
- Subbloque "Benchmark 1 – Compras públicas": referencia o estado, observaciones por fuente, ventana, emparejamiento con criterios, base tributaria, desviación, "Ver fórmula", visualización de distribución, "Ver como tabla".
- Subbloque "Benchmark 2 – Mercado": referencia o estado, observaciones y fuentes, ventana, desviación, lista de observaciones con marcas.
- Observaciones activables para abrir la ficha del contrato de origen o el detalle de la observación de mercado.

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa los resultados de comparación, las observaciones de compras públicas (SECOP II, TVEC) y las observaciones de mercado (Alkosto, Falabella, incluidas las manuales) ya almacenadas por la plataforma.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-076 (estructura de la ficha), HU-077 (ítems), HU-079 (señales)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-10, RN-11):** la distribución del Benchmark 1 se visualiza como gráfico de puntos con mediana y Q1–Q3, siempre acompañado de tabla equivalente y resumen textual.
- **Resuelto (RN-01):** la ficha muestra los parámetros realmente usados en el cálculo (ventana, mínimos), que son configurables.
- **Resuelto (Escenario 13):** las observaciones públicas enlazan a la ficha del contrato de origen y las de mercado a su detalle de evidencia.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-006 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
