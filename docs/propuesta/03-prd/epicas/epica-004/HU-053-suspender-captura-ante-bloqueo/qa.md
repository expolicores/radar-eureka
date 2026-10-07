# Casos de Prueba — HU-053: Suspender la captura automática y notificar ante CAPTCHA, bloqueo, autenticación o cambio de robots.txt

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba, contra una **fuente simulada**, la detección de las cuatro condiciones de suspensión, la detención inmediata sin reintentos, la evidencia, la notificación con reintentos, la persistencia de la suspensión, la reactivación, la conservación de observaciones previas, la configuración y los permisos. Ninguna prueba provoca bloqueos en sitios reales.

Fuera de alcance: panel de estado de fuentes y relanzamiento manual (épica de operación).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador, destinatario de notificaciones); `analista1@prueba.local` (Analista).
- **Fuente simulada:** "Alkosto" apuntando a `https://tienda-simulada.prueba.local`, captura habilitada en entorno `pruebas`, rutas requeridas `/sitemap*.xml` y `/p/`, 10 páginas candidatas.
- **Servicio de correo de prueba** con buzón capturable y modo de falla configurable.
- **Fecha de referencia:** 2026-10-02T02:00-05:00 (hora programada).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-02 | QA-01 |
| Escenario 2 / RN-01 / RN-02 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-01 / RN-02 | QA-04 |
| RN-01 (orden de evaluación, respuestas que no suspenden) | QA-05 |
| Escenario 5 / RN-03 | QA-06 |
| Escenario 6 / RN-03 | QA-07 |
| RN-03 (una notificación por suspensión) | QA-08 |
| Escenario 7 / RN-04 | QA-09 |
| Escenario 8 / RN-05 | QA-10, QA-11 |
| Escenario 9 / RN-05 | QA-12 |
| Escenario 10 / RN-02 | QA-13 |
| RN-06 | QA-14 |
| RN-07 | QA-15 |
| Escenario 11 | QA-16 |

---

## Casos de Prueba

### QA-01: Suspensión por CAPTCHA

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02
- **Datos de prueba:**

  | Página | Respuesta simulada |
  | ----- | ----- |
  | 4.ª de 10 | 200 con cuerpo que contiene `<div class="g-recaptcha">` |

- **Resultado esperado:** el servidor no recibe ninguna solicitud posterior a la 4.ª página; ejecución `suspendida`; fuente `suspendida`, motivo `captcha`, con URL, código 200, cabeceras sin cookies y primeros 2 KB del cuerpo como evidencia.

### QA-02: Suspensión por bloqueo 403 y 429

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01, RN-02
- **Datos de prueba:**

  | Respuesta a la 2.ª página | Motivo esperado |
  | ----- | ----- |
  | 403 | `bloqueo` (403) |
  | 429 con `Retry-After: 60` | `bloqueo` (429) |

- **Resultado esperado:** en ambos casos, 0 reintentos y 0 solicitudes posteriores; el `Retry-After` no provoca reanudación automática.

### QA-03: Suspensión por autenticación

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | Respuesta | Motivo esperado |
  | ----- | ----- |
  | 401 | `autenticacion` |
  | 302 a `/iniciar-sesion?next=/p/123` | `autenticacion` |
  | 301 a `/p/123-nuevo` (no es login) | sin suspensión; se sigue la redirección |

- **Resultado esperado:** en los casos de suspensión no se solicita la URL de inicio de sesión ni se envían credenciales.

### QA-04: Suspensión por cambio de robots.txt

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-01, RN-02
- **Datos de prueba:**

  | robots.txt al iniciar | Resultado |
  | ----- | ----- |
  | agrega `Disallow: /p/` | suspensión `robots_txt`; 0 solicitudes de sitemaps o páginas; contenido y hash del nuevo robots como evidencia |
  | responde 403 | suspensión `robots_txt` |
  | agrega `Disallow: /ofertas/` (no requerida) | sin suspensión; advertencia `robots_txt_modificado` |

### QA-05: Orden de motivos y respuestas que no suspenden

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Respuesta | Resultado |
  | ----- | ----- |
  | 403 con cuerpo que contiene "captcha" | motivo `captcha` (primero en la tabla) |
  | 404 | sin suspensión; URL con error |
  | 503 sin marcadores | sin suspensión; reintentos del marco común |
  | 200 con la palabra "CAPTCHA" en mayúsculas | motivo `captcha` |

