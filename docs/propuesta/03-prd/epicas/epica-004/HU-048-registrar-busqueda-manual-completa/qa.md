# Casos de Prueba — HU-048: Registrar una búsqueda manual con todas las ofertas comparables y sus términos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el registro atómico de una búsqueda manual: encabezado, ofertas comparables, ofertas descartadas, conteos, búsqueda sin ofertas, duplicados, doble envío, vínculo de las observaciones con su búsqueda, consulta, evento auditable y permisos.

Fuera de alcance: validaciones individuales ya probadas en la carga manual individual (HU-047), salvo su propagación con prefijo de oferta.

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Fecha de referencia:** 2026-10-02T12:00-05:00. Antigüedad máxima manual: 7 días.
- **Encabezado base (B-BASE):** fuente Alkosto; producto buscado "Samsung 55 UN55DU7000"; términos ["televisor samsung 55 4k", "UN55DU7000"]; fecha 2026-10-02T11:00; resultados revisados 12; evidencia `resultados-alkosto.png` (800 KB); declaración marcada.
- **Ofertas comparables base:**

  | # | Modelo | Vendedor | Precio | URL |
  | ----- | ----- | ----- | ----- | ----- |
  | 1 | UN55DU7000KXZL | Alkosto | 1899900 | https://www.alkosto.com/tv-samsung-55-du7000/p/0000000000001 |
  | 2 | UN55DU8000KXZL | Alkosto | 2299900 | https://www.alkosto.com/tv-samsung-55-du8000/p/0000000000002 |
  | 3 | UN55CU7000KXZL | Alkosto | 1749900 | https://www.alkosto.com/tv-samsung-55-cu7000/p/0000000000003 |

  Todas con marca Samsung, condición ninguna, IVA indeterminado, evidencia PNG válida y declaración de precio por unidad.
- **Oferta descartada base:** URL https://www.alkosto.com/combo-tv-soporte/p/0000000000009, vendedor Alkosto, precio 2099900, motivo `no_comparable`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-05 / RN-07 | QA-01 |
| Escenario 2 / RN-02 / RN-05 | QA-02 |
| Escenario 3 | QA-03 |
| Escenario 4 / RN-01 | QA-04 |
| RN-01 (límites del encabezado) | QA-05 |
| Escenario 5 / RN-04 | QA-06 |
| Escenario 6 / RN-03 | QA-07, QA-08 |
| Escenario 7 / RN-06 | QA-09 |
| Escenario 8 / RN-08 | QA-10 |
| RN-08 (anulación de una observación de la búsqueda) | QA-11 |
| Escenario 9 / RN-06 | QA-12 |
| RN-09 | QA-13 |
| RN-10 | QA-14 |
| Escenario 10 | QA-15 |

---

## Casos de Prueba

### QA-01: Búsqueda con tres ofertas comparables y una descartada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-05, RN-07
- **Pasos:**
  1. Enviar B-BASE con las 3 ofertas comparables base y la oferta descartada base.
- **Resultado esperado:** `"Búsqueda registrada: {id_busqueda}. Observaciones creadas: 3. Ofertas descartadas: 1."`; 3 observaciones con `canal_carga = busqueda`, `protocolo_busqueda = registrado`, `id_contexto = id_busqueda`, `fecha_observacion = 2026-10-02T11:00`, `registrado_por = admin.po@prueba.local`, `etiqueta_origen = "Observación manual"`; la oferta descartada queda guardada con su motivo y sin observación.

### QA-02: Una oferta inválida rechaza todo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02, RN-05
- **Datos de prueba:**

  | Oferta | Problema |
  | ----- | ----- |
  | 3 | sin evidencia |
  | 2 | precio anterior 2199900 (menor que el efectivo 2299900) |

- **Resultado esperado:** no se guarda búsqueda ni observaciones; se devuelven `"Oferta 2: El precio anterior debe ser mayor que el precio efectivo."` y `"Oferta 3: La observación requiere al menos una evidencia."`

### QA-03: Búsqueda sin ofertas comparables

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | fuente | Falabella |
  | producto buscado | LG OLED77C4PSA |
  | resultados revisados | 5 |
  | ofertas | ninguna |

- **Resultado esperado:** búsqueda guardada con resultado "sin ofertas comparables"; `"Búsqueda registrada: {id}. Observaciones creadas: 0. Ofertas descartadas: 0."`

### QA-04: Encabezado incompleto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-01
- **Datos de prueba:**

  | Cambio sobre B-BASE | Mensaje esperado |
  | ----- | ----- |
  | términos vacíos | `"Registre al menos un término de búsqueda."` |
  | sin evidencia de resultados | `"Adjunte la evidencia de la página de resultados."` |
  | declaración sin marcar | `"Confirme que registró todas las ofertas comparables encontradas."` |
  | producto buscado "TV" | `"Indique el producto buscado (3 a 200 caracteres)."` |
  | fuente Éxito (deshabilitada) | `"La fuente Éxito no está habilitada para el método manual."` |

