# Casos de Prueba — HU-050: Ejecutar la captura automática controlada de una fuente retail

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el marco común de captura contra una **fuente simulada** (servidor de prueba que imita `robots.txt`, sitemaps y páginas de producto): habilitación y condiciones previas, programación, `robots.txt` en cada ejecución, ritmo y volumen, User-Agent, reintentos, filtros de producto, almacenamiento con evidencia, registro de la ejecución, deshabilitación, independencia de la carga manual y permisos. Nunca se prueba contra los sitios reales con volúmenes de prueba.

Fuera de alcance: lectura específica de cada fuente (HU-051, HU-052) y la suspensión y notificación (HU-053), salvo la verificación de que se invoca.

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Fuente simulada:** "Alkosto" apuntando al servidor de prueba `https://tienda-simulada.prueba.local`, con conector de prueba que declara rutas requeridas `/sitemap*.xml` y `/p/`.
- **Configuración base:** captura permitida; User-Agent `SeguimientoComprasPublicas/0.1 (+contacto: equipo@prueba.local)`; semanal, lunes 02:00; intervalo 2 s; volumen 2.000/7 días; entorno `pruebas`.
- **robots.txt base:** `User-agent: *` / `Disallow: /search/` / `Disallow: /*?q=`.
- **Sitemap simulado:** 10 URLs de producto: 7 televisores válidos de la tienda, 1 "Combo TV 55 + soporte de pared", 1 televisor sin modelo identificable, 1 URL `/p/oculto-123` que se prohibirá por robots en QA-05.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-09 / RN-10 | QA-01 |
| Escenario 2 / RN-01 / RN-05 | QA-02, QA-03 |
| Escenario 3 / RN-03 | QA-05 |
| Escenario 4 / RN-03 | QA-06 |
| RN-03 (rutas requeridas prohibidas, robots modificado) | QA-07 |
| Escenario 5 / RN-04 | QA-08 |
| Escenario 6 / RN-04 | QA-09 |
| RN-04 (configuración inválida) | QA-10 |
| RN-05 / RN-06 | QA-11 |
| Escenario 7 / RN-07 | QA-12, QA-13 |
| Escenario 8 / RN-08 | QA-14 |
| RN-09 (IVA por defecto, URL repetida) | QA-15 |
| Escenario 9 / RN-02 | QA-16 |
| Escenario 10 | QA-17 |
| Escenario 11 / RN-11 | QA-18 |
| RN-12 | QA-19 |
| Escenario 12 | QA-20 |
| RN-01 (términos de uso en producción) | QA-04 |

---

## Casos de Prueba

### QA-01: Ejecución programada completa

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-09, RN-10
- **Pasos:**
  1. Habilitar la captura y simular la llegada del lunes 02:00.
  2. Consultar la ejecución y las observaciones creadas.
- **Resultado esperado:** ejecución `completada`; 7 observaciones con `metodo_adquisicion = sitemap_datos_estructurados`, `canal_carga = conector`, `registrado_por = conector:Alkosto`, `id_contexto = id_ejecucion`, `protocolo_busqueda = no_aplica` y evidencia (bloque de datos estructurados, URL, fecha y hora, código 200, hash); contadores: 10 candidatas, 2 descartes (`no_es_televisor`, `modelo_no_identificable`), hash de `robots.txt` guardado; el servidor recibió solo solicitudes con el User-Agent configurado.

### QA-02: Habilitar sin condiciones previas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Datos de prueba:**

  | Situación | Mensaje esperado |
  | ----- | ----- |
  | User-Agent vacío | `"Configure un User-Agent con contacto antes de habilitar la captura."` |
  | Fuente Ktronix (sin conector) | `"La fuente Ktronix no admite captura automática."` |

### QA-03: Validación del User-Agent

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | User-Agent | Resultado |
  | ----- | ----- |
  | `SeguimientoComprasPublicas/0.1` (sin contacto) | `"El User-Agent debe incluir un correo o URL de contacto."` |
  | `SCP (+a@b.co)` (14 caracteres, con contacto) | Aceptado |
  | 201 caracteres | `"El User-Agent debe tener entre 10 y 200 caracteres."` |

### QA-04: Términos de uso en producción

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-01
- **Pasos:**
  1. En entorno `produccion`, habilitar la captura de Alkosto sin revisión de términos registrada.
  2. Registrar la revisión (fecha 2026-10-01, nota "Revisión manual de términos de uso: sin prohibición expresa de lectura de páginas de producto") y habilitar de nuevo.
  3. En entorno `pruebas`, habilitar sin revisión.
- **Resultado esperado:** paso 1: `"Registre la revisión de términos de uso de Alkosto antes de habilitar la captura en producción."`; pasos 2 y 3: habilitada.

### QA-05: URL prohibida por robots que no es ruta requerida

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Precondiciones:** `robots.txt` base + `Disallow: /p/oculto-123`.
- **Resultado esperado:** el servidor no recibe solicitudes a `/p/oculto-123`; la ejecución la registra como `omitida_por_robots` y continúa con las demás.

### QA-06: robots.txt no disponible

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03
- **Datos de prueba:**

  | Respuesta de /robots.txt | Resultado esperado |
  | ----- | ----- |
  | 404 | `fallida`, motivo `"robots.txt no disponible (404)"`, evento `captura_fallida`, 0 solicitudes adicionales |
  | 500 | `fallida`, motivo con 500 |
  | sin respuesta en 30 s | `fallida`, motivo con timeout |
  | 403 | se invoca la suspensión de HU-053 |

