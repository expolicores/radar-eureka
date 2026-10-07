# Historia #059: Generar la «señal que merece revisión» por desviación al alza con regla híbrida configurable

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Generación y Confianza de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-063

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que el sistema genere una "señal que merece revisión" cuando el precio unitario contratado está por encima de la referencia según una regla híbrida configurable,  
**Para** priorizar los casos que conviene revisar entre cientos de ítems, sin que la señal sea una conclusión.

## Descripción

Por cada ítem y cada benchmark con referencia (Benchmark 1 y Benchmark 2, por separado), el sistema evalúa si la **desviación por encima** de la referencia justifica una señal, con una **estrategia híbrida configurable** (decisión P-03):

- **(a) Regla de valores atípicos**, cuando la muestra de comparables es suficiente y homogénea: señal si el precio contratado supera `Q3 + 1,5 × IQR` (configuración inicial).
- **(b) Umbrales porcentuales provisionales**, en cualquier otro caso: señal si la desviación es **≥ +30 %** con emparejamiento de **mismo modelo**, o **≥ +50 %** con **producto equivalente** (configuración inicial).

Estos umbrales sirven **exclusivamente para priorizar** revisión, no significan irregularidad y se recalibran con evidencia real. **Solo las desviaciones al alza generan señal** (decisión P-04); los precios anormalmente bajos se tratan en HU-060 como revisión de calidad. La evidencia completa de la señal se registra en HU-062 y su confianza en HU-061.

---

## Criterios de Aceptación

### Escenario 1: Señal por regla de atípicos

- **Dado** que el Benchmark 1 del ítem tiene "Referencia estadística" con 7 observaciones homogéneas (todas mismo modelo, comparación tributaria completa) con Q3 = 2.250.000 e IQR = 300.000 COP (límite 2.700.000), y el precio contratado es 2.750.000 COP
- **Cuando** el sistema evalúa la señal
- **Entonces** se genera una señal "Vigente", versión 1, con benchmark "Benchmark 1 – Contratación pública", regla "Valor atípico: precio > Q3 + 1,5 × IQR (límite 2.700.000 COP)" y desviación "+31,0 %"

### Escenario 2: Precio igual al límite de atípicos

- **Dado** el mismo caso del escenario 1 con precio contratado de 2.700.000 COP
- **Cuando** el sistema evalúa la señal
- **Entonces** no se genera señal (el precio debe ser estrictamente mayor que el límite)

### Escenario 3: Señal por umbral de mismo modelo con muestra pequeña

- **Dado** que el Benchmark 1 tiene "Referencia disponible – evidencia limitada" con 3 observaciones de mismo modelo, referencia 2.000.000 COP, y precio contratado 2.600.000 COP (desviación +30,0 %)
- **Cuando** el sistema evalúa
- **Entonces** se genera una señal con regla "Umbral porcentual provisional: mismo modelo ≥ +30 %"

### Escenario 4: Desviación justo debajo del umbral

- **Dado** el caso del escenario 3 con precio 2.598.900 COP (desviación +29,9 %)
- **Cuando** el sistema evalúa
- **Entonces** no se genera señal

### Escenario 5: Umbral de producto equivalente

- **Dado** que el conjunto es de tipo "Producto equivalente", referencia 2.000.000 COP
- **Cuando** el sistema evalúa con precio 3.000.000 COP (+50,0 %) y con precio 2.990.000 COP (+49,5 %)
- **Entonces** con 3.000.000 se genera señal con regla "Umbral porcentual provisional: producto equivalente ≥ +50 %" y con 2.990.000 no

### Escenario 6: Muestra suficiente pero no homogénea

- **Dado** que el Benchmark 1 tiene "Referencia estadística" con 7 observaciones mezcladas (4 mismo modelo y 3 equivalentes)
- **Cuando** el sistema evalúa
- **Entonces** no aplica la regla de atípicos y aplica el umbral porcentual de "producto equivalente" (≥ +50 %), y la señal, si se genera, registra el motivo "Regla de atípicos no aplicable: muestra no homogénea (tipos de emparejamiento mezclados)"

