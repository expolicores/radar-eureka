# Casos de Prueba — HU-017: Excluir documentos vacíos, formularios en blanco y duplicados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban las reglas determinísticas de archivo vacío, duplicado por hash dentro del proceso y formulario en blanco, su orden de evaluación, el recalculo de la priorización, el registro de la causa y la reversión manual. Queda fuera: la descarga (HU-016) y la apertura de archivos dañados (HU-019).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración: tamaño mínimo 1.024 bytes; mínimo de 200 caracteres utilizables; umbral de valor monetario 10.000.
- Procesos base: `CO1.BDOS.9640674`, `CO1.BDOS.9691113`, `CO1.BDOS.1111111`, `CO1.BDOS.2222222`, con documentos descargados y priorizados según cada caso.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-08 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-06, RN-09 | QA-03 |
| Escenario 4 / RN-06 | QA-04, QA-05 |
| Escenario 5 / RN-07 | QA-06 |
| Escenario 6 / RN-05 | QA-07 |
| Escenario 7 / RN-04 | QA-08, QA-09 |
| Escenario 8 / RN-04 | QA-10 |
| Escenario 9 / RN-02 | QA-11 |
| Escenario 10 / RN-10 | QA-12, QA-13 |
| RN-11 / Permisos | QA-14 |

---

## Casos de Prueba

### QA-01: Archivo vacío por tamaño (valores límite)

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-08
- **Datos de prueba:**

  | Tamaño | Resultado esperado |
  | ------ | ------------------ |
  | 0 bytes | archivo vacío |
  | 130 bytes | archivo vacío |
  | 1.023 bytes | archivo vacío |
  | 1.024 bytes (PDF de 1 página con texto) | elegible |

- **Pasos:**
  1. Ejecutar la evaluación de elegibilidad para cada documento en `CO1.BDOS.9640674`.
- **Resultado esperado:** el de la tabla; para los vacíos se dispara el recalculo de la priorización.

### QA-02: Archivo vacío por estructura

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 2 / RN-03
- **Datos de prueba:**

  | Archivo | Característica |
  | ------- | -------------- |
  | vacio.pdf (3.000 bytes) | 0 páginas |
  | precios.xlsx (8.000 bytes) | 3 hojas sin valores |
  | carta.docx (12.000 bytes) | Sin texto ni imágenes |

- **Pasos:**
  1. Ejecutar la evaluación.
- **Resultado esperado:** los tres quedan "no elegible: archivo vacío".

### QA-03: Formato de propuesta económica sin diligenciar

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documento | ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx | Categoría oferta o propuesta económica |
  | Texto | 1.450 caracteres; encabezados ÍTEM, DESCRIPCIÓN, CANTIDAD, VALOR UNITARIO, VALOR TOTAL; celdas de valor en 0; "Vigencia 2025"; "Página 1 de 2" | Sin valores monetarios válidos |

- **Pasos:**
  1. Ejecutar la evaluación.
- **Resultado esperado:** "no elegible: formulario en blanco", causa "fuente", regla RN-06 y fecha registradas; se recalcula la priorización.

### QA-04: Propuesta diligenciada sigue elegible

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-06
- **Datos de prueba:**

  | Texto con valores | Formato |
  | ----------------- | ------- |
  | "$ 2.150.000" | Con símbolo |
  | "COP 17200000" | Con código de moneda |
  | "2,150,000" | Separador coma |

- **Pasos:**
  1. Ejecutar la evaluación con un documento por formato.
- **Resultado esperado:** los tres siguen elegibles.

### QA-05: Valores límite del umbral monetario

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Único número del texto | Resultado esperado |
  | ---------------------- | ------------------ |
  | "9.999" | formulario en blanco |
  | "10.000" | elegible |
  | "2025" (año, sin separador) | formulario en blanco |

- **Pasos:**
  1. Ejecutar la evaluación de un formato de anexo económico de 300 caracteres con cada número.
- **Resultado esperado:** el de la tabla.

