# Casos de Prueba — HU-071: Filtrar la exploración por fechas, rango de valor y UNSPSC

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban los filtros de fechas de compra (rango manual, abierto y predefinido), rango de valor del contrato u orden y UNSPSC: validaciones, límites, nulos, nota de TVEC, combinación, persistencia, tiempos y accesibilidad. Quedan fuera la vista base (HU-069) y los demás filtros (HU-070, HU-072).

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (rol Analista, sesión activa). **Fecha de ejecución de referencia:** 02/10/2026.
- **Universo semilla:**

  | Registro | Fuente | Fecha de compra | Valor | UNSPSC principal |
  | -------- | ------ | --------------- | ----- | ---------------- |
  | R1 | SECOP II | 01/01/2025 | $ 10.000.000 | V1.52161505 |
  | R2 | SECOP II | 31/12/2025 | $ 50.000.000 | V1.52161505 |
  | R3 | SECOP II | 01/01/2026 | $ 50.000.001 | V1.43211500 |
  | R4 | TVEC | 03/10/2025 | $ 9.999.999 | (no aplica) |
  | R5 | TVEC | 02/10/2025 | $ 12.480.000 | (no aplica) |
  | R6 | SECOP II | (sin fecha) | (sin valor) | (sin UNSPSC) |
  | R7 | SECOP II | 15/06/2023 | $ 123.900.000 | V1.52161505 |

- Fecha de compra más antigua del universo: 15/06/2023.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-02 | QA-05 |
| Escenario 6 / RN-04 / RN-05 | QA-06 |
| Escenario 7 / RN-05 | QA-07 |
| Escenario 8 / RN-06 / RN-08 | QA-08 |
| Escenario 9 / RN-06 | QA-09 |
| RN-06 límite de 5 códigos / RN-07 | QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11 / RN-09 | QA-12 |
| Escenario 12 / RN-11 | QA-13 |
| RN-10 aplicar solo si es válido | QA-04, QA-05, QA-07 |
| RN-11 persistencia | QA-14 |
| RN-12 | QA-15 |
| RN-13 | QA-16 |

---

## Casos de Prueba

### QA-01: Rango de fechas inclusivo en ambos extremos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Desde | 01/01/2025 | coincide con R1 |
  | Hasta | 31/12/2025 | coincide con R2 |

- **Pasos:**
  1. Ingresar las fechas y pulsar "Aplicar".
- **Resultado esperado:** listado R1, R2, R4 y R5 (R3, del 01/01/2026, queda fuera); etiqueta "Fechas: 01/01/2025 – 31/12/2025"; ayuda "Histórico disponible desde 15/06/2023".

### QA-02: Rango predefinido "Últimos 12 meses"

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Elegir "Últimos 12 meses" el 02/10/2026.
  2. Guardar la URL y abrirla en una sesión con fecha simulada 03/10/2026.
- **Resultado esperado:** paso 1 aplica 03/10/2025 – 02/10/2026: aparecen R3 y R4; R5 (02/10/2025) queda fuera; etiqueta "Fechas: Últimos 12 meses (03/10/2025 – 02/10/2026)". Paso 2 recalcula a 04/10/2025 – 03/10/2026 y R4 queda fuera.

### QA-03: Solo fecha inicial o solo fecha final

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Desde | 01/01/2026 | sin "Hasta" |
  | Hasta | 15/06/2023 | sin "Desde" |

- **Pasos:**
  1. Aplicar cada caso por separado.
- **Resultado esperado:** "Desde 01/01/2026" lista R3 con etiqueta "Fechas: desde 01/01/2026"; "Hasta 15/06/2023" lista R7 con etiqueta "Fechas: hasta 15/06/2023".

### QA-04: Fecha inicial posterior a la final no se aplica

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-10
- **Pasos:**
  1. Ingresar "Desde" 01/06/2026 y "Hasta" 01/01/2026 y pulsar "Aplicar".
- **Resultado esperado:** "La fecha inicial no puede ser posterior a la fecha final."; sin etiqueta nueva; listado sin cambios.

### QA-05: Fechas inválidas y futuras

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-02 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Desde | 31/02/2026 | fecha inexistente |
  | Desde | 2026-01-15 | formato distinto |
  | Hasta | 03/10/2026 | hoy + 1 |
  | Hasta | 02/10/2026 | hoy (válido) |

- **Pasos:**
  1. Ingresar cada valor y pulsar "Aplicar".
- **Resultado esperado:** los dos primeros muestran "Ingresa una fecha válida con formato DD/MM/AAAA."; 03/10/2026 muestra "La fecha no puede ser posterior a hoy."; 02/10/2026 se aplica. En los casos inválidos el listado no cambia.

### QA-06: Rango de valor inclusivo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-04 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Valor mínimo | 10000000 | se muestra 10.000.000 |
  | Valor máximo | 50000000 | se muestra 50.000.000 |

