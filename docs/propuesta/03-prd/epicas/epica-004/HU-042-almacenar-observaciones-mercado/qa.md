# Casos de Prueba — HU-042: Almacenar observaciones de precio de mercado con registro mínimo trazable

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la operación común de alta de observaciones en la base propia de mercado: validación campo a campo del registro mínimo, coherencia fuente–método–usuario, campos derivados (`es_manual`, `etiqueta_origen`, `apta_para_referencia`), catálogo de fuentes, evidencia con hash, independencia frente a la comparación, permisos y estado vacío.

Fuera de alcance: reglas de vendedor (HU-044), precio anterior (HU-045), detección de condiciones especiales (HU-046), canales de carga concretos (HU-047 a HU-049) y captura automática (HU-050 a HU-053).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Catálogo:** configuración inicial de RN-02 (Alkosto, Falabella, Éxito, Mercado Libre).
- **Observación base (OBS-BASE):**

  | Campo | Valor |
  | ----- | ----- |
  | fuente | Alkosto |
  | producto_descripcion | Televisor Samsung 55 pulgadas Crystal UHD 4K Smart |
  | marca | Samsung |
  | modelo_referencia | UN55DU7000KXZL |
  | ean_gtin | (vacío) |
  | vendedor | Alkosto |
  | precio_efectivo | 1899900 |
  | moneda | COP |
  | condicion_especial | ninguna |
  | tipo_referencia / referencia_origen | url / https://www.alkosto.com/televisor-samsung-55-un55du7000kxzl/p/0000000000001 |
  | fecha_observacion | 2026-10-02T10:00:00-05:00 |
  | iva_condicion | indeterminado |
  | evidencia | captura-alkosto-un55.png (450 KB) |
  | metodo_adquisicion / canal_carga | manual / individual |
  | registrado_por | admin.po@prueba.local |
  | protocolo_busqueda | no_registrado |

- Fecha y hora de ejecución de referencia: 2026-10-02T12:00:00-05:00.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03 / RN-05 / RN-06 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-03 | QA-03, QA-04, QA-05, QA-06 |
| Escenario 4 / RN-04 | QA-08 |
| Escenario 5 | QA-09 |
| Escenario 6 / RN-05 | QA-11 |
| Escenario 7 / RN-06 | QA-07 |
| Escenario 8 / RN-01 | QA-12 |
| Escenario 9 / RN-02 | QA-13 |
| Escenario 10 | QA-14 |
| Escenario 11 | QA-15 |
| RN-04 (coherencia de registrado_por) | QA-10 |
| RN-07 | QA-16 |
| RN-08 | QA-18 |
| RN-09 | QA-17 |

---

## Casos de Prueba

### QA-01: Guardar una observación manual completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-03, RN-05, RN-06
- **Pasos:**
  1. Como `admin.po@prueba.local`, enviar OBS-BASE a la operación de alta.
  2. Consultar la observación por el `id_observacion` devuelto.
- **Resultado esperado:** se devuelve un `id_observacion` único; la observación tiene `fecha_registro` = momento del servidor, `estado = vigente`, `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `apta_para_referencia = sí` y todos los campos enviados sin modificación (modelo `UN55DU7000KXZL` sin normalizar).

### QA-02: Rechazo por campos obligatorios ausentes, con un error por campo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-03
- **Datos de prueba:**

  | Variante | Cambio sobre OBS-BASE | Errores esperados |
  | ----- | ----- | ---- |
  | A | `modelo_referencia` vacío | `"Campo obligatorio ausente: modelo_referencia."` |
  | B | `marca` nulo y `vendedor` nulo | `"Campo obligatorio ausente: marca."`, `"Campo obligatorio ausente: vendedor."` (en ese orden) |
  | C | sin `evidencia` | `"La observación requiere al menos una evidencia."` |

- **Pasos:**
  1. Enviar cada variante.
- **Resultado esperado:** ninguna variante se guarda; se devuelven exactamente los errores indicados, en el orden de la tabla RN-03.

### QA-03: Valores límite del precio efectivo

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | precio_efectivo | Resultado |
  | ----- | ----- |
  | 0 | Rechazo: `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."` |
  | 1 | Guardada |
  | 999999999 | Guardada |
  | 1000000000 | Rechazo (mismo mensaje) |
  | 1899900.5 | Rechazo (mismo mensaje) |
  | -1899900 | Rechazo (mismo mensaje) |

- **Pasos:**
  1. Enviar OBS-BASE cambiando solo `precio_efectivo` por cada valor.
- **Resultado esperado:** según la tabla.

