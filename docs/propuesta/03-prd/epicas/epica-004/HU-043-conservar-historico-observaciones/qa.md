# Casos de Prueba — HU-043: Conservar el histórico inmutable de observaciones de mercado

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba que la base de observaciones sea de solo inserción: repetición de observaciones, rechazo de edición y borrado, anulación con motivo, corrección atómica, protección ante duplicados dentro de un mismo contexto, consulta del histórico con filtros, permisos y eventos auditables.

Fuera de alcance: validación del registro mínimo campo a campo (HU-042) y los canales que crean observaciones (HU-047 a HU-050).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Observaciones semilla** (todas de Samsung, modelo publicado `UN55DU7000KXZL`, salvo OBS-3):

  | ID | Fuente | Precio efectivo | fecha_observacion | Método | Estado |
  | ----- | ----- | ----- | ----- | ----- | ----- |
  | OBS-1 | Alkosto | 1899900 | 2026-09-25T09:00 | manual | vigente |
  | OBS-2 | Alkosto | 18999000 | 2026-09-28T09:00 | manual | vigente |
  | OBS-3 | Falabella | 1849900 (modelo `UN55DU700KXZL`) | 2026-09-29T15:00 | manual | vigente |
  | OBS-5 | Alkosto | 1849900 | 2026-09-18T09:00 | sitemap_datos_estructurados | vigente |
  | OBS-6 | Falabella | 1879900 | 2026-09-30T11:00 | manual | vigente |

- Fecha de ejecución de referencia: 2026-10-02.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 | QA-01 |
| Escenario 2 / RN-01 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-03 | QA-04 |
| Escenario 5 / RN-03 | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| Escenario 7 / RN-04 | QA-07 |
| Escenario 8 / RN-04 | QA-08 |
| Escenario 9 / RN-04 | QA-09 |
| Escenario 10 / RN-06 | QA-10, QA-11 |
| Escenario 11 / RN-06 | QA-12 |
| Escenario 12 | QA-13 |
| RN-02 (duplicado en contexto) | QA-14 |
| RN-05 | QA-15 |
| RN-07 | QA-16 |
| RN-08 | QA-17 |

---

## Casos de Prueba

### QA-01: Nueva observación del mismo producto no reemplaza la anterior

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02
- **Pasos:**
  1. Registrar una observación de Alkosto, misma URL que OBS-1, precio 1799900, `fecha_observacion` 2026-10-02T09:00, con otro `id_contexto`.
  2. Consultar OBS-1 y la nueva.
- **Resultado esperado:** existen dos observaciones con identificadores distintos; OBS-1 conserva precio 1899900, su fecha y su evidencia.

### QA-02: Rechazo de modificación de campos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Datos de prueba:**

  | Actor | Campo | Nuevo valor |
  | ----- | ----- | ----- |
  | admin.po@prueba.local | precio_efectivo de OBS-1 | 1799900 |
  | proceso de comparación | iva_condicion de OBS-5 | incluido |

- **Resultado esperado:** ambas se rechazan con `"Las observaciones no se modifican. Para corregir, anule la observación y registre una nueva."`; los valores no cambian.

### QA-03: Rechazo de eliminación

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01
- **Pasos:**
  1. Intentar eliminar OBS-1 (vigente).
  2. Anular OBS-6 e intentar eliminarla.
- **Resultado esperado:** ambos intentos se rechazan con `"Las observaciones no se eliminan; solo pueden anularse."`; ambas siguen existiendo.

### QA-04: Anulación con motivo válido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | observación | OBS-2 |
  | motivo | "Precio digitado con un cero de más; ver captura" |

- **Resultado esperado:** OBS-2 queda `anulada`, `apta_para_referencia = no`, con `motivo_anulacion`, `anulada_por = admin.po@prueba.local` y `fecha_anulacion`; el resto de campos y la evidencia no cambian; aparece en el histórico con "incluir anuladas = sí".

### QA-05: Valores límite del motivo de anulación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-03
- **Datos de prueba:**

  | Longitud del motivo | Resultado |
  | ----- | ----- |
  | vacío | Rechazo: `"El motivo de anulación debe tener entre 10 y 500 caracteres."` |
  | 9 | Rechazo (mismo mensaje) |
  | 10 | Anulada |
  | 500 | Anulada |
  | 501 | Rechazo (mismo mensaje) |

- **Resultado esperado:** según la tabla; en los rechazos la observación sigue `vigente`. Usar una observación vigente distinta por cada variante aceptada.

### QA-06: Anulación repetida y reversión no permitidas

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-03
- **Precondiciones:** OBS-2 anulada (QA-04).
- **Pasos:**
  1. Anular OBS-2 de nuevo (simula doble envío).
  2. Intentar cambiar OBS-2 a `vigente`.
- **Resultado esperado:** paso 1: `"La observación OBS-2 ya está anulada."`; paso 2: `"Una anulación no se revierte; registre una nueva observación."`; existe un único evento `anulacion_observacion` para OBS-2.

