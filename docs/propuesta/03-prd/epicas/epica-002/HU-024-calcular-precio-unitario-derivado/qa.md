# Casos de Prueba — HU-024: Calcular el precio unitario derivado solo cuando se cumplen las seis condiciones

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la evaluación de las seis condiciones, la decisión de cálculo, la fórmula y el redondeo, las prohibiciones de FR-099 y FR-100, los datos guardados, la confianza reducida, el recalculo tras corrección y el funcionamiento sin IA. Los insumos se suministran como resultado simulado de HU-022 y HU-023.

## Precondiciones y Datos Base

- Usuarios `admin.po@piloto.test` (Administrador) y `analista1@piloto.test` (Analista).
- Factor de derivación 0,80.
- Ítem base `CO1.PCCNTR.6100001-01`: sin precio explícito; cantidad 8 (Contrato 012-2024.pdf v1, página 1, confianza 0,90); valor total 17.200.000,00 `con_iva` (Aceptacion de oferta.pdf v1, página 2, confianza 0,85); etapa "adjudicado"; condiciones 2–5 reportadas "cumple" con soporte, salvo que el caso diga otra cosa.
- Contrato base con `valor_del_contrato` en datos abiertos = 89.800.000.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04, RN-05, RN-07, RN-08 | QA-01 |
| Escenario 2 / RN-02, RN-06 | QA-02 |
| Escenario 3 / RN-02 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 / RN-04 | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| RN-03 (condición 1) | QA-07 |
| Escenario 7 / RN-06, RN-01 | QA-08 |
| Escenario 8 / RN-01 | QA-09 |
| Escenario 9 / RN-03 | QA-10 |
| Escenario 10 / RN-09 | QA-11, QA-12 |
| Escenario 11 / RN-05 | QA-13 |
| RN-08 (factor configurable) | QA-14 |
| RN-10 / Permisos | QA-15 |

---

## Casos de Prueba

### QA-01: Precio derivado con las seis condiciones

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04, RN-05, RN-07, RN-08
- **Pasos:**
  1. Evaluar el precio derivado del ítem base.
- **Resultado esperado:** precio 2.150.000,00; `precio_unitario_tipo = derivado`; indicador "sí"; fórmula "17.200.000,00 / 8"; valor total usado 17.200.000,00 y cantidad 8 con sus documentos y ubicaciones; seis condiciones "cumple" con soporte; etapa "adjudicado"; base `con_iva`; confianza 0,68.

### QA-02: Contrato mixto

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02, RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Valor total documentado | 45.000.000 | Incluye 10 computadores y 2 televisores |
  | Cantidad de TV | 2 | |
  | Condición 2 | no cumple | |
  | Condición 4 | no cumple | |

- **Pasos:**
  1. Evaluar el precio derivado.
- **Resultado esperado:** no hay precio derivado (ningún 22.500.000); motivo entregado "condiciones de precio derivado no cumplidas: 2, 4".

### QA-03: Instalación incluida

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-02
- **Pasos:**
  1. Evaluar con el valor "suministro e instalación de 6 televisores 55 pulgadas con soporte de pared" (condiciones 2 y 5 "no cumple").
- **Resultado esperado:** sin precio derivado; motivo "condiciones de precio derivado no cumplidas: 2, 5".

### QA-04: Modelos distintos en el mismo valor

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-02
- **Pasos:**
  1. Evaluar un valor total que cubre 4 TV de 43" y 2 de 65" (condición 3 "no cumple").
- **Resultado esperado:** sin precio derivado; motivo "condiciones de precio derivado no cumplidas: 3".

### QA-05: Condición no determinable

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-04
- **Pasos:**
  1. Evaluar con la condición 5 "no determinable".
- **Resultado esperado:** sin precio derivado; motivo "condiciones de precio derivado no cumplidas: 5 (no determinable)".

### QA-06: "Cumple" sin soporte se trata como no determinable

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Caso | Condición 2 |
  | ---- | ----------- |
  | A | "cumple" sin texto ni ubicación |
  | B | "cumple" con texto pero sin ubicación |

- **Pasos:**
  1. Evaluar cada caso.
