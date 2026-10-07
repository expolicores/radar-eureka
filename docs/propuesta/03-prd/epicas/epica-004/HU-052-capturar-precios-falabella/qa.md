# Casos de Prueba — HU-052: Capturar observaciones de Falabella con vendedor = Falabella desde sitemaps y datos estructurados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el conector de Falabella contra un **servidor simulado** con la estructura observada en D6 (índice de sitemaps con varios archivos, páginas con varias ofertas y vendedores): filtro de vendedor, precios general, normal y CMR, reutilización de sitemaps por `lastmod`, mapeo de campos, descartes, evidencia y detección de cambio de estructura.

Fuera de alcance: ritmo, volumen, User-Agent, reintentos y registro de ejecución (HU-050); suspensión (HU-053).

## Precondiciones y Datos Base

- **Usuario:** `admin.po@prueba.local` (Administrador).
- **Servidor simulado** `https://falabella-simulado.prueba.local`: `robots.txt` que prohíbe carrito y cuenta y declara el índice de sitemaps; índice con 3 archivos (`pdp-1.xml`, `pdp-2.xml` con `lastmod`, `pdp-3.xml` sin `lastmod`).
- **Patrón de URL de televisores de prueba:** `/tv-`.
- **Página base (PG-FAL):** Product name "Televisor LG 65 pulgadas UHD 4K Smart TV 65UT8050PSA", brand "LG", sku "123456789"; oferta seller "Falabella", price 2099900, priceCurrency COP, availability InStock; precio normal 2499900.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04 / RN-06 / RN-08 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / RN-04 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-05 | QA-06 |
| Escenario 7 / RN-02 | QA-07 |
| RN-02 (origen de sitemaps) | QA-08 |
| Escenario 8 / RN-03 | QA-09 |
| Escenario 9 / RN-04 | QA-10 |
| RN-04 (EAN y modelo) | QA-11 |
| Escenario 10 / RN-07 | QA-12 |
| RN-01 | QA-13 |

---

## Casos de Prueba

### QA-01: Página vendida por Falabella con precio normal

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-04, RN-06, RN-08
- **Pasos:**
  1. Ejecutar la captura con PG-FAL como única candidata.
- **Resultado esperado:** observación con marca LG, modelo 65UT8050PSA, sku 123456789, EAN nulo, tamaño 65, 4K UHD, smart sí, vendedor Falabella, `precio_efectivo = 2099900`, `precio_anterior = 2499900`, condición ninguna, `iva_condicion = indeterminado`, `registrado_por = conector:Falabella`; evidencia con el bloque completo, URL, fecha y hora, código 200 y hash.

### QA-02: Oferta única de tercero

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-04
- **Datos de prueba:**

  | seller | price |
  | ----- | ----- |
  | ElectroMundo Store | 1950000 |

- **Resultado esperado:** sin observación; descarte `vendedor_tercero` con "ElectroMundo Store" y la URL.

### QA-03: Varias ofertas con vendedores distintos

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-04
- **Datos de prueba:**

  | Oferta | seller | price |
  | ----- | ----- | ----- |
  | 1 | ElectroMundo Store | 1950000 |
  | 2 | Falabella | 2099900 |

- **Resultado esperado:** observación con `precio_efectivo = 2099900` y vendedor Falabella; 1950000 no aparece en la observación (solo en la evidencia textual del bloque); descarte `vendedor_tercero` por la oferta 1.

### QA-04: Oferta sin vendedor

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-04
- **Resultado esperado:** PG-FAL sin `seller` produce el descarte `vendedor_no_identificable`; sin observación.

### QA-05: Precio CMR junto al general

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-05
- **Datos de prueba:**

  | Precio de la oferta de Falabella | Rótulo |
  | ----- | ----- |
  | 2099900 | precio internet |
  | 1899900 | "Precio CMR" |

- **Resultado esperado:** `precio_efectivo = 2099900`, condición ninguna, `apta_para_referencia = sí`, `precios_condicionados_evidencia` = [{1899900, `tarjeta_especifica`, "Precio CMR"}].

### QA-06: Solo precio CMR

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-05
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 1899900 | CMR (sin texto de rótulo) |

- **Resultado esperado:** observación con `precio_efectivo = 1899900`, `condicion_especial = tarjeta_especifica`, detalle "Precio con tarjeta CMR", `apta_para_referencia = no`.

### QA-07: Reutilización de sitemaps por lastmod

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-02
- **Pasos:**
  1. Ejecutar una captura (descarga los 3 archivos).
  2. Cambiar en el índice solo el `lastmod` de `pdp-2.xml` y ejecutar de nuevo.
- **Resultado esperado:** en la segunda ejecución el servidor recibe solicitudes a `pdp-2.xml` y `pdp-3.xml` (sin `lastmod`), no a `pdp-1.xml`; las URLs de `pdp-1.xml` se toman de la lista guardada.

### QA-08: Origen de los sitemaps

- **Tipo:** Integración
- **Prioridad:** Baja
- **Cubre:** RN-02
- **Datos de prueba:**

  | robots.txt con `Sitemap:` | URL de índice configurada | Resultado |
  | ----- | ----- | ----- |
  | no | vacía | ejecución `fallida`, motivo `"Sin sitemap de productos para Falabella"` |
  | no | https://falabella-simulado.prueba.local/sitemap-index.xml | se usa la configurada |

### QA-09: Habilitar sin patrón

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-03
- **Datos de prueba:**

  | Patrón | Resultado |
  | ----- | ----- |
  | (vacío) | `"Configure el patrón de URL de televisores de Falabella antes de habilitar la captura."` |
  | `(tv-` | `"El patrón de URL no es válido."` |

### QA-10: Agotado, moneda y modelo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-04
- **Datos de prueba:**

  | Cambio sobre PG-FAL | Descarte esperado |
  | ----- | ----- |
  | availability OutOfStock | `no_disponible` |
  | priceCurrency USD | `moneda_no_cop` |
  | name "Televisor Kalley 32 pulgadas HD", sin model | `modelo_no_identificable` |

### QA-11: EAN y modelo en Falabella

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Datos | Resultado |
  | ----- | ----- |
  | sku "8806095520005", sin gtin | EAN nulo (el SKU no se usa como EAN) |
  | gtin13 "8806095520005" | EAN 8806095520005 |
  | model "65UT8050PSA" y name con otro código | modelo 65UT8050PSA |

### QA-12: Cambio de estructura

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-07
- **Datos de prueba:**

  | Páginas sin datos estructurados (de 10) | Resultado |
  | ----- | ----- |
  | 5 | `completada`, 5 descartes `datos_estructurados_ausentes` |
  | 6 | `fallida`, motivo `"posible cambio de estructura en Falabella"`, evento `captura_fallida` |

### QA-13: Solo rutas permitidas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-01
- **Pasos:**
  1. Revisar todas las solicitudes recibidas por el servidor simulado en QA-01 a QA-12.
- **Resultado esperado:** solo hay solicitudes a `robots.txt`, sitemaps y páginas que cumplen `/tv-`; ninguna a carrito, cuenta ni búsqueda.

---

**Total de casos:** 13
