# Casos de Prueba — HU-027: Detectar inconsistencias aritméticas en los datos extraídos y dirigirlas a revisión de calidad

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la comprobación del ítem y de la tabla, la tolerancia, el tratamiento de bases tributarias distintas, los casos no comprobables, el efecto sobre la revisión, la resolución y el lenguaje. Los datos extraídos se suministran como entradas simuladas. Queda fuera: la pantalla de revisión (HU-028) y los precios anormalmente bajos (épica de señales).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Tolerancia: 0,5 % y mínimo COP 100.
- Lista de términos prohibidos: "sobreprecio", "corrupción", "fraude", "hallazgo fiscal".

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02 | QA-01 |
| Escenario 2 / RN-06, RN-07, RN-09 | QA-02 |
| Escenario 3 / RN-04 | QA-03, QA-04 |
| Escenario 4 / RN-03 | QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 / RN-02 | QA-07 |
| Escenario 7 / RN-05 | QA-08 |
| Escenario 8 / RN-05 | QA-09 |
| Escenario 9 / RN-01, RN-08 | QA-10, QA-11 |
| Escenario 10 / RN-09 | QA-12 |
| RN-04 (configuración) | QA-13 |
| RN-11 / Permisos | QA-14 |

---

## Casos de Prueba

### QA-01: Ítem consistente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02
- **Pasos:**
  1. Comprobar el ítem con cantidad 8, precio 2.150.000,00 y total 17.200.000,00, todos `con_iva`.
- **Resultado esperado:** "consistente"; sin motivo de revisión.

### QA-02: Error aritmético de la tabla

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-06, RN-07, RN-09
- **Pasos:**
  1. Comprobar cantidad 4, precio 1.020.000,00 y total 4.800.000,00 con la misma base.
- **Resultado esperado:** "inconsistente" con detalle "4 × 1.020.000,00 = 4.080.000,00 ≠ 4.800.000,00 (diferencia 720.000,00; 17,65 %)"; el ítem queda con "inconsistencia aritmética abierta", en revisión, no disponible para comparación, y con el texto "Inconsistencia aritmética: revisión de calidad o de evidencia; no constituye una irregularidad".

### QA-03: Valores límite de la tolerancia porcentual

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Cantidad × precio | Total | Diferencia | Resultado |
  | ----------------- | ----- | ---------- | --------- |
  | 10 × 1.000.000,00 | 10.050.000,00 | 50.000 (0,50 % de 10.050.000 = 50.250) | consistente |
  | 10 × 1.000.000,00 | 10.051.000,00 | 51.000 (límite 50.255) | inconsistente |
  | 10 × 1.000.000,00 | 10.060.000,00 | 60.000 (límite 50.300) | inconsistente |
  | 3 × 3.333.333,00 | 10.000.000,00 | 1,00 | consistente |

- **Pasos:**
  1. Comprobar cada ítem.
- **Resultado esperado:** el de la tabla.

### QA-04: Tolerancia mínima en valores pequeños

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Cantidad × precio | Total | Diferencia | Límite | Resultado |
  | ----------------- | ----- | ---------- | ------ | --------- |
  | 1 × 10.000,00 | 10.100,00 | 100 | máx(50,50; 100) = 100 | consistente |
  | 1 × 10.000,00 | 10.101,00 | 101 | 100 | inconsistente |

- **Pasos:**
  1. Comprobar cada ítem.
- **Resultado esperado:** el de la tabla.

### QA-05: Bases distintas con tasa documentada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03
- **Datos de prueba:**

  | Caso | Precio (base) | Total (base) | Tasa | Esperado | Resultado |
  | ---- | ------------- | ------------ | ---- | -------- | --------- |
  | A | 1.806.723,00 (sin_iva) | 17.200.000,00 (con_iva) | 19 % | 17.200.002,96 | consistente |
  | B | 2.150.000,00 (con_iva) | 14.453.782,00 (sin_iva) | 19 % | 14.453.781,51 | consistente |
  | C | 1.806.723,00 (sin_iva) | 14.453.784,00 (con_iva) | 19 % | 17.200.002,96 | inconsistente |

- **Pasos:**
  1. Comprobar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-06: Bases distintas sin tasa o con base indeterminada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-03
