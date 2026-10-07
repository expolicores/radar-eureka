# Historia #057: Calcular el Benchmark 1 – Contratación pública y la desviación del precio contratado

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Cálculo de Benchmarks  
**Prioridad:** Crítica  
**FRs relacionados:** FR-054, FR-058, FR-059, FR-061

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema calcule para cada ítem de televisor con precio unitario la distribución de precios de compras públicas comparables, una referencia estadística (mediana) cuando haya observaciones suficientes, y la desviación porcentual del precio contratado,  
**Para** saber cuánto se aleja ese precio de lo que pagaron otras entidades por el mismo producto o uno equivalente, sabiendo si la referencia es robusta o solo evidencia limitada.

## Descripción

El Benchmark 1 toma el conjunto de comparables públicos ya seleccionado (SECOP II + TVEC, por emparejamiento y ventana temporal) y ya homologado a precio final con IVA, y calcula:
- la **distribución**: número de observaciones, mínimo, Q1, mediana, Q3, rango intercuartílico (IQR) y máximo;
- la **referencia**: la mediana. Si hay al menos el mínimo configurado de observaciones (configuración inicial: ≥ 5), es una **referencia estadística**; si hay menos, se presenta como **"referencia disponible – evidencia limitada"**, nunca como referencia estadística robusta;
- la **desviación porcentual** del precio contratado frente a la referencia: `(precio contratado − referencia) / referencia × 100`.

Cada resultado conserva el vínculo con cada observación usada. No se calcula un promedio simple por entidad (revisión de la Ecuación 2 de la tesis): la unidad es el ítem.

---

## Criterios de Aceptación

### Escenario 1: Referencia estadística con muestra suficiente

- **Dado** que el ítem tiene precio contratado homologado de 2.450.000 COP y 7 comparables homologados: 1.800.000, 1.900.000, 2.000.000, 2.100.000, 2.200.000, 2.300.000 y 2.400.000 COP, con mínimo 5
- **Cuando** el sistema calcula el Benchmark 1
- **Entonces** el estado es "Referencia estadística", n = 7, mínimo 1.800.000, Q1 1.950.000, mediana 2.100.000, Q3 2.250.000, IQR 300.000, máximo 2.400.000, y la desviación es "+16,7 %"

### Escenario 2: Número par de observaciones

- **Dado** que hay 6 comparables: 1.800.000, 1.900.000, 2.000.000, 2.300.000, 2.400.000 y 2.500.000 COP y el precio contratado es 2.450.000 COP
- **Cuando** el sistema calcula
- **Entonces** la mediana es 2.150.000 COP y la desviación es "+14,0 %"

### Escenario 3: Referencia disponible por debajo del mínimo

- **Dado** que hay 3 comparables (1.900.000, 2.000.000 y 2.100.000 COP), mínimo 5, y el precio contratado es 2.600.000 COP
- **Cuando** el sistema calcula
- **Entonces** el estado es "Referencia disponible – evidencia limitada (3 de 5 observaciones mínimas)", el valor de referencia es 2.000.000 COP, la desviación es "+30,0 %", se listan las 3 observaciones y no se presentan Q1, Q3 ni IQR

### Escenario 4: Una sola observación

- **Dado** que hay 1 comparable de 2.000.000 COP y el precio contratado es 1.700.000 COP
- **Cuando** el sistema calcula
- **Entonces** el estado es "Referencia disponible – evidencia limitada (1 de 5 observaciones mínimas)", la referencia es 2.000.000 COP y la desviación es "−15,0 %"

### Escenario 5: Sin comparables

- **Dado** que el conjunto de comparables está vacío
- **Cuando** el sistema calcula
- **Entonces** el estado es "Sin comparables públicos", no hay referencia ni desviación, y el resultado no produce error

### Escenario 6: Ítem no elegible

- **Dado** que el ítem quedó "Benchmark 1 no calculado" con motivo "Sin precio unitario"
- **Cuando** el sistema ejecuta el cálculo
- **Entonces** no se calcula el benchmark y se conserva el estado y el motivo

### Escenario 7: Comparación incompleta por base tributaria

- **Dado** que la homologación marcó la comparación como "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones"
- **Cuando** el sistema calcula
- **Entonces** calcula la distribución, la referencia y la desviación con normalidad y el resultado conserva esa marca textual

### Escenario 8: Vínculo con cada observación

- **Dado** que el Benchmark 1 se calculó con 7 observaciones
- **Cuando** se consulta el resultado
- **Entonces** el resultado lista los 7 identificadores de observación con su origen (SECOP II / TVEC), precio original, precio homologado y tipo de emparejamiento

### Escenario 9: Recalculo con nuevo mínimo

