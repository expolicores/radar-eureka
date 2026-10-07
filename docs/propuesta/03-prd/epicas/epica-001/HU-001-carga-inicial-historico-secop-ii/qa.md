# Casos de Prueba — HU-001: Carga inicial del histórico de contratos SECOP II

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la carga inicial de contratos SECOP II desde la API de datos.gov.co: ventana histórica, prefiltro, lista blanca de campos, descarte de campos sensibles, trazabilidad (identificador, URL, fecha de corte), idempotencia, reintentos, errores no recuperables, exclusión mutua, ejecución sin token y fuente vacía.

Queda fuera: la marcación precisa de candidatos (HU-008), las validaciones de calidad generales (HU-005), la carga incremental (HU-002) y la verificación automática de ausencia de datos sensibles en todas las capas (HU-007).

## Precondiciones y Datos Base

- Usuario de operación con rol Administrador: `admin.po@piloto.test`.
- Configuración base: `fecha_inicio_historico = 2023-01-01`; dataset `jbjy-vk9h`; términos "TELEVISOR", "SMART TV", "TV"; página de 1.000 registros; 3 reintentos (2, 4, 8 s); tiempo de espera 60 s.
- Fecha de ejecución de referencia: 2026-10-02.
- API simulada (doble de prueba) que devuelve los contratos semilla y permite inyectar fallas.
- Contratos semilla:

  | id_contrato | fecha_de_firma | objeto_del_contrato | codigo_de_categoria_principal | urlproceso | ultima_actualizacion |
  |---|---|---|---|---|---|
  | CO1.PCCNTR.5000001 | 2024-03-15 | Adquisición de televisores 65 pulgadas | V1.52161505 | https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.1001 | 2024-03-20T10:00:00 |
  | CO1.PCCNTR.5000002 | 2025-07-01 | Compra de 52 equipos de cómputo y 1 smart tv | V1.43211500 | https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.1002 | 2025-07-05T08:30:00 |
  | CO1.PCCNTR.5000003 | 2023-01-01 | Suministro de televisor LED 43" | V1.52161505 | (nulo) | 2023-01-10T09:00:00 |

- Cada contrato semilla incluye además los campos sensibles simulados: `nombre_del_banco = Banco Ficticio S.A.`, `tipo_de_cuenta = Ahorros`, `n_mero_de_cuenta = 000123456789`, `identificaci_n_representante_legal = 99999999`, `n_mero_de_documento_supervisor = 88888888`, `n_mero_de_documento_ordenador_del_gasto = 77777777`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01, RN-03, RN-04, RN-09, RN-15, RN-16 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / RN-05 | QA-03 |
| Escenario 4 / RN-02, RN-11 | QA-04 |
| Escenario 5 / RN-11 | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-08 | QA-07 |
| Escenario 8 / RN-12 | QA-08 |
| Escenario 9 / RN-12, RN-10 | QA-09 |
| Escenario 10 / RN-12 | QA-10 |
| Escenario 11 / RN-10 | QA-11 |
| Escenario 12 / RN-14 | QA-12, QA-13 |
| Escenario 13 / RN-13 | QA-14 |
| Escenario 14 | QA-15 |
| RN-06, RN-07 (URL como objeto) | QA-16 |
| RN-11 (formato de fecha inválido) | QA-04 |

---

## Casos de Prueba

### QA-01: Carga inicial exitosa con trazabilidad completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01, RN-03, RN-04, RN-09, RN-15, RN-16
- **Pasos:**
  1. Ejecutar el comando de carga inicial de SECOP II con la configuración base y los 3 contratos semilla.
  2. Consultar los contratos guardados.
- **Resultado esperado:** 3 contratos guardados con `id_contrato`, `proceso_de_compra`, `url_publica` (nula en CO1.PCCNTR.5000003), `fecha_corte`, `fecha_ingesta`, `id_ejecucion` y candidatura "Pendiente de marcación". La consulta enviada a la API incluye el filtro de UNSPSC `V1.52161505` o los términos configurados y la ventana desde 2023-01-01. Resumen: "Carga inicial SECOP II finalizada. Leídos: 3. Nuevos: 3. Actualizados: 0. Sin cambios: 0. Rechazados: 0." Estado "Exitosa". No se descargó ningún documento ni se invocó extracción.