### QA-04: Rechazo por formatos inválidos en otros campos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Campo | Valor | Mensaje esperado |
  | ----- | ----- | ---- |
  | moneda | USD | `"Solo se aceptan precios en COP."` |
  | fecha_observacion | 2026-10-03T08:00:00-05:00 | `"La fecha de observación no puede ser futura."` |
  | ean_gtin | 8806095520001 (dígito de control erróneo) | `"ean_gtin no es un GTIN válido."` |
  | ean_gtin | 88060955 2000 (con espacio) | `"ean_gtin no es un GTIN válido."` |
  | referencia_origen (url) | ftp://alkosto.com/tv | `"referencia_origen no es una URL http/https válida."` |
  | tamano_pulgadas | 9.9 | `"tamano_pulgadas debe estar entre 10 y 120."` |
  | tamano_pulgadas | 120.1 | `"tamano_pulgadas debe estar entre 10 y 120."` |
  | resolucion | 1080p | `"resolucion no es un valor permitido."` |
  | producto_descripcion | "TV" (2 caracteres) | `"producto_descripcion debe tener entre 3 y 300 caracteres."` |
  | modelo_referencia | texto de 61 caracteres | `"modelo_referencia debe tener entre 2 y 60 caracteres."` |
  | iva_condicion | con IVA | `"iva_condicion no es un valor permitido."` |
  | metodo_adquisicion | scraping | `"metodo_adquisicion no es un valor permitido."` |

- **Pasos:**
  1. Enviar OBS-BASE cambiando solo el campo indicado.
- **Resultado esperado:** la observación no se guarda y se devuelve el mensaje indicado.

### QA-05: Campos opcionales en límite o vacíos se aceptan

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | ean_gtin | 8806095520005 (13 dígitos, control válido) |
  | tamano_pulgadas | 10 y luego 120 |
  | sku | (vacío) |
  | iva_condicion | indeterminado |

- **Pasos:**
  1. Enviar OBS-BASE con cada valor.
- **Resultado esperado:** todas se guardan; los campos opcionales vacíos quedan nulos; `iva_condicion` queda `indeterminado` sin inferir otro valor.

### QA-06: Referencia de texto solo en observaciones manuales

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Variante | metodo / registrado_por | tipo_referencia / referencia_origen | Resultado |
  | ----- | ----- | ----- | ---- |
  | A | manual / admin.po@prueba.local | texto / "Catálogo impreso Alkosto, octubre 2026, pág. 4" | Guardada |
  | B | sitemap_datos_estructurados / conector:Alkosto (captura habilitada) | texto / "Catálogo impreso" | Rechazo: `"La referencia de texto solo se admite en observaciones manuales."` |
  | C | manual / admin.po@prueba.local | texto / "Ver" (3 caracteres) | Rechazo por longitud |

- **Resultado esperado:** según la tabla.

### QA-07: Condición especial exige detalle y deja la observación no apta

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-03, RN-06
- **Datos de prueba:**

  | Variante | condicion_especial | condicion_especial_detalle | Resultado |
  | ----- | ----- | ----- | ---- |
  | A | tarjeta_especifica | "Precio exclusivo con tarjeta de crédito de la tienda" | Guardada, `apta_para_referencia = no` |
  | B | cupon | (vacío) | Rechazo: `"Describa la condición especial (3 a 300 caracteres)."` |
  | C | ninguna | (vacío) | Guardada, `apta_para_referencia = sí` |

- **Resultado esperado:** según la tabla; la variante A queda con `estado = vigente`.

### QA-08: Método automático no permitido para la fuente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Datos de prueba:**

  | fuente | metodo_adquisicion | Mensaje esperado |
  | ----- | ----- | ---- |
  | Éxito | extraccion_web | `"El método extraccion_web no está permitido para la fuente Éxito."` |
  | Alkosto (captura_automatica_habilitada = no) | sitemap_datos_estructurados | `"La fuente Alkosto no está habilitada para el método sitemap_datos_estructurados."` |

- **Resultado esperado:** ninguna se guarda.

### QA-09: Fuente reservada, inexistente o deshabilitada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | fuente | Mensaje esperado |
  | ----- | ----- |
  | TVEC | `"TVEC y SECOP II son fuentes de contratación pública; no se registran como observaciones de mercado."` |
  | Homecenter (no existe) | `"La fuente Homecenter no existe en el catálogo de fuentes de mercado."` |
  | Mercado Libre (carga manual deshabilitada), método manual | `"La fuente Mercado Libre no está habilitada para el método manual."` |

- **Resultado esperado:** ninguna se guarda.

