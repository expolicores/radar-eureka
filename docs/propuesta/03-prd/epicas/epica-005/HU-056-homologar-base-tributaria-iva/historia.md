# Historia #056: Homologar la base tributaria (IVA) y marcar comparaciones incompletas

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Selección de Comparables  
**Prioridad:** Crítica  
**FRs relacionados:** FR-057

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema compare precios solo en la misma base tributaria (precio final con IVA) y marque como incompleta/no confiable toda comparación en la que la base de algún valor no se pueda determinar,  
**Para** no recibir nunca una comparación que mezcle en silencio valores con IVA y sin IVA.

## Descripción

Antes de calcular cualquier referencia (Benchmark 1 o 2), el sistema lleva el precio unitario contratado y cada observación del conjunto seleccionado a la base **precio final con IVA**. Si un valor viene **sin IVA**, se convierte **solo** cuando el documento fuente declara explícitamente el valor del IVA o la tarifa aplicable a ese valor; la conversión queda marcada como "convertido" con la tarifa o el IVA usado y su evidencia (documento y página/hoja/celda). Si un valor **sin IVA** no tiene IVA ni tarifa explícitos, o si la base de un valor es **indeterminada**, no se convierte ni se supone ninguna tarifa: la comparación queda marcada **"Incompleta / no confiable: base tributaria indeterminada"** (NFR-CAL-006: 0 % de comparaciones mezclando IVA sin marca). No se usa una tarifa general por defecto: el spike D4 encontró exenciones regionales (p. ej. San Andrés), por lo que suponer 19 % puede producir señales falsas (decisión PO, 2026-10-05).

Caso conocido: la base tributaria de los precios de la **TVEC no está determinada** (tarea de verificación INV-01, pendiente con documentación oficial de Colombia Compra Eficiente). Hasta que el Administrador registre el resultado de INV-01 en la configuración, todos los precios TVEC se tratan como de base **indeterminada**. La HU no asume la respuesta.

---

## Criterios de Aceptación

### Escenario 1: Todos los valores con IVA

- **Dado** que el precio contratado (SECOP II, 2.380.000 COP, "con IVA") y las 5 observaciones del conjunto declaran base "con IVA"
- **Cuando** el sistema homologa la base tributaria
- **Entonces** todos los valores se usan sin cambios, ninguno queda "convertido" y el estado tributario de la comparación es "Completa – precio final con IVA"

### Escenario 2: Valor sin IVA sin tarifa explícita en el documento

- **Dado** que el precio contratado es 2.000.000 COP "sin IVA" y el documento no registra ni el valor del IVA ni la tarifa aplicable
- **Cuando** el sistema homologa
- **Entonces** el valor no se convierte (no se asume 19 % ni ninguna otra tarifa), se trata como base indeterminada, la comparación queda "Incompleta / no confiable: base tributaria indeterminada del precio contratado" y se muestra el motivo "Valor sin IVA sin tarifa explícita en el documento: no se convierte (posibles exenciones o tarifas diferenciales, ej. San Andrés)"

### Escenario 3: Conversión con IVA unitario explícito

- **Dado** que el precio contratado es 2.000.000 COP "sin IVA" y el documento registra un IVA unitario explícito de 380.000 COP
- **Cuando** el sistema homologa
- **Entonces** el precio homologado es 2.380.000 COP, marcado "Convertido desde sin IVA (IVA explícito del documento)", y el registro guarda el IVA usado (380.000 COP) y su evidencia (documento y página/hoja/celda)

### Escenario 4: Conversión con tarifa explícita en el documento

- **Dado** que el precio contratado es 2.000.000 COP "sin IVA" y el documento indica para ese valor "IVA 19 %" (contrato CO1.PCCNTR.6660001, página 3)
- **Cuando** el sistema homologa
- **Entonces** el precio homologado es 2.380.000 COP, marcado "Convertido desde sin IVA (tarifa 19 % explícita en el documento)", el registro guarda la tarifa usada y su evidencia ("CO1.PCCNTR.6660001, página 3") y, si los demás valores son determinados, la comparación queda "Completa – precio final con IVA (incluye valores convertidos)"

### Escenario 5: Precio contratado con base indeterminada

- **Dado** que el precio contratado tiene base "indeterminada"
- **Cuando** el sistema homologa
- **Entonces** el valor no se convierte, la comparación queda "Incompleta / no confiable: base tributaria indeterminada del precio contratado" y el cálculo continúa con esa marca visible