- **Datos de prueba:**

  | Caso | Precio | Total | Tasa | Resultado |
  | ---- | ------ | ----- | ---- | --------- |
  | A | sin_iva | con_iva | no publicada | no comprobable: bases tributarias distintas sin tasa de IVA documentada |
  | B | indeterminada | con_iva | 19 % | no comprobable, mismo motivo |
  | C | indeterminada | indeterminada | — | comparación directa |

- **Pasos:**
  1. Comprobar cada caso con cantidad 8, precio 2.150.000,00 y total 17.200.000,00.
- **Resultado esperado:** el de la tabla (C queda "consistente").

### QA-07: Datos faltantes y precio derivado

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-02
- **Datos de prueba:**

  | Caso | Situación | Resultado |
  | ---- | --------- | --------- |
  | A | Sin total | no comprobable: faltan datos para comprobar |
  | B | Sin cantidad | no comprobable: faltan datos para comprobar |
  | C | Precio derivado | no comprobable: precio derivado: consistente por construcción |

- **Pasos:**
  1. Comprobar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-08: Suma de ítems frente al total de la tabla

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-05
- **Datos de prueba:**

  | Caso | Totales de ítems | Total de la tabla | Resultado |
  | ---- | ---------------- | ----------------- | --------- |
  | A | 8.400.000,00 + 9.800.000,00 | 19.200.000,00 | inconsistente; ambos ítems con inconsistencia abierta |
  | B | 8.400.000,00 + 9.800.000,00 | 18.200.000,00 | consistente |
  | C | 8.400.000,00 + (nulo) | 18.200.000,00 | no comprobable: faltan datos para comprobar |

- **Pasos:**
  1. Comprobar cada tabla (solo televisores, misma base).
- **Resultado esperado:** el de la tabla.

### QA-09: Tabla con otros bienes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-05
- **Pasos:**
  1. Comprobar una tabla que incluye computadores (no extraídos) con total publicado.
- **Resultado esperado:** "no comprobable: la tabla incluye bienes que no son televisores"; los ítems no quedan con inconsistencia por esta comprobación.

### QA-10: Resolución por corrección

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-01, RN-08
- **Pasos:**
  1. Tras QA-02, el Administrador corrige el total a 4.080.000,00 con evidencia.
- **Resultado esperado:** nueva comprobación "consistente"; inconsistencia "resuelta" con usuario, fecha y acción "corrección"; el ítem pierde el motivo "inconsistencia aritmética".

### QA-11: Resolución como error del documento

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Caso | Comentario | Resultado |
  | ---- | ---------- | --------- |
  | A | "El documento publica 4.800.000 por error de suma; los valores extraídos son fieles" | resuelta; visible como "inconsistencia del documento" |
  | B | (vacío) | rechazado: el comentario es obligatorio |

- **Pasos:**
  1. Tras QA-02, el Administrador valida el ítem indicando error del documento con cada comentario.
- **Resultado esperado:** el de la tabla.

### QA-12: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-09
- **Pasos:**
  1. Generar las inconsistencias de QA-02, QA-03 y QA-08.
  2. Buscar los términos prohibidos en todos los textos generados.
- **Resultado esperado:** 0 coincidencias; todos los textos incluyen "revisión de calidad o de evidencia; no constituye una irregularidad".

### QA-13: Configuración de la tolerancia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Parámetro | Valores válidos | Valores inválidos |
  | --------- | --------------- | ----------------- |
  | Tolerancia porcentual | 0,0 %, 10,0 % | -0,1 %, 10,1 % |
  | Tolerancia mínima | 0, 100.000 | -1, 100.001 |

- **Pasos:**
  1. Como Administrador, guardar cada valor.
- **Resultado esperado:** los válidos se guardan; los inválidos se rechazan con "Valor fuera de rango para {parámetro}: debe estar entre {mín} y {máx}" y se conserva el anterior.

### QA-14: Funciona sin IA y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-11 / Permisos requeridos
- **Pasos:**
  1. Desactivar la extracción con IA y repetir QA-02.
  2. Como `analista1@piloto.test`, consultar el detalle de la inconsistencia e intentar cambiar la tolerancia.
- **Resultado esperado:** QA-02 da el mismo resultado sin llamadas al servicio de IA; el Analista ve el detalle y recibe acceso denegado al cambiar la tolerancia.

---

**Total de casos:** 14
