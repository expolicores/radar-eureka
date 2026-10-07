# Casos de Prueba — HU-039: Clasificar el resultado de emparejamiento de cada ítem

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la consolidación del resultado de emparejamiento por ítem objetivo: precedencia, etiquetas, motivos, resumen de criterios, lenguaje, indicador de cobertura del 100 %, ítems pendientes, recálculo, ítems inactivos y errores. Queda fuera la generación de los pares (HU-035, HU-036, HU-038).

## Precondiciones y Datos Base

- Reglas `televisor` v1 vigentes.
- Ítems objetivo activos y sus pares vigentes:

| id_origen | Pares MISMO_MODELO | Pares EQUIVALENTE | Pares en conflicto | Otros datos |
|---|---|---|---|---|
| TVEC-1601 | 3 (2 por marca y modelo, 1 por EAN) | 12 | 0 | SAMSUNG · UN55DU8000KXZL |
| SEC-2601-I1 | 0 | 8 (1 con `modelos_distintos = sí`) | 0 | 65" / 4K / LED / SI |
| SEC-2602-I1 | 0 | 0 | 0 | motivo `SIN_CANDIDATOS_QUE_CUMPLAN` |
| TVEC-1602 | 0 | 0 | 2 | — |
| TVEC-1603 | 0 | 0 | 0 | `SIN_ATRIBUTOS_MINIMOS` |
| SEC-2603-I1 | 0 | 0 | 0 | `ATRIBUTOS_OBLIGATORIOS_FALTANTES: tamano_pulgadas` |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-03, RN-06 | QA-01 |
| Escenario 2 / RN-06 | QA-02 |
| Escenario 3 / RN-04 | QA-03, QA-04 |
| Escenario 4 / RN-04 | QA-05 |
| Escenario 5 / RN-04 | QA-06 |
| Escenario 6 / RN-02, RN-07 | QA-07, QA-08 |
| Escenario 7 / RN-08 | QA-09, QA-10 |
| Escenario 8 / RN-08 | QA-11 |
| RN-06 (lenguaje no acusatorio) | QA-12 |
| RN-09 | QA-08 |

---

## Casos de Prueba

### QA-01: Mismo modelo tiene precedencia

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03, RN-06
- **Resultado esperado:** TVEC-1601 con `clasificacion = MISMO_MODELO`, etiqueta "Mismo modelo", conteos 3 / 12 / 0 y resumen "Mismo modelo: 3 productos con la misma marca y modelo (SAMSUNG · UN55DU8000KXZL); 1 por código EAN/GTIN".

### QA-02: Equivalente con resumen de criterios

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-06
- **Resultado esperado:** SEC-2601-I1 con `EQUIVALENTE`, etiqueta "Producto equivalente" y resumen "Producto equivalente: 8 productos con tamaño 65", resolución 4K, tecnología LED y Smart; no evaluados: marca, generación; incluye referencias de modelo distintas".

### QA-03: Insuficiente por falta de candidatos

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Resultado esperado:** SEC-2602-I1 con `INSUFICIENTE_NO_CONFIABLE`, etiqueta "Insuficiente / no confiable", motivo `SIN_CANDIDATOS_QUE_CUMPLAN` con el texto "Ningún otro televisor cumple todos los criterios de equivalencia configurados."

### QA-04: Insuficiente por atributos obligatorios faltantes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 3 / RN-04
- **Resultado esperado:** SEC-2603-I1 con motivo `ATRIBUTOS_OBLIGATORIOS_FALTANTES` y texto "Faltan características obligatorias para buscar equivalentes: tamaño."

### QA-05: Solo pares en conflicto

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-04
- **Resultado esperado:** TVEC-1602 con `INSUFICIENTE_NO_CONFIABLE`, `conflicto = 2` y motivo `SOLO_PARES_EN_CONFLICTO` con texto "Hay 2 productos con la misma marca y modelo pero con características contradictorias; requieren revisión."

### QA-06: Sin atributos mínimos

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-04
- **Resultado esperado:** TVEC-1603 con `INSUFICIENTE_NO_CONFIABLE` y motivo `SIN_ATRIBUTOS_MINIMOS`.

### QA-07: Indicador de cobertura al 100 %

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-02, RN-07
- **Pasos:**
  1. Ejecutar el cálculo completo con los 6 ítems base.
  2. Consultar el indicador.
- **Resultado esperado:** 6 ítems activos, 6 con resultado vigente, 100,00 %; cada resultado tiene uno de los tres valores; ninguno nulo.

### QA-08: Ítem con error queda pendiente

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-07, RN-09
- **Pasos:**
  1. Simular un error al calcular TVEC-1603 y ejecutar.
  2. Consultar el indicador.
  3. Eliminar la causa y ejecutar de nuevo.
- **Resultado esperado:** paso 2: 5 de 6 (83,33 %), lista con TVEC-1603 y `clasificacion_pendiente = sí`; el resto del lote se procesó. Paso 3: 100,00 % y `clasificacion_pendiente = no`.

### QA-09: Recalcular ante un nuevo par mismo modelo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Agregar un par vigente `MISMO_MODELO` a SEC-2601-I1 y recalcular.
- **Resultado esperado:** nuevo resultado vigente `MISMO_MODELO`; el resultado `EQUIVALENTE` anterior queda `vigente = no` con fecha y versión de reglas.

### QA-10: Pérdida de pares y reejecución sin cambios

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Dejar sin pares vigentes a SEC-2601-I1 (todos pasan a no vigentes) y recalcular.
  2. Recalcular sin cambios.
- **Resultado esperado:** paso 1: resultado `INSUFICIENTE_NO_CONFIABLE` con su motivo. Paso 2: no se crea resultado nuevo.

### QA-11: Ítem inactivo

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-08
- **Pasos:**
  1. Inactivar TVEC-1602 y recalcular.
- **Resultado esperado:** su resultado pasa a `vigente = no`; el indicador muestra 5 ítems activos y 5 con resultado (100,00 %).

### QA-12: Textos sin lenguaje acusatorio

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Revisar las etiquetas, los resúmenes y los textos de motivos de todos los resultados generados.
- **Resultado esperado:** ningún texto contiene términos de la lista de términos prohibidos de lenguaje acusatorio del producto ni afirma conclusiones sobre contrato, entidad o proveedor.

---

**Total de casos:** 12
