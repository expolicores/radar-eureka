# Casos de Prueba — HU-074: Ver la lista priorizada de señales que merecen revisión

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la vista "Señales": contenido (señales vigentes, una por ítem), prioridad por defecto, columnas y marcas, advertencia, navegación al detalle y a la ficha (≤ 3 clics hasta la evidencia), estados vacío / carga / error, paginación y conservación de estado, acceso, lenguaje, formatos, tiempos, accesibilidad y responsive. Quedan fuera el cálculo de señales, el contenido del detalle de la señal y los filtros/orden configurable (HU-075).

## Precondiciones y Datos Base

- **Usuarios:** `analista.piloto1@prueba.co` (Analista); visitante sin sesión.
- **Señales semilla (vigentes salvo indicación):**

  | Señal | Ítem | Contrato u orden | Fecha | Precio unitario | Referencia | Desviación | Emparejamiento | Confianza | Otros |
  | ----- | ---- | ---------------- | ----- | --------------- | ---------- | ---------- | -------------- | --------- | ----- |
  | S1 | Samsung UN65CU7000 65" | SECOP II CO1.PCCNTR.5512001 | 15/09/2026 | $ 3.900.000 Explícito | Compras públicas $ 2.884.000 | +35,2 % | Mismo modelo | Alta | B2 no disponible |
  | S2 | LG 55UR8750 55" | SECOP II CO1.PCCNTR.5512001 | 15/09/2026 | $ 2.950.000 Derivado | Compras públicas $ 1.900.000 | +55,3 % | Producto equivalente | Media | |
  | S3 | Televisor 50 pulgadas smart (sin marca) | TVEC 98765 | 01/08/2026 | $ 2.600.000 Explícito | Compras públicas $ 1.700.000 | +52,9 % | Producto equivalente | Media | IVA indeterminado; proveedor sin dato |
  | S4 | Kalley K-TV32HD 32" | SECOP II CO1.PCCNTR.4410022 | 10/03/2025 | $ 1.300.000 Explícito | Referencia disponible (3 obs.) | +31,0 % | Mismo modelo | Baja | |
  | S5 | Samsung UN50CU7000 50" | SECOP II CO1.PCCNTR.3300046 | 20/09/2026 | $ 2.500.000 Explícito | Compras públicas $ 1.800.000 | +38,9 % | Mismo modelo | Alta | **No vigente** (recalculada) |

- Ítem con precio anormalmente bajo en revisión de calidad: Challenger 43" en CO1.PCCNTR.3300046 (no es señal).
- Universo ampliado de 60 señales vigentes para paginación.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-03 / RN-04 | QA-01, QA-02 |
| Escenario 2 / RN-07 | QA-03 |
| Escenario 3 / RN-09 | QA-04 |
| Escenario 4 | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 / RN-05 | QA-06 |
| Escenario 7 / RN-05 | QA-06 |
| RN-06 datos faltantes | QA-06 |
| Escenario 8 | QA-07 |
| Escenario 9 / RN-10 | QA-08 |
| Escenario 10 | QA-09 |
| Escenario 11 | QA-10 |
| Escenario 12 | QA-11 |
| Escenario 13 | QA-12 |
| RN-08 | QA-13 |
| RN-11 | QA-01 |
| RN-12 | QA-14 |
| RN-13 | QA-15 |

---

## Casos de Prueba

### QA-01: La lista muestra solo señales vigentes con columnas y formatos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-02 / RN-04 / RN-11
- **Pasos:**
  1. Abrir "Señales".
- **Resultado esperado:** 4 filas (S1–S4); S5 (no vigente) y el ítem Challenger (precio bajo) no aparecen; S1 y S2 aparecen como filas separadas del mismo contrato; texto "4 señales que merecen revisión"; S1 muestra "15/09/2026", "$ 3.900.000", "Explícito", "Compras públicas $ 2.884.000", "+35,2 %", "Mismo modelo", "Alta".

### QA-02: Prioridad por defecto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Pasos:**
  1. Abrir "Señales" sin cambiar el orden.
- **Resultado esperado:** orden S1 (Alta), S2 (Media, +55,3 %), S3 (Media, +52,9 %), S4 (Baja).

### QA-03: Advertencia visible en escritorio y móvil

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-07
- **Pasos:**
  1. Abrir "Señales" a 1366 px y a 360 px.
- **Resultado esperado:** en ambos anchos, antes de la primera fila o tarjeta, aparece "Una señal indica que un precio merece revisión. No constituye una conclusión ni una acusación sobre la entidad, el proveedor o las personas relacionadas."

