# Casos de Prueba — HU-040: Consultar los criterios de emparejamiento de un ítem

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la vista "Detalle del emparejamiento": encabezado, filas de mismo modelo y equivalente con sus criterios, insuficiente, conflictos, orden y paginación, estados (carga, pendiente, inexistente, error), acceso, lenguaje, rendimiento y usabilidad. Queda fuera el cálculo de pares y clasificaciones.

## Precondiciones y Datos Base

- Usuarios: `analista.piloto1` (Analista), `admin.po` (Administrador); un visitante sin sesión.
- Reglas `televisor` v1; fecha de cálculo de referencia 2026-10-02 08:15.
- Ítems:

| id_origen | Clasificación | Pares |
|---|---|---|
| TVEC-1701 | Mismo modelo | RET-3701 (marca y modelo), RET-3702 (marca, modelo y EAN) |
| SEC-2701-I1 | Producto equivalente | TVEC-1702, TVEC-1703 (modelos distintos), RET-3703 |
| SEC-2702-I1 | Insuficiente / no confiable | 0; motivo `SIN_CANDIDATOS_QUE_CUMPLAN`; descartes tamaño 120, tecnología (desconocida) 14 |
| TVEC-1704 | Insuficiente / no confiable | 2 en conflicto (tamaño 55 vs 65) |
| TVEC-1705 | Producto equivalente | 120 equivalentes |
| TVEC-1706 | pendiente | — |

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-02, RN-03 | QA-01, QA-02 |
| Escenario 2 / RN-03 | QA-03 |
| Escenario 3 / RN-04 | QA-04 |
| Escenario 4 / RN-05 | QA-05 |
| Escenario 5 / RN-06 | QA-06 |
| Escenarios 6, 7, 8 / RN-07 | QA-07, QA-08, QA-09 |
| Escenario 9 / RN-09 | QA-10 |
| RN-01 (solo vigentes) | QA-11 |
| RN-08 | QA-12 |
| RN-10 | QA-13, QA-14 |

---

## Casos de Prueba

### QA-01: Encabezado de un ítem mismo modelo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-02
- **Pasos:**
  1. Con `analista.piloto1`, abrir el detalle de TVEC-1701.
- **Resultado esperado:** fuente "TVEC", identificador, descripción original, atributos normalizados (tamaño con `"`, Smart "Sí"), etiqueta "Mismo modelo", resumen de criterios, "Reglas v1" y fecha "2026-10-02 08:15"; la generación nula se muestra "No determinado".

### QA-02: Criterios de mismo modelo por fila

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-03
- **Resultado esperado:** RET-3701 muestra "Marca y modelo coinciden (SAMSUNG · UN55DU8000KXZL)"; RET-3702 muestra además "Código EAN/GTIN coincide (08806095512341)"; la fuente aparece como "Retail – Alkosto".

### QA-03: Tabla de criterios de equivalencia y aviso de referencias distintas

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03
- **Pasos:**
  1. Abrir el detalle de SEC-2701-I1 y expandir cada fila.
- **Resultado esperado:** tabla atributo | valor del ítem | valor del producto | resultado con "Cumple" en tamaño, resolución, tecnología y Smart, "Cumple (tolerancia ±1)" en generación cuando aplica y "No evaluado: dato desconocido" en marca; TVEC-1703 muestra "Referencias de modelo distintas: equivalencia por características técnicas".

### QA-04: Explicación de insuficiente

- **Tipo:** Estado UI
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04
- **Resultado esperado:** SEC-2702-I1 muestra "Insuficiente / no confiable", "Ningún otro televisor cumple todos los criterios de equivalencia configurados.", descartes "tamaño: 120" antes de "tecnología (desconocida): 14", el texto "No se relajan los criterios para encontrar una referencia." y ninguna tabla de productos.

### QA-05: Sección de conflictos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-05
- **Resultado esperado:** TVEC-1704 muestra la sección "Productos con la misma marca y modelo pero datos contradictorios" con 2 entradas "Tamaño: 55" vs 65""; la sección no aparece en TVEC-1701.

### QA-06: Orden y paginación

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 5 / RN-06
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | TVEC-1705 | 120 pares | 3 páginas: 50, 50, 20 |
  | Mezcla de fuentes | 30 SECOP II, 60 TVEC, 30 Retail | Orden por fuente |

- **Resultado esperado:** total "120 productos emparejados"; página 1 con 50 filas empezando por SECOP II ordenadas por identificador; página 3 con 20 filas Retail.

### QA-07: Ítem pendiente

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-07
- **Resultado esperado:** TVEC-1706 muestra "El emparejamiento de este ítem aún no se ha calculado." sin etiqueta de clasificación.

### QA-08: Ítem inexistente o inactivo

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-07
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Identificador | `TVEC-9999` | No existe |
  | Identificador | `TVEC-1707` | `activo = no` |

- **Resultado esperado:** ambos muestran "El ítem solicitado no existe o no está disponible."

### QA-09: Carga y error con reintento

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Abrir el detalle con respuesta lenta simulada.
  2. Simular un error de carga.
  3. Restablecer el servicio y pulsar "Reintentar".
- **Resultado esperado:** paso 1: "Cargando detalle del emparejamiento…"; paso 2: "No fue posible cargar el detalle del emparejamiento. Intenta de nuevo." con "Reintentar"; paso 3: se muestra el detalle.

### QA-10: Acceso sin sesión y con roles

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 9 / RN-09
- **Pasos:**
  1. Sin sesión, abrir la dirección del detalle de TVEC-1701.
  2. Iniciar sesión con `analista.piloto1`.
  3. Repetir con `admin.po`.
- **Resultado esperado:** paso 1 redirige al inicio de sesión; paso 2 regresa al detalle de TVEC-1701; paso 3 muestra el mismo detalle; la vista no ofrece acciones de edición.

### QA-11: Solo se muestran datos vigentes

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Precondiciones:** TVEC-1701 tiene además un par histórico `vigente = no` con RET-3704.
- **Resultado esperado:** RET-3704 no aparece en la vista.

### QA-12: Lenguaje y ausencia de precios

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-08
- **Resultado esperado:** en las vistas de los ítems base no aparece ningún término de la lista de términos prohibidos del producto, ni precios, desviaciones o señales.

### QA-13: Tiempo de carga

- **Tipo:** Integración
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Con el volumen del MVP cargado (≈ 1.500 ítems públicos y sus pares), abrir 100 veces el detalle de TVEC-1705.
- **Resultado esperado:** p95 ≤ 3 segundos.

### QA-14: Responsive y accesibilidad

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** RN-10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ancho | 1366 px | Tabla completa |
  | Ancho | 768 px | Funcional |
  | Ancho | 360 px | Criterios como lista |

- **Resultado esperado:** todas las capacidades disponibles en los tres anchos; navegación completa con teclado (expandir filas, paginar, reintentar) y contraste WCAG 2.1 AA.

---

**Total de casos:** 14
