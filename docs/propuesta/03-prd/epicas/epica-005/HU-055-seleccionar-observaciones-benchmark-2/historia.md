# Historia #055: Seleccionar observaciones retail del Benchmark 2 cercanas a la fecha de la compra

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Selección de Comparables  
**Prioridad:** Crítica  
**FRs relacionados:** FR-056, FR-062

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema seleccione, para cada ítem de televisor, solo las observaciones de precio retail registradas dentro de una ventana configurable alrededor de la fecha de la compra,  
**Para** que el Benchmark 2 – Mercado nunca juzgue una compra antigua con un precio actual y que cada observación usada muestre su tienda, su fecha y su método de adquisición.

## Descripción

El Benchmark 2 compara el precio contratado contra observaciones de la **base propia de observaciones de mercado** (Alkosto como fuente principal y Falabella como secundaria, obtenidas por captura automática permitida o por carga manual o semiautomática). Esta HU define **qué observaciones entran** al conjunto del Benchmark 2 de un ítem. El cálculo de la referencia, la degradación a "no disponible" y la desviación se hacen en HU-058.

La regla temporal es estricta: solo entran observaciones con fecha de observación dentro de la ventana configurable (configuración inicial: ±30 días respecto a la fecha de la compra). **No hay ampliación automática** de esta ventana. Por eso, para contratos antiguos anteriores al histórico propio de precios, el conjunto queda vacío y el Benchmark 2 se degradará a "no disponible" sin afectar al Benchmark 1.

El Benchmark 2 usa **solo observaciones retail**; las compras públicas (SECOP II y TVEC) se usan exclusivamente en el Benchmark 1.

---

## Criterios de Aceptación

### Escenario 1: Selección con mismo modelo de dos tiendas dentro de la ventana

- **Dado** que un ítem elegible tiene fecha de compra 2026-08-20 y existen 2 observaciones Alkosto y 1 observación Falabella de su mismo modelo con fechas entre 2026-07-21 y 2026-09-19
- **Cuando** el sistema ejecuta la selección del Benchmark 2
- **Entonces** el conjunto contiene las 3 observaciones, tipo "Mismo modelo", ventana "±30 días", y cada una muestra origen ("Retail – Alkosto" o "Retail – Falabella"), fecha de observación, precio efectivo, método de adquisición e indicador "Manual" cuando aplique

### Escenario 2: Observación fuera de la ventana

- **Dado** que la única observación del mismo modelo es del 2026-09-25 y la fecha de compra es 2026-08-20
- **Cuando** el sistema ejecuta la selección
- **Entonces** esa observación no entra (está a 36 días), el conjunto queda vacío con estado "Sin observaciones de mercado en la ventana (±30 días)" y se registra 1 descarte "fuera de ventana"

### Escenario 3: Compra antigua sin histórico de mercado

- **Dado** que el ítem tiene fecha de compra 2023-04-10 y la observación retail más antigua del sistema es de 2026-09-01
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto queda vacío con estado "Sin observaciones de mercado en la ventana (±30 días)"; nunca se usa una observación actual para esa compra

### Escenario 4: Incorporación de equivalentes cuando el mismo modelo no alcanza el mínimo

- **Dado** que el ítem tiene 2 observaciones Alkosto de mismo modelo y 2 observaciones Falabella de producto equivalente dentro de la ventana, con mínimo 3 observaciones de 2 fuentes
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto contiene las 4 observaciones, con tipo de conjunto "Producto equivalente"

### Escenario 5: Ningún paso alcanza el mínimo

- **Dado** que el ítem tiene 1 observación Alkosto manual de mismo modelo dentro de la ventana y ninguna equivalente
- **Cuando** el sistema ejecuta la selección
- **Entonces** el conjunto contiene esa observación, marcado "Por debajo del mínimo configurado (1 observación de 1 fuente; mínimo 3 de 2 fuentes)", y la observación aparece con el indicador "Manual"

### Escenario 6: Exclusión de observaciones no válidas

