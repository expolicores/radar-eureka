# Casos de Prueba — HU-099: Relanzar una ingesta o captura y reactivar una fuente suspendida

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueban las operaciones "relanzar" y "reactivar": precondiciones, exclusión mutua, registro de la ejecución manual, punto de partida de la ingesta incremental, ausencia de duplicados y de reprocesamiento con IA, límites retail, auditoría de la reactivación, mensajes y permisos. Queda fuera: la lógica interna de ingesta y captura de otras épicas, la detección de restricciones que suspende una fuente (FR-047) y el envío de alertas (HU-100).

## Precondiciones y Datos Base

- Fecha y hora de referencia: **2026-10-02 08:00 (UTC−05:00)**.
- Usuarios: `admin.po@prueba.co` (Administrador); `analista1@prueba.co` (Analista).
- Fuentes semilla:

  | Fuente | Estado de partida |
  | ----- | ----- |
  | SECOP II — Contratos | sin ejecuciones en curso; última exitosa con marca 2026-10-01 23:10 |
  | SECOP II — Archivos | sin ejecuciones en curso; 5 documentos `DOC-1001`…`DOC-1005` con extracción IA terminada |
  | TVEC — Ítems | ejecución `en_curso` desde 2026-10-02 07:40 |
  | TVEC — Órdenes | sin ninguna ejecución exitosa |
  | Alkosto | captura automática habilitada; suspendida desde 2026-09-28 10:15, motivo "Cambio en robots.txt que prohíbe la ruta de captura"; 1.250 solicitudes consumidas esta semana |
  | Falabella | sin captura automática habilitada; no suspendida |

- Configuración: ventana histórica desde 2023-01-01; reintentos = 3; límites retail 1 solicitud / 2 s y 2.000 / semana.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ----- | ----- |
| Escenario 1, RN-02, RN-05 | QA-01 |
| Escenario 2, RN-02 | QA-02 |
| Escenario 3, RN-03 | QA-03 |
| Escenario 4, RN-04 | QA-04 |
| Escenario 5, RN-04 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7, RN-09, RN-10 | QA-07 |
| Escenario 8, RN-09 (límites del motivo) | QA-08 |
| RN-09 (falla de auditoría) | QA-09 |
| Escenario 9, Escenario 10 | QA-10 |
| Escenario 11 | QA-11 |
| Escenario 12, RN-03 | QA-12 |
| Escenario 13, RN-06 | QA-13 |
| Escenario 14, RN-07 | QA-14 |
| Escenario 15, RN-08 | QA-15 |
| Escenario 16, RN-01 | QA-16 |
| Escenario 17 | QA-17 |

---

## Casos de Prueba

### QA-01: Relanzar una fuente pública desde la última marca exitosa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-02, RN-05
- **Pasos:**
  1. Como `admin.po@prueba.co`, relanzar "SECOP II — Contratos".
  2. Consultar el registro de la ejecución creada.
- **Resultado esperado:** respuesta inmediata "Ejecución {id} iniciada para SECOP II — Contratos."; la ejecución tiene origen `manual`, usuario `admin.po@prueba.co`, resultado inicial `en_curso`, y solo solicita registros con fecha de última actualización ≥ 2026-10-01 23:10.

### QA-02: Primera ejecución exitosa parte del inicio de la ventana histórica

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02
- **Pasos:**
  1. Relanzar "TVEC — Órdenes".
- **Resultado esperado:** "Ejecución {id} iniciada para TVEC — Órdenes."; la lectura parte de 2023-01-01.

### QA-03: Relanzar captura retail activa respetando límites

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Precondiciones:** Alkosto no suspendida (estado activo), 1.250 solicitudes consumidas.
- **Pasos:**
  1. Relanzar "Alkosto".
  2. Observar el ritmo de solicitudes de la ejecución.
- **Resultado esperado:** "Ejecución {id} iniciada para Alkosto."; la captura verifica `robots.txt` al iniciar, no supera 1 solicitud cada 2 segundos y se detiene si alcanza 2.000 solicitudes en la semana (consume como máximo 750 adicionales).

### QA-04: Rechazo por ejecución en curso

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04
- **Pasos:**
  1. Relanzar "TVEC — Ítems".
- **Resultado esperado:** "Ya existe una ejecución en curso para TVEC — Ítems, iniciada el 2026-10-02 07:40. Espere a que termine."; no se crea ejecución.

### QA-05: Doble solicitud simultánea crea una sola ejecución

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-04
- **Pasos:**
  1. Enviar dos solicitudes de relanzar "SECOP II — Contratos" con menos de 1 segundo de diferencia.
- **Resultado esperado:** existe una sola ejecución nueva; una respuesta es "Ejecución {id} iniciada para SECOP II — Contratos." y la otra el mensaje de ejecución en curso.

### QA-06: Rechazo por fuente suspendida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6
- **Pasos:**
  1. Relanzar "Alkosto" (suspendida).
- **Resultado esperado:** "La fuente Alkosto está suspendida desde 2026-09-28 10:15 (motivo: Cambio en robots.txt que prohíbe la ruta de captura). Reactívela antes de relanzar."; no se crea ejecución.

### QA-07: Reactivación exitosa con auditoría y sin lanzar ejecución

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-09, RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Motivo | Se verificó el robots.txt del 2026-10-02 y la ruta vuelve a estar permitida | 76 caracteres |

- **Pasos:**
  1. Reactivar "Alkosto" con el motivo.
  2. Consultar el log de auditoría y las ejecuciones de Alkosto.
