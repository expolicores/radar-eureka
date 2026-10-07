# Casos de Prueba — HU-106: Calcular la precisión de la extracción, global y por campo

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban las fórmulas de precisión por campo y global, la clasificación de cada resultado, el redondeo, la evaluación de la meta y su precedencia de estados, los desgloses, la tabla de calibración, los cortes históricos, el estado vacío y los permisos. Queda fuera: el registro de resultados (HU-105) y la configuración del umbral (HU-102).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Configuración: meta 90,0 %; mínimo 50 elementos con validación completa.
- **Conjunto A** (52 elementos completos): conteos de la tabla del Escenario 1 de la historia.
- **Conjunto B** (50 elementos completos): todos los campos críticos ≥ 90,0 %.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-03, RN-04 | QA-01 |
| Escenario 2, RN-06 | QA-02 |
| Escenario 3, RN-06 | QA-03 |
| Escenario 4, RN-05, RN-06 (límite del mínimo) | QA-04 |
| Escenario 5, RN-06 | QA-05 |
| Escenario 6, RN-02 | QA-06 |
| RN-03 (redondeo y límite de la meta) | QA-07 |
| Escenario 7, RN-07 | QA-08 |
| Escenario 8, RN-08 | QA-09 |
| Escenario 9, RN-09, RN-10 | QA-10 |
| RN-01 (sin doble conteo) | QA-11 |
| Escenario 10 | QA-12 |
| Escenario 11 | QA-13 |

---

## Casos de Prueba

### QA-01: Precisión por campo y global con el conjunto A

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-03, RN-04
- **Pasos:**
  1. Cargar el conjunto A y calcular la precisión.
- **Resultado esperado:** precio unitario 90,0 % (45/50); cantidad 94,0 % (47/50); tamaño 96,0 % (48/50); modelo/referencia 72,0 % (36/50); marca 98,0 % (49/50); global 90,0 % (225/250); por campo se muestran correctos, incorrectos, omitidos ("no encontrados"), inventados ("falsos positivos") y excluidos (ausentes y no verificables). Los campos no críticos aparecen solo en la sección informativa.

### QA-02: Un campo débil impide "Cumple" global

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-06
- **Pasos:**
  1. Revisar los estados del cálculo de QA-01.
- **Resultado esperado:** estados por campo: Cumple, Cumple, Cumple, No cumple (modelo_referencia), Cumple; global "No cumple" con "Campos críticos por debajo de la meta: modelo_referencia (72,0 %)."

### QA-03: Cumplimiento total con el conjunto B

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-06
- **Pasos:**
  1. Cargar el conjunto B y calcular.
- **Resultado esperado:** estado global "Cumple"; todos los campos "Cumple".

### QA-04: Límite del mínimo de elementos completos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-05, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Elementos completos (con precisiones del conjunto B) | 38 | "Muestra insuficiente: 38 de 50 elementos con validación completa." |
  | Elementos completos | 49 | "Muestra insuficiente: 49 de 50 …" |
  | Elementos completos | 50 | "Cumple" |

- **Pasos:**
  1. Calcular con cada tamaño.
- **Resultado esperado:** el estado indicado; con muestra insuficiente se muestran las cifras y ningún estado global dice "Cumple".

### QA-05: Campo crítico sin casos evaluables

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | cantidad | 30 `ausente_y_no_extraido`, 2 `no_verificable` | denominador 0 |

- **Pasos:**
  1. Calcular con 50 elementos completos y ese campo.
- **Resultado esperado:** cantidad: precisión "—", estado "Sin datos"; global "No concluyente: el campo cantidad no tiene casos evaluables."

### QA-06: Excluidos y pendientes fuera del cálculo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | marca | 49 correctos, 1 incorrecto | base |
  | marca | + 3 `no_verificable`, 4 sin resultado, 2 "requiere revalidar" | adicionales |

- **Pasos:**
  1. Calcular antes y después de agregar las filas adicionales.
- **Resultado esperado:** marca sigue en 98,0 % (49/50); el reporte muestra excluidas 3 y pendientes 6.

### QA-07: Redondeo y comparación con la meta

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | precio_unitario | 1.799 / 2.000 = 89,95 % | se muestra 90,0 % → Cumple |
  | precio_unitario | 1.798 / 2.000 = 89,90 % | 89,9 % → No cumple |
  | precio_unitario | 9 / 10 = 90,00 % | 90,0 % → Cumple |

- **Pasos:**
  1. Calcular con cada conteo (resto de campos ≥ 90 %, muestra suficiente).
- **Resultado esperado:** el valor y estado indicados.

### QA-08: Desgloses por tipo de precio, OCR y lote

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | precio_unitario explícito | 40 correctos / 42 evaluables | 95,2 % |
  | precio_unitario derivado | 5 / 8 | 62,5 % |
  | Requiere OCR/multimodal = sí | 110 / 125 | 88,0 % |
  | Lote "2026-10-S1" | 0 evaluables | "—" |

- **Pasos:**
  1. Calcular y revisar los desgloses.
- **Resultado esperado:** cada grupo con numerador, denominador y el porcentaje indicado; grupo sin evaluables con "—".

### QA-09: Tabla de calibración por tramos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-08
- **Datos de prueba:**

  | Confianza | Evaluables | Correctos | Nota |
  | ----- | ----- | ----- | ----- |
  | 0,10 | 1 | 0 | tramo [0,10–0,20) |
  | 0,7999 | 10 | 6 | tramo [0,70–0,80) |
  | 0,80 | 20 | 18 | tramo [0,80–0,90) (límite inferior incluido) |
  | 1,00 | 30 | 30 | tramo [0,90–1,00] |
  | incierta | 4 | 2 | tramo "incierta" |

- **Pasos:**
  1. Calcular y revisar la tabla.
- **Resultado esperado:** cada valor cae en el tramo indicado; para t = 0,80: precisión de los evaluables con confianza ≥ 0,80 = 48/50 = 96,0 % y % que iría a revisión = 15/65 = 23,1 %; el umbral configurado no cambia.

### QA-10: Cortes históricos inmutables

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-09, RN-10
- **Pasos:**
  1. Calcular el 2026-10-02.
  2. Cargar nuevos resultados y calcular el 2026-10-09.
  3. Consultar el historial.
- **Resultado esperado:** dos cortes, del más reciente al más antiguo, con fecha, usuario, versión de configuración, elementos, precisiones y estados; el corte del 2026-10-02 conserva sus cifras originales; calcular no modificó resultados ni configuración.

### QA-11: Un campo marcado por contrato y por documento cuenta una vez

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Precondiciones:** DOC-30542 marcado individualmente y su contrato CO1.PCCNTR.5100200 también; DOC-30542 aporta 5 campos críticos correctos.
- **Pasos:**
  1. Calcular la precisión.
- **Resultado esperado:** esos 5 campos aparecen una sola vez en numerador y denominador.

### QA-12: Sin resultados de validación

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Sin resultados registrados, calcular.
- **Resultado esperado:** "No hay resultados de validación registrados; no es posible calcular la precisión."; no se crea corte.

### QA-13: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 11
- **Pasos:**
  1. Como `analista1@prueba.co`, calcular y consultar el historial.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador." en ambos.

---

**Total de casos:** 13
