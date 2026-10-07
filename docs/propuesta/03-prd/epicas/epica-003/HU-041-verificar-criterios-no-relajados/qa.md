# Casos de Prueba — HU-041: Verificar que ningún emparejamiento use criterios relajados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la verificación de pares vigentes (equivalentes y mismo modelo), el retiro de violaciones, la alerta, los pares desactualizados, el reporte, la muestra de verificación (reparto, faltantes, registro), los veredictos y la exactitud, las validaciones, los permisos y la auditoría. Queda fuera la generación de pares.

## Precondiciones y Datos Base

- Reglas `televisor` v1 vigentes (tamaño, resolución, tecnología, Smart exactos y obligatorios; generación ±1 y marca solo si ambos conocidos).
- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Pares vigentes semilla (manipulados directamente en datos de prueba para simular violaciones):

| Par | Tipo | Situación |
|---|---|---|
| P-01 | EQUIVALENTE | Cumple todo |
| P-02 | EQUIVALENTE | Tamaño 55 vs 58 (exacto) |
| P-03 | EQUIVALENTE | Tecnología nula en candidato (obligatorio) |
| P-04 | EQUIVALENTE | Generación 2022 vs 2024 (tolerancia 1) |
| P-05 | MISMO_MODELO | Modelos `55UA7300PSA` vs `55UA7300PSB`, sin EAN |
| P-06 | MISMO_MODELO | Cumple (SAMSUNG · UN55DU8000KXZL) |
| P-07 | EQUIVALENTE | Cumple, calculado con `version_reglas = 1` cuando la vigente es 2 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-05 | QA-01 |
| Escenario 2 / RN-02, RN-03 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-07 | QA-07 |
| Escenario 8 / RN-08 | QA-08, QA-09 |
| Escenario 9 / permisos | QA-10 |
| RN-06 (frecuencia) | QA-11 |
| RN-09 (validaciones) | QA-12, QA-13 |
| RN-10 (auditoría) | QA-14 |

---

## Casos de Prueba

### QA-01: Verificación conforme

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-05
- **Precondiciones:** solo existen P-01 y P-06.
- **Resultado esperado:** reporte con inicio y fin, 1 mismo modelo y 1 equivalente verificados, `violaciones = 0`, `pares_desactualizados = 0`, resultado "Conforme"; sin alerta.

### QA-02: Violaciones de criterio obligatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02, RN-03
- **Pasos:**
  1. Ejecutar la verificación con P-02 y P-03.
- **Resultado esperado:** ambos listados como violación (criterio, valores `55 vs 58` y `tecnologia: LED vs desconocido`, versión 1); ambos `vigente = no` con `RETIRADO_POR_VERIFICACION`; sus ítems marcados para recálculo; resultado "No conforme"; alerta generada al Administrador.

### QA-03: Tolerancia excedida

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | P-04 | 2022 vs 2024 | Diferencia 2 → violación |
  | P-08 | 2023 vs 2024 | Diferencia 1 → conforme |

- **Resultado esperado:** P-04 retirado como violación; P-08 sigue vigente.

### QA-04: Mismo modelo sin igualdad exacta

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | P-05 | `55UA7300PSA` vs `55UA7300PSB` | Sufijo distinto |
  | P-09 | mismo modelo, tamaño 55 vs 65 | Conflicto de control |
  | P-10 | EAN igual, marcas SAMSUNG vs LG | Conflicto de marca |

- **Resultado esperado:** los tres retirados como violación; P-06 sigue vigente.

### QA-05: Pares desactualizados

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | P-07 | `version_reglas = 1`, vigente 2 | Reglas obsoletas |
  | P-11 | referencia una versión no vigente del candidato | Producto obsoleto |

- **Resultado esperado:** `pares_desactualizados = 2`, listados y marcados para recálculo; no cuentan como violación ni se retiran; si no hay violaciones, resultado "Conforme".

### QA-06: Muestra de 50 repartida 25/25

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-07
- **Precondiciones:** 40 pares vigentes `MISMO_MODELO` y 200 `EQUIVALENTE`.
- **Pasos:**
  1. Con `admin.po`, solicitar una muestra de 50.
  2. Solicitar otra muestra con la misma semilla.
- **Resultado esperado:** paso 1: 25 y 25 pares distintos, cada uno con descripción original, atributos de ambos productos, tipo y criterios; muestra registrada con identificador, fecha, usuario, semilla y copia de datos. Paso 2: misma selección de pares.

### QA-07: Tipo con pares insuficientes y tamaño impar

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Disponibles | 10 mismo modelo, 200 equivalentes; muestra 50 | 10 + 40 |
  | Disponibles | 10 mismo modelo, 20 equivalentes; muestra 50 | 10 + 20 = 30 |
  | Disponibles | 40 / 200; muestra 51 | 25 + 26 |

- **Resultado esperado:** 10 + 40 con aviso "Muestra de mismo modelo menor a 25: 10"; 10 + 20 con ambos avisos; 25 mismo modelo + 26 equivalentes.

### QA-08: Exactitud y cumplimiento por tipo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mismo modelo | 24 correctos / 25 | 96,00 % → Cumple (≥ 95) |
  | Equivalente | 22 correctos / 25 | 88,00 % → No cumple (≥ 90) |
  | Límite | 19 / 20 mismo modelo | 95,00 % → Cumple |

- **Resultado esperado:** exactitudes y dictámenes de la columna Nota; los pares marcados "Incorrecto" siguen vigentes.

### QA-09: Muestra incompleta y cambio de veredicto

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Registrar veredictos en 48 de 50 pares.
  2. Consultar el resultado.
  3. Cambiar un veredicto de "Correcto" a "Incorrecto".
- **Resultado esperado:** paso 2: "Muestra incompleta: 2 pares sin veredicto", sin cumplimiento. Paso 3: queda el nuevo veredicto y el historial conserva el anterior con usuario y fecha.

### QA-10: Analista sin permiso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9
- **Pasos:**
  1. Con `analista.piloto1`, ejecutar la verificación, generar una muestra y registrar un veredicto.
- **Resultado esperado:** las tres acciones se rechazan por falta de permiso y no se registran efectos.

### QA-11: Ejecución automática tras el emparejamiento

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Ejecutar un emparejamiento completo.
- **Resultado esperado:** al terminar existe un nuevo reporte de verificación con usuario "sistema".

### QA-12: Validaciones de parámetros

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tamaño de muestra | 1 | Mín−1 |
  | Tamaño de muestra | 2 | Mínimo → válido |
  | Tamaño de muestra | 500 | Máximo → válido |
  | Tamaño de muestra | 501 | Máx+1 |
  | Meta equivalente | 101 % | Fuera de rango |
  | Comentario | 501 caracteres | Excede |
  | Comentario | 500 caracteres | Límite → válido |
  | Veredicto | "Dudoso" | No permitido |
  | Veredicto | par fuera de la muestra | No pertenece |

- **Resultado esperado:** los inválidos se rechazan con "Parámetro inválido: {detalle}"; los válidos se aceptan.

### QA-13: Sin pares vigentes

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Resultado esperado:** con 0 pares vigentes, la solicitud de muestra responde "No hay emparejamientos vigentes para muestrear" y no se registra muestra; la verificación termina "Conforme" con 0 verificados.

### QA-14: Auditoría

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Resultado esperado:** tras QA-02, QA-06 y QA-08, la auditoría contiene la ejecución, los retiros, la muestra y los veredictos con usuario (o "sistema"), fecha y hora; los reportes anteriores no se modificaron.

---

**Total de casos:** 14
