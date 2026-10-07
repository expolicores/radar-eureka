# Casos de Prueba — HU-008: Marcar candidatos a televisor en contratos SECOP II

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la regla de candidatura SECOP II: normalización, coincidencia por palabra completa y plural, UNSPSC, motivos, efecto sobre la clasificación, pérdida de candidatura, disparo automático y manual, cambio de términos y estado vacío.

Queda fuera: la clasificación estricta (HU-010, HU-011).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Términos versión 1: "televisor", "smart tv", "tv".
- Contratos "Pendiente de marcación":

  | id_contrato | unspsc_principal | objeto | descripcion_proceso |
  |---|---|---|---|
  | CO1.PCCNTR.8000001 | V1.52161505 | Adquisición de televisores 65 pulgadas | (nula) |
  | CO1.PCCNTR.8000002 | V1.43211500 | Compra de 52 equipos de cómputo y 1 smart tv | (nula) |
  | CO1.PCCNTR.8000003 | V1.52161505 | Mantenimiento preventivo de equipos audiovisuales | (nula) |
  | CO1.PCCNTR.8000004 | V1.47131700 | Compra en la TVEC de suministros de aseo | (nula) |
  | CO1.PCCNTR.8000005 | V1.83111800 | Servicio de televisión por cable | (nula) |
  | CO1.PCCNTR.8000006 | (nulo) | Dotación | Suministro de TELEVISOR LED para aula |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-05, RN-06 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-05 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 / RN-08 | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-09 | QA-07 |
| Escenario 8 / RN-03 | QA-08 |
| Escenario 9 / RN-03 | QA-09 |
| Escenario 10 | QA-10 |
| RN-01, RN-04 | QA-11 |
| RN-05 (formatos) | QA-12 |
| RN-10 | QA-13 |
| RN-11 | QA-14 |

---

## Casos de Prueba

### QA-01: Candidato por UNSPSC y texto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-05, RN-06
- **Pasos:**
  1. Ejecutar la marcación.
- **Resultado esperado:** CO1.PCCNTR.8000001: "Candidato", "UNSPSC y texto", términos [televisor en objeto], "Pendiente de clasificación", fecha y `version_terminos = 1`.

### QA-02: Candidato solo por texto con dos términos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Ejecutar la marcación.
- **Resultado esperado:** CO1.PCCNTR.8000002: "Candidato", motivo "Texto", términos "smart tv" y "tv" en objeto.

### QA-03: Candidato solo por UNSPSC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-05
- **Pasos:**
  1. Ejecutar la marcación.
- **Resultado esperado:** CO1.PCCNTR.8000003: "Candidato", motivo "UNSPSC", sin términos.

### QA-04: Fragmentos que no son términos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | objeto | Compra en la TVEC de suministros de aseo | "tvec" no es "tv" |
  | objeto | Servicio de televisión por cable | "television" no es término |
  | objeto | Compra de 3 TVs para biblioteca | "tvs" → plural de tv → candidato |
  | objeto | Equipos smartTV | "smarttv" una palabra → no candidato |

- **Pasos:**
  1. Ejecutar la marcación con cada objeto (sin UNSPSC 52161505).
- **Resultado esperado:** los dos primeros y el cuarto "No candidato" con "No cumple UNSPSC ni términos"; el tercero "Candidato" por texto ("tv").

### QA-05: Pérdida de candidatura

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-08
- **Precondiciones:** CO1.PCCNTR.8000001 "Candidato" y clasificado "Incluido" por regla.
- **Pasos:**
  1. Cambiar su objeto a "Adquisición de mobiliario", su UNSPSC a V1.56101700, dejarlo "Pendiente de marcación" y ejecutar.
- **Resultado esperado:** "No candidato"; evento "Dejó de ser candidato" con fecha y candidatura anterior; historial de clasificación intacto; el contrato sigue existiendo.

### QA-06: Texto modificado con clasificación por regla vs. manual

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.8000002 clasificación vigente | Incluido (regla) | |
  | CO1.PCCNTR.8000006 clasificación vigente | Excluido (manual) | |

- **Pasos:**
  1. Cambiar el objeto de ambos manteniendo un término, dejarlos pendientes y ejecutar.
- **Resultado esperado:** 8000002 queda "Pendiente de clasificación"; 8000006 conserva "Excluido (manual)" y `texto_cambio_tras_clasificacion_manual = sí`.

### QA-07: Disparo automático tras carga y ejecución manual

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-09
- **Pasos:**
  1. Terminar una carga incremental "Fallida" que dejó 2 contratos pendientes.
  2. Agregar otro pendiente y ejecutar el comando de marcación.
- **Resultado esperado:** (1) la marcación corre sola sobre los 2. (2) El comando marca el tercero.

### QA-08: Nueva versión de términos y remarcación total

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-03
- **Pasos:**
  1. Guardar términos "televisor", "smart tv", "tv", "television".
  2. Ejecutar "remarcar todos los candidatos SECOP II".
- **Resultado esperado:** versión 2 creada; todos los contratos se remarcan; CO1.PCCNTR.8000005 pasa a "Candidato" por texto con `version_terminos = 2`.

### QA-09: Validación de la lista de términos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Lista | (vacía) | rechazada |
  | Término | "t" | 1 carácter → rechazada |
  | Término | "tv" | 2 caracteres → aceptada |
  | Término | 51 caracteres "a" | rechazada |
  | Término | 50 caracteres "a" | aceptada |
  | Lista | "TV", "tv", "Tv" | se guarda un solo "tv" |

- **Pasos:**
  1. Guardar cada lista.
- **Resultado esperado:** las rechazadas muestran "La lista de términos debe tener al menos un término de 2 a 50 caracteres" y se conserva la versión anterior; las aceptadas crean versión.

### QA-10: Sin pendientes

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10
- **Pasos:**
  1. Con todos los contratos ya marcados, ejecutar la marcación.
- **Resultado esperado:** sin cambios y "No hay contratos SECOP II pendientes de marcación."

### QA-11: Normalización y búsqueda en descripción con objeto sin términos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-01, RN-04
- **Pasos:**
  1. Ejecutar la marcación sobre CO1.PCCNTR.8000006 y sobre una variante con objeto "TELEVISOR-LED 32\"" y descripción nula.
- **Resultado esperado:** 8000006 "Candidato" por texto con "televisor" en `descripcion_proceso`; la variante "Candidato" con "televisor" en objeto.

### QA-12: Formatos de UNSPSC

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | unspsc_principal | V1.52161505 | coincide |
  | unspsc_principal | 52161505 | coincide (sin prefijo) |
  | unspsc_principal | V1.521615 | familia, no coincide |
  | unspsc_principal | V1.52161506 | no coincide |
  | unspsc_principal | (nulo) | no coincide |

- **Pasos:**
  1. Ejecutar con objeto "Dotación de oficina" y cada UNSPSC.
- **Resultado esperado:** solo los dos primeros quedan "Candidato" con motivo "UNSPSC".

### QA-13: Idempotencia

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Ejecutar dos veces la remarcación total sin cambios.
- **Resultado esperado:** mismos resultados; la segunda no genera eventos nuevos.

### QA-14: Resumen de la marcación

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-11
- **Pasos:**
  1. Ejecutar la marcación sobre los 6 contratos base.
- **Resultado esperado:** "Marcación SECOP II: 6 evaluados. Candidatos: 4 (UNSPSC: 1; Texto: 2; Ambos: 1). No candidatos: 2. Dejaron de ser candidatos: 0."

---

**Total de casos:** 14
