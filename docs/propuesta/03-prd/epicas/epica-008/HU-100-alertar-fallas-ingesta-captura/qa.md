# Casos de Prueba — HU-100: Alertar al Administrador ante una ingesta o captura fallida o retrasada

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la detección de ejecuciones fallidas y retrasadas, el plazo y el contenido de la alerta, la no duplicación, el aviso de recuperación, los reintentos de envío, la bitácora, la configuración de destinatarios y los permisos. Queda fuera: la notificación de suspensiones retail (FR-047) y la lógica de ingesta.

## Precondiciones y Datos Base

- Fecha de referencia: **2026-10-02 (UTC−05:00)**.
- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Destinatarios iniciales: `admin.po@prueba.co`. Plazo de alerta: 60 minutos. Tolerancia de retraso: 1 hora. Frecuencias: pública 24 h, retail 7 días.
- Servicio de correo simulado que registra los mensajes recibidos y permite simular indisponibilidad.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-04, RN-05 | QA-01 |
| RN-04 (límites del plazo) | QA-02 |
| Escenario 2, RN-03 | QA-03 |
| Escenario 3, RN-03 | QA-04 |
| RN-03 (fuente sin ejecuciones) | QA-05 |
| Escenario 4, RN-02 | QA-06 |
| Escenario 5, RN-06 | QA-07 |
| Escenario 6 | QA-08 |
| Escenario 7, RN-01 | QA-09 |
| Escenario 8, RN-07 | QA-10 |
| Escenario 9, RN-09 | QA-11 |
| Escenario 10, RN-09, RN-10 | QA-12 |
| Escenario 11, RN-08 | QA-13 |
| Escenario 12, RN-08 (rango máximo) | QA-14 |
| Escenario 13 | QA-15 |
| RN-05 (sin credenciales ni datos personales) | QA-16 |

---

## Casos de Prueba

### QA-01: Alerta por ejecución fallida dentro del plazo con el contenido completo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-04, RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Ejecución | 812, SECOP II — Contratos, programada | fin 2026-10-02 03:12, `fallida` |
  | Conteos | leídos 60, nuevos 0, actualizados 12, rechazados 1, errores 1 | — |
  | Mensaje | Tiempo de espera agotado tras 3 reintentos | — |

- **Pasos:**
  1. Registrar la ejecución fallida.
  2. Revisar el servicio de correo y la bitácora hasta las 04:12.
- **Resultado esperado:** antes de las 04:12 llega un correo a `admin.po@prueba.co` con asunto "[Compras Públicas] Falla en SECOP II — Contratos: ejecución fallida" y cuerpo con fuente, tipo, "2026-10-02 03:12", id 812, origen `programada`, los conteos, el mensaje y "Revise el estado de fuentes y relance la fuente si corresponde."; la bitácora registra la alerta con estado "Enviada".

### QA-02: Plazo de alerta configurable en sus límites

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Plazo | 5 | aceptado; alerta en ≤ 5 min |
  | Plazo | 60 | aceptado |
  | Plazo | 4 | rechazado, no cambia la configuración |
  | Plazo | 61 | rechazado, no cambia la configuración |

- **Pasos:**
  1. Configurar cada valor; para los aceptados, provocar una ejecución fallida.
- **Resultado esperado:** con 5 el correo llega en ≤ 5 minutos; con 60 en ≤ 60 minutos; 4 y 61 se rechazan con "El plazo de alerta debe ser un número entero entre 5 y 60 minutos." y el plazo vigente no cambia.

### QA-03: Alerta por ejecución retrasada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-03
- **Precondiciones:** última ejecución de TVEC — Ítems iniciada 2026-10-01 05:00; ninguna posterior.
- **Pasos:**
  1. Dejar transcurrir hasta 2026-10-02 06:01 sin ejecuciones.
- **Resultado esperado:** antes de 2026-10-02 07:00 llega el correo "[Compras Públicas] Falla en TVEC — Ítems: ejecución retrasada", con id e inicio de la última ejecución y próxima ejecución esperada "2026-10-02 05:00"; a las 06:00 exactas todavía no se considera retrasada.

### QA-04: Sin alertas de retraso repetidas para el mismo vencimiento

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Pasos:**
  1. Tras QA-03, dejar pasar 5 ciclos de verificación sin ejecuciones.
  2. Iniciar una ejecución de TVEC — Ítems a las 2026-10-02 09:00 y luego no ejecutar nada hasta 2026-10-03 10:01.
- **Resultado esperado:** en el paso 1 no llega ningún correo nuevo; en el paso 2 llega una nueva alerta de retraso (nuevo vencimiento).

### QA-05: Fuente que nunca se ejecutó no genera alerta de retraso

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-03
- **Precondiciones:** TVEC — Órdenes sin ninguna ejecución.
- **Pasos:**
  1. Ejecutar 3 ciclos de verificación.
- **Resultado esperado:** no se genera alerta para TVEC — Órdenes.

### QA-06: Una alerta por cada ejecución fallida, sin duplicados

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02
- **Pasos:**
  1. Registrar las ejecuciones fallidas 901 y 902 de SECOP II — Archivos.
  2. Forzar dos ciclos de verificación adicionales.
