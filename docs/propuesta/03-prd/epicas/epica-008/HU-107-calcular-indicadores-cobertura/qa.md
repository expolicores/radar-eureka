# Casos de Prueba — HU-107: Calcular los tres indicadores de cobertura sobre SECOP II, con TVEC aparte

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la disponibilidad en la fuente (principal y complementaria), la cobertura de extracción con sus condiciones y estados, la cobertura end-to-end por contrato y por ítem con sus variantes, el embudo, la separación de TVEC, los estados vacíos, los cortes históricos y los permisos. Queda fuera: la validación manual (HU-105) y los cálculos de benchmark (otra épica).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Configuración: meta de cobertura de extracción 80,0 %; mínimo de muestra 50; ventana histórica desde 2023-01-01.
- **Muestra M1:** 50 contratos con veredicto completo; 36 con ES_COMPRA = si; 17 con (si, si); de los 17: 14 cumplen RN-04 automáticamente, 2 solo con intervención humana, 1 no alcanzado.
- **Universo U1:** 355 contratos SECOP II candidatos (470 ítems); 98 contratos / 121 ítems con comparación utilizable automática; 40 contratos adicionales solo con comparaciones incompletas por base tributaria; 15 contratos con comparación utilizable solo tras corrección humana.
- **TVEC T1:** 1.150 ítems candidatos; 1.020 confirmados; 870 con comparación utilizable.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-03 | QA-01 |
| Escenario 2, RN-04, RN-05 | QA-02 |
| RN-04 (tabla de decisión de condiciones) | QA-03 |
| Escenario 3, RN-05 (límite de la meta) | QA-04 |
| Escenario 4, RN-05 | QA-05 |
| Escenario 5, RN-01, RN-06 | QA-06 |
| Escenario 6, RN-07 | QA-07 |
| Escenario 7, Escenario 8, RN-06 | QA-08 |
| Escenario 9, RN-08 | QA-09 |
| Escenario 10, RN-05 (sin elegibles) | QA-10 |
| Escenario 11, RN-09 | QA-11 |
| Escenario 12, RN-10 | QA-12 |
| Escenario 13 | QA-13 |

---

## Casos de Prueba

### QA-01: Disponibilidad principal y complementaria

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-03
- **Pasos:**
  1. Con M1, calcular la cobertura.
- **Resultado esperado:** disponibilidad 34,0 % (17/50) y complementaria 47,2 % (17/36); estado "Se reporta (sin meta)".

### QA-02: Cobertura de extracción que cumple

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-04, RN-05
- **Pasos:**
  1. Con M1, calcular.
- **Resultado esperado:** 82,4 % (14/17); "Cumple (meta provisional 80,0 %)"; "con intervención humana: 2; no alcanzados: 1".

### QA-03: Condiciones del numerador de cobertura de extracción

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-04
- **Datos de prueba:**

  | Contrato elegible | Información suficiente | Cantidad y precio `correcto` | Pasó por revisión / corregido | Resultado |
  | ----- | ----- | ----- | ----- | ----- |
  | E1 | sí (precio explícito) | sí | no | numerador |
  | E2 | sí (precio derivado) | sí | no | numerador |
  | E3 | sí | precio `incorrecto` | no | no alcanzado |
  | E4 | sí | sí | sí (precio corregido) | con intervención humana |
  | E5 | no (información insuficiente) | — | no | no alcanzado |
  | E6 | 2 ítems: ítem 1 no, ítem 2 sí y `correcto` sin revisión | — | — | numerador (basta un ítem) |
  | E7 | sí | sí | clasificación pasó por revisión | con intervención humana |

- **Pasos:**
  1. Calcular con una muestra formada solo por E1–E7 (más 43 contratos no elegibles para alcanzar 50 con veredicto).
- **Resultado esperado:** cobertura 42,9 % (3/7); con intervención humana 2; no alcanzados 2.

### QA-04: Límite de la meta y nota de recalibración

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Numerador / elegibles | 16 / 20 = 80,0 % | Cumple |
  | Numerador / elegibles | 12 / 17 = 70,6 % | No cumple |
  | Numerador / elegibles | 1.599 / 2.000 = 79,95 % → 80,0 % | Cumple (redondeo) |

