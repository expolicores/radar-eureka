# Historia #058: Calcular el Benchmark 2 – Mercado con degradación a "no disponible"

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Cálculo de Benchmarks  
**Prioridad:** Crítica  
**FRs relacionados:** FR-058, FR-059, FR-060, FR-061

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema calcule el Benchmark 2 – Mercado con las observaciones retail cercanas a la fecha de la compra, presentándolo como referencia estadística, como "referencia de mercado disponible" o como "no disponible / evidencia insuficiente" según la evidencia,  
**Para** contrastar el precio contratado con el mercado solo cuando hay evidencia confiable, sin que la falta de esa evidencia impida revisar el Benchmark 1.

## Descripción

El Benchmark 2 toma el conjunto de observaciones retail ya seleccionado (Alkosto, Falabella; ventana configurable ±30 días) y homologado a precio final con IVA. Si hay al menos el mínimo configurado (configuración inicial: **≥ 3 observaciones de al menos 2 fuentes**), calcula una **referencia estadística de mercado** (mediana, con cuartiles). Si hay menos, la presenta como **"referencia de mercado disponible"** con el número de observaciones y fuentes, nunca como "precio de mercado". Si no hay ninguna observación válida, el Benchmark 2 queda **"no disponible / evidencia insuficiente"**.

**Regla de degradación (Adenda 2, A2.7):** el estado del Benchmark 2 nunca bloquea, retrasa ni modifica el cálculo del Benchmark 1, ni la generación de señales a partir del Benchmark 1. Nunca se relajan criterios para producir una referencia de mercado.

---

## Criterios de Aceptación

### Escenario 1: Referencia estadística de mercado

- **Dado** que el ítem tiene precio contratado homologado de 2.300.000 COP y 4 observaciones de 2 fuentes: 1.799.900 (Alkosto), 1.849.900 (Alkosto), 1.899.900 (Falabella) y 1.949.900 (Falabella)
- **Cuando** el sistema calcula el Benchmark 2
- **Entonces** el estado es "Referencia estadística de mercado (4 observaciones de 2 fuentes)", la mediana es 1.874.900 COP, se muestran Q1, Q3 e IQR, y la desviación es "+22,7 %"

### Escenario 2: Referencia de mercado disponible por falta de fuentes

- **Dado** que hay 3 observaciones de Alkosto (1.800.000, 1.850.000, 1.900.000 COP) y ninguna de otra fuente, y el precio contratado es 2.405.000 COP
- **Cuando** el sistema calcula
- **Entonces** el estado es "Referencia de mercado disponible – evidencia limitada (3 observaciones de 1 fuente; mínimo 3 de 2 fuentes)", el valor de referencia es 1.850.000 COP, la desviación es "+30,0 %" y no se usa la expresión "precio de mercado"

### Escenario 3: Una observación manual

- **Dado** que hay 1 observación manual de Alkosto de 2.000.000 COP
- **Cuando** el sistema calcula
- **Entonces** el estado es "Referencia de mercado disponible – evidencia limitada (1 observación de 1 fuente; mínimo 3 de 2 fuentes)", la observación aparece con el indicador "Manual" y se calcula la desviación frente a 2.000.000 COP

### Escenario 4: Sin observaciones: Benchmark 2 no disponible y Benchmark 1 intacto

- **Dado** que el conjunto del Benchmark 2 está vacío y el Benchmark 1 del mismo ítem tiene "Referencia estadística"
- **Cuando** el sistema calcula ambos benchmarks
- **Entonces** el Benchmark 2 queda "No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)", sin referencia ni desviación, y el Benchmark 1 se calcula y queda disponible igual que si el Benchmark 2 no existiera

### Escenario 5: Ítem no elegible para el Benchmark 2

- **Dado** que el ítem quedó "Benchmark 2 no calculado" con motivo "Sin fecha de compra"
- **Cuando** el sistema calcula
- **Entonces** el Benchmark 2 queda "No disponible / evidencia insuficiente – Sin fecha de compra"

### Escenario 6: Falla del cálculo del Benchmark 2

- **Dado** que el cálculo del Benchmark 2 de un ítem falla por un error inesperado
- **Cuando** se ejecuta el proceso de cálculo
- **Entonces** el Benchmark 2 de ese ítem queda "No disponible / evidencia insuficiente – error de cálculo", el error se registra en el log con el identificador del ítem, y el Benchmark 1 y las señales derivadas de él se calculan y publican normalmente

### Escenario 7: Comparación incompleta por base tributaria