### QA-02: Los campos sensibles no se persisten en ninguna capa

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04
- **Pasos:**
  1. Ejecutar la carga con los contratos semilla (que traen los 6 campos sensibles simulados).
  2. Buscar los valores `Banco Ficticio S.A.`, `000123456789`, `99999999`, `88888888` y `77777777` en la base de datos, los logs de la ejecución, los registros de rechazo y los archivos temporales.
- **Resultado esperado:** ninguna coincidencia. Los contratos guardados solo tienen las columnas de la lista blanca.

### QA-03: Configuración con campo prohibido impide iniciar

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Campo agregado a la lista blanca | `nombre_del_banco` | coincide con "banco" |
  | Campo agregado a la lista blanca | `Identificación_Representante_Legal` | coincide con tildes y mayúsculas |

- **Pasos:**
  1. Agregar el campo a la lista blanca (una fila por ejecución).
  2. Ejecutar la carga.
- **Resultado esperado:** la carga no inicia, la API no recibe solicitudes y se muestra "La lista de campos permitidos contiene un campo prohibido: {campo}. Corrija la configuración antes de ejecutar la carga."

### QA-04: Rechazo por fecha de firma ausente, inválida o fuera de ventana

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-02, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | fecha_de_firma | 2023-01-01 | límite inferior → se carga (CO1.PCCNTR.5000003) |
  | fecha_de_firma | 2022-12-31 | mín − 1 → "Fecha de firma fuera de la ventana histórica" |
  | fecha_de_firma | 2026-10-02 | fecha de ejecución → se carga |
  | fecha_de_firma | 2026-10-03 | futuro → "Fecha de firma fuera de la ventana histórica" |
  | fecha_de_firma | (nulo) | "Fecha de firma ausente" |
  | fecha_de_firma | 15/03/2024 | "Fecha de firma con formato inválido" |

- **Pasos:**
  1. Ejecutar la carga con un contrato por cada valor (ids CO1.PCCNTR.5100001 a 5100006).
- **Resultado esperado:** se cargan solo los de 2023-01-01 y 2026-10-02; los demás se cuentan como rechazados con el motivo indicado, registrados con id de ejecución, id_contrato, campo y valor recibido, y la carga continúa.

### QA-05: Rechazo por identificador de origen ausente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | id_contrato | (nulo) | |
  | id_contrato | "" | cadena vacía |

- **Pasos:**
  1. Ejecutar la carga con los dos registros más un contrato válido.
- **Resultado esperado:** solo se guarda el contrato válido; los dos se cuentan como rechazados con el motivo "Identificador de origen ausente".

### QA-06: Contrato sin URL pública se carga con advertencia

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Pasos:**
  1. Ejecutar la carga con CO1.PCCNTR.5000003 (`urlproceso` nulo) y una variante con `urlproceso = ""`.
- **Resultado esperado:** ambos se cargan con `url_publica` nula y `sin_url_publica = sí`; el resumen muestra "Advertencias: 2".

### QA-07: Fecha de corte desde metadatos y alternativa aproximada

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | rowsUpdatedAt | 1790722800 | metadatos disponibles |
  | Metadatos | HTTP 500 | metadatos no disponibles |

- **Pasos:**
  1. Ejecutar la carga con metadatos disponibles.
  2. Repetir con la consulta de metadatos fallando.
- **Resultado esperado:** (1) `fecha_corte` = conversión de 1790722800 a America/Bogota y `fecha_corte_aproximada = no`. (2) `fecha_corte` = fecha y hora de inicio de la ejecución, `fecha_corte_aproximada = sí` en todos los contratos de esa ejecución y la carga continúa.

### QA-08: Falla transitoria recuperada con reintento

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 8 / RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falla inyectada en página 1 | tiempo de espera agotado, luego éxito | 1 reintento |
  | Falla inyectada en página 1 | HTTP 429, HTTP 503, luego éxito | 2 reintentos |

- **Pasos:**
  1. Ejecutar la carga con cada falla inyectada.
- **Resultado esperado:** la página se procesa, los 3 contratos quedan guardados una sola vez, las esperas siguen la secuencia 2 s y 4 s, y los errores de la ejecución registran el reintento como recuperado. Estado "Exitosa".

### QA-09: Falla persistente deja la ejecución fallida y permite reanudar sin duplicados

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-12, RN-10
- **Precondiciones:** API simulada con 2.500 contratos válidos (3 páginas).
- **Pasos:**
  1. Inyectar HTTP 503 permanente en la página 2 y ejecutar la carga.
  2. Quitar la falla y ejecutar de nuevo.