- **Resultado esperado:** en ambos, condición 2 "no determinable", sin precio derivado; motivo "condiciones de precio derivado no cumplidas: 2 (no determinable)".

### QA-07: Cantidad sin evidencia propia

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-03
- **Pasos:**
  1. Evaluar un ítem cuya cantidad no tiene evidencia propia (fue descartada en la extracción) y cuyo total sí la tiene.
- **Resultado esperado:** no se evalúa el precio derivado, porque falta un insumo con evidencia (RN-01); el motivo lo asigna HU-025.

### QA-08: El valor de datos abiertos nunca se usa

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-06, RN-01
- **Pasos:**
  1. Evaluar un ítem sin valor total documental, cantidad 8, contrato con valor en datos abiertos 89.800.000.
- **Resultado esperado:** no se evalúa ni calcula precio derivado; no aparece 11.225.000 en ningún campo del ítem.

### QA-09: Existe precio explícito

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-01
- **Pasos:**
  1. Evaluar un ítem con precio explícito 2.150.000, total 17.200.000 y cantidad 8.
- **Resultado esperado:** no se deriva; el precio sigue `explicito`.

### QA-10: Condición 6 según el motivo de la base indeterminada

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-03
- **Datos de prueba:**

  | Base del total | Motivo | Condición 6 | Resultado |
  | -------------- | ------ | ----------- | --------- |
  | indeterminada | declaraciones tributarias contradictorias | no cumple | sin precio derivado |
  | indeterminada | sin declaración tributaria en el documento | cumple | derivado con base `indeterminada` |
  | sin_iva | — | cumple | derivado con base `sin_iva` |
  | con_iva, pero la extracción reporta partes con bases distintas | — | no cumple | sin precio derivado |

- **Pasos:**
  1. Evaluar cada caso.
- **Resultado esperado:** el de la tabla.

### QA-11: Recalculo tras corrección de cantidad

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 10 / RN-09
- **Pasos:**
  1. Tras QA-01, el Administrador corrige la cantidad a 10.
- **Resultado esperado:** precio derivado 1.720.000,00, fórmula "17.200.000,00 / 10"; el historial guarda 2.150.000,00 con fecha y usuario.

### QA-12: Corrección que elimina el derivado

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-09
- **Pasos:**
  1. Tras QA-01, el Administrador corrige la condición 5 a "no cumple" (el valor incluye transporte).
- **Resultado esperado:** el precio derivado se elimina del ítem (queda en el historial) y se entrega el motivo "condiciones de precio derivado no cumplidas: 5".

### QA-13: Redondeo

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 11 / RN-05
- **Datos de prueba:**

  | Valor total | Cantidad | Precio esperado |
  | ----------- | -------- | --------------- |
  | 10.000.000,00 | 3 | 3.333.333,33 |
  | 20.000.000,00 | 3 | 6.666.666,67 |
  | 1.000.000,05 | 2 | 500.000,03 |
  | 1.999.999,00 | 1 | 1.999.999,00 |

- **Pasos:**
  1. Evaluar cada caso con las seis condiciones cumplidas.
- **Resultado esperado:** el de la tabla.

### QA-14: Factor de derivación configurable

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-08
- **Datos de prueba:**

  | Factor | Resultado |
  | ------ | --------- |
  | 0,09 | rechazado: "El factor de derivación debe estar entre 0,10 y 0,99" |
  | 0,10 | aceptado; confianza QA-01 = 0,09 |
  | 0,99 | aceptado; confianza QA-01 = 0,84 |
  | 1,00 | rechazado |

- **Pasos:**
  1. Como Administrador, guardar cada factor y reevaluar QA-01 con los aceptados.
- **Resultado esperado:** el de la tabla; ante un rechazo se conserva el factor anterior.

### QA-15: Funciona sin IA y permisos

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** RN-10 / Permisos requeridos
- **Pasos:**
  1. Desactivar la extracción con IA y reevaluar QA-01.
  2. Como `analista1@piloto.test`, consultar el precio derivado e intentar cambiar el factor.
- **Resultado esperado:** la reevaluación funciona sin llamadas al servicio de IA; el Analista ve precio, indicador, fórmula e insumos, y recibe acceso denegado al cambiar el factor.

---

**Total de casos:** 15
