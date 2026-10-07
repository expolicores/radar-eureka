# Casos de Prueba — HU-044: Aceptar solo observaciones cuyo vendedor sea directamente la tienda

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la regla de vendedor = la tienda en canales manuales y en captura automática: comparación normalizada de nombres, vendedor ausente con y sin vendedor implícito, varias ofertas en una página, registro de descartes, fuente sin vendedores, cambios de configuración no retroactivos y permisos.

Fuera de alcance: elección del precio entre ofertas de la propia tienda (HU-045) y el funcionamiento de los conectores (HU-051, HU-052).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Catálogo:** Alkosto (vendedores ["Alkosto"], implícito = sí), Falabella (["Falabella"], implícito = no), Mercado Libre (sin vendedores, carga manual habilitada para la prueba).
- **Observación manual base (OBS-M):** Falabella, "Televisor LG 65 pulgadas UHD 4K Smart", LG, 65UT8050PSA, precio 2099900 COP, URL https://www.falabella.com.co/falabella-co/product/00000001/tv-lg-65, fecha 2026-10-02T09:30, IVA indeterminado, evidencia captura-falabella-lg65.png, método manual, canal individual.
- **Ejecución de captura de prueba:** `EJEC-PRUEBA-FAL-01` (Falabella) y `EJEC-PRUEBA-ALK-01` (Alkosto), con captura habilitada en entorno de prueba.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-02 | QA-01, QA-02 |
| Escenario 2 / RN-06 | QA-03 |
| Escenario 3 / RN-05 | QA-04 |
| Escenario 4 / RN-04 | QA-05, QA-06 |
| Escenario 5 / RN-03 | QA-07 |
| Escenario 6 / RN-03 | QA-08 |
| RN-03 (vendedor vacío en canal manual) | QA-09 |
| Escenario 7 / RN-08 | QA-10 |
| Escenario 8 / RN-07 | QA-11 |
| Escenario 9 | QA-12 |
| RN-08 (límites de la lista) | QA-13 |

---

## Casos de Prueba

### QA-01: Aceptar vendedor igual a la tienda con variaciones de forma

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02
- **Datos de prueba:**

  | vendedor enviado | Resultado |
  | ----- | ----- |
  | " FALABELLA " | Guardada, `vendedor = "FALABELLA"`, `vendedor_es_tienda = sí`, `vendedor_origen = publicado` |
  | "falabella" | Guardada |
  | "Falabélla" | Guardada (se ignoran tildes) |

- **Pasos:**
  1. Enviar OBS-M con cada valor de `vendedor`.

### QA-02: No hay coincidencia parcial

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Datos de prueba:**

  | vendedor enviado |
  | ----- |
  | "Falabella Outlet Tercero SAS" |
  | "Falabela" |

- **Resultado esperado:** ambas se rechazan con `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: {vendedor}."`

### QA-03: Rechazo de tercero en carga manual

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-06
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | vendedor | TecnoImport SAS |

- **Resultado esperado:** no se guarda; mensaje `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: TecnoImport SAS."`

### QA-04: Descarte de tercero en captura automática

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-05
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | URL | https://www.falabella.com.co/falabella-co/product/00000002/tv-tcl-55 |
  | vendedor publicado | ElectroMundo Store |

- **Pasos:**
  1. Procesar la página en `EJEC-PRUEBA-FAL-01`.
- **Resultado esperado:** no se crea observación; la ejecución registra un descarte con URL, vendedor "ElectroMundo Store", motivo `vendedor_tercero`, fecha y hora; el contador "descartadas por vendedor tercero" = 1.

### QA-05: Varias ofertas, una de la tienda

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Datos de prueba:**

  | Oferta | Vendedor | Precio |
  | ----- | ----- | ----- |
  | 1 | Falabella | 2099900 |
  | 2 | ElectroMundo Store | 1950000 |

- **Resultado esperado:** se crea una observación con `vendedor = "Falabella"` y `precio_efectivo = 2099900`; el valor 1950000 no aparece en ningún campo de la observación; se registra un descarte `vendedor_tercero` para la oferta 2.

### QA-06: Varias ofertas, ninguna de la tienda

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Oferta | Vendedor | Precio |
  | ----- | ----- | ----- |
  | 1 | ElectroMundo Store | 1950000 |
  | 2 | Mundo TV Ltda | 1990000 |

- **Resultado esperado:** no se crea observación; se registra un descarte `vendedor_tercero` por la página.

### QA-07: Vendedor implícito en Alkosto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-03
- **Pasos:**
  1. Procesar en `EJEC-PRUEBA-ALK-01` una página de Alkosto sin vendedor publicado.
- **Resultado esperado:** observación guardada con `vendedor = "Alkosto"`, `vendedor_es_tienda = sí`, `vendedor_origen = implicito`.

### QA-08: Vendedor no identificable en Falabella

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-03
- **Pasos:**
  1. Procesar en `EJEC-PRUEBA-FAL-01` una página de Falabella sin vendedor publicado.
- **Resultado esperado:** no se crea observación; descarte con motivo `vendedor_no_identificable` y la URL; contador "descartadas por vendedor no identificable" = 1.

### QA-09: Vendedor vacío en carga manual

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Datos de prueba:**

  | Fuente | vendedor |
  | ----- | ----- |
  | Falabella | (vacío) |
  | Alkosto (implícito = sí) | (vacío) |

- **Resultado esperado:** con Falabella se rechaza con `"Campo obligatorio ausente: vendedor."`; con Alkosto se guarda con `vendedor = "Alkosto"` y `vendedor_origen = implicito`.

### QA-10: Cambio de lista no retroactivo y auditado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-08
- **Pasos:**
  1. Guardar OBS-M con `vendedor = "Falabella"`.
  2. Agregar "falabella.com" a la lista de Falabella.
  3. Enviar OBS-M con `vendedor = "falabella.com"`.
- **Resultado esperado:** la observación del paso 1 no cambia; la del paso 3 se acepta; existe un evento `cambio_catalogo_fuente` con usuario, fecha y hora, lista anterior ["Falabella"] y nueva ["Falabella", "falabella.com"].

### QA-11: Fuente sin vendedores configurados

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Pasos:**
  1. Enviar una observación manual de Mercado Libre con vendedor "Mercado Libre".
- **Resultado esperado:** `"La fuente Mercado Libre no tiene vendedores aceptados configurados; no se pueden registrar observaciones."`

### QA-12: Analista no modifica la configuración de vendedores

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9
- **Pasos:**
  1. Como `analista1@prueba.local`, agregar "falabella.com" a Falabella y cambiar el implícito de Alkosto a "no".
- **Resultado esperado:** ambas se rechazan con `"Operación permitida solo para el rol Administrador."`; la configuración no cambia.

### QA-13: Límites de la lista de vendedores aceptados

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Datos de prueba:**

  | Acción | Resultado |
  | ----- | ----- |
  | Agregar "FALABELLA" a la lista ["Falabella"] | `"El vendedor FALABELLA ya está en la lista de la fuente Falabella."` |
  | Lista con 10 nombres distintos | Aceptada |
  | Lista con 11 nombres | `"La lista de vendedores aceptados admite de 1 a 10 nombres."` |
  | Nombre "F" (1 carácter) | `"Cada nombre de vendedor debe tener entre 2 y 100 caracteres."` |

---

**Total de casos:** 13
