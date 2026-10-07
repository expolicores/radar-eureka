# Casos de Prueba — HU-013: Revisión y corrección manual de la clasificación de candidatos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la cola de revisión de clasificación, la corrección y confirmación manual con sus validaciones, los efectos sobre el contrato y el indicador `en_analisis`, la precedencia manual, la devolución a clasificación automática, la muestra de verificación con su cálculo de acierto y los permisos.

Queda fuera: las reglas (HU-010, HU-011) y la IA (HU-012), salvo como precondiciones.

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`; Analista: `analista1@piloto.test`.
- Candidatos:

  | Id | Tipo | Texto | Vigente | Método | Sugerencia IA |
  |---|---|---|---|---|---|
  | IT-01 | Ítem TVEC | Monitor TV 43 pulgadas para CCTV | Requiere revisión (R6) desde 2026-09-28 | Regla | Excluido / monitor o CCTV / 0,95 |
  | IT-02 | Ítem SECOP II (contrato CT-09) | KIT TELEVISOR 43 + BARRA DE SONIDO | Requiere revisión (R8b) desde 2026-09-29 | Regla | — |
  | CT-01 | Contrato SECOP II | Dotación de equipos para auditorio | Requiere revisión (C7) desde 2026-09-30 | Regla | — |
  | IT-05 | Ítem TVEC | Televisor 55 pulgadas | Incluido (R10) | Regla | — |
  | IT-06 | Ítem SECOP II (contrato CT-09) | Smart TV 50 pulgadas | Incluido (R10) | Regla | — |
  | NC-01 | Ítem TVEC | ACTIVIDADES TVEC CAPACITACION | No candidato | — | — |

- Contrato CT-09: "Compra de equipos y televisores", clasificación derivada "Incluido" (C8), ítems IT-02 e IT-06.
- Población para muestras: 120 candidatos con vigente automática Incluido/Excluido (semilla de datos de prueba).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-06, RN-10 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-11 | QA-05 |
| Escenario 6 / RN-01, RN-03, RN-04, RN-05 | QA-06, QA-07 |
| Escenario 7 / RN-09 | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| Escenario 9 / RN-08 | QA-10 |
| Escenario 10 / RN-12 | QA-11 |
| Escenario 11 / RN-12 | QA-12 |
| Escenario 12 / RN-13 | QA-13 |
| Escenario 13 / RN-14 | QA-14 |

---

## Casos de Prueba

### QA-01: Cola de revisión ordenada con sugerencia de IA

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02
- **Pasos:**
  1. Consultar la cola.
  2. Consultar la cola filtrando tipo "Contrato SECOP II".
- **Resultado esperado:** (1) IT-01, IT-02, CT-01 en ese orden, con tipo, texto, criterio, fecha de entrada y, en IT-01, "Excluido / Producto excluido: monitor o CCTV / {justificación} / 0,95". (2) Solo CT-01.

### QA-02: Cola vacía

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 2
- **Pasos:**
  1. Resolver los 3 candidatos y consultar la cola.
- **Resultado esperado:** "No hay candidatos pendientes de revisión de clasificación."

### QA-03: Corrección de un candidato en revisión

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06, RN-10
- **Pasos:**
  1. Clasificar IT-01 como "Excluido", motivo "Producto excluido: monitor o CCTV", comentario "La ficha técnica del ítem indica monitor de vigilancia".
- **Resultado esperado:** vigente "Excluido" método "Manual"; evento con resultado anterior "Requiere revisión", criterio "R6", método anterior "Regla", nuevo "Excluido", motivo, comentario, `admin.po@piloto.test` y fecha y hora; estado "Clasificado"; mensaje "Clasificación actualizada: IT-01 pasó de Requiere revisión a Excluido."

### QA-04: Corrección de un incluido automático

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:**
  1. Clasificar IT-05 como "Excluido", motivo "Accesorio", comentario "Es un soporte, descripción incompleta en la fuente".
- **Resultado esperado:** vigente "Excluido (Manual)"; `en_analisis = no`.

### QA-05: Efectos sobre el contrato y el análisis

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-11
- **Pasos:**
  1. Clasificar IT-06 como "Excluido" (motivo "Producto excluido: monitor o CCTV", comentario válido).
  2. Clasificar IT-02 como "Excluido" (motivo "Kit sin precio unitario determinable").
  3. Clasificar CT-09 manualmente como "Incluido" (motivo "Contrato con al menos un televisor") y luego IT-06 como "Incluido".
- **Resultado esperado:** (1) CT-09 pasa a "Requiere revisión" (C10) porque IT-02 sigue en revisión y no hay incluidos. (2) CT-09 pasa a "Excluido" (C9), `apto_gestion_documental = no`. (3) CT-09 queda "Incluido (Manual)" y no se rederiva; IT-06 `en_analisis = sí`.

### QA-06: Validaciones de la corrección

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-01, RN-03, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Candidato | IT-999 | "No existe el candidato IT-999." |
  | Candidato | NC-01 | "Solo se puede clasificar un candidato; NC-01 está marcado como No candidato." |
  | Resultado | Dudoso | "El resultado debe ser Incluido, Excluido o Requiere revisión." |
  | Motivo | Electrodoméstico | "El motivo no pertenece a la lista de motivos permitidos." |
  | IT-01 → Excluido, motivo "Producto excluido: monitor o CCTV" | después de QA-03 (vigente manual igual) | "La clasificación indicada es igual a la vigente; no se registró ningún cambio." |

- **Pasos:**
  1. Enviar cada corrección con comentario válido.
- **Resultado esperado:** ningún evento registrado y el mensaje indicado.

### QA-07: Longitud del comentario

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comentario | 9 caracteres "Es monitr" | rechazo |
  | Comentario | 10 caracteres "Es monitor" | aceptado |
  | Comentario | "   Es monitor   " | 10 sin extremos → aceptado |
  | Comentario | 500 caracteres | aceptado |
  | Comentario | 501 caracteres | rechazo |
  | Comentario | (vacío) | rechazo |

- **Pasos:**
  1. Corregir IT-02 a "Excluido" con cada comentario (restaurando el estado entre intentos aceptados).
- **Resultado esperado:** los rechazos muestran "El comentario es obligatorio y debe tener entre 10 y 500 caracteres."

### QA-08: Confirmación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-09
- **Pasos:**
  1. Confirmar IT-06 (Incluido R10) sin comentario.
  2. Intentar confirmar CT-01 (Requiere revisión).
- **Resultado esperado:** (1) evento "Confirmación" con usuario y fecha; vigente y método siguen "Incluido / Regla". (2) "Un candidato en Requiere revisión no se puede confirmar; clasifíquelo como Incluido o Excluido."

### QA-09: Precedencia manual

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Tras QA-03, ejecutar la reclasificación total por reglas y la clasificación asistida por IA.
  2. Corregir de nuevo IT-01 a "Requiere revisión" con comentario válido.
- **Resultado esperado:** (1) IT-01 sigue "Excluido (Manual)". (2) La nueva corrección manual se registra y queda vigente, estado "En revisión".

### QA-10: Devolver a clasificación automática

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-08
- **Pasos:**
  1. Ejecutar "devolver a clasificación automática" sobre IT-05 (Excluido manual de QA-04) con comentario "Se verificó que sí es un televisor".
  2. Repetir con comentario vacío.
- **Resultado esperado:** (1) evento "Devolución a automática"; IT-05 pasa a "Pendiente de clasificación" y queda "Incluido (R10, Regla)"; historial completo conservado. (2) Rechazo por comentario.

### QA-11: Generar una muestra de 50

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-12
- **Pasos:**
  1. Generar una muestra de tamaño 50.
  2. Generar otra con la misma semilla registrada.
- **Resultado esperado:** (1) muestra con identificador, fecha, semilla, tamaño 50 y 50 candidatos distintos, todos con vigente automática Incluido/Excluido (ninguno manual), en "Pendiente de verificación". (2) Mismos 50 candidatos.

### QA-12: Tamaño de muestra inválido o población insuficiente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tamaño | 9 | rechazo |
  | Tamaño | 10 | aceptado |
  | Tamaño | 120 | igual a la población → aceptado |
  | Tamaño | 121 | mayor que la población → rechazo |
  | Tamaño | 501 (con población de 600) | rechazo |

- **Pasos:**
  1. Generar una muestra con cada tamaño.
- **Resultado esperado:** los rechazos muestran "La población elegible tiene {n} candidatos; el tamaño de la muestra debe estar entre 10 y {mínimo entre 500 y n}."

### QA-13: Cálculo del acierto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-13
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Confirmados / corregidos | 48 / 2 | 96,0 % |
  | Confirmados / corregidos | 47 / 3 | 94,0 % (bajo la meta) |
  | Confirmados / corregidos | 20 / 0 (30 sin revisar) | 100,0 %, revisados 20 de 50 |

- **Pasos:**
  1. Resolver la muestra con cada combinación y consultar el resultado.
- **Resultado esperado:** ej. "Muestra {id}: revisados 50 de 50. Confirmados: 48. Corregidos: 2. Acierto: 96,0 % (meta de la épica: ≥ 95 %)." y la lista de corregidos con valor anterior y nuevo.

### QA-14: El Analista no puede actuar

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-14
- **Pasos:**
  1. Con `analista1@piloto.test`, intentar consultar la cola, corregir IT-02, confirmar IT-06, devolver IT-05 y generar una muestra.
- **Resultado esperado:** todas las acciones denegadas; ningún evento nuevo.

---

**Total de casos:** 14
