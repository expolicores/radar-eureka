# Casos de Prueba — HU-022: Extraer con IA los datos de cada ítem de televisor con su evidencia de origen

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la extracción por ítem de televisor, la evidencia obligatoria por campo, el límite de categoría, los contratos mixtos, el tratamiento de varios oferentes, la etapa y la precedencia de precios, la prohibición de usar el valor de datos abiertos, la validación de la respuesta, las fallas del servicio, la reextracción y la separación respecto de la ingesta. El componente de IA se sustituye por un extractor simulado que devuelve respuestas controladas, más una prueba integrada con documentos reales de la muestra D4. Queda fuera: base tributaria (HU-023), precio derivado (HU-024), información insuficiente (HU-025), umbral (HU-026) e inconsistencias (HU-027).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Extracción con IA activa. Tiempo de espera 300 s; 3 reintentos; 3 ejecuciones antes de "requiere intervención".
- Proceso base `CO1.BDOS.1234567` / contrato `CO1.PCCNTR.7654321` (valor en datos abiertos 89.800.000), en "documentos preparados", con:

  | Documento | Categoría | Contenido relevante |
  | --------- | --------- | ------------------- |
  | Propuesta_economica_ganador.pdf (v1, 3 págs.) | oferta del adjudicatario | Pág. 2: "1 \| Televisor Smart TV Samsung UN55DU7000 55 pulgadas 4K LED \| 8 \| $ 2.150.000 \| $ 17.200.000" |
  | Contrato 045-2025.pdf (v1, 4 págs.) | contrato | Pág. 1: "cantidad: ocho (8) televisores" |
  | Estudio previo.pdf (v1, 30 págs.) | estudios previos | Pág. 12: presupuesto unitario $ 2.400.000 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04, RN-05, RN-12, RN-16 | QA-01 |
| RN-04 (formatos numéricos y moneda) | QA-02 |
| RN-04 (referencia orientativa) | QA-03 |
| Escenario 2 / RN-05 | QA-04 |
| Escenario 3 / RN-03 | QA-05 |
| Escenario 4 / RN-12 | QA-06 |
| Escenario 5 / RN-06 | QA-07 |
| Escenario 6 / RN-05 | QA-08 |
| Escenario 7 / RN-08 | QA-09 |
| Escenario 8 / RN-08 | QA-10 |
| Escenario 9 / RN-04 | QA-11 |
| Escenario 10 / RN-09 | QA-12 |
| Escenario 11 / RN-02, RN-10 | QA-13 |
| Escenario 12 / RN-16 | QA-14 |
| Escenario 13 / RN-14, RN-15, RN-16 | QA-15, QA-16, QA-17 |
| Escenario 14 / RN-01 | QA-18 |
| RN-07 | QA-19 |
| RN-11 | QA-20 |
| RN-13 | QA-21 |
| RN-17 | QA-22 |
| RN-18 | QA-23 |
| Permisos | QA-24 |

---

## Casos de Prueba

### QA-01: Extracción de un ítem con precio unitario publicado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04, RN-05, RN-12, RN-16
- **Pasos:**
  1. Ejecutar la extracción del proceso base.
  2. Consultar el ítem `CO1.PCCNTR.7654321-01`.
- **Resultado esperado:** marca "Samsung", modelo "UN55DU7000", tamaño 55 "pulgadas", resolución "4K", tecnología "LED", Smart "sí", cantidad 8 (evidencia contrato pág. 1), precio unitario 2.150.000,00, valor total 17.200.000,00, etapa "adjudicado", tipo `explicito`; cada campo con documento, versión 1, página y confianza; proceso "extraído" con 1 ítem.

### QA-02: Interpretación de formatos numéricos y moneda

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-04
- **Datos de prueba:**

  | Texto en el documento | Valor esperado |
  | --------------------- | -------------- |
  | $ 2.150.000,00 | 2150000,00 |
  | 2.150.000 | 2150000,00 |
  | COP 1.999.999,50 | 1999999,50 |
  | USD 650 | nulo, "moneda distinta de COP" |

- **Pasos:**
  1. Ejecutar la extracción con un documento por formato.
- **Resultado esperado:** el de la tabla.

### QA-03: Modelo como referencia orientativa

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Extraer un estudio previo con "Televisor tipo LG 55UR8750 o equivalente".
- **Resultado esperado:** modelo "55UR8750" con la anotación "referencia orientativa".