- **Pasos:**
  1. Calcular con cada combinación (muestra suficiente).
- **Resultado esperado:** el estado indicado; en "No cumple" aparece la nota "Meta provisional sujeta a calibración con D4-4. Si la evidencia muestra que no es técnicamente razonable, se propone una recalibración explícita; no se reduce automáticamente."; la meta configurada no cambia.

### QA-05: Muestra insuficiente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Contratos con veredicto completo | 30 | "Muestra insuficiente: 30 de 50 contratos con veredicto." |
  | Contratos con veredicto completo | 49 | "Muestra insuficiente: 49 de 50 …" |
  | Contrato con ES_COMPRA = si y EXISTE_INFO vacío | — | no cuenta como veredicto completo |

- **Pasos:**
  1. Calcular en cada situación.
- **Resultado esperado:** cifras de (a) y (b) visibles; estado de (b) "Muestra insuficiente…", nunca "Cumple".

### QA-06: End-to-end por contrato y por ítem

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-01, RN-06
- **Precondiciones:** U1 más un contrato firmado el 2022-12-15 marcado como candidato.
- **Pasos:**
  1. Calcular la cobertura.
- **Resultado esperado:** por contrato 27,6 % (98/355); por ítem 25,7 % (121/470); el contrato de 2022 no entra al universo; estado "Se reporta".

### QA-07: Embudo de pérdidas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-07
- **Datos de prueba:**

  | Etapa | Contratos |
  | ----- | ----- |
  | Candidatos | 355 |
  | Confirmados compra de TV | 256 |
  | Con documentos obtenidos | 240 |
  | Con ítem con información suficiente | 120 (120 en "información insuficiente": 95 "sin precio unitario publicado", 25 "solo valor global") |
  | Con comparación utilizable automática | 98 |

- **Pasos:**
  1. Calcular y revisar el embudo.
- **Resultado esperado:** cada etapa con su conteo y pérdida: 99 (27,9 %), 16 (6,3 %), 120 (50,0 %), 22 (18,3 %); motivos de información insuficiente con sus conteos.

### QA-08: Variantes por base tributaria e intervención humana

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, Escenario 8, RN-06
- **Pasos:**
  1. Con U1, calcular.
- **Resultado esperado:** principal 27,6 % (98/355) sin los 40 ni los 15; variante "incluyendo comparaciones incompletas por base tributaria" 38,9 % (138/355); "con intervención humana: 15".

### QA-09: TVEC separada de SECOP II

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-08
- **Pasos:**
  1. Calcular con U1 y T1.
  2. Calcular con U1 y sin datos TVEC.
- **Resultado esperado:** sección "TVEC (reporte aparte)" con 1.150 / 1.020 / 870 y 75,7 %; los indicadores (a), (b) y (c) de SECOP II son idénticos en ambos cálculos.

### QA-10: Sin veredictos o sin elegibles

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Muestra | sin veredictos | (a) y (b): "Sin datos: no hay contratos con veredicto en la muestra." |
  | Muestra | 50 con veredicto, 0 elegibles | (a) 0,0 % (0/50); (b) "—" con "Sin contratos elegibles en la muestra." |

- **Pasos:**
  1. Calcular en cada situación.
- **Resultado esperado:** el texto indicado; (c) y TVEC calculados normalmente.

### QA-11: Universo vacío sin división por cero

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 11, RN-09
- **Pasos:**
  1. Con 0 candidatos SECOP II, calcular.
- **Resultado esperado:** (c) "—" con "Sin contratos candidatos SECOP II en el alcance."; el cálculo termina sin error.

### QA-12: Cortes históricos inmutables

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-10
- **Pasos:**
  1. Calcular el 2026-10-02; cambiar datos; calcular el 2026-10-09; consultar historial.
- **Resultado esperado:** dos cortes con fecha, fechas de corte SECOP II y TVEC, versión de configuración e indicadores; el primero conserva sus cifras; calcular no modificó datos.

### QA-13: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como `analista1@prueba.co`, calcular y consultar el historial.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador."

---

**Total de casos:** 13
