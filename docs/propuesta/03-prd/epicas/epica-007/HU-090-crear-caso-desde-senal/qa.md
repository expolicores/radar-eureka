# Casos de Prueba — HU-090: Crear un caso de investigación desde una señal

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la creación del caso desde el detalle de una señal, el título sugerido, las validaciones de título y descripción, el contenido completo de la instantánea (incluidos datos ausentes y estados de Benchmark 2), su inmutabilidad ante recálculos, la señal no vigente, la cancelación, el doble envío, la falla al guardar, el lenguaje y la privacidad. Quedan fuera la creación desde contrato (HU-091) y la vista del caso (HU-096).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org`, sesión activa |
| Otro analista | `luis.mora@ejemplo.org`, sesión activa |
| Señal S-1 | contrato `CO1.PCCNTR.5512345`, Gobernación de Santander, firma 14/03/2026; ítem 8 televisores Samsung UN65DU7000 de 65", precio unitario $4.250.000 `explicito`, con IVA; Benchmark 1 mediana $2.990.000 con 9 observaciones (TVEC y SECOP II), ventana ±6 meses; Benchmark 2 "referencia de mercado disponible" con 2 observaciones (Alkosto, 1 manual); desviación +42 %; mismo modelo; regla umbral porcentual; confianza "Medio"; evidencia: `oferta_economica.pdf`, página 3 |
| Señal S-2 | contrato TVEC sin fecha de firma disponible, sin modelo extraído, Benchmark 2 "no disponible / evidencia insuficiente" |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-01 / RN-04 | QA-01 |
| Escenario 2 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-03 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 5 / Escenario 6 / RN-06 | QA-06 |
| Escenario 7 / RN-07 | QA-07 |
| Escenario 8 / RN-08 | QA-08 |
| Escenario 9 | QA-09 |
| Escenario 10 / RN-09 | QA-10 |
| Escenario 11 / RN-09 | QA-11 |
| RN-10 | QA-12 |
| RN-11 | QA-13 |

---

## Casos de Prueba

### QA-01: Crear caso desde una señal

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | título | sugerido sin cambios | |
  | descripción | `Revisar estudios previos y oferta.` | |

- **Pasos:**
  1. En el detalle de S-1, pulsar "Crear caso" y luego "Crear".
  2. Pulsar "Abrir caso".
- **Resultado esperado:** "Caso creado con la señal guardada."; el caso tiene autora Ana, fecha de creación y de última actualización iguales, identificador no secuencial y un único elemento de tipo señal con fecha y hora de captura.

### QA-02: Título sugerido

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 2
- **Datos de prueba:**

  | Señal | Título sugerido esperado |
  | ----- | ------------------------ |
  | S-1 | `Señal — Gobernación de Santander — 14/03/2026` |
  | S-2 | `Señal — {entidad}` sin fecha |
  | señal de una entidad con nombre de 130 caracteres | recortado a 120 caracteres |

- **Pasos:**
  1. Abrir "Crear caso" en cada señal.
- **Resultado esperado:** según la tabla; el título es editable.

### QA-03: Validación del título

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-02
- **Datos de prueba:**

  | Título | Esperado |
  | ------ | -------- |
  | (vacío) | error |
  | `   ` | error |
  | `TV` (2) | error |
  | `TVs` (3) | aceptado |
  | 120 caracteres | aceptado |
  | 121 caracteres | error |
  | `  Caso TV  ` | aceptado como `Caso TV` |

- **Pasos:**
  1. Crear caso con cada título.
- **Resultado esperado:** errores con "Ingresa un título de 3 a 120 caracteres." y sin caso creado; aceptados crean el caso.

### QA-04: Descripción en el límite

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4, RN-03
- **Datos de prueba:**

  | Descripción | Esperado |
  | ----------- | -------- |
  | (vacía) | caso sin descripción |
  | 1.000 caracteres | aceptado |
  | 1.001 caracteres | "La descripción admite máximo 1.000 caracteres." |
  | `<script>alert(1)</script>` | guardado y mostrado como texto plano |

- **Pasos:**
  1. Crear caso con cada descripción.
- **Resultado esperado:** según la tabla.

### QA-05: Instantánea completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-05
- **Pasos:**
  1. Crear caso desde S-1 y consultar la instantánea.
- **Resultado esperado:** contiene ítem (Samsung, UN65DU7000, 65", 8 unidades, $4.250.000, `explicito`, con IVA), contrato (`CO1.PCCNTR.5512345`, entidad, proveedor, SECOP II, 14/03/2026, valor de referencia, URL), Benchmark 1 (referencia estadística, $2.990.000, 9 observaciones, ±6 meses) con cada observación (origen, precio, fecha, método), Benchmark 2 ("referencia de mercado disponible", 2 observaciones, una marcada manual), fórmula, +42 %, mismo modelo, regla umbral porcentual, confianza "Medio", evidencia (`oferta_economica.pdf`, página 3, hash, URL), fecha de corte y la advertencia "Esta señal no constituye una conclusión ni una acusación; indica un caso que merece revisión."

### QA-06: Datos ausentes y Benchmark 2 no disponible

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5, Escenario 6, RN-06
- **Pasos:**
  1. Crear caso desde S-2 y consultar la instantánea.
- **Resultado esperado:** modelo y fecha de firma figuran como "No disponible"; Benchmark 2 figura como "no disponible / evidencia insuficiente"; en ningún lugar aparece "precio de mercado" ni se usa el valor del contrato como precio unitario.

### QA-07: Instantánea inmutable tras recálculo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-07
- **Pasos:**
  1. Crear caso desde S-1.
  2. Recalcular benchmarks de modo que S-1 pase a +35 % y confianza "Alto".
  3. Recalcular de modo que S-1 deje de existir.
  4. Consultar la instantánea después de cada recálculo.
- **Resultado esperado:** la instantánea sigue mostrando +42 %, "Medio" y la misma fecha y hora de captura en ambos casos.

### QA-08: Señal no vigente al confirmar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8, RN-08
- **Pasos:**
  1. Abrir "Crear caso" en S-1.
  2. Recalcular de modo que S-1 desaparezca.
  3. Pulsar "Crear".
- **Resultado esperado:** "Esta señal ya no está disponible. Actualiza la página para ver la información vigente."; no se crea caso.

### QA-09: Cancelar la creación

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 9
- **Pasos:**
  1. Abrir "Crear caso", escribir un título y pulsar "Cancelar".
  2. Repetir cerrando el formulario con la tecla Escape.
- **Resultado esperado:** no se crea caso; se permanece en el detalle de la señal.

### QA-10: Doble envío

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 10, RN-09
- **Pasos:**
  1. Enviar dos solicitudes de creación idénticas seguidas.
- **Resultado esperado:** un solo caso con una sola instantánea en "Mis casos".

### QA-11: Falla al guardar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-09
- **Precondiciones:** el almacenamiento de instantáneas simula un error.
- **Pasos:**
  1. Crear caso desde S-1 con título `Caso Santander`.
- **Resultado esperado:** "No pudimos crear el caso. Intenta de nuevo."; no existe caso ni instantánea; el formulario conserva `Caso Santander`; error en log.

### QA-12: Lenguaje no acusatorio en textos del sistema

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Revisar título sugerido, etiquetas, mensajes y la instantánea del caso creado desde S-1 contra la lista de términos prohibidos.
- **Resultado esperado:** ningún texto generado por el sistema contiene "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal".

### QA-13: El caso solo es visible para su autora

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-11
- **Pasos:**
  1. Ana crea un caso desde S-1.
  2. Luis abre "Mis casos" y solicita el caso de Ana por su identificador.
- **Resultado esperado:** el caso no aparece en la lista de Luis y la solicitud directa responde "No encontramos este caso."

---

**Total de casos:** 13