- **Resultado esperado:** exactamente 2 alertas (ids 901 y 902); los ciclos adicionales no generan más.

### QA-07: Aviso de recuperación solo tras una alerta previa

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | SECOP II — Contratos | fallida 812 alertada → exitosa 813 fin 2026-10-02 05:30 | se envía recuperación |
  | TVEC — Ítems | exitosa sin alerta previa | no se envía recuperación |
  | SECOP II — Contratos | exitosa 814 después de 813 | no se envía una segunda recuperación |

- **Pasos:**
  1. Registrar las ejecuciones en el orden de la tabla.
- **Resultado esperado:** solo se envía un correo "[Compras Públicas] Fuente recuperada: SECOP II — Contratos" con id 813 y hora 2026-10-02 05:30, registrado como tipo "Recuperación".

### QA-08: Ejecución manual fallida identifica origen y usuario

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Registrar una ejecución de TVEC — Órdenes con origen `manual`, usuario `admin.po@prueba.co`, resultado `fallida`.
- **Resultado esperado:** la alerta indica origen `manual` y usuario `admin.po@prueba.co`.

### QA-09: Fuentes suspendidas o sin captura automática no alertan retraso

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Alkosto | suspendida; última ejecución hace 8 días y 2 horas | sin alerta |
  | Falabella | sin captura automática | sin alerta |

- **Pasos:**
  1. Ejecutar un ciclo de verificación.
- **Resultado esperado:** no se genera ninguna alerta para estas fuentes.

### QA-10: Reintentos de envío y estado "No entregada"

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Servicio de correo | falla en el 1.er intento, acepta el 2.º | termina "Enviada" |
  | Servicio de correo | falla en los 4 intentos (inicial + 3) | termina "No entregada" |

- **Pasos:**
  1. Para cada configuración del servicio, provocar una ejecución fallida.
- **Resultado esperado:** en el primer caso la alerta queda "Enviada"; en el segundo hay exactamente 4 intentos dentro de los 60 minutos, la alerta queda "No entregada" con el último error del servicio y no hay más intentos después.

### QA-11: Configurar destinatarios válidos con auditoría

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-09
- **Pasos:**
  1. Como Administrador, configurar `po@comprastv.co` y `operacion@comprastv.co`.
  2. Provocar una ejecución fallida.
- **Resultado esperado:** la siguiente alerta llega a ambas direcciones con estado de envío por destinatario; existe un evento de auditoría de cambio de configuración con valor anterior `admin.po@prueba.co` y nuevo `po@comprastv.co, operacion@comprastv.co`.

### QA-12: Validación de la lista de destinatarios

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-09, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Lista | (vacía) | "Debe configurar al menos un destinatario de alertas." |
  | Lista | po@comprastv | "La dirección 'po@comprastv' no tiene un formato de correo válido." |
  | Lista | 6 direcciones válidas | "Se permiten como máximo 5 destinatarios de alertas." |
  | Lista | 5 direcciones válidas | aceptada |
  | Lista | po@comprastv.co, PO@comprastv.co | "La dirección 'PO@comprastv.co' está repetida." |

- **Pasos:**
  1. Intentar guardar cada lista.
- **Resultado esperado:** el mensaje indicado; en los rechazos la configuración vigente no cambia y no se registra auditoría.

### QA-13: Consultar la bitácora con filtros y orden

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-08
- **Precondiciones:** 3 alertas en los últimos 7 días (2 de SECOP II — Contratos, 1 de TVEC — Ítems) y 1 de hace 10 días.
- **Pasos:**
  1. Consultar la bitácora sin filtros.
  2. Consultar filtrando fuente "TVEC — Ítems".
- **Resultado esperado:** paso 1: 3 alertas (la de hace 10 días queda fuera del rango por defecto), de la más reciente a la más antigua, con todos los campos de RN-08; paso 2: 1 alerta.

### QA-14: Bitácora vacía y rango excesivo

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 12, RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Rango | 2026-01-01 a 2026-01-31 | sin alertas |
  | Rango | 2025-10-01 a 2026-10-02 | 366 días |

- **Pasos:**
  1. Consultar con cada rango.
- **Resultado esperado:** primero: "No hay alertas registradas en el período consultado."; segundo: "El rango de consulta no puede superar 365 días."

### QA-15: Analista no puede consultar la bitácora ni cambiar destinatarios

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como `analista1@prueba.co`, consultar la bitácora.
  2. Como `analista1@prueba.co`, cambiar los destinatarios.
- **Resultado esperado:** ambas devuelven "Acción no permitida: esta operación requiere el rol Administrador." y no se modifica nada.

### QA-16: La alerta no expone secretos ni datos personales

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Mensaje de error de la API | contiene la URL con el parámetro `$$app_token=TOKEN_FICTICIO_123` | — |

- **Pasos:**
  1. Provocar una ejecución fallida con ese mensaje.
- **Resultado esperado:** el correo y la bitácora no contienen `TOKEN_FICTICIO_123` ni ningún dato personal; el resto del mensaje se conserva.

---

**Total de casos:** 16
