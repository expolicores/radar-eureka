# Casos de Prueba — HU-037: Configurar las reglas de equivalencia por categoría

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la configuración inicial, los cambios válidos, las validaciones de dominio, el piso no configurable, la justificación, los permisos, el versionado, la auditoría, la consulta de versiones, la categoría sin reglas y el efecto prospectivo. Queda fuera la lógica de evaluación de pares (HU-038).

## Precondiciones y Datos Base

- Usuarios: `admin.po` (Administrador), `analista.piloto1` (Analista).
- Conjunto `televisor` v1 cargado con la configuración inicial de RN-02.
- Justificación válida de referencia: "Calibración con muestra revisada de octubre" (44 caracteres).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01, RN-02 | QA-01 |
| Escenario 2 / RN-05, RN-06 | QA-02 |
| Escenario 3 / RN-04 (justificación) | QA-03 |
| Escenario 4 / RN-03 | QA-04, QA-05 |
| Escenario 5 / RN-04 | QA-06, QA-07 |
| Escenario 6 / permisos | QA-08 |
| Escenario 7 / RN-05 | QA-09 |
| Escenario 8 / RN-08 | QA-10 |
| Escenario 9 / RN-07 | QA-11 |
| RN-06 (auditoría de rechazos) | QA-12 |

---

## Casos de Prueba

### QA-01: Configuración inicial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-02
- **Pasos:**
  1. Instalar desde cero y consultar las reglas de `televisor`.
- **Resultado esperado:** versión 1 vigente con los 6 criterios de RN-02 exactamente (modo, tolerancia y obligatoriedad), `fecha_fin` nula.

### QA-02: Cambio válido crea versión nueva auditada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05, RN-06
- **Pasos:**
  1. Con `admin.po`, cambiar la tolerancia de generación a 0 con la justificación de referencia.
- **Resultado esperado:** v2 vigente con tolerancia 0; v1 `vigente = no` con `fecha_fin`; auditoría con usuario, fecha y hora, valores anteriores y nuevos, justificación y resultado "aceptado".

### QA-03: Justificación obligatoria (valores límite)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Justificación | vacía | Rechazo |
  | Justificación | `Calibrar.` (9 caracteres) | Mín−1 → rechazo |
  | Justificación | `Calibrado.` (10 caracteres) | Mínimo → aceptado |

- **Resultado esperado:** los dos primeros rechazados con "Configuración inválida: la justificación es obligatoria (mínimo 10 caracteres)"; el tercero crea versión.

### QA-04: Criterios núcleo no se pueden relajar

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | tamaño | obligatoriedad `SI_AMBOS_CONOCIDOS` | Relaja núcleo |
  | resolución | `NO_EVALUADO` | Relaja núcleo |
  | tamaño | eliminado | Relaja núcleo |
  | tecnología, Smart | ambos a `SI_AMBOS_CONOCIDOS` | Quedan 2 obligatorios (< 3) |

- **Resultado esperado:** todos rechazados con "Configuración inválida: {criterio} es un criterio núcleo y no puede relajarse por debajo del piso" (o el detalle de mínimo 3 obligatorios); sin versión nueva.

### QA-05: Tolerancia de tamaño en el límite del piso

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | tamaño | `TOLERANCIA` 1 | Máximo → aceptado |
  | tamaño | `TOLERANCIA` 1,5 | Supera piso → rechazo |
  | tamaño | `TOLERANCIA` 2 | Rechazo |

- **Resultado esperado:** solo la tolerancia 1 crea versión.

### QA-06: Validaciones de dominio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | generación | tolerancia −1 | Negativa |
  | resolución | `EXACTO` con tolerancia 1 | Tolerancia en exacto |
  | tecnología | `TOLERANCIA` 1 | No numérico |
  | `color` | `EXACTO` | Atributo inexistente |
  | marca | modo `APROXIMADO` | Modo no reconocido |
  | marca | criterio repetido dos veces | Repetido |
  | generación | `TOLERANCIA` sin valor | Nula |

- **Resultado esperado:** todos rechazados con "Configuración inválida: {detalle}"; sin versión nueva.

### QA-07: Tolerancia de generación en el límite

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | generación | tolerancia 3 | Máximo → aceptado |
  | generación | tolerancia 4 | Máx+1 → rechazo |

- **Resultado esperado:** según la nota.

### QA-08: Analista sin permiso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 6
- **Pasos:**
  1. Con `analista.piloto1`, intentar cambiar la tolerancia de generación con justificación válida.
- **Resultado esperado:** rechazo por falta de permiso; sin versión nueva.

### QA-09: Consulta del historial

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-05
- **Precondiciones:** existen v1, v2 y v3.
- **Resultado esperado:** la consulta devuelve v3 como vigente y el historial con versión, criterios, fechas de inicio y fin, usuario y justificación de las tres; ninguna versión anterior aparece modificada.

### QA-10: Categoría sin reglas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-08
- **Precondiciones:** producto de prueba de categoría `computador` sin conjunto de reglas.
- **Resultado esperado:** la consulta de reglas indica que no hay reglas vigentes; el emparejamiento de equivalentes no genera pares para ese producto y registra `SIN_REGLAS_EQUIVALENCIA`.

### QA-11: Efecto prospectivo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-07
- **Precondiciones:** existe un par equivalente vigente calculado con v1.
- **Pasos:**
  1. Crear v2.
  2. Consultar el par antes del siguiente emparejamiento.
  3. Ejecutar el emparejamiento.
- **Resultado esperado:** paso 2: el par sigue igual con `version_reglas = 1`. Paso 3: el par v1 queda `vigente = no`; los pares vigentes tienen `version_reglas = 2`.

### QA-12: Los intentos rechazados quedan auditados

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Repetir uno de los cambios rechazados de QA-04.
- **Resultado esperado:** la auditoría contiene el intento con usuario, fecha y hora, valores propuestos, justificación y resultado "rechazado" con su motivo.

---

**Total de casos:** 12