### QA-06: Notificación por correo en menos de 1 hora

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-03
- **Pasos:**
  1. Provocar la suspensión de QA-02 (429).
  2. Revisar el buzón de `admin.po@prueba.local`.
- **Resultado esperado:** antes de 1 hora llega un correo con asunto `"Captura suspendida: Alkosto — bloqueo"`, con fuente, motivo, fecha y hora, URL, código 429, `id_ejecucion` y el texto `"La carga manual y por archivo siguen disponibles. La captura no se reanudará hasta que un Administrador la reactive."`; la alerta queda `entregada`; el correo no contiene términos prohibidos.

### QA-07: Falla en el envío del correo

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-03
- **Datos de prueba:**

  | Comportamiento del servicio de correo | Resultado esperado |
  | ----- | ----- |
  | falla 2 veces y luego acepta | 3 intentos con 15 min entre ellos; alerta `entregada` |
  | falla siempre | 5 intentos (inicial + 4 reintentos); alerta `no_entregada` visible en el estado de la fuente; la fuente sigue `suspendida` |

### QA-08: Una sola notificación por suspensión

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-03
- **Pasos:**
  1. Suspender Alkosto y dejar pasar 2 horas programadas.
- **Resultado esperado:** existe un único correo; las ejecuciones omitidas no generan correos nuevos.

### QA-09: Fuente suspendida no se ejecuta y la carga manual sigue

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-04
- **Pasos:**
  1. Con Alkosto suspendida, simular la siguiente hora programada.
  2. Registrar una observación manual de Alkosto.
- **Resultado esperado:** 0 solicitudes al servidor; ejecución `omitida`, motivo `"fuente suspendida"`; la observación manual se guarda normalmente.

### QA-10: Reactivación válida

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-05
- **Pasos:**
  1. Reactivar Alkosto con la nota "Revisado: el bloqueo fue temporal; se mantiene ritmo de 1 solicitud cada 2 s".
  2. Verificar que no hay solicitudes inmediatas.
  3. Simular la siguiente hora programada con el servidor respondiendo normalmente.
- **Resultado esperado:** mensaje `"Captura de Alkosto reactivada; se verificará robots.txt en la próxima ejecución."`; `estado_captura = activa`; ninguna solicitud hasta la hora programada; la ejecución empieza solicitando `robots.txt` y termina `completada`.

### QA-11: La condición persiste tras reactivar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-05
- **Pasos:**
  1. Reactivar Alkosto con el servidor aún respondiendo 403.
  2. Simular la siguiente hora programada.
- **Resultado esperado:** la fuente se suspende de nuevo con motivo `bloqueo`; se envía una nueva notificación (es una nueva suspensión).

### QA-12: Reactivación inválida

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-05
- **Datos de prueba:**

  | Situación | Mensaje esperado |
  | ----- | ----- |
  | Falabella activa | `"La captura de Falabella no está suspendida."` |
  | nota "ok" (2 caracteres) | `"La nota de reactivación debe tener entre 10 y 500 caracteres."` |
  | nota de 501 caracteres | mismo mensaje |
  | nota de 10 caracteres | reactivada |

### QA-13: Observaciones previas a la suspensión se conservan

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10, RN-02
- **Pasos:**
  1. Configurar 50 páginas candidatas; el servidor responde 429 a la 41.ª.
- **Resultado esperado:** las 40 observaciones creadas siguen `vigente` sin cambios; la ejecución registra 10 URLs sin procesar.

### QA-14: Historial y eventos auditables

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-06
- **Resultado esperado:** tras QA-02 y QA-10, el historial de Alkosto muestra la suspensión (motivo, fecha, `id_ejecucion`, estado de alerta) y la reactivación (usuario, fecha, nota); existen los eventos `suspension_captura` y `reactivacion_captura`.

### QA-15: Configuración de marcadores y destinatarios

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Datos de prueba:**

  | Acción | Resultado |
  | ----- | ----- |
  | destinatarios vacíos | `"Indique entre 1 y 5 correos válidos de Administradores."` |
  | 6 destinatarios | mismo mensaje |
  | destinatario "admin@" | mismo mensaje |
  | agregar marcador "acceso denegado" | aceptado; aplica desde la siguiente solicitud; evento auditable |

### QA-16: Analista no reactiva

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 11
- **Resultado esperado:** como `analista1@prueba.local`, reactivar Alkosto devuelve `"Operación permitida solo para el rol Administrador."`; la fuente sigue `suspendida`.

---

**Total de casos:** 16
