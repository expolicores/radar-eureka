# Historia #106: Calcular la precisión de la extracción, global y por campo

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)  
**Feature:** Medir KPIs del MVP  
**Prioridad:** Alta  
**FRs relacionados:** FR-091 (relacionados: FR-028, FR-092; NFR-CAL-001, NFR-CAL-002)

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (el PO),  
**Quiero** calcular la precisión de la extracción sobre la muestra validada manualmente, global y por cada campo crítico, con la relación entre la confianza del extractor y la corrección real,  
**Para** saber si se cumple la meta de ≥ 90 % sin que una buena cifra global oculte un campo débil, y tener la evidencia para calibrar el umbral de aceptación automática.

## Descripción

El KPI de extracción del Brief es **≥ 90 % de precisión en campos críticos** (marca, modelo/referencia, tamaño, cantidad, precio unitario) sobre una muestra **diversa de ≥ 50 contratos/documentos** validados manualmente (NFR-CAL-001). La metodología aprobada (P-06, NFR-CAL-002) es:

`precisión = campos extraídos correctamente / campos realmente presentes según la validación manual`

- ausente en el documento y no extraído → no cuenta;
- presente y bien extraído → correcto;
- presente y mal extraído → error;
- presente y no extraído → error (está en el denominador de "realmente presentes");
- ausente pero inventado → error.

Esta HU calcula el indicador a partir de los resultados vigentes registrados en HU-105, lo entrega como reporte y guarda cada cálculo como un corte histórico. También entrega la **tabla de calibración** confianza ↔ corrección (insumo de D4-4 y P-15). El cálculo **no fija** el umbral; solo aporta la evidencia.

**Implementación sin UI permitida:** comando, script, consulta o reporte (texto, CSV o JSON).

---

## Criterios de Aceptación

### Escenario 1: Precisión por campo y global

- **Dado** que la muestra tiene 52 elementos con validación completa y estos resultados vigentes:

  | Campo | correcto | incorrecto | omitido | inventado | ausente_y_no_extraido | no_verificable |
  |---|---|---|---|---|---|---|
  | precio_unitario | 45 | 3 | 2 | 0 | 20 | 1 |
  | cantidad | 47 | 1 | 1 | 1 | 18 | 0 |
  | tamano_pulgadas | 48 | 2 | 0 | 0 | 15 | 0 |
  | modelo_referencia | 36 | 6 | 6 | 2 | 22 | 2 |
  | marca | 49 | 1 | 0 | 0 | 10 | 0 |

- **Cuando** el Administrador calcula la precisión
- **Entonces** obtiene precisión por campo: precio unitario 90,0 % (45/50), cantidad 94,0 % (47/50), tamaño 96,0 % (48/50), modelo/referencia 72,0 % (36/50), marca 98,0 % (49/50); precisión global 90,0 % (225/250); y por cada campo los conteos de correctos, incorrectos, omitidos ("no encontrados"), inventados ("falsos positivos") y excluidos

### Escenario 2: Una buena cifra global no oculta un campo débil

- **Dado** los resultados del Escenario 1 y la meta de 90,0 %
- **Cuando** se evalúa la meta
- **Entonces** los estados por campo son: precio unitario "Cumple", cantidad "Cumple", tamaño "Cumple", modelo/referencia "No cumple", marca "Cumple"; y el estado global es "No cumple" con el texto "Campos críticos por debajo de la meta: modelo_referencia (72,0 %)."

### Escenario 3: Cumplimiento total

- **Dado** que la muestra tiene 50 elementos con validación completa y los 5 campos críticos tienen precisión ≥ 90,0 %
- **Cuando** se evalúa la meta
- **Entonces** el estado global es "Cumple"

### Escenario 4: Muestra insuficiente

- **Dado** que solo 38 elementos de la muestra tienen validación completa
- **Cuando** el Administrador calcula la precisión
- **Entonces** se entregan las cifras calculadas, pero el estado global es "Muestra insuficiente: 38 de 50 elementos con validación completa." y ningún estado dice "Cumple"

### Escenario 5: Campo sin casos evaluables

