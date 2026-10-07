# Historia #060: Dirigir los precios anormalmente bajos a la cola de revisión de calidad

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Generación y Confianza de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-063

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador (que actúa como Revisor en el MVP),  
**Quiero** que los ítems cuyo precio unitario está anormalmente por debajo de la referencia lleguen a la cola de revisión de calidad en lugar de generar una señal,  
**Para** detectar y corregir posibles errores de extracción, cantidad, normalización, producto o base tributaria antes de que contaminen los benchmarks.

## Descripción

Por decisión P-04, en el MVP **solo las desviaciones al alza generan señal**. Un precio muy por debajo de la referencia suele indicar un problema del dato (ej. se leyó el precio sin IVA, se tomó el valor de un accesorio, la cantidad está mal o el producto no es comparable). Esta HU detecta esos casos con una regla simétrica a la de señales (configurable por separado) y crea un elemento en la **cola de revisión humana** con tipo "Precio anormalmente bajo frente a referencia". Nunca se crea una señal por un precio bajo.

La regla puede ejecutarse sin interfaz gráfica: el elemento queda en la cola de revisión existente, que el Administrador consulta por el medio definido para esa cola (interfaz mínima, consulta o reporte).

---

## Criterios de Aceptación

### Escenario 1: Precio bajo por regla de atípicos

- **Dado** que el Benchmark 1 del ítem tiene "Referencia estadística" homogénea con Q1 = 1.950.000 e IQR = 300.000 COP (límite inferior 1.500.000) y el precio contratado es 1.450.000 COP
- **Cuando** el sistema evalúa los precios bajos
- **Entonces** se crea un elemento en la cola de revisión con tipo "Precio anormalmente bajo frente a referencia", regla "Valor atípico inferior: precio < Q1 − 1,5 × IQR (límite 1.500.000 COP)", desviación "−31,0 %", y no se genera ninguna señal

### Escenario 2: Precio igual al límite inferior

- **Dado** el caso del escenario 1 con precio 1.500.000 COP
- **Cuando** el sistema evalúa
- **Entonces** no se crea elemento en la cola

### Escenario 3: Umbral porcentual con mismo modelo

- **Dado** que el benchmark tiene "Referencia disponible – evidencia limitada" de mismo modelo con referencia 2.000.000 COP
- **Cuando** el sistema evalúa con precio 1.400.000 COP (−30,0 %) y con 1.402.000 COP (−29,9 %)
- **Entonces** con 1.400.000 se crea elemento con regla "Umbral porcentual: mismo modelo ≤ −30 %" y con 1.402.000 no

### Escenario 4: Umbral porcentual con producto equivalente

- **Dado** que el conjunto es "Producto equivalente" con referencia 2.000.000 COP
- **Cuando** el sistema evalúa con precio 1.000.000 COP (−50,0 %) y 1.300.000 COP (−35,0 %)
- **Entonces** solo con 1.000.000 se crea elemento

### Escenario 5: Sin duplicados

- **Dado** que ya existe un elemento abierto para el mismo ítem y benchmark
- **Cuando** un recálculo vuelve a cumplir la condición
- **Entonces** no se crea un elemento nuevo; se actualizan los valores (referencia, desviación, regla, fecha de última evaluación) del elemento abierto

### Escenario 6: Cierre automático

- **Dado** que existe un elemento abierto y, tras un recálculo, el precio ya no cumple la condición
- **Cuando** el sistema reevalúa
- **Entonces** el elemento se cierra con la resolución "Cerrado automáticamente: ya no cumple la condición tras el recálculo del {AAAA-MM-DD}"

### Escenario 7: Benchmark sin referencia

- **Dado** que el benchmark del ítem está "Sin comparables públicos" o "No disponible / evidencia insuficiente"
- **Cuando** el sistema evalúa
- **Entonces** no se crea ningún elemento

### Escenario 8: Marca visible en el benchmark

- **Dado** que un ítem tiene un elemento abierto de precio anormalmente bajo en el Benchmark 1
- **Cuando** se consulta el resultado del Benchmark 1 de ese ítem
- **Entonces** el resultado muestra la marca "En revisión de calidad: precio anormalmente bajo frente a la referencia" y no muestra ninguna señal asociada a esa desviación

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador / Revisor (único usuario del MVP con acceso a la cola de revisión).
- **Permisos requeridos:** Rol Administrador para ver la cola. La detección es automática.
- **Valor de negocio:** Protege la calidad del Benchmark 1 y evita que errores de datos se presenten como evidencia.

