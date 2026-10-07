# Casos de Prueba — HU-011: Clasificar contratos SECOP II y soportar contratos mixtos a nivel de ítem

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la clasificación preliminar de contratos SECOP II (C1 a C7), la derivación por ítems (C8 a C10), los contratos mixtos, el indicador `en_analisis`, el indicador `apto_gestion_documental`, la precedencia manual, el registro de eventos y el estado vacío.

Queda fuera: las reglas por ítem (HU-010), la IA (HU-012) y la corrección manual en sí (HU-013).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Listas iniciales de RN-03, reglas versión 1.
- Todos los contratos son candidatos SECOP II en "Pendiente de clasificación", sin ítems salvo que se indique.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / C5, RN-08 | QA-01 |
| Escenario 2 / C1 | QA-02 |
| Escenario 3, 4 / C2 | QA-03 |
| Escenario 5 / C3 | QA-04 |
| Escenario 6 / C4 | QA-05 |
| Escenario 7 / C7 | QA-06 |
| Escenario 8 / C6 | QA-06 |
| RN-04 (orden) | QA-07 |
| Escenario 9 / RN-05, RN-06, RN-07 | QA-08 |
| Escenario 10 / C9 | QA-09 |
| Escenario 11 / C10 | QA-10 |
| Escenario 12 / RN-09 | QA-11 |
| Escenario 13 / RN-07 | QA-12 |
| Escenario 14 | QA-13 |
| RN-10 | QA-14 |
| RN-12 | QA-15 |

---

## Casos de Prueba

### QA-01: Contrato con televisores queda incluido preliminar

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / C5, RN-08
- **Pasos:**
  1. Clasificar "Adquisición de televisores 65 pulgadas para aulas".
- **Resultado esperado:** "Incluido", nivel "Preliminar (contrato)", criterio "C5 — El contrato menciona televisores; pendiente de confirmación por ítem", método "Regla", `apto_gestion_documental = sí`.

### QA-02: Comodato excluido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / C1
- **Pasos:**
  1. Clasificar "Contrato de comodato de televisores para la sede".
- **Resultado esperado:** "Excluido" con "C1 — El contrato no es una compra (comodato, arrendamiento o préstamo)"; `apto_gestion_documental = no`.

### QA-03: Servicios con y sin adquisición (tabla de decisión)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenarios 3 y 4 / C2
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | objeto | Mantenimiento preventivo y correctivo de televisores y equipos audiovisuales | SV sin AD → C2 Excluido |
  | objeto | Suministro e instalación de televisores para el hospital | SV con AD → C5 Incluido |
  | objeto | Servicio de soporte técnico a pantallas | SV sin AD, sin T → C2 Excluido |

- **Pasos:**
  1. Clasificar cada contrato.
- **Resultado esperado:** según la nota.

### QA-04: Posible CCTV

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / C3
- **Pasos:**
  1. Clasificar "Adquisición de cámaras y televisores para el sistema de circuito cerrado".
- **Resultado esperado:** "Requiere revisión" con "C3 — El contrato menciona televisores junto con CCTV o videovigilancia".

### QA-05: Proceso por lotes

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / C4
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | objeto / descripción | "Lote 2 equipos de cómputo" / "…lote 1 televisores, lote 2 equipos de cómputo" | T solo en descripción + lote → C4 |
  | objeto / descripción | "Lote 1 televisores" / "…lote 1 televisores, lote 2 cómputo" | T en objeto → C5 |
  | objeto / descripción | "Dotación aulas" / "Compra de televisores" | T solo en descripción sin "lote" → C5 |

- **Pasos:**
  1. Clasificar cada contrato.
- **Resultado esperado:** según la nota; C4 con "Proceso por lotes: verificar que el lote del contrato corresponda al televisor".

### QA-06: Solo UNSPSC, con y sin producto excluido

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenarios 7 y 8 / C6, C7
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | objeto | Dotación de equipos para auditorio | C7 Requiere revisión |
  | objeto | Suministro de videowall para centro de control | C6 Excluido |

- **Pasos:**
  1. Clasificar ambos (UNSPSC V1.52161505).
