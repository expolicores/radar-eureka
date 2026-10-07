# Historia #110: Calcular los KPIs de señales sustentadas y de eficiencia por caso

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-091, FR-093 (relacionados: FR-069, FR-094; NFR-CAL-007, NFR-CAL-008)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** calcular el porcentaje de señales calificadas como "suficientemente sustentadas para merecer revisión" por los analistas y la reducción del tiempo humano por caso frente a la línea base manual,  
**Para** saber si el MVP valida su hipótesis de valor: señales creíbles para usuarios reales, obtenidas con mucho menos esfuerzo que el análisis manual.

## Descripción

Dos KPIs del Brief dependen del uso real del producto:

- **Validación humana (NFR-CAL-007):** ≥ 70 % de las señales presentadas para validación deben ser calificadas como "suficientemente sustentadas para merecer revisión" por al menos 3 usuarios del perfil de diseño (aunque luego no haya irregularidad).
- **Eficiencia (NFR-CAL-008):** el tiempo humano promedio por caso debe reducirse ≥ 70 % frente a la línea base manual medida en el discovery (D2). Meta provisional, se recalibra con la línea base.

Esta HU calcula ambos indicadores a partir de las calificaciones de los Analistas (FR-069) y de las mediciones de tiempo (FR-093, HU-109), permite registrar la línea base manual cuando D2 la entregue y guarda cada cálculo como corte histórico. Calificar una señal como "sustentada" **no** significa que exista una irregularidad: solo que merece revisión.

**Implementación sin UI permitida:** comando, script, consulta o reporte; la línea base se registra como parámetro de la configuración versionada.

---

## Criterios de Aceptación

### Escenario 1: Porcentaje de señales sustentadas que cumple

- **Dado** que 4 Analistas distintos tienen 50 calificaciones vigentes sobre 22 señales, de las cuales 37 son "sustentada"
- **Cuando** el Administrador calcula los KPIs
- **Entonces** obtiene calificaciones sustentadas 74,0 % (37/50), analistas que calificaron 4, estado "Cumple" (meta 70,0 %, mínimo 3 analistas), y el desglose por señal y por Analista de RN-04

### Escenario 2: Menos de 3 analistas

- **Dado** que solo 2 Analistas han calificado señales y el 80,0 % de sus calificaciones es "sustentada"
- **Cuando** se calculan los KPIs
- **Entonces** se muestra 80,0 %, pero el estado es "Insuficientes usuarios: 2 de 3 analistas." y no dice "Cumple"

### Escenario 3: Porcentaje por debajo de la meta

- **Dado** que 3 Analistas tienen 40 calificaciones vigentes, 26 "sustentada"
- **Cuando** se calculan los KPIs
- **Entonces** obtiene 65,0 % (26/40) y estado "No cumple"

### Escenario 4: Recalificación

- **Dado** que la Analista `analista1@prueba.co` calificó SEN-0101 como "sustentada" y luego la recalificó como "no sustentada"
- **Cuando** se calculan los KPIs
- **Entonces** solo cuenta su calificación vigente ("no sustentada") para ese par Analista–señal

### Escenario 5: Registrar la línea base manual

- **Dado** que la línea base está "no registrada"
- **Cuando** el Administrador registra 60 minutos por caso con la fuente "D2: 12 casos reales cronometrados, 2026-11" y un motivo válido
- **Entonces** se crea una nueva versión de configuración con ese valor y su fuente, y se registra el evento de auditoría con valor anterior "no registrada" y nuevo 60

### Escenario 6: Reducción del tiempo que cumple

- **Dado** que la línea base es 60 minutos y hay 20 mediciones "completa" con tiempo activo promedio 14:30
- **Cuando** se calculan los KPIs
- **Entonces** obtiene tiempo promedio 14:30, mediana, número de mediciones 20, reducción 75,8 % ((60 − 14,5) / 60) y estado "Cumple (meta provisional 70,0 %)"

### Escenario 7: Plataforma más lenta que la línea base

- **Dado** que la línea base es 10 minutos y el promedio de tiempo activo es 12:00
- **Cuando** se calculan los KPIs
- **Entonces** la reducción es −20,0 % y el estado es "No cumple"

### Escenario 8: Sin línea base

- **Dado** que la línea base está "no registrada" y hay mediciones completas
- **Cuando** se calculan los KPIs
- **Entonces** se muestran el promedio, la mediana y el número de mediciones, la reducción es "—" y el estado es "Línea base no registrada (pendiente de D2)."

### Escenario 9: Sin calificaciones o sin mediciones

- **Dado** que no hay calificaciones vigentes ni mediciones completas en el período
- **Cuando** se calculan los KPIs
- **Entonces** el KPI de señales sustentadas muestra "—" con "Sin datos: no hay calificaciones de analistas." y el de eficiencia "—" con "Sin datos: no hay mediciones de tiempo completas."

### Escenario 10: Línea base inválida

- **Dado** que el Administrador está autenticado
- **Cuando** registra una línea base de 0, de 10.001 minutos, un valor no numérico o sin fuente
- **Entonces** no se crea versión y recibe "La línea base debe ser un número entre 1 y 10000 minutos." o "Debe indicar la fuente de la línea base (10 a 200 caracteres)."

