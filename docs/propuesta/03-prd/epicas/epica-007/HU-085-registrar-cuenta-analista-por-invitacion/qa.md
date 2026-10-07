# Casos de Prueba — HU-085: Registrar cuenta de Analista mediante invitación con aceptación de términos y política de datos

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la validación del enlace de invitación en todos sus estados, el formulario de registro (nombre, contraseña, confirmación, casillas de aceptación), la precondición de documentos vigentes, el registro de la prueba de aceptación, la atomicidad e idempotencia y la ausencia de registro público. Queda fuera la emisión de invitaciones (HU-084) y el inicio de sesión (HU-086).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Invitación válida | `ana.rojas@ejemplo.org`, `Pendiente`, vence 09/10/2026 10:00 |
| Términos vigentes | versión `TDU-1.0` |
| Política vigente | versión `PTD-1.0` |
| Mínimo de contraseña | `longitud_minima_contrasena = 10` |
| Contraseña válida de referencia | `Televisor-2026` (14 caracteres) |
| Fecha de prueba | 2026-10-02 (UTC−5) |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-06 / RN-10 / RN-11 / RN-12 / RN-14 / RN-15 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 / RN-01 | QA-07 |
| Escenario 8 / RN-04 | QA-08, QA-09 |
| Escenario 9 / RN-05 | QA-10, QA-11 |
| Escenario 10 / RN-07 | QA-12 |
| Escenario 11 / RN-08 | QA-13 |
| Escenario 12 / RN-09 | QA-14 |
| Escenario 13 / RN-13 | QA-15 |
| Escenario 14 | QA-16 |
| RN-02 (revalidación al enviar) | QA-17 |

---

## Casos de Prueba

### QA-01: Registro exitoso

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-06, RN-10, RN-11, RN-12, RN-14, RN-15
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | nombre visible | `Ana Rojas` | |
  | contraseña / confirmación | `Televisor-2026` | |
  | casillas | ambas marcadas | |

- **Pasos:**
  1. Abrir el enlace de invitación válido y diligenciar.
  2. Pulsar "Crear cuenta".
  3. Revisar cuenta, aceptaciones, invitación y log de auditoría.
- **Resultado esperado:** redirección al inicio de sesión con "Tu cuenta fue creada. Inicia sesión para continuar."; cuenta `Activa`, rol `Analista`; contraseña almacenada solo como hash adaptativo (no aparece en claro en base ni logs); dos registros de aceptación (`terminos_uso` `TDU-1.0`, `politica_datos` `PTD-1.0`, fecha y hora, medio `registro_por_invitacion`); invitación `Usada` con fecha de uso; evento en auditoría; sin sesión iniciada.

### QA-02: Correo no editable

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | correo enviado en la solicitud | `otro@ejemplo.org` | manipulado |

- **Pasos:**
  1. Verificar que el campo correo es de solo lectura.
  2. Enviar el formulario manipulando el correo.
- **Resultado esperado:** la cuenta se crea con `ana.rojas@ejemplo.org`; no existe cuenta para `otro@ejemplo.org`.

### QA-03: Token inexistente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | token | `abc123` | no existe |

- **Pasos:**
  1. Abrir el enlace con el token.
- **Resultado esperado:** "El enlace de invitación no es válido."; no se muestra formulario.

### QA-04: Invitación vencida

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | vencimiento | 02/10/2026 09:59 con prueba a las 10:00 | vencida por 1 minuto |
  | vencimiento | 02/10/2026 10:01 con prueba a las 10:00 | vigente |

- **Pasos:**
  1. Abrir el enlace en cada caso.
- **Resultado esperado:** vencida → "Tu invitación venció. Solicita una nueva al administrador." y estado persistido `Vencida`; vigente → se muestra el formulario.

### QA-05: Invitación ya usada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5
- **Pasos:**
  1. Abrir el enlace de una invitación `Usada`.
- **Resultado esperado:** "Esta invitación ya fue usada. Inicia sesión con tu cuenta." con enlace al inicio de sesión; sin formulario.

### QA-06: Invitación reemplazada o revocada

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | estado | `Reemplazada` | |
  | estado | `Revocada` | |

- **Pasos:**
  1. Abrir el enlace en cada estado.
- **Resultado esperado:** "Esta invitación ya no está activa. Solicita una nueva al administrador."; sin formulario.

### QA-07: Registro sin invitación

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-01
- **Pasos:**
  1. Abrir la página de registro sin token.
  2. Enviar directamente una solicitud de registro sin token.
- **Resultado esperado:** "El registro solo está disponible por invitación."; no se crea cuenta.

