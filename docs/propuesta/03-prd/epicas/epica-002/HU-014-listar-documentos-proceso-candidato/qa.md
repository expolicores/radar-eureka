# Casos de Prueba — HU-014: Listar y registrar los documentos publicados de cada proceso candidato

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la obtención de la lista de documentos de los procesos candidatos desde los datasets oficiales de Archivos Descarga, su registro con identificador estable, la no duplicación, el manejo de nulos y URLs no válidas, la paginación, la tolerancia a fallas de la API y el registro de ejecución. Queda fuera: la descarga de archivos (HU-016), la priorización (HU-015) y la clasificación de candidatos (épica de universo de compras).

## Precondiciones y Datos Base

- Usuario `admin.po@piloto.test` con rol Administrador; usuario `analista1@piloto.test` con rol Analista.
- Datasets configurados en el orden: `dmgg-8hin`, `nbae-kzan`, `3skv-9na7`, `kgcd-kt7i`, `f8va-cf4m`. Reintentos: 3. Tamaño de página: 1.000 (se reduce a 100 solo en QA-10). Dominios permitidos: `community.secop.gov.co`.
- Contratos base (ya ingeridos):

  | id_contrato | proceso_de_compra | Clasificación | Fecha de firma |
  | ----------- | ----------------- | ------------- | -------------- |
  | CO1.PCCNTR.7654321 | CO1.BDOS.1234567 | incluido | 2025-03-14 |
  | CO1.PCCNTR.2222000 | CO1.BDOS.2222222 | incluido | 2026-09-29 |
  | CO1.PCCNTR.3333333 | CO1.BDOS.3333333 | excluido | 2024-06-10 |
  | CO1.PCCNTR.5555555 | CO1.BDOS.5555555 | requiere revisión | 2024-11-02 |
  | CO1.PCCNTR.4444000 | CO1.BDOS.4444444 | incluido | 2023-08-21 |

- URL de ejemplo válida: `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=500101`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04, RN-13 | QA-01 |
| Escenario 2 / RN-02, RN-03, RN-05 | QA-02, QA-03 |
| Escenario 3 / RN-08 | QA-04 |
| Escenario 4 / RN-01 | QA-05 |
| Escenario 5 / RN-01 | QA-06 |
| RN-01 (requiere revisión) | QA-07 |
| Escenario 6 / RN-05, RN-09 | QA-08, QA-09 |
| Escenario 7 / RN-06 | QA-11, QA-12 |
| Escenario 8 / RN-07 | QA-13 |
| Escenario 9 / RN-11 | QA-14, QA-15 |
| Escenario 10 / RN-12 | QA-10 |
| Escenario 11 / RN-14 | QA-16 |
| RN-15 | QA-17 |
| RN-16 | QA-01 |
| Permisos | QA-18 |

---

## Casos de Prueba

### QA-01: Listado y registro completo de un proceso candidato incluido

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04, RN-13, RN-16
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | proceso | CO1.BDOS.1234567 | 23 registros en `dmgg-8hin` |
  | id_documento (ejemplo) | 500101 | nombre "oferta.pdf", extensión "pdf", tamaño 245760, fecha_carga 2025-03-01 |

- **Pasos:**
  1. Ejecutar el listado documental.
  2. Consultar el inventario del proceso `CO1.BDOS.1234567`.
- **Resultado esperado:** 23 documentos registrados, cada uno con id_documento, nombre, descripción, extensión, tamaño, fecha de carga, URL, número de contrato, dataset `dmgg-8hin` y fecha de listado. Estado documental "documentos listados" con conteo 23. No se descargó ningún archivo.

### QA-02: Documentos repartidos en dos datasets anuales

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `nbae-kzan` | 10 documentos del proceso CO1.BDOS.5555555 | Histórico 2024 |
  | `dmgg-8hin` | 6 documentos del mismo proceso | Uno es el 500100, también presente en `nbae-kzan` |
  | proceso en archivo | " co1.bdos.5555555 " | Con espacios y minúsculas |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** 15 documentos distintos registrados para CO1.BDOS.5555555; el valor con espacios y minúsculas se relaciona correctamente con el proceso.

### QA-03: Documento repetido en dos datasets conserva los datos del primero en el orden

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | id_documento | 500100 | En `dmgg-8hin` nombre "anexo_economico.xlsx"; en `nbae-kzan` nombre "anexo economico.xlsx" |

- **Pasos:**
  1. Ejecutar el listado documental.
  2. Consultar el documento 500100.
- **Resultado esperado:** un único registro con nombre "anexo_economico.xlsx" (datos de `dmgg-8hin`, primero en el orden) y datasets de origen `dmgg-8hin` y `nbae-kzan`.

### QA-04: Proceso sin documentos publicados

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-08
- **Pasos:**
  1. Verificar que ningún dataset tiene registros para CO1.BDOS.2222222 y que todas las consultas responden 200.
  2. Ejecutar el listado documental dos veces (dos días seguidos).
- **Resultado esperado:** el proceso queda "sin documentos publicados" con la fecha de verificación de cada día; se consultó en ambas ejecuciones.

### QA-05: Contrato excluido no se lista

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-01
- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** no hay consultas ni documentos registrados para CO1.BDOS.3333333.

### QA-06: Contrato reclasificado de excluido a incluido entra en la siguiente ejecución

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-01
- **Pasos:**
  1. Cambiar la clasificación de CO1.PCCNTR.3333333 a "incluido".
  2. Ejecutar el listado documental.
