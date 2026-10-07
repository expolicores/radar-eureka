# Casos de Prueba — HU-051: Capturar observaciones de Alkosto desde su sitemap y datos estructurados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el conector de Alkosto contra un **servidor simulado** con `robots.txt`, sitemaps y páginas de producto que replican la estructura observada en D6: obtención de URLs candidatas, mapeo de datos estructurados a la observación, descartes específicos, evidencia y detección de cambio de estructura. Una prueba de humo opcional contra el sitio real se limita a 1 ejecución de bajo volumen en entorno de validación, con la captura habilitada por el PO.

Fuera de alcance: ritmo, volumen, User-Agent, reintentos y registro de ejecución (HU-050) y suspensión (HU-053).

## Precondiciones y Datos Base

- **Usuario:** `admin.po@prueba.local` (Administrador).
- **Servidor simulado** `https://alkosto-simulado.prueba.local`: `robots.txt` con `Disallow: /search/`, `Disallow: /*?q=` y `Sitemap: https://alkosto-simulado.prueba.local/sitemap.xml`; índice con 2 sitemaps de producto (50 URLs, 10 cumplen el patrón de televisores).
- **Patrón de URL de televisores de prueba:** `/televisor-`.
- **Página base (PG-BASE):** JSON-LD Product: name "Televisor SAMSUNG 55 Pulgadas LED Uhd4K Smart TV UN55DU7000KXZL", brand "SAMSUNG", sku "8806095520005", offers {price 1899900, priceCurrency COP, availability InStock}, sin seller.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04 / RN-05 / RN-07 | QA-01 |
| Escenario 2 / RN-01 / RN-02 / RN-03 | QA-02, QA-03 |
| Escenario 3 / RN-03 | QA-04 |
| Escenario 4 / RN-04 | QA-05 |
| Escenario 5 / RN-04 (regla de modelo) | QA-06 |
| Escenario 6 / RN-04 | QA-07 |
| Escenario 7 / RN-04 | QA-08 |
| Escenario 8 / RN-04 | QA-09 |
| RN-04 (características desde el nombre) | QA-10 |
| Escenario 9 / RN-06 | QA-11 |
| Escenario 10 | QA-12 |

---

## Casos de Prueba

### QA-01: Mapeo completo de una página de Alkosto

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-04, RN-05, RN-07
- **Pasos:**
  1. Ejecutar una captura con PG-BASE como única página candidata.
- **Resultado esperado:** observación con descripción = name, marca SAMSUNG, modelo UN55DU7000KXZL, sku y EAN 8806095520005, tamaño 55, 4K UHD, LED, smart sí, vendedor "Alkosto" (`vendedor_origen = implicito`), `precio_efectivo = 1899900`, `iva_condicion = indeterminado`, `metodo_adquisicion = sitemap_datos_estructurados`, `registrado_por = conector:Alkosto`; evidencia con el bloque JSON-LD textual, URL, fecha y hora, código 200 y hash.

### QA-02: URLs candidatas desde el sitemap

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01, RN-03
- **Pasos:**
  1. Ejecutar la captura con el servidor simulado completo; una URL de televisor aparece en ambos sitemaps.
- **Resultado esperado:** se solicitan `robots.txt`, el índice, los 2 sitemaps y solo las 10 páginas de televisor (la repetida, una vez); ninguna solicitud a `/search/` ni con `?q=`.

### QA-03: Origen de los sitemaps

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | robots.txt | URL de índice configurada | Resultado |
  | ----- | ----- | ----- |
  | con `Sitemap:` | otra URL | se usa la de `robots.txt` |
  | sin `Sitemap:` | https://alkosto-simulado.prueba.local/sitemap.xml | se usa la configurada |
  | sin `Sitemap:` | vacía | ejecución `fallida`, motivo `"Sin sitemap de productos para Alkosto"` |

### QA-04: Habilitar sin patrón o con patrón inválido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Patrón | Resultado |
  | ----- | ----- |
  | (vacío) | `"Configure el patrón de URL de televisores de Alkosto antes de habilitar la captura."` |
  | `[televisor` (expresión mal formada) | `"El patrón de URL no es válido."` |
  | `/televisor-` | Habilitación permitida |

