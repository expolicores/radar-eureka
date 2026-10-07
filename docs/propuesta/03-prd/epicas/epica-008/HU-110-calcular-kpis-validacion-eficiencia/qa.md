# Casos de Prueba — HU-110: Calcular los KPIs de señales sustentadas y de eficiencia por caso

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el KPI de señales sustentadas (calificaciones vigentes, mínimo de analistas, meta, desgloses), el KPI de eficiencia (promedio, mediana, reducción, línea base), el registro versionado de la línea base, los períodos, los estados vacíos, los cortes y los permisos. Queda fuera: la captura de tiempos (HU-109) y la calificación de señales (otra épica).

## Precondiciones y Datos Base

- Usuarios Analista: `analista1@prueba.co` … `analista4@prueba.co`; Administrador: `admin.po@prueba.co`.
- Configuración inicial: meta sustentadas 70,0 %; mínimo 3 analistas; meta de reducción 70,0 %; línea base "no registrada".
- **Conjunto C1:** 4 analistas, 50 calificaciones vigentes sobre 22 señales, 37 "sustentada".
- **Conjunto T1:** 20 mediciones "completa" con tiempo activo promedio 14:30 (mediana 13:50).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-04, RN-05 | QA-01 |
| Escenario 2, RN-05 (límite de analistas) | QA-02 |
| Escenario 3, RN-05 (límite de la meta) | QA-03 |
| Escenario 4, RN-01 | QA-04 |
| RN-01 (calificaciones de Administrador) | QA-05 |
| Escenario 5, RN-08 | QA-06 |
| Escenario 6, RN-06, RN-07 | QA-07 |
| Escenario 7, RN-06 | QA-08 |
| Escenario 8, RN-07 | QA-09 |
| Escenario 9 | QA-10 |
| Escenario 10, RN-03 | QA-11 |
| Escenario 11, RN-09, RN-10 | QA-12 |
| RN-11 | QA-13 |
| Escenario 12 | QA-14 |

---

## Casos de Prueba

### QA-01: KPI de señales sustentadas que cumple, con desgloses

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-04, RN-05
- **Pasos:**
  1. Con C1, calcular.
- **Resultado esperado:** 74,0 % (37/50); analistas 4; "Cumple"; desglose por señal (con resultado mayoritario o "empate") y por Analista; indicador complementario de señales con mayoría sustentada.

### QA-02: Mínimo de analistas

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Analistas | 2 (80,0 % sustentadas) | "Insuficientes usuarios: 2 de 3 analistas." |
  | Analistas | 3 (80,0 %) | "Cumple" |

- **Pasos:**
  1. Calcular con cada conjunto.
- **Resultado esperado:** el estado indicado; el porcentaje se muestra en ambos.

### QA-03: Límite de la meta de señales sustentadas

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Sustentadas / total (3 analistas) | 26 / 40 = 65,0 % | No cumple |
  | Sustentadas / total | 28 / 40 = 70,0 % | Cumple |
  | Sustentadas / total | 1.399 / 2.000 = 69,95 % → 70,0 % | Cumple (redondeo) |
  | Sustentadas / total | 1.397 / 2.000 = 69,85 % → 69,9 % | No cumple |

- **Pasos:**
  1. Calcular con cada combinación.
- **Resultado esperado:** el estado indicado.

### QA-04: Solo cuenta la calificación vigente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-01
- **Pasos:**
  1. `analista1` califica SEN-0101 "sustentada" y luego "no sustentada"; calcular.
- **Resultado esperado:** ese par cuenta una sola vez como "no sustentada".

### QA-05: Calificaciones del Administrador no cuentan

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Con C1, `admin.po@prueba.co` califica 5 señales "sustentada"; calcular.
- **Resultado esperado:** el KPI sigue en 74,0 % (37/50) con 4 analistas.

### QA-06: Registrar la línea base con versión y auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-08
- **Pasos:**
  1. Registrar 60 minutos, fuente "D2: 12 casos reales cronometrados, 2026-11" y motivo válido.
- **Resultado esperado:** nueva versión de configuración con línea base 60 y la fuente; evento de auditoría con anterior "no registrada", nuevo 60, fuente y versión.

### QA-07: Reducción que cumple

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-06, RN-07
- **Pasos:**
  1. Con línea base 60 y T1, calcular.
- **Resultado esperado:** promedio 14:30; mediana 13:50; 20 mediciones; reducción 75,8 %; "Cumple (meta provisional 70,0 %)"; las mediciones "sin calificar" e "incompleta" no se usan.

### QA-08: Reducción negativa y límite de la meta

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-06
- **Datos de prueba:**

  | Línea base | Promedio | Reducción | Estado |
  | ----- | ----- | ----- | ----- |
  | 10 | 12:00 | −20,0 % | No cumple |
  | 60 | 18:00 | 70,0 % | Cumple |
  | 60 | 18:06 | 69,8 % | No cumple |

- **Pasos:**
  1. Calcular con cada combinación.
- **Resultado esperado:** la reducción y el estado indicados.

### QA-09: Sin línea base

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Pasos:**
  1. Con línea base "no registrada" y T1, calcular.
- **Resultado esperado:** promedio, mediana y 20 mediciones visibles; reducción "—"; "Línea base no registrada (pendiente de D2)."

### QA-10: Sin calificaciones ni mediciones

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9
- **Pasos:**
  1. En un período sin datos, calcular.
- **Resultado esperado:** "Sin datos: no hay calificaciones de analistas." y "Sin datos: no hay mediciones de tiempo completas."; sin error.

### QA-11: Validación de la línea base

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Línea base | 1 / 10000 | aceptados (con fuente) |
  | Línea base | 0 / 10001 / sesenta | "La línea base debe ser un número entre 1 y 10000 minutos." |
  | Fuente | (vacía) / "D2" | "Debe indicar la fuente de la línea base (10 a 200 caracteres)." |

- **Pasos:**
  1. Registrar cada valor con motivo válido.
- **Resultado esperado:** el resultado indicado; en los rechazos no hay versión nueva.

### QA-12: Período y corte histórico

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-09, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Período | 2026-11-01 a 2026-11-30 | incluye calificaciones del 01 y del 30 |
  | Período | 2026-11-30 a 2026-11-01 | "La fecha inicial no puede ser posterior a la fecha final." |
  | Período | 2025-10-01 a 2026-11-30 | "El rango de consulta no puede superar 365 días." |

- **Pasos:**
  1. Calcular con cada período; consultar el historial.
- **Resultado esperado:** el primero usa solo datos del período y genera un corte con período, versión (con línea base) e indicadores; los otros devuelven el mensaje indicado.

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Generar el reporte; buscar "sobreprecio", "corrupción", "fraude", "hallazgo fiscal".
- **Resultado esperado:** ningún término aparece.

### QA-14: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Pasos:**
  1. Como `analista1@prueba.co`, calcular y registrar línea base.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador."; sin versión nueva.

---

**Total de casos:** 14
