# Casos de Prueba — HU-073: Ordenar los resultados de la exploración por desviación, valor, fecha o confianza

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el control de orden de la exploración: los cuatro criterios en ambos sentidos y ambos modos, definición de desviación y confianza a nivel de contrato, nulos al final, desempate, orden por defecto e inválido, persistencia, conjunto sin datos, tiempos y accesibilidad. Queda fuera el cálculo de desviaciones y confianza.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (rol Analista, sesión activa).
- **Universo semilla (modo "Contratos"):**

  | Registro | Identificador | Fecha | Valor | Ítems: precio unitario / desviación / confianza de señal |
  | -------- | ------------- | ----- | ----- | -------------------------------------------------------- |
  | R1 | CO1.PCCNTR.1001 | 10/09/2026 | $ 22.900.000 | I1: $ 2.862.500 / +35,2 % / Alta (señal); I2: $ 1.900.000 / +4,0 % / sin señal |
  | R2 | CO1.PCCNTR.1002 | 10/09/2026 | $ 50.000.000 | I3: $ 3.100.000 / +58,0 % / Baja (señal) |
  | R3 | 98765 (TVEC) | 01/08/2026 | $ 12.480.000 | I4: $ 2.080.000 / −12,5 % / sin señal |
  | R4 | CO1.PCCNTR.1004 | 15/03/2025 | (sin valor) | I5: $ 2.500.000 / +35,2 % / Media (señal) |
  | R5 | CO1.PCCNTR.1005 | (sin fecha) | $ 9.000.000 | sin ítems extraídos |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-07 | QA-01 |
| Escenario 2 / RN-03 | QA-02, QA-03 |
| Escenario 3 / RN-04 | QA-04 |
| Escenario 4 / RN-05 | QA-05 |
| Escenario 5 / RN-08 | QA-06 |
| Escenario 6 / RN-06 | QA-07 |
| Escenario 7 / RN-09 / RN-11 | QA-08 |
| Escenario 8 / RN-10 | QA-09 |
| Escenario 9 | QA-10 |
| RN-11 persistencia | QA-11 |
| RN-12 | QA-12 |
| RN-13 | QA-13 |

---

## Casos de Prueba

### QA-01: Desviación de mayor a menor en modo contratos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-07
- **Pasos:**
  1. Elegir "Desviación" — "Mayor a menor".
- **Resultado esperado:** orden R2 (+58,0 %), R1 (+35,2 %, fecha 10/09/2026), R4 (+35,2 %, fecha 15/03/2025), R3 (−12,5 %), R5 (sin dato, al final); página 1.

### QA-02: Valor en modo contratos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Elegir "Valor" — "Mayor a menor".
- **Resultado esperado:** R2 ($ 50.000.000), R1, R3, R5 ($ 9.000.000), R4 (sin valor, al final).

### QA-03: Valor en modo ítems usa el precio unitario

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Cambiar a "Ítems de televisor" con "Valor" — "Mayor a menor".
- **Resultado esperado:** I3 ($ 3.100.000), I1, I5, I4, I2 ($ 1.900.000).

### QA-04: Fecha más antigua primero con nulos al final

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-04
- **Pasos:**
  1. Elegir "Fecha" — "Más antigua primero".
- **Resultado esperado:** R4 (15/03/2025), R3, R1 (CO1.PCCNTR.1001), R2 (CO1.PCCNTR.1002), R5 (sin fecha, al final).

### QA-05: Nivel de confianza con escala ordinal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Elegir "Nivel de confianza" — "Mayor a menor" en modo "Contratos".
  2. Cambiar a "Menor a mayor".
- **Resultado esperado:** paso 1: R1 (Alta), R4 (Media), R2 (Baja), luego R3 y R5 sin señal (ordenados por fecha: R3, R5). Paso 2: R2 (Baja), R4 (Media), R1 (Alta), luego R3 y R5 al final.

### QA-06: Empates resueltos por fecha e identificador

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Empate por desviación | R1 y R4 con +35,2 % | fechas distintas |
  | Empate por fecha | R1 y R2 con 10/09/2026 | identificadores distintos |

- **Pasos:**
  1. Ordenar por "Desviación" — "Mayor a menor" y repetir 3 veces.
  2. Ordenar por "Fecha" — "Más reciente primero".
- **Resultado esperado:** paso 1: R1 siempre antes que R4 en las 3 repeticiones; paso 2: R1 (CO1.PCCNTR.1001) antes que R2 (CO1.PCCNTR.1002).

### QA-07: Invertir el sentido desde el encabezado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-06
- **Precondiciones:** orden "Desviación — Mayor a menor", en página 2 del universo ampliado.
- **Pasos:**
  1. Activar el encabezado "Mayor desviación".
- **Resultado esperado:** orden R3 (−12,5 %), R1, R4, R2, y R5 sigue al final; vuelve a la página 1; el selector muestra "Menor a mayor".

### QA-08: Orden conservado al paginar, filtrar y cambiar de modo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-09 / RN-11
- **Precondiciones:** universo ampliado (> 25 registros) con orden "Valor — Mayor a menor".
- **Pasos:**
  1. Ir a la página 2.
  2. Aplicar el filtro "Fuente: SECOP II".
  3. Cambiar a modo "Ítems de televisor".
- **Resultado esperado:** la página 2 continúa el orden descendente del conjunto completo (su primer registro tiene un valor ≤ el último de la página 1); tras el filtro y el cambio de modo el criterio "Valor — Mayor a menor" se mantiene.

### QA-09: Orden por defecto y valor inválido en la URL

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | orden en URL | (ausente) | |
  | orden en URL | popularidad | criterio inexistente |
  | sentido en URL | diagonal | sentido inexistente |

- **Pasos:**
  1. Abrir la exploración con cada URL.
- **Resultado esperado:** en todos los casos se aplica "Fecha — Más reciente primero", el control lo refleja y no se muestra error.

### QA-10: Ningún resultado con desviación calculada

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9
- **Precondiciones:** filtro que deja solo R5.
- **Pasos:**
  1. Ordenar por "Desviación".
  2. Ordenar por "Nivel de confianza".
- **Resultado esperado:** notas "Ningún resultado tiene todavía un valor calculado de desviación; se muestran por fecha." y "Ningún resultado tiene todavía un valor calculado de nivel de confianza; se muestran por fecha."; R5 listado.

### QA-11: Persistencia al recargar y al volver de la ficha

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Ordenar por "Nivel de confianza — Mayor a menor", recargar, abrir la ficha de R1 y volver.
- **Resultado esperado:** el orden se mantiene en ambos casos.

### QA-12: Tiempo de respuesta al cambiar el orden

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Precondiciones:** volumen del MVP y 20 sesiones concurrentes.
- **Pasos:**
  1. Alternar criterios y sentidos durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-13: Orden accesible con teclado y lector de pantalla

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Llegar con Tab al encabezado "Fecha" y activarlo con Enter.
- **Resultado esperado:** el orden cambia; el encabezado muestra la flecha y el lector de pantalla anuncia "Fecha, orden ascendente" o "descendente" según corresponda.

---

**Total de casos:** 13
