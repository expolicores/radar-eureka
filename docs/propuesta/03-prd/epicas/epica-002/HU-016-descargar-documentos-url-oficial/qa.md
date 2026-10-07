# Casos de Prueba — HU-016: Descargar los documentos priorizados desde la URL oficial sin evadir restricciones

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la descarga por URL oficial, el registro del resultado y del hash, los reintentos de fallos temporales, la detección de bloqueos sin evasión, la suspensión por bloqueos repetidos, los límites de tamaño y redirección, la idempotencia, la liberación de cupos y el estado del proceso. Se usa un servidor simulado que replica las respuestas de `community.secop.gov.co`. Queda fuera: la detección de vacíos y duplicados (HU-017) y la conservación de evidencia (HU-021).

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Configuración: dominios permitidos `community.secop.gov.co`; reintentos 3 (esperas 2, 4 y 8 s); tiempo de espera 120 s; tamaño máximo 200 MB; 1 s entre solicitudes; 2 en paralelo; suspensión tras 5 bloqueos consecutivos; User-Agent "SeguimientoComprasPublicas/0.1 (contacto: soporte@piloto.test)".
- Proceso `CO1.BDOS.1234567` con documentos seleccionados 600001–600008 y contenedor 600010; URL base `https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId={id}`.
- Archivo de referencia para 600001: PDF de 245.760 bytes.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01, RN-02, RN-10 | QA-01 |
| RN-03 (identificación, sin evasión) | QA-02, QA-06 |
| Escenario 2 / RN-06 | QA-03 |
| Escenario 3 / RN-06, RN-12 | QA-04 |
| RN-06 (429 con espera del servidor) | QA-05 |
| Escenario 4 / RN-04 | QA-06 |
| Escenario 5 / RN-05 | QA-07 |
| Escenario 6 / RN-07 | QA-08 |
| Escenario 7 / RN-08 | QA-09 |
| Escenario 8 / RN-02 | QA-10 |
| Escenario 9 / RN-11 | QA-11, QA-12 |
| Escenario 10 / RN-13 | QA-13 |
| Escenario 11 / RN-06, RN-10 | QA-14 |
| RN-09 | QA-15 |
| RN-14 / Permisos | QA-16 |

---

## Casos de Prueba

### QA-01: Descarga exitosa con hash y metadatos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-02, RN-10
- **Pasos:**
  1. Ejecutar la descarga documental.
  2. Consultar el resultado de 600001.
- **Resultado esperado:** una solicitud GET a la URL registrada; estado "descargado", tamaño 245.760, tipo de contenido "application/pdf", hash SHA-256 igual al del archivo de referencia, 1 intento, fecha y hora de descarga.

### QA-02: Las solicitudes llevan el User-Agent propio y no envían credenciales

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Pasos:**
  1. Inspeccionar en el servidor simulado las solicitudes recibidas en QA-01.
- **Resultado esperado:** User-Agent "SeguimientoComprasPublicas/0.1 (contacto: soporte@piloto.test)"; sin cabeceras de autorización ni cookies de sesión.

### QA-03: Fallo temporal recuperado

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 600002 | 503 y luego 200 | |

- **Pasos:**
  1. Ejecutar la descarga.
- **Resultado esperado:** "descargado" con 2 intentos (1 reintento) y un único contenido guardado.

### QA-04: Fallo temporal persistente libera el cupo

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-06, RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 600004 | Tiempo de espera en 4 intentos | |
  | 600009 | Siguiente en la priorización | |

- **Pasos:**
  1. Ejecutar la descarga.
- **Resultado esperado:** 4 intentos con esperas de 2, 4 y 8 s; 600004 "descarga fallida definitiva" con último error "tiempo de espera agotado" y 4 intentos; se dispara el recalculo y 600009 pasa a "seleccionado" y se descarga.

### QA-05: Respuesta 429 con espera indicada por el servidor

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Caso A | 429 con espera de 30 s, luego 200 | Se respeta |
  | Caso B | 429 con espera de 900 s | Supera 10 min: se usa la espera exponencial |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** A: segundo intento tras ≥ 30 s y "descargado". B: no se esperan 900 s; se aplican los reintentos con espera exponencial y, si persiste, "descarga fallida definitiva".

### QA-06: Bloqueos no se reintentan ni se evaden

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-03, RN-04
- **Datos de prueba:**

  | Respuesta | Motivo esperado |
  | --------- | --------------- |
  | 403 | acceso denegado |
  | 401 | requiere autenticación |
  | 200 HTML con formulario de CAPTCHA | CAPTCHA detectado |
  | 200 HTML con formulario de usuario y contraseña | requiere autenticación |

