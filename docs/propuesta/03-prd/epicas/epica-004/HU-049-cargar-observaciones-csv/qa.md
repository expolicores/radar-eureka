# Casos de Prueba — HU-049: Cargar observaciones de precio de forma semiautomática con un archivo CSV

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la carga por paquete .zip con CSV: validación del paquete, codificación y encabezado, validación campo a campo por fila con aceptación parcial, grupos de búsqueda todo o nada, evidencias, duplicados de paquete y de URL, reporte, campos asignados, procesamiento de 100 y 1.000 filas, evento auditable y permisos.

Fuera de alcance: reglas individuales ya cubiertas en HU-042 y HU-047, salvo su aplicación por fila.

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Fecha de referencia de carga:** 2026-10-02T12:00-05:00. Antigüedad máxima manual: 7 días.
- **Fila válida base (R-BASE):** `Alkosto, "Televisor Samsung 55 pulgadas Crystal UHD 4K Smart", Samsung, UN55DU7000KXZL, , , 55, 4K UHD, LED, sí, Alkosto, 1899900, , ninguna, , url, https://www.alkosto.com/tv-samsung-55-du7000/p/{n}, 2026-10-02 10:00, indeterminado, evidencias/obs-{n}.png, sí, , ` (con `{n}` distinto por fila para que las URL no se repitan).
- **Paquetes de prueba:**

  | Paquete | Contenido |
  | ----- | ----- |
  | P100 | CSV con 100 filas R-BASE y 100 PNG válidos (300 KB c/u) |
  | P100-ERR | P100 con fila 8 precio "1.899.900", fila 16 marca vacía, fila 41 evidencia `evidencias/no-existe.png` |
  | P1000 | 1.000 filas válidas |
  | P1001 | 1.001 filas |
  | P-GRUPOS | filas 2–5 con grupo G1 y términos "televisor lg 65\|65UT8050"; filas 6–8 grupo G2 con la fila 7 sin evidencia |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-09 / RN-08 | QA-01 |
| Escenario 2 / RN-04 / RN-08 | QA-02 |
| RN-03 / RN-04 (valores por columna) | QA-03 |
| Escenario 3 / RN-01 / RN-02 | QA-04, QA-05 |
| Escenario 4 / RN-02 / RN-03 | QA-06 |
| Escenario 5 / RN-02 | QA-07 |
| RN-02 (formato RFC 4180, filas vacías, columnas) | QA-08 |
| Escenario 6 / RN-05 | QA-09 |
| Escenario 7 / RN-05 | QA-10 |
| Escenario 8 / RN-05 | QA-11 |
| RN-06 | QA-12 |
| Escenario 9 / RN-07 | QA-13 |
| Escenario 10 / RN-07 | QA-14 |
| Escenario 11 | QA-15 |
| RN-10 | QA-16 |
| RN-11 | QA-17 |
| Escenario 12 | QA-18 |

---

## Casos de Prueba

### QA-01: Carga de 100 observaciones válidas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-08, RN-09
- **Pasos:**
  1. Como `admin.po@prueba.local`, cargar P100.
- **Resultado esperado:** `"Lote {id_lote}: 100 filas leídas, 100 aceptadas, 0 rechazadas."`; 100 observaciones con `metodo_adquisicion = manual`, `canal_carga = archivo`, `id_contexto = id_lote`, `registrado_por = admin.po@prueba.local`, `etiqueta_origen = "Observación manual"`, `protocolo_busqueda = no_registrado`; el lote guarda nombre y hash del paquete.

### QA-02: Aceptación parcial con reporte por fila y columna

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-04, RN-08
- **Pasos:**
  1. Cargar P100-ERR.
  2. Descargar el reporte del lote.
- **Resultado esperado:** 97 observaciones creadas; resumen `"Lote {id}: 100 filas leídas, 97 aceptadas, 3 rechazadas."`; el reporte contiene: `8, precio_efectivo, 1.899.900, precio_efectivo debe ser un entero entre 1 y 999.999.999 COP.`; `16, marca, , Campo obligatorio ausente: marca.`; `41, archivos_evidencia, evidencias/no-existe.png, Archivo de evidencia no encontrado en el paquete: evidencias/no-existe.png.`

