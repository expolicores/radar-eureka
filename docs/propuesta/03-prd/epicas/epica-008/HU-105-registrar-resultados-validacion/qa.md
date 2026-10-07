# Casos de Prueba — HU-105: Generar la plantilla de validación y cargar los resultados verificados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban la generación de la plantilla (contenido, filtros, estado vacío), la carga (validación por fila, compatibilidad de resultados, formatos de valor correcto, veredicto por contrato, filas sin diligenciar o ajenas a la muestra, archivo inválido), el historial, la idempotencia, el estado de validación, la auditoría y los permisos. Queda fuera: el cálculo de KPIs (HU-106, HU-107).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Muestra: lote "D4-4" con 50 contratos (incluye CO1.PCCNTR.4838434 y CO1.PCCNTR.4946355); lote "2026-10-S1" con 3 documentos individuales; 76 ítems de televisor detectados en total.
- Fila semilla `VF-000123`: CO1.PCCNTR.4838434, ítem 1, `tamano_pulgadas`, valor extraído 60, resultado vigente `correcto`.
- Fila `VF-000014`: `precio_unitario`, valor extraído 2483599, sin resultado.
- Fila `VF-000020`: `marca`, valor extraído vacío. Fila `VF-000021`: `marca`, valor extraído "LG".
- Fila `VC-000002`: CO1.PCCNTR.4946355 (comodato).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01, RN-02, RN-03 | QA-01 |
| Escenario 2, RN-10 | QA-02 |
| Escenario 3 | QA-03 |
| Escenario 4, RN-06, RN-08, RN-11 | QA-04 |
| Escenario 5, Escenario 6, RN-04 (tabla de decisión) | QA-05 |
| Escenario 7 | QA-06 |
| RN-05 (formatos y límites de VALOR_CORRECTO) | QA-07 |
| Escenario 8, RN-06 | QA-08 |
| Escenario 9 | QA-09 |
| Escenario 10, RN-03 | QA-10 |
| Escenario 11, RN-07 | QA-11 |
| Escenario 12, RN-07 | QA-12 |
| Escenario 13, RN-06 | QA-13 |
| RN-06 (nota > 500 caracteres) | QA-14 |
| Escenario 14, RN-09 | QA-15 |
| RN-10 (reextracción → requiere revalidar) | QA-16 |
| Escenario 15 | QA-17 |

---

## Casos de Prueba

### QA-01: Plantilla completa con filas críticas siempre presentes

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02, RN-03
- **Pasos:**
  1. Generar la plantilla sin filtros.
- **Resultado esperado:** XLSX con hojas "Validación por campo", "Validación por contrato" e "Instrucciones"; 380 filas críticas (76 × 5) más una por cada otro campo con valor extraído; las filas críticas sin valor tienen `valor_extraido` vacío; 50 filas por contrato; columnas en el orden de RN-02 y RN-03; ids `VF-` y `VC-` de 6 dígitos.

### QA-02: Plantilla filtrada por lote y solo pendientes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Lote | 2026-10-S1, solo pendientes | solo filas sin resultado de los 3 documentos; sin hoja por contrato con filas |
  | Lote | D4-4, solo pendientes | excluye VF-000123 (ya tiene resultado) |
  | Lote | LOTE-X | "El lote 'LOTE-X' no existe en la muestra." |

- **Pasos:**
  1. Generar con cada filtro.
- **Resultado esperado:** el contenido o mensaje indicado; los `id_fila` coinciden con los de QA-01.

### QA-03: Sin filas por validar

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 3
- **Pasos:**
  1. Con la muestra vacía, generar la plantilla.
- **Resultado esperado:** "No hay filas por validar para el filtro indicado."; no se genera archivo.

### QA-04: Carga válida con resumen y auditoría

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-06, RN-08, RN-11
- **Pasos:**
  1. Diligenciar 40 filas por campo y 10 por contrato con resultados válidos; dejar el resto vacío.
  2. Cargar el archivo.
- **Resultado esperado:** "Filas aplicadas: 50. Sin cambios: 0. Sin diligenciar: {resto}. Rechazadas: 0."; cada resultado con usuario y fecha; evento "Carga de resultados de validación" con nombre, hash y conteos.

### QA-05: Compatibilidad entre RESULTADO, valor extraído y VALOR_CORRECTO

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, Escenario 6, RN-04
- **Datos de prueba:**

  | valor_extraido | RESULTADO | VALOR_CORRECTO | Resultado esperado |
  | ----- | ----- | ----- | ----- |
  | 2483599 | correcto | (vacío) | aplicada |
  | 2483599 | incorrecto | (vacío) | "Fila {n}: el resultado 'incorrecto' exige VALOR_CORRECTO." |
  | 2483599 | incorrecto | 2438599 | aplicada |
  | (vacío) | omitido | Samsung | aplicada |
  | (vacío) | omitido | (vacío) | "Fila {n}: el resultado 'omitido' exige VALOR_CORRECTO." |
  | (vacío) | ausente_y_no_extraido | (vacío) | aplicada |
  | (vacío) | ausente_y_no_extraido | LG | "Fila {n}: con el resultado 'ausente_y_no_extraido', VALOR_CORRECTO debe quedar vacío." |
  | LG | inventado | (vacío) | aplicada |
  | (vacío) | correcto | — | "Fila {n}: el resultado 'correcto' no es compatible con un valor extraído vacío." |
  | LG | ausente_y_no_extraido | — | "Fila {n}: el resultado 'ausente_y_no_extraido' no es compatible con un valor extraído no vacío." |
  | (vacío) / LG | no_verificable | (cualquiera) | aplicada |