- **Dado** que la homologación marcó la comparación del Benchmark 2 como "Incompleta / no confiable: base tributaria indeterminada en 1 de 4 observaciones"
- **Cuando** el sistema calcula
- **Entonces** el resultado se calcula y conserva esa marca

### Escenario 8: Vínculo con cada observación y su método

- **Dado** que el Benchmark 2 se calculó con 4 observaciones
- **Cuando** se consulta el resultado
- **Entonces** se listan las 4 con identificador, origen "Retail – {tienda}", fecha de observación, precio efectivo original y homologado, método de adquisición e indicador "Manual" cuando aplique

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). Proceso automático.
- **Permisos requeridos:** Ninguno para el cálculo; parámetros solo por el Administrador.
- **Valor de negocio:** Aporta el contraste con el mercado en compras recientes sin comprometer la disponibilidad del análisis (la automatización retail no es condición de éxito del MVP).

### Reglas de Negocio

**RN-01 – Entrada.** Conjunto de observaciones retail seleccionado (ventana `b2_ventana_dias`, inicial 30) y homologado a precio final con IVA, en COP.

**RN-02 – Estados del Benchmark 2** (uno por ítem):
- "Referencia estadística de mercado ({n} observaciones de {f} fuentes)": n ≥ `b2_minimo_observaciones` (inicial 3) **y** f ≥ `b2_minimo_fuentes` (inicial 2).
- "Referencia de mercado disponible – evidencia limitada ({n} observación(es) de {f} fuente(s); mínimo {m} de {mf} fuentes)": n ≥ 1 sin cumplir lo anterior.
- "No disponible / evidencia insuficiente – {motivo}": n = 0 (motivo "sin observaciones de mercado en la ventana (±{D} días)"), ítem no elegible (motivo de elegibilidad) o error de cálculo (motivo "error de cálculo").

**RN-03 – Cálculos.** Mediana: valor central (n impar) o promedio de los dos centrales (n par), redondeo al peso entero. Cuartiles solo en "Referencia estadística de mercado", por interpolación lineal inclusiva: h = (n − 1) × p; Qp = x⌊h⌋ + (h − ⌊h⌋) × (x⌊h⌋+1 − x⌊h⌋); IQR = Q3 − Q1.

**RN-04 – Desviación (FR-061).** `(precio contratado homologado − referencia) / referencia × 100`, redondeada a 1 decimal (0,05 hacia arriba en valor absoluto), con signo. Se calcula en los dos primeros estados; no en "No disponible".

**RN-05 – Lenguaje (FR-059, A2.6).** La expresión "precio de mercado" no se usa en ningún estado. Las etiquetas permitidas son exactamente las de RN-02. En "Referencia de mercado disponible" no se muestran cuartiles y se agrega "Evidencia limitada: no es una referencia estadística robusta".

**RN-06 – Degradación (FR-060).** El Benchmark 1 y el Benchmark 2 se calculan de forma independiente. Ningún estado, demora o error del Benchmark 2 impide calcular, guardar o publicar el Benchmark 1 ni las señales del Benchmark 1. Un error de cálculo del Benchmark 2 se registra en el log (identificador del ítem, fecha-hora, descripción) y deja el estado "No disponible / evidencia insuficiente – error de cálculo".

**RN-07 – Marcas heredadas y vínculo (FR-058).** Se conservan: estado tributario, tipo de emparejamiento del conjunto, ventana usada y, por observación, identificador, origen "Retail – {tienda}", fecha, precio original y homologado, base, método de adquisición e indicador "Manual".

**RN-08 – Resultado almacenado.** Por ítem: estado, n, f, mínimos usados, mediana/Q1/Q3/IQR (si aplican), referencia, desviación, marcas, parámetros y fecha-hora. Cada cálculo reemplaza al vigente; las señales conservan su copia.

**RN-09 – Ejecución.** Mismos disparadores que el Benchmark 1, más el registro de nuevas observaciones de mercado. Asíncrono.

### Interfaz

Sin interfaz propia. Se muestra en el detalle de la señal (HU-063) y en la ficha del contrato.

### Sistemas Externos (Si aplica)

No consulta tiendas: usa solo la base propia de observaciones.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-055 (observaciones), HU-056 (base tributaria), HU-057 (Benchmark 1), HU-059 (señal).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Error técnico del Benchmark 2 tratado como "no disponible"** para no bloquear el Benchmark 1: resuelto en RN-06.
- **Cuartiles también en el Benchmark 2** cuando la referencia es estadística (los necesita la regla de atípicos): resuelto en RN-03.

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
