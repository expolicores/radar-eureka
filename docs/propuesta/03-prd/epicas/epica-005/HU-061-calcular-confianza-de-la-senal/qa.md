# Casos de Prueba — HU-061: Calcular el nivel de confianza de la comparación y de la señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el puntaje (100 − penalizaciones), cada factor, los cortes de nivel, el tope por base tributaria incompleta, la garantía de que un precio derivado reduce la confianza, el desglose, la herencia por versión de señal y los parámetros. Queda fuera la presentación visual (HU-063).

## Precondiciones y Datos Base

- Penalizaciones iniciales: F1 0/20; F2 0/25; F3 0/10/30; F4 0/10; F5 0/15; F6 0/5/10. Cortes: Alta 75, Media 50.
- **Caso base CB:** SECOP II CO1.PCCNTR.9990001, precio `explicito` validado por revisor, Benchmark 1 "Referencia estadística", "Mismo modelo", base "Completa – precio final con IVA", referencias públicas (sin manuales).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 | QA-01 |
| Escenario 2 / RN-03 F5 | QA-02 |
| Escenario 3 / RN-03 F1, F2 | QA-03 |
| Escenario 4 / RN-06 | QA-04 |
| Escenario 5 / RN-03 F6 | QA-05 |
| RN-03 F6 ≤ 50 % | QA-06 |
| Escenario 6 / RN-03 F3, F4 | QA-07 |
| Escenario 7 / RN-05 | QA-08 |
| RN-02 mínimo 0 | QA-09 |
| RN-01 sin referencia | QA-10 |
| Escenario 8 / RN-08 | QA-11 |
| Escenario 9 / RN-04, RN-09 | QA-12 |
| RN-07 desglose | QA-13 |

---

## Casos de Prueba

### QA-01: Caso más sólido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02
- **Pasos:**
  1. Calcular la confianza de CB.
- **Resultado esperado:** Puntaje 100, nivel "Alta", 0 puntos en los 6 factores.

### QA-02: Derivado frente a explícito

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tipo de precio | `derivado` | Resto igual a CB |

- **Pasos:**
  1. Calcular CB y CB derivado.
- **Resultado esperado:** 100 frente a 85; el desglose de la variante muestra "Tipo de precio unitario: derivado −15".

### QA-03: Equivalente, evidencia limitada y derivado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Pasos:**
  1. Calcular con conjunto "Producto equivalente", "Referencia disponible – evidencia limitada" y precio `derivado`.
- **Resultado esperado:** Puntaje 40, nivel "Baja".

### QA-04: Tope por base tributaria incompleta

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem | TVEC orden 150001 (estructurado) | F4 = 0 |
  | Base | Incompleta | F3 = −30 |

- **Pasos:**
  1. Calcular.
- **Resultado esperado:** Puntaje 70, nivel "Baja" con la nota "Nivel limitado a Baja: comparación incompleta por base tributaria".

### QA-05: Más de la mitad de las observaciones manuales

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Benchmark 2 | 2 observaciones, ambas manuales | Evidencia limitada |

- **Pasos:**
  1. Calcular.
- **Resultado esperado:** Puntaje 65, nivel "Media".

### QA-06: Manuales en exactamente el 50 %

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Benchmark 2 | 4 observaciones de 2 fuentes, 2 manuales | 50 %: −5 |
  | Variante | 4 observaciones, 3 manuales | 75 %: −10 |

- **Pasos:**
  1. Calcular cada variante (referencia estadística, mismo modelo, base completa).
- **Resultado esperado:** 95 "Alta" y 90 "Alta".

### QA-07: Conversión de IVA y extracción automática

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-03
- **Pasos:**
  1. Calcular CB con base "Completa (incluye valores convertidos)" y precio aceptado automáticamente.
- **Resultado esperado:** Puntaje 80, nivel "Alta".

### QA-08: Cortes de nivel

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Equivalente + 1 manual ≤ 50 % | 75 | Alta |
  | Evidencia limitada + derivado + aceptado automático | 50 | Media |
  | Evidencia limitada + derivado + aceptado automático + 1 manual ≤ 50 % | 45 | Baja |

- **Pasos:**
  1. Calcular cada combinación.
- **Resultado esperado:** Niveles según la tabla.

### QA-09: Puntaje no baja de 0

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Penalización F2 evidencia limitada | 60 | Configurada |
  | Caso | Equivalente, evidencia limitada, incompleta, derivado | 100 − 20 − 60 − 30 − 15 = −25 |

- **Pasos:**
  1. Calcular.
- **Resultado esperado:** Puntaje 0, nivel "Baja".

### QA-10: Comparación sin referencia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Calcular para un Benchmark 2 "No disponible / evidencia insuficiente".
- **Resultado esperado:** Confianza "No aplica"; sin puntaje.

### QA-11: Confianza por versión de señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Generar una señal con CB derivado (85 "Alta").
  2. Recalcular con conjunto que pasa a equivalente y evidencia limitada (100 − 20 − 25 − 15 = 40) manteniendo la señal.
- **Resultado esperado:** Versión 2 con 40 "Baja"; versión 1 conserva 85 "Alta".

### QA-12: Parámetros inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-04 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Penalización F1 equivalente | −5 | Negativa → 20 |
  | Penalización F5 derivado | 0 | Viola RN-04 → 15 |
  | `confianza_corte_media` | 80 con alta 75 | Viola RN-05 → 50 |

- **Pasos:**
  1. Configurar cada valor y calcular.
- **Resultado esperado:** Se usa el valor inicial indicado y se registra "Parámetro {nombre} inválido; se usó el valor inicial {valor}".

### QA-13: Desglose completo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Calcular QA-04 y consultar el resultado.
- **Resultado esperado:** Se listan F1 a F6 con condición y puntos (F3 "Incompleta −30"), puntaje 70, nivel "Baja", nota de tope y parámetros usados.

---

**Total de casos:** 13
