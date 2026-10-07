# Casos de Prueba — HU-002: Carga incremental periódica de contratos SECOP II

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la carga incremental de SECOP II: requisito de carga inicial previa, marca de agua y solape, consulta principal y de seguimiento, clasificación de cada registro (nuevo, actualizado, sin cambios), retorno a "Pendiente de marcación", rechazos, reintentos, programación y exclusión mutua, y la separación respecto a la extracción con IA.

Queda fuera: la marcación de candidatos (HU-008), la bitácora detallada (HU-006) y la verificación global de datos sensibles (HU-007). Los campos sensibles se verifican aquí solo en lo que escribe esta carga.

## Precondiciones y Datos Base

- Usuario Administrador: `admin.po@piloto.test`.
- Carga inicial "Exitosa" ejecutada el 2026-10-01 con marca de agua 2026-10-01T02:00:00 (America/Bogota).
- Configuración: frecuencia 24 h a las 02:00; solape 24 h; `fecha_inicio_historico = 2023-01-01`; términos "TELEVISOR", "SMART TV", "TV"; lote de seguimiento 100; 3 reintentos (2, 4, 8 s).
- Contratos guardados:

  | id_contrato | objeto | unspsc_principal | estado_contrato | ultima_actualizacion_fuente | Clasificación |
  |---|---|---|---|---|---|
  | CO1.PCCNTR.5000001 | Adquisición de televisores 65 pulgadas | V1.52161505 | En ejecución | 2026-09-30T11:00:00 | Incluido |
  | CO1.PCCNTR.5000002 | Compra de 52 equipos de cómputo y 1 smart tv | V1.43211500 | Firmado | 2025-07-05T08:30:00 | Incluido |
  | CO1.PCCNTR.5000004 | Dotación de televisor para sala de juntas | V1.52161505 | Firmado | 2026-09-30T20:00:00 | Requiere revisión |

- CO1.PCCNTR.5000001 tiene 3 documentos descargados y 2 ítems extraídos con IA.
- API simulada con capacidad de inyectar fallas y registrar las consultas recibidas.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03, RN-05, RN-10 | QA-01 |
| Escenario 2 / RN-08 | QA-02 |
| Escenario 3 / RN-08 | QA-03 |
| Escenario 4 / RN-08 | QA-04 |
| Escenario 5 / RN-06, RN-16 | QA-05 |
| Escenario 6 / RN-02 | QA-06 |
| Escenario 7 / RN-03, RN-12 | QA-07 |
| Escenario 8 / RN-04 | QA-08 |
| Escenario 9 / RN-14 | QA-09 |
| Escenario 10 / RN-03 | QA-10 |
| Escenario 11 / RN-15 | QA-11 |
| Escenario 12 / RN-13 | QA-12 |
| Escenario 13 / RN-18 | QA-13 |
| RN-07 | QA-14 |
| RN-09 | QA-15 |
| RN-12 (error no recuperable) | QA-16 |
| RN-17 | QA-14 |

---

## Casos de Prueba

### QA-01: Incremental programada guarda contratos nuevos y avanza la marca de agua

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-05, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.6000001.ultima_actualizacion | 2026-10-01T15:20:00 | nuevo |
  | CO1.PCCNTR.6000002.ultima_actualizacion | 2026-10-01T22:45:00 | nuevo, máximo |

- **Pasos:**
  1. Avanzar el reloj a 2026-10-02T02:00 y dejar correr la programación.
  2. Revisar la consulta enviada y los contratos.
- **Resultado esperado:** la consulta pide `ultima_actualizacion` > 2026-09-30T02:00:00, `fecha_de_firma` ≥ 2023-01-01 y el prefiltro. Los 2 contratos quedan "Nuevo", candidatura "Pendiente de marcación", con `fecha_corte`, `fecha_ingesta` e `id_ejecucion`. Estado "Exitosa". Marca de agua = 2026-10-01T22:45:00.

