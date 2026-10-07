# Historia #061: Calcular el nivel de confianza de la comparación y de la señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Generación y Confianza de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-068

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada comparación y cada señal tengan un nivel de confianza calculado con reglas explícitas (emparejamiento, cantidad de observaciones, base tributaria, confianza de la extracción, tipo de precio unitario y método de adquisición), con el aporte de cada factor visible,  
**Para** decidir qué señales revisar primero y entender por qué una señal es más o menos sólida.

## Descripción

El sistema calcula un **puntaje de confianza de 0 a 100** y un **nivel** (Alta / Media / Baja) para cada comparación (ítem × benchmark) con referencia. Parte de 100 y resta puntos por cada factor que debilita la comparación. Las penalizaciones y los cortes de nivel son **parámetros configurables** con valores iniciales de diseño, que se recalibran con la validación humana de señales.

Reglas obligatorias del PRD que este cálculo garantiza:
- Un **precio unitario `derivado`** siempre produce un puntaje **menor** que el mismo caso con precio `explicito` (FR-068, decisión D4-3).
- Una comparación marcada **incompleta/no confiable por base tributaria** nunca puede tener nivel superior a **Baja**.
- La confianza de una señal es la de la comparación que la generó, en esa versión.

---

## Criterios de Aceptación

### Escenario 1: Comparación más sólida

- **Dado** un ítem SECOP II con precio `explicito` validado por el revisor, Benchmark 1 con "Referencia estadística", conjunto "Mismo modelo", base tributaria "Completa – precio final con IVA" y referencias públicas
- **Cuando** el sistema calcula la confianza
- **Entonces** el puntaje es 100, el nivel es "Alta" y el desglose muestra 0 puntos en los 6 factores

### Escenario 2: Precio derivado reduce la confianza

- **Dado** el mismo caso del escenario 1 pero con precio unitario `derivado`
- **Cuando** el sistema calcula la confianza
- **Entonces** el puntaje es 85 (−15 por "Tipo de precio unitario: derivado"), menor que el del escenario 1, y el desglose lo explica

### Escenario 3: Combinación de factores débiles

- **Dado** un conjunto "Producto equivalente" con "Referencia disponible – evidencia limitada" y precio `derivado`
- **Cuando** el sistema calcula
- **Entonces** el puntaje es 40 (100 − 20 − 25 − 15) y el nivel "Baja"

### Escenario 4: Tope por base tributaria incompleta

- **Dado** un ítem TVEC, conjunto "Mismo modelo", "Referencia estadística", comparación "Incompleta / no confiable: base tributaria indeterminada"
- **Cuando** el sistema calcula
- **Entonces** el puntaje es 70, pero el nivel es "Baja" con la nota "Nivel limitado a Baja: comparación incompleta por base tributaria"

### Escenario 5: Observaciones manuales en el Benchmark 2

- **Dado** un Benchmark 2 "Referencia de mercado disponible – evidencia limitada" con 2 observaciones manuales de 2 (100 % manuales), mismo modelo, base completa sin conversiones y precio `explicito` validado
- **Cuando** el sistema calcula
- **Entonces** el puntaje es 65 (−25 evidencia limitada, −10 más de la mitad de las observaciones manuales) y el nivel "Media"

### Escenario 6: Valores convertidos y extracción aceptada automáticamente

- **Dado** un conjunto "Mismo modelo", "Referencia estadística", base completa con valores convertidos desde sin IVA, y precio `explicito` aceptado automáticamente por el umbral de extracción
- **Cuando** el sistema calcula
- **Entonces** el puntaje es 80 (−10 conversión, −10 extracción automática) y el nivel "Alta"

### Escenario 7: Límites de nivel

- **Dado** los cortes iniciales (Alta ≥ 75, Media 50–74, Baja < 50)
- **Cuando** el puntaje es 75, 50 o 45
- **Entonces** el nivel es "Alta", "Media" y "Baja" respectivamente

### Escenario 8: Señal hereda la confianza de su versión

- **Dado** que una señal versión 1 tenía confianza 85 "Alta" y un recálculo la deja en versión 2 con confianza 60 "Media"
- **Cuando** se consulta la señal
- **Entonces** la versión vigente muestra 60 "Media" y la versión 1 conserva 85 "Alta"

