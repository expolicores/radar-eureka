# Casos de Prueba — Historia #1: R0 – Scaffold técnico mínimo

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** que el esqueleto arranca (backend y frontend), que la base de datos conecta y la migración inicial vacía se aplica, el comportamiento de `GET /healthz` con y sin base de datos, la configuración por ambiente (`DATABASE_URL` obligatoria, `APP_ENV` y `LOG_LEVEL` con valores por defecto), los identificadores de correlación (`X-Correlation-ID`, `X-Request-ID`), el log estructurado, las verificaciones de calidad (lint, typing, tests y fronteras de importación) en local y en CI, y que el diff respeta el alcance de R0.

**Queda fuera:** funcionalidades de negocio, autenticación, cola y pipeline de jobs, dispatcher, CLI, IA (puertos, fakes, variables, adaptadores), tablas de negocio, endpoint de *liveness* aparte, *tracing* distribuido y despliegue a producción.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Base de datos local | PostgreSQL 16 levantado con `docker compose up -d` | Ambiente local objetivo |
| Base de datos CI | PostgreSQL 16 como *service container* de GitHub Actions | Validación completa mientras el equipo local no tenga Docker ni uv |
| `DATABASE_URL` válida | `postgresql+psycopg://procurement:procurement_local@localhost:5432/public_procurement` | Credenciales locales de ejemplo, no reales |
| `DATABASE_URL` inaccesible | `postgresql+psycopg://procurement:procurement_local@localhost:5499/public_procurement` | Puerto sin servicio |
| `X-Correlation-ID` de prueba | `3f2b8c1e-7a4d-4e9b-9c11-5d2a6f8e0b47` | Valor válido enviado por el cliente |
| `X-Request-ID` de prueba | `a91c0d5e-2b7f-4c3a-8e64-1f9d7b2c4e08` | Valor válido enviado por el cliente |
| Versión de Python | 3.12 (gestionada con uv) | Estándar objetivo |
| Repositorio | Rama con el scaffold de R0, sin cambios locales | |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: Flujo principal (migración, backend, frontend, `/healthz` 200) | QA-01, QA-02, QA-03, QA-04 |
| Escenario 2: Validaciones (lint, formato, typing, fronteras, tests en local y CI) | QA-10, QA-11, QA-12 |
| Escenario 3: `/healthz` 503 sin PostgreSQL, textos exactos | QA-05 |
| Escenario 4: Configuración por ambiente | QA-06, QA-07, QA-08 |
| Escenario 5: Alcance controlado | QA-13 |
| Escenario 6: Identificadores de correlación | QA-09, QA-14, QA-05 |
| Regla: logs JSON con `module`, `event`, `correlation_id`, `request_id` | QA-03, QA-05, QA-09, QA-14 |
| Regla: variables de R0 (`DATABASE_URL` obligatoria; `APP_ENV`, `LOG_LEVEL` con defecto) | QA-06, QA-07, QA-08 |
| Regla: secretos fuera del repositorio | QA-08 |
| Regla: errores de API en *problem details* en español, sin trazas | QA-05 |
| Regla: Python 3.12 con uv y lockfile | QA-12 |
| Disparador relanzable: migración | QA-02 |
| Disparador: PR o *push* dispara el CI | QA-12 |

---

## Casos de Prueba

### QA-01: La migración inicial se aplica sobre una base vacía y registra su revisión

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Precondiciones:** base de datos local sin tablas; `DATABASE_URL` válida.
- **Pasos:**
  1. Ejecutar la migración hasta la última revisión.
  2. Consultar la tabla `alembic_version`.
- **Resultado esperado:** la migración termina sin error; `alembic_version` contiene exactamente una fila con la revisión inicial; no se crea ninguna otra tabla.

### QA-02: Ejecutar la migración dos veces no produce cambios ni errores

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 1 / disparador relanzable
- **Precondiciones:** QA-01 ejecutado.
- **Pasos:**
  1. Ejecutar de nuevo la migración hasta la última revisión.
  2. Consultar `alembic_version` y la lista de tablas.