- **Resultado esperado:** según la nota con sus criterios.

### QA-07: Orden de precedencia preliminar

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | objeto | Arrendamiento y mantenimiento de televisores | C1 gana a C2 |
  | objeto | Compra de televisores y videowall | C5 gana a C6 (T presente) |

- **Pasos:**
  1. Clasificar.
- **Resultado esperado:** C1 Excluido y C5 Incluido preliminar.

### QA-08: Contrato mixto confirmado por ítems

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-05, RN-06, RN-07
- **Precondiciones:** contrato "Compra de 52 equipos de cómputo y 1 smart tv" en "Incluido" preliminar.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem 1 | Computador de escritorio — Excluido R2 | |
  | Ítem 2 | Impresora láser — Excluido R2 | |
  | Ítem 3 | Smart TV 50 pulgadas — Incluido R10 | |

- **Pasos:**
  1. Registrar y clasificar los 3 ítems.
- **Resultado esperado:** contrato "Incluido", nivel "Confirmado por ítem", "C8 — Al menos un ítem es un televisor dentro del límite de categoría", `contrato_mixto = sí`, `items_tv_incluidos = 1`, `items_excluidos = 2`, `items_en_revision = 0`; ítem 3 `en_analisis = sí`, ítems 1 y 2 `en_analisis = no`.

### QA-09: Ningún ítem es televisor

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / C9
- **Pasos:**
  1. En un contrato "Incluido" preliminar, clasificar sus 2 ítems como "Excluido" (R3 soporte y R4 mantenimiento).
- **Resultado esperado:** contrato "Excluido", "C9 — Ningún ítem del contrato es un televisor dentro del límite de categoría"; `apto_gestion_documental = no`; ningún ítem en análisis.

### QA-10: Ítems en revisión sin incluidos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / C10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ítem 1 | Monitor TV 43 para CCTV — Requiere revisión R6 | |
  | Ítem 2 | Cámara domo — Excluido R2 | |
  | Ítem 3 | (sin clasificar) | se ignora |

- **Pasos:**
  1. Derivar la clasificación.
- **Resultado esperado:** "Requiere revisión", "C10 — El contrato tiene ítems pendientes de revisión y ningún televisor confirmado"; `apto_gestion_documental = sí`.

### QA-11: Contrato excluido manualmente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-09
- **Precondiciones:** contrato de QA-08 con clasificación vigente "Excluido" método "Manual".
- **Pasos:**
  1. Reclasificar el ítem 3 (sigue "Incluido").
- **Resultado esperado:** el contrato conserva "Excluido (manual)"; `resultado_derivado = Incluido` queda como información; el ítem 3 `en_analisis = no`.

### QA-12: Indicador de análisis para ítems TVEC

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 13 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Clasificación ítem TVEC | Incluido | en_analisis = sí |
  | Clasificación ítem TVEC | Excluido | no |
  | Clasificación ítem TVEC | Requiere revisión | no |

- **Pasos:**
  1. Calcular el indicador con cada clasificación.
- **Resultado esperado:** según la nota.

### QA-13: Sin contratos pendientes

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 14
- **Pasos:**
  1. Ejecutar sin pendientes.
- **Resultado esperado:** "No hay contratos SECOP II pendientes de clasificación."

### QA-14: Eventos solo ante cambios

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. En el contrato de QA-08, agregar un cuarto ítem "Mouse" (Excluido R2).
  2. Reclasificar todos los contratos sin cambios.
- **Resultado esperado:** (1) el contrato sigue "Incluido" C8 sin nuevo evento; sus contadores pasan a `items_excluidos = 3`. (2) No se agregan eventos. Cada evento existente tiene resultado, nivel, criterio, términos, método, versión y fecha.

### QA-15: Resumen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Pasos:**
  1. Clasificar juntos los contratos de QA-01, QA-02, QA-04 y QA-08.
- **Resultado esperado:** "Clasificación de contratos SECOP II: 4 evaluados. Incluidos: 2 (preliminar: 1; confirmados: 1). Excluidos: 1. Requiere revisión: 1. Mixtos: 1. Omitidos por clasificación manual: 0."

---

**Total de casos:** 15