### Escenario 6: Observaciones TVEC con INV-01 sin resolver

- **Dado** que el parámetro `base_tributaria_tvec` tiene el valor "indeterminada" (configuración inicial) y el conjunto del Benchmark 1 tiene 6 observaciones TVEC y 2 SECOP II "con IVA"
- **Cuando** el sistema homologa
- **Entonces** las 6 observaciones TVEC quedan con base "indeterminada"; como las 2 observaciones determinadas no alcanzan el mínimo (5), se usan las 8 observaciones y la comparación queda "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones"

### Escenario 7: Suficientes observaciones determinadas

- **Dado** que el conjunto del Benchmark 1 tiene 6 observaciones "con IVA" y 2 de base indeterminada, con mínimo 5, y el precio contratado tiene base determinada
- **Cuando** el sistema homologa
- **Entonces** se usan solo las 6 observaciones determinadas, las 2 indeterminadas se registran como "excluida por base tributaria indeterminada" y la comparación queda "Completa"

### Escenario 8: INV-01 resuelto por el Administrador

- **Dado** que el Administrador cambia `base_tributaria_tvec` a "con IVA"
- **Cuando** se ejecuta el siguiente recálculo
- **Entonces** los precios TVEC se tratan como "con IVA", las comparaciones afectadas se recalculan y el registro guarda el valor del parámetro usado

### Escenario 9: Observación retail sin información de IVA

- **Dado** que una observación de Alkosto no tiene información de IVA registrada (campo vacío)
- **Cuando** el sistema homologa
- **Entonces** esa observación queda con base "indeterminada" y se aplica la misma regla de exclusión o marca de los escenarios 6 y 7

### Escenario 10: Base tributaria con valor no reconocido

- **Dado** que un valor llega con base tributaria "IVA incluido parcial" (valor fuera del dominio)
- **Cuando** el sistema homologa
- **Entonces** se trata como "indeterminada" y el log de la ejecución registra "Base tributaria no reconocida '{valor}' en {identificador}; tratada como indeterminada"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). Proceso automático.
- **Permisos requeridos:** Ninguno para la ejecución. Solo el Administrador modifica `base_tributaria_tvec`.
- **Valor de negocio:** Evita falsos positivos por diferencias debidas solo al IVA y por suponer una tarifa que puede no aplicar (exenciones o tarifas diferenciales, p. ej. San Andrés, halladas en el spike D4); cumple NFR-CAL-006 (meta del Brief).

### Reglas de Negocio

**RN-01 – Dominio de la base tributaria.** Cada valor tiene una base: `con_iva`, `sin_iva` o `indeterminada`. Nulo, vacío o cualquier otro valor → `indeterminada` (con registro en log si el valor no es nulo ni vacío).

**RN-02 – Origen de la base por tipo de dato.**
- Precio unitario contratado de SECOP II: la base registrada por la extracción (con IVA / sin IVA / indeterminada).
- Precio de la TVEC (como ítem objetivo o como comparable): el valor del parámetro `base_tributaria_tvec` (configuración inicial: `indeterminada`, mientras INV-01 no se resuelva). Valores permitidos: `con_iva`, `sin_iva`, `indeterminada`. Con `sin_iva`, cada precio TVEC se convierte solo si la orden de compra declara el IVA o la tarifa de ese valor (RN-03).
- Observación retail: la información de IVA registrada en la observación ("incluye IVA" → `con_iva`; "no incluye IVA" → `sin_iva`; vacío o desconocido → `indeterminada`).

**RN-03 – Conversión a precio final con IVA.**
- `con_iva`: se usa tal cual.
- `sin_iva` con IVA unitario explícito en el documento: precio + IVA unitario. Marca "Convertido desde sin IVA (IVA explícito del documento)".
- `sin_iva` con tarifa explícita en el documento para ese valor: precio × (1 + t/100), donde t es la tarifa declarada (incluido 0 % si el documento declara exención). Marca "Convertido desde sin IVA (tarifa {t} % explícita en el documento)". Si el documento declara IVA unitario y tarifa, prevalece el IVA unitario. Una tarifa no numérica o fuera de 0 a 100 % se trata como no declarada y se registra en log "Tarifa de IVA no válida '{valor}' en {identificador}; se trata como no declarada".
- Toda conversión registra el IVA o la tarifa usados y su evidencia: identificador del documento y página, hoja o celda de donde se tomó.
- `sin_iva` sin IVA ni tarifa explícitos en el documento: **no se convierte** y no se supone ninguna tarifa (ni 19 % ni otra por defecto). El valor se trata como `indeterminada` para RN-05 y RN-06 y muestra el motivo "Valor sin IVA sin tarifa explícita en el documento: no se convierte (posibles exenciones o tarifas diferenciales, ej. San Andrés)".
- `indeterminada`: no se convierte.
- Redondeo: al peso entero más cercano (0,5 hacia arriba). Moneda COP.