### QA-10: Coherencia entre método y quien registra

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | metodo_adquisicion | registrado_por | Resultado |
  | ----- | ----- | ---- |
  | manual | conector:Alkosto | Rechazo |
  | sitemap_datos_estructurados (Alkosto habilitada) | admin.po@prueba.local | Rechazo |
  | sitemap_datos_estructurados (fuente Falabella) | conector:Alkosto | Rechazo |

- **Resultado esperado:** ninguna se guarda; en todos los casos se devuelve `"registrado_por no corresponde al método de adquisición ni a la fuente."`

### QA-11: Etiqueta de origen manual frente a automática

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-05
- **Precondiciones:** Alkosto con captura automática permitida y habilitada.
- **Pasos:**
  1. Guardar OBS-BASE (manual).
  2. Guardar una observación de Alkosto con `metodo_adquisicion = sitemap_datos_estructurados`, `canal_carga = conector`, `registrado_por = conector:Alkosto`, `protocolo_busqueda = no_aplica`, `id_contexto = EJEC-2026-10-02-ALK`.
  3. Leer ambas desde la consulta administrativa y desde la lectura que usa la comparación.
- **Resultado esperado:** la manual se entrega con `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `registrado_por` y `fecha_registro`; la automática con `es_manual = no` y `etiqueta_origen = "Captura automática (sitemap_datos_estructurados)"`. Ninguna lectura omite estos campos.

### QA-12: Independencia de la base frente a la comparación

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-01
- **Pasos:**
  1. Guardar una observación del modelo `XR-77A95L` (sin contratos en el sistema).
  2. Consultarla.
  3. Ejecutar un recálculo de benchmarks y volver a consultar todas las observaciones.
- **Resultado esperado:** la observación existe en el paso 2; tras el recálculo, ningún campo de ninguna observación cambió (comparación campo a campo antes/después).

### QA-13: Gestión del catálogo de fuentes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-02
- **Datos de prueba:**

  | Acción | Resultado esperado |
  | ----- | ----- |
  | Crear "Ktronix" con vendedores ["Ktronix"] | Creada con `carga_manual_habilitada = sí`, `captura_automatica_permitida = no`, `creada_por` y `fecha_creacion` |
  | Crear "Panamericana" sin vendedores | `"Una fuente de mercado requiere al menos un nombre de vendedor aceptado."` |
  | Crear "tvec" | `"TVEC y SECOP II son fuentes de contratación pública; no se registran como fuentes de mercado."` |
  | Crear "alkosto" | `"Ya existe una fuente con el nombre alkosto."` |
  | Poner `captura_automatica_permitida = sí` a Éxito | `"Éxito no admite captura automática en el MVP; solo carga manual."` |
  | Poner `captura_automatica_permitida = sí` a Ktronix | `"La fuente Ktronix no tiene conector de captura automática."` |
  | Eliminar Alkosto con observaciones | `"No se puede eliminar una fuente con observaciones; deshabilítela."` |

### QA-14: Operaciones rechazadas para el rol Analista

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10
- **Pasos:**
  1. Como `analista1@prueba.local`, enviar OBS-BASE.
  2. Como `analista1@prueba.local`, intentar crear la fuente "Ktronix".
- **Resultado esperado:** ambas se rechazan con `"Operación permitida solo para el rol Administrador."`; no se crea nada.

### QA-15: Consulta sobre base vacía

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11
- **Precondiciones:** base de observaciones sin registros.
- **Pasos:**
  1. Solicitar observaciones de Samsung UN55DU7000KXZL.
- **Resultado esperado:** lista vacía, sin error.

### QA-16: Evidencia guardada como copia con hash

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** RN-07
- **Pasos:**
  1. Guardar OBS-BASE.
  2. Recuperar la evidencia guardada y calcular su SHA-256.
  3. Verificar que la evidencia se recupera aunque la URL de origen no responda.
  4. Ejecutar el respaldo diario y restaurarlo en un entorno de prueba.
- **Resultado esperado:** el hash calculado coincide con el registrado; la copia es recuperable sin depender de la URL; la observación y su evidencia están presentes tras la restauración.

### QA-17: Evento auditable por alta y cambio de catálogo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Guardar OBS-BASE.
  2. Crear la fuente "Ktronix".
- **Resultado esperado:** existen dos eventos: `alta_observacion` con `admin.po@prueba.local`, fecha y hora e `id_observacion`; `cambio_catalogo_fuente` con usuario, fecha y hora e identificador de la fuente.

### QA-18: Ausencia de términos prohibidos

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Provocar todos los mensajes de error de RN-02 y RN-03 y revisar las etiquetas de origen.
- **Resultado esperado:** ningún texto contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

---

**Total de casos:** 18
