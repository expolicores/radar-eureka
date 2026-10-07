# Casos de Prueba — HU-018: Descomprimir archivos ZIP y RAR y tratar su contenido como documentos del proceso

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la expansión de ZIP y RAR, el registro de documentos internos con identificador estable, el anidamiento, los límites de seguridad, los protegidos, dañados, vacíos, entradas ignoradas, rutas no válidas, formatos no soportados y la idempotencia. Queda fuera: la evaluación de los archivos internos (HU-017) y su priorización (HU-015), que solo se verifican como disparadas.

## Precondiciones y Datos Base

- Usuario `admin.po@piloto.test` (Administrador); `analista1@piloto.test` (Analista).
- Configuración: profundidad 3; máximo 500 archivos; 1 GB descomprimido; relación 100 a 1.
- Proceso `CO1.BDOS.1234567`; URL del comprimido 600010: `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=600010`; fecha de carga 2025-02-12.
- Comprimidos de prueba construidos para cada caso (archivos ficticios sin datos personales).

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03, RN-04, RN-12 | QA-01 |
| Escenario 2 / RN-01 | QA-02, QA-03 |
| Escenario 3 / RN-03, RN-05 | QA-04 |
| Escenario 4 / RN-05 | QA-05 |
| Escenario 5 / RN-07 | QA-06 |
| Escenario 6 / RN-08 | QA-07 |
| Escenario 7 / RN-06 | QA-08 |
| Escenario 8 / RN-09, RN-10 | QA-09, QA-10 |
| Escenario 9 / RN-11 | QA-11 |
| Escenario 10 / RN-02 | QA-12 |
| Escenario 11 / RN-13 | QA-13 |
| Permisos | QA-14 |

---

## Casos de Prueba

### QA-01: Expansión de ZIP con tres archivos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-04, RN-12
- **Datos de prueba:**

  | Entrada | Tamaño |
  | ------- | ------ |
  | Cotizacion Alkosto.pdf | 180.000 bytes |
  | Cotizacion proveedor 2.pdf | 210.000 bytes |
  | Anexo/precios.xlsx | 25.000 bytes |

- **Pasos:**
  1. Ejecutar la expansión de 600010.
- **Resultado esperado:** 3 documentos internos con identificadores `600010::Cotizacion Alkosto.pdf`, `600010::Cotizacion proveedor 2.pdf`, `600010::Anexo/precios.xlsx`, con nombre, ruta, extensión, tamaño, hash, comprimido de origen 600010, fecha de carga 2025-02-12 y la URL de 600010; comprimido "expandido"; se disparan la evaluación de HU-017 y el recalculo de la priorización.

### QA-02: Expansión de RAR 4 y RAR 5

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-01
- **Pasos:**
  1. Expandir "Propuesta.rar" (RAR 4) y "Propuesta5.rar" (RAR 5), cada uno con "Oferta economica.pdf".
- **Resultado esperado:** en ambos se registra `{id}::Oferta economica.pdf`.

### QA-03: La firma del contenido prevalece sobre la extensión

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Archivo | Contenido real |
  | ------- | -------------- |
  | anexos.pdf | ZIP válido |
  | anexos.zip | PDF |

- **Pasos:**
  1. Ejecutar la expansión con ambos marcados "contenedor por expandir".
- **Resultado esperado:** "anexos.pdf" se expande como ZIP; "anexos.zip" no se expande (no es comprimido) y se devuelve como documento normal a la priorización.

### QA-04: Comprimido anidado dentro de la profundidad

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-03, RN-05
- **Pasos:**
  1. Expandir 700100 "Sobre2.zip" → "Economico.zip" → "Oferta.pdf".
- **Resultado esperado:** `700100::Economico.zip` registrado como contenedor interno expandido y `700100::Economico.zip/Oferta.pdf` como documento interno.

### QA-05: Profundidad máxima superada

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-05
- **Datos de prueba:**

  | Nivel | Archivo |
  | ----- | ------- |
  | 1 | N1.zip (publicado) |
  | 2 | N2.zip + a.pdf |
  | 3 | N3.zip + b.pdf |
  | 4 | N4.zip + c.pdf |

