# Casos de Prueba — HU-019: Leer los formatos documentales soportados y generar su representación con ubicaciones

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la lectura determinística de PDF, XLSX/XLS, DOCX/DOC, JPG y PNG, la representación con ubicaciones (página, hoja y celda), el registro de imágenes incrustadas, los formatos no soportados, dañados y protegidos, los límites y el estado del proceso. Queda fuera: la decisión de lectura visual (HU-020) y la extracción con IA (HU-022).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración: máximo 300 páginas por documento; máximo 100.000 celdas por hoja.
- Proceso `CO1.BDOS.1234567` con documentos de prueba seleccionados y elegibles (archivos ficticios construidos para cada caso).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-11 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-04 | QA-03, QA-04 |
| Escenario 4 / RN-05 | QA-05 |
| Escenario 5 / RN-06 | QA-06 |
| RN-07 | QA-07 |
| Escenario 6 / RN-02, RN-12 | QA-08 |
| Escenario 7 / RN-08 | QA-09, QA-10 |
| Escenario 8 / RN-09 | QA-11 |
| Escenario 9 / RN-02 | QA-12 |
| Escenario 10 / RN-10 | QA-13 |
| Escenario 11 / RN-13 | QA-14 |
| RN-14 | QA-15 |
| Permisos | QA-16 |

---

## Casos de Prueba

### QA-01: PDF con capa de texto y tabla

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documento | Propuesta_economica_ganador.pdf, 3 páginas | |
  | Página 2 | Tabla "Ítem / Descripción / Cantidad / Valor unitario" con fila "1 / Televisor Smart 55 pulgadas / 8 / $ 2.150.000" | |

- **Pasos:**
  1. Ejecutar la preparación.
- **Resultado esperado:** 3 unidades "página 1" a "página 3"; la página 2 contiene "1 | Televisor Smart 55 pulgadas | 8 | $ 2.150.000"; tildes y "ñ" conservadas; estado "preparado".

### QA-02: PDF escaneado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Preparar "Oferta economica firmada.pdf" (4 páginas escaneadas).
- **Resultado esperado:** 4 páginas con texto vacío y "sin capa de texto"; estado "preparado".

### QA-03: Hoja de cálculo con fórmulas, hoja oculta y celdas combinadas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Celda | Contenido |
  | ----- | --------- |
  | Oferta!B5 | Televisor 55 pulgadas |
  | Oferta!C5 | 8 |
  | Oferta!D5 | =2150000 (valor calculado 2150000) |
  | Oferta!E5 | =C5*D5 (valor calculado 17200000) |
  | Oferta!B2:E2 combinadas | "PROPUESTA ECONÓMICA" |
  | Oferta!F1 | Fecha 2025-03-03 |
  | Base (oculta)!A1 | IVA 19% |

- **Pasos:**
  1. Preparar el XLSX y repetir con la misma hoja guardada como XLS.
- **Resultado esperado:** en ambos formatos: `Oferta!D5` = 2150000 y `Oferta!E5` = 17200000 (no las fórmulas); "PROPUESTA ECONÓMICA" en `Oferta!B2`; `Oferta!F1` = 2025-03-03; hoja "Base" incluida y marcada "oculta".

### QA-04: Fórmula sin valor calculado guardado

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Pasos:**
  1. Preparar un XLSX cuya celda `Oferta!E6` tiene fórmula sin valor calculado guardado.
- **Resultado esperado:** `Oferta!E6` vacía con anotación "fórmula sin valor calculado".

### QA-05: DOCX y DOC convertidos a representación paginada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Preparar "Aceptacion de oferta.docx" (2 páginas, tabla en la página 2) y su versión DOC.
- **Resultado esperado:** representación de 2 páginas con la tabla en la página 2 con celdas separadas por " | "; la versión paginada queda guardada junto al original con el mismo identificador de documento.

