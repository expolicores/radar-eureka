# Casos de Prueba — HU-092: Guardar señales, contratos y evidencias en un caso existente

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba guardar cada tipo de elemento (señal, contrato, evidencia de documento de origen y de observación de referencia) en un caso propio, el selector (casos propios, estado vacío, crear caso nuevo), duplicados, el mismo elemento en casos distintos, el máximo configurable, elementos no disponibles, inmutabilidad, fallas, doble envío y la protección de casos ajenos. Quedan fuera la creación de casos desde las acciones "Crear caso" (HU-090, HU-091) y la vista del caso (HU-096).

## Precondiciones y Datos Base

| Dato | Valor |
| ---- | ----- |
| Analista | `ana.rojas@ejemplo.org` con casos A "Compra TV 65 Gobernación" (3 elementos) y B "Tunja 2025" (0 notas, 1 elemento) |
| Otra analista | `marta.diaz@ejemplo.org` sin casos |
| Otro analista | `luis.mora@ejemplo.org` con caso L "Caso de Luis" |
| Señal S-3 | contrato `CO1.PCCNTR.5512399`, desviación +55 %, producto equivalente, confianza "Bajo" |
| Contrato C-1 | `CO1.PCCNTR.5598765`, Municipio de Tunja |
| Evidencia E-doc | `oferta_economica.pdf`, página 3, precio unitario $4.250.000 (de la señal S-1) |
| Evidencia E-obs | observación Alkosto manual, LG 55UR7300, $2.399.900 con IVA, 10/03/2026 (de S-1) |
| Parámetro | `max_elementos_por_caso = 100` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04 / RN-11 | QA-01 |
| Escenario 2 / RN-05 | QA-02 |
| Escenario 3 / RN-06 (a) | QA-03 |
| Escenario 4 / RN-06 (b) | QA-04 |
| Escenario 5 / RN-03 | QA-05 |
| Escenario 6 | QA-06 |
| Escenario 7 / RN-09 | QA-07 |
| Escenario 8 / RN-08 / RN-09 | QA-08 |
| Escenario 9 / RN-10 | QA-09, QA-10 |
| Escenario 10 | QA-11 |
| Escenario 11 / RN-12 | QA-12 |
| RN-02 | QA-13, QA-14 |
| RN-07 | QA-15 |

---

## Casos de Prueba

### QA-01: Guardar una señal en un caso existente

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-04, RN-11
- **Pasos:**
  1. En el detalle de S-3, pulsar "Guardar en caso", elegir A y "Guardar".
- **Resultado esperado:** "Señal guardada en el caso «Compra TV 65 Gobernación»."; A tiene 4 elementos; la instantánea de S-3 contiene +55 %, producto equivalente, "Bajo", benchmarks, observaciones, evidencia de origen, fecha de corte y advertencia; la fecha de última actualización de A cambia.

### QA-02: Guardar un contrato

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-05
- **Pasos:**
  1. En la ficha de C-1, guardar en A.
- **Resultado esperado:** "Contrato guardado en el caso «Compra TV 65 Gobernación»."; instantánea con los datos de RN-05.

### QA-03: Guardar evidencia de documento de origen

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-06 (a)
- **Pasos:**
  1. En el detalle de S-1, pulsar "Guardar en caso" en E-doc y elegir B.
- **Resultado esperado:** "Evidencia guardada en el caso «Tunja 2025»."; elemento `documento_origen` con identificador, `oferta_economica.pdf`, tipo, página 3, hash, URL original, fuente, fecha de descarga, "precio unitario: $4.250.000", contrato y señal de origen.

### QA-04: Guardar observación de referencia manual

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-06 (b)
- **Pasos:**
  1. Guardar E-obs en B.
- **Resultado esperado:** elemento `observacion_referencia` con origen retail Alkosto, LG 55UR7300, vendedor, $2.399.900, con IVA, 10/03/2026, método "manual", indicador de observación manual, referencia y evidencia adjunta.

### QA-05: Crear caso nuevo desde el selector

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 5, RN-03
- **Datos de prueba:**

  | Título | Esperado |
  | ------ | -------- |
  | `Equivalentes 55` | caso creado |
  | `ab` | "Ingresa un título de 3 a 120 caracteres." |