- **Resultado esperado:** "La fuente Alkosto fue reactivada. La próxima captura verificará de nuevo robots.txt y las restricciones de acceso."; evento "Reactivación de fuente" con usuario, fecha y hora, estado anterior "Suspendida", nuevo "Activa", motivo de suspensión y motivo de reactivación; no se creó ninguna ejecución nueva.

### QA-08: Límites del motivo de reactivación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Motivo | (vacío) | rechazado |
  | Motivo | `Verificado` + 2 espacios al final | 10 caracteres efectivos → aceptado |
  | Motivo | `Revisado.` | 9 caracteres → rechazado |
  | Motivo | texto de 500 caracteres | aceptado |
  | Motivo | texto de 501 caracteres | rechazado |

- **Pasos:**
  1. Con Alkosto suspendida, intentar reactivar con cada motivo (volver a suspender entre intentos aceptados).
- **Resultado esperado:** los rechazados devuelven "Debe indicar un motivo de reactivación de 10 a 500 caracteres.", la fuente sigue suspendida y no hay evento de auditoría; los aceptados reactivan la fuente.

### QA-09: Falla al registrar la auditoría impide la reactivación

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Precondiciones:** el registro de auditoría no está disponible (simulado en el entorno de prueba).
- **Pasos:**
  1. Reactivar "Alkosto" con un motivo válido.
- **Resultado esperado:** "No fue posible registrar la auditoría; la reactivación no se aplicó. Intente de nuevo."; Alkosto sigue suspendida.

### QA-10: Reactivar fuente no suspendida o pública

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 9, Escenario 10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Fuente | Falabella | retail no suspendida |
  | Fuente | SECOP II — Contratos | pública |

- **Pasos:**
  1. Reactivar cada fuente con motivo válido.
- **Resultado esperado:** Falabella: "La fuente Falabella no está suspendida."; SECOP II — Contratos: "Solo las fuentes retail pueden suspenderse y reactivarse."; no hay cambios ni auditoría.

### QA-11: Rechazo por fuente sin captura automática

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11
- **Pasos:**
  1. Relanzar "Falabella".
- **Resultado esperado:** "La fuente Falabella no tiene captura automática habilitada; sus observaciones ingresan por carga manual o semiautomática."; no se crea ejecución.

### QA-12: Rechazo por límite semanal alcanzado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 12, RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Solicitudes consumidas en la semana | 1.999 | se permite relanzar |
  | Solicitudes consumidas en la semana | 2.000 | se rechaza |

- **Pasos:**
  1. Con Alkosto activa, fijar cada valor y relanzar.
- **Resultado esperado:** con 1.999 se crea la ejecución; con 2.000: "Se alcanzó el límite semanal de 2000 solicitudes configurado para Alkosto; la captura no se relanzó."

### QA-13: La ingesta relanzada no reprocesa documentos ya extraídos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 13, RN-06
- **Pasos:**
  1. Relanzar "SECOP II — Archivos" con una respuesta de la API que incluye `DOC-1001`…`DOC-1005`.
  2. Revisar la cola de extracción y los datos extraídos de esos documentos.
- **Resultado esperado:** ninguno de los 5 documentos entra a extracción con IA y sus datos extraídos quedan idénticos.

### QA-14: Releer registros ya guardados no los duplica

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 14, RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Registros ya guardados por la ejecución fallida | 40 (`CO1.PCCNTR.6000001`…`CO1.PCCNTR.6000040`) | 3 de ellos cambiaron su valor en la fuente |

- **Pasos:**
  1. Relanzar "SECOP II — Contratos" con una respuesta que incluye los 40 registros.
- **Resultado esperado:** siguen existiendo 40 registros con esos identificadores (sin duplicados); la ejecución reporta nuevos = 0 para ellos y actualizados = 3.

### QA-15: La ejecución relanzada que falla queda registrada como manual fallida

- **Tipo:** Integración
- **Prioridad:** Alta
- **Cubre:** Escenario 15, RN-08
- **Precondiciones:** la API de datos.gov.co simulada no responde.
- **Pasos:**
  1. Relanzar "SECOP II — Contratos".
  2. Esperar el fin de la ejecución.
- **Resultado esperado:** se observan 3 reintentos con espera creciente; la ejecución termina `fallida`, con origen `manual`, usuario `admin.po@prueba.co` y mensaje de error principal no vacío.

### QA-16: Fuente inexistente y nombre sin tildes

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** Escenario 16, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ----- |
  | Fuente | Éxito | inexistente (relanzar y reactivar) |
  | Fuente | secop ii — contratos | válida |

- **Pasos:**
  1. Relanzar cada valor; reactivar "Éxito".
- **Resultado esperado:** "Éxito" devuelve "La fuente 'Éxito' no existe. Fuentes válidas: SECOP II — Contratos, SECOP II — Archivos, TVEC — Ítems, TVEC — Órdenes, Alkosto, Falabella." en ambas operaciones; "secop ii — contratos" se relanza.

### QA-17: Analista no puede relanzar ni reactivar

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 17
- **Pasos:**
  1. Como `analista1@prueba.co`, relanzar "SECOP II — Contratos".
  2. Como `analista1@prueba.co`, reactivar "Alkosto" con motivo válido.
- **Resultado esperado:** ambas devuelven "Acción no permitida: esta operación requiere el rol Administrador."; no se crea ejecución ni cambia la suspensión.

---

**Total de casos:** 17