### Escenario 7: Comparación incompleta por base tributaria

- **Dado** que la comparación está marcada "Incompleta / no confiable: base tributaria indeterminada" y la desviación es +45 % con mismo modelo
- **Cuando** el sistema evalúa
- **Entonces** aplica el umbral porcentual (no la regla de atípicos), genera la señal y esta conserva la marca "Incompleta / no confiable"

### Escenario 8: Desviación negativa o nula

- **Dado** que la desviación del ítem es −35 % o 0,0 %
- **Cuando** el sistema evalúa
- **Entonces** no se genera señal (las desviaciones a la baja se evalúan solo en HU-060)

### Escenario 9: Benchmark sin referencia

- **Dado** que el Benchmark 2 del ítem está "No disponible / evidencia insuficiente" y el Benchmark 1 está "Sin comparables públicos"
- **Cuando** el sistema evalúa
- **Entonces** no se genera señal en ninguno de los dos benchmarks

### Escenario 10: Señal en ambos benchmarks

- **Dado** que el ítem cumple la regla en el Benchmark 1 y en el Benchmark 2
- **Cuando** el sistema evalúa
- **Entonces** se generan dos señales independientes, una por benchmark, cada una con su regla y su desviación

### Escenario 11: Recalculo que deja de cumplir la regla

- **Dado** que existe una señal "Vigente" versión 2 y tras un recálculo la desviación pasa a +12,0 %
- **Cuando** el sistema reevalúa
- **Entonces** la señal pasa a "No vigente", con motivo "Tras el recálculo del {AAAA-MM-DD}, la desviación ya no cumple la regla configurada", conserva todas sus versiones y no se elimina

### Escenario 12: Recalculo que cambia los valores y sigue cumpliendo

- **Dado** que existe una señal "Vigente" versión 1 y tras el recálculo cambia la referencia de 2.100.000 a 2.050.000 COP pero sigue cumpliendo la regla
- **Cuando** el sistema reevalúa
- **Entonces** se crea la versión 2 con los nuevos valores; si nada cambió (referencia, desviación, regla y observaciones), no se crea versión nueva

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). Proceso automático.
- **Permisos requeridos:** Ninguno para la evaluación; los parámetros los cambia el Administrador.
- **Valor de negocio:** Convierte comparaciones en una lista priorizable de casos que merecen revisión (hipótesis de eficiencia ≥ 70 %).

### Reglas de Negocio

**RN-01 – Unidad.** Se evalúa cada par (ítem, benchmark) por separado. Solo se evalúan benchmarks en estado "Referencia estadística", "Referencia estadística de mercado", "Referencia disponible – evidencia limitada" o "Referencia de mercado disponible – evidencia limitada". Los estados sin referencia ("Sin comparables públicos", "No disponible / evidencia insuficiente", "no calculado") nunca generan señal.

**RN-02 – Solo al alza (P-04).** Si la desviación redondeada es ≤ 0,0 %, no se genera señal.

**RN-03 – Muestra suficiente y homogénea.** La regla de atípicos aplica solo si se cumplen todas:
1. El benchmark está en estado de referencia estadística (n ≥ mínimo configurado del benchmark).
2. Todas las observaciones tienen el mismo tipo individual de emparejamiento (todas "mismo modelo" o todas "producto equivalente").
3. El estado tributario de la comparación es "Completa" (con o sin valores convertidos).
4. IQR > 0.
5. `senal_regla_atipicos_habilitada` = sí.
Si alguna falla, se aplica la regla de umbrales y se registra el motivo: "muestra insuficiente", "muestra no homogénea (tipos de emparejamiento mezclados)", "comparación tributaria incompleta", "dispersión nula (IQR = 0)" o "regla de atípicos deshabilitada" (el primero que aplique, en ese orden).

