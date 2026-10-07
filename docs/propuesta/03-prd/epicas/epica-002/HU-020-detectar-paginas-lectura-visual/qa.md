# Casos de Prueba — HU-020: Detectar las páginas que requieren OCR o lectura multimodal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la clasificación por página (sin texto utilizable, imagen incrustada, documento de imagen), las imágenes en hojas de cálculo, la generación de imágenes, el límite por proceso, las fallas, los indicadores y la validación de parámetros. Queda fuera: la lectura con OCR o multimodal (HU-022).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración: mínimo 50 caracteres utilizables; umbral de imagen 10 %; resolución 110 dpi; límite 60 páginas visuales por proceso.
- Proceso `CO1.BDOS.1234567` con documentos preparados (HU-019) construidos para cada caso.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-08 | QA-01 |
| Escenario 2 / RN-04, RN-08 | QA-02 |
| Escenario 3 / RN-04 | QA-03 |
| RN-05 | QA-04 |
| Escenario 4 / RN-06 | QA-05 |
| Escenario 5 / RN-07 | QA-06 |
| Escenario 6 / RN-09 | QA-07 |
| Escenario 7 / RN-10 | QA-08 |
| Escenario 8 / RN-11 | QA-09 |
| Escenario 9 / RN-02, RN-03 | QA-10 |
| RN-12 | QA-11 |
| RN-13 / Permisos | QA-12 |

---

## Casos de Prueba

### QA-01: Página escaneada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-08
- **Pasos:**
  1. Ejecutar la detección sobre "Oferta economica firmada.pdf" (4 páginas, 0 caracteres).
- **Resultado esperado:** las 4 páginas "requiere lectura visual", motivo "sin texto utilizable"; 4 imágenes a 110 dpi asociadas a páginas 1 a 4.

### QA-02: Tabla incrustada como imagen en página con texto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04, RN-08
- **Datos de prueba:**

  | Página | Caracteres | Imagen mayor | Resultado esperado |
  | ------ | ---------- | ------------ | ------------------ |
  | 4 | 1.200 | 35 % | requiere lectura visual (imagen incrustada) |
  | 5 | 900 | 10 % | requiere lectura visual (límite exacto) |
  | 6 | 900 | 9 % | texto suficiente |

- **Pasos:**
  1. Ejecutar la detección.
- **Resultado esperado:** el de la tabla; las páginas 4 y 5 tienen imagen generada y conservan su capa de texto.

### QA-03: Logotipos pequeños no activan la regla aunque sumen más del umbral

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-04
- **Datos de prueba:**

  | Página | Caracteres | Imágenes |
  | ------ | ---------- | -------- |
  | 1 | 2.000 | 3 imágenes de 6 %, 5 % y 4 % (suma 15 %) |

- **Pasos:**
  1. Ejecutar la detección.
- **Resultado esperado:** "texto suficiente"; no se genera imagen.

### QA-04: Página con ambos motivos

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-05
- **Pasos:**
  1. Ejecutar la detección sobre una página con 10 caracteres y una imagen del 80 %.
- **Resultado esperado:** "requiere lectura visual" con motivos "sin texto utilizable" e "imagen incrustada".

### QA-05: Documentos de imagen y reducción de imágenes muy grandes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-06
- **Datos de prueba:**

  | Archivo | Tamaño | Resultado esperado |
  | ------- | ------ | ------------------ |
  | Cotizacion.jpg | 1.600 × 2.200 px | se usa original |
  | Cotizacion.png | 6.000 × 8.000 px | se reduce a 3.000 × 4.000 px |

- **Pasos:**
  1. Ejecutar la detección.
- **Resultado esperado:** ambos "requiere lectura visual", motivo "documento de imagen", con el tamaño de la tabla.

### QA-06: Imagen insertada en hoja de cálculo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-07
- **Pasos:**
  1. Ejecutar la detección sobre un XLSX con la hoja "Oferta" con 2 imágenes y celdas con texto.
- **Resultado esperado:** unidades "Oferta, imagen 1" y "Oferta, imagen 2" con "requiere lectura visual" y motivo "imagen incrustada"; las celdas siguen disponibles.

### QA-07: Límite de páginas visuales por proceso

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-09
- **Datos de prueba:**

  | Caso | Páginas que requieren lectura visual | Resultado esperado |
  | ---- | ------------------------------------ | ------------------ |
  | A | 60 | 60 imágenes, 0 omitidas |
  | B | 61 | 60 imágenes, 1 omitida |
  | C | 75 (doc. posición 1: 40 págs.; posición 2: 35 págs.) | 40 del doc. 1 + 20 primeras del doc. 2; 15 omitidas |

- **Pasos:**
  1. Ejecutar la detección para cada caso.
- **Resultado esperado:** el de la tabla; las omitidas quedan "lectura visual omitida por límite" y el proceso anota su número.

### QA-08: Falla al generar la imagen de una página

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-10
- **Pasos:**
  1. Simular falla en la generación de la imagen de la página 3 de un PDF escaneado de 5 páginas.
- **Resultado esperado:** página 3 "requiere lectura visual" con "imagen no generada" y el error; páginas 1, 2, 4 y 5 con imagen generada.

### QA-09: Indicadores por documento y proceso

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-11
- **Pasos:**
  1. Tras QA-01 y QA-02 en el mismo proceso, consultar como Administrador.
- **Resultado esperado:** "Oferta economica firmada.pdf": 4 páginas, 4 sin texto utilizable, 0 con imagen incrustada, 4 imágenes generadas; documento de QA-02: 3 páginas evaluadas, 0 sin texto, 2 con imagen incrustada, 2 imágenes; proceso "requirió lectura visual: sí".

### QA-10: Valores límite de caracteres utilizables

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-02, RN-03
- **Datos de prueba:**

  | Página sin imágenes | Resultado esperado |
  | ------------------- | ------------------ |
  | 49 caracteres utilizables | requiere lectura visual |
  | 50 caracteres utilizables | texto suficiente |
  | 40 letras + 60 espacios y signos | requiere lectura visual (solo cuentan 40) |

- **Pasos:**
  1. Ejecutar la detección.
- **Resultado esperado:** el de la tabla.

### QA-11: Validación de parámetros

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Datos de prueba:**

  | Parámetro | Valores válidos | Valores inválidos |
  | --------- | --------------- | ----------------- |
  | Mínimo de caracteres | 0, 1.000 | -1, 1.001 |
  | Umbral de imagen | 1 %, 100 % | 0 %, 101 % |
  | Resolución | 72, 300 dpi | 71, 301 dpi |
  | Límite por proceso | 1, 500 | 0, 501 |

- **Pasos:**
  1. Como Administrador, guardar cada valor.
- **Resultado esperado:** los válidos se guardan; los inválidos se rechazan con "Valor fuera de rango para {parámetro}: debe estar entre {mín} y {máx}" y se conserva el valor anterior.

### QA-12: Funciona sin IA y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-13 / Permisos requeridos
- **Pasos:**
  1. Desactivar la extracción con IA y repetir QA-01.
  2. Como `analista1@piloto.test`, intentar cambiar el umbral de imagen.
- **Resultado esperado:** QA-01 produce el mismo resultado sin llamadas al servicio de IA; el Analista recibe acceso denegado y el umbral no cambia.

---

**Total de casos:** 12
