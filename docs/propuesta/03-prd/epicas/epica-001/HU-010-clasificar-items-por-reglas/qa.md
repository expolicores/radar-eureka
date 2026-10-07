# Casos de Prueba — HU-010: Clasificar ítems candidatos contra el límite de categoría por reglas

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la clasificación determinística por ítem: cada regla R1 a R10 con su orden de precedencia, campos opcionales (`costo_servicio_discriminado`, `precio_unitario_discriminado`, `lote_descripcion`), registro del criterio y del método, precedencia manual, reclasificación por versión, validación de listas y estado vacío.

Queda fuera: la clasificación del contrato SECOP II (HU-011), la sugerencia con IA (HU-012) y la corrección manual (HU-013).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Reglas versión 1 con las listas iniciales de RN-04. Términos T: "televisor", "smart tv", "tv".
- Todos los ítems de prueba son candidatos en "Pendiente de clasificación"; origen TVEC salvo que se indique "SECOP II".

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / R10, RN-06, RN-09 | QA-01 |
| Escenario 2 / R1 | QA-02 |
| Escenario 3 / R2 | QA-03 |
| Escenario 4 / R3 | QA-04 |
| Escenario 5 / R4 | QA-05 |
| Escenario 6 / R5 | QA-06 |
| Escenario 7 / R6 | QA-07 |
| Escenario 8 / R7 | QA-08 |
| Escenario 9 / R8a, R8b | QA-09 |
| Escenario 10 / R9 | QA-10 |
| RN-05 (orden de precedencia) | QA-11 |
| Escenario 11 / RN-07 | QA-12 |
| Escenario 12 / RN-08 | QA-13 |
| Escenario 13 / RN-04 | QA-14 |
| Escenario 14 | QA-15 |
| RN-10 | QA-16 |

---

## Casos de Prueba

### QA-01: Televisores incluidos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / R10, RN-06, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | TELEVISOR SAMSUNG 55" UN55CU7000 SMART 4K | |
  | descripcion_item | GSF01-SMART TV LG 43LR6500PSA | |
  | descripcion_item | Televisor LED 24 pulgadas convencional | tamaño pequeño, no Smart |
  | descripcion_item | TELEVISOR LG CON CONTROL REMOTO | control remoto no está en AA |

- **Pasos:**
  1. Clasificar cada ítem.
- **Resultado esperado:** todos "Incluido", criterio "R10 — Televisor dentro del límite de categoría", método "Regla", `version_reglas = 1`, fecha, `estado_clasificacion = Clasificado`.

### QA-02: No es una compra

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / R1
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | Entrega en comodato de televisor 50 pulgadas | comodato |
  | descripcion_item | Alquiler de televisores para evento | alquiler (plural de término no aplica; "alquiler" exacto) |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** "Excluido" con "R1 — No es una compra (comodato, arrendamiento o préstamo)" y el término.

### QA-03: Ítem de contrato que no es televisor

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / R2
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item (SECOP II) | Computador portátil Core i5 16 GB | |
  | descripcion_item (SECOP II) | Aire acondicionado 12000 BTU | |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** "Excluido" con "R2 — El ítem no es un televisor".

### QA-04: Accesorio como producto principal vs. accesorio después del televisor

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / R3
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | SOPORTE DE PARED PARA TV 32 A 70 PULGADAS | AC antes de T → R3 |
  | descripcion_item | CONTROL REMOTO PARA TELEVISOR LG | R3 |
  | descripcion_item | Cable HDMI 2 metros televisor | R3 |
  | descripcion_item | Televisor 43 pulgadas y su control remoto | AC después de T → no R3 |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** las tres primeras "Excluido" con "R3 — Accesorio de televisor" y el término del accesorio; la cuarta no cumple R3 y termina "Incluido" (R10), porque "control remoto" no está en la lista AA de R9.

### QA-05: Servicio sobre televisores

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / R4
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item (SECOP II) | Mantenimiento preventivo de televisores del hospital | |
  | descripcion_item (SECOP II) | Servicio de reparación de TV | |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** "Excluido" con "R4 — Servicio sobre televisores (mantenimiento o instalación), no compra del bien".

### QA-06: Precio inseparable de instalación (tabla de decisión)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / R5
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion + costo_servicio_discriminado | Televisor 65 pulgadas incluida instalación y adecuación eléctrica / no | R5 Excluido |
  | ídem | ídem / nulo | nulo = no → R5 Excluido |
  | ídem | ídem / sí | R5 no aplica → R10 Incluido |

- **Pasos:**
  1. Clasificar cada combinación (origen SECOP II).