- **Resultado esperado:** termina sin error; `alembic_version` sigue con una sola fila y la misma revisión; no aparecen tablas nuevas.

### QA-03: `/healthz` responde 200 con la base de datos conectada

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / regla de logs JSON
- **Precondiciones:** backend arrancado con `DATABASE_URL` válida; QA-01 ejecutado.
- **Pasos:**
  1. Enviar `GET /healthz` sin cabeceras de correlación.
  2. Revisar la línea de log de la solicitud.
- **Resultado esperado:** respuesta **200**; el cuerpo indica que el servicio está disponible y que la base de datos está conectada. La línea de log es JSON e incluye `module`, `event`, `correlation_id` y `request_id`, sin correos ni datos personales.

### QA-04: El frontend carga la página inicial en español

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Pasos:**
  1. Arrancar el servidor de desarrollo del frontend.
  2. Abrir en el navegador la URL que informa el servidor.
- **Resultado esperado:** la página inicial carga sin errores en la consola del navegador y muestra un texto en español que confirma que la aplicación arrancó; no hay vistas de negocio.

### QA-05: `/healthz` responde 503 en *problem details* cuando PostgreSQL no está disponible

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / Escenario 6 / regla de *problem details* / regla de logs JSON
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Estado de la base | Contenedor de PostgreSQL detenido con `DATABASE_URL` válida | Servicio caído |
  | `DATABASE_URL` | Valor «inaccesible» de los datos base | Puerto sin servicio |
  | `DATABASE_URL` | URL válida con contraseña `clave_incorrecta` | La base responde pero rechaza la conexión |

- **Pasos:**
  1. Arrancar el backend en cada una de las condiciones de la tabla.
  2. Enviar `GET /healthz` con los `X-Correlation-ID` y `X-Request-ID` de prueba.
  3. Revisar la respuesta y el log.
- **Resultado esperado:** respuesta **503** con tipo de contenido `application/problem+json`, `title` = «Servicio no disponible» y `detail` = «No fue posible verificar la conexión con la base de datos.», sin trazas, nombres de host, credenciales ni mensajes internos del motor. La respuesta devuelve las mismas cabeceras `X-Correlation-ID` y `X-Request-ID` enviadas. Se registra una línea de log JSON con `module`, `event` y esos mismos `correlation_id` y `request_id`, sin la contraseña.

### QA-06: El backend no arranca si falta `DATABASE_URL`

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / regla de variables de R0
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `DATABASE_URL` | (no definida) | Variable ausente |
  | `DATABASE_URL` | `""` | Variable vacía |

- **Pasos:**
  1. Arrancar el backend en cada condición.
- **Resultado esperado:** el arranque falla con el mensaje exacto «Falta la variable de entorno obligatoria: DATABASE_URL.» y el proceso no queda escuchando solicitudes.

### QA-07: El backend arranca solo con `DATABASE_URL` y aplica los valores por defecto

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / regla de variables de R0
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | `DATABASE_URL` | Valor válido de los datos base | Única variable definida |
  | `APP_ENV` | (no definida) | Debe quedar `local` |
  | `LOG_LEVEL` | (no definida) | Debe quedar `INFO` |

- **Pasos:**
  1. Arrancar el backend con solo `DATABASE_URL` definida.
  2. Enviar `GET /healthz` y revisar el log.
- **Resultado esperado:** el backend arranca; `APP_ENV` toma `local` y `LOG_LEVEL` toma `INFO` (se registran líneas de nivel INFO y no de nivel DEBUG).

### QA-08: `.env.example` documenta las variables de R0 y no hay secretos versionados

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / regla de secretos / regla de variables de R0
- **Pasos:**
  1. Comparar las variables que lee la configuración del backend con las de `.env.example`.
  2. Revisar los archivos versionados en busca de archivos `.env` o de contraseñas y tokens.
