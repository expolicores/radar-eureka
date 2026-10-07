# Casos de Prueba — HU-072: Filtrar la exploración por territorio, fuente y existencia de señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban los filtros Territorio (departamento, municipio, sin información territorial), Fuente y Señal: opciones, normalización de nombres, lógica entre departamento y municipio, nulos, restricción de fuente, señal vigente en ambos modos, estado sin señales, combinación, persistencia, lenguaje, tiempos y accesibilidad. Quedan fuera el cálculo de señales (otro proceso de la plataforma) y los demás filtros.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (rol Analista, sesión activa).
- **Universo semilla:**

  | Registro | Fuente | Departamento | Municipio | Ítems y señal |
  | -------- | ------ | ------------ | --------- | ------------- |
  | R1 | SECOP II | BOYACÁ | TUNJA | 2 ítems: I1 con señal vigente, I2 sin señal |
  | R2 | SECOP II | Boyaca | Duitama | 1 ítem sin señal |
  | R3 | TVEC | Santander | Bucaramanga | 1 ítem con señal vigente |
  | R4 | SECOP II | Santander | Bucaramanga | 1 ítem con precio anormalmente bajo en revisión de calidad (sin señal) |
  | R5 | SECOP II | (sin dato) | (sin dato) | identificado, sin comparación |
  | R6 | SECOP II | Santander | (sin dato) | 1 ítem con señal vigente |
  | R7 | TVEC | Bogotá, D.C. | Bogotá, D.C. | 1 ítem sin señal |
  | R8 | SECOP II | BOGOTA D.C. | BOGOTA D.C. | 1 ítem sin señal |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-03 | QA-01, QA-02 |
| Escenario 2 / RN-04 | QA-03 |
| Escenario 3 | QA-04 |
| Escenario 4 | QA-05 |
| Escenario 5 / RN-05 | QA-06 |
| Escenario 6 / RN-06 | QA-07 |
| Escenario 7 | QA-08 |
| Escenario 8 / RN-07 / RN-09 | QA-09 |
| Escenario 9 / RN-08 | QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11 / RN-11 | QA-12 |
| RN-10 lenguaje | QA-13 |
| RN-11 persistencia | QA-14 |
| RN-12 | QA-15 |
| RN-13 | QA-16 |

---

## Casos de Prueba

### QA-01: Filtrar por departamento agrupando variantes de escritura

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-03
- **Pasos:**
  1. Abrir "Territorio" y marcar "Boyacá".
- **Resultado esperado:** la lista de departamentos muestra una sola opción para BOYACÁ/Boyaca con "(2)"; el listado muestra R1 y R2; etiqueta "Departamento: Boyacá".

### QA-02: Variantes de Bogotá se agrupan en una opción

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Revisar la lista de departamentos y marcar la opción de Bogotá.
- **Resultado esperado:** una sola opción de Bogotá con "(2)"; listado R7 y R8.

### QA-03: Municipio dentro de departamentos y lógica combinada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04
- **Pasos:**
  1. Marcar "Boyacá" y abrir "Municipio".
  2. Marcar "Tunja (Boyacá)".
  3. Marcar además el departamento "Santander".
- **Resultado esperado:** paso 1 lista solo Tunja (Boyacá) y Duitama (Boyacá); paso 2 muestra R1 con etiqueta "Municipio: Tunja (Boyacá)"; paso 3 muestra R1, R3, R4 y R6 (Tunja + todo Santander).

### QA-04: Municipio deshabilitado sin departamento

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 3
- **Pasos:**
  1. Sin departamentos marcados, observar "Municipio".
- **Resultado esperado:** selector deshabilitado con la ayuda "Elige primero uno o más departamentos."

### QA-05: Quitar departamento elimina sus municipios

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Precondiciones:** "Boyacá", "Santander" y "Tunja (Boyacá)" marcados.
- **Pasos:**
  1. Desmarcar "Boyacá".
- **Resultado esperado:** desaparecen la selección y la etiqueta "Municipio: Tunja (Boyacá)"; listado R3, R4 y R6.

### QA-06: Registros sin información territorial

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-05
- **Pasos:**
  1. Marcar solo "Sin información territorial".
  2. Marcar además "Santander".
  3. Marcar "Bucaramanga (Santander)".
- **Resultado esperado:** paso 1 lista R5 con opción "Sin información territorial (1)"; paso 2 lista R5, R3, R4 y R6; paso 3 lista R5, R3 y R4 (R6, sin municipio, no cumple el filtro de municipio).

### QA-07: Filtrar por una sola fuente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-06
- **Pasos:**
  1. Verificar que ambas fuentes están marcadas y no hay etiqueta de fuente.
  2. Desmarcar "TVEC".
- **Resultado esperado:** paso 1 lista los 8 registros; paso 2 lista R1, R2, R4, R5, R6 y R8 con etiqueta "Fuente: SECOP II".

### QA-08: No se pueden desmarcar ambas fuentes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. Con solo "SECOP II" marcada, intentar desmarcarla.
- **Resultado esperado:** la casilla sigue marcada y aparece "Debe quedar al menos una fuente seleccionada."

### QA-09: Con señal en modo contratos y en modo ítems

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07 / RN-09
- **Pasos:**
  1. En modo "Contratos" elegir "Con señal que merece revisión".
  2. Cambiar a modo "Ítems de televisor".
- **Resultado esperado:** paso 1 lista R1, R3 y R6 (R4 no aparece: precio bajo en revisión de calidad no es señal); etiqueta "Señal: con señal que merece revisión". Paso 2 lista I1, el ítem de R3 y el de R6; I2 no aparece.

### QA-10: Sin señal incluye registros sin comparación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-08
- **Pasos:**
  1. En modo "Contratos" elegir "Sin señal".
- **Resultado esperado:** lista R2, R4, R5, R7 y R8 (R1 tiene un ítem con señal y no aparece); etiqueta "Señal: sin señal".

### QA-11: Universo sin señales generadas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Precondiciones:** ambiente donde ningún ítem tiene señal vigente.
- **Pasos:**
  1. Elegir "Con señal que merece revisión".
- **Resultado esperado:** "Todavía no hay señales que merezcan revisión con los filtros aplicados." y botón "Limpiar filtros".

### QA-12: Combinación de territorio, fuente y señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-11
- **Pasos:**
  1. Marcar "Santander", dejar solo "SECOP II" y elegir "Con señal que merece revisión".
- **Resultado esperado:** solo R6, en la página 1.

### QA-13: Lenguaje no acusatorio en etiquetas y mensajes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-10
- **Pasos:**
  1. Recorrer la sección "Señal", sus etiquetas y el mensaje de QA-11.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-14: Persistencia de los filtros

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Aplicar la combinación de QA-12, recargar, abrir la ficha de R6 y volver.
- **Resultado esperado:** los tres filtros y sus etiquetas se mantienen.

### QA-15: Tiempo de respuesta

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Precondiciones:** volumen del MVP y 20 sesiones concurrentes.
- **Pasos:**
  1. Aplicar combinaciones de territorio, fuente y señal durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-16: Operación con teclado

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Recorrer con Tab las secciones, marcar casillas con barra espaciadora y cambiar la opción de "Señal" con flechas.
- **Resultado esperado:** todas las opciones se operan con teclado con foco visible; el lector de pantalla anuncia el selector de municipio como deshabilitado junto con su ayuda.

---

**Total de casos:** 16