### QA-03: Validación campo a campo de valores

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-03, RN-04
- **Datos de prueba:** (cada variante es una fila R-BASE con un cambio)

  | Columna | Valor | Mensaje esperado |
  | ----- | ----- | ----- |
  | precio_efectivo | $1899900 | `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."` |
  | precio_efectivo | 999999999 | Aceptada |
  | precio_anterior | 1899900 | `"El precio anterior debe ser mayor que el precio efectivo."` |
  | tamano_pulgadas | 55,5 | `"tamano_pulgadas debe estar entre 10 y 120."` |
  | vendedor | TecnoImport SAS | `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Alkosto. Vendedor recibido: TecnoImport SAS."` |
  | fecha_observacion | 2026-09-25 11:59 | `"La fecha de observación no puede tener más de 7 días de antigüedad."` |
  | fecha_observacion | 2026-10-02 13:00 | `"La fecha de observación no puede ser futura."` |
  | precio_por_unidad | no | `"precio_por_unidad debe ser sí."` |
  | archivos_evidencia | evidencias/ficha.docx | `"Formato de evidencia no permitido: use PNG, JPG o PDF."` |
  | archivos_evidencia | 6 rutas | `"Se admiten máximo 5 evidencias por observación."` |
  | marca y modelo_referencia | vacíos | `"Campo obligatorio ausente: marca."` y `"Campo obligatorio ausente: modelo_referencia."` en la misma fila |

### QA-04: Paquete inválido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | Archivo cargado | Mensaje esperado |
  | ----- | ----- |
  | observaciones.csv (sin comprimir) | `"El paquete debe ser un archivo .zip."` |
  | .zip solo con imágenes | `"El paquete debe contener exactamente un archivo .csv."` |
  | .zip con dos CSV | `"El paquete debe contener exactamente un archivo .csv."` |
  | .zip de 101 MB | `"El paquete supera el tamaño máximo de 100 MB."` |
  | .zip truncado | `"El paquete está dañado y no se puede abrir."` |

- **Resultado esperado:** en todos los casos no se crea lote ni observaciones.

### QA-05: Límites de filas

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Paquete | Resultado |
  | ----- | ----- |
  | CSV solo con encabezado | `"El archivo CSV no tiene filas de datos."` |
  | CSV con 1 fila válida | Lote con 1 aceptada |
  | P1000 | Lote con 1.000 aceptadas |
  | P1001 | `"El archivo CSV supera el máximo de 1.000 filas."` |

### QA-06: Encabezado con columna faltante o desconocida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02, RN-03
- **Datos de prueba:**

  | Encabezado | Mensaje esperado |
  | ----- | ----- |
  | sin `precio_efectivo` | `"Falta la columna obligatoria: precio_efectivo."` |
  | con `precio_oferta` adicional | `"Columna no reconocida: precio_oferta."` |
  | columnas en otro orden y en mayúsculas, sin columnas opcionales | Aceptado |

### QA-07: Codificación no UTF-8

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-02
- **Datos de prueba:**

  | CSV | Resultado |
  | ----- | ----- |
  | Windows-1252 con "Televisor pequeño" | `"El archivo CSV debe estar codificado en UTF-8."` |
  | UTF-8 con BOM | Aceptado |

### QA-08: Formato RFC 4180, filas vacías y número de columnas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Fila | Contenido | Resultado |
  | ----- | ----- | ----- |
  | 2 | descripción `"Televisor LG 65"", UHD"` entre comillas | Aceptada con la descripción `Televisor LG 65", UHD` |
  | 3 | completamente vacía | Ignorada (no cuenta como leída) |
  | 4 | una columna de menos | `"La fila 4 tiene un número de columnas distinto al encabezado."` |