- **Pasos:**
  1. En S-3, "Guardar en caso" → "Crear caso nuevo" con cada título.
- **Resultado esperado:** con título válido, "Caso creado con el elemento guardado." y el caso tiene S-3 como único elemento; con título inválido no se crea nada.

### QA-06: Selector sin casos

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Con la sesión de Marta, abrir "Guardar en caso" en S-3.
- **Resultado esperado:** "Aún no tienes casos." y solo la opción "Crear caso nuevo".

### QA-07: Elemento duplicado en el mismo caso

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-09
- **Datos de prueba:**

  | Elemento repetido en A | Esperado |
  | ---------------------- | -------- |
  | S-3 | rechazado |
  | C-1 | rechazado |
  | E-doc (misma página) | rechazado |
  | evidencia del mismo documento, página 4 | aceptado |

- **Pasos:**
  1. Guardar cada elemento en A cuando ya existe.
- **Resultado esperado:** rechazados con "Este elemento ya está guardado en el caso «Compra TV 65 Gobernación»." y sin nueva instantánea; la página 4 se agrega.

### QA-08: Mismo elemento en dos casos con instantáneas independientes

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-08, RN-09
- **Pasos:**
  1. Guardar S-3 en A.
  2. Recalcular de modo que S-3 pase a +48 %.
  3. Guardar S-3 en B.
- **Resultado esperado:** A muestra +55 %; B muestra +48 %; cada una con su fecha de captura.

### QA-09: Máximo de elementos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 9, RN-10
- **Datos de prueba:**

  | Elementos actuales en A | Esperado al guardar uno más |
  | ----------------------- | --------------------------- |
  | 99 | se agrega (queda en 100) |
  | 100 | "El caso alcanzó el máximo de 100 elementos guardados. Crea un caso nuevo para continuar." |

- **Pasos:**
  1. Guardar un elemento en cada situación.
- **Resultado esperado:** según la tabla.

### QA-10: Reducción del máximo por debajo de un caso existente

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Pasos:**
  1. Con A en 50 elementos, configurar `max_elementos_por_caso = 40`.
  2. Abrir A e intentar guardar un elemento.
  3. Intentar configurar 9 y 501.
- **Resultado esperado:** A conserva sus 50 elementos y rechaza el nuevo con el mensaje de máximo (40); 9 y 501 se rechazan por fuera del rango 10 a 500.

### QA-11: Elemento no disponible

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Pasos:**
  1. Abrir el detalle de S-3; recalcular de modo que S-3 desaparezca; pulsar "Guardar".
- **Resultado esperado:** "Este elemento ya no está disponible. Actualiza la página para ver la información vigente."; A no cambia.

### QA-12: Falla al guardar y doble envío

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 11, RN-12
- **Pasos:**
  1. Con error simulado en el almacenamiento, guardar S-3 en A.
  2. Sin error, enviar dos solicitudes idénticas de guardar C-1 en B.
- **Resultado esperado:** (1) "No pudimos guardar el elemento. Intenta de nuevo.", A sin cambios y error en log; (2) B tiene una sola instantánea de C-1.

### QA-13: Selector solo con casos propios y orden

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Pasos:**
  1. Con la sesión de Ana, abrir el selector tras actualizar B más recientemente que A.
- **Resultado esperado:** aparecen B y luego A, con título y fecha de actualización; L de Luis no aparece.

### QA-14: Guardar en caso ajeno por solicitud directa

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** RN-02
- **Pasos:**
  1. Con la sesión de Ana, enviar una solicitud para guardar S-3 en L.
- **Resultado esperado:** "No encontramos este caso."; L no cambia.

### QA-15: Datos ausentes en la instantánea

- **Tipo:** Borde
- **Prioridad:** Baja
- **Cubre:** RN-07
- **Precondiciones:** observación de referencia TVEC sin vendedor ni URL.
- **Pasos:**
  1. Guardar esa observación en A.
- **Resultado esperado:** vendedor y URL figuran como "No disponible".

---

**Total de casos:** 15
