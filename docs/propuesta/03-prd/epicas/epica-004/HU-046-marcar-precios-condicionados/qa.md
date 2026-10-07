# Casos de Prueba — HU-046: Identificar y marcar precios sujetos a condiciones especiales

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el registro manual de la condición especial, la detección automática por mapeo del conector y por palabras clave, la convivencia de precios generales y condicionados, el caso de solo precio condicionado, varias condiciones, la limitación de la detección al rótulo del precio, la configuración de palabras clave y los permisos.

Fuera de alcance: la selección del precio efectivo entre varios precios generales (HU-045).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Palabras clave:** configuración inicial de RN-03.
- **Observación manual base (OBS-M):** Falabella, "Televisor LG 65 pulgadas UHD 4K Smart", LG, 65UT8050PSA, vendedor Falabella, precio 2099900, URL https://www.falabella.com.co/falabella-co/product/00000001/tv-lg-65, fecha 2026-10-02T09:30, IVA indeterminado, evidencia captura.png, método manual, canal individual.
- **Ejecución de captura de prueba:** `EJEC-PRUEBA-FAL-02` con páginas simuladas de Falabella (vendedor Falabella).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02 | QA-01 |
| Escenario 2 / RN-02 / RN-06 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-03 / RN-04 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-05 | QA-06 |
| Escenario 7 / RN-03 | QA-07 |
| RN-03 (palabras clave por tipo, mayúsculas y tildes) | QA-08 |
| Escenario 8 / RN-07 | QA-09, QA-10 |
| Escenario 9 | QA-11 |

---

## Casos de Prueba

### QA-01: Precio general en carga manual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02
- **Pasos:**
  1. Enviar OBS-M con `condicion_especial = ninguna`.
- **Resultado esperado:** guardada con `apta_para_referencia = sí` y detalle vacío.

### QA-02: Precio condicionado en carga manual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02, RN-06
- **Datos de prueba:**

  | condicion_especial | detalle | Marca esperada |
  | ----- | ----- | ----- |
  | membresia | "Precio para afiliados del programa de fidelización" | `"Precio sujeto a condición especial: membresía"` |
  | financiacion | "Precio aplicando crédito de la tienda a 24 meses" | `"Precio sujeto a condición especial: financiación"` |

- **Resultado esperado:** ambas guardadas con `apta_para_referencia = no` y la marca indicada.

### QA-03: Condición ausente o sin detalle

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | condicion_especial | detalle | Mensaje esperado |
  | ----- | ----- | ----- |
  | (vacío) | — | `"Campo obligatorio ausente: condicion_especial."` |
  | cupon | (vacío) | `"Describa la condición especial (3 a 300 caracteres)."` |
  | cupon | "Ok" (2 caracteres) | mismo mensaje |
  | descuento | — | `"condicion_especial no es un valor permitido."` |

### QA-04: Precio general y precio CMR en captura

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03, RN-04
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 2099900 | precio vigente |
  | 1899900 | "Precio CMR" (campo mapeado por el conector) |

- **Resultado esperado:** `precio_efectivo = 2099900`, `condicion_especial = ninguna`, `apta_para_referencia = sí`; `precios_condicionados_evidencia` = [{1899900, `tarjeta_especifica`, "Precio CMR"}].

### QA-05: Solo precio con cupón

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-05
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 1649900 | "Con cupón TVFEST" |

- **Resultado esperado:** observación con `precio_efectivo = 1649900`, `condicion_especial = cupon`, detalle "Con cupón TVFEST", `apta_para_referencia = no`.

### QA-06: Varias condiciones en el único precio

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-05
- **Datos de prueba:**

  | Precio | Rótulo |
  | ----- | ----- |
  | 1599900 | "Con tarjeta de la tienda y cupón" |

- **Resultado esperado:** `condicion_especial = otra`, detalle `"tarjeta_especifica, cupon: Con tarjeta de la tienda y cupón"`, `apta_para_referencia = no`.

### QA-07: Texto de financiación fuera del rótulo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-03
- **Datos de prueba:**

  | Elemento | Texto |
  | ----- | ----- |
  | rótulo del precio 1899900 | "Precio" |
  | banner de la página | "Paga hasta en 12 cuotas" |

- **Resultado esperado:** `condicion_especial = ninguna`, `apta_para_referencia = sí`.

### QA-08: Detección por palabras clave sin distinguir mayúsculas ni tildes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Rótulo del único precio | Tipo esperado |
  | ----- | ----- |
  | "PRECIO CON TARJETA" | tarjeta_especifica |
  | "Usa tu codigo promocional" | cupon |
  | "Precio a cuotas" | financiacion |
  | "Exclusivo SOCIO" | membresia |
  | "Precio Internet" | ninguna |

### QA-09: Cambio de palabras clave no retroactivo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Pasos:**
  1. Capturar una página con único precio rotulado "Precio Puntos Colombia" (queda `ninguna`).
  2. Agregar "Puntos Colombia" al tipo `membresia`.
  3. Capturar de nuevo la misma página en otra ejecución.
- **Resultado esperado:** la observación del paso 1 no cambia; la del paso 3 queda `membresia` y `apta_para_referencia = no`; existe un evento con usuario, fecha y hora, lista anterior y nueva.

### QA-10: Límites de la lista de palabras clave

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Datos de prueba:**

  | Acción | Resultado |
  | ----- | ----- |
  | Agregar "CUPÓN" al tipo cupon | `"La palabra clave CUPÓN ya existe en el tipo cupon."` |
  | Tipo con 30 frases | Aceptado |
  | Tipo con 31 frases | `"Cada tipo admite hasta 30 palabras clave de 2 a 60 caracteres."` |
  | Frase "x" (1 carácter) | mismo mensaje |

### QA-11: Analista no modifica palabras clave

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9
- **Resultado esperado:** como `analista1@prueba.local`, agregar una palabra clave se rechaza con `"Operación permitida solo para el rol Administrador."`

---

**Total de casos:** 11