- **Dado** que dentro de la ventana existen: una observación con vendedor tercero de marketplace, una con precio condicionado (tarjeta específica), una con precio efectivo 0, una con emparejamiento "insuficiente/no confiable" y una de una fuente pública (TVEC)
- **Cuando** el sistema ejecuta la selección
- **Entonces** ninguna entra al conjunto y el registro de la selección indica 1 descarte por cada motivo: "vendedor no es la tienda", "precio condicionado", "precio inválido", "emparejamiento insuficiente", "fuente no retail"

### Escenario 7: Observaciones repetidas del mismo producto en la misma tienda

- **Dado** que Alkosto tiene 4 observaciones semanales del mismo SKU dentro de la ventana (2026-08-03, 2026-08-10, 2026-08-17, 2026-08-24) y la fecha de compra es 2026-08-20
- **Cuando** el sistema ejecuta la selección
- **Entonces** solo entra la observación del 2026-08-17 (la más cercana; ante empate de distancia se prefiere la anterior a la fecha de compra) y las otras 3 se registran como descarte "repetida por tienda y producto"

### Escenario 8: Ítem objetivo no elegible

- **Dado** que el ítem objetivo no tiene precio unitario válido, no tiene fecha de compra, tiene datos pendientes de revisión o su producto está marcado como "insuficiente/no confiable" para emparejamiento
- **Cuando** el sistema intenta la selección
- **Entonces** no se construye conjunto y el ítem queda con estado "Benchmark 2 no calculado" y el motivo exacto ("Sin precio unitario", "Precio unitario inválido", "Datos pendientes de revisión", "Sin fecha de compra" o "Emparejamiento insuficiente")

### Escenario 9: Límite exacto de la ventana y cambio de parámetro

- **Dado** que la fecha de compra es 2026-08-20, hay una observación del 2026-07-21 (−30 días) y otra del 2026-07-20 (−31 días), y luego el Administrador cambia la ventana a 45 días
- **Cuando** se ejecuta la selección antes y después del cambio
- **Entonces** antes del cambio entra solo la del 2026-07-21; después entran ambas, y el registro guarda la ventana usada en cada ejecución

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). Proceso automático del sistema.
- **Permisos requeridos:** Ninguno para la ejecución automática. Solo el Administrador modifica los parámetros.
- **Valor de negocio:** Garantiza la regla temporal del Brief ("un precio actual no se usa para juzgar una compra antigua") y la trazabilidad del método de adquisición de cada precio de mercado.

### Reglas de Negocio

**RN-01 – Ítem objetivo elegible.** Las mismas condiciones del Benchmark 1: clasificación "incluido"; precio unitario no nulo y > 0 COP (`explicito` o `derivado`); datos "aceptados automáticamente", "validados" o "corregidos por revisor" (o estructurados de origen TVEC); fecha de compra no nula; producto normalizado no marcado "insuficiente/no confiable". Si no cumple, estado "Benchmark 2 no calculado" con el primer motivo que aplique en este orden: "Sin precio unitario", "Precio unitario inválido", "Datos pendientes de revisión", "Sin fecha de compra", "Emparejamiento insuficiente".

**RN-02 – Fecha de la compra.** SECOP II: `fecha_de_firma` del contrato. TVEC: fecha de la orden de compra. Formato AAAA-MM-DD.

**RN-03 – Observación válida.** Una observación de la base de mercado es candidata solo si cumple todas:
1. Su fuente es una fuente retail habilitada (configuración inicial: Alkosto, Falabella). Observaciones de fuentes públicas → descarte "fuente no retail".
2. Vendedor = la tienda de la fuente. Otro vendedor → descarte "vendedor no es la tienda".
3. Precio efectivo no nulo y > 0 COP. Si no → descarte "precio inválido". El precio tachado o anterior nunca se usa como precio de la observación.
4. No está marcada como precio condicionado (tarjeta específica, cupón, financiación, membresía u otra condición especial). Si lo está → descarte "precio condicionado".
5. Fecha de observación no nula. Si es nula → descarte "sin fecha de observación".
6. Emparejamiento con el producto del ítem objetivo = "mismo modelo" o "producto equivalente" (según la clasificación del módulo de emparejamiento, sin recalcularla ni relajarla). "Insuficiente/no confiable" → descarte "emparejamiento insuficiente".
Las observaciones manuales y semiautomáticas son válidas si cumplen lo anterior.

