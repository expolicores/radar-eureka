# Casos de Prueba — HU-111: Consultar el costo por documento procesado con IA y el costo mensual por componente

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el reporte mensual y por rango, los indicadores de costo de IA por documento, el registro manual y por CSV de componentes no IA (validaciones, reemplazo con historial), el manejo de componentes faltantes y monedas, los estados vacíos y los permisos. Queda fuera: el cálculo del costo por documento en la extracción (FR-034, otra épica).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Mes en curso para las pruebas: **2026-12**.
- Noviembre 2026: 320 procesamientos de documentos con IA, costo total 41,60 USD (316 con costo, 4 sin costo; promedio sobre 316); almacenamiento 6,20 USD; cómputo 28,00 USD; búsqueda 9,50 USD.
- Diciembre 2026: costos de IA, almacenamiento y cómputo; búsqueda sin registrar.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-03, RN-06 | QA-01 |
| Escenario 2, RN-06 | QA-02 |
| Escenario 3, RN-06 | QA-03 |
| Escenario 4, RN-04 | QA-04 |
| Escenario 5, RN-04 | QA-05 |
| Escenario 6, RN-04, RN-07 (límites) | QA-06 |
| Escenario 7, RN-02 | QA-07 |
| Escenario 8, RN-05 | QA-08 |
| Escenario 9, RN-02 | QA-09 |
| Escenario 10, RN-03 | QA-10 |
| Escenario 11 | QA-11 |
| Escenario 12, RN-06 | QA-12 |
| Escenario 13 | QA-13 |

---

## Casos de Prueba

### QA-01: Reporte mensual completo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-03, RN-06
- **Precondiciones:** para este caso, los 320 documentos tienen costo.
- **Pasos:**
  1. Consultar el reporte de 2026-11.
- **Resultado esperado:** IA 41,60 USD, 320 documentos, promedio 0,13 USD, mediana, máximo y tiempo promedio de procesamiento; almacenamiento 6,20; cómputo 28,00; búsqueda 9,50; total 85,30 USD; participación 48,8 % / 7,3 % / 32,8 % / 11,1 %.

### QA-02: Componente no registrado

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | búsqueda 2026-12 | sin registro | "no registrado" |
  | almacenamiento 2026-12 | 0,00 USD registrado | se muestra 0,00 |

- **Pasos:**
  1. Consultar 2026-12.
- **Resultado esperado:** búsqueda "no registrado"; almacenamiento 0,00; total marcado "parcial: falta búsqueda"; participación solo sobre componentes registrados.

### QA-03: Totales por moneda sin conversión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-06
- **Pasos:**
  1. Registrar almacenamiento 2026-11 en 24.500 COP y consultar.
- **Resultado esperado:** "USD 79,10 · COP 24.500" (IA + cómputo + búsqueda en USD); participación calculada dentro de cada moneda.

### QA-04: Registrar un costo nuevo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Pasos:**
  1. Sin cómputo para 2026-10, registrar cómputo, 2026-10, 28,00, USD, "Factura del proveedor de nube n.º 1182".
- **Resultado esperado:** "Costo de cómputo para 2026-10 registrado."; registro con usuario y fecha.

### QA-05: Reemplazo con historial

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-04
- **Pasos:**
  1. Registrar cómputo 2026-11 = 31,40 USD.
- **Resultado esperado:** "Costo de cómputo para 2026-11 actualizado (anterior: 28,00 USD)."; historial con el valor anterior, usuario y fecha.

### QA-06: Validaciones del registro

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-04, RN-07
- **Datos de prueba:**

  | Campo | Valor | Resultado esperado |
  | ----- | ----- | ----- |
  | componente | red | "El componente 'red' no es válido. Componentes válidos: almacenamiento, cómputo, búsqueda." |
  | componente | busqueda | aceptado |
  | mes | 2026-13 / 2027-01 | "El mes '…' no es válido; use el formato AAAA-MM y un mes no posterior al actual." |
  | monto | 0 / 1000000000 | aceptados |
  | monto | -1 / 1000000000,01 / 12,345 / doce | "El monto debe ser un número entre 0 y 1000000000 con máximo 2 decimales." |
  | moneda | dólares / usd | "La moneda '…' no es válida; use un código ISO 4217 de 3 letras (ej. USD, COP)." |
  | fuente | (vacía) / "FV" | "Debe indicar la fuente del costo (3 a 200 caracteres)." |

- **Pasos:**
  1. Registrar con cada valor (resto válido).
- **Resultado esperado:** el resultado indicado; en los rechazos no se registra nada.

### QA-07: IA no se registra manualmente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-02
- **Pasos:**
  1. Registrar componente "IA" para 2026-11.
- **Resultado esperado:** "El costo de IA se calcula a partir de los documentos procesados y no se registra manualmente."; el costo de IA no cambia.

### QA-08: Carga CSV parcial

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Archivo | 6 filas; la fila 4 con componente "red" | — |
  | Archivo | 501 filas | rechazado completo por exceder 500 filas |

- **Pasos:**
  1. Cargar cada archivo.
- **Resultado esperado:** primero: "Filas registradas: 5. Rechazadas: 1." con "Fila 4" y el mensaje de componente inválido; segundo: "El archivo supera el máximo de 500 filas." sin registrar ninguna fila.

### QA-09: Detalle de costo por documento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-02
- **Precondiciones:** DOC-30542 se procesó dos veces en 2026-11.
- **Pasos:**
  1. Pedir el detalle de IA de 2026-11 y exportar.
- **Resultado esperado:** 320 filas ordenadas por costo descendente con id, contrato, fecha, costo, moneda y tiempo; DOC-30542 aparece dos veces; CSV UTF-8.

### QA-10: Documentos sin costo

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-03
- **Pasos:**
  1. Con 4 documentos sin costo, consultar 2026-11.
- **Resultado esperado:** promedio sobre 316 documentos; texto "4 documentos procesados sin costo registrado".

### QA-11: Mes sin datos

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11
- **Pasos:**
  1. Consultar 2026-01.
- **Resultado esperado:** "No hay costos registrados para el período consultado."

### QA-12: Rango de meses

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Rango | 2026-10 a 2026-12 | 3 secciones + acumulado |
  | Rango | 2024-12 a 2026-11 | 24 meses: aceptado |
  | Rango | 2024-11 a 2026-11 | 25 meses: "El rango no puede superar 24 meses." |
  | Rango | 2026-12 a 2026-10 | "El mes inicial no puede ser posterior al mes final." |

- **Pasos:**
  1. Consultar cada rango.
- **Resultado esperado:** el resultado indicado.

### QA-13: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar y registrar costos.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador."

---

**Total de casos:** 13
