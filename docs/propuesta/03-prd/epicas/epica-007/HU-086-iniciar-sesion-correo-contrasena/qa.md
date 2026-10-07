# Casos de Prueba — HU-086: Iniciar sesión con correo y contraseña

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el inicio de sesión exitoso, la redirección a la página solicitada y su validación de seguridad, la protección de páginas sin sesión, los errores de credenciales y campos vacíos, el bloqueo temporal por intentos fallidos y el registro de eventos. Quedan fuera el cierre de sesión y la expiración (HU-087) y la recuperación de contraseña (HU-088).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org` / `Televisor-2026`, `Activa` |
| Administrador | `admin.po@ejemplo.org` / `Admin-Piloto-2026`, `Activa` |
| Parámetros | `max_intentos_fallidos = 5`, `ventana_intentos_minutos = 15`, `duracion_bloqueo_minutos = 15` |
| Página protegida de ejemplo | "Mis casos" |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 / RN-05 / RN-06 / RN-09 | QA-01, QA-02 |
| Escenario 2 | QA-03 |
| Escenario 3 / RN-08 | QA-04 |
| Escenario 4 / RN-03 | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 / RN-04 | QA-07, QA-08 |
| Escenario 7 / RN-04 | QA-09 |
| Escenario 8 | QA-10 |
| Escenario 9 / RN-07 | QA-11 |
| RN-10 | QA-12 |

---

## Casos de Prueba

### QA-01: Inicio de sesión exitoso del Analista

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02, RN-05, RN-06, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | ` Ana.Rojas@Ejemplo.org ` | mayúsculas y espacios |
  | contraseña | `Televisor-2026` | |

- **Pasos:**
  1. Abrir la página de inicio de sesión e ingresar los datos.
  2. Revisar destino, cuenta y log de aplicación.
- **Resultado esperado:** se abre la lista priorizada de señales; el identificador de sesión es distinto al que existía antes del login; se actualiza el último acceso; el log registra el intento exitoso sin la contraseña.

### QA-02: Inicio de sesión del Administrador y sesiones simultáneas

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 1, RN-05, RN-06
- **Pasos:**
  1. Iniciar sesión como `admin.po@ejemplo.org` en un navegador.
  2. Iniciar sesión con la misma cuenta en otro navegador.
- **Resultado esperado:** ambas sesiones quedan activas y llegan a la lista priorizada de señales.

### QA-03: Redirección a la página solicitada

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Pasos:**
  1. Sin sesión, abrir "Mis casos".
  2. Iniciar sesión como Analista.
- **Resultado esperado:** tras el login se muestra "Mis casos".

### QA-04: Página protegida sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-08
- **Datos de prueba:**

  | Recurso | Esperado |
  | ------- | -------- |
  | "Mis casos" | redirección al login |
  | ficha de un contrato | redirección al login |
  | lista de señales | redirección al login |
  | política de tratamiento de datos | accesible sin sesión |
  | solicitud de recuperación de contraseña | accesible sin sesión |

- **Pasos:**
  1. Sin sesión, abrir cada recurso.
- **Resultado esperado:** los protegidos no muestran datos y dirigen al login con "Inicia sesión para continuar."; los públicos se muestran.

### QA-05: Credenciales incorrectas con mensaje genérico

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-03
- **Datos de prueba:**

  | Correo | Contraseña | Nota |
  | ------ | ---------- | ---- |
  | `ana.rojas@ejemplo.org` | `televisor-2026` | contraseña errada (minúscula) |
  | `nadie@ejemplo.org` | `Televisor-2026` | correo inexistente |
  | `ana.rojas@ejemplo.org` | ` Televisor-2026` | contraseña con espacio inicial: no se recorta |

- **Pasos:**
  1. Intentar iniciar sesión con cada combinación.
- **Resultado esperado:** en todos, "Correo o contraseña incorrectos."; sin sesión; el correo se conserva y la contraseña se borra.

### QA-06: Campos vacíos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | Correo | Contraseña |
  | ------ | ---------- |
  | (vacío) | `Televisor-2026` |
  | `ana.rojas@ejemplo.org` | (vacío) |
  | (vacío) | (vacío) |

- **Pasos:**
  1. Pulsar "Iniciar sesión" con cada combinación.
- **Resultado esperado:** "Ingresa tu correo y tu contraseña."; no cuenta como intento fallido.

### QA-07: Bloqueo al alcanzar el máximo de intentos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-04
- **Pasos:**
  1. Hacer 4 intentos fallidos con `ana.rojas@ejemplo.org` y luego iniciar sesión con la contraseña correcta.
  2. En otra prueba, hacer 5 intentos fallidos en 10 minutos y luego intentar con la contraseña correcta.
- **Resultado esperado:** con 4 fallos, el quinto intento correcto inicia sesión; con 5 fallos, el intento correcto muestra "Demasiados intentos fallidos. Intenta de nuevo en 15 minutos o recupera tu contraseña." y no crea sesión.

### QA-08: Bloqueo también para correo inexistente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04, RN-03
- **Pasos:**
  1. Hacer 5 intentos fallidos con `nadie@ejemplo.org`.
  2. Hacer un sexto intento.
- **Resultado esperado:** el sexto intento muestra el mismo mensaje de bloqueo que una cuenta existente.

### QA-09: Fin del bloqueo y reinicio del contador

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-04
- **Precondiciones:** `ana.rojas@ejemplo.org` bloqueada a las 10:00.
- **Pasos:**
  1. A las 10:14 intentar con la contraseña correcta.
  2. A las 10:15 intentar con la contraseña correcta.
  3. Cerrar sesión, hacer 4 intentos fallidos y uno correcto.
- **Resultado esperado:** a las 10:14 sigue bloqueada ("Intenta de nuevo en 1 minutos…"); a las 10:15 inicia sesión; el contador se reinició, de modo que 4 fallos posteriores no bloquean.

### QA-10: Usuario con sesión abre el login

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 8
- **Pasos:**
  1. Con sesión activa, abrir la página de inicio de sesión.
- **Resultado esperado:** se dirige a la lista priorizada de señales.

### QA-11: Destino externo ignorado

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | destino | `https://sitio-externo.ejemplo/login` | externo |
  | destino | `//sitio-externo.ejemplo` | externo relativo a protocolo |

- **Pasos:**
  1. Iniciar sesión con cada destino en la solicitud.
- **Resultado esperado:** se abre la lista priorizada de señales, no el destino externo.

### QA-12: Sin enlace de registro público

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Revisar la página de inicio de sesión.
- **Resultado esperado:** no hay enlace "registrarse"; se muestra "El acceso es por invitación." y el enlace "¿Olvidaste tu contraseña?".

---

**Total de casos:** 12