### QA-07: Cambios de robots.txt

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Datos de prueba:**

  | robots.txt en la ejecución | Resultado esperado |
  | ----- | ----- |
  | base + comentario nuevo (permite rutas requeridas) | continúa; advertencia `robots_txt_modificado`; hash nuevo guardado |
  | `Disallow: /p/` | se invoca la suspensión por cambio de `robots.txt` (HU-053); no se solicita ninguna página |
  | grupo específico `User-agent: SeguimientoComprasPublicas` con `Disallow: /` y grupo `*` permisivo | se aplica el grupo específico: suspensión |

### QA-08: Límite de volumen

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Precondiciones:** 1.995 solicitudes registradas a la fuente en los últimos 7 días; sitemap con 10 URLs.
- **Resultado esperado:** la ejecución hace exactamente 5 solicitudes, termina `completada_con_limite` con las URLs pendientes contadas; la ejecución siguiente (fuera de la ventana) empieza por las pendientes.

### QA-09: Ritmo con y sin Crawl-delay

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-04
- **Datos de prueba:**

  | Intervalo configurado | Crawl-delay | Separación mínima observada en el servidor |
  | ----- | ----- | ----- |
  | 2 s | (ninguno) | ≥ 2 s |
  | 2 s | 5 | ≥ 5 s |
  | 3 s | 1 | ≥ 3 s |

### QA-10: Configuración de ritmo y volumen inválida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Parámetro | Valor | Mensaje esperado |
  | ----- | ----- | ----- |
  | intervalo | 0,5 s | `"El intervalo mínimo entre solicitudes no puede ser menor de 1 segundo."` |
  | intervalo | 1 s | Aceptado |
  | volumen | 0 | `"El volumen semanal debe ser un entero entre 1 y 20.000."` |
  | volumen | 20001 | mismo mensaje |

### QA-11: Sin mecanismos de evasión

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-05, RN-06
- **Pasos:**
  1. Registrar en el servidor simulado todas las solicitudes de QA-01.
  2. Hacer que el servidor responda 429 a una página.
  3. Revisión de código de la captura con la lista de RN-06.
- **Resultado esperado:** todas las solicitudes tienen el mismo User-Agent, sin cookies de sesión ni credenciales, desde el mismo origen; ninguna solicitud a `/search/` ni con `?q=`; ante el 429 no hay reintento (se invoca HU-053); la revisión de código no encuentra resolución de CAPTCHA, rotación de User-Agent o IP, proxies ni simulación de interacción humana.

### QA-12: Reintentos ante errores transitorios

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-07
- **Datos de prueba:**

  | Respuestas de una página | Resultado esperado |
  | ----- | ----- |
  | 503, 503, 200 | observación creada; 3 solicitudes a esa URL con esperas ≥ 2 y ≥ 4 s |
  | 503 × 4 | 4 solicitudes (1 + 3 reintentos, esperas 2, 4, 8 s); URL con error; la ejecución continúa |
  | 404 | sin reintentos; URL con error |

### QA-13: Ejecución fallida por exceso de errores

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-07
- **Datos de prueba:**

  | Páginas de producto con error | Resultado |
  | ----- | ----- |
  | 5 de 10 (50 %) | `completada` |
  | 6 de 10 (60 %) | `fallida`, evento `captura_fallida` |

### QA-14: Filtros de producto

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-08
- **Datos de prueba:**

  | Nombre del producto | Resultado |
  | ----- | ----- |
  | "Combo TV 55 + soporte de pared" | descarte `no_es_televisor` |
  | "Barra de Sonido Samsung HW-B450" | descarte `no_es_televisor` |
  | "Televisor LG 50 pulgadas" sin modelo | descarte `modelo_no_identificable` |
  | página sin datos estructurados | descarte `datos_estructurados_ausentes` |
  | "Televisor Samsung 55 UN55DU7000KXZL" | observación creada |

### QA-15: IVA por defecto y URL repetida en la ejecución

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-09
- **Datos de prueba:**

  | Situación | Resultado |
  | ----- | ----- |
  | página sin declaración de IVA, IVA por defecto `indeterminado` | `iva_condicion = indeterminado` |
  | la misma URL aparece en dos sitemaps | una sola observación en la ejecución |

### QA-16: Ejecución omitida

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-02
- **Datos de prueba:**

  | Situación a la hora programada | Resultado esperado |
  | ----- | ----- |
  | ejecución anterior `en_curso` | ejecución `omitida`, motivo `"ejecución anterior en curso"` |
  | fuente `suspendida` | ejecución `omitida`, motivo `"fuente suspendida"`; 0 solicitudes |

### QA-17: Deshabilitar durante la ejecución

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Iniciar una ejecución y, tras 3 observaciones creadas, deshabilitar la captura.
- **Resultado esperado:** la ejecución termina tras la solicitud en curso con estado `detenida_por_administrador`; las 3 observaciones se conservan; no hay más solicitudes.

### QA-18: Sin fuentes automatizadas, la carga manual sigue

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 11, RN-11
- **Pasos:**
  1. Con todas las capturas deshabilitadas (y luego con Alkosto suspendida), registrar una observación manual de Alkosto y cargar un paquete CSV de 3 filas.
- **Resultado esperado:** no se ejecuta ninguna captura; la observación manual y las 3 filas se guardan normalmente.

### QA-19: Cambios de configuración auditados

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-12
- **Resultado esperado:** cambiar el intervalo de 2 a 3 s y agregar el término de exclusión "parlante" genera dos eventos con usuario, fecha y hora, valor anterior y nuevo.

### QA-20: Analista no configura la captura

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 12
- **Resultado esperado:** como `analista1@prueba.local`, habilitar la captura o cambiar el volumen devuelve `"Operación permitida solo para el rol Administrador."`

---

**Total de casos:** 20