**RN-04 – Regla de atípicos.** Límite = Q3 + `senal_factor_iqr` × IQR, redondeado al peso entero. Señal si precio contratado homologado > límite (estricto).

**RN-05 – Regla de umbrales.** Umbral según el tipo de emparejamiento **del conjunto**: "Mismo modelo" → `senal_umbral_mismo_modelo`; "Producto equivalente" → `senal_umbral_equivalente`. Señal si desviación redondeada a 1 decimal ≥ umbral.

**RN-06 – Parámetros configurables.**

| Parámetro | Configuración inicial | Rango |
|---|---|---|
| `senal_regla_atipicos_habilitada` | sí | sí / no |
| `senal_factor_iqr` | 1,5 | 0,5 a 5,0 (1 decimal) |
| `senal_umbral_mismo_modelo` | 30 (%) | 1 a 500, entero |
| `senal_umbral_equivalente` | 50 (%) | 1 a 500, entero |

Valor faltante o inválido → configuración inicial y advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

**RN-07 – Datos de la señal generada.** Identificador estable por (ítem, benchmark); denominación fija "Señal que merece revisión"; benchmark ("Benchmark 1 – Contratación pública" / "Benchmark 2 – Mercado"); regla aplicada con su texto ("Valor atípico: precio > Q3 + {k} × IQR (límite {valor} COP)", "Umbral porcentual provisional: mismo modelo ≥ +{u} %", "Umbral porcentual provisional: producto equivalente ≥ +{u} %"); motivo de no aplicación de la regla de atípicos cuando corresponda; desviación; referencia; precio contratado homologado; parámetros usados; estado; versión; fechas de creación y última evaluación. La evidencia completa la registra HU-062.

**RN-08 – Ciclo de vida.**
- Primera vez que se cumple la regla → señal "Vigente", versión 1.
- Recalculo y sigue cumpliendo: si cambió la referencia, la desviación, la regla aplicada o el conjunto de observaciones → nueva versión (n + 1); si no cambió nada → sin versión nueva, solo se actualiza la fecha de última evaluación.
- Recalculo y deja de cumplir → "No vigente", motivo "Tras el recálculo del {AAAA-MM-DD}, la desviación ya no cumple la regla configurada".
- El ítem deja de ser elegible o el benchmark queda sin referencia → "No vigente", motivo "El ítem dejó de ser comparable: {motivo del estado del benchmark}".
- Señal "No vigente" que vuelve a cumplir → "Vigente" con nueva versión.
- Las señales y sus versiones nunca se eliminan.

**RN-09 – Lenguaje.** Toda señal se denomina "Señal que merece revisión". Ningún texto generado incluye "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

**RN-10 – Ejecución.** Se evalúa después de cada cálculo de benchmarks (mismos disparadores). Asíncrono.

### Interfaz

Sin interfaz propia. Las señales vigentes alimentan la lista priorizada de señales y el detalle de la señal (HU-063).

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas (las señales nuevas no notifican a nadie).
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-057, HU-058 (benchmarks), HU-060 (precios bajos), HU-061 (confianza), HU-062 (evidencia).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Definición operativa de "muestra suficiente y homogénea"** (mínimo del benchmark, un solo tipo de emparejamiento, base tributaria completa, IQR > 0): resuelto en RN-03, configurable vía habilitación de la regla.
- **Una señal por ítem y benchmark**: resuelto en RN-01/RN-07.
- **Comparaciones tributarias incompletas sí pueden generar señal** (con marca y confianza reducida), porque el PRD exige marcarlas, no descartarlas: resuelto en RN-03/Escenario 7.
- **Versionado y estado "No vigente"** en recálculos, sin borrar señales: resuelto en RN-08.
- **Umbral evaluado sobre la desviación redondeada a 1 decimal**: resuelto en RN-05.

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
