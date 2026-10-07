# Casos de Prueba — HU-091: Crear un caso de investigación desde un contrato

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la creación del caso desde la ficha de un contrato SECOP II y de una orden TVEC, el título sugerido, las validaciones, el contenido de la instantánea (ítems, información insuficiente, resumen de señales, datos ausentes, exclusión de datos personales), su inmutabilidad, la cancelación, el doble envío, la falla al guardar y la privacidad. Queda fuera la creación desde señal (HU-090).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, sesión activa |
| Otro analista | `luis.mora@ejemplo.org` |
| Contrato C-1 | `CO1.PCCNTR.5598765`, SECOP II, Municipio de Tunja, mínima cuantía, firma 02/05/2025, estado "comparado", 1 ítem LG 55UR7300 55" × 4 a $2.100.000 `explicito`, con IVA, 2 señales vigentes |
| Contrato C-2 | `CO1.PCCNTR.5600001`, SECOP II, estado "documentos obtenidos", sin ítems extraídos |
| Contrato C-3 | SECOP II con 1 ítem "información insuficiente", motivo "No se publica precio unitario" |
| Orden O-1 | orden TVEC `TVEC-123456`, sin número de proceso |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-02 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-01 | QA-03 |
| Escenario 4 / RN-04 / RN-05 / RN-11 | QA-04 |
| Escenario 5 | QA-05 |
| Escenario 6 / RN-07 | QA-06 |
| Escenario 7 / RN-03 | QA-07 |
| Escenario 8 / RN-06 | QA-08 |
| Escenario 9 / RN-08 | QA-09, QA-10 |
| RN-09 | QA-11 |
| RN-10 | QA-12 |

---

## Casos de Prueba

### QA-01: Crear caso desde la ficha de un contrato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-02
- **Pasos:**
  1. En la ficha de C-1, pulsar "Crear caso" y "Crear" con el título sugerido.
- **Resultado esperado:** "Caso creado con el contrato guardado." con "Abrir caso"; el caso tiene un único elemento de tipo contrato con fecha y hora de captura.

### QA-02: Título sugerido

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Pasos:**
  1. Abrir "Crear caso" en C-1.
- **Resultado esperado:** título `Contrato — CO1.PCCNTR.5598765 — Municipio de Tunja`, editable.

### QA-03: Título y descripción inválidos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-01
- **Datos de prueba:**

  | Campo | Valor | Esperado |
  | ----- | ----- | -------- |
  | título | `ab` | "Ingresa un título de 3 a 120 caracteres." |
  | título | 121 caracteres | "Ingresa un título de 3 a 120 caracteres." |
  | título | 120 caracteres | aceptado |
  | descripción | 1.001 caracteres | "La descripción admite máximo 1.000 caracteres." |
  | descripción | 1.000 caracteres | aceptado |

- **Pasos:**
  1. Crear caso con cada valor.
- **Resultado esperado:** según la tabla; en los errores no se crea caso.

### QA-04: Instantánea completa del contrato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-04, RN-05, RN-11
- **Pasos:**
  1. Crear caso desde C-1 y consultar la instantánea.
- **Resultado esperado:** incluye fuente SECOP II, identificador, URL, entidad, proveedor, objeto, modalidad, valor como dato de referencia, fechas, departamento y municipio, estado "comparado", el ítem LG con sus datos, resumen de 2 señales, documentos y fecha de corte; los campos sin dato muestran "No disponible"; no aparece ningún dato bancario ni documento de identidad.

### QA-05: Contrato sin ítems o con información insuficiente

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Datos de prueba:**

  | Contrato | Esperado en la instantánea |
  | -------- | -------------------------- |
  | C-2 | estado "documentos obtenidos" y "Sin ítems de televisor extraídos" |
  | C-3 | ítem con motivo "No se publica precio unitario" |

- **Pasos:**
  1. Crear un caso desde cada contrato.
- **Resultado esperado:** ambos casos se crean con lo indicado en la tabla.

### QA-06: Contrato con señales

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-07
- **Pasos:**
  1. Crear caso desde C-1.
  2. Revisar elementos del caso.
- **Resultado esperado:** un único elemento (contrato) con el resumen de 2 señales (identificador, ítem, benchmark, desviación, confianza); no hay elementos de tipo señal; se muestra "Para conservar el detalle y la evidencia de una señal, guárdala en el caso desde su detalle."

### QA-07: Orden de compra TVEC

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7, RN-03
- **Pasos:**
  1. Crear caso desde la ficha de O-1.
- **Resultado esperado:** instantánea con fuente "TVEC", identificador `TVEC-123456`; número de proceso "No disponible".

### QA-08: Inmutabilidad tras extracción posterior

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. Crear caso desde C-2.
  2. Simular la extracción de 3 ítems y la generación de una señal para C-2.
  3. Consultar la instantánea.
- **Resultado esperado:** sigue mostrando "Sin ítems de televisor extraídos", "Sin señales" y la fecha de captura original.

### QA-09: Cancelar y doble envío

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-08
- **Pasos:**
  1. Abrir "Crear caso" y cancelar.
  2. Enviar dos solicitudes de creación idénticas seguidas.
- **Resultado esperado:** al cancelar no hay caso; con doble envío existe un solo caso.

### QA-10: Falla al guardar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-08
- **Precondiciones:** el almacenamiento simula un error.
- **Pasos:**
  1. Crear caso desde C-1 con título `Tunja 2025`.
- **Resultado esperado:** "No pudimos crear el caso. Intenta de nuevo."; sin caso ni instantánea; el formulario conserva `Tunja 2025`; error en log.

### QA-11: Lenguaje no acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Revisar los textos generados por el sistema en el formulario, mensajes e instantánea contra la lista de términos prohibidos.
- **Resultado esperado:** ninguno contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### QA-12: Privacidad del caso

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-10
- **Pasos:**
  1. Ana crea un caso desde C-1.
  2. Luis solicita el caso por su identificador.
- **Resultado esperado:** "No encontramos este caso."; no aparece en "Mis casos" de Luis.

---

**Total de casos:** 12