- **Resultado esperado:** los documentos de CO1.BDOS.3333333 quedan registrados y el proceso pasa a "documentos listados".

### QA-07: Contrato en "requiere revisión" sí se lista

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** los documentos de CO1.BDOS.5555555 (contrato "requiere revisión") quedan registrados.

### QA-08: Reejecución sin duplicados con documentos nuevos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-05, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Documentos ya registrados | 23 | De QA-01 |
  | Documentos en la fuente | 25 | 2 nuevos: 500124 y 500125 |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** 25 documentos en el inventario, sin duplicados; 500124 y 500125 marcados "nuevo" con su fecha; no se dispara ninguna extracción con IA.

### QA-09: Cambio de metadatos conserva historial y no borra documentos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 500101 nombre anterior | oferta.pdf | |
  | 500101 nombre nuevo | oferta_economica.pdf | |
  | 500102 | Ya no aparece en la fuente | |

- **Pasos:**
  1. Ejecutar el listado documental.
  2. Consultar 500101 y 500102.
- **Resultado esperado:** 500101 mantiene el id, muestra "oferta_economica.pdf" y su historial tiene "oferta.pdf" con la fecha del cambio; 500102 sigue registrado, marcado "no publicado en la última verificación".

### QA-10: Paginación de un proceso con 419 documentos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Tamaño de página | 100 | 5 páginas: 100, 100, 100, 100, 19 |
  | proceso | CO1.BDOS.4444444 | 419 documentos |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** 419 documentos registrados; ningún documento de la última página se pierde.

### QA-11: Registro sin URL o sin identificador queda rechazado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Registro A | id_documento 500200, url_descarga_documento vacía | |
  | Registro B | id_documento nulo, URL válida | |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** A queda "rechazado en listado" con motivo "falta URL de descarga"; B con "falta identificador del documento"; ninguno pasa a priorización; ambos cuentan como rechazados en el registro de ejecución.

### QA-12: Nulos no obligatorios se completan según la regla

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | nombre_archivo | (vacío) | Esperado "(sin nombre)" |
  | extensión vacía, nombre "Cotizacion.XLSX" | — | Esperado "xlsx" |
  | extensión vacía, nombre "documento" | — | Esperado "desconocida" |
  | fecha_carga | "31/02/2025" | Esperado nulo con advertencia |
  | tamanno_archivo | "N/D" | Esperado nulo |

- **Pasos:**
  1. Ejecutar el listado documental con cada registro.
- **Resultado esperado:** cada documento queda registrado (no rechazado) con el valor esperado de la columna Nota; la fecha inválida muestra la advertencia "fecha de carga no válida".

### QA-13: URL fuera de dominios permitidos o no válida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | URL 1 | http://otro-sitio.example/archivo.pdf | Motivo "URL fuera de los dominios oficiales permitidos" |
  | URL 2 | /Public/Archive/RetrieveFile/Index?DocumentId=1 | Relativa: motivo "URL no válida" |
  | URL 3 | ftp://community.secop.gov.co/a.pdf | Esquema no permitido: "URL no válida" |
  | URL 4 | http://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=2 | Válida (http permitido) |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** URL 1 a 3 quedan "rechazado en listado" con el motivo indicado y nunca se intentan descargar; URL 4 queda registrada como válida.

### QA-14: Falla persistente de un dataset deja la ejecución parcial sin marcar "sin documentos"

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `nbae-kzan` | Tiempo de espera en intento inicial y 3 reintentos | |
  | Proceso CO1.BDOS.2222222 | Sin registros en los demás datasets | |

- **Pasos:**
  1. Ejecutar el listado documental.
- **Resultado esperado:** 4 intentos a `nbae-kzan` con espera creciente; ejecución "parcial" con dataset y error registrados; CO1.BDOS.2222222 conserva su estado anterior y no queda "sin documentos publicados"; los documentos de los otros datasets sí se registran.

### QA-15: Recuperación en un reintento y falla total

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Caso A | `dmgg-8hin` responde 503 una vez y luego 200 | |
  | Caso B | Los 5 datasets fallan tras 3 reintentos | |

- **Pasos:**
  1. Ejecutar el listado en el caso A y luego en el caso B.
- **Resultado esperado:** A: ejecución "completa" sin documentos duplicados. B: ejecución "fallida", ningún proceso cambia de estado.

### QA-16: Registro de la ejecución con sus contadores

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-14
- **Pasos:**
  1. Tras QA-08, QA-09 y QA-11 (misma ejecución), consultar el registro de ejecuciones como `admin.po@piloto.test`.
- **Resultado esperado:** el registro muestra inicio, fin, estado "completa", procesos consultados, 2 documentos nuevos, 1 actualizado, 2 rechazados y 0 errores.

### QA-17: El app token no aparece en registros ni configuración versionada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-15
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | App token de prueba | TOKEN-PRUEBA-QA-0001 | Ficticio, cargado como secreto |

- **Pasos:**
  1. Ejecutar el listado documental.
  2. Buscar el texto "TOKEN-PRUEBA-QA-0001" en los registros de la ejecución y en la configuración versionada.
- **Resultado esperado:** el texto no aparece en ninguno de ellos y la ejecución se autenticó correctamente.

### QA-18: El Analista no puede consultar el inventario ni el registro de ejecuciones

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar consultar el inventario documental y el registro de ejecuciones.
  2. Repetir como `admin.po@piloto.test`.
- **Resultado esperado:** el Analista recibe acceso denegado; el Administrador obtiene la información.

---

**Total de casos:** 18
