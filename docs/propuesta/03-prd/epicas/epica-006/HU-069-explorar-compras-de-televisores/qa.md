# Casos de Prueba — HU-069: Explorar el listado de compras públicas de televisores

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la vista base de exploración: modos "Contratos" e "Ítems de televisor", universo visible, columnas, orden por defecto, paginación, combinación y limpieza de filtros (con criterios de prueba genéricos), conservación del estado en la URL y al volver de la ficha, estados vacío / sin resultados / carga / error, control de acceso, datos faltantes, formatos, lenguaje, accesibilidad, responsive y tiempo de respuesta. Quedan fuera: el comportamiento detallado de cada filtro (HU-070 a HU-072), el ordenamiento configurable (HU-073), el contenido de la ficha (HU-076 a HU-082) y la fecha de actualización (HU-083).

## Precondiciones y Datos Base

- **Usuarios:** `analista.piloto1@prueba.co` (rol Analista, sesión activa); `admin.po@prueba.co` (rol Administrador); visitante sin sesión.
- **Universo semilla (fecha de referencia 2026-10-02):**

  | Registro | Fuente | Identificador | Entidad | Proveedor | Modalidad | Fecha | Valor | Ítems y estado |
  | -------- | ------ | ------------- | ------- | --------- | --------- | ----- | ----- | -------------- |
  | R1 | SECOP II | CO1.PCCNTR.5512001 | Alcaldía de Tunja | Distribuciones Andinas S.A.S. | Mínima cuantía | 15/09/2026 | $ 22.900.000 | 2 ítems "incluido"; 1 con señal vigente, desviación +35,2 %, confianza Alta |
  | R2 | TVEC | 98765 | Gobernación de Santander | Comercializadora Nova S.A.S. | (no publicada) | 01/08/2026 | $ 12.480.000 | 1 ítem "incluido", sin señal, desviación +4,0 % |
  | R3 | SECOP II | CO1.PCCNTR.4410022 | Hospital San Rafael E.S.E. | (sin proveedor publicado) | Régimen especial | 10/03/2025 | (sin valor) | Identificado, sin ítems extraídos |
  | R4 | SECOP II | CO1.PCCNTR.3300045 | Instituto Municipal de Turismo | Ecoviajes Ltda. | Contratación directa | 05/05/2024 | $ 80.000.000 | Todos los ítems "excluido" |
  | R5 | SECOP II | CO1.PCCNTR.3300046 | Alcaldía de Tunja | Distribuciones Andinas S.A.S. | Mínima cuantía | 15/09/2026 | $ 9.000.000 | 1 ítem "incluido", 1 ítem "requiere revisión" |

- **Volumen de carga para paginación y rendimiento:** universo ampliado a 355 contratos SECOP II y 1.150 líneas TVEC visibles.

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1 / RN-04 / RN-05 | QA-01, QA-02 |
| Escenario 2 / RN-02 / RN-06 | QA-03 |
| RN-01 / RN-03 | QA-01, QA-04 |
| Escenario 3 / RN-07 | QA-05, QA-06 |
| Escenario 4 | QA-07 |
| Escenario 5 / Escenario 8 / RN-09 | QA-08, QA-09 |
| Escenario 6 / RN-08 | QA-10 |
| Escenario 7 | QA-11 |
| Escenario 9 | QA-12 |
| Escenario 10 | QA-13 |
| Escenario 11 | QA-14 |
| Escenario 12 / RN-14 | QA-15 |
| Escenario 13 | QA-16 |
| Escenario 14 | QA-17 |
| Escenario 15 / RN-11 | QA-18 |
| RN-10 | QA-19 |
| RN-12 | QA-20 |
| RN-15 | QA-21 |
| Escenario 16 / RN-16 | QA-22 |
| RN-13 | QA-23 |
| Permisos (Administrador) | QA-24 |

---

## Casos de Prueba

### QA-01: Abrir la exploración en modo contratos muestra el universo visible

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-01 / RN-03 / RN-05
- **Precondiciones:** universo semilla R1–R5; sesión de `analista.piloto1@prueba.co`.
- **Pasos:**
  1. Abrir "Exploración".
