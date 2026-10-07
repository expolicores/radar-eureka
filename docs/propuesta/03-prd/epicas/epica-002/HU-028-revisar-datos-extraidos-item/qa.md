# Casos de Prueba — HU-028: Validar, corregir o rechazar los datos extraídos de un ítem conservando el historial

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban las operaciones de revisión (consultar, validar, corregir, rechazar, reabrir, resolver propuesta de reextracción), las transiciones de estado válidas e inválidas, las validaciones de cada campo, la reevaluación posterior, el historial inmutable, la auditoría, la concurrencia y los permisos. Se ejecutan como operaciones sin interfaz gráfica o desde una vista mínima, indistintamente. Queda fuera: la cola priorizada de revisión (épica de operación) y el reporte de errores del Analista (épica de señales).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Ítem base `CO1.PCCNTR.7654321-01`, "pendiente de revisión" (motivos "umbral de aceptación no calibrado" e "inconsistencia aritmética", porque 10 × 2.150.000 ≠ 17.200.000), versión 3: cantidad 10 (oferta, página 2), precio unitario explícito 2.150.000,00 `con_iva`, valor total 17.200.000,00 `con_iva`, tamaño 55 pulgadas, marca nula.
- Documentos del proceso: "Contrato 045-2025.pdf" (4 páginas), "Propuesta_economica_ganador.pdf" (3 páginas). Documento de otro proceso: "Oferta_otro_proceso.pdf".

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02, RN-03, RN-13 | QA-01 |
| RN-03 (ítem insuficiente) | QA-02 |
| Escenario 2 / RN-04, RN-07, RN-11 | QA-03 |
| Escenario 3 / RN-04 | QA-04 |
| RN-04 (sin evidencia nueva), RN-06 | QA-05, QA-06 |
| Escenario 4 / RN-07 | QA-07 |
| Escenario 5 / RN-03 | QA-08 |
| Escenario 6 / RN-08 | QA-09 |
| Escenario 7 / RN-08 | QA-10 |
| Escenario 8 / RN-02, RN-09 | QA-11, QA-12 |
| Escenario 9 / RN-05 | QA-13, QA-14 |
| Escenario 10 / RN-10 | QA-15 |
| Escenario 11 / RN-01 | QA-16 |
| RN-11 (inmutabilidad), RN-12 | QA-17 |
| Escenario 12 / Permisos | QA-18 |
| RN-01 (consulta) | QA-19 |

---

## Casos de Prueba

### QA-01: Validar un ítem pendiente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-03, RN-13
- **Pasos:**
  1. Como Administrador, validar el ítem `CO1.PCCNTR.7654321-02` ("pendiente de revisión" por "umbral de aceptación no calibrado"; cantidad 4, precio 1.800.000,00, total 7.200.000,00, misma base; sin inconsistencias).
- **Resultado esperado:** "validado"; disponible para comparación; historial con "validar", usuario, fecha y hora, estado anterior "pendiente de revisión".

### QA-02: Validar un ítem sin información suficiente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Pasos:**
  1. Validar un ítem "no comparable: información insuficiente" con precio nulo.
- **Resultado esperado:** rechazo con "El ítem no tiene cantidad y precio unitario suficientes; corríjalo o rechácelo"; sin cambios.

### QA-03: Corregir la cantidad con evidencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04, RN-07, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Cantidad nueva | 8 | |
  | Evidencia | Contrato 045-2025.pdf, versión 1, página 1 | |
  | Comentario | La oferta decía 10, el contrato fija 8 | |

- **Pasos:**
  1. Corregir el ítem base.
- **Resultado esperado:** valor vigente 8 con la nueva evidencia; historial con original 10 (oferta, página 2), nuevo 8, origen "corrección manual", usuario, fecha y comentario; se repiten base, derivado, suficiencia y aritmética; la aritmética queda consistente (8 × 2.150.000 = 17.200.000) y el ítem "validado con correcciones".

### QA-04: Corregir un campo nulo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-04
- **Pasos:**
  1. Corregir la marca a "Samsung" con evidencia "Propuesta_economica_ganador.pdf, versión 1, página 2".
- **Resultado esperado:** historial con original nulo y nuevo "Samsung".

### QA-05: Corrección sin evidencia y eliminación de un dato

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Caso | Campo | Nuevo valor | Evidencia |
  | ---- | ----- | ----------- | --------- |
  | A | Tamaño | 50 | ninguna |
  | B | Modelo | nulo | ninguna |

- **Pasos:**
  1. Corregir cada caso.
- **Resultado esperado:** A: tamaño 50 con la evidencia original y la anotación "corrección manual". B: modelo vigente nulo; el original queda en el historial.

### QA-06: La base corregida manualmente prevalece

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Corregir la base del precio unitario a `sin_iva`.
  2. Corregir después la cantidad (dispara reevaluación).
- **Resultado esperado:** la base del precio sigue `sin_iva` tras la reevaluación; la base del total se recalcula automáticamente.

### QA-07: Corrección que deja el ítem pendiente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-07
- **Pasos:**
  1. En un ítem con cantidad 8 y total 4.800.000,00 (misma base), corregir el precio a 2.150.000,00.
- **Resultado esperado:** comprobación "inconsistente"; el ítem queda "pendiente de revisión" con "inconsistencia aritmética".

### QA-08: Validar con inconsistencia abierta

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-03
- **Datos de prueba:**

  | Caso | Indicación | Resultado |
  | ---- | ---------- | --------- |
  | A | Ninguna | rechazo: "El ítem tiene inconsistencias aritméticas abiertas: corrija los valores o indique que el error está en el documento" |
  | B | Error del documento, comentario "La tabla del oferente suma mal" | validado; inconsistencia "resuelta" como "inconsistencia del documento" |
  | C | Error del documento, comentario vacío | rechazo por comentario obligatorio |

