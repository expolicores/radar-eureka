# Casos de Prueba — HU-081: Ver el estado de procesamiento del contrato en la ficha

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la sección "Estado de procesamiento" y el resumen del encabezado: las cinco etapas, sus cuatro estados y reglas de cálculo para SECOP II y TVEC, revisión humana pendiente, fuente sin documentos, extracción desactivada, errores, comparación parcial, ítems sin precio, clasificación en revisión, estado general, fechas, cobertura, lenguaje, rendimiento y accesibilidad. Quedan fuera la ejecución de los procesos y el detalle de motivos (HU-082).

## Precondiciones y Datos Base

- **Usuario:** `analista.piloto1@prueba.co` (Analista).
- **Registros semilla:**

  | Registro | Situación |
  | -------- | --------- |
  | P1 (SECOP II) | candidato el 02/09/2026 08:00; 8 de 23 documentos priorizados y obtenidos el 05/09/2026 10:15; extracción terminada el 06/09/2026 14:30; 0 ítems pendientes de revisión; 3 ítems con precio, todos comparados el 07/09/2026 06:00 |
  | P2 (SECOP II) | documentos obtenidos; 3 de 8 documentos priorizados aún sin extraer |
  | P3 (SECOP II) | extracción terminada; 2 ítems pendientes de revisión humana |
  | P4 (SECOP II) | la fuente no publicó documentos |
  | P5 (SECOP II) | 2 documentos sin extraer; extracción con IA desactivada |
  | P6 (SECOP II) | descarga fallida en los 4 documentos priorizados |
  | P6b (SECOP II) | documentos obtenidos; extracción fallida en todos |
  | P7 (TVEC) | orden con 1 ítem estructurado, comparado |
  | P8 (SECOP II) | 4 ítems con precio, 3 comparados |
  | P9 (SECOP II) | extracción terminada; ningún ítem con precio unitario |
  | P10 (SECOP II) | candidato; clasificación de ítems en revisión |
  | P11 (SECOP II) | extracción terminada sin ningún ítem |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-03 / RN-04 / RN-05 / RN-07 / RN-10 | QA-01 |
| Escenario 2 / RN-06 / RN-07 / RN-09 | QA-02 |
| Escenario 3 / RN-06 | QA-03 |
| Escenario 4 / RN-04 / RN-09 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-04 / RN-05 | QA-06 |
| Escenario 7 / RN-08 | QA-07 |
| Escenario 8 / RN-07 | QA-08 |
| Escenario 9 / RN-07 | QA-09 |
| Escenario 10 / RN-03 | QA-10 |
| RN-06 extracción sin ítems | QA-11 |
| RN-11 cobertura 100 % | QA-12 |
| RN-12 | QA-13 |
| RN-13 | QA-14 |

---

## Casos de Prueba

### QA-01: Contrato completamente procesado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-03 / RN-04 / RN-05 / RN-07 / RN-10
- **Pasos:**
  1. Abrir la ficha de P1 en "Estado de procesamiento".
- **Resultado esperado:** etapas en orden Identificado (02/09/2026 08:00), Documentos obtenidos ("8 documentos priorizados de 23 publicados", 05/09/2026 10:15), Extraído (06/09/2026 14:30), Revisado y Comparado (07/09/2026 06:00), todas "Completada"; encabezado "Estado: Comparado".

### QA-02: Etapa intermedia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-06 / RN-07 / RN-09
- **Pasos:**
  1. Abrir la ficha de P2.
- **Resultado esperado:** Identificado y Documentos obtenidos "Completada"; Extraído, Revisado y Comparado "En curso o pendiente" (Revisado y Comparado sin conteo); encabezado "Estado: Documentos obtenidos".

### QA-03: Ítems pendientes de revisión humana

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-06
- **Pasos:**
  1. Abrir la ficha de P3.
- **Resultado esperado:** Revisado "En curso o pendiente" con "2 ítems pendientes de revisión humana"; encabezado "Estado: Extraído".

### QA-04: Fuente sin documentos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04 / RN-09
- **Pasos:**
  1. Abrir la ficha de P4 y activar "Ver motivos".
- **Resultado esperado:** Documentos obtenidos "Incompleta" con "La fuente no ha publicado documentos para este proceso."; Extraído, Revisado y Comparado "No aplica"; encabezado "Estado: Identificado — con información insuficiente"; el enlace lleva a la sección de motivos.

### QA-05: Extracción desactivada

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-05
- **Pasos:**
  1. Abrir la ficha de P5.
- **Resultado esperado:** Extraído "En curso o pendiente" con "La extracción automática de documentos está desactivada temporalmente; los datos ya extraídos y las comparaciones siguen disponibles."

### QA-06: Errores en obtención y en extracción

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-04 / RN-05
- **Pasos:**
  1. Abrir la ficha de P6.
  2. Abrir la ficha de P6b.
- **Resultado esperado:** P6: Documentos obtenidos "Incompleta" con "No se pudieron obtener los documentos priorizados. El equipo de operación lo revisará." y Extraído "No aplica"; P6b: Extraído "Incompleta" con "No se pudieron leer los documentos priorizados. El equipo de operación lo revisará."

### QA-07: Orden TVEC

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Abrir la ficha de P7.
- **Resultado esperado:** Identificado "Completada"; Documentos obtenidos y Extraído "No aplica" con "Datos estructurados publicados por la TVEC"; Revisado y Comparado "Completada"; encabezado "Estado: Comparado".

### QA-08: Comparación parcial

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Abrir la ficha de P8.
- **Resultado esperado:** Comparado "En curso o pendiente" con "3 de 4 ítems con precio unitario comparados".

### QA-09: Ningún ítem con precio unitario

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-07
- **Pasos:**
  1. Abrir la ficha de P9.
- **Resultado esperado:** Comparado "No aplica" con "Ningún ítem tiene precio unitario para comparar." y "Ver motivos".

### QA-10: Clasificación en revisión

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** Escenario 10 / RN-03
- **Pasos:**
  1. Abrir la ficha de P10.
- **Resultado esperado:** Identificado "Completada" con "Candidato identificado el {fecha}; clasificación de ítems en revisión".

### QA-11: Extracción terminada sin ítems

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Pasos:**
  1. Abrir la ficha de P11.
- **Resultado esperado:** Extraído "Completada"; Revisado "No aplica"; Comparado "No aplica".

### QA-12: La sección existe en todas las fichas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-11
- **Precondiciones:** universo del MVP cargado.
- **Pasos:**
  1. Abrir automáticamente la ficha de cada registro visible del universo.
- **Resultado esperado:** el 100 % de las fichas muestra la sección con las cinco etapas y el estado general.

### QA-13: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Pasos:**
  1. Buscar los términos prohibidos en la sección de P1 a P11.
- **Resultado esperado:** 0 apariciones de "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".

### QA-14: Rendimiento, accesibilidad y móvil

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-13
- **Precondiciones:** 20 sesiones concurrentes.
- **Pasos:**
  1. Abrir fichas durante 10 minutos.
  2. Leer la sección con lector de pantalla y verla a 360 px.
- **Resultado esperado:** ficha en ≤ 3 s (p95); las etapas se leen como lista ordenada con su estado en texto; a 360 px la línea de etapas es vertical.

---

**Total de casos:** 14
