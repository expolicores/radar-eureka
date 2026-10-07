# Casos de Prueba — HU-012: Clasificación asistida por IA de candidatos que requieren revisión

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el envío de candidatos en revisión a un servicio de IA simulado: sugerencias, aceptación automática con umbral, validación de respuestas, indisponibilidad del servicio, IA deshabilitada, candidatos no elegibles, configuración, datos enviados y estado vacío.

Queda fuera: la calidad real del modelo (se calibra con la revisión manual) y la cola de revisión (HU-013).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Servicio de IA simulado (doble de prueba) con respuestas configurables.
- Configuración inicial: IA habilitada; aceptación automática deshabilitada; sin umbral.
- Candidatos en "Requiere revisión" (método "Regla"), `estado_ia = Sin procesar`:

  | Id | Tipo | Texto | Regla |
  |---|---|---|---|
  | IT-01 | Ítem TVEC | Monitor TV 43 pulgadas para CCTV | R6 |
  | IT-02 | Ítem SECOP II | KIT TELEVISOR 43 + BARRA DE SONIDO | R8b |
  | CT-01 | Contrato SECOP II | Dotación de equipos para auditorio (entidad: Alcaldía de Ensayo; proveedor: Comercializadora Demo Ltda.) | C7 |

- Candidato IT-03 "Televisor Samsung 55" con clasificación vigente "Incluido" por regla; IT-04 con clasificación vigente manual.

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-08 | QA-01 |
| Escenario 2 / RN-09 | QA-02 |
| Escenario 3 / RN-09 | QA-03 |
| Escenario 4 / RN-05, RN-06 | QA-04, QA-05 |
| Escenario 5 / RN-07 | QA-06, QA-07 |
| Escenario 6 / RN-01 | QA-08 |
| Escenario 7 / RN-02 | QA-09 |
| Escenario 8 / RN-01 | QA-10 |
| Escenario 9 | QA-11 |
| RN-03 | QA-12 |
| RN-10 | QA-13 |
| RN-13 | QA-14 |

---

## Casos de Prueba

### QA-01: Sugerencia sin aceptación automática

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Respuesta IA para IT-01 | Excluido / Producto excluido: monitor o CCTV / "Se describe como monitor para circuito cerrado" / 0,95 | |

- **Pasos:**
  1. Ejecutar la clasificación asistida.
- **Resultado esperado:** evento de sugerencia con todos los campos de RN-08 y `aceptada_automaticamente = no`; IT-01 sigue "Requiere revisión" con `estado_ia = Sugerencia disponible`.

### QA-02: Aceptación automática en el umbral y por encima

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-09
- **Precondiciones:** aceptación automática habilitada, umbral 0,85.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Confianza para IT-01 (Excluido) | 0,92 | aceptada |
  | Confianza para CT-01 (Excluido, "Información insuficiente") | 0,85 | igual al umbral → aceptada |

- **Pasos:**
  1. Ejecutar la clasificación asistida.
- **Resultado esperado:** ambos con clasificación vigente "Excluido", método "IA", criterio "IA — {categoría}", confianza; IT-01 "Clasificado"; CT-01 en nivel "Preliminar (contrato)"; `estado_ia = Aceptada automáticamente`.

### QA-03: Por debajo del umbral o propuesta de revisión

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-09
- **Precondiciones:** aceptación automática habilitada, umbral 0,85.
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | IT-01 | Excluido, 0,84 | umbral − 0,01 → sugerencia |
  | IT-02 | Requiere revisión, 0,99 | nunca se acepta |

- **Pasos:**
  1. Ejecutar.
- **Resultado esperado:** ambos quedan "Requiere revisión" con sugerencia registrada (`aceptada_automaticamente = no`).

### QA-04: Respuestas inválidas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Respuesta | sin `confianza` | campo faltante |
  | Respuesta | resultado "Dudoso" | fuera de lista |
  | Respuesta | categoría "Electrodoméstico" | fuera de lista |
  | Respuesta | confianza 1,2 | fuera de rango |
  | Respuesta | texto libre no estructurado | no interpretable |
  | Respuesta | justificación "Posible sobreprecio del kit" | término prohibido |
  | Respuesta | justificación de 501 caracteres | excede límite |

