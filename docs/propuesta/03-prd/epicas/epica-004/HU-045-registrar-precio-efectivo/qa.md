# Casos de Prueba — HU-045: Usar el precio efectivo de venta y conservar el precio anterior solo como evidencia

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la determinación de `precio_efectivo` y `precio_anterior` en canales manuales y en captura automática: selección entre varios precios, valores límite y consistencia del precio anterior, ausencia de precio vigente, interpretación de formatos de precio, uso exclusivo del precio efectivo como referencia y separación frente a precios condicionados.

Fuera de alcance: detección y registro de condiciones especiales (HU-046) y la lectura de las páginas por cada conector (HU-051, HU-052).

## Precondiciones y Datos Base

- **Usuario:** `admin.po@prueba.local` (Administrador).
- **Observación manual base (OBS-M):** Alkosto, "Televisor Samsung 55 pulgadas Crystal UHD 4K Smart", Samsung, UN55DU7000KXZL, vendedor Alkosto, URL https://www.alkosto.com/televisor-samsung-55/p/0000000000001, fecha 2026-10-02T10:00, IVA indeterminado, evidencia captura.png, condición ninguna, método manual, canal individual.
- **Ejecución de captura de prueba:** `EJEC-PRUEBA-ALK-02` con páginas simuladas de Alkosto.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 / RN-03 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-03 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| Escenario 7 / RN-05 | QA-07 |
| Escenario 8 / RN-03 | QA-08 |
| RN-06 | QA-09 |
| RN-07 | QA-10 |

---

## Casos de Prueba

### QA-01: Precio vigente y precio anterior

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-03
- **Datos de prueba:**

  | Precio publicado | Rótulo |
  | ----- | ----- |
  | 1739900 | precio de oferta vigente |
  | 4200000 | "Antes" (tachado) |

- **Pasos:**
  1. Procesar la página en `EJEC-PRUEBA-ALK-02`.
- **Resultado esperado:** `precio_efectivo = 1739900`; `precio_anterior = 4200000`.

### QA-02: Solo precio vigente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Pasos:**
  1. Procesar una página con un único precio 1899900.
  2. Registrar OBS-M con `precio_efectivo = 1899900` y sin precio anterior.
- **Resultado esperado:** en ambos casos `precio_efectivo = 1899900` y `precio_anterior` nulo.

### QA-03: Varios precios generales vigentes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 2049900 | precio internet |
  | 2199900 | precio normal (no tachado) |

- **Resultado esperado:** `precio_efectivo = 2049900`; `precio_anterior = 2199900`.

### QA-04: Límites del precio anterior en carga manual

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Datos de prueba:**

  | precio_efectivo | precio_anterior | Resultado |
  | ----- | ----- | ----- |
  | 1899900 | 1899899 | Rechazo: `"El precio anterior debe ser mayor que el precio efectivo."` |
  | 1899900 | 1899900 | Rechazo (mismo mensaje) |
  | 1899900 | 1899901 | Guardada |
  | 1899900 | (vacío) | Guardada, anterior nulo |

### QA-05: Precio anterior inconsistente en captura automática

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-04
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 1899900 | vigente |
  | 1799900 | "Antes" |

- **Resultado esperado:** observación guardada con `precio_efectivo = 1899900` y `precio_anterior` nulo; advertencia `precio_anterior_inconsistente` con URL, 1899900 y 1799900.

### QA-06: Solo precio anterior

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-03
- **Pasos:**
  1. Procesar una página de producto agotado que solo muestra "Antes $ 2.499.900".
  2. Registrar OBS-M sin `precio_efectivo` y con `precio_anterior = 2499900`.
- **Resultado esperado:** paso 1: sin observación, descarte `sin_precio_vigente` con la URL; paso 2: `"Campo obligatorio ausente: precio_efectivo."`

### QA-07: El precio anterior no se usa como referencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-05
- **Pasos:**
  1. Leer la observación de QA-01 desde la lectura que usa la comparación y desde la consulta administrativa.
- **Resultado esperado:** el valor de referencia entregado es 1739900; 4200000 se entrega solo con la etiqueta `"Precio anterior (solo evidencia)"`.

### QA-08: Precio condicionado no reemplaza al general

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-03
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 2099900 | precio vigente |
  | 1899900 | "Precio exclusivo con tarjeta de la tienda" |

- **Resultado esperado:** `precio_efectivo = 2099900`; `precio_anterior` nulo; 1899900 no ocupa ni el precio efectivo ni el anterior.

### QA-09: Interpretación de formatos de precio leídos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Precio leído | Resultado |
  | ----- | ----- |
  | "$ 1.739.900" | 1739900 |
  | "1739900.00" | 1739900, sin advertencia |
  | "1739900.60" | 1739901, advertencia `precio_con_decimales` |
  | "Consultar precio" (único precio) | Sin precio vigente: descarte `sin_precio_vigente` y advertencia `precio_no_interpretable` |

### QA-10: Etiquetas sin términos prohibidos

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Pasos:**
  1. Revisar las etiquetas y mensajes de esta HU.
- **Resultado esperado:** ningún texto contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

---

**Total de casos:** 10