### Escenario 9: Parámetros inválidos

- **Dado** que el Administrador configura una penalización de −5 (negativa) o un corte de Media mayor o igual al de Alta
- **Cuando** se calcula la confianza
- **Entonces** se usan los valores iniciales del parámetro afectado y se registra "Parámetro {nombre} inválido; se usó el valor inicial {valor}"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); proceso automático.
- **Permisos requeridos:** Ninguno para el cálculo; solo el Administrador cambia penalizaciones y cortes.
- **Valor de negocio:** Reduce falsos positivos percibidos (riesgo R2) y hace explicable la priorización.

### Reglas de Negocio

**RN-01 – Alcance.** Se calcula para cada comparación (ítem × benchmark) con referencia (estadística o evidencia limitada). Comparaciones sin referencia no tienen confianza ("No aplica").

**RN-02 – Puntaje.** Puntaje = 100 − suma de penalizaciones de los 6 factores; mínimo 0; entero.

**RN-03 – Factores y penalizaciones** (configuración inicial; cada penalización es un entero de 0 a 100):

| # | Factor | Condición | Penalización inicial |
|---|---|---|---|
| F1 | Tipo de emparejamiento del conjunto | Mismo modelo / Producto equivalente | 0 / 20 |
| F2 | Cantidad de observaciones | Referencia estadística / Evidencia limitada (por debajo del mínimo) | 0 / 25 |
| F3 | Base tributaria | Completa sin conversiones / Completa con valores convertidos / Incompleta | 0 / 10 / 30 |
| F4 | Confianza de la extracción del precio contratado | Dato estructurado de fuente (TVEC), validado o corregido por revisor / Aceptado automáticamente por umbral de confianza | 0 / 10 |
| F5 | Tipo de precio unitario | `explicito` / `derivado` | 0 / 15 |
| F6 | Método de adquisición de las referencias | Ninguna manual / Manuales ≤ 50 % del conjunto / Manuales > 50 % | 0 / 5 / 10 |

**RN-04 – Precio derivado.** La penalización de `derivado` (F5) debe ser ≥ 1. Si se configura en 0, se usa el valor inicial (15) con la advertencia de parámetros.

**RN-05 – Niveles.** Alta: puntaje ≥ `confianza_corte_alta` (inicial 75). Media: ≥ `confianza_corte_media` (inicial 50) y < corte alta. Baja: < corte media. Restricción: 1 ≤ corte media < corte alta ≤ 100.

**RN-06 – Tope por base tributaria.** Si F3 = Incompleta, el nivel es "Baja" sin importar el puntaje, y se agrega la nota "Nivel limitado a Baja: comparación incompleta por base tributaria".

**RN-07 – Desglose.** Se guarda y se muestra cada factor con su condición y los puntos restados, el puntaje, el nivel, la nota de tope si aplica y los parámetros usados.

**RN-08 – Señal.** Cada versión de una señal guarda la confianza (puntaje, nivel, desglose) de la comparación que la generó en ese momento. Versiones anteriores no se modifican.

**RN-09 – Parámetros inválidos.** Valor faltante, no entero, fuera de 0–100 o que viole RN-04/RN-05 → valor inicial del parámetro y advertencia "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

**RN-10 – Ejecución.** Junto con el cálculo de benchmarks y la evaluación de señales.

### Interfaz

Sin interfaz propia. El nivel, el puntaje y el desglose se muestran en el detalle de la señal (HU-063).

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

**Historias relacionadas:** HU-056 (base tributaria), HU-057, HU-058 (benchmarks), HU-059 (señal), HU-063 (detalle).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Fórmula de confianza** (puntaje 100 con penalizaciones por factor y cortes Alta/Media/Baja): el PRD fija los factores pero no los pesos; se resuelve con valores iniciales de diseño configurables (RN-02 a RN-05), sujetos a recalibración con la validación humana.
- **Tope "Baja" para comparaciones tributarias incompletas**: resuelto en RN-06 (coherente con "incompleta/no confiable").
- **Penalización de precio derivado siempre > 0**: resuelto en RN-04 para garantizar FR-068.

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