### QA-06: Imágenes JPG y PNG

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-06
- **Pasos:**
  1. Preparar "Cotizacion.jpg" y "Cotizacion.png".
- **Resultado esperado:** cada uno con una única "página 1", sin texto, marcada "imagen"; estado "preparado".

### QA-07: Registro de imágenes incrustadas por página

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** RN-07
- **Datos de prueba:**

  | Página | Contenido |
  | ------ | --------- |
  | 1 | Solo texto |
  | 2 | Texto y una imagen de tabla que ocupa ~40 % del área |
  | 3 | Dos logos que ocupan ~3 % del área |

- **Pasos:**
  1. Preparar el PDF.
- **Resultado esperado:** página 1: 0 imágenes, 0 %; página 2: 1 imagen, ~40 %; página 3: 2 imágenes, ~3 %.

### QA-08: Formatos no soportados

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-02, RN-12
- **Datos de prueba:**

  | Archivo |
  | ------- |
  | Plano.dwg |
  | Video.mp4 |
  | Correo.msg |

- **Pasos:**
  1. Preparar cada archivo.
- **Resultado esperado:** "no elegible: formato no soportado"; se recalcula la priorización.

### QA-09: Archivo dañado

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Preparar un PDF con estructura corrupta.
- **Resultado esperado:** "no elegible: archivo dañado" con el error de apertura; se recalcula la priorización.

### QA-10: Página no legible dentro de un PDF que sí abre

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-08
- **Pasos:**
  1. Preparar un PDF de 5 páginas cuya página 3 está corrupta.
- **Resultado esperado:** páginas 1, 2, 4 y 5 preparadas; página 3 vacía con "página no legible"; documento "preparado".

### QA-11: PDF protegido frente a PDF con restricciones

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Datos de prueba:**

  | Caso | Protección | Resultado esperado |
  | ---- | ---------- | ------------------ |
  | A | Contraseña de apertura | no elegible: archivo protegido, sin intentos de contraseña |
  | B | Solo restricción de impresión y copia | preparado con su texto |

- **Pasos:**
  1. Preparar ambos.
- **Resultado esperado:** el de la tabla.

### QA-12: Extensión que no coincide con el contenido

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-02
- **Pasos:**
  1. Preparar "oferta.pdf" cuyo contenido es un XLSX.
- **Resultado esperado:** se representa como hoja de cálculo con referencias de celda; anotación "extensión no coincide con el contenido".

### QA-13: Límites de páginas y celdas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Caso | Tamaño | Resultado esperado |
  | ---- | ------ | ------------------ |
  | A | PDF de 300 páginas | 300 preparadas, sin anotación |
  | B | PDF de 301 páginas | 300 preparadas, "truncado por límite de páginas: 300 de 301" |
  | C | PDF de 420 páginas | "truncado por límite de páginas: 300 de 420" |
  | D | Hoja con 100.001 celdas con valor | 100.000 celdas, "truncado por límite de celdas: 100000 de 100001" |

- **Pasos:**
  1. Preparar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-14: Estado del proceso

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-13
- **Datos de prueba:**

  | Caso | Resultado de los 8 documentos | Estado esperado |
  | ---- | ----------------------------- | --------------- |
  | A | 7 preparados, 1 dañado | documentos preparados (7) |
  | B | 8 no elegibles | sin documentos legibles |

- **Pasos:**
  1. Preparar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-15: Funciona con la IA desactivada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-14
- **Pasos:**
  1. Desactivar la extracción con IA.
  2. Preparar el PDF de QA-01.
- **Resultado esperado:** el documento queda "preparado" igual que en QA-01 y no se registra ninguna llamada al servicio de IA.

### QA-16: Permisos

- **Tipo:** Permisos
- **Prioridad:** Baja
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar consultar la representación de 600002.
  2. Repetir como `admin.po@piloto.test`.
- **Resultado esperado:** acceso denegado para el Analista; el Administrador ve la representación.

---

**Total de casos:** 16