- **Pasos:**
  1. Configurar el doble para devolver la respuesta inválida 3 veces seguidas para IT-02.
- **Resultado esperado:** 3 intentos en la ejecución; cada uno registra "Respuesta de IA inválida: {motivo}"; IT-02 queda `estado_ia = Fallida` y "Requiere revisión"; no se guarda ninguna sugerencia.

### QA-05: Respuesta inválida recuperada en reintento

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-06
- **Pasos:**
  1. Devolver para IT-02 primero una respuesta sin `confianza` y luego una válida.
- **Resultado esperado:** se registra un intento inválido y la sugerencia válida queda guardada; `estado_ia = Sugerencia disponible`.

### QA-06: Servicio no disponible entre ejecuciones

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Pasos:**
  1. Responder HTTP 503 en los 4 intentos para IT-01 y ejecutar 3 veces.
- **Resultado esperado:** tras la 1.ª y 2.ª ejecución `estado_ia = Pendiente de reintento` (esperas 2, 4, 8 s en cada una); tras la 3.ª, `Fallida`; IT-01 sigue "Requiere revisión".

### QA-07: Error no recuperable del servicio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Pasos:**
  1. Responder HTTP 401.
- **Resultado esperado:** un solo intento, `estado_ia = Fallida`, log "El servicio de IA rechazó la solicitud (HTTP 401)" sin la credencial.

### QA-08: IA deshabilitada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-01
- **Pasos:**
  1. Configurar `clasificacion_ia_habilitada = no`.
  2. Ejecutar la clasificación por reglas y el comando de clasificación asistida.
- **Resultado esperado:** 0 solicitudes al servicio; el comando informa "La clasificación asistida por IA está deshabilitada."; la clasificación por reglas termina normalmente.

### QA-09: Candidatos no elegibles

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-02
- **Pasos:**
  1. Ejecutar la clasificación asistida.
- **Resultado esperado:** IT-03 (Incluido por regla) e IT-04 (manual) no se envían.

### QA-10: Validación del umbral

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Umbral | (vacío) | rechazo |
  | Umbral | 0,49 | rechazo |
  | Umbral | 0,50 | aceptado |
  | Umbral | 1,00 | aceptado |
  | Umbral | 1,01 | rechazo |

- **Pasos:**
  1. Habilitar la aceptación automática con cada umbral.
- **Resultado esperado:** los rechazados muestran "Para habilitar la aceptación automática defina un umbral entre 0,50 y 1,00." y se conserva la configuración anterior.

### QA-11: Sin candidatos en revisión

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9
- **Pasos:**
  1. Ejecutar sin candidatos elegibles.
- **Resultado esperado:** 0 solicitudes; "No hay candidatos pendientes de clasificación asistida."

### QA-12: Datos enviados a la IA

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-03, RN-12
- **Pasos:**
  1. Capturar la solicitud enviada para CT-01.
- **Resultado esperado:** incluye objeto, descripción, UNSPSC, criterio C7 y el límite de categoría; no incluye "Alcaldía de Ensayo", "Comercializadora Demo Ltda." ni ningún identificador; la credencial no aparece en logs.

### QA-13: Reinicio del estado de IA tras cambio en la fuente

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Con IT-01 en "Sugerencia disponible", cambiar su descripción en la fuente y reclasificar por reglas (sigue en R6).
- **Resultado esperado:** `estado_ia = Sin procesar` y se envía de nuevo en la siguiente ejecución; la sugerencia anterior se conserva en el historial.

### QA-14: Resumen

- **Tipo:** Positivo
- **Prioridad:** Baja
- **Cubre:** RN-13
- **Pasos:**
  1. Con aceptación automática deshabilitada, ejecutar con respuestas válidas para IT-01 y CT-01 e inválidas permanentes para IT-02.
- **Resultado esperado:** "Clasificación asistida por IA: 3 enviados. Sugerencias: 2. Aceptadas automáticamente: 0. Respuestas inválidas: 3. Pendientes de reintento: 0. Fallidas: 1."

---

**Total de casos:** 14