### QA-04: Evidencia en celda y en página de lectura visual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Extraer un proceso con cantidad en `Oferta!C5` de un XLSX y precio en la imagen de la página 3 de un PDF escaneado.
- **Resultado esperado:** evidencia de cantidad "hoja Oferta, celda C5"; evidencia del precio "página 3 (lectura visual)".

### QA-05: Contrato mixto con accesorios

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-03
- **Datos de prueba:**

  | Línea del documento | ¿Ítem de TV? |
  | ------------------- | ------------ |
  | 10 Computadores portátiles | No |
  | 2 Televisores 65" 4K Smart | Sí |
  | 2 Soportes de pared | No |
  | 1 Monitor 24" para CCTV | No |
  | 1 Videowall 2x2 | No |

- **Pasos:**
  1. Ejecutar la extracción.
- **Resultado esperado:** 1 único ítem de televisor con cantidad 2.

### QA-06: Varios ítems de televisor

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-12
- **Pasos:**
  1. Extraer una oferta con "4 TV 43 pulgadas" (línea 1) y "2 TV 65 pulgadas" (línea 2).
- **Resultado esperado:** ítems `-01` (43", cantidad 4) y `-02` (65", cantidad 2) con sus evidencias.

### QA-07: Campos ausentes quedan nulos

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Pasos:**
  1. Extraer documentos que solo dicen "Televisor 50 pulgadas 4K, 3 unidades, valor unitario $ 1.800.000".
- **Resultado esperado:** marca, modelo, tecnología y Smart nulos sin evidencia ni confianza; tamaño, resolución, cantidad y precio registrados.

### QA-08: Datos sin evidencia válida se descartan

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Campo devuelto | Evidencia devuelta | Resultado esperado |
  | -------------- | ------------------ | ------------------ |
  | marca "LG" | ninguna | nulo, "dato sin evidencia válida descartado" (valor "LG") |
  | precio 2.000.000 | "página 9" de un documento de 4 páginas | nulo, observación con valor 2.000.000 |
  | cantidad 8 | documento no enviado al extractor | nulo, observación |
  | tamaño 55 | "hoja Oferta, celda Z999" sin valor | nulo, observación |

- **Pasos:**
  1. Configurar el extractor simulado para devolver esos campos.
  2. Ejecutar la extracción.
- **Resultado esperado:** el de la tabla.

### QA-09: Varios oferentes con adjudicatario identificado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Datos de prueba:**

  | Oferente | Precio unitario | Adjudicado |
  | -------- | --------------- | ---------- |
  | COMERCIALIZADORA ABC SAS | 2.150.000 | Sí |
  | DISTRIBUCIONES XYZ LTDA | 2.090.000 | No |
  | TECNOLOGÍA 123 SAS | 2.300.000 | No |

- **Pasos:**
  1. Extraer el informe de evaluación con esa tabla.
- **Resultado esperado:** solo se registra 2.150.000 con etapa "adjudicado"; no hay registro de 2.090.000 ni de 2.300.000.

### QA-10: Adjudicatario no identificable

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Extraer la misma tabla de QA-09 sin columna de adjudicado y sin aceptación ni contrato seleccionados.
- **Resultado esperado:** precio unitario y valor total nulos con "oferta adjudicada no identificable"; tamaño, resolución y cantidad registrados con su evidencia.

### QA-11: Solo precio de presupuesto

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-04
- **Pasos:**
  1. Extraer un proceso cuyo único precio es el presupuesto de $ 2.400.000 del estudio previo (pág. 12).
- **Resultado esperado:** precio unitario 2.400.000,00 con etapa "presupuesto o cotización" y evidencia "Estudio previo.pdf, página 12".

### QA-12: Conflicto entre documentos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-09
- **Datos de prueba:**

  | Documento | Cantidad |
  | --------- | -------- |
  | Contrato (pág. 1) | 8 |
  | Oferta del adjudicatario (pág. 2) | 10 |

- **Pasos:**
  1. Ejecutar la extracción.
- **Resultado esperado:** cantidad 8 con evidencia del contrato; anotación "valores distintos en documentos: 8 (contrato, página 1) / 10 (oferta, página 2)"; ítem marcado "con conflicto entre documentos".

### QA-13: El valor de datos abiertos no se usa ni se entrega al extractor

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-02, RN-10
- **Pasos:**
  1. Extraer un proceso sin precio ni valor del ítem en los documentos; contrato con valor en datos abiertos 89.800.000 y cantidad 8.
  2. Inspeccionar la entrada enviada al extractor simulado.