- **Resultado esperado:** según la nota; en los excluidos el criterio es "R5 — Precio inseparable de instalación, obra o servicio sin costo discriminado".

### QA-07: Productos excluidos van a revisión

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / R6
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | Monitor TV 43 pulgadas para CCTV | monitor, cctv |
  | descripcion_item | Pantalla interactiva tipo smart tv 75" | pantalla interactiva |
  | descripcion_item | Videowall 4 pantallas TV 55 | videowall |
  | descripcion_item | Televisor inflable publicitario | inflable |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** "Requiere revisión" con "R6 — Coincide con un producto excluido del límite de categoría" y los términos; `estado_clasificacion = En revisión`.

### QA-08: Lote sin televisores

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / R7
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | lote_descripcion | Lote 2: equipos de cómputo | R7 |
  | lote_descripcion | Lote 1: televisores y soportes | menciona T → no R7 |
  | lote_descripcion | (nula) | no R7 |

- **Pasos:**
  1. Clasificar un ítem SECOP II "Televisor 50 pulgadas" con cada lote.
- **Resultado esperado:** el primero "Requiere revisión" con "R7 — El lote del ítem no menciona televisores"; los otros "Incluido".

### QA-09: Kits

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / R8a, R8b
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | precio_unitario_discriminado | no | R8a Excluido |
  | precio_unitario_discriminado | nulo | R8b Requiere revisión |
  | precio_unitario_discriminado | sí | R8b Requiere revisión |

- **Pasos:**
  1. Clasificar "KIT TELEVISOR 43 + BARRA DE SONIDO" con cada valor.
- **Resultado esperado:** según la nota, con "R8 — Kit sin precio unitario determinable" o "R8 — Kit o combo: verificar que el precio unitario del televisor sea determinable".

### QA-10: Accesorio incluido

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10 / R9
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | Televisor 55 pulgadas con soporte de pared | R9 |
  | descripcion_item | TELEVISOR 50 + SOPORTE | "+" → R9 |
  | descripcion_item | Televisor 50 con garantía de dos años y soporte | soporte a 5 palabras de "con" → no R9 |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** las dos primeras "Requiere revisión" con "R9 — Accesorio incluido en el ítem sin precio discriminado"; la tercera "Incluido".

### QA-11: Orden de precedencia de reglas

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | descripcion_item | Comodato de monitor y televisor | R1 gana a R6 |
  | descripcion_item | Mantenimiento de videowall y TV | R4 gana a R6 |
  | descripcion_item | Kit televisor con soporte | R8b gana a R9 |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** se aplica la primera regla de la nota.

### QA-12: Clasificación manual vigente no se reemplaza

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-07
- **Precondiciones:** ítem "Monitor TV 43 pulgadas para CCTV" con clasificación vigente "Excluido" método "Manual".
- **Pasos:**
  1. Ejecutar la reclasificación total.
- **Resultado esperado:** la clasificación vigente sigue siendo la manual; no se agrega evento; cuenta "Omitido por clasificación manual".

### QA-13: Reclasificación con nueva versión

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-08
- **Pasos:**
  1. Guardar versión 2 de reglas agregando "pantalla publicitaria" a PE.
  2. Ejecutar la reclasificación total con un ítem "Televisor pantalla publicitaria 50" (antes "Incluido").
- **Resultado esperado:** el ítem pasa a "Requiere revisión" (R6) con `version_reglas = 2`; el evento anterior se conserva; los ítems sin cambios no agregan evento; el resumen muestra "Cambiaron de resultado: 1".

### QA-14: Validación de términos de regla

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 13 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Término PE | "x" | 1 carácter → rechazo |
  | Término PE | "pc" | 2 → aceptado |
  | Lista KT | (vacía) | aceptado; R8 nunca se cumple |

- **Pasos:**
  1. Guardar cada configuración.
- **Resultado esperado:** la primera se rechaza con "Los términos de las reglas deben tener entre 2 y 50 caracteres: x" y se conserva la versión vigente; las otras se aceptan.

### QA-15: Sin pendientes

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 14
- **Pasos:**
  1. Ejecutar sin ítems pendientes.
- **Resultado esperado:** "No hay ítems pendientes de clasificación."

### QA-16: Resumen por resultado y criterio

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Clasificar juntos los 4 ítems de QA-01, los 2 de QA-02 y los 4 de QA-07.
- **Resultado esperado:** "Clasificación por reglas: 10 evaluados. Incluidos: 4. Excluidos: 2. Requiere revisión: 4. Omitidos por clasificación manual: 0. Cambiaron de resultado: 0." y totales R10: 4, R1: 2, R6: 4.

---

**Total de casos:** 16
