# Casos de Prueba — HU-015: Priorizar los documentos relevantes de cada proceso para la extracción

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la clasificación de documentos en categorías por nombre y descripción, el orden y desempate, el límite configurable, el tratamiento de comprimidos, el recalculo por documentos no elegibles, el filtrado por lote y la validación de la configuración. Queda fuera: la descarga (HU-016), la detección de vacíos y duplicados (HU-017) y la expansión de comprimidos (HU-018), que aquí se simulan como entradas.

## Precondiciones y Datos Base

- Usuario `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración inicial: categorías y palabras clave de RN-03 y RN-04, límite 8, máximo de contenedores 10.
- Proceso base `CO1.BDOS.1234567` (contrato `CO1.PCCNTR.7654321`, objeto "Adquisición de televisores para la sede administrativa"), con estos documentos válidos:

  | id_documento | Nombre | Fecha de carga |
  | ------------ | ------ | -------------- |
  | 600001 | Informe de evaluación económica.pdf | 2025-03-05 |
  | 600002 | Propuesta_economica_ganador.pdf | 2025-03-03 |
  | 600003 | ANEXO 3 - FORMATO PROPUESTA ECONOMICA.xlsx | 2025-02-20 |
  | 600004 | Aceptacion de oferta.pdf | 2025-03-07 |
  | 600005 | Anexo tecnico.pdf | 2025-02-20 |
  | 600006 | Contrato 045-2025.pdf | 2025-03-14 |
  | 600007 | Estudio previo.pdf | 2025-02-10 |
  | 600008 | Oferta.pdf | 2025-03-02 |
  | 600009 | Invitacion publica.pdf | 2025-02-20 |
  | 600010 | Cotizaciones.zip | 2025-02-12 |
  | 600011 | CDP 123.pdf | 2025-02-08 |
  | 600012 | Poliza de cumplimiento.pdf | 2025-03-15 |
  | 600013 | RUT proveedor.pdf | 2025-03-02 |
  | 600014 | Garantia de seriedad de la oferta.pdf | 2025-03-02 |
  | 600015 | foto1.jpg | 2025-03-02 |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-06, RN-07, RN-11 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| RN-04 (palabra completa) | QA-03 |
| Escenario 3 / RN-07 | QA-04 |
| Escenario 4 / RN-12 | QA-05 |
| Escenario 5 / RN-08 | QA-06, QA-07 |
| Escenario 6 / RN-09 | QA-08 |
| Escenario 7 / RN-10 | QA-09 |
| Escenario 8 / RN-10 | QA-10 |
| Escenario 9 / RN-13 | QA-11 |
| Escenario 10 / RN-07 | QA-12 |
| Escenario 11 / RN-02, RN-05 | QA-13 |
| RN-06 (desempate y determinismo) | QA-14 |
| RN-13 (registro de cambios de configuración) / Permisos | QA-15 |

---

## Casos de Prueba

### QA-01: Selección de los 8 documentos más relevantes del proceso base

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-06, RN-07, RN-11
- **Pasos:**
  1. Ejecutar la priorización sobre `CO1.BDOS.1234567`.
  2. Consultar el resultado por documento.
- **Resultado esperado:** seleccionados en orden: 600001 (pos. 1), 600002 (pos. 2, fecha más reciente), 600003 (pos. 3), 600004, 600005, 600006, 600007, 600008 (pos. 8). 600009 "no seleccionado: fuera del límite (posición 9)"; 600010 "contenedor por expandir"; 600011–600014 "no seleccionado: categoría excluida"; 600015 "no seleccionado: sin categoría relevante". Cada resultado guarda categoría, fecha y versión de configuración. Estado del proceso "documentos priorizados" (8).

### QA-02: La categoría excluida prevalece

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-05
- **Pasos:**
  1. Revisar el resultado de 600014 en QA-01.
- **Resultado esperado:** "no seleccionado: categoría excluida (póliza o garantía)".

### QA-03: Palabras clave excluidas se comparan como palabra completa

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Nombre | Ruta de entrega - anexo economico.pdf | "ruta" no debe coincidir con "rut" |
  | Nombre | RUT.pdf | Sí coincide con "rut" |

- **Pasos:**
  1. Ejecutar la priorización con ambos documentos.
- **Resultado esperado:** el primero queda en categoría "anexo económico"; el segundo, "categoría excluida (RUT)".

### QA-04: Menos relevantes que el límite no se rellenan con excluidos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proceso | CO1.BDOS.6666666 | 3 relevantes (oferta económica, contrato, estudio previo) y 9 excluidos |

- **Pasos:**
  1. Ejecutar la priorización.
- **Resultado esperado:** 3 seleccionados; los 9 excluidos siguen "no seleccionado: categoría excluida"; estado "documentos priorizados" (3).

### QA-05: Proceso sin documentos relevantes

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Proceso | CO1.BDOS.7777777 | CDP 1.pdf, Poliza.pdf, Certificado bancario.pdf |

- **Pasos:**
  1. Ejecutar la priorización.
- **Resultado esperado:** estado "sin documentos relevantes" con motivo "ningún documento corresponde a las categorías relevantes".

### QA-06: Archivos internos del comprimido desplazan a los de menor prioridad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Internos de 600010 | Cotizacion Alkosto.pdf, Cotizacion proveedor 2.pdf | Categoría cotización (5) |

- **Pasos:**
  1. Registrar los internos como expandidos.
  2. Recalcular la priorización.
- **Resultado esperado:** las dos cotizaciones quedan en posiciones 5 y 6 (tras aceptación de oferta); 600007 y 600008 pasan a "no seleccionado: fuera del límite"; el contenedor 600010 no ocupa cupo.

### QA-07: Máximo de contenedores por proceso

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Comprimidos | 11 archivos .zip ("anexos_1.zip" … "anexos_11.zip") | Misma categoría, fechas distintas |
  | Comprimido excluido | polizas.rar | Categoría excluida |

- **Pasos:**
  1. Ejecutar la priorización.
- **Resultado esperado:** 10 quedan "contenedor por expandir" (los de fecha más reciente); el undécimo queda "no seleccionado: fuera del límite de contenedores"; polizas.rar queda "categoría excluida" y no se expande.

### QA-08: Formulario en blanco libera su cupo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 600003 | marcado "formulario en blanco" | Simulado como entrada de HU-017 |
  | Otros motivos | 600005 "descarga fallida definitiva" | Mismo comportamiento |

- **Pasos:**
  1. Recalcular la priorización tras QA-01 con cada motivo.
- **Resultado esperado:** el documento afectado queda "no seleccionado: {motivo}" y 600009 (y luego el siguiente disponible) ocupa el cupo liberado; siguen seleccionados 8.

### QA-09: Proceso por lotes con lote del televisor determinado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Objeto del contrato | Adquisición de elementos para el LOTE II - televisores | Romano II → 2 |
  | Documentos | Oferta economica lote 1.pdf, Oferta economica lote 2.pdf, Estudio previo.pdf | |

- **Pasos:**
  1. Ejecutar la priorización.
- **Resultado esperado:** "Oferta economica lote 1.pdf" queda "no seleccionado: lote no corresponde al televisor"; los otros dos quedan seleccionados.

### QA-10: Lote no determinable

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Objeto A | Adquisición de equipos audiovisuales | Sin lote |
  | Objeto B | Lote 1 y lote 3 - equipos | Más de un lote |
  | Documentos | Oferta lote 1.pdf, Oferta lote 3.pdf | |

- **Pasos:**
  1. Ejecutar la priorización con el objeto A y luego con el B.
- **Resultado esperado:** en ambos casos ningún documento se descarta por lote y el proceso queda marcado "lote no determinado".

### QA-11: Cambio del límite solo afecta procesos no extraídos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-13
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Límite nuevo | 10 | |
  | CO1.BDOS.1234567 | No extraído | |
  | CO1.BDOS.8888888 | Ya extraído, con 8 seleccionados | |

- **Pasos:**
  1. Cambiar el límite a 10.
  2. Ejecutar la priorización.
- **Resultado esperado:** CO1.BDOS.1234567 queda con 9 seleccionados (los 9 relevantes disponibles); CO1.BDOS.8888888 conserva sus 8 y su versión de configuración anterior.

### QA-12: Límite fuera de rango

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Límite | 0 | mín − 1 |
  | Límite | 1 | mín (válido) |
  | Límite | 50 | máx (válido) |
  | Límite | 51 | máx + 1 |
  | Límite | 7,5 | No entero |
  | Límite | (vacío) | Nulo |

- **Pasos:**
  1. Intentar guardar cada valor.
- **Resultado esperado:** 1 y 50 se guardan; 0, 51, 7,5 y vacío se rechazan con "El número de documentos por proceso debe ser un entero entre 1 y 50" y se conserva el valor anterior.

### QA-13: Normalización de tildes, mayúsculas y uso de la descripción

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-02, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Nombre 1 | EVALUACIÓN_ECONÓMICA-DEFINITIVA.PDF | |
  | Nombre 2 / descripción | doc_17.pdf / "Propuesta económica del adjudicatario" | |

- **Pasos:**
  1. Ejecutar la priorización.
- **Resultado esperado:** el primero en "evaluación económica"; el segundo en "oferta o propuesta económica".

### QA-14: Desempate determinístico con fecha nula

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 700002 | Oferta economica.pdf, fecha 2025-05-01 | |
  | 700001 | Oferta economica v2.pdf, fecha 2025-05-01 | Misma fecha |
  | 700003 | Oferta economica final.pdf, fecha nula | |

- **Pasos:**
  1. Ejecutar la priorización dos veces con la misma configuración.
- **Resultado esperado:** orden 700001, 700002, 700003 en ambas ejecuciones (misma fecha → id ascendente; fecha nula al final).

### QA-15: Registro de cambios de configuración y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-13 / Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar cambiar el límite a 9.
  2. Como `admin.po@piloto.test`, cambiar el límite de 8 a 9.
  3. Consultar el registro de cambios de configuración.
- **Resultado esperado:** el Analista recibe acceso denegado y el límite no cambia; el cambio del Administrador queda registrado con usuario, fecha, valor anterior 8 y valor nuevo 9.

---

**Total de casos:** 15