- **Resultado esperado:** modo "Contratos" seleccionado; aparecen R1, R5, R2 y R3 (R4 no aparece); R2 muestra Fuente "TVEC" e Identificador "98765"; texto "Mostrando 1–4 de 4 contratos"; columnas Fuente, Identificador, Entidad, Proveedor, Modalidad, Fecha, Valor del contrato u orden, N.º de ítems de televisor, Señal, Mayor desviación y Nivel de confianza. R1 muestra "Merece revisión (1)", "+35,2 %" y "Alta"; R5 muestra N.º de ítems "1".

### QA-02: Orden por defecto por fecha descendente con desempate por identificador

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Abrir "Exploración" sin cambiar el orden.
- **Resultado esperado:** orden R5 (CO1.PCCNTR.3300046, 15/09/2026), R1 (CO1.PCCNTR.5512001, 15/09/2026), R2 (01/08/2026), R3 (10/03/2025). R5 precede a R1 porque su identificador es menor alfabéticamente.

### QA-03: Modo ítems de televisor muestra solo ítems incluidos

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-02 / RN-06
- **Pasos:**
  1. Abrir "Exploración" y seleccionar "Ítems de televisor".
- **Resultado esperado:** aparecen 4 ítems (2 de R1, 1 de R2, 1 incluido de R5); no aparecen el ítem "requiere revisión" de R5 ni ítems de R3 o R4; texto "Mostrando 1–4 de 4 ítems de televisor"; columnas de RN-06 con precio unitario marcado "Explícito" o "Derivado"; página 1.

### QA-04: Registro identificado sin ítems clasificados sí aparece en modo contratos

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-01
- **Pasos:**
  1. Abrir "Exploración" en modo "Contratos" y ubicar R3.
- **Resultado esperado:** R3 aparece con N.º de ítems "Pendiente", Mayor desviación "Pendiente" y Señal "Sin señal".

### QA-05: Navegar entre páginas conserva modo, filtros y orden

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-07
- **Precondiciones:** universo ampliado (355 contratos SECOP II + órdenes TVEC visibles).
- **Pasos:**
  1. En modo "Contratos" pulsar "Siguiente".
  2. Pulsar el número de página 3.
  3. Cambiar "Resultados por página" a 50.
- **Resultado esperado:** paso 1 muestra "Mostrando 26–50 de {total}"; paso 2 muestra "Mostrando 51–75 de {total}"; paso 3 vuelve a la página 1 con "Mostrando 1–50 de {total}"; modo y orden se mantienen.

### QA-06: Valores de página y tamaño inválidos en la URL

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-07 / RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | página | 999 | mayor que la última página |
  | tamaño | 30 | no permitido |
  | página | 0 | menor que el mínimo |
  | parámetro | color=rojo | desconocido |

- **Pasos:**
  1. Abrir la URL de exploración con cada valor.
- **Resultado esperado:** página 999 → se muestra la última página; tamaño 30 → se aplica 25; página 0 → se muestra la página 1; parámetro desconocido → se ignora; en ningún caso se muestra un mensaje de error.

### QA-07: Abrir la ficha desde un contrato y desde un ítem

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:**
  1. En modo "Contratos" activar con la tecla Enter la fila de R1.
  2. Volver; en modo "Ítems de televisor" hacer clic en el ítem de R2.
- **Resultado esperado:** paso 1 abre la ficha de CO1.PCCNTR.5512001; paso 2 abre la ficha de la orden TVEC 98765 posicionada en el ítem seleccionado.

### QA-08: Volver de la ficha restaura el estado completo

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-09
- **Precondiciones:** universo ampliado; un filtro de fuente "SECOP II" aplicado, tamaño 50, página 3.
- **Pasos:**
  1. Abrir una ficha desde la página 3.
  2. Usar "Volver a la exploración".
  3. Repetir y usar el botón atrás del navegador.
- **Resultado esperado:** en ambos casos la exploración muestra modo, filtro, orden, tamaño 50 y página 3 iguales a los previos.

