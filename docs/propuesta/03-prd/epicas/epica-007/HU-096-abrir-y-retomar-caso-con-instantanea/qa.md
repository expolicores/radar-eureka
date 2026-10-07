# Casos de Prueba — HU-096: Abrir y retomar un caso con su evidencia conservada como instantánea

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el detalle del caso: encabezado, elementos y resúmenes por tipo, contenido completo de instantáneas, inmutabilidad frente a recálculos, enlace a la versión vigente, elementos no vigentes, apertura de la evidencia documental conservada y su indisponibilidad, retomar el trabajo, caso inexistente o ajeno, errores, estados vacíos, lenguaje y rendimiento. Quedan fuera la gestión de notas (HU-093, HU-094) y guardar elementos (HU-092).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org` |
| Caso A | "Compra TV 65 Gobernación", sin descripción, creado 25/09/2026 10:00; elementos: señal S-1 (instantánea 25/09/2026 10:00, +42 %, "Medio"), señal S-4 (instantánea 26/09/2026 08:00), contrato C-1 (instantánea 28/09/2026 12:00), evidencia E-doc `oferta_economica.pdf` pág. 3 (instantánea 29/09/2026 16:00); 3 notas |
| Caso V | "Caso sin notas", de Ana, 1 elemento, 0 notas |
| Caso L | "Caso de Luis", de `luis.mora@ejemplo.org` |
| Estado actual | S-1 recalculada a +35 % "Alto"; S-4 ya no existe; C-1 existe |
| Hoja de cálculo | evidencia E-xls `anexo_economico.xlsx`, hoja "Precios", celda F12, guardada en V |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-03 | QA-01 |
| Escenario 2 / RN-08 | QA-02 |
| Escenario 3 / RN-04 / RN-05 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-06 | QA-05, QA-06 |
| Escenario 6 / RN-07 | QA-07, QA-08 |
| Escenario 7 | QA-09 |
| Escenario 8 | QA-10 |
| Escenario 9 / RN-10 | QA-11 |
| Escenario 10 | QA-12 |
| Escenario 11 | QA-13 |
| RN-09 | QA-14 |
| RN-11 | QA-15 |

---

## Casos de Prueba

### QA-01: Abrir un caso propio

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02, RN-03
- **Pasos:**
  1. Abrir A desde "Mis casos"; luego abrirlo por su dirección directa.
- **Resultado esperado:** "Sin descripción", "Creado el 25/09/2026 10:00", fecha de actualización; 4 elementos en orden E-doc, C-1, S-4, S-1 con conteos Señales 2, Contratos 1, Evidencias 1; cada uno con "Instantánea del …" y el resumen de RN-03; 3 notas.

### QA-02: Contenido completo de la instantánea de señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-08
- **Pasos:**
  1. En S-1, pulsar "Ver detalle".
- **Resultado esperado:** se muestran ítem, contrato, benchmarks con estado, cada observación con origen, fecha, método e indicador manual, fórmula, desviación, emparejamiento, confianza, base tributaria, evidencia de origen, fecha de corte y la advertencia "Esta señal no constituye una conclusión ni una acusación; indica un caso que merece revisión."

### QA-03: Instantánea frente a recálculo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-04, RN-05
- **Pasos:**
  1. Abrir A.
- **Resultado esperado:** S-1 muestra +42 % y "Medio"; ofrece "Ver versión actual" con "La información vigente puede diferir de esta instantánea."

### QA-04: Ver versión actual

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Pasos:**
  1. Pulsar "Ver versión actual" en S-1; volver al caso.
  2. Pulsar "Ver versión actual" en C-1.
- **Resultado esperado:** (1) se abre el detalle vigente de S-1 con +35 % y "Alto"; al volver, la instantánea sigue en +42 %; (2) se abre la ficha vigente de C-1.

### QA-05: Señal no vigente

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-06
- **Pasos:**
  1. Revisar el elemento S-4 en A.
- **Resultado esperado:** instantánea completa visible; no hay "Ver versión actual"; texto "Esta señal ya no está vigente en el sistema; se conserva la instantánea guardada."

### QA-06: Contrato no disponible y observación sin versión vigente

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-05, RN-06
- **Precondiciones:** C-1 retirado del sistema en el entorno de prueba; V con una evidencia de observación.
- **Pasos:**
  1. Abrir A y revisar C-1.
  2. Abrir V y revisar la evidencia de observación.
- **Resultado esperado:** C-1 muestra "Este contrato ya no está disponible en el sistema; se conserva la instantánea guardada."; la observación no ofrece "Ver versión actual".

### QA-07: Abrir documento PDF conservado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-07
- **Pasos:**
  1. En E-doc, pulsar "Ver documento"; contar clics desde el detalle del caso.
- **Resultado esperado:** se abre la copia conservada con el hash registrado en la página 3, en ≤ 2 clics; hay enlace "Ver en la fuente oficial" con la URL original.

### QA-08: Abrir evidencia de hoja de cálculo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. En V, pulsar "Ver documento" en E-xls.
- **Resultado esperado:** se abre la copia en la hoja "Precios" posicionada en F12; si no es posible posicionar, se muestra "Ubicación: hoja Precios, celda F12".

### QA-09: Copia del documento no disponible

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Precondiciones:** almacenamiento de evidencia simulado como no disponible.
- **Pasos:**
  1. Pulsar "Ver documento" en E-doc.
- **Resultado esperado:** "La copia del documento no está disponible en este momento. Puedes consultar la fuente oficial." con enlace a la URL original; error en log.

### QA-10: Retomar el caso tras cerrar sesión

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8
- **Pasos:**
  1. Abrir A, agregar una nota, cerrar sesión.
  2. Iniciar sesión, guardar C-2 en A desde la exploración y abrir A.
- **Resultado esperado:** A muestra la nota y el nuevo contrato; los elementos previos están intactos; la fecha de actualización refleja el último cambio.

### QA-11: Caso inexistente o ajeno

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-10
- **Datos de prueba:**

  | Usuario | Caso solicitado |
  | ------- | --------------- |
  | Ana | L (de Luis) |
  | Administrador | A (de Ana) |
  | Ana | identificador inexistente |

- **Pasos:**
  1. Abrir cada caso por dirección directa.
- **Resultado esperado:** en todos, "No encontramos este caso." con enlace a "Mis casos" y sin ningún dato; la respuesta es idéntica para ajeno e inexistente.

### QA-12: Error al cargar el caso

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Precondiciones:** error simulado en la consulta.
- **Pasos:**
  1. Abrir A; quitar el error y pulsar "Reintentar".
- **Resultado esperado:** "No pudimos cargar el caso. Intenta de nuevo." con "Reintentar"; tras reintentar, el caso se muestra.

### QA-13: Caso sin notas

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11
- **Pasos:**
  1. Abrir V.
- **Resultado esperado:** "Aún no hay notas en este caso."

### QA-14: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Revisar los textos generados por el sistema en el detalle de A contra la lista de términos prohibidos.
- **Resultado esperado:** ninguno contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### QA-15: Rendimiento con el máximo de elementos

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Precondiciones:** caso con 100 elementos y 200 notas.
- **Pasos:**
  1. Medir 100 aperturas del caso con 20 usuarios concurrentes.
- **Resultado esperado:** p95 ≤ 3 segundos.

---

**Total de casos:** 15