- **Dado** que en la muestra todos los resultados de `cantidad` son `ausente_y_no_extraido` o `no_verificable`
- **Cuando** se calcula la precisión
- **Entonces** el campo cantidad muestra precisión "—" y estado "Sin datos", y el estado global es "No concluyente: el campo cantidad no tiene casos evaluables."

### Escenario 6: Filas excluidas y pendientes

- **Dado** que hay filas `no_verificable`, filas sin resultado y filas en estado "requiere revalidar"
- **Cuando** se calcula la precisión
- **Entonces** ninguna de ellas entra al numerador ni al denominador; el reporte las informa como "excluidas (no verificables)" y "pendientes (sin resultado o por revalidar)"

### Escenario 7: Desgloses

- **Dado** que la muestra incluye ítems con precio unitario explícito y derivado, documentos que requirieron OCR o lectura multimodal y dos lotes
- **Cuando** se calcula la precisión
- **Entonces** el reporte incluye la precisión de precio unitario por tipo de precio (`explicito` / `derivado`), la precisión global por necesidad de OCR o lectura multimodal (sí / no) y la precisión global por lote, cada una con su denominador

### Escenario 8: Tabla de calibración confianza ↔ corrección

- **Dado** que los campos críticos evaluables tienen confianza registrada en la escala 0,00–1,00 o como "incierta"
- **Cuando** se calcula la precisión
- **Entonces** el reporte incluye una tabla con 10 tramos de confianza ([0,00–0,10), [0,10–0,20) … [0,90–1,00]) más el tramo "incierta", con, por tramo, número de campos evaluables, correctos y precisión; y, por cada tramo inferior t, la "precisión de los campos con confianza ≥ t" y el "% de campos que irían a revisión humana con umbral t"

### Escenario 9: Corte histórico

- **Dado** que el Administrador calculó la precisión el 2026-10-02 y vuelve a calcularla el 2026-10-09
- **Cuando** consulta el historial de cálculos
- **Entonces** ve ambos cortes con fecha y hora, versión de configuración, número de elementos validados, precisión global y por campo, y estados; el corte del 2026-10-02 no cambia aunque después se carguen nuevos resultados

### Escenario 10: Sin resultados de validación

- **Dado** que no hay resultados de validación registrados
- **Cuando** el Administrador calcula la precisión
- **Entonces** no se genera corte y recibe "No hay resultados de validación registrados; no es posible calcular la precisión."

### Escenario 11: Usuario sin rol Administrador

- **Dado** que un usuario con rol Analista está autenticado
- **Cuando** intenta calcular o consultar la precisión
- **Entonces** recibe "Acción no permitida: esta operación requiere el rol Administrador."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP, el PO).
- **Permisos requeridos:** rol Administrador.
- **Valor de negocio:** demuestra (o refuta) el KPI de extracción del Brief, impide que una cifra global esconda un campo crítico débil y aporta la evidencia para calibrar el umbral de aceptación automática (D4-4, P-15).

### Reglas de Negocio

- **RN-01 — Base del cálculo:** resultados **vigentes** por campo de los elementos de la muestra de validación (contratos y documentos), registrados por validación manual. Cada campo se cuenta una vez aunque su documento esté marcado individualmente y a través de su contrato.
- **RN-02 — Clasificación de resultados:**

  | Resultado | Numerador | Denominador |
  |---|---|---|
  | `correcto` | sí | sí |
  | `incorrecto` | no | sí |
  | `omitido` (presente, no extraído) | no | sí |
  | `inventado` (ausente, pero extraído) | no | sí |
  | `ausente_y_no_extraido` | no | no |
  | `no_verificable` | no | no (excluido) |
  | sin resultado o "requiere revalidar" | no | no (pendiente) |