### QA-02: Cambio de objeto devuelve la candidatura a pendiente sin tocar la clasificación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000001.objeto | Adquisición de televisores 65 y 75 pulgadas | cambió |
  | ultima_actualizacion | 2026-10-01T10:00:00 | |

- **Pasos:**
  1. Ejecutar la incremental.
- **Resultado esperado:** "Actualizado"; `actualizado_en_fuente = sí`; `fecha_actualizacion_detectada` = fecha de la ejecución; candidatura "Pendiente de marcación"; clasificación "Incluido", documentos e ítems sin cambios.

### QA-03: Cambio en campos no relevantes para la candidatura

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000002.estado_contrato | Terminado | antes "Firmado" |
  | CO1.PCCNTR.5000004.fecha_de_fin_del_contrato | 2026-12-31 | antes nula |

- **Pasos:**
  1. Ejecutar la incremental.
- **Resultado esperado:** ambos "Actualizado" con `actualizado_en_fuente = sí`; la candidatura y la clasificación de cada uno se mantienen.

### QA-04: Nueva fecha de actualización sin cambios en campos permitidos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-08
- **Pasos:**
  1. Devolver CO1.PCCNTR.5000004 idéntico salvo `ultima_actualizacion = 2026-10-01T09:00:00` y un campo no permitido cambiado (`nombre_del_banco`).
  2. Ejecutar la incremental.
- **Resultado esperado:** "Sin cambios"; solo cambian `ultima_actualizacion_fuente`, `fecha_corte` e `id_ejecucion`; `actualizado_en_fuente` no se marca; el campo no permitido no se persiste.

### QA-05: Contrato que deja de cumplir el prefiltro se actualiza por seguimiento

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06, RN-16
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000004.objeto | Dotación de mobiliario para sala de juntas | sin términos |
  | CO1.PCCNTR.5000004.unspsc_principal | V1.56101700 | ya no es 52161505 |

- **Pasos:**
  1. Ejecutar la incremental; la consulta principal no lo devuelve y la de seguimiento sí.
- **Resultado esperado:** el contrato se procesa una sola vez, queda "Actualizado" con candidatura "Pendiente de marcación" y sigue existiendo en la base.

### QA-06: Incremental sin carga inicial exitosa se omite

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-02
- **Precondiciones:** base sin ejecuciones "Exitosa" de carga inicial (solo una "Fallida").
- **Pasos:**
  1. Ejecutar la incremental manual y luego dejar correr la programada.
- **Resultado esperado:** ambas se registran "Omitida"; la API no recibe solicitudes; mensaje "No existe una carga inicial exitosa de SECOP II. Ejecute primero la carga inicial."

### QA-07: Falla persistente no avanza la marca de agua y la siguiente recupera sin duplicar

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-03, RN-12
- **Precondiciones:** API con 1.500 contratos modificados (2 páginas).
- **Pasos:**
  1. Inyectar HTTP 503 permanente en la página 2 y ejecutar.
  2. Quitar la falla y ejecutar de nuevo.
- **Resultado esperado:** (1) 4 intentos sobre la página 2, estado "Fallida", marca de agua sigue en 2026-10-01T02:00:00, 1.000 contratos escritos. (2) La consulta usa la misma marca de agua; al final hay 1.500 contratos sin duplicados; los 1.000 previos cuentan "Sin cambios".

### QA-08: Registros del solape no se duplican

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000004.ultima_actualizacion | 2026-09-30T20:00:00 | dentro del solape, igual a la guardada |
  | Solape | 0 h | valor límite inferior |
  | Solape | 168 h | valor límite superior |
  | Solape | 169 h | fuera de rango → configuración rechazada |

- **Pasos:**
  1. Ejecutar con solape 24 h.
  2. Configurar cada valor de solape.