- **Resultado esperado:** (1) 4 intentos sobre la página 2 (original + 3 reintentos con esperas de 2, 4 y 8 s); estado "Fallida"; 1.000 contratos guardados; mensaje "La carga inicial SECOP II falló en la página 2: …". (2) Al final hay exactamente 2.500 contratos, sin `id_contrato` repetido; los 1.000 previos se cuentan como "Sin cambios".

### QA-10: Error no recuperable sin reintentos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10 / RN-12
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Respuesta API | HTTP 400 | consulta inválida |
  | Respuesta API | HTTP 403 | token inválido |
  | Respuesta API | HTTP 404 | dataset `xxxx-0000` inexistente |

- **Pasos:**
  1. Ejecutar la carga con cada respuesta.
- **Resultado esperado:** un solo intento, estado "Fallida" y mensaje "La API de datos.gov.co rechazó la consulta (HTTP {código}). Verifique el identificador del dataset, la consulta y el app token."

### QA-11: Re-ejecución idempotente con y sin cambios en la fuente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 11 / RN-10
- **Precondiciones:** carga de QA-01 ya realizada.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | CO1.PCCNTR.5000001.ultima_actualizacion | 2026-09-30T11:00:00 | más reciente → actualizado |
  | CO1.PCCNTR.5000002.ultima_actualizacion | 2025-07-05T08:30:00 | igual → sin cambios |
  | CO1.PCCNTR.5000003.ultima_actualizacion | 2022-12-01T00:00:00 | anterior → sin cambios |

- **Pasos:**
  1. Ejecutar de nuevo la carga inicial.
- **Resultado esperado:** siguen existiendo 3 contratos; resumen "Nuevos: 0. Actualizados: 1. Sin cambios: 2."; CO1.PCCNTR.5000001 refleja los datos nuevos y su `id_ejecucion` es el de la nueva ejecución.

### QA-12: Rechazo de una segunda ejecución concurrente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 12 / RN-14
- **Pasos:**
  1. Iniciar una carga con la API simulada en pausa (ejecución en curso).
  2. Intentar iniciar otra carga de SECOP II.
- **Resultado esperado:** la segunda no inicia y se muestra "Ya existe una carga en curso para SECOP II (ejecución {id_ejecucion}). Espere a que termine."

### QA-13: Ejecución abandonada se cierra al iniciar una nueva

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Última actividad de la ejecución "En curso" | hace 6 h 1 min | supera el límite → abandonada |
  | Última actividad de la ejecución "En curso" | hace 5 h 59 min | no supera → bloquea |

- **Pasos:**
  1. Preparar una ejecución "En curso" con cada antigüedad e intentar una nueva carga.
- **Resultado esperado:** con 6 h 1 min, la ejecución anterior pasa a "Fallida" y la nueva inicia; con 5 h 59 min, la nueva se rechaza con el mensaje de QA-12.

### QA-14: Ejecución sin app token

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 13 / RN-13
- **Pasos:**
  1. Eliminar el secreto del app token y ejecutar la carga.
  2. Revisar las solicitudes enviadas y los logs.
- **Resultado esperado:** las solicitudes no llevan `X-App-Token`; la carga se completa; la ejecución registra "Ejecución sin app token: la API puede aplicar límites más estrictos". Con token configurado, el valor del token no aparece en ningún log.

### QA-15: Fuente sin registros

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 14
- **Pasos:**
  1. Configurar la API simulada para devolver una lista vacía y ejecutar la carga.
- **Resultado esperado:** estado "Exitosa", todos los contadores en 0 y el mensaje "La fuente no devolvió contratos para la ventana y el prefiltro configurados."

### QA-16: URL como objeto y valor del contrato como dato de referencia

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-06, RN-07, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | urlproceso | {"url": "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.2001"} | objeto |
  | valor_del_contrato | "18500000.50" | texto numérico |
  | departamento | (campo ausente en la respuesta) | campo permitido inexistente |

- **Pasos:**
  1. Ejecutar la carga con un contrato con esos valores.
- **Resultado esperado:** `url_publica` = el texto de la URL; `valor_contrato_referencia` = 18.500.000,50; `departamento` nulo sin error ni rechazo.

---

**Total de casos:** 16