- **RN-03 — Fórmulas:** precisión por campo = correctos / (correctos + incorrectos + omitidos + inventados) de ese campo. Precisión global = suma de correctos de los 5 campos críticos / suma de sus denominadores. Porcentajes con 1 decimal, redondeo a la mitad hacia arriba (ej. 89,95 % → 90,0 %); la comparación con la meta se hace con el valor ya redondeado. Si un denominador es 0, la precisión es "—".
- **RN-04 — Campos críticos:** `marca`, `modelo_referencia`, `tamano_pulgadas`, `cantidad`, `precio_unitario`. Los demás campos validados se reportan en una sección informativa con la misma fórmula, sin estado de meta y sin entrar a la precisión global.
- **RN-05 — Parámetros (configurables):** meta de precisión, decimal de 50,0 a 100,0 %, **configuración inicial: 90,0 %** (meta del Brief); mínimo de elementos con validación completa, entero de 1 a 1.000, **configuración inicial: 50** (el mismo mínimo de muestra de HU-104).
- **RN-06 — Estados (se evalúan en este orden):**
  1. "Muestra insuficiente: {n} de {mínimo} elementos con validación completa." si los elementos con validación completa son menos que el mínimo.
  2. "No concluyente: el campo {campo} no tiene casos evaluables." si algún campo crítico tiene denominador 0 (se listan todos).
  3. "No cumple" si la precisión global o la de algún campo crítico es menor que la meta, con el texto "Campos críticos por debajo de la meta: {campo} ({x} %)[, …]." cuando aplique y "Precisión global por debajo de la meta ({x} %)." cuando aplique.
  4. "Cumple" en otro caso.
  Estado por campo: "Sin datos" (denominador 0), "Cumple" (≥ meta) o "No cumple" (< meta).
- **RN-07 — Desgloses:** precisión de `precio_unitario` por `precio_unitario_tipo` (`explicito` / `derivado`); precisión global por "requiere OCR o lectura multimodal" del documento de origen (sí / no); precisión global por lote de la muestra. Cada desglose muestra numerador y denominador; un grupo con denominador 0 muestra "—".
- **RN-08 — Tabla de calibración:** sobre los campos críticos evaluables (RN-02, denominador). Tramos de confianza de ancho 0,10, cerrados a la izquierda y abiertos a la derecha, salvo el último [0,90–1,00] cerrado en ambos extremos; tramo adicional "incierta" para confianza no numérica. Por tramo: evaluables, correctos y precisión. Por cada límite inferior t ∈ {0,10; 0,20; … 0,90}: precisión de los evaluables con confianza ≥ t y porcentaje de evaluables con confianza < t o "incierta" (los que irían a revisión humana con ese umbral). La tabla es solo informativa: no cambia el umbral configurado.
- **RN-09 — Corte histórico:** cada cálculo se guarda como corte inmutable con fecha y hora (UTC−05:00), usuario, número de versión de configuración vigente, número de elementos de la muestra y con validación completa, conteos, precisiones, estados, desgloses y tabla de calibración. Los cortes no se recalculan ni se borran; el historial se lista del más reciente al más antiguo.
- **RN-10 — Cálculo a demanda:** se ejecuta cuando el Administrador lo solicita; no modifica resultados de validación, datos extraídos ni configuración.
- **RN-11 — Mensajes:**
  - "No hay resultados de validación registrados; no es posible calcular la precisión."
  - "Acción no permitida: esta operación requiere el rol Administrador."

### Interfaz

No requiere interfaz gráfica. Mínimo aceptable: comando "calcular precisión" que imprime o exporta (CSV/JSON) el reporte con las secciones: resumen y estados, tabla por campo, desgloses, tabla de calibración y campos informativos; y comando "historial de precisión".

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Operación, Calidad y Medición del MVP](../../../epicas.md#épica-008-operación-calidad-y-medición-del-mvp)

**Exclusiones de la Épica:**
- NO incluye analítica de uso avanzada ni embudos de producto.
- NO incluye facturación ni gestión de planes.
- NO incluye administración multi-organización.

**Historias relacionadas:** HU-104 (muestra), HU-105 (resultados de validación), HU-102 (umbral de aceptación automática), HU-107 (cobertura).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La precisión global es el agregado de los 5 campos críticos (suma de correctos / suma de denominadores) → resuelto en RN-03.
- `omitido` cuenta como error en el denominador y `no_verificable` se excluye → resuelto en RN-02.
- La meta global solo se declara "Cumple" si la global y cada campo crítico alcanzan la meta y la muestra es suficiente → resuelto en RN-06.
- La tabla de calibración por tramos de 0,10 es informativa y no fija el umbral → resuelto en RN-08.

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-008 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
