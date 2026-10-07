# Casos de Prueba — HU-084: Emitir invitación de registro para un Analista

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la emisión, reemisión, consulta y revocación de invitaciones por el Administrador, la validación del correo, la precondición de política publicada, la atomicidad con el envío de correo, los estados de la invitación, la auditoría y la autorización. Queda fuera el uso del enlace para crear la cuenta (HU-085) y la interfaz gráfica (no exigida).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Administrador | `admin.po@ejemplo.org`, rol Administrador, sesión activa |
| Analista existente | `luis.mora@ejemplo.org`, rol Analista, cuenta registrada |
| Política vigente | versión `PTD-1.0`, publicada 2026-09-30 |
| Vigencia configurada | `vigencia_invitacion_dias = 7` |
| Fecha de prueba | 2026-10-02 10:00 (UTC−5) |
| Servicio de correo | simulado, configurable para aceptar o fallar |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-06 / RN-07 / RN-09 / RN-14 | QA-01 |
| Escenario 2 / RN-02 | QA-02, QA-03 |
| Escenario 3 / RN-03 | QA-04 |
| Escenario 4 / RN-04 | QA-05 |
| Escenario 5 / RN-10 | QA-06, QA-07 |
| Escenario 6 / RN-11 | QA-08 |
| Escenario 7 / RN-08 / RN-12 | QA-09 |
| Escenario 8 | QA-10 |
| Escenario 9 | QA-11 |
| Escenario 10 / RN-08 | QA-12 |
| Escenario 11 / RN-01 | QA-13 |
| RN-05 | QA-01 |
| RN-06 (rango y no retroactividad) | QA-14 |
| RN-13 | QA-15 |

---

## Casos de Prueba

### QA-01: Emitir invitación para correo nuevo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-05, RN-06, RN-07, RN-09, RN-14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | `  Ana.Rojas@Ejemplo.org ` | con espacios y mayúsculas |

- **Pasos:**
  1. Emitir invitación con el correo indicado.
  2. Consultar la invitación y el correo recibido.
- **Resultado esperado:** invitación `Pendiente` para `ana.rojas@ejemplo.org`, rol `Analista`, vence `09/10/2026 10:00`; mensaje "Invitación enviada a ana.rojas@ejemplo.org. Vence el 09/10/2026 10:00."; correo con asunto "Invitación a Seguimiento Compras Públicas", enlace, fecha de vencimiento y texto "Si no esperabas esta invitación, ignora este correo."; el token no aparece en claro en la consulta.

### QA-02: Correo vacío o mal formado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | (vacío) | nulo |
  | correo | `ana.rojasejemplo.org` | sin @ |
  | correo | `ana@ejemplo` | dominio sin punto |
  | correo | `ana @ejemplo.org` | espacio interno |
  | correo | `ana@@ejemplo.org` | dos @ |

- **Pasos:**
  1. Emitir invitación con cada valor.
- **Resultado esperado:** para cada valor, "Ingresa un correo electrónico válido."; no se crea invitación ni se envía correo.

### QA-03: Longitud límite del correo

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | parte local de 242 caracteres + `@ejemplo.org` (254) | máximo |
  | correo | parte local de 243 caracteres + `@ejemplo.org` (255) | máximo + 1 |

- **Pasos:**
  1. Emitir invitación con cada valor.
- **Resultado esperado:** 254 caracteres → invitación creada; 255 caracteres → "Ingresa un correo electrónico válido." sin invitación.

### QA-04: Correo de una cuenta existente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | `Luis.Mora@Ejemplo.org` | difiere solo en mayúsculas |

- **Pasos:**
  1. Emitir invitación.
- **Resultado esperado:** "Ya existe una cuenta registrada con este correo."; no se crea invitación ni se envía correo.

### QA-05: Reemitir invitación pendiente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Precondiciones:** invitación `Pendiente` para `ana.rojas@ejemplo.org` emitida el 2026-10-01.
- **Pasos:**
  1. Emitir nueva invitación para `ana.rojas@ejemplo.org`.
  2. Intentar usar el enlace de la invitación anterior.
  3. Consultar invitaciones de ese correo.
- **Resultado esperado:** mensaje "Invitación enviada a ana.rojas@ejemplo.org. La invitación pendiente anterior quedó reemplazada."; la anterior queda `Reemplazada` y su enlace no funciona; existe exactamente una `Pendiente` con vencimiento 09/10/2026 10:00.

