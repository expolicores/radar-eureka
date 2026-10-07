# Casos de Prueba — HU-089: Aplicar los roles Analista y Administrador con permisos diferenciados

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la asignación de un único rol por cuenta, la matriz de permisos con los perfiles sin sesión, Analista y Administrador, el control en el servidor ante solicitudes directas, la ocultación de opciones administrativas, la privacidad de casos frente al Administrador, el aprovisionamiento y cambio de rol por procedimiento técnico, el mínimo de Administradores y la auditoría. Quedan fuera las funciones administrativas en sí (otras historias).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, rol Analista, con el caso "Compra TV 65 Gobernación" |
| Administrador | `admin.po@ejemplo.org`, rol Administrador (único) |
| Segundo usuario técnico | `soporte.po@ejemplo.org`, rol Analista, para pruebas de cambio de rol |
| Responsable técnico | operador de infraestructura con acceso al procedimiento de aprovisionamiento |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-03 / RN-04 / RN-09 | QA-03 |
| Escenario 4 | QA-04 |
| Escenario 5 / RN-02 | QA-05 |
| Escenario 6 / RN-04 | QA-06 |
| Escenario 7 / RN-06 / RN-08 / RN-09 | QA-07, QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| Escenario 9 / RN-04 | QA-10 |
| RN-05 | QA-11 |
| RN-10 | QA-12 |

---

## Casos de Prueba

### QA-01: Rol único por cuenta

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01
- **Pasos:**
  1. Registrar una cuenta por invitación.
  2. Aprovisionar una cuenta de Administrador.
  3. Intentar aprovisionar una cuenta sin rol o con un rol `Revisor`.
- **Resultado esperado:** la cuenta por invitación queda `Analista`; la aprovisionada queda `Administrador`; el procedimiento rechaza la cuenta sin rol y el rol no permitido.

### QA-02: Analista usa funciones de investigación

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Datos de prueba:**

  | Operación | Esperado |
  | --------- | -------- |
  | buscar contratos por entidad | permitido |
  | abrir ficha de contrato | permitido |
  | abrir detalle de señal | permitido |
  | calificar una señal | permitido |
  | reportar un error | permitido |
  | crear caso y nota propios | permitido |

- **Pasos:**
  1. Con la sesión de la analista, ejecutar cada operación.
- **Resultado esperado:** todas permitidas.

### QA-03: Analista intenta funciones administrativas por solicitud directa

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03, RN-04, RN-09
- **Datos de prueba:**

  | Operación administrativa |
  | ------------------------ |
  | emitir invitación |
  | cambiar `tiempo_inactividad_sesion_minutos` |
  | relanzar ingesta SECOP II |
  | corregir precio unitario en la cola de revisión |
  | registrar observación manual de precio |
  | consultar KPIs |
  | consultar log de auditoría |

- **Pasos:**
  1. Enviar cada solicitud directamente con la sesión de la analista.
- **Resultado esperado:** cada una responde "No tienes permisos para realizar esta acción."; ningún dato ni parámetro cambia; cada intento queda en el log de aplicación con usuario y operación.

### QA-04: Interfaz del Analista sin opciones administrativas

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 4
- **Pasos:**
  1. Recorrer menús y páginas con la sesión de la analista.
- **Resultado esperado:** no aparecen menús, botones ni enlaces administrativos; el menú de usuario muestra "Ana Rojas — Analista".

### QA-05: Administrador usa ambos grupos de funciones

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-02
- **Pasos:**
  1. Con la sesión del Administrador, emitir una invitación, consultar KPIs, abrir una señal y crear un caso propio.
- **Resultado esperado:** todas permitidas.

### QA-06: Administrador no accede a casos ajenos

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-04
- **Pasos:**
  1. Con la sesión del Administrador, solicitar el caso "Compra TV 65 Gobernación" por su identificador y añadirle una nota.
- **Resultado esperado:** "No encontramos este caso." en ambas; no se muestra ni se modifica nada.

### QA-07: Cambio de rol aplica en la sesión abierta

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-06, RN-08, RN-09
- **Precondiciones:** `soporte.po@ejemplo.org` tiene sesión abierta como Analista.
- **Pasos:**
  1. El responsable técnico cambia su rol a `Administrador`.
  2. Sin cerrar sesión, `soporte.po` consulta KPIs.
  3. Revisar el log de auditoría.
- **Resultado esperado:** la consulta de KPIs es permitida; auditoría con cuenta, rol anterior `Analista`, rol nuevo `Administrador`, responsable, fecha y hora.

### QA-08: Rol no asignable desde el producto

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Con la sesión del Administrador, buscar en el producto una opción para cambiar roles; enviar una solicitud directa de cambio de rol a la aplicación.
- **Resultado esperado:** no existe pantalla de roles; la solicitud no cambia ningún rol.

### QA-09: No se elimina el último Administrador

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-07
- **Pasos:**
  1. Con `admin.po` como único Administrador, cambiar su rol a `Analista`.
  2. Con dos Administradores (`admin.po` y `soporte.po`), cambiar `soporte.po` a `Analista`.
- **Resultado esperado:** el primero se rechaza con "Debe existir al menos una cuenta con rol Administrador."; el segundo se aplica.

### QA-10: Funciones protegidas sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-04
- **Pasos:**
  1. Sin sesión, solicitar una función de investigación (lista de señales) y una administrativa (emitir invitación).
- **Resultado esperado:** ninguna se ejecuta; ambas dirigen al inicio de sesión con "Inicia sesión para continuar."

### QA-11: Función sin grupo declarado

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-05
- **Precondiciones:** en el entorno de prueba existe una función habilitada sin grupo declarado en la matriz.
- **Pasos:**
  1. Invocarla como Analista y como Administrador.
- **Resultado esperado:** Analista → "No tienes permisos para realizar esta acción."; Administrador → permitida.

### QA-12: Suite automática de autorización

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-10
- **Pasos:**
  1. Ejecutar la suite de pruebas de autorización.
- **Resultado esperado:** la suite cubre el 100 % de las funciones con los tres perfiles y todos los resultados coinciden con la matriz de RN-02.

---

**Total de casos:** 12
