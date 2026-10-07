# Casos de Prueba — HU-112: Registrar el log de auditoría y aplicar la retención de logs

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban el registro de cada tipo de evento con sus campos, el evento por registro en acciones masivas, la atomicidad, la cobertura de todas las vías, la inmutabilidad, el truncado y enmascarado, la depuración por retención de auditoría y de logs de aplicación, los cambios de retención y la verificación de integridad. Queda fuera: la consulta del log (HU-113) y la lógica funcional de cada acción auditada (otras HU y épicas).

## Precondiciones y Datos Base

- Usuarios: `admin.po@prueba.co` (Administrador/Revisor); `analista1@prueba.co` (Analista).
- Datos: ítem 1 de CO1.PCCNTR.5030063 con cantidad 80; ítem candidato con clasificación "requiere revisión"; configuración vigente versión 3 (umbral mismo modelo 30).
- Retenciones: auditoría 12 meses; logs de aplicación 30 días.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-01, RN-02 | QA-01 |
| Escenario 2, RN-01 | QA-02 |
| Escenario 3, RN-03 | QA-03 |
| Escenario 4, RN-01 | QA-04 |
| RN-01 (eventos propios de la épica) | QA-05 |
| Escenario 5, RN-04 | QA-06 |
| Escenario 6, RN-05 | QA-07 |
| Escenario 7, RN-06 | QA-08 |
| Escenario 8, RN-07 | QA-09 |
| Escenario 9, RN-08 | QA-10 |
| Escenario 10, RN-09 | QA-11 |
| Escenario 11, RN-10 | QA-12 |
| Escenario 12, RN-11 | QA-13 |

---

## Casos de Prueba

### QA-01: Evento de corrección con todos los campos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02
- **Pasos:**
  1. Corregir la cantidad de 80 a 8 con comentario "Se leyó 80 por un error de OCR".
  2. Leer el último evento.
- **Resultado esperado:** tipo "Corrección de dato extraído"; id consecutivo; fecha con segundos UTC−05:00; usuario `admin.po@prueba.co`; rol Administrador; entidad ítem e id; campo "cantidad"; anterior 80; nuevo 8; comentario; origen `interfaz` o `comando o script` según la vía usada; id de operación.

### QA-02: Evento de clasificación manual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-01
- **Pasos:**
  1. Cambiar la clasificación a "excluido" con motivo "Comodato, no es compra".
- **Resultado esperado:** evento "Clasificación manual" con anterior "requiere revisión", nuevo "excluido" y motivo.

### QA-03: Carga manual y semiautomática

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Observación manual | Alkosto, TV 55" LG 55UR8750, 2.199.900 COP | — |
  | Archivo | observaciones_falabella.csv con 12 filas válidas | — |

- **Pasos:**
  1. Registrar la observación manual.
  2. Cargar el archivo.
- **Resultado esperado:** 1 evento "Carga manual de observación"; 12 eventos "Carga semiautomática de observación" con el mismo id de operación, nombre y hash del archivo, origen `carga de archivo`.

### QA-04: Evento de cambio de configuración

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-01
- **Pasos:**
  1. Cambiar el umbral de mismo modelo a 25 con motivo válido.
- **Resultado esperado:** evento "Cambio de configuración" con parámetro, anterior 30, nuevo 25, versión 4 y motivo.

### QA-05: Eventos de las acciones administrativas de la épica

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Acción | Tipo de evento esperado |
  | ----- | ----- |
  | Reactivar Alkosto | Reactivación de fuente |
  | Marcar CO1.PCCNTR.4946355 en la muestra | Marcado de muestra de validación |
  | Retirar CO1.PCCNTR.4946355 | Retiro de muestra de validación |
  | Cargar la plantilla de validación | Carga de resultados de validación |

- **Pasos:**
  1. Ejecutar cada acción.
- **Resultado esperado:** un evento del tipo indicado por acción.

### QA-06: Sin auditoría no hay acción

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Precondiciones:** almacenamiento de auditoría no disponible (simulado).
- **Pasos:**
  1. Corregir la cantidad del ítem a 8.
  2. Cambiar un parámetro de configuración.