### Reglas de Negocio

**RN-01 – Alcance.** Se evalúa cada par (ítem, benchmark) con referencia ("Referencia estadística", "Referencia estadística de mercado", "Referencia disponible – evidencia limitada", "Referencia de mercado disponible – evidencia limitada"). Sin referencia → no se evalúa.

**RN-02 – Aplicabilidad de la regla de atípicos.** Igual que para señales: benchmark en estado de referencia estadística; todas las observaciones con el mismo tipo individual de emparejamiento; estado tributario "Completa"; IQR > 0; `calidad_bajo_atipicos_habilitada` = sí. Si no se cumple, se usa la regla de umbrales.

**RN-03 – Regla de atípicos inferior.** Límite inferior = Q1 − `calidad_bajo_factor_iqr` × IQR, redondeado al peso entero. Condición: precio contratado homologado < límite inferior (estricto). Si el límite es ≤ 0, la regla de atípicos no puede cumplirse y no se crea elemento por esa vía.

**RN-04 – Regla de umbrales.** Condición: desviación redondeada a 1 decimal ≤ −`calidad_bajo_umbral_mismo_modelo` (conjunto "Mismo modelo") o ≤ −`calidad_bajo_umbral_equivalente` (conjunto "Producto equivalente").

**RN-05 – Parámetros configurables** (independientes de los de señal):

| Parámetro | Configuración inicial | Rango |
|---|---|---|
| `calidad_bajo_atipicos_habilitada` | sí | sí / no |
| `calidad_bajo_factor_iqr` | 1,5 | 0,5 a 5,0 |
| `calidad_bajo_umbral_mismo_modelo` | 30 (%) | 1 a 99, entero |
| `calidad_bajo_umbral_equivalente` | 50 (%) | 1 a 99, entero |

Valor faltante o inválido → configuración inicial y advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

**RN-06 – Elemento en la cola.** Campos: tipo "Precio anormalmente bajo frente a referencia"; ítem; contrato SECOP II u orden TVEC; benchmark; precio contratado homologado; tipo de precio (`explicito`/`derivado`); referencia; desviación; regla aplicada ("Valor atípico inferior: precio < Q1 − {k} × IQR (límite {valor} COP)" o "Umbral porcentual: mismo modelo ≤ −{u} %" / "producto equivalente ≤ −{u} %"); texto fijo de posibles causas: "Posibles causas a verificar: error de extracción, cantidad, normalización, producto diferente o base tributaria distinta"; estado "Abierto"; fecha de creación y de última evaluación.

**RN-07 – Unicidad.** Máximo un elemento abierto por (ítem, benchmark). Si existe, se actualiza (RN-06) en vez de crear otro.

**RN-08 – Cierre automático.** Si un elemento abierto ya no cumple la condición o el benchmark queda sin referencia, se cierra con la resolución "Cerrado automáticamente: ya no cumple la condición tras el recálculo del {AAAA-MM-DD}". La resolución manual del elemento (corregir el dato, confirmar o descartar) se hace con los mecanismos de revisión de datos existentes y está fuera de esta HU.

**RN-09 – Nunca señal.** Un precio por debajo de la referencia no genera señal en ningún caso. El resultado del benchmark muestra la marca "En revisión de calidad: precio anormalmente bajo frente a la referencia" mientras exista un elemento abierto.

**RN-10 – Ejecución.** Después de cada cálculo de benchmarks. Asíncrono.

### Interfaz

Sin interfaz propia. Los elementos se agregan a la cola de revisión humana existente; la marca se muestra donde se presenta el benchmark.

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

**Historias relacionadas:** HU-057, HU-058 (benchmarks), HU-059 (regla al alza).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Definición de "precio anormalmente bajo"**: el PRD no fija un criterio; se resuelve con una regla simétrica a la de señales (Q1 − 1,5 × IQR; −30 % mismo modelo; −50 % equivalente) con parámetros propios configurables (RN-02 a RN-05).
- **Unicidad y cierre automático** del elemento de cola: resuelto en RN-07/RN-08.

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