- **Resultado esperado:** la configuración lee exactamente `DATABASE_URL`, `APP_ENV` y `LOG_LEVEL`, y las tres aparecen en `.env.example` con una descripción en español y un valor de ejemplo no real; no hay variables de Azure AI Foundry, correo ni *storage*; ningún `.env` está versionado y el repositorio no contiene credenciales.

### QA-09: El backend reutiliza las cabeceras de correlación válidas que recibe

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / regla de logs JSON
- **Precondiciones:** backend arrancado con `DATABASE_URL` válida.
- **Pasos:**
  1. Enviar `GET /healthz` con los `X-Correlation-ID` y `X-Request-ID` de prueba.
  2. Revisar las cabeceras de la respuesta y la línea de log.
- **Resultado esperado:** la respuesta devuelve `X-Correlation-ID` = `3f2b8c1e-7a4d-4e9b-9c11-5d2a6f8e0b47` y `X-Request-ID` = `a91c0d5e-2b7f-4c3a-8e64-1f9d7b2c4e08`; la línea de log tiene esos mismos valores en `correlation_id` y `request_id`.

### QA-10: Todas las verificaciones de calidad pasan en local

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Backend | `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest` | |
  | Frontend | `npm run lint`, verificación de Prettier, `npm test` | |

- **Pasos:**
  1. Ejecutar cada verificación de la tabla.
- **Resultado esperado:** todas terminan con código de salida 0 y sin advertencias que bloqueen.

### QA-11: `lint-imports` falla ante una violación de frontera

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Pasos:**
  1. En una rama temporal, agregar un import que viole un contrato configurado.
  2. Ejecutar `lint-imports`.
  3. Revertir el cambio.
- **Resultado esperado:** `lint-imports` termina con error y nombra el contrato violado; después de revertir, vuelve a pasar.

### QA-12: El CI corre lint, typing y tests con Python 3.12 y PostgreSQL 16 en cada PR o *push*

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / regla de Python 3.12 con uv / disparador del CI
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Evento | Apertura de un PR | |
  | Evento | *Push* a la rama del PR | Mismo comportamiento |

- **Pasos:**
  1. Disparar el CI con cada evento.
  2. Revisar los trabajos de backend y frontend.
- **Resultado esperado:** el CI se ejecuta; el backend instala dependencias con uv desde el lockfile sobre Python 3.12, aplica la migración contra PostgreSQL 16 y corre lint, typing, `lint-imports` y tests; el frontend corre lint, Prettier y Vitest; todos los trabajos terminan en verde.

### QA-13: El diff de R0 no introduce infraestructura fuera del alcance

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Pasos:**
  1. Revisar la estructura de carpetas y las dependencias declaradas del backend y el frontend.
- **Resultado esperado:** no hay dispatcher, CLI, cola o pipeline de jobs, autenticación, *tracing* distribuido, código, configuración ni dependencias de IA, módulo `extraction`, tablas de negocio, módulos vacíos fuera de `shared/` y `entrypoints/api/`, ni código *placeholder* sin consumidor.

### QA-14: El backend genera los identificadores de correlación que no llegan o no son válidos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / regla de logs JSON
- **Precondiciones:** backend arrancado con `DATABASE_URL` válida.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Cabeceras | Ninguna de las dos | Ambas se generan |
  | Cabeceras | Solo `X-Correlation-ID` de prueba | Se reutiliza el de correlación y se genera el de solicitud |
  | Cabeceras | `X-Correlation-ID` y `X-Request-ID` con valor vacío | Ambas se consideran no válidas y se generan |

- **Pasos:**
  1. Enviar `GET /healthz` en cada condición; repetir la primera condición una segunda vez.
  2. Revisar las cabeceras de la respuesta y la línea de log.
- **Resultado esperado:** la respuesta siempre trae `X-Correlation-ID` y `X-Request-ID` no vacíos; los valores recibidos válidos se devuelven sin cambios y los demás son nuevos; dos solicitudes sin cabeceras reciben valores distintos; la línea de log coincide con las cabeceras de la respuesta.

---

**Total de casos:** 14
