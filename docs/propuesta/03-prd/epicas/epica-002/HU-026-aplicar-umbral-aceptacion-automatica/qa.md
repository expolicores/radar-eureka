# Casos de Prueba — HU-026: Aplicar el umbral configurable de aceptación automática y dirigir a revisión los datos dudosos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la configuración del umbral (global, específico, estados, fuente y validaciones), la decisión por ítem (aceptado o pendiente con motivos), el tratamiento de ítems insuficientes, campos no críticos y precio derivado, la disponibilidad para comparación, la reevaluación al cambiar el umbral, el registro y la leyenda. Queda fuera: la revisión humana (HU-028) y el cálculo de la calibración (validación D4-4).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración inicial: umbral global "sin valor", sin específicos.
- Ítem base `CO1.PCCNTR.7654321-01`, información suficiente, sin conflictos, inconsistencias, lote no determinado ni propuesta de reextracción. Confianzas base: marca 0,90, modelo 0,90, tamaño 0,92, cantidad 0,90, precio unitario explícito 0,85, resolución 0,88.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04, RN-06, RN-09 | QA-01 |
| Escenario 2 / RN-01, RN-05, RN-06 | QA-02, QA-03 |
| Escenario 3 / RN-06 | QA-04 |
| Escenario 4 / RN-04 | QA-05, QA-06 |
| Escenario 5 / RN-06 | QA-07 |
| Escenario 6 / RN-06 | QA-08 |
| Escenario 7 / RN-08 | QA-09 |
| Escenario 8 / RN-07 | QA-10 |
| Escenario 9 / RN-02, RN-03, RN-11 | QA-11, QA-12 |
| Escenario 10 / RN-10 | QA-13 |
| Escenario 11 / RN-12 | QA-14 |
| RN-13 / Permisos | QA-15 |

---

## Casos de Prueba

### QA-01: Sin umbral no hay aceptación automática

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04, RN-06, RN-09
- **Pasos:**
  1. Con el umbral "sin valor", evaluar el ítem base con todas las confianzas en 0,95.
- **Resultado esperado:** "pendiente de revisión", motivo "umbral de aceptación no calibrado"; no disponible para comparación.

### QA-02: Aceptación automática con campos críticos nulos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-01, RN-05, RN-06
- **Pasos:**
  1. Configurar global 0,80 "calibrado" con fuente "D4-4, 228 filas, 2026-10-20".
  2. Evaluar un ítem con cantidad 0,90, precio 0,85, tamaño 0,92, marca y modelo nulos.
- **Resultado esperado:** "aceptado automáticamente" y disponible para comparación.

### QA-03: Valores límite de la comparación

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Datos de prueba:**

  | Confianza del precio | Umbral | Resultado |
  | -------------------- | ------ | --------- |
  | 0,80 | 0,80 | aceptado automáticamente |
  | 0,79 | 0,80 | pendiente: "confianza bajo el umbral: precio unitario (0,79 < 0,80)" |
  | 1,00 | 1,00 | aceptado automáticamente |
  | 0,00 | 0,00 | aceptado automáticamente |

- **Pasos:**
  1. Evaluar el ítem base cambiando solo la confianza del precio y el umbral global.
- **Resultado esperado:** el de la tabla.

### QA-04: Dato crítico bajo el umbral

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. Con global 0,80, evaluar el ítem base con precio 0,60 y cantidad 0,70.
- **Resultado esperado:** "pendiente de revisión" con "confianza bajo el umbral: precio unitario (0,60 < 0,80)" y "confianza bajo el umbral: cantidad (0,70 < 0,80)".

### QA-05: Umbral específico más exigente

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-04
- **Pasos:**
  1. Global 0,80; específico de precio 0,90; evaluar el ítem base (precio 0,85).
- **Resultado esperado:** "pendiente de revisión" con "confianza bajo el umbral: precio unitario (0,85 < 0,90)".

### QA-06: Umbral específico con global sin valor

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Global "sin valor"; específico de precio 0,80 "provisional" con fuente "muestra parcial D4-4"; evaluar el ítem base.
- **Resultado esperado:** "pendiente de revisión" con "umbral de aceptación no calibrado" (los demás campos críticos usan el global sin valor).

### QA-07: Precio derivado bajo el umbral

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Pasos:**
  1. Global 0,70; evaluar un ítem con precio derivado de confianza 0,68 y demás campos ≥ 0,90.