### Escenario 11: Período del cálculo y corte histórico

- **Dado** que el Administrador calcula los KPIs para el período 2026-11-01 a 2026-11-30
- **Cuando** consulta luego el historial
- **Entonces** el cálculo usa solo calificaciones y mediciones con fecha de calificación en ese período, y el corte guarda período, fecha y hora, versión de configuración (con la línea base usada) e indicadores

### Escenario 12: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta calcular los KPIs o registrar la línea base
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** son los dos KPIs que demuestran la hipótesis de valor del MVP (objetivo de negocio 1 del Brief).

### Reglas de Negocio

- **RN-01 — Calificaciones vigentes:** por cada par (Analista, señal), la última calificación emitida por un usuario con rol Analista dentro del período ("sustentada" o "no sustentada"). Calificaciones de usuarios Administrador no cuentan.
- **RN-02 — KPI de señales sustentadas:** = calificaciones vigentes "sustentada" / calificaciones vigentes. Analistas que calificaron = usuarios Analista distintos con al menos una calificación vigente.
- **RN-03 — Parámetros (configurables):** meta de señales sustentadas, decimal 0,0–100,0 %, **configuración inicial: 70,0 %**; mínimo de analistas, entero 1–50, **configuración inicial: 3**; meta de reducción de tiempo, decimal 0,0–100,0 %, **configuración inicial: 70,0 %** (provisional); línea base manual, decimal de 1 a 10.000 minutos por caso o "no registrada", **configuración inicial: no registrada**, con fuente obligatoria de 10 a 200 caracteres cuando tiene valor.
- **RN-04 — Desgloses del KPI de señales sustentadas:** por señal: número de calificaciones, "sustentada", "no sustentada" y resultado mayoritario ("sustentada", "no sustentada" o "empate"); por Analista (identificado por su correo): número de calificaciones y porcentaje "sustentada". Se informa además "señales con mayoría sustentada / señales calificadas" como indicador complementario sin meta.
- **RN-05 — Estados del KPI de señales sustentadas (en orden):** "Sin datos: no hay calificaciones de analistas." (0 calificaciones); "Insuficientes usuarios: {n} de {mínimo} analistas."; "Cumple" si el porcentaje redondeado a 1 decimal ≥ meta; "No cumple".
- **RN-06 — KPI de eficiencia:** tiempo promedio = media aritmética del tiempo activo de las mediciones con estado "completa" y fecha de calificación en el período; se informan también mediana y número de mediciones. Reducción = (línea base − promedio en minutos) / línea base × 100, con 1 decimal; puede ser negativa.
- **RN-07 — Estados del KPI de eficiencia (en orden):** "Sin datos: no hay mediciones de tiempo completas."; "Línea base no registrada (pendiente de D2)." (reducción "—"); "Cumple (meta provisional {m} %)" si la reducción redondeada ≥ meta; "No cumple".
- **RN-08 — Registro de la línea base:** se hace con el mecanismo de configuración versionada (nueva versión, motivo de 10 a 500 caracteres, control de concurrencia, evento de auditoría "Cambio de configuración" con valor anterior, nuevo, fuente y versión). Si la auditoría falla, no se aplica.
- **RN-09 — Período:** rango de fechas `AAAA-MM-DD` con extremos incluidos (por defecto, desde la primera calificación registrada hasta hoy), máximo 365 días; inicio ≤ fin.
- **RN-10 — Corte histórico:** cada cálculo se guarda inmutable con período, fecha y hora (UTC−05:00), usuario, versión de configuración (incluye línea base y metas), indicadores, estados y desgloses. A demanda; no modifica calificaciones ni mediciones.
- **RN-11 — Lenguaje:** el reporte habla de "señales que merecen revisión"; nunca usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".
- **RN-12 — Mensajes:** los de RN-05 y RN-07; "La línea base debe ser un número entre 1 y 10000 minutos."; "Debe indicar la fuente de la línea base (10 a 200 caracteres)."; "El rango de consulta no puede superar 365 días."; "La fecha inicial no puede ser posterior a la fecha final."; "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "calcular KPIs de validación y eficiencia" con período opcional, reporte (texto, CSV o JSON) e historial; la línea base se registra con el comando de configuración.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-109 (medición de tiempo), HU-101 (configuración versionada), HU-112 (auditoría).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La unidad del KPI de señales sustentadas es la calificación vigente por par Analista–señal; el resultado mayoritario por señal se reporta como complemento → resuelto en RN-01, RN-02 y RN-04.
- "Al menos 3 usuarios" se verifica como número de analistas distintos que calificaron; con menos, el estado es "Insuficientes usuarios" → resuelto en RN-05.
- La línea base manual (D2) es un parámetro versionado con fuente obligatoria; mientras no exista, la reducción no se calcula → resuelto en RN-03, RN-07 y RN-08.
- El tiempo promedio usa el tiempo activo de las mediciones completas → resuelto en RN-06.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-008 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