### QA-09: Recargar o abrir la URL en otra pestaña reproduce el estado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-09
- **Pasos:**
  1. Aplicar modo "Ítems de televisor", un filtro y la página 2.
  2. Recargar la página.
  3. Copiar la URL y abrirla en otra pestaña con la misma sesión.
- **Resultado esperado:** ambos pasos muestran exactamente el mismo modo, filtro y página.

### QA-10: Dos criterios distintos se combinan con Y; valores del mismo criterio con O

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 6 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Criterio A | Fuente = SECOP II | |
  | Criterio B | Entidad = Alcaldía de Tunja | |
  | Criterio B' | Entidad = Alcaldía de Tunja o Gobernación de Santander | dos valores del mismo criterio |

- **Pasos:**
  1. Aplicar A y B.
  2. Reemplazar B por B' manteniendo A.
- **Resultado esperado:** paso 1 lista R1 y R5, con etiquetas "Fuente: SECOP II" y "Entidad: Alcaldía de Tunja" y conteo 2; paso 2 lista R1 y R5 (R2 es TVEC y no cumple A), conteo 2; el listado vuelve a la página 1 en cada cambio.

### QA-11: Quitar una etiqueta y limpiar todos los filtros

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7
- **Precondiciones:** filtros A y B de QA-10 aplicados; orden elegido distinto del por defecto.
- **Pasos:**
  1. Pulsar "Quitar" en la etiqueta "Entidad: Alcaldía de Tunja".
  2. Pulsar "Limpiar filtros".
- **Resultado esperado:** paso 1 lista R1, R5 y R3 (solo SECOP II visibles); paso 2 lista los 4 registros visibles; ambos en página 1 y con el orden elegido conservado; "Limpiar filtros" queda deshabilitado tras el paso 2.

### QA-12: Universo vacío

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 9
- **Precondiciones:** ambiente sin registros del universo de televisores.
- **Pasos:**
  1. Abrir "Exploración".
- **Resultado esperado:** mensaje "Aún no hay compras de televisores disponibles. Los datos aparecerán cuando termine la primera carga de SECOP II y TVEC."; no se muestran tabla ni paginación y el panel de filtros no está activo.

### QA-13: Sin resultados para los filtros aplicados

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 10
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Fuente | TVEC | |
  | Entidad | Alcaldía de Tunja | sin órdenes TVEC |

- **Pasos:**
  1. Aplicar ambos filtros.
- **Resultado esperado:** mensaje "No encontramos resultados con los filtros aplicados.", conteo "0 resultados", etiquetas visibles y botón "Limpiar filtros" disponible.

### QA-14: Indicador de carga y controles deshabilitados

- **Tipo:** Estado UI
- **Prioridad:** Baja
- **Cubre:** Escenario 11
- **Precondiciones:** respuesta del servicio de resultados demorada artificialmente 5 segundos.
- **Pasos:**
  1. Cambiar de página.
- **Resultado esperado:** indicador de carga visible sobre el listado; paginación, selector de modo y filtros deshabilitados; un lector de pantalla anuncia "Cargando resultados"; al llegar la respuesta los controles se habilitan.

### QA-15: Error al cargar y reintento sin consultas duplicadas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 12 / RN-14
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Falla simulada | error del servicio | |
  | Falla simulada | sin respuesta durante 16 s | supera el límite de 15 s |

- **Pasos:**
  1. Abrir la exploración con cada falla simulada.
  2. Pulsar "Reintentar" tres veces seguidas rápidamente con la falla aún activa.
  3. Retirar la falla y pulsar "Reintentar".
- **Resultado esperado:** paso 1 muestra "No fue posible cargar los resultados. Intenta de nuevo en unos minutos." y "Reintentar", con filtros y orden conservados; paso 2 lanza una sola consulta (el botón se deshabilita mientras está en curso); paso 3 muestra el listado.

### QA-16: Acceso sin sesión redirige al inicio de sesión

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 13
- **Pasos:**
  1. Como visitante sin sesión, abrir la URL de exploración con un filtro de fuente "TVEC".
  2. Iniciar sesión como `analista.piloto1@prueba.co`.
- **Resultado esperado:** paso 1 redirige al inicio de sesión sin mostrar datos del universo; paso 2 vuelve a la exploración con el filtro "Fuente: TVEC" aplicado.