- **Resultado esperado:** "pendiente de revisión" con "confianza bajo el umbral: precio unitario derivado (0,68 < 0,70)".

### QA-08: Otros motivos de revisión

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-06
- **Datos de prueba:**

  | Caso | Marca del ítem | Motivo esperado |
  | ---- | -------------- | --------------- |
  | A | con conflicto entre documentos | conflicto entre documentos |
  | B | inconsistencia aritmética abierta | inconsistencia aritmética |
  | C | lote no determinado | lote no determinado |
  | D | propuesta de reextracción | propuesta de reextracción |
  | E | A + B | ambos motivos |

- **Pasos:**
  1. Global 0,50; evaluar el ítem base con cada marca.
- **Resultado esperado:** todos "pendiente de revisión" con el motivo de la tabla.

### QA-09: Campo no crítico con baja confianza

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Global 0,80; evaluar el ítem base con resolución 0,40.
- **Resultado esperado:** "aceptado automáticamente"; resolución marcada "confianza baja".

### QA-10: Ítems con información insuficiente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Datos de prueba:**

  | Caso | Motivos de insuficiencia | Estado esperado |
  | ---- | ------------------------ | --------------- |
  | A | valor global mezcla bienes o servicios (fuente) | no comparable: información insuficiente |
  | B | precio unitario no publicado (fuente) + dato descartado por falta de evidencia válida (procesamiento) | pendiente de revisión: posible pérdida de dato en el procesamiento |

- **Pasos:**
  1. Global 0,80; evaluar cada caso.
- **Resultado esperado:** el de la tabla; ninguno disponible para comparación.

### QA-11: Configuración válida y su registro

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-02, RN-11
- **Pasos:**
  1. Como Administrador, registrar global 0,80, estado "calibrado", fuente "D4-4, 228 filas, 2026-10-20".
  2. Consultar el registro de cambios.
- **Resultado esperado:** configuración guardada; registro con usuario, fecha y hora, anterior "sin valor", nuevo 0,80, estado y fuente.

### QA-12: Validaciones de la configuración

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-02, RN-03
- **Datos de prueba:**

  | Valor | Fuente | Mensaje esperado |
  | ----- | ------ | ---------------- |
  | 0,80 | (vacía) | "Indique la fuente de calibración del umbral" |
  | -0,01 | D4-4 | "El umbral debe ser un número entre 0,00 y 1,00 con máximo 2 decimales" |
  | 1,01 | D4-4 | Mismo mensaje |
  | 0,805 | D4-4 | Mismo mensaje |
  | 0,80 | texto de 301 caracteres | Rechazado por longitud de la fuente (máximo 300) |
  | 0,80 | texto de 300 caracteres | Aceptado |

- **Pasos:**
  1. Guardar cada configuración.
- **Resultado esperado:** los rechazados conservan la configuración anterior y muestran el mensaje; el último se guarda.

### QA-13: Cambio de umbral reevalúa solo ítems sin revisión humana

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Grupo | Cantidad | Estado previo | Confianzas |
  | ----- | -------- | ------------- | ---------- |
  | A | 30 | pendiente (umbral no calibrado) | todas ≥ 0,85 |
  | B | 10 | pendiente (umbral no calibrado) | precio 0,60 |
  | C | 10 | validado por el Administrador | precio 0,50 |

- **Pasos:**
  1. Cambiar el global de "sin valor" a 0,80.
- **Resultado esperado:** A pasa a "aceptado automáticamente"; B queda "pendiente" con "confianza bajo el umbral: precio unitario (0,60 < 0,80)"; C sin cambios.

### QA-14: Leyenda de la confianza

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-12
- **Pasos:**
  1. Consultar la confianza del precio del ítem base como Analista.
- **Resultado esperado:** el valor 0,85 se acompaña de "Nivel de confianza del extractor; no es una probabilidad de acierto".

### QA-15: Funciona sin IA y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-13 / Permisos requeridos
- **Pasos:**
  1. Desactivar la extracción con IA y repetir QA-02.
  2. Como `analista1@piloto.test`, intentar cambiar el umbral global.
- **Resultado esperado:** QA-02 da el mismo resultado sin llamadas al servicio de IA; el Analista recibe acceso denegado y el umbral no cambia.

---

**Total de casos:** 15
