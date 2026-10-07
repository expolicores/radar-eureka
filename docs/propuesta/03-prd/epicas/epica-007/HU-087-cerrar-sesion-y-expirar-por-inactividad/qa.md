# Casos de Prueba — HU-087: Cerrar sesión y expirar la sesión por inactividad

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el cierre de sesión voluntario, la invalidación en el servidor, la ausencia de datos en caché, el aviso previo, la continuación de la sesión, la expiración por inactividad, la definición de actividad, el regreso a la página y la configuración de parámetros. Queda fuera el inicio de sesión (HU-086).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, sesión activa |
| Parámetros | `tiempo_inactividad_sesion_minutos = 30`, `aviso_expiracion_minutos = 2` |
| Página de trabajo | detalle de un caso "Compra TV 65 Gobernación" con una nota en edición sin guardar |
| Reloj | controlable en el entorno de prueba |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-10 | QA-01, QA-02 |
| Escenario 2 / RN-02 | QA-03 |
| Escenario 3 | QA-04 |
| Escenario 4 / RN-04 | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 / RN-06 / RN-08 / RN-10 | QA-07 |
| Escenario 7 / RN-07 | QA-08 |
| Escenario 8 / RN-05 | QA-09, QA-10 |
| Escenario 9 / RN-09 | QA-11 |
| RN-03 / RN-04 (rangos) | QA-12 |

---

## Casos de Prueba

### QA-01: Cerrar sesión

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-10
- **Pasos:**
  1. Pulsar "Cerrar sesión" en el menú de usuario.
  2. Revisar el log de aplicación.
- **Resultado esperado:** página de inicio de sesión con "Cerraste sesión."; evento `cierre` registrado con usuario, fecha y hora.

### QA-02: Cerrar sesión no afecta otros dispositivos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Precondiciones:** la analista tiene sesión en el navegador A y en el navegador B.
- **Pasos:**
  1. Cerrar sesión en A.
  2. Abrir "Mis casos" en B.
- **Resultado esperado:** en B la sesión sigue activa y se muestra "Mis casos".

### QA-03: Botón atrás tras cerrar sesión

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Pasos:**
  1. Abrir el detalle del caso, cerrar sesión y pulsar "atrás".
- **Resultado esperado:** no se muestran datos del caso; se dirige al inicio de sesión con "Inicia sesión para continuar."

### QA-04: Reutilizar identificador de sesión cerrada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Pasos:**
  1. Copiar el identificador de sesión, cerrar sesión.
  2. Enviar una solicitud para crear una nota usando el identificador copiado.
- **Resultado esperado:** solicitud rechazada como no autenticada; no se crea la nota.

### QA-05: Aviso previo a la expiración

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Pasos:**
  1. Dejar la página sin actividad 27 min 59 s y luego 28 min.
- **Resultado esperado:** a 27:59 no hay aviso; a 28:00 aparece "Tu sesión se cerrará en 2 minutos por inactividad." con "Seguir conectado", operable por teclado.

### QA-06: Seguir conectado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. Con el aviso visible al minuto 29, pulsar "Seguir conectado".
  2. Esperar 29 minutos más sin actividad.
- **Resultado esperado:** el aviso se oculta y la nota en edición conserva su texto; la sesión sigue activa al minuto 29 posterior (el contador se reinició).

### QA-07: Expiración por inactividad y regreso a la página

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-06, RN-08, RN-10
- **Pasos:**
  1. Dejar la página sin actividad 30 minutos.
  2. Iniciar sesión de nuevo.
- **Resultado esperado:** al minuto 30 la página pasa al login con "Tu sesión expiró por inactividad. Inicia sesión de nuevo."; la sesión queda invalidada en el servidor; evento `expiracion` en el log; tras el login se vuelve al detalle del caso.

### QA-08: Guardar con sesión ya expirada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-07
- **Pasos:**
  1. Escribir una nota, suspender el equipo 35 minutos.
  2. Al reanudar, pulsar "Guardar nota".
- **Resultado esperado:** la nota no se guarda (ni parcialmente); se dirige al login con "Tu sesión expiró por inactividad. Inicia sesión de nuevo."

### QA-09: Acciones del usuario reinician el contador

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-05
- **Datos de prueba:**

  | Acción al minuto 25 | Esperado al minuto 50 |
  | ------------------- | --------------------- |
  | abrir una ficha de contrato | sesión activa |
  | aplicar un filtro | sesión activa |
  | guardar una nota | sesión activa |

- **Pasos:**
  1. Realizar la acción al minuto 25 y esperar sin actividad hasta el minuto 50.
- **Resultado esperado:** en todos los casos la sesión sigue activa al minuto 50 (25 minutos tras la última acción).

### QA-10: Consultas automáticas no cuentan como actividad

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Pasos:**
  1. Dejar abierta una página que hace consultas automáticas de fondo, sin interacción, 30 minutos.
- **Resultado esperado:** la sesión expira al minuto 30.

### QA-11: Cambio del tiempo de inactividad con sesiones abiertas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-09
- **Pasos:**
  1. Con una sesión abierta e inactiva 20 minutos, cambiar el parámetro a 60.
  2. Esperar hasta el minuto 45 de inactividad.
- **Resultado esperado:** la sesión sigue activa al minuto 45; el aviso aparece al minuto 58.

### QA-12: Rangos de los parámetros

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-03, RN-04
- **Datos de prueba:**

  | Parámetro | Valor | Esperado |
  | --------- | ----- | -------- |
  | tiempo_inactividad_sesion_minutos | 4 | rechazado |
  | tiempo_inactividad_sesion_minutos | 5 | aceptado |
  | tiempo_inactividad_sesion_minutos | 480 | aceptado |
  | tiempo_inactividad_sesion_minutos | 481 | rechazado |
  | aviso_expiracion_minutos | 0 | rechazado |
  | aviso_expiracion_minutos | 10 | aceptado (con inactividad 30) |
  | aviso_expiracion_minutos | 11 | rechazado |
  | aviso_expiracion_minutos | 5 con inactividad 5 | rechazado (no es menor) |

- **Pasos:**
  1. Configurar cada valor.
- **Resultado esperado:** según la tabla; ante rechazo se conserva el valor anterior.

---

**Total de casos:** 12