- **Pasos:**
  1. Validar el ítem de QA-07 en cada caso.
- **Resultado esperado:** el de la tabla.

### QA-09: Rechazar un ítem

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-08
- **Pasos:**
  1. Rechazar un ítem con el motivo "no es un televisor del alcance".
- **Resultado esperado:** "rechazado", no disponible para comparación; motivo, usuario y fecha registrados; datos y evidencias conservados.

### QA-10: Motivo "otro" y motivo fuera de la lista

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Datos de prueba:**

  | Motivo | Comentario | Resultado |
  | ------ | ---------- | --------- |
  | otro | (vacío) | "El comentario es obligatorio cuando el motivo es 'otro'" |
  | otro | "Ítem de un lote anulado" | rechazado |
  | "precio raro" | — | "Valor no permitido para motivo de rechazo" |

- **Pasos:**
  1. Rechazar con cada combinación.
- **Resultado esperado:** el de la tabla.

### QA-11: Reabrir un ítem rechazado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-02, RN-09
- **Pasos:**
  1. Tras QA-09, reabrir con comentario "Revisado: sí es un televisor 43 pulgadas".
- **Resultado esperado:** "pendiente de revisión" con motivo "reabierto por el Revisor"; historial con la operación.

### QA-12: Transiciones inválidas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-02, RN-09
- **Datos de prueba:**

  | Estado | Operación | Mensaje esperado |
  | ------ | --------- | ---------------- |
  | rechazado | validar | "Reabra el ítem antes de validarlo o corregirlo" |
  | rechazado | corregir | "Reabra el ítem antes de validarlo o corregirlo" |
  | rechazado | reabrir sin comentario | "El comentario es obligatorio para reabrir un ítem" |

- **Pasos:**
  1. Ejecutar cada operación.
- **Resultado esperado:** el mensaje de la tabla y sin cambios.

### QA-13: Validaciones de valores numéricos y de texto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-05
- **Datos de prueba:**

  | Campo | Inválidos | Válidos límite |
  | ----- | --------- | -------------- |
  | Cantidad | 0, 1.000.000, 2,5 | 1, 999.999 |
  | Precio unitario | 0, -1, "dos millones", 10.000.000.000,01, 1.000,555 | 0,01, 10.000.000.000 |
  | Tamaño (pulgadas) | 0, 150,1 | 150 |
  | Tamaño (cm) | 381,1 | 381 |
  | Tasa de IVA | 101 | 0, 100 |
  | Base | "con iva incluido" | `con_iva` |
  | Marca | 201 caracteres | 200 caracteres |
  | Descripción | 1.001 caracteres | 1.000 caracteres |

- **Pasos:**
  1. Corregir cada valor.
- **Resultado esperado:** los inválidos se rechazan con el mensaje de RN-05 del campo y no cambia ningún valor; los válidos se aceptan.

### QA-14: Evidencia inexistente o de otro proceso; operación con un campo inválido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-05
- **Datos de prueba:**

  | Caso | Corrección | Resultado |
  | ---- | ---------- | --------- |
  | A | Cantidad 8 con evidencia "Propuesta_economica_ganador.pdf, página 9" | "La ubicación de evidencia no existe en el documento indicado" |
  | B | Cantidad 8 con evidencia "Oferta_otro_proceso.pdf, página 1" | mismo mensaje |
  | C | Cantidad 8 válida + precio 0 en la misma operación | rechazo completo; la cantidad no cambia |

- **Pasos:**
  1. Ejecutar cada corrección.
- **Resultado esperado:** el de la tabla.

### QA-15: Resolver propuesta de reextracción

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Caso | Acción | Valor vigente esperado |
  | ---- | ------ | ---------------------- |
  | A | Aceptar propuesta 2.090.000,00 | 2.090.000,00, origen "reextracción aceptada" |
  | B | Descartar propuesta | 2.150.000,00; propuesta "descartada" |

- **Pasos:**
  1. Ejecutar cada acción sobre un ítem validado con una propuesta de precio 2.090.000,00.
- **Resultado esperado:** el de la tabla; en ambos casos se registran usuario y fecha y desaparece el motivo "propuesta de reextracción".

### QA-16: Modificación concurrente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-01
- **Pasos:**
  1. Consultar el ítem (versión 3).
  2. Provocar una reevaluación automática (versión 4).
  3. Guardar una corrección con versión 3.
- **Resultado esperado:** rechazo con "El ítem fue modificado por otra operación; vuelva a consultarlo"; sin cambios.

### QA-17: Historial inmutable y auditoría

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-11, RN-12
- **Pasos:**
  1. Tras QA-03 y QA-09, intentar modificar y eliminar una entrada del historial como Administrador.
  2. Consultar los eventos de auditoría.
- **Resultado esperado:** ambas operaciones sobre el historial se rechazan; el valor extraído original 10 sigue consultable; existen eventos de auditoría de la corrección y del rechazo con usuario, fecha, ítem y operación.

### QA-18: El Analista no puede revisar

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar validar, corregir, rechazar y reabrir.
  2. Consultar el estado y el historial del ítem.
- **Resultado esperado:** acceso denegado en las cuatro operaciones, sin cambios; la consulta sí funciona.

### QA-19: Consulta de ítems por estado

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Caso | Filtro | Resultado esperado |
  | ---- | ------ | ---------------- |
  | A | Estado "pendiente de revisión" con 3 ítems | 3 ítems con datos, evidencias, confianzas, motivos e historial |
  | B | Estado "rechazado" sin ítems | lista vacía |

- **Pasos:**
  1. Como Administrador, consultar cada filtro.
- **Resultado esperado:** el de la tabla.

---

**Total de casos:** 19