**RN-04 – Parámetros configurables.**

| Parámetro | Configuración inicial | Rango |
|---|---|---|
| `base_tributaria_tvec` | `indeterminada` | `con_iva` / `sin_iva` / `indeterminada` |

Valor faltante o inválido → configuración inicial y advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

**RN-05 – Tratamiento de observaciones indeterminadas.** Sea M el mínimo de observaciones del benchmark (Benchmark 1: `b1_minimo_observaciones`, inicial 5; Benchmark 2: `b2_minimo_observaciones`, inicial 3, y además `b2_minimo_fuentes`, inicial 2). Si las observaciones con base determinada (`con_iva` o `sin_iva` convertida) alcanzan por sí solas el mínimo, se usan solo esas y las indeterminadas (incluidas las `sin_iva` no convertidas por falta de tarifa explícita) se registran como "excluida por base tributaria indeterminada". Si no lo alcanzan, se usan todas (determinadas e indeterminadas) y la comparación se marca incompleta.

**RN-06 – Estado tributario de la comparación** (uno solo, el primero que aplique):
1. "Incompleta / no confiable: base tributaria indeterminada del precio contratado" – si el precio contratado es `indeterminada`.
2. "Incompleta / no confiable: base tributaria indeterminada en {k} de {n} observaciones" – si el conjunto usado incluye ≥ 1 indeterminada.
3. "Completa – precio final con IVA (incluye valores convertidos)" – si hay ≥ 1 valor convertido.
4. "Completa – precio final con IVA".
Si se cumplen 1 y 2 a la vez, el texto combina ambos motivos: "Incompleta / no confiable: base tributaria indeterminada del precio contratado y de {k} de {n} observaciones".
Los valores `sin_iva` sin IVA ni tarifa explícitos cuentan como indeterminados en 1 y 2, y el detalle muestra para cada uno el motivo de RN-03.

**RN-07 – Continuidad del cálculo.** Una comparación incompleta **no se descarta**: se calcula y se muestra con su marca. La marca se conserva en la referencia, la desviación y en cualquier señal derivada, y afecta su nivel de confianza (HU-061).

**RN-08 – Registro.** Por cada valor: base original, base final, valor original, valor homologado, método de conversión, IVA o tarifa usados con su evidencia (documento y página/hoja/celda) y, si no se convirtió, el motivo. Por cada comparación: estado tributario, parámetros usados y conteo de excluidas por base indeterminada.

### Interfaz

Sin interfaz propia. El estado tributario y la marca "convertido" se muestran en el detalle de la señal (HU-063).

### Sistemas Externos (Si aplica)

No aplica. La verificación INV-01 se hace fuera del sistema; su resultado se registra en `base_tributaria_tvec`.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-054, HU-055 (conjuntos que se homologan), HU-057, HU-058 (cálculo), HU-061 (confianza).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Conversión de valores sin IVA solo con IVA o tarifa explícitos en el documento**: el Brief permite comparar "cuando ambos valores puedan llevarse a esa base"; por decisión del PO (2026-10-05) no se usa tarifa general por defecto, porque el spike D4 encontró exenciones regionales (p. ej. San Andrés) que la harían producir señales falsas. Resuelto en RN-03 (conversión con evidencia; sin tarifa explícita → comparación incompleta).
- **Base TVEC como parámetro** mientras INV-01 no se resuelva (inicial: indeterminada): resuelto en RN-02/RN-04 sin asumir la respuesta.
- **Preferir observaciones determinadas cuando alcanzan el mínimo**: resuelto en RN-05.

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
| 2026-10-05 | 1.1 | Se elimina la conversión con tarifa general; sin tarifa explícita → comparación incompleta (decisión PO) | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