- **Dado** que el Administrador cambia `b1_minimo_observaciones` de 5 a 8 y el ítem del escenario 1 tiene 7 observaciones
- **Cuando** se ejecuta el recálculo
- **Entonces** el estado pasa a "Referencia disponible – evidencia limitada (7 de 8 observaciones mínimas)"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). Proceso automático.
- **Permisos requeridos:** Ninguno para el cálculo. Los parámetros los cambia el Administrador.
- **Valor de negocio:** El Benchmark 1 es la referencia principal del histórico de 3 años; sin él no hay señal explicable.

### Reglas de Negocio

**RN-01 – Entrada.** Se calcula para cada ítem de televisor con precio unitario que tenga un conjunto de comparables públicos seleccionado (por emparejamiento y ventana) y homologado a precio final con IVA. Todos los cálculos usan **valores homologados** en COP.

**RN-02 – Estados del Benchmark 1** (uno por ítem):
- "Referencia estadística": n ≥ `b1_minimo_observaciones` (configuración inicial 5).
- "Referencia disponible – evidencia limitada ({n} de {m} observaciones mínimas)": 1 ≤ n < m.
- "Sin comparables públicos": n = 0.
- "Benchmark 1 no calculado – {motivo}": ítem no elegible (motivos: Sin precio unitario, Precio unitario inválido, Datos pendientes de revisión, Sin fecha de compra, Emparejamiento insuficiente).

**RN-03 – Mediana.** Con n impar, el valor central ordenado; con n par, el promedio de los dos centrales. Se redondea al peso entero (0,5 hacia arriba).

**RN-04 – Cuartiles** (solo en "Referencia estadística"). Percentil por interpolación lineal inclusiva: valores ordenados x₀…xₙ₋₁; posición h = (n − 1) × p; Qp = x⌊h⌋ + (h − ⌊h⌋) × (x⌊h⌋+1 − x⌊h⌋). Q1 con p = 0,25; Q3 con p = 0,75; IQR = Q3 − Q1. Redondeo al peso entero.

**RN-05 – Desviación porcentual (FR-061).** `desviación = (precio contratado homologado − referencia) / referencia × 100`. Se redondea a 1 decimal (0,05 hacia arriba en valor absoluto) y se muestra con signo ("+16,7 %", "−15,0 %", "0,0 %"). El valor redondeado es el que usan las reglas de señal. Se calcula en "Referencia estadística" y en "Referencia disponible"; no en los demás estados. La referencia nunca es 0 porque las observaciones con precio ≤ 0 no entran al conjunto.

**RN-06 – Presentación por debajo del mínimo (FR-059).** En "Referencia disponible" no se muestran Q1, Q3 ni IQR; se listan todas las observaciones, el número de observaciones y el texto "Evidencia limitada: no es una referencia estadística robusta".

**RN-07 – Marcas heredadas.** El resultado conserva: el estado tributario de la homologación (completa/incompleta), el tipo de emparejamiento del conjunto, la ventana aplicada (y si fue ampliada) y si quedó por debajo del mínimo.

**RN-08 – Vínculo con observaciones (FR-058).** El resultado guarda, por observación: identificador, origen ("Contratación pública – SECOP II" / "Contratación pública – TVEC"), precio original, base original, precio homologado, tipo de emparejamiento y fecha.

**RN-09 – Resultado almacenado.** Por ítem: estado, n, mínimo, Q1, mediana, Q3, IQR, máximo (los que apliquen), referencia, desviación, marcas de RN-07, parámetros usados y fecha-hora del cálculo. Cada cálculo reemplaza al vigente del ítem; las señales conservan su propia copia de evidencia.

**RN-10 – Ejecución.** Se ejecuta después de cada selección y homologación de comparables (mismos disparadores: ingesta/extracción, correcciones validadas, nuevas observaciones, cambio de parámetros, ejecución manual del Administrador). Es asíncrono y no bloquea al usuario.

### Interfaz

Sin interfaz propia. Los resultados se muestran en el detalle de la señal (HU-063) y en la ficha del contrato.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-054 (comparables), HU-056 (base tributaria), HU-059 (señal), HU-060 (precios bajos), HU-061 (confianza).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Método de cuartiles** (interpolación lineal inclusiva): resuelto en RN-04 para que la regla de atípicos sea reproducible.
- **Desviación también con evidencia limitada**, frente a la mediana de las observaciones disponibles (FR-061 exige desviación frente a cada referencia disponible): resuelto en RN-05/RN-06.
- **Redondeo** de valores (peso entero) y desviación (1 decimal, usado por las reglas de señal): resuelto en RN-03 a RN-05.

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