### QA-05: Límites del encabezado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Campo | Valor | Resultado |
  | ----- | ----- | ----- |
  | términos | 10 términos válidos | Aceptado |
  | términos | 11 términos | `"Cada término debe tener entre 2 y 200 caracteres (máximo 10 términos)."` |
  | términos | ["x"] | mismo mensaje |
  | resultados revisados | 1001 | `"Resultados revisados debe ser un entero entre 0 y 1.000."` |
  | resultados revisados | -1 | mismo mensaje |
  | fecha | 2026-09-25T11:59 | `"La fecha de la búsqueda no puede tener más de 7 días de antigüedad."` |
  | fecha | 2026-10-02T12:30 | `"La fecha de la búsqueda no puede ser futura."` |
  | nota | 1.001 caracteres | `"La nota admite máximo 1.000 caracteres."` |

### QA-06: Conteos inconsistentes

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Datos de prueba:**

  | Resultados revisados | Comparables | Descartadas | Resultado |
  | ----- | ----- | ----- | ----- |
  | 2 | 2 | 1 | `"El número de ofertas registradas (3) no puede superar el total de resultados revisados (2)."` |
  | 3 | 2 | 1 | Aceptada |
  | 0 | 0 | 0 | Aceptada |

### QA-07: Vendedor tercero como descartada y como comparable

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-03
- **Datos de prueba:**

  | Variante | Registro de "ElectroMundo Store" (Falabella, precio 1950000) | Resultado |
  | ----- | ----- | ----- |
  | A | Oferta descartada, motivo `vendedor_tercero` | Búsqueda guardada; sin observación para esa oferta |
  | B | Oferta comparable en posición 2 | Rechazo: `"Oferta 2: Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: ElectroMundo Store."` |

### QA-08: Oferta descartada sin motivo o con motivo "otro" sin detalle

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Oferta descartada 1 | Resultado |
  | ----- | ----- |
  | sin motivo | `"Oferta descartada 1: indique el motivo de descarte."` |
  | motivo `otro`, detalle vacío | `"Oferta descartada 1: describa el motivo (3 a 300 caracteres)."` |
  | motivo `sin_precio_visible`, sin precio | Aceptada |

### QA-09: URL repetida en la búsqueda

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-06
- **Pasos:**
  1. Enviar B-BASE con las ofertas 1 y 2 usando ambas la URL de la oferta 1.
- **Resultado esperado:** `"Oferta 2: Observación duplicada en la búsqueda: https://www.alkosto.com/tv-samsung-55-du7000/p/0000000000001."`; nada se guarda.

### QA-10: La observación expone su búsqueda

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-08
- **Pasos:**
  1. Leer una observación de QA-01 desde la lectura de comparación.
- **Resultado esperado:** incluye `etiqueta_origen = "Observación manual"`, `protocolo_busqueda = registrado`, `id_busqueda`, términos ["televisor samsung 55 4k", "UN55DU7000"], 3 comparables y 1 descartada.

### QA-11: Anulación de una observación de la búsqueda

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Pasos:**
  1. Anular la observación de la oferta 2 de QA-01.
  2. Consultar la búsqueda.
- **Resultado esperado:** la búsqueda sigue con 3 observaciones vinculadas; la de la oferta 2 aparece como anulada; encabezado y descartadas sin cambios.

### QA-12: Doble envío de la búsqueda

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-06
- **Pasos:**
  1. Enviar de nuevo, 2 minutos después, exactamente lo de QA-01.
- **Resultado esperado:** `"Esta búsqueda ya fue registrada hace menos de 10 minutos ({id_busqueda})."`; el número de búsquedas y observaciones no cambia.

### QA-13: Consulta y listado de búsquedas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Datos de prueba:**

  | Consulta | Resultado esperado |
  | ----- | ----- |
  | por `id_busqueda` de QA-01 | encabezado, evidencia, 1 descartada, 3 observaciones con estado |
  | listado Alkosto, 2026-10-01 a 2026-10-02 | búsqueda de QA-01, orden por fecha descendente |
  | listado Alkosto, 2026-09-01 a 2026-09-02 | `"No hay búsquedas manuales para los filtros indicados."` |

### QA-14: Evento auditable de la búsqueda

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Resultado esperado:** tras QA-01 existe el evento `carga_manual_busqueda` con usuario, fecha y hora, `id_busqueda` y 3 observaciones creadas; QA-02 no generó evento.

### QA-15: Analista no registra búsquedas

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10
- **Resultado esperado:** como `analista1@prueba.local`, enviar B-BASE devuelve `"Operación permitida solo para el rol Administrador."`

---

**Total de casos:** 15