- **Pasos:**
  1. Expandir N1.zip.
- **Resultado esperado:** se registran a.pdf y b.pdf; N4.zip queda "no expandido: profundidad máxima superada"; c.pdf no se registra; N1.zip "expandido parcialmente".

### QA-06: Comprimido protegido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Pasos:**
  1. Expandir 600031 "Oferta.zip", protegido con contraseña.
- **Resultado esperado:** "no elegible: archivo protegido" sin ningún intento de contraseña; se recalcula la priorización.

### QA-07: Comprimido parcial o totalmente dañado

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-08
- **Datos de prueba:**

  | Caso | Entradas | Resultado esperado |
  | ---- | -------- | ------------------ |
  | A | 5, de las cuales 2 dañadas | 3 registradas, 2 "archivo interno dañado", "expandido parcialmente" |
  | B | Archivo corrupto sin entradas legibles | "no elegible: archivo dañado" |

- **Pasos:**
  1. Expandir cada caso.
- **Resultado esperado:** el de la tabla.

### QA-08: Límites de seguridad

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06
- **Datos de prueba:**

  | Caso | Contenido | Resultado esperado |
  | ---- | --------- | ------------------ |
  | A | 500 archivos | expandido (500 registrados) |
  | B | 501 archivos | 500 registrados, "expandido parcialmente: límite de archivos superado" |
  | C | Entradas que suman 1,2 GB descomprimidos | se detiene al superar 1 GB, "límite de tamaño descomprimido superado" |
  | D | Entrada de 1 MB comprimido que declara 500 MB | "relación de compresión anómala" |

- **Pasos:**
  1. Expandir cada caso.
- **Resultado esperado:** el de la tabla; en ningún caso se guarda una entrada que supere los límites.

### QA-09: Entradas de sistema ignoradas

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Datos de prueba:**

  | Entrada | Esperado |
  | ------- | -------- |
  | __MACOSX/._oferta.pdf | ignorada |
  | .DS_Store | ignorada |
  | Thumbs.db | ignorada |
  | desktop.ini | ignorada |
  | Carpeta vacía "Soportes/" | ignorada |
  | Carpeta "Economico/" con "oferta.pdf" | se registra `{id}::Economico/oferta.pdf` |

- **Pasos:**
  1. Expandir el ZIP.
- **Resultado esperado:** el de la tabla.

### QA-10: Rutas no válidas no escriben fuera del espacio de trabajo

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-10
- **Datos de prueba:**

  | Entrada |
  | ------- |
  | ../../config.txt |
  | /etc/archivo.txt |
  | C:\temp\archivo.txt |

- **Pasos:**
  1. Expandir el ZIP.
  2. Verificar el sistema de archivos fuera del espacio de trabajo.
- **Resultado esperado:** las tres entradas anotadas "ruta no válida", no registradas como documentos; no se creó ningún archivo fuera del espacio de trabajo.

### QA-11: Comprimido sin archivos

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9 / RN-11
- **Pasos:**
  1. Expandir 600033, ZIP válido sin entradas.
- **Resultado esperado:** "expandido" con 0 documentos internos y anotación "comprimido sin archivos".

### QA-12: Formatos comprimidos no soportados

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-02
- **Datos de prueba:**

  | Archivo |
  | ------- |
  | Anexos.7z |
  | Anexos.tar.gz |

- **Pasos:**
  1. Ejecutar la expansión.
- **Resultado esperado:** ambos "no elegible: formato de comprimido no soportado"; se recalcula la priorización.

### QA-13: Reejecución sin duplicados y reexpansión solicitada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-13
- **Pasos:**
  1. Tras QA-01, ejecutar de nuevo la expansión.
  2. Como Administrador, solicitar la reexpansión de 600010.
- **Resultado esperado:** en el paso 1 no se procesa el comprimido; en el paso 2 se expande de nuevo y siguen existiendo exactamente 3 documentos internos con los mismos identificadores.

### QA-14: Permisos

- **Tipo:** Permisos
- **Prioridad:** Baja
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar consultar los documentos internos de 600010 y solicitar una reexpansión.
- **Resultado esperado:** acceso denegado en ambas operaciones.

---

**Total de casos:** 14