### QA-07: Corrección atómica de una observación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-04
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | observación a corregir | OBS-3 |
  | motivo | "Modelo mal digitado, falta un cero" |
  | nueva observación | Igual a OBS-3 pero `modelo_referencia = UN55DU7000KXZL` y la misma evidencia |

- **Resultado esperado:** OBS-3 queda anulada con el motivo y `corregida_por = OBS-4`; se crea OBS-4 con `corrige_a = OBS-3`, `registrado_por = admin.po@prueba.local` y evidencia con el mismo hash que la de OBS-3.

### QA-08: Corrección con datos inválidos no aplica cambios

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-04
- **Pasos:**
  1. Corregir OBS-6 enviando una nueva observación sin evidencia.
- **Resultado esperado:** se devuelve `"La observación requiere al menos una evidencia."`; OBS-6 sigue `vigente` sin `corregida_por`; no se crea ninguna observación.

### QA-09: Corrección de una observación anulada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-04
- **Precondiciones:** OBS-2 anulada.
- **Resultado esperado:** `"Solo se pueden corregir observaciones vigentes."`; no se crea observación.

### QA-10: Consulta del histórico con y sin anuladas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-06
- **Precondiciones:** QA-04 y QA-07 ejecutados (OBS-2 y OBS-3 anuladas, OBS-4 creada).
- **Datos de prueba:**

  | Filtro | Valor |
  | ----- | ----- |
  | marca | samsung |
  | modelo | un55du7000-kxzl |
  | incluir_anuladas | sí, luego no |

- **Resultado esperado:** con "sí": OBS-4, OBS-6, OBS-2, OBS-1, OBS-5 (OBS-3 no coincide por modelo) ordenadas por `fecha_observacion` descendente, cada una con fuente, precio, fecha, `etiqueta_origen`, estado y vínculos `corrige_a` / `corregida_por`; con "no": se excluye OBS-2.

### QA-11: Filtros por fuente, método, EAN y rango de fechas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Filtros | Resultado esperado |
  | ----- | ----- |
  | fuente = Alkosto, método = sitemap_datos_estructurados | Solo OBS-5 |
  | desde 2026-09-25 hasta 2026-09-25 | Solo OBS-1 (límites inclusivos) |
  | desde 2026-09-30 hasta 2026-09-25 | `"La fecha inicial no puede ser posterior a la fecha final."` |
  | sin filtros | Todas las vigentes, paginadas de a 50 |

### QA-12: Consulta sin resultados

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11, RN-06
- **Datos de prueba:**

  | Filtro | Valor |
  | ----- | ----- |
  | marca / modelo | LG / OLED77C4PSA |

- **Resultado esperado:** lista vacía y `"No hay observaciones de mercado para los filtros indicados."`

### QA-13: Operaciones rechazadas para el rol Analista

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Pasos:**
  1. Como `analista1@prueba.local`: anular OBS-1, corregir OBS-1 y consultar el histórico de Samsung.
- **Resultado esperado:** las tres se rechazan con `"Operación permitida solo para el rol Administrador."`; OBS-1 sigue vigente.

### QA-14: Duplicado dentro del mismo contexto

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Datos de prueba:**

  | Intento | id_contexto | referencia_origen (url) | Resultado |
  | ----- | ----- | ----- | ---- |
  | 1 | EJEC-2026-10-02-ALK | https://www.alkosto.com/tv-x/p/0000000000002 | Creada |
  | 2 | EJEC-2026-10-02-ALK | misma URL | `"Observación duplicada en el contexto EJEC-2026-10-02-ALK: https://www.alkosto.com/tv-x/p/0000000000002."` |
  | 3 | EJEC-2026-10-09-ALK | misma URL | Creada |
  | 4 y 5 | BUSQ-0001, tipo texto "Tienda física Alkosto Calle 80" en ambos | — | Ambas creadas |

### QA-15: Anulación no altera cálculos previos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Pasos:**
  1. Registrar el resultado de un benchmark calculado que usó OBS-6.
  2. Anular OBS-6.
  3. Consultar el resultado calculado del paso 1 y luego leer las observaciones aptas del producto.
- **Resultado esperado:** el resultado del paso 1 no cambió; la lectura de observaciones aptas ya no incluye OBS-6 (`apta_para_referencia = no`).

### QA-16: Conservación sin purga y en respaldo

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Pasos:**
  1. Verificar que no existe ningún proceso programado que elimine observaciones.
  2. Restaurar el respaldo diario en un entorno de prueba.
- **Resultado esperado:** no hay purga configurada; las observaciones semilla, incluidas las anuladas, están presentes tras la restauración.

### QA-17: Eventos auditables de anulación y corrección

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Precondiciones:** QA-04, QA-05 (rechazos) y QA-07 ejecutados.
- **Resultado esperado:** existe un evento `anulacion_observacion` por cada anulación aceptada y un evento `correccion_observacion` para OBS-3 → OBS-4, cada uno con usuario, fecha y hora, identificadores y motivo; los intentos rechazados no generaron eventos.

---

**Total de casos:** 17