### QA-17: Sesión expirada al cambiar de página

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Escenario 14
- **Precondiciones:** sesión expirada por inactividad (30 minutos, valor inicial configurable).
- **Pasos:**
  1. Pulsar "Siguiente".
- **Resultado esperado:** mensaje "Tu sesión expiró. Inicia sesión de nuevo para continuar." y redirección al inicio de sesión; tras iniciar sesión se retoma la URL de exploración.

### QA-18: Datos faltantes muestran "Sin dato" o "Pendiente"

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 15 / RN-11
- **Pasos:**
  1. Ubicar R3 y R2 en modo "Contratos".
- **Resultado esperado:** R3 muestra Proveedor "Sin dato", Valor "Sin dato", N.º de ítems "Pendiente" y Mayor desviación "Pendiente"; R2 muestra Modalidad según la fuente o "Sin dato" si no se publica; ninguna celda vacía.

### QA-19: Formatos de fecha, moneda, porcentaje y cantidad

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-10
- **Pasos:**
  1. Revisar R1 en modo "Contratos" y su ítem con señal en modo "Ítems de televisor".
- **Resultado esperado:** fecha "15/09/2026"; valor "$ 22.900.000"; desviación "+35,2 %"; cantidad como entero (ej. "8"); ítem con descripción de más de 80 caracteres truncada con "…" y texto completo visible al pasar el foco.

### QA-20: Lista de términos prohibidos ausente en la vista

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** RN-12
- **Pasos:**
  1. Recorrer la vista en ambos modos, estados vacío, sin resultados y error.
  2. Buscar en el texto renderizado "sobreprecio", "corrupción", "fraude" y "hallazgo fiscal".
- **Resultado esperado:** 0 apariciones; la señal se presenta como "Merece revisión".

### QA-21: Navegación por teclado y lectura accesible

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** RN-15
- **Pasos:**
  1. Recorrer la vista solo con Tab, Shift+Tab y Enter.
  2. Verificar contraste con una herramienta de contraste.
  3. Aplicar un filtro con lector de pantalla activo.
- **Resultado esperado:** todos los controles reciben foco visible y se activan con teclado; contraste ≥ 4,5:1 en texto y ≥ 3:1 en componentes; "Merece revisión" y "Explícito/Derivado" se leen como texto; el nuevo conteo se anuncia.

### QA-22: Adaptación a tablet y móvil sin pérdida de acciones

- **Tipo:** Estado UI
- **Prioridad:** Media
- **Cubre:** Escenario 16 / RN-16
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Ancho | 1366 px | escritorio |
  | Ancho | 768 px | tablet |
  | Ancho | 767 px | límite inferior de tablet − 1 |
  | Ancho | 360 px | móvil mínimo |

- **Pasos:**
  1. Abrir la exploración en cada ancho con un filtro aplicado.
- **Resultado esperado:** 1366 px: panel lateral visible y tabla; 768 px: panel plegado detrás de "Filtros (1)" y tabla; 767 px y 360 px: tarjetas etiqueta–valor con todas las columnas y la acción de abrir ficha, cambio de modo, paginación y filtros disponibles; probado en las 2 últimas versiones de Chrome, Edge, Firefox y Safari.

### QA-23: Tiempo de respuesta con volumen del MVP y 20 usuarios concurrentes

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-13
- **Precondiciones:** universo ampliado; 20 sesiones concurrentes de Analista.
- **Pasos:**
  1. Ejecutar durante 10 minutos cargas iniciales, cambios de modo, de filtro y de página.
- **Resultado esperado:** p95 ≤ 3 segundos (objetivo inicial de diseño, recalibrable).

### QA-24: El Administrador accede con las mismas capacidades

- **Tipo:** Permisos
- **Prioridad:** Baja
- **Cubre:** Usuario y Contexto / Permisos
- **Pasos:**
  1. Iniciar sesión como `admin.po@prueba.co` y abrir "Exploración".
- **Resultado esperado:** ve el mismo listado, modos, filtros y paginación que el Analista.

---

**Total de casos:** 24