- **Pasos:**
  1. Escribir los valores y pulsar "Aplicar".
- **Resultado esperado:** mientras se escribe se muestran separadores de miles; listado R1, R2 y R5 (R4 con $ 9.999.999 y R3 con $ 50.000.001 quedan fuera); etiqueta "Valor: $ 10.000.000 – $ 50.000.000"; ayuda "Valor publicado en datos abiertos; no es el precio unitario del ítem."

### QA-07: Valores no válidos no se aplican

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Mínimo / Máximo | 60.000.000 / 50.000.000 | mínimo > máximo |
  | Mínimo | -1 | negativo |
  | Mínimo | 1500,50 | decimales |
  | Máximo | diez millones | letras |
  | Máximo | 1000000000000 | 13 dígitos |
  | Máximo | 999999999999 | 12 dígitos (válido) |
  | Mínimo | 0 | límite inferior (válido) |

- **Pasos:**
  1. Ingresar cada caso y pulsar "Aplicar".
- **Resultado esperado:** mínimo > máximo muestra "El valor mínimo no puede ser mayor que el valor máximo."; negativo, decimales, letras y 13 dígitos muestran "Ingresa un valor en pesos, solo con números enteros (máximo 12 dígitos)." (o el campo no admite el carácter); 999.999.999.999 y 0 se aplican.

### QA-08: Filtrar por UNSPSC con y sin prefijo y nota de TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-06 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | UNSPSC | 52161505 | sin prefijo |
  | UNSPSC | V1.52161505 | con prefijo |

- **Pasos:**
  1. Agregar cada valor (en ejecuciones separadas).
- **Resultado esperado:** ambos producen la etiqueta "UNSPSC: 52161505" y listan R1, R2 y R7; R4 y R5 (TVEC) no aparecen y se muestra "Los registros de la TVEC no publican código UNSPSC y no aparecen cuando este filtro está activo."

### QA-09: Códigos UNSPSC inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | UNSPSC | 5216150 | 7 dígitos |
  | UNSPSC | 521615051 | 9 dígitos |
  | UNSPSC | 52161505X | carácter no numérico |

- **Pasos:**
  1. Intentar agregar cada código.
- **Resultado esperado:** ninguno se agrega; mensaje "Ingresa un código UNSPSC de 8 dígitos (ej. 52161505)."

### QA-10: Hasta 5 códigos UNSPSC y sugerencias

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06 / RN-07
- **Pasos:**
  1. Enfocar el campo UNSPSC.
  2. Agregar 52161505 y 43211500 (O entre ellos).
  3. Agregar 3 códigos más hasta 5 e intentar un sexto.
- **Resultado esperado:** paso 1 lista "52161505 (3 contratos)" antes que "43211500 (1 contratos)"; paso 2 lista R1, R2, R3 y R7; paso 3 acepta el 5.º código y rechaza el 6.º con "Puedes agregar hasta 5 códigos UNSPSC."

### QA-11: Código válido sin registros

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Agregar el código 52161600.
- **Resultado esperado:** etiqueta "UNSPSC: 52161600" y estado "No encontramos resultados con los filtros aplicados."

### QA-12: Registro sin fecha, valor ni UNSPSC

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-09
- **Pasos:**
  1. Sin filtros, ubicar R6.
  2. Aplicar por separado "Desde 01/01/2020", "Valor mínimo 0" y "UNSPSC 52161505".
- **Resultado esperado:** R6 aparece sin filtros y no aparece con ninguno de los tres filtros activos.

### QA-13: Combinación con un filtro de otra HU

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-11
- **Precondiciones:** R1 y R7 pertenecen a "Alcaldía de Tunja"; R2 a otra entidad.
- **Pasos:**
  1. Aplicar UNSPSC 52161505, fechas 01/01/2025 – 31/12/2025, valor mínimo 5.000.000 y entidad "Alcaldía de Tunja".
- **Resultado esperado:** solo R1, en la página 1.

### QA-14: Persistencia en la URL y al volver de la ficha

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Aplicar fechas, valor y UNSPSC; recargar.
  2. Abrir la ficha de R1 y volver.
- **Resultado esperado:** los tres filtros y sus etiquetas se restauran en ambos casos.

### QA-15: Tiempo de respuesta

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Precondiciones:** volumen del MVP y 20 sesiones concurrentes.
- **Pasos:**
  1. Aplicar repetidamente combinaciones de los tres filtros durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-16: Accesibilidad de calendario y mensajes

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Abrir el calendario de "Desde" con teclado y elegir una fecha con flechas y Enter.
  2. Provocar el error de QA-04 con lector de pantalla activo.
- **Resultado esperado:** el calendario se opera solo con teclado; los campos indican su formato; el mensaje de error se anuncia y queda asociado al campo.

---

**Total de casos:** 16
