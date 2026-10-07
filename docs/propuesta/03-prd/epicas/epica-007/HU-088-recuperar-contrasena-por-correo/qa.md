# Casos de Prueba — HU-088: Recuperar la contraseña por correo electrónico

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la solicitud de restablecimiento (respuesta neutral, validación de correo, límite), el enlace (vigencia, uso único, reemplazo), la definición de la contraseña nueva y sus efectos (sesiones, bloqueo, aviso), y el comportamiento ante fallas del servicio de correo. Queda fuera el inicio de sesión en sí (HU-086).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, contraseña actual `Televisor-2026`, sesiones activas en navegadores A y B |
| Parámetros | `vigencia_enlace_restablecimiento_minutos = 60`, `max_solicitudes_restablecimiento_por_hora = 3`, `longitud_minima_contrasena = 10` |
| Contraseña nueva válida | `Pantalla-Nueva-65` |
| Mensaje neutral | "Si el correo corresponde a una cuenta, te enviamos un enlace para restablecer tu contraseña. Revisa tu bandeja de entrada." |
| Servicio de correo | simulado, configurable para aceptar o fallar |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-03 / RN-08 / RN-11 | QA-01 |
| Escenario 2 / RN-02 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-04 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-06 / RN-07 / RN-09 | QA-06, QA-07 |
| Escenario 7 / RN-03 | QA-08, QA-09 |
| Escenario 8 / RN-06 | QA-10 |
| Escenario 9 / RN-10 | QA-11 |
| RN-09 (falla del aviso) | QA-12 |

---

## Casos de Prueba

### QA-01: Solicitud con correo registrado

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-03, RN-08, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | `ANA.ROJAS@ejemplo.org` | se normaliza |

- **Pasos:**
  1. Solicitar el restablecimiento.
  2. Revisar el correo recibido y el log.
- **Resultado esperado:** mensaje neutral; correo con asunto "Restablece tu contraseña — Seguimiento Compras Públicas", enlace, vigencia de 60 minutos y el texto de RN-08; log sin token.

### QA-02: Solicitud con correo sin cuenta

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo | `nadie@ejemplo.org` | sin cuenta |

- **Pasos:**
  1. Solicitar el restablecimiento.
- **Resultado esperado:** mismo mensaje neutral que QA-01; no se envía correo.

### QA-03: Correo inválido en la solicitud

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | correo | (vacío) |
  | correo | `ana.rojas` |
  | correo | 255 caracteres |

- **Pasos:**
  1. Solicitar con cada valor.
- **Resultado esperado:** "Ingresa un correo electrónico válido."; no se procesa.

### QA-04: Nueva solicitud invalida el enlace anterior

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Pasos:**
  1. Solicitar dos enlaces seguidos.
  2. Abrir el primero; luego el segundo.
- **Resultado esperado:** el primero muestra "El enlace para restablecer la contraseña no es válido o ya venció. Solicita uno nuevo."; el segundo muestra el formulario.

### QA-05: Límite de solicitudes por hora

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-05
- **Pasos:**
  1. Hacer 3 solicitudes entre 10:00 y 10:20; hacer la cuarta a las 10:30.
  2. Hacer una quinta a las 11:01.
- **Resultado esperado:** las 3 primeras envían correo; la cuarta muestra el mensaje neutral, no envía correo, deja válido el tercer enlace y registra el evento; la quinta (fuera de la ventana de la primera) envía correo.

### QA-06: Definir contraseña nueva y efectos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-07, RN-09
- **Precondiciones:** la cuenta tiene 4 intentos fallidos recientes.
- **Pasos:**
  1. Abrir el enlace vigente, ingresar `Pantalla-Nueva-65` dos veces y guardar.
  2. Intentar usar el navegador A y B.
  3. Iniciar sesión con la contraseña anterior y luego con la nueva.
  4. Reabrir el mismo enlace.
- **Resultado esperado:** mensaje "Tu contraseña fue actualizada. Inicia sesión con tu nueva contraseña."; sesiones A y B cerradas; la contraseña anterior falla y la nueva funciona; el contador de fallos se reinició; se recibe el correo "Tu contraseña fue cambiada — Seguimiento Compras Públicas"; el enlace reabierto muestra el mensaje de enlace no válido.

### QA-07: Restablecer levanta un bloqueo temporal

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-07
- **Precondiciones:** cuenta bloqueada temporalmente por intentos fallidos.
- **Pasos:**
  1. Restablecer la contraseña.
  2. Iniciar sesión de inmediato con la contraseña nueva.
- **Resultado esperado:** el inicio de sesión es exitoso sin esperar el fin del bloqueo.

### QA-08: Enlace vencido

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-03
- **Datos de prueba:**

  | Momento de uso | Esperado |
  | -------------- | -------- |
  | minuto 59 tras la solicitud | formulario disponible |
  | minuto 61 tras la solicitud | mensaje de enlace no válido |

- **Pasos:**
  1. Abrir el enlace en cada momento.
- **Resultado esperado:** según la tabla; en el minuto 61 no se puede cambiar la contraseña.

### QA-09: Enlace inexistente o vencido mientras se diligencia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Pasos:**
  1. Abrir un enlace con token `zzz999` inexistente.
  2. Abrir un enlace vigente al minuto 58, diligenciar y enviar al minuto 61.
- **Resultado esperado:** en ambos casos "El enlace para restablecer la contraseña no es válido o ya venció. Solicita uno nuevo."; la contraseña no cambia.

### QA-10: Contraseña nueva inválida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-06
- **Datos de prueba:**

  | Contraseña | Confirmación | Mensaje |
  | ---------- | ------------ | ------- |
  | `Tele-2026` (9) | igual | "La contraseña debe tener entre 10 y 128 caracteres." |
  | 129 caracteres | igual | "La contraseña debe tener entre 10 y 128 caracteres." |
  | `ana.rojas@ejemplo.org` | igual | "La contraseña no puede ser igual a tu correo." |
  | `Pantalla-Nueva-65` | `Pantalla-Nueva-66` | "Las contraseñas no coinciden." |

- **Pasos:**
  1. Enviar el formulario con cada combinación.
- **Resultado esperado:** mensaje correspondiente; la contraseña no cambia y el enlace sigue vigente (se puede reintentar con datos válidos).

### QA-11: Falla del servicio de correo al solicitar

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-10
- **Precondiciones:** existe un enlace vigente previo; servicio de correo configurado para fallar.
- **Pasos:**
  1. Solicitar el restablecimiento para `ana.rojas@ejemplo.org`.
- **Resultado esperado:** mensaje neutral; error en log; el enlace recién generado no es utilizable; el enlace previo sigue vigente.

### QA-12: Falla del correo de aviso de cambio

- **Tipo:** Integración
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Precondiciones:** el servicio de correo falla solo para el aviso de cambio.
- **Pasos:**
  1. Restablecer la contraseña con datos válidos.
- **Resultado esperado:** la contraseña se cambia y los efectos de RN-07 se aplican; el error del aviso queda en el log.

---

**Total de casos:** 12