### QA-04: Evidencia de origen en ≤ 3 clics

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-09
- **Pasos:**
  1. En la fila S1 activar "Ver señal" (clic 1).
  2. En el detalle, abrir la evidencia del precio (clic 2).
- **Resultado esperado:** se llega al documento y página de origen del precio en 2 clics (≤ 3).

### QA-05: Abrir la ficha desde el identificador

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Pasos:**
  1. Activar "CO1.PCCNTR.5512001" en la fila S2.
- **Resultado esperado:** se abre la ficha del contrato posicionada en el ítem LG 55UR8750.

### QA-06: Marcas de benchmark, IVA, tipo de precio y datos faltantes

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenarios 5, 6 y 7 / RN-05 / RN-06
- **Pasos:**
  1. Revisar las filas S1, S2, S3 y S4.
- **Resultado esperado:** S1 aparece con referencia de compras públicas aunque su B2 no esté disponible; S2 muestra "Derivado"; S3 muestra "IVA indeterminado — comparación incompleta", Proveedor "Sin dato" y descripción original del ítem; S4 muestra "Referencia disponible (3 obs.)".

### QA-07: Sin señales vigentes

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8
- **Precondiciones:** ninguna señal vigente.
- **Pasos:**
  1. Abrir "Señales" y activar el enlace del mensaje.
- **Resultado esperado:** "Por ahora no hay señales que merezcan revisión. Puedes explorar todas las compras de televisores en Exploración."; no se muestra la advertencia ni la tabla; el enlace lleva a "Exploración".

### QA-08: Paginación y valores inválidos en la URL

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-10
- **Precondiciones:** 60 señales vigentes.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Página | 3 con tamaño 25 | última página |
  | Tamaño | 100 | todas en una página |
  | Tamaño en URL | 7 | no permitido |

- **Pasos:**
  1. Ir a la página 3; cambiar a 100; abrir la URL con tamaño 7.
- **Resultado esperado:** página 3 muestra "Mostrando 51–60 de 60"; tamaño 100 vuelve a la página 1 con "Mostrando 1–60 de 60"; tamaño 7 se reemplaza por 25 sin error.

### QA-09: Volver a la lista conserva página y orden

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Desde la página 2, abrir una señal y volver con "Volver a señales".
  2. Abrir una ficha y volver con el botón atrás del navegador.
- **Resultado esperado:** en ambos casos la lista vuelve a la página 2 con el mismo orden y tamaño.

### QA-10: Error al cargar y reintento

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falla | error del servicio | |
  | Falla | 16 s sin respuesta | supera 15 s |

- **Pasos:**
  1. Abrir "Señales" con cada falla; pulsar "Reintentar" dos veces seguidas.
- **Resultado esperado:** "No fue posible cargar las señales. Intenta de nuevo en unos minutos." y "Reintentar"; cada clic lanza una sola consulta (botón deshabilitado mientras está en curso).

### QA-11: Acceso sin sesión y sesión expirada

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Pasos:**
  1. Como visitante sin sesión abrir la URL de "Señales".
  2. Con sesión expirada pulsar "Siguiente".
- **Resultado esperado:** paso 1 redirige al inicio de sesión sin mostrar señales y, tras iniciar sesión, vuelve a la lista; paso 2 muestra "Tu sesión expiró. Inicia sesión de nuevo para continuar." y redirige.

### QA-12: Estado de carga

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 13
- **Precondiciones:** respuesta demorada 5 s.
- **Pasos:**
  1. Abrir "Señales".
- **Resultado esperado:** indicador de carga, paginación deshabilitada y anuncio "Cargando señales".

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-08
- **Pasos:**
  1. Recorrer la lista, la advertencia y los estados vacío y error buscando "sobreprecio", "corrupción", "fraude" y "hallazgo fiscal".
- **Resultado esperado:** 0 apariciones.

### QA-14: Tiempo de respuesta

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Precondiciones:** 60 señales; 20 sesiones concurrentes.
- **Pasos:**
  1. Cargar y paginar la lista durante 10 minutos.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño).

### QA-15: Accesibilidad y responsive

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Recorrer la lista solo con teclado y verificar contraste.
  2. Abrir a 768 px y a 360 px.
- **Resultado esperado:** "Ver señal" y el enlace del identificador se activan con Enter con foco visible; contraste ≥ 4,5:1; las marcas "Derivado", "Explícito", "IVA indeterminado — comparación incompleta" y la confianza se leen como texto; a 360 px cada señal es una tarjeta con todas las columnas y ambas acciones.

---

**Total de casos:** 15