### QA-06: Documento escaneado no se marca como en blanco

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Datos de prueba:**

  | Caso | Caracteres utilizables | Resultado esperado |
  | ---- | ---------------------- | ------------------ |
  | Oferta economica firmada.pdf (4 páginas escaneadas) | 0 | elegible, "en blanco no determinable sin lectura visual" |
  | Oferta con 199 caracteres y sin valores | 199 | elegible, misma anotación |
  | Oferta con 200 caracteres y sin valores | 200 | formulario en blanco |

- **Pasos:**
  1. Ejecutar la evaluación.
- **Resultado esperado:** el de la tabla.

### QA-07: Categoría no económica no se evalúa como formulario

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Documento | Categoría |
  | --------- | --------- |
  | Estudio previo.pdf, 5.000 caracteres sin valores | estudios previos |
  | Anexo tecnico.pdf, 3.000 caracteres sin valores | anexo técnico |

- **Pasos:**
  1. Ejecutar la evaluación.
- **Resultado esperado:** ambos siguen elegibles.

### QA-08: Duplicados con original por posición de priorización

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-04
- **Datos de prueba:**

  | Documento | Posición | Hash |
  | --------- | -------- | ---- |
  | 610001 | 2 | H1 |
  | 610005 | 6 | H1 |
  | 610009::oferta.pdf (interno) | no seleccionado | H1 |

- **Pasos:**
  1. Ejecutar la evaluación en `CO1.BDOS.9691113`.
- **Resultado esperado:** 610001 elegible; 610005 y el interno "no elegible: duplicado de 610001", causa "procesamiento"; se recalcula la priorización.

### QA-09: Original cuando ninguno está seleccionado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Documento | Fecha de carga | Hash |
  | --------- | -------------- | ---- |
  | 620003 | 2025-04-02 | H2 |
  | 620001 | 2025-04-05 | H2 |
  | 620002 | 2025-04-02 | H2 |

- **Pasos:**
  1. Ejecutar la evaluación con los tres no seleccionados.
- **Resultado esperado:** original 620002 (fecha más antigua y menor id entre los de 2025-04-02); 620001 y 620003 "duplicado de 620002".

### QA-10: Mismo archivo en procesos distintos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-04
- **Pasos:**
  1. Ejecutar la evaluación con un archivo de hash H3 en `CO1.BDOS.1111111` y en `CO1.BDOS.2222222`.
- **Resultado esperado:** ambos siguen elegibles.

### QA-11: Vacío se evalúa antes que duplicado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-02
- **Pasos:**
  1. Ejecutar la evaluación con dos documentos de 0 bytes en el mismo proceso.
- **Resultado esperado:** ambos "no elegible: archivo vacío"; ninguno marcado como duplicado.

### QA-12: Reversión manual de un formulario en blanco

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documento | El de QA-03 | |
  | Comentario | "Contiene precios escritos en letras: dos millones ciento cincuenta mil pesos" | |

- **Pasos:**
  1. Como Administrador, marcar el documento como "elegible por revisión manual".
  2. Ejecutar de nuevo la evaluación.
- **Resultado esperado:** el documento queda elegible; se registran usuario, fecha, marca anterior "formulario en blanco" y comentario; la segunda evaluación no lo vuelve a marcar; se recalcula la priorización.

### QA-13: Reversión inválida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Datos de prueba:**

  | Caso | Entrada | Mensaje esperado |
  | ---- | ------- | ---------------- |
  | A | Documento marcado, comentario vacío | "El comentario es obligatorio para revertir una marca automática" |
  | B | Documento sin marca, comentario "ok" | "El documento no tiene una marca automática que revertir" |
  | C | Comentario de 501 caracteres | Rechazado por longitud (máximo 500) |
  | D | Comentario de 500 caracteres | Aceptado |

- **Pasos:**
  1. Ejecutar cada reversión como Administrador.
- **Resultado esperado:** A, B y C se rechazan sin cambios (con el mensaje indicado); D se acepta.

### QA-14: Contadores por proceso y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-11 / Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar consultar los contadores y revertir una marca.
  2. Como `admin.po@piloto.test`, consultar los contadores de `CO1.BDOS.9691113` tras QA-08.
- **Resultado esperado:** el Analista recibe acceso denegado; el Administrador ve 0 vacíos, 0 en blanco y 2 duplicados.

---

**Total de casos:** 14
