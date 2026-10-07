# Casos de Prueba — HU-097: Restringir el acceso a casos, elementos y notas únicamente a su autor

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la regla de autoría en todas las operaciones sobre casos, elementos y notas con los perfiles autor, otro Analista, Administrador no autor y sin sesión; la respuesta uniforme; recursos derivados; listados y conteos; identificadores no adivinables; ausencia de efectos; registro de intentos denegados sin contenido; y la suite automática. Quedan fuera los roles en general (HU-089).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Autora | `ana.rojas@ejemplo.org`, caso A "Compra TV 65 Gobernación" con instantánea de señal I-1, evidencia E-doc y nota N1 |
| Otro Analista | `luis.mora@ejemplo.org`, con 2 casos |
| Administrador | `admin.po@ejemplo.org`, sin ser autor de A |
| Identificador inexistente | identificador aleatorio válido en formato que no corresponde a ningún caso |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 | QA-01 |
| Escenario 2 / RN-02 / RN-04 / RN-06 | QA-02, QA-03 |
| Escenario 3 / RN-01 / RN-08 | QA-04 |
| Escenario 4 | QA-05 |
| Escenario 5 | QA-06 |
| Escenario 6 | QA-07 |
| Escenario 7 / RN-07 | QA-08 |
| Escenario 8 / RN-10 | QA-09 |
| RN-03 | QA-10 |
| RN-05 | QA-11 |
| RN-09 | QA-12 |

---

## Casos de Prueba

### QA-01: La autora opera sobre su caso

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01
- **Pasos:**
  1. Con la sesión de Ana, listar casos, abrir A, ver I-1, abrir E-doc, guardar un contrato, agregar, editar y eliminar una nota.
- **Resultado esperado:** todas las operaciones se permiten.

### QA-02: Otro Analista sobre el caso ajeno

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-02, RN-04, RN-06
- **Datos de prueba:**

  | Operación de Luis sobre A |
  | ------------------------- |
  | abrir el detalle |
  | ver la instantánea I-1 |
  | abrir el documento E-doc desde el caso |
  | guardar un elemento |
  | agregar una nota |
  | editar N1 |
  | eliminar N1 |

- **Pasos:**
  1. Enviar cada solicitud directa con la sesión de Luis.
- **Resultado esperado:** todas responden "No encontramos este caso." sin datos; A, I-1 y N1 no cambian.

### QA-03: Respuesta idéntica para ajeno e inexistente

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-04
- **Pasos:**
  1. Con la sesión de Luis, abrir A y abrir el identificador inexistente.
  2. Comparar mensaje, código de respuesta y contenido.
- **Resultado esperado:** ambas respuestas son idénticas.

### QA-04: Administrador no autor

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-01, RN-08
- **Pasos:**
  1. Con la sesión del Administrador, repetir las operaciones de QA-02 sobre A.
  2. Revisar las funciones administrativas disponibles.
- **Resultado esperado:** todas responden "No encontramos este caso."; no existe consulta ni reporte de casos de analistas en las funciones administrativas.

### QA-05: Recursos derivados por identificador propio

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:**
  1. Con la sesión de Luis, solicitar I-1 y N1 por su identificador sin indicar el caso.
- **Resultado esperado:** "No encontramos este caso." sin datos.

### QA-06: Sin sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. Sin sesión, solicitar la lista de casos, el detalle de A y crear una nota en A.
- **Resultado esperado:** ninguna se ejecuta; todas dirigen al inicio de sesión con "Inicia sesión para continuar."

### QA-07: Listados y conteos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Con la sesión de Ana, abrir "Mis casos" y el selector "Guardar en caso".
- **Resultado esperado:** solo aparecen casos de Ana; los totales no incluyen los 2 casos de Luis.

### QA-08: Registro de intentos denegados sin contenido

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-07
- **Pasos:**
  1. Ejecutar QA-02 y revisar el log de aplicación.
- **Resultado esperado:** un registro por intento con usuario `luis.mora@ejemplo.org`, operación, identificador solicitado, fecha y hora; ningún registro contiene título, descripción, notas ni contenido de instantáneas.

### QA-09: Suite automática de autorización

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-10
- **Pasos:**
  1. Ejecutar la suite.
  2. Introducir en un entorno de prueba una operación de notas sin verificación de autoría y ejecutar la suite de nuevo.
- **Resultado esperado:** (1) cubre el 100 % de las operaciones con los cuatro perfiles y pasa; (2) la suite falla señalando la operación defectuosa.

### QA-10: Parámetro de autor manipulado

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-03
- **Pasos:**
  1. Con la sesión de Luis, abrir A enviando un parámetro o cabecera de autor `ana.rojas@ejemplo.org`.
  2. Con la sesión de Luis, crear un caso enviando autor `ana.rojas@ejemplo.org`.
- **Resultado esperado:** (1) "No encontramos este caso."; (2) el caso creado tiene como autor a Luis.

### QA-11: Identificadores no adivinables

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-05
- **Pasos:**
  1. Crear 3 casos y 3 notas seguidos y comparar sus identificadores.
- **Resultado esperado:** identificadores aleatorios sin secuencia ni relación con títulos o fechas.

### QA-12: Indicadores agregados sin contenido

- **Tipo:** Negativo
- **Prioridad:** Baja
- **Cubre:** RN-09
- **Precondiciones:** existe algún indicador administrativo que use casos.
- **Pasos:**
  1. Con la sesión del Administrador, consultar ese indicador.
- **Resultado esperado:** solo muestra conteos agregados; ningún título, nota ni contenido de casos.

---

**Total de casos:** 12