### QA-08: Nombre visible con límites de longitud

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | nombre | (vacío) | nulo |
  | nombre | `A` | 1 carácter |
  | nombre | `Al` | 2, mínimo |
  | nombre | 80 letras | máximo |
  | nombre | 81 letras | máximo + 1 |
  | nombre | `   Ana    Rojas  ` | se normaliza a `Ana Rojas` |

- **Pasos:**
  1. Enviar el formulario con cada valor y el resto válido.
- **Resultado esperado:** vacío, 1 y 81 → "Ingresa un nombre de 2 a 80 caracteres, solo con letras, espacios, apóstrofo, punto o guion."; 2, 80 y el normalizado → cuenta creada (nombre guardado `Ana Rojas`).

### QA-09: Nombre visible con caracteres

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | nombre | `María José O'Neil-Peña Jr.` | permitido |
  | nombre | `Ana123` | dígitos |
  | nombre | `<b>Ana</b>` | símbolos |

- **Pasos:**
  1. Enviar el formulario con cada valor.
- **Resultado esperado:** el primero se acepta; los otros dos muestran el mensaje de nombre inválido.

### QA-10: Longitud de contraseña

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | contraseña | `Tele-2026` (9) | mínimo − 1 |
  | contraseña | `Tele--2026` (10) | mínimo |
  | contraseña | 128 caracteres | máximo |
  | contraseña | 129 caracteres | máximo + 1 |
  | contraseña | `mi clave de tv` (14, con espacios) | espacios permitidos |

- **Pasos:**
  1. Enviar el formulario con cada valor (confirmación igual).
- **Resultado esperado:** 9 y 129 → "La contraseña debe tener entre 10 y 128 caracteres."; 10, 128 y la que tiene espacios → cuenta creada.

### QA-11: Contraseña igual al correo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | contraseña | `ANA.ROJAS@EJEMPLO.ORG` | igual al correo sin distinguir mayúsculas |

- **Pasos:**
  1. Enviar el formulario.
- **Resultado esperado:** "La contraseña no puede ser igual a tu correo."; no se crea cuenta.

### QA-12: Confirmación distinta

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | contraseña | `Televisor-2026` | |
  | confirmación | `televisor-2026` | difiere en mayúscula |

- **Pasos:**
  1. Enviar el formulario.
- **Resultado esperado:** "Las contraseñas no coinciden."; no se crea cuenta.

### QA-13: Casillas de aceptación sin marcar

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 11, RN-08
- **Datos de prueba:**

  | Términos | Política | Resultado |
  | -------- | -------- | --------- |
  | sin marcar | marcada | mensaje de términos |
  | marcada | sin marcar | mensaje de política |
  | sin marcar | sin marcar | ambos mensajes |

- **Pasos:**
  1. Verificar que ambas casillas aparecen desmarcadas al cargar.
  2. Enviar con cada combinación.
- **Resultado esperado:** según la tabla, "Debes aceptar los términos de uso para crear tu cuenta." y/o "Debes aceptar la política de tratamiento de datos personales para crear tu cuenta."; no se crea cuenta; los enlaces a los documentos abren la versión vigente sin perder lo diligenciado.

### QA-14: Sin versión vigente de términos o política

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 12, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | términos vigentes | ninguno | política sí |
  | política vigente | ninguna | términos sí |

- **Pasos:**
  1. Abrir un enlace de invitación válido en cada configuración.
- **Resultado esperado:** "El registro no está disponible en este momento. Intenta más tarde o contacta al administrador."; evento en log de aplicación; la invitación sigue `Pendiente`.

### QA-15: Doble envío

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 13, RN-13
- **Pasos:**
  1. Enviar dos solicitudes de registro simultáneas con la misma invitación y datos válidos.
- **Resultado esperado:** una sola cuenta y un solo par de registros de aceptación; la segunda solicitud recibe "Esta invitación ya fue usada. Inicia sesión con tu cuenta."

### QA-16: Conservación de datos ante errores

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | nombre | `Ana Rojas` | |
  | contraseña | `corta` | inválida |
  | casillas | términos marcada, política sin marcar | |

- **Pasos:**
  1. Enviar el formulario.
- **Resultado esperado:** se muestran los errores; el nombre y el estado de las casillas se conservan; contraseña y confirmación quedan vacías.

### QA-17: Invitación revocada mientras se diligencia el formulario

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Pasos:**
  1. Abrir el enlace válido.
  2. El Administrador revoca la invitación.
  3. Enviar el formulario con datos válidos.
- **Resultado esperado:** "Esta invitación ya no está activa. Solicita una nueva al administrador."; no se crea cuenta.

---

**Total de casos:** 17
