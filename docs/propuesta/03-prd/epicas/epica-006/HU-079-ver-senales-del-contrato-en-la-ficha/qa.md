# Casos de Prueba — HU-079: Ver las señales que merecen revisión del contrato en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Señales" de la ficha: señales vigentes, campos, orden, advertencia, navegación al detalle y al ítem, marcas, estados sin señales y sin comparación, comparación parcial, bloque de revisión de calidad, lenguaje, rendimiento, accesibilidad y móvil. Quedan fuera el cálculo de señales y el contenido del detalle de la señal.

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Contrato C1 (SECOP II CO1.PCCNTR.5512001):**

  | Ítem | Estado | Benchmark / referencia | Precio | Desviación | Emparejamiento | Confianza | Marcas |
  | ---- | ------ | ---------------------- | ------ | ---------- | -------------- | --------- | ------ |
  | I1 Samsung UN65CU7000 | señal vigente | Compras públicas $ 2.884.000 | $ 3.900.000 | +35,2 % | Mismo modelo | Alta | |
  | I2 LG 55UR8750 | señal vigente | Compras públicas, Referencia disponible (3 obs.) | $ 2.950.000 | +55,3 % | Producto equivalente | Media | IVA indeterminado; precio derivado |
  | I5 Challenger 43" | revisión de calidad | — | $ 400.000 | −68,0 % | — | — | precio anormalmente bajo |
  | I6 Samsung UN50CU7000 | señal no vigente (recalculada) | — | — | — | — | — | |

- **Contrato C2:** comparaciones calculadas, sin señales.
- **Contrato C3:** sin comparaciones calculadas.
- **Contrato C4:** un ítem con señal vigente y otro sin comparación calculada.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-03 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 / RN-06 | QA-06 |
| Escenario 7 / RN-06 | QA-07 |
| RN-06 comparación parcial | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| RN-08 | QA-10 |
| RN-09 | QA-11 |

---

## Casos de Prueba

### QA-01: Señales vigentes con campos y orden

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-03
- **Pasos:**
  1. Abrir la ficha de C1 en "Señales".
- **Resultado esperado:** título "Señales que merecen revisión (2)"; filas I1 (Alta) y luego I2 (Media); I6 no aparece; I1 muestra "Compras públicas", "$ 2.884.000", "$ 3.900.000", "+35,2 %", "Mismo modelo", "Alta" y "Ver señal".

### QA-02: Advertencia permanente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Ver la sección de C1 a 1366 px y a 360 px.
- **Resultado esperado:** en ambos anchos aparece "Una señal indica que un precio merece revisión. No constituye una conclusión ni una acusación sobre la entidad, el proveedor o las personas relacionadas." antes de la primera señal.

### QA-03: Abrir el detalle de la señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Pasos:**
  1. Activar "Ver señal" en I1 y luego abrir la evidencia desde el detalle.
- **Resultado esperado:** se abre el detalle de la señal de I1 y la evidencia de origen se alcanza con un clic adicional.

### QA-04: Ir a la tarjeta del ítem

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Pasos:**
  1. Activar el nombre "LG 55UR8750".
- **Resultado esperado:** la ficha se desplaza a la tarjeta de I2 en "Ítems de televisor" y la resalta.

### QA-05: Marcas de IVA indeterminado y precio derivado

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-04
- **Pasos:**
  1. Revisar la fila de I2.
- **Resultado esperado:** marcas "IVA indeterminado — comparación incompleta" y "Precio derivado"; referencia "Referencia disponible (3 obs.)".

### QA-06: Contrato sin señales

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-06
- **Pasos:**
  1. Abrir la ficha de C2 en "Señales".
- **Resultado esperado:** "Este contrato no tiene señales que merezcan revisión con la información disponible."; sin advertencia.

### QA-07: Comparaciones no calculadas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-06
- **Pasos:**
  1. Abrir la ficha de C3 en "Señales".
- **Resultado esperado:** "Las señales se mostrarán cuando termine la comparación de los ítems de este contrato."

### QA-08: Comparación parcial

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Abrir la ficha de C4 en "Señales".
- **Resultado esperado:** se muestra la señal vigente y la nota "Algunos ítems aún no tienen comparación calculada."

### QA-09: Precio anormalmente bajo no es señal

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Revisar la sección de C1 debajo de las señales.
- **Resultado esperado:** bloque "En revisión de calidad (1)" con I5 y el texto "Precio muy por debajo de la referencia: se revisa como posible error de extracción, cantidad, producto o base tributaria. No es una señal."; I5 no cuenta en el título de señales.

### QA-10: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-08
- **Pasos:**
  1. Buscar los términos prohibidos en la sección de C1, C2 y C3.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-11: Formatos, rendimiento, teclado y móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-09
- **Precondiciones:** 20 sesiones concurrentes abriendo fichas con señales.
- **Pasos:**
  1. Abrir la ficha de C1 repetidamente durante 10 minutos.
  2. Recorrer la sección con teclado y verla a 360 px.
- **Resultado esperado:** ficha completa en ≤ 3 s (p95); valores "$ 3.900.000" y "+35,2 %"; "Ver señal" y el nombre del ítem se activan con Enter con foco visible; a 360 px cada señal es una tarjeta con todos sus campos y acciones.

---

**Total de casos:** 11