**RN-04 – Ventana temporal.** Intervalo cerrado [fecha de compra − D días, fecha de compra + D días], con D = `b2_ventana_dias`. Fuera → descarte "fuera de ventana". No existe ampliación automática.

**RN-05 – Parámetros configurables** (leídos en cada ejecución):

| Parámetro | Configuración inicial | Rango permitido |
|---|---|---|
| `b2_ventana_dias` | 30 | 1 a 180, entero |
| `b2_minimo_observaciones` | 3 | 1 a 50, entero |
| `b2_minimo_fuentes` | 2 | 1 a 10, entero |
| `b2_fuentes_retail_habilitadas` | Alkosto, Falabella | Lista no vacía |

Valor faltante o fuera de rango → se usa la configuración inicial y se registra la advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

**RN-06 – Una observación por tienda y producto.** Entre observaciones válidas de la misma fuente y el mismo producto observado (identificado por SKU; si no hay SKU, por EAN; si no hay EAN, por marca + modelo normalizado), se conserva solo la de fecha más cercana a la fecha de compra. Empate de distancia → la anterior a la fecha de compra. Mismo día → la registrada más recientemente. Las demás → descarte "repetida por tienda y producto".

**RN-07 – Selección escalonada.** Un conjunto "alcanza el mínimo" si tiene ≥ `b2_minimo_observaciones` observaciones **y** ≥ `b2_minimo_fuentes` fuentes distintas. Pasos:
1. Mismo modelo dentro de la ventana.
2. Mismo modelo + producto equivalente dentro de la ventana.
Se usa el primer paso que alcance el mínimo. Si ninguno lo alcanza: paso 1 si tiene ≥ 1 observación; si no, paso 2 si tiene ≥ 1; si ambos están vacíos, conjunto vacío con estado "Sin observaciones de mercado en la ventana (±{D} días)". Un conjunto con observaciones pero sin alcanzar el mínimo se marca "Por debajo del mínimo configurado ({n} observaciones de {f} fuentes; mínimo {m} de {mf} fuentes)".

**RN-08 – Tipo de emparejamiento del conjunto.** "Mismo modelo" si todas lo son; "Producto equivalente" si al menos una es equivalente. Cada observación conserva su tipo individual.

**RN-09 – Origen y trazabilidad de cada observación (FR-062).** Cada observación del conjunto registra: origen = "Retail – {fuente}"; identificador de la observación; producto, marca/modelo, SKU/EAN si existen; precio efectivo; fecha de observación; información de IVA registrada; método de adquisición (API / dataset / feed / sitemap-datos estructurados / extracción web / manual); indicador "Manual" cuando el método es manual; URL o referencia y evidencia asociada.

**RN-10 – Registro de la selección.** Por ítem: paso usado, ventana usada, mínimos usados, n.º de observaciones y de fuentes, si quedó por debajo del mínimo, conteo de descartes por motivo y fecha-hora de ejecución.

**RN-11 – Recálculo.** Igual que el Benchmark 1: tras ingesta/extracción, tras nuevas observaciones de mercado (captura, carga manual o CSV), tras correcciones validadas, tras cambio de parámetros y por ejecución manual del Administrador.

### Interfaz

Sin interfaz propia. El conjunto y el origen de cada observación se muestran en el detalle de la señal (HU-063).

### Sistemas Externos (Si aplica)

No consulta tiendas en tiempo de ejecución: usa exclusivamente la base propia de observaciones ya registradas. Nunca dispara capturas para "completar" un conjunto.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-056 (base tributaria), HU-058 (cálculo del Benchmark 2), HU-063 (detalle de la señal).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Sin ampliación de la ventana del Benchmark 2**: el PRD solo prevé ampliación para el Benchmark 1; resuelto en RN-04.
- **Una observación por tienda y producto** para que las capturas semanales repetidas no inflen el conteo: resuelto en RN-06.
- **Benchmark 2 solo retail** (FR-056 lo dice explícitamente; la TVEC complementa vía Benchmark 1): resuelto en RN-03.
- **Precios condicionados excluidos del conjunto** (FR-046: no son precio general de mercado): resuelto en RN-03.

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