- **Resultado esperado:** (1) CO1.PCCNTR.5000004 cuenta "Sin cambios" y no se duplica. (2) 0 y 168 se aceptan (la consulta usa marca de agua − 0 h y − 168 h); 169 se rechaza y se conserva el valor anterior.

### QA-09: Programada omitida por ejecución en curso

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9 / RN-14
- **Pasos:**
  1. Iniciar una incremental manual con la API en pausa.
  2. Llegar a la hora programada.
  3. Intentar otra ejecución manual.
- **Resultado esperado:** la programada queda "Omitida" con "Ejecución en curso: {id_ejecucion}"; la manual se rechaza con "Ya existe una carga en curso para SECOP II (ejecución {id_ejecucion}). Espere a que termine."

### QA-10: Sin cambios en la fuente

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 10 / RN-03
- **Pasos:**
  1. API sin registros modificados; ejecutar la incremental.
- **Resultado esperado:** "Exitosa", contadores en 0 y marca de agua sin cambios.

### QA-11: La actualización no crea solicitudes de descarga ni de extracción con IA

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-15
- **Pasos:**
  1. Ejecutar la incremental con la modificación de QA-02.
  2. Revisar las solicitudes de descarga de documentos y de extracción con IA, y los ítems de CO1.PCCNTR.5000001.
- **Resultado esperado:** 0 solicitudes nuevas de descarga y de extracción; los 2 ítems extraídos y los 3 documentos quedan iguales.

### QA-12: Validación del cambio de frecuencia

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-13
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Frecuencia | 1 | mínimo → aceptado |
  | Frecuencia | 168 | máximo → aceptado |
  | Frecuencia | 12 | aceptado |
  | Frecuencia | 0 | mín − 1 → rechazado |
  | Frecuencia | 169 | máx + 1 → rechazado |
  | Frecuencia | 6.5 | no entero → rechazado |
  | Frecuencia | (vacío) | rechazado |

- **Pasos:**
  1. Configurar cada valor.
- **Resultado esperado:** los aceptados reprograman la siguiente ejecución (con 12: 14:00 si la anterior fue a las 02:00); los rechazados muestran "La frecuencia de ingesta debe ser un número entero de horas entre 1 y 168" y se conserva el valor anterior.

### QA-13: Ejecución manual con las mismas reglas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 13 / RN-18
- **Pasos:**
  1. Ejecutar por comando la incremental a las 10:00 del 2026-10-02.
- **Resultado esperado:** ejecución de tipo "Incremental manual" con las reglas de QA-01; la siguiente programada sigue en 2026-10-03T02:00.

### QA-14: Lista blanca y app token en la incremental

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-07, RN-17
- **Pasos:**
  1. Devolver CO1.PCCNTR.6000001 con `n_mero_de_cuenta = 000123456789` e `identificaci_n_representante_legal = 99999999`, con el token configurado.
  2. Repetir sin token.
- **Resultado esperado:** los valores sensibles no aparecen en base de datos ni logs; el token no aparece en logs; sin token, la carga se completa con la advertencia "Ejecución sin app token: la API puede aplicar límites más estrictos".

### QA-15: Rechazos no borran la versión guardada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000002.fecha_de_firma | (nulo) | contrato existente |
  | Nuevo registro id_contrato | "" | |
  | CO1.PCCNTR.6000003.fecha_de_firma | 2022-11-30 | fuera de ventana |

- **Pasos:**
  1. Ejecutar la incremental.
- **Resultado esperado:** los 3 se cuentan como rechazados con "Fecha de firma ausente", "Identificador de origen ausente" y "Fecha de firma fuera de la ventana histórica"; CO1.PCCNTR.5000002 conserva su versión anterior; CO1.PCCNTR.6000003 no se crea.

### QA-16: Error no recuperable en la incremental

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-12
- **Pasos:**
  1. Responder HTTP 403 a la primera consulta.
- **Resultado esperado:** un solo intento, "Fallida", marca de agua sin cambios.

---

**Total de casos:** 16