### QA-09: Grupo de búsqueda válido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-05
- **Pasos:**
  1. Cargar P-GRUPOS con la fila 7 corregida y la declaración de grupos confirmada.
- **Resultado esperado:** filas 2–5 crean 4 observaciones con `protocolo_busqueda = registrado` vinculadas a la búsqueda `{id_lote}-G1` con términos ["televisor lg 65", "65UT8050"].

### QA-10: Grupo con una fila inválida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-05
- **Pasos:**
  1. Cargar P-GRUPOS (fila 7 sin evidencia) con la declaración confirmada.
- **Resultado esperado:** G1 aceptado; G2 rechazado completo: fila 7 con `"Campo obligatorio ausente: archivos_evidencia."`, filas 6 y 8 con `"Fila rechazada porque su grupo de búsqueda G2 tiene errores."`

### QA-11: Grupo inconsistente y falta de declaración

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-05
- **Datos de prueba:**

  | Variante | Resultado |
  | ----- | ----- |
  | G1 con la fila 3 de fuente Falabella | filas 2–5: `"Las filas del grupo G1 deben tener la misma fuente, fecha_observacion y terminos_busqueda."` |
  | G1 con la fila 4 sin `terminos_busqueda` | fila 4: `"terminos_busqueda es obligatorio cuando hay grupo_busqueda."`; resto del grupo rechazado por grupo con errores |
  | P-GRUPOS sin declaración | Paquete rechazado: `"Confirme que cada grupo de búsqueda incluye todas las ofertas comparables encontradas."` |

### QA-12: Evidencias compartidas y no referenciadas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Situación | Resultado |
  | ----- | ----- |
  | filas 2 y 3 referencian `evidencias/resultados.png` | ambas aceptadas; misma evidencia con el mismo hash |
  | el paquete incluye `evidencias/sobrante.png` sin referencia | advertencia `"Archivo de evidencia no referenciado: evidencias/sobrante.png."`; el archivo no se guarda |

### QA-13: Paquete ya cargado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-07
- **Pasos:**
  1. Cargar P100 de nuevo después de QA-01.
  2. Cargar dos veces un paquete cuyas filas son todas inválidas.
- **Resultado esperado:** paso 1: `"Este paquete ya fue cargado el 2026-10-02 (lote {id})."` y no se crean observaciones; paso 2: la segunda carga se procesa (el lote anterior tuvo 0 aceptadas).

### QA-14: URL repetida dentro del lote

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-07
- **Datos de prueba:**

  | Fila | URL |
  | ----- | ----- |
  | 10 | https://www.alkosto.com/tv-samsung-55-du7000/p/0000000000001 |
  | 25 | misma URL |

- **Resultado esperado:** fila 10 aceptada; fila 25: `"Observación duplicada en el contexto {id_lote}: https://www.alkosto.com/tv-samsung-55-du7000/p/0000000000001."`

### QA-15: Ninguna fila válida

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 11
- **Pasos:**
  1. Cargar un paquete de 5 filas, todas con precio "abc".
- **Resultado esperado:** lote registrado con `"Lote {id}: 5 filas leídas, 0 aceptadas, 5 rechazadas."` y 5 renglones de error; ninguna observación creada.

### QA-16: Evento auditable del lote

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Resultado esperado:** tras QA-02 existe el evento `carga_manual_archivo` con usuario, fecha y hora, `id_lote` y conteos 100/97/3.

### QA-17: Procesamiento asíncrono de un paquete grande

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Cargar P1000 en un entorno donde el procesamiento tarde más de 30 segundos.
  2. Consultar el lote al terminar.
- **Resultado esperado:** la operación responde `"Lote {id_lote} en proceso."` sin bloquear; al terminar, el reporte muestra 1.000 aceptadas.

### QA-18: Analista no carga paquetes

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Resultado esperado:** como `analista1@prueba.local`, cargar P100 devuelve `"Operación permitida solo para el rol Administrador."`; no se crea lote.

---

**Total de casos:** 18