- **Resultado esperado:** ambas responden "No fue posible registrar la auditoría; la acción no se aplicó. Intente de nuevo."; la cantidad sigue en 80 y la versión de configuración no cambia.

### QA-07: Acciones por script quedan auditadas

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 6, RN-05
- **Pasos:**
  1. Como `admin.po@prueba.co`, ejecutar el script administrativo que corrige 3 precios unitarios.
- **Resultado esperado:** 3 eventos "Corrección de dato extraído" con origen `comando o script`, el usuario y un id de operación común.

### QA-08: Inmutabilidad del log

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-06
- **Pasos:**
  1. Como Administrador, intentar modificar el evento 1520.
  2. Como Administrador y como Analista, intentar borrarlo.
- **Resultado esperado:** todos los intentos devuelven "El log de auditoría no admite modificaciones ni borrados."; el evento no cambia.

### QA-09: Truncado y enmascarado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Valor anterior | 4.000 caracteres | se guarda completo |
  | Valor anterior | 4.001 / 6.000 caracteres | 4.000 + "[truncado]" + SHA-256 del completo |
  | Parámetro con token | `app_token=TOKEN_FICTICIO_123` | se guarda "****" |

- **Pasos:**
  1. Ejecutar acciones con cada valor.
- **Resultado esperado:** el almacenamiento indicado; `TOKEN_FICTICIO_123` no aparece en el log de auditoría ni en los logs de aplicación.

### QA-10: Depuración de auditoría por retención

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-08
- **Datos de prueba:**

  | Evento | Fecha | Nota |
  | ----- | ----- | ----- |
  | E-A | 2026-10-01 23:59:59 | se elimina |
  | E-B | 2026-10-02 00:00:00 | se conserva (límite) |
  | E-C | 2027-05-10 | se conserva |

- **Pasos:**
  1. Con fecha simulada 2027-10-02, ejecutar la depuración diaria.
  2. Ejecutarla de nuevo el mismo día.
- **Resultado esperado:** paso 1: solo E-A eliminado y evento "Depuración de auditoría" con cantidad y rango; paso 2: nada que eliminar y ningún evento nuevo.

### QA-11: Depuración de logs de aplicación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-09
- **Datos de prueba:**

  | Log | Antigüedad | Nota |
  | ----- | ----- | ----- |
  | L-1 | 31 días | se elimina |
  | L-2 | 30 días | se conserva |
  | Evento de auditoría | 40 días | se conserva |

- **Pasos:**
  1. Ejecutar la depuración diaria.
- **Resultado esperado:** solo L-1 eliminado; el evento de auditoría intacto.

### QA-12: Cambios de retención

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-10
- **Datos de prueba:**

  | Campo | Valor | Resultado esperado |
  | ----- | ----- | ----- |
  | Retención auditoría | 1 / 24 / 120 | aceptados, evento "Cambio de configuración" |
  | Retención auditoría | 0 / 121 | "La retención de auditoría debe ser un número entero entre 1 y 120 meses." |
  | Retención logs aplicación | 1 / 365 | aceptados |
  | Retención logs aplicación | 0 / 366 | "La retención de logs de aplicación debe ser un número entero entre 1 y 365 días." |
  | Cualquier cambio | como `analista1@prueba.co` | "Acción no permitida: esta operación requiere el rol Administrador." |

- **Pasos:**
  1. Aplicar cada cambio con motivo válido.
- **Resultado esperado:** el resultado indicado.

### QA-13: Verificación de integridad

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-11
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Secuencia | 1 a 2.000 completa | íntegro |
  | Secuencia | 1 a 300 eliminados por depuración registrada | íntegro |
  | Secuencia | falta el id 1.733 sin depuración (borrado simulado fuera de la aplicación) | saltos detectados |

- **Pasos:**
  1. Ejecutar la verificación en cada situación.
- **Resultado esperado:** "Log de auditoría íntegro: {n} eventos, sin saltos de numeración fuera de las depuraciones registradas." en los dos primeros; "Se detectaron saltos de numeración: 1733." en el tercero.

---

**Total de casos:** 13