- **Pasos:**
  1. Cargar un archivo con una fila por combinación.
- **Resultado esperado:** cada fila con el resultado indicado; las válidas se aplican aunque haya rechazadas.

### QA-06: Resultado no reconocido y mayúsculas

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | RESULTADO | bien | rechazada |
  | RESULTADO | CORRECTO | aceptada |

- **Pasos:**
  1. Cargar ambas filas.
- **Resultado esperado:** "Fila {n}: el resultado 'bien' no es válido. Valores permitidos: correcto, incorrecto, omitido, ausente_y_no_extraido, inventado, no_verificable."; la segunda se aplica.

### QA-07: Formatos y límites de VALOR_CORRECTO

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | tamano_pulgadas | 10 / 120 / 54,6 | válidos |
  | tamano_pulgadas | 9 / 121 / sesenta | inválidos |
  | cantidad | 1 / 100000 | válidos |
  | cantidad | 0 / 100001 / 2,5 | inválidos |
  | precio_unitario | $ 2.974.255 | válido → 2974255 |
  | precio_unitario | 0 / 1000000001 | inválidos |
  | marca | texto de 100 / 101 caracteres | válido / inválido |

- **Pasos:**
  1. Cargar filas `incorrecto` con cada VALOR_CORRECTO.
- **Resultado esperado:** válidos aplicados con el valor normalizado; inválidos rechazados con "Fila {n}: VALOR_CORRECTO '{v}' no es válido para el campo {campo}."

### QA-08: Fila sin diligenciar no borra un resultado previo

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. Cargar un archivo donde VF-000123 tiene RESULTADO vacío.
- **Resultado esperado:** VF-000123 sigue `correcto`; se cuenta como "sin diligenciar".

### QA-09: Fila ajena a la muestra

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | id_fila | VF-999999 | inexistente |
  | id_fila | fila de un documento retirado de la muestra | retirado |

- **Pasos:**
  1. Cargar ambas filas diligenciadas.
- **Resultado esperado:** "Fila {n}: la fila '{id_fila}' no corresponde a un elemento vigente de la muestra." para cada una.

### QA-10: Veredicto por contrato

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-03
- **Datos de prueba:**

  | ES_COMPRA_TV_EN_CATEGORIA | EXISTE_INFO_MINIMA | Resultado esperado |
  | ----- | ----- | ----- |
  | no | si | rechazada con el mensaje del Escenario 10 |
  | no | (vacío) | aplicada |
  | Sí | no | aplicada (tilde y mayúscula aceptadas) |
  | si | tal vez | "Fila {n}: 'tal vez' no es un valor permitido en EXISTE_INFO_MINIMA; use 'si' o 'no'." |

- **Pasos:**
  1. Cargar VC-000002 con cada combinación.
- **Resultado esperado:** el resultado indicado.

### QA-11: Nuevo resultado conserva el anterior en historial

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11, RN-07
- **Pasos:**
  1. Cargar VF-000123 con `incorrecto` y VALOR_CORRECTO 55.
- **Resultado esperado:** vigente `incorrecto` / 55; historial con `correcto`, usuario y fecha previos; cuenta como aplicada.

### QA-12: Recargar el mismo archivo es idempotente

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-07
- **Pasos:**
  1. Cargar el archivo de QA-04 por segunda vez.
- **Resultado esperado:** "Filas aplicadas: 0. Sin cambios: 50. Sin diligenciar: {resto}. Rechazadas: 0."; no se crea historial.

### QA-13: Archivos inválidos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 13, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Archivo | validacion.pdf | "Formato no soportado: use XLSX o CSV con la estructura de la plantilla." |
  | Archivo | XLSX de 10,5 MB | "El archivo supera el tamaño máximo de 10 MB." |
  | Archivo | XLSX sin la columna RESULTADO | "Faltan columnas obligatorias: RESULTADO." |
  | Archivo | XLSX solo con encabezados | "El archivo no contiene filas de datos." |

- **Pasos:**
  1. Cargar cada archivo.
- **Resultado esperado:** el mensaje indicado; no se aplica ninguna fila.

### QA-14: Nota truncada con aviso

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Pasos:**
  1. Cargar una fila válida con NOTA de 520 caracteres.
- **Resultado esperado:** fila aplicada con la nota truncada a 500 caracteres y aviso "Fila {n}: la nota se truncó a 500 caracteres."

### QA-15: Estado de validación parcial y completa

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 14, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Contrato | CO1.PCCNTR.4838434 con 12 filas por campo | 7 con resultado, sin veredicto → parcial |
  | Contrato | mismo, 12 filas y veredicto completo | completa |
  | Contrato | CO1.PCCNTR.4946355, 0 filas por campo, ES_COMPRA = no | completa |

- **Pasos:**
  1. Cargar resultados en cada estado y consultar el estado del elemento.
- **Resultado esperado:** el estado indicado.

### QA-16: Reextracción de un documento deja la fila para revalidar

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Reprocesar el documento de VF-000123 de modo que el valor extraído pase de 60 a 65.
  2. Generar la plantilla "solo pendientes".
- **Resultado esperado:** VF-000123 conserva su id, muestra 65, su resultado previo pasa al historial con estado "requiere revalidar" y aparece en la plantilla de pendientes.

### QA-17: Analista sin acceso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 15
- **Pasos:**
  1. Como `analista1@prueba.co`, generar y cargar la plantilla.
- **Resultado esperado:** "Acción no permitida: esta operación requiere el rol Administrador." en ambas; nada cambia.

---

**Total de casos:** 17