### QA-06: Falla el envío en una emisión nueva

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-10
- **Precondiciones:** servicio de correo configurado para responder error.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | `marta.diaz@ejemplo.org` | sin invitaciones previas |

- **Pasos:**
  1. Emitir invitación.
  2. Consultar invitaciones.
- **Resultado esperado:** "No fue posible enviar el correo de invitación. La invitación no quedó activa; intenta de nuevo más tarde."; no existe invitación `Pendiente` para ese correo; el error queda en el log de aplicación.

### QA-07: Falla el envío en una reemisión

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-10
- **Precondiciones:** invitación `Pendiente` para `ana.rojas@ejemplo.org`; servicio de correo con tiempo de espera agotado.
- **Pasos:**
  1. Reemitir invitación para `ana.rojas@ejemplo.org`.
- **Resultado esperado:** mismo mensaje de QA-06; la invitación anterior sigue `Pendiente` y su enlace sigue funcionando.

### QA-08: Sin política de datos publicada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-11
- **Precondiciones:** no existe versión vigente publicada de la política.
- **Pasos:**
  1. Emitir invitación para `marta.diaz@ejemplo.org`.
- **Resultado esperado:** "No hay una política de tratamiento de datos publicada. Publícala antes de invitar analistas."; no se crea invitación.

### QA-09: Consultar invitaciones en todos los estados

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-08, RN-12
- **Precondiciones:** invitaciones: una `Usada`, una `Revocada`, una `Reemplazada`, una `Pendiente` vigente y una `Pendiente` emitida el 2026-09-20 (vencida el 27/09/2026).
- **Pasos:**
  1. Consultar invitaciones.
- **Resultado esperado:** lista por fecha de emisión descendente con correo, estado, emisión, vencimiento, emisor y fecha de uso/revocación; la emitida el 2026-09-20 aparece y queda persistida como `Vencida`.

### QA-10: Consulta sin invitaciones

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 8
- **Precondiciones:** ninguna invitación emitida.
- **Pasos:**
  1. Consultar invitaciones.
- **Resultado esperado:** "No hay invitaciones emitidas."

### QA-11: Revocar invitación pendiente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9
- **Precondiciones:** invitación `Pendiente` vigente para `pedro.gil@ejemplo.org`.
- **Pasos:**
  1. Revocar la invitación.
  2. Intentar usar su enlace.
- **Resultado esperado:** "Invitación revocada."; estado `Revocada` con fecha y Administrador; el enlace no funciona; no se envía correo al invitado.

### QA-12: Revocar invitación no pendiente

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | estado | `Usada` | |
  | estado | `Vencida` | |
  | estado | `Reemplazada` | |
  | estado | `Revocada` | |

- **Pasos:**
  1. Intentar revocar una invitación en cada estado.
- **Resultado esperado:** "Solo se pueden revocar invitaciones pendientes."; el estado no cambia.

### QA-13: Gestión de invitaciones sin rol Administrador

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 11, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | usuario | `luis.mora@ejemplo.org` | rol Analista |
  | usuario | sin sesión | anónimo |

- **Pasos:**
  1. Intentar emitir, consultar y revocar invitaciones con cada usuario.
- **Resultado esperado:** Analista → "No tienes permisos para realizar esta acción." sin efectos; sin sesión → dirigido al inicio de sesión, sin efectos.

### QA-14: Cambio de vigencia no afecta invitaciones emitidas

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | vigencia_invitacion_dias | 1 | mínimo |
  | vigencia_invitacion_dias | 30 | máximo |
  | vigencia_invitacion_dias | 0 / 31 | fuera de rango |

- **Pasos:**
  1. Emitir invitación con vigencia 7; cambiar vigencia a 1; emitir otra invitación a otro correo.
  2. Intentar configurar 0 y 31.
- **Resultado esperado:** la primera conserva vencimiento 09/10/2026 10:00; la segunda vence 03/10/2026 10:00; 30 se acepta; 0 y 31 se rechazan como fuera del rango 1 a 30.

### QA-15: Auditoría de acciones sobre invitaciones

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Pasos:**
  1. Emitir, reemitir y revocar invitaciones.
  2. Consultar el log de auditoría.
- **Resultado esperado:** existe un registro por cada acción con acción, correo invitado, Administrador, fecha y hora.

---

**Total de casos:** 15