- **Pasos:**
  1. Ejecutar la descarga con cada respuesta (una por documento).
- **Resultado esperado:** cada documento queda "descarga bloqueada" con el motivo esperado tras 1 solo intento; no se envía ninguna respuesta al CAPTCHA ni credencial; el Administrador recibe un aviso por cada uno con proceso, documento, URL y motivo.

### QA-07: Suspensión tras 5 bloqueos consecutivos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Caso A | 4 bloqueos consecutivos y luego una descarga exitosa | No suspende |
  | Caso B | 5 bloqueos consecutivos, quedan 12 documentos | Suspende |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** A: la ejecución continúa y el contador se reinicia. B: tras el quinto bloqueo no se hacen más solicitudes; los 12 quedan "pendiente de descarga"; ejecución "suspendida por bloqueos"; aviso al Administrador.

### QA-08: Documento no disponible

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | 600006 | 404 | |
  | 600008 | 410 | |

- **Pasos:**
  1. Ejecutar la descarga.
- **Resultado esperado:** ambos "documento no disponible en la fuente" con 1 intento; se libera su cupo.

### QA-09: Límite de tamaño

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Datos de prueba:**

  | Caso | Tamaño | Resultado esperado |
  | ---- | ------ | ------------------ |
  | Cabecera 200 MB exactos | 209.715.200 bytes | descargado |
  | Cabecera 200 MB + 1 byte | 209.715.201 bytes | excede tamaño máximo, sin solicitud del cuerpo |
  | Sin cabecera, flujo de 250 MB | — | se interrumpe al superar 200 MB, excede tamaño máximo |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** el de la tabla; en los casos excedidos no queda contenido parcial guardado.

### QA-10: Redirecciones

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-02
- **Datos de prueba:**

  | Caso | Redirección | Resultado esperado |
  | ---- | ----------- | ------------------ |
  | A | A `https://community.secop.gov.co/otra/ruta` | se sigue y descarga |
  | B | A `https://descargas.otro-dominio.example/archivo.pdf` | descarga bloqueada: redirección fuera de los dominios permitidos |
  | C | 6 redirecciones encadenadas dentro del dominio | descarga fallida definitiva por exceso de redirecciones |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** el de la tabla.

### QA-11: Documento ya descargado no se repite

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-11
- **Pasos:**
  1. Tras QA-01, ejecutar de nuevo la descarga.
- **Resultado esperado:** el servidor no recibe solicitudes para 600001; su registro no cambia.

### QA-12: Redescarga solicitada con cambio de hash

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-11
- **Pasos:**
  1. Cambiar en el servidor simulado el contenido de 600001.
  2. Como Administrador, solicitar la redescarga de 600001.
- **Resultado esperado:** se descarga de nuevo; se registra el cambio de hash con fecha y se conservan el contenido anterior y el nuevo.

### QA-13: El proceso pasa a "documentos obtenidos"

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-13
- **Datos de prueba:**

  | Caso | Resultado de los 9 archivos |
  | ---- | --------------------------- |
  | A | 8 descargados, 1 no disponible |
  | B | 9 bloqueados o no disponibles |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** A: "documentos obtenidos" con 8 descargados y 1 fallido ("documento no disponible en la fuente"). B: "documentos obtenidos" con 0 descargados y los motivos por documento.

### QA-14: Respuesta vacía y respuesta truncada

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-06, RN-10
- **Datos de prueba:**

  | Caso | Respuesta | Resultado esperado |
  | ---- | --------- | ------------------ |
  | A | 200 con 0 bytes | descargado, tamaño 0 |
  | B | 200 con cabecera 100.000 y 40.000 bytes recibidos, luego completo | descargado al reintento |

- **Pasos:**
  1. Ejecutar la descarga con cada caso.
- **Resultado esperado:** el de la tabla.

### QA-15: Ritmo y paralelismo

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Pasos:**
  1. Descargar los 9 archivos del proceso base registrando la hora de cada solicitud en el servidor simulado.
- **Resultado esperado:** nunca hay más de 2 solicitudes simultáneas y entre inicios de solicitudes consecutivas hay al menos 1 segundo.

### QA-16: Registro de ejecución y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-14 / Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar consultar el registro de ejecución y solicitar una redescarga.
  2. Como `admin.po@piloto.test`, consultar el registro de la ejecución de QA-13 caso A.
- **Resultado esperado:** el Analista recibe acceso denegado; el Administrador ve inicio, fin, estado "completa", 9 intentados, 8 descargados, 1 fallido por "documento no disponible en la fuente" y 0 bloqueos.

---

**Total de casos:** 16