- **Resultado esperado:** precio unitario y valor total nulos (ningún 11.225.000 ni 89.800.000 en el ítem); 89.800.000 visible solo como "valor del contrato (datos abiertos, referencia)"; el valor 89.800.000 no aparece en la entrada al extractor.

### QA-14: Proceso sin ítems de televisor

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-16
- **Pasos:**
  1. Extraer documentos de un servicio de mantenimiento de televisores.
- **Resultado esperado:** "extraído sin ítems de televisor" con la observación del extractor.

### QA-15: Servicio de IA no disponible

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-15
- **Pasos:**
  1. Configurar el servicio simulado para fallar en 4 intentos.
  2. Ejecutar la extracción.
- **Resultado esperado:** 4 intentos con espera creciente; "extracción fallida: servicio de IA no disponible"; ningún ítem guardado.

### QA-16: Respuesta inválida del extractor

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 13 / RN-14
- **Datos de prueba:**

  | Caso | Respuestas | Resultado esperado |
  | ---- | ---------- | ------------------ |
  | A | Formato inválido y luego válido | extraído con la segunda respuesta |
  | B | Formato inválido dos veces | extracción fallida: respuesta inválida del extractor, sin ítems |
  | C | Válida con cantidad -3 | cantidad nula, "valor fuera de rango descartado"; resto registrado |

- **Pasos:**
  1. Ejecutar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-17: Reintento entre ejecuciones y requerimiento de intervención

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-16
- **Pasos:**
  1. Hacer fallar la extracción del proceso en 3 ejecuciones programadas consecutivas.
  2. Ejecutar una cuarta vez.
- **Resultado esperado:** tras la tercera falla, "extracción fallida: requiere intervención"; la cuarta ejecución no lo intenta.

### QA-18: La ingesta no dispara reextracción; la solicitud del Administrador sí

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 14 / RN-01
- **Pasos:**
  1. Tras QA-01, ejecutar una ingesta que actualiza el contrato y agrega 2 documentos.
  2. Ejecutar la extracción programada.
  3. Como Administrador, solicitar la reextracción del proceso.
- **Resultado esperado:** en el paso 2 no hay llamadas al extractor; en el paso 3 sí.

### QA-19: Registro de la confianza

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Datos de prueba:**

  | Confianza devuelta | Valor registrado |
  | ------------------ | ---------------- |
  | 0,87 | 0,87 |
  | "alta" | 0,90 |
  | "media" | 0,60 |
  | "baja" | 0,30 |
  | 1,20 | campo nulo, "valor fuera de rango descartado" |
  | (ausente en un campo con valor) | campo nulo, "valor fuera de rango descartado" |

- **Pasos:**
  1. Ejecutar la extracción con cada valor.
- **Resultado esperado:** el de la tabla.

### QA-20: Lote no determinado se propaga al ítem

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Extraer un proceso marcado "lote no determinado".
- **Resultado esperado:** cada ítem queda marcado "lote no determinado".

### QA-21: Datos no permitidos se descartan

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-13
- **Pasos:**
  1. Configurar el extractor simulado para devolver además "cuenta bancaria 123-456789-01" y "cédula 1.000.000.001" (ficticios).
  2. Buscar esos valores en todo lo almacenado.
- **Resultado esperado:** no se encuentran en ningún registro.

### QA-22: Reextracción respeta campos validados

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-17
- **Pasos:**
  1. Tras QA-01, el Administrador corrige la cantidad a 9 (validada).
  2. Reextraer; el extractor devuelve cantidad 8 y precio 2.150.000.
- **Resultado esperado:** la cantidad sigue en 9; se registra 8 como "propuesta de reextracción" y el ítem pasa a revisión; la extracción anterior se conserva como versión previa.

### QA-23: Efectos posteriores disparados

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-18
- **Pasos:**
  1. Tras QA-01, verificar los registros de evidencia, costo y tiempo.
- **Resultado esperado:** existe la copia de evidencia de los documentos usados, y la extracción quedó entregada a base tributaria, precio derivado, información insuficiente, confianza e inconsistencias, con costo y tiempo registrados.

### QA-24: Permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, consultar el ítem `-01` y luego solicitar una reextracción.
- **Resultado esperado:** la consulta funciona; la reextracción se rechaza con acceso denegado.

---

**Total de casos:** 24
