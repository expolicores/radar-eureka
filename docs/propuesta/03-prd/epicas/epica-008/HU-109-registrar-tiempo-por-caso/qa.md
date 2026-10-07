# Casos de Prueba — HU-109: Registrar el tiempo que el Analista dedica a cada señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la captura de eventos, la atribución entre señales, el cálculo de tiempo bruto y activo con el umbral de inactividad, los estados de la medición, la no interferencia con el Analista, la consulta, la exportación y los permisos. Queda fuera: el cálculo del KPI de eficiencia (HU-110) y la calificación de señales (otra épica).

## Precondiciones y Datos Base

- Fecha de las pruebas: **2026-10-02 (UTC−05:00)**.
- Usuarios: `analista1@prueba.co`, `analista2@prueba.co`, `analista3@prueba.co` (Analista); `admin.po@prueba.co` (Administrador).
- Señales SEN-0101 a SEN-0106 disponibles para calificar.
- Umbral de inactividad: 30 minutos.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-05, RN-07 | QA-01 |
| Escenario 2, RN-05 | QA-02 |
| Escenario 3, RN-05, RN-06 (límite del umbral) | QA-03 |
| RN-06 (cambio de umbral no retroactivo y rango) | QA-04 |
| Escenario 4, RN-03 | QA-05 |
| Escenario 5, RN-08 | QA-06 |
| Escenario 6, RN-04 | QA-07 |
| Escenario 7, RN-08 | QA-08 |
| Escenario 8, RN-10 | QA-09 |
| Escenario 9, RN-09 | QA-10 |
| Escenario 10, RN-11 | QA-11 |
| Escenario 11, RN-13 | QA-12 |
| Escenario 12, RN-12 | QA-13 |

---

## Casos de Prueba

### QA-01: Medición completa sin pausas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-05, RN-07
- **Pasos:**
  1. Como `analista1@prueba.co`, abrir SEN-0101 a las 09:00:00; ir al contrato 09:02:00; al documento 09:05:30; a una observación 09:09:00; calificar "sustentada" 09:12:40.
  2. Como Administrador, consultar la medición.
- **Resultado esperado:** estado "completa"; bruto 12:40 (760 s); activo 12:40; 1 apertura; 0 pausas; calificación "sustentada"; umbral 30.

### QA-02: Pausa larga excluida

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-05
- **Pasos:**
  1. Abrir SEN-0102 10:00; documento 10:04; reabrir 10:50; calificar 10:56.
- **Resultado esperado:** bruto 56:00; activo 10:00; 2 aperturas; 1 pausa excluida.

### QA-03: Límite del umbral de inactividad

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-05, RN-06
- **Datos de prueba:**

  | Intervalo entre eventos | Resultado | Nota |
  | ----- | ----- | ----- |
  | 30:00 | se cuenta completo | igual al umbral |
  | 30:01 | se excluye completo | mayor que el umbral |

- **Pasos:**
  1. Para cada caso: abrir una señal, generar un segundo evento tras el intervalo y calificar 1 minuto después.
- **Resultado esperado:** activo 31:00 en el primer caso; 1:00 y 1 pausa excluida en el segundo.

### QA-04: Cambio de umbral sin recalcular y rango permitido

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Umbral | 5 / 120 | aceptados |
  | Umbral | 4 / 121 | rechazados; el vigente no cambia |

- **Pasos:**
  1. Con la medición de QA-02 guardada (umbral 30), cambiar el umbral a 120.
  2. Intentar 4 y 121.
- **Resultado esperado:** la medición de QA-02 conserva activo 10:00 y umbral 30; las nuevas mediciones usan 120; 4 y 121 se rechazan con "El umbral de inactividad debe ser un número entero entre 5 y 120 minutos."

### QA-05: Señales intercaladas

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03
- **Pasos:**
  1. Abrir SEN-0103 11:00; abrir SEN-0104 11:05; reabrir SEN-0103 11:15; calificar SEN-0103 11:20; reabrir SEN-0104 11:22; calificar SEN-0104 11:30.
- **Resultado esperado:** SEN-0103 activo 10:00 (bruto 20:00); SEN-0104 activo 18:00 (bruto 25:00).

### QA-06: Señal sin calificar

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-08
- **Pasos:**
  1. Abrir SEN-0105 sin calificar; consultar mediciones.
- **Resultado esperado:** estado "sin calificar", sin tiempos; no se incluye entre las "completa".

### QA-07: Recalificación no altera la medición

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-04
- **Pasos:**
  1. Tras QA-01, recalificar SEN-0101 como "no sustentada" el 2026-10-03.
- **Resultado esperado:** la medición conserva fin 09:12:40, tiempos 12:40 y la calificación registrada en la medición sigue siendo la primera ("sustentada").

### QA-08: Calificación sin apertura

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-08
- **Pasos:**
  1. Registrar una calificación de SEN-0106 sin apertura previa de esa Analista.
- **Resultado esperado:** estado "incompleta", motivo "No hay apertura registrada para la señal."

### QA-09: Falla del registro de eventos no afecta al Analista

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-10
- **Precondiciones:** registro de eventos no disponible (simulado) durante la calificación.
- **Pasos:**
  1. Abrir y calificar SEN-0104 como `analista2@prueba.co`.
- **Resultado esperado:** la calificación se guarda sin mensaje de error para la Analista y sin demora perceptible; la medición queda "incompleta" con "Eventos de medición perdidos."

### QA-10: El Administrador no es medido

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-09
- **Pasos:**
  1. Como `admin.po@prueba.co`, abrir y calificar SEN-0103.
- **Resultado esperado:** no existe medición para el Administrador.

### QA-11: Consulta filtrada y exportación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Analista | analista1@prueba.co | — |
  | Rango | 2026-10-02 a 2026-10-02 | extremos incluidos |
  | Estado | completa | — |

- **Pasos:**
  1. Consultar con los filtros; exportar CSV sin filtros.
- **Resultado esperado:** solo mediciones completas de analista1 calificadas el 2026-10-02, en orden de calificación descendente; CSV UTF-8 con todos los campos de RN-07 para las 3 Analistas.

### QA-12: Sin mediciones y rangos inválidos

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11, RN-13
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Rango | 2026-01-01 a 2026-01-31 | "No hay mediciones de tiempo en el período consultado." |
  | Rango | 2025-09-01 a 2026-10-02 | "El rango de consulta no puede superar 365 días." |
  | Rango | 2026-10-02 a 2026-09-01 | "La fecha inicial no puede ser posterior a la fecha final." |

- **Pasos:**
  1. Consultar con cada rango.
- **Resultado esperado:** el mensaje indicado.

### QA-13: Ningún Analista consulta mediciones

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12, RN-12
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar mediciones propias y exportar.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador."; las pantallas de la Analista no muestran tiempos.

---

**Total de casos:** 13
