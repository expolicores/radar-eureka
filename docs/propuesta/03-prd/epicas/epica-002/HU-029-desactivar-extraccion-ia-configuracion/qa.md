# Casos de Prueba — HU-029: Activar o desactivar la extracción con IA por configuración sin afectar las funciones determinísticas

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el interruptor de extracción con IA: cambio sin redespliegue, ausencia de llamadas a IA con el interruptor inactivo, procesos pendientes, extracciones en curso, funciones determinísticas no afectadas, reactivación, reextracción solicitada, registro, consulta y validaciones. El servicio de IA se sustituye por uno simulado que cuenta las solicitudes recibidas.

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Interruptor inicial "activa".
- Procesos en "documentos preparados": `CO1.BDOS.1234567` y otros 11 de prueba con fechas de preparación distintas.
- Ítems ya extraídos y aceptados en `CO1.BDOS.8888888`.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-02, RN-08 | QA-01 |
| Escenario 2 / RN-03, RN-04 | QA-02 |
| Escenario 3 / RN-03 | QA-03 |
| Escenario 4 / RN-05 | QA-04, QA-05 |
| Escenario 5 / RN-06 | QA-06 |
| Escenario 6 / RN-07 | QA-07 |
| Escenario 7 / RN-09 | QA-08 |
| Escenario 8 / RN-01 | QA-09 |
| Escenario 9 / RN-08 | QA-10 |
| Permisos | QA-11 |

---

## Casos de Prueba

### QA-01: Desactivar sin redespliegue

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02, RN-08
- **Pasos:**
  1. Como Administrador, cambiar el interruptor a "inactiva" con comentario "Pausa por revisión de calidad".
  2. Sin reiniciar la aplicación, ejecutar una extracción programada.
- **Resultado esperado:** el servicio simulado no recibe solicitudes; el registro muestra usuario, fecha y hora, "activa" → "inactiva" y el comentario.

### QA-02: Proceso nuevo con IA inactiva queda pendiente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03, RN-04
- **Pasos:**
  1. Con el interruptor inactivo, llevar `CO1.BDOS.1234567` a "documentos preparados" y ejecutar la extracción.
- **Resultado esperado:** 0 solicitudes al servicio de IA; el proceso queda "pendiente de extracción (IA desactivada)" con su fecha de preparación.

### QA-03: Extracción en curso termina

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-03
- **Pasos:**
  1. Iniciar la extracción de `CO1.BDOS.5555555` con el servicio simulado respondiendo en 60 s y un segundo proceso en cola.
  2. A los 10 s, desactivar el interruptor.
- **Resultado esperado:** `CO1.BDOS.5555555` termina y registra su resultado; el segundo proceso no se envía y queda pendiente por IA desactivada.

### QA-04: Funciones determinísticas siguen operando

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Con el interruptor inactivo, ejecutar listado, priorización, descarga, descompresión, lectura de formatos y detección de páginas sobre un proceso nuevo.
  2. Validar y corregir un ítem de `CO1.BDOS.8888888`.
- **Resultado esperado:** todas las operaciones terminan con el mismo resultado que con la IA activa; 0 solicitudes al servicio de IA.

### QA-05: Datos ya extraídos siguen disponibles

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** RN-05
- **Pasos:**
  1. Con el interruptor inactivo, consultar los ítems aceptados de `CO1.BDOS.8888888` y su evidencia.
- **Resultado esperado:** los ítems siguen "aceptado automáticamente" o "validado", disponibles para comparación, con evidencia consultable.

### QA-06: Reactivación procesa los pendientes por antigüedad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-06
- **Datos de prueba:**

  | Proceso | Fecha de preparación |
  | ------- | -------------------- |
  | P-A | 2026-09-20 |
  | P-B | 2026-09-25 |
  | P-C | 2026-09-22 |
  | (otros 9) | 2026-09-26 a 2026-10-01 |

- **Pasos:**
  1. Reactivar el interruptor.
  2. Ejecutar la extracción programada.
- **Resultado esperado:** se extraen los 12, empezando por P-A, luego P-C, luego P-B; ninguno queda pendiente por IA desactivada.

### QA-07: Reextracción solicitada con IA inactiva

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Pasos:**
  1. Con el interruptor inactivo, solicitar la reextracción de `CO1.BDOS.8888888`.
  2. Reactivar y ejecutar la extracción programada.
- **Resultado esperado:** paso 1: mensaje "La extracción con IA está desactivada; la solicitud se ejecutará cuando se reactive" y proceso pendiente; paso 2: se reextrae.

### QA-08: Consulta del estado

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-09
- **Datos de prueba:**

  | Caso | Situación | Esperado |
  | ---- | --------- | -------- |
  | A | Inactiva con 12 pendientes | estado "inactiva", último cambio y comentario, 12 pendientes |
  | B | Activa tras procesar todos | estado "activa", 0 pendientes |

- **Pasos:**
  1. Consultar el estado en cada situación.
- **Resultado esperado:** el de la tabla.

### QA-09: Valor inválido y comentario largo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-01, RN-08
- **Datos de prueba:**

  | Valor | Comentario | Resultado |
  | ----- | ---------- | --------- |
  | parcial | — | "Valor no permitido: use 'activa' o 'inactiva'" |
  | (vacío) | — | mismo mensaje |
  | inactiva | 501 caracteres | rechazado por longitud del comentario (máximo 500) |
  | inactiva | 500 caracteres | aceptado |

- **Pasos:**
  1. Guardar cada configuración partiendo de "activa".
- **Resultado esperado:** el de la tabla; ante un rechazo se conserva el valor anterior.

### QA-10: Cambio al mismo valor

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** Escenario 9 / RN-08
- **Pasos:**
  1. Con el interruptor inactivo, cambiarlo a "inactiva".
- **Resultado esperado:** respuesta "La extracción con IA ya está inactiva"; no se agrega registro.

### QA-11: Permisos

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Como `analista1@piloto.test`, intentar cambiar y consultar el interruptor.
- **Resultado esperado:** acceso denegado en ambas operaciones; el valor no cambia.

---

**Total de casos:** 11