### QA-05: Modelo desde `model` o `mpn`

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-04
- **Datos de prueba:**

  | Datos estructurados | Modelo esperado |
  | ----- | ----- |
  | `model = "55UT8050PSA"` y name con otro código | 55UT8050PSA |
  | sin `model`, `mpn = "QN65Q60DAKXZL"` | QN65Q60DAKXZL |

### QA-06: Extracción del modelo desde el nombre

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Datos de prueba:**

  | name (sin model ni mpn) | Resultado |
  | ----- | ----- |
  | "Televisor SAMSUNG 55 Pulgadas LED Uhd4K Smart TV UN55DU7000KXZL" | UN55DU7000KXZL |
  | "Televisor LG 65 Pulgadas 65UT8050PSA 4K Smart" | 65UT8050PSA |
  | "Televisor KALLEY 32 Pulgadas HD Smart" | descarte `modelo_no_identificable` |
  | "Televisor TCL 50 Pulgadas 3840X2160 UHD4K" | descarte `modelo_no_identificable` (medida y resolución excluidas) |
  | "Televisor HISENSE 43A4K 43A4KV" | 43A4KV (el más largo) |

### QA-07: Producto agotado

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-04
- **Datos de prueba:**

  | availability | Resultado |
  | ----- | ----- |
  | OutOfStock | descarte `no_disponible` |
  | Discontinued | descarte `no_disponible` |
  | PreOrder | se procesa |
  | (ausente) | se procesa |

### QA-08: Moneda o precio inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-04
- **Datos de prueba:**

  | offers | Resultado |
  | ----- | ----- |
  | priceCurrency USD | descarte `moneda_no_cop` |
  | sin price | descarte `sin_precio_vigente` |
  | AggregateOffer con lowPrice 1799900 | precio vigente 1799900 |

### QA-09: SKU que no es GTIN

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 8, RN-04
- **Datos de prueba:**

  | sku | gtin13 | Resultado |
  | ----- | ----- | ----- |
  | ALK-998877 | (ausente) | sku ALK-998877, EAN nulo |
  | 8806095520001 (control inválido) | (ausente) | EAN nulo |
  | ALK-998877 | 8806095520005 | EAN 8806095520005 |

### QA-10: Características desde el nombre

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | name | Tamaño | Resolución | Tecnología | Smart |
  | ----- | ----- | ----- | ----- | ----- |
  | "Televisor LG 65\" OLED 4K Smart OLED65C4PSA" | 65 | 4K UHD | OLED | sí |
  | "Televisor TCL 55 pulg QLED UHD 55C655K" | 55 | 4K UHD | QLED | desconocido |
  | "Televisor SAMSUNG 98 Pulgadas Mini LED 8K QN98QN990F" | 98 | 8K | Mini LED | desconocido |
  | "Televisor CHALLENGER 24 Pulgadas HD 24T3000" | 24 | HD | desconocida | desconocido |
  | "Televisor XYZ 150 Pulgadas ABC12345" | nulo (fuera de 10–120) | desconocida | desconocida | desconocido |

### QA-11: Página sin datos estructurados y cambio de estructura

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-06
- **Datos de prueba:**

  | Páginas de televisor sin datos estructurados (de 10) | Resultado |
  | ----- | ----- |
  | 1 | descarte `datos_estructurados_ausentes` para esa página; ejecución `completada` |
  | 5 | ejecución `completada` |
  | 6 | ejecución `fallida`, motivo `"posible cambio de estructura en Alkosto"`, evento `captura_fallida`; observaciones ya creadas se conservan |

### QA-12: Vendedor publicado distinto de la tienda

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Datos de prueba:**

  | offers.seller.name | Resultado |
  | ----- | ----- |
  | Proveedor Externo SAS | descarte `vendedor_tercero` |
  | Alkosto | observación con `vendedor_origen = publicado` |

---

**Total de casos:** 12
