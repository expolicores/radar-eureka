# Casos de Prueba — HU-009: Marcar candidatos a televisor en ítems de la TVEC

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la candidatura de ítems TVEC: normalización del texto TVEC, coincidencia por palabra completa y plural, descripción vacía, efecto sobre la clasificación, pérdida de candidatura, disparos automático y manual, idempotencia, resumen y estado vacío.

Queda fuera: la clasificación (HU-010) y la validación de la lista de términos (HU-008).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Términos versión 1: "televisor", "smart tv", "tv".
- Ítems "Pendiente de marcación":

  | id_origen_item | descripcion_item |
  |---|---|
  | row-t001 | GSF01-SMART TV LG 43LR6500PSA |
  | row-t002 | TELEVISORES SAMSUNG 55 PULGADAS |
  | row-t003 | ACTIVIDADES TVEC CAPACITACION |
  | row-t004 | SOPORTE PARA TELEVISION |
  | row-t005 | MONITOR 43TV INDUSTRIAL |
  | row-t006 | Televisor Kalley 32" |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01, RN-05 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-06 | QA-04, QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 | QA-07 |
| RN-04 | QA-08 |
| RN-07, RN-08 | QA-09 |

---

## Casos de Prueba

### QA-01: Ítem candidato con texto TVEC no normalizado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-05
- **Pasos:**
  1. Ejecutar la marcación TVEC.
- **Resultado esperado:** row-t001 "Candidato", motivo "Texto", términos [smart tv, tv], "Pendiente de clasificación", con fecha y `version_terminos = 1`. row-t006 "Candidato" con [televisor].

### QA-02: Plural

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-02
- **Pasos:**
  1. Ejecutar la marcación.
- **Resultado esperado:** row-t002 "Candidato" con [televisor].

### QA-03: Fragmentos que no son términos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Pasos:**
  1. Ejecutar la marcación.
- **Resultado esperado:** row-t003, row-t004 y row-t005 "No candidato" con "No contiene términos de televisor".

### QA-04: Descripción modificada que sigue siendo candidata

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | row-t001 clasificación vigente | Incluido (regla) | |
  | row-t006 clasificación vigente | Incluido (manual) | |

- **Pasos:**
  1. Cambiar ambas descripciones manteniendo "tv", dejarlas pendientes y ejecutar.
- **Resultado esperado:** row-t001 "Pendiente de clasificación"; row-t006 conserva "Incluido (manual)" y `texto_cambio_tras_clasificacion_manual = sí`.

### QA-05: Ítem que deja de ser candidato

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-06
- **Pasos:**
  1. Cambiar row-t002 a "NEVERA SAMSUNG 300 L", dejarlo pendiente y ejecutar.
- **Resultado esperado:** "No candidato"; evento "Dejó de ser candidato"; historial de clasificación conservado; el ítem sigue existiendo.

### QA-06: Disparo automático, manual y remarcación total

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-03
- **Pasos:**
  1. Terminar una carga de ítems TVEC con 2 ítems pendientes.
  2. Guardar términos versión 2 con "television" y ejecutar "remarcar todos los candidatos TVEC".
- **Resultado esperado:** (1) la marcación corre sola sobre los 2. (2) Todos los ítems se remarcan con versión 2; row-t004 pasa a "Candidato".

### QA-07: Sin pendientes

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 6
- **Pasos:**
  1. Ejecutar sin ítems pendientes.
- **Resultado esperado:** "No hay ítems TVEC pendientes de marcación."

### QA-08: Descripción vacía

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | "" | |
  | descripcion_item | "---" | queda vacía tras normalizar |

- **Pasos:**
  1. Ejecutar la marcación con cada valor.
- **Resultado esperado:** "No candidato" con "Descripción vacía".

### QA-09: Idempotencia y resumen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-07, RN-08
- **Pasos:**
  1. Ejecutar la marcación sobre los 6 ítems base.
  2. Ejecutar la remarcación total sin cambios.
- **Resultado esperado:** (1) "Marcación TVEC: 6 evaluados. Candidatos: 3. No candidatos: 3. Dejaron de ser candidatos: 0." (2) Mismos resultados, sin eventos nuevos.

---

**Total de casos:** 9
