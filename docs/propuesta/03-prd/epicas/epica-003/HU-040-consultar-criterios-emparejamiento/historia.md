# Historia #040: Consultar los criterios de emparejamiento de un ítem

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Clasificar y Explicar el Emparejamiento  
**Prioridad:** Crítica  
**FRs relacionados:** FR-039

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver, para un televisor comprado, su clasificación de emparejamiento y, para cada producto emparejado, qué criterios se usaron y con qué valores,  
**Para** juzgar por mí mismo si la comparación es razonable antes de confiar en una referencia o en una señal.

## Descripción

FR-039 exige **mostrar** los criterios usados en cada emparejamiento. Esta HU entrega la vista **"Detalle del emparejamiento"** de un ítem objetivo (ítem de televisor de SECOP II o TVEC): encabezado con los atributos normalizados del ítem y su clasificación, y la lista de productos emparejados con su fuente, sus atributos, el tipo de emparejamiento y la evaluación criterio por criterio. Cuando el ítem es insuficiente/no confiable, la vista explica por qué.

La vista se abre por el identificador del ítem, para que la ficha del contrato y el detalle de una señal puedan enlazarla. No muestra precios ni desviaciones (eso pertenece a los benchmarks) y usa lenguaje descriptivo, no acusatorio.

---

## Criterios de Aceptación

### Escenario 1: Ítem clasificado como mismo modelo

- **Dado** que el Analista autenticado abre el detalle del emparejamiento del ítem TVEC-1701 (`MISMO_MODELO`, 2 pares)
- **Cuando** la vista carga
- **Entonces** ve el encabezado con fuente "TVEC", descripción original, marca, modelo, tamaño, resolución, tecnología, Smart y generación normalizados (o "No determinado" si son nulos), la etiqueta "Mismo modelo" y el resumen de criterios
- **Y** ve una fila por producto emparejado con: fuente (SECOP II / TVEC / Retail – {tienda}), descripción original, marca y modelo, tipo "Mismo modelo" y el criterio "Marca y modelo coinciden" o "Código EAN/GTIN coincide"

### Escenario 2: Ítem clasificado como producto equivalente

- **Dado** que el ítem SEC-2701-I1 es `EQUIVALENTE` con 3 pares
- **Cuando** el Analista abre el detalle
- **Entonces** cada fila muestra la tabla de criterios con atributo, valor del ítem, valor del producto emparejado y resultado ("Cumple" / "No evaluado: dato desconocido"), y la versión de reglas usada
- **Y** las filas con referencias de modelo distintas muestran el aviso "Referencias de modelo distintas: equivalencia por características técnicas"

### Escenario 3: Ítem insuficiente / no confiable

- **Dado** que el ítem es `INSUFICIENTE_NO_CONFIABLE` con motivo `SIN_CANDIDATOS_QUE_CUMPLAN` y descartes `tamaño: 120`, `tecnología (desconocida): 14`
- **Cuando** el Analista abre el detalle
- **Entonces** ve la etiqueta "Insuficiente / no confiable", el texto del motivo, el conteo de productos descartados por criterio y el mensaje "No se relajan los criterios para encontrar una referencia."
- **Y** no se muestra ninguna lista de productos emparejados

### Escenario 4: Pares en conflicto

- **Dado** que el ítem tiene pares `INSUFICIENTE_NO_CONFIABLE` por conflicto de atributos
- **Cuando** el Analista abre el detalle
- **Entonces** ve una sección "Productos con la misma marca y modelo pero datos contradictorios" con el detalle de cada conflicto (ej. "Tamaño: 55" vs 65"")

### Escenario 5: Muchos productos emparejados

- **Dado** que el ítem tiene 120 productos emparejados
- **Cuando** el Analista abre el detalle
- **Entonces** ve 50 filas por página, ordenadas por tipo (mismo modelo primero) y luego por fuente (SECOP II, TVEC, Retail), con paginación y el total "120 productos emparejados"

### Escenario 6: Ítem sin resultado calculado

- **Dado** que el ítem existe pero tiene `clasificacion_pendiente = sí`
- **Cuando** el Analista abre el detalle
- **Entonces** ve "El emparejamiento de este ítem aún no se ha calculado." sin clasificación

### Escenario 7: Ítem inexistente o inactivo

- **Dado** que el identificador no existe o corresponde a un producto inactivo
- **Cuando** el Analista abre el detalle
- **Entonces** ve "El ítem solicitado no existe o no está disponible."

### Escenario 8: Error de carga

- **Dado** que ocurre un error al obtener el detalle
- **Cuando** la vista intenta cargar
- **Entonces** se muestra "No fue posible cargar el detalle del emparejamiento. Intenta de nuevo." con un botón "Reintentar"

### Escenario 9: Usuario no autenticado

- **Dado** que un usuario sin sesión intenta abrir el detalle
- **Cuando** accede a la vista
- **Entonces** es redirigido al inicio de sesión y, tras autenticarse, vuelve al detalle solicitado

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (principal); Administrador.
- **Permisos requeridos:** usuario autenticado con rol Analista o Administrador. Solo lectura.
- **Valor de negocio:** la clasificación visible con sus criterios es la base de la confianza en las señales (KPI ≥ 70 % de señales sustentadas).

### Reglas de Negocio

**RN-01 — Fuente de datos.** La vista muestra el resultado de emparejamiento **vigente** del ítem y sus pares vigentes (`MISMO_MODELO`, `EQUIVALENTE` e `INSUFICIENTE_NO_CONFIABLE` por conflicto), tal como están registrados; no recalcula nada.

**RN-02 — Encabezado.** Fuente (SECOP II / TVEC), identificador de origen, descripción original, atributos normalizados (marca, modelo normalizado, tamaño en pulgadas con `"`, resolución, tecnología, Smart "Sí"/"No", generación), etiqueta de clasificación ("Mismo modelo", "Producto equivalente", "Insuficiente / no confiable"), resumen de criterios, versión de reglas y fecha del cálculo (formato `AAAA-MM-DD HH:mm`, hora de Colombia). Un atributo nulo se muestra como "No determinado".

**RN-03 — Filas de productos emparejados.** Por par: fuente (`SECOP II`, `TVEC` o `Retail – {nombre de la tienda}`), identificador de origen, descripción original, marca y modelo, tamaño, resolución, tecnología, Smart, generación, tipo y criterios:
- Mismo modelo: "Marca y modelo coinciden ({marca} · {modelo})", "Código EAN/GTIN coincide ({ean})" o ambos; si `ean_distinto = sí`, "Códigos EAN distintos: {ean1} / {ean2}".
- Equivalente: tabla atributo | valor del ítem | valor del producto | resultado, con resultados "Cumple", "Cumple (tolerancia ±{n})" y "No evaluado: dato desconocido". Los criterios configurados como no evaluados no se listan.
- Referencias distintas: aviso "Referencias de modelo distintas: equivalencia por características técnicas".

**RN-04 — Insuficiente.** Se muestran los textos de los motivos, el conteo de descartes por criterio (de mayor a menor) y el texto fijo "No se relajan los criterios para encontrar una referencia."

**RN-05 — Conflictos.** Sección propia con cada par en conflicto y el detalle "{atributo}: {valor del ítem} vs {valor del producto}".

**RN-06 — Orden y paginación.** Orden: tipo (Mismo modelo, Producto equivalente), luego fuente (SECOP II, TVEC, Retail) y luego identificador de origen ascendente. 50 filas por página; se muestra el total.

**RN-07 — Mensajes de estado.** Carga: indicador "Cargando detalle del emparejamiento…". Pendiente: "El emparejamiento de este ítem aún no se ha calculado.". Inexistente o inactivo: "El ítem solicitado no existe o no está disponible.". Error: "No fue posible cargar el detalle del emparejamiento. Intenta de nuevo." + "Reintentar".

**RN-08 — Lenguaje.** Ningún texto de la vista usa términos de la lista de términos prohibidos del producto ni atribuye conclusiones al contrato, la entidad o el proveedor. La vista no muestra precios, desviaciones ni señales.

**RN-09 — Acceso.** Requiere sesión; sin sesión redirige al inicio de sesión y regresa a la vista solicitada. La vista es accesible por una dirección que incluye el identificador del ítem, para que otras vistas la enlacen.

**RN-10 — Rendimiento y usabilidad.** Carga en ≤ 3 segundos (p95) con el volumen del MVP (objetivo inicial del piloto). Diseño para escritorio desde 1366 × 768 px y funcional desde 360 px; las tablas de criterios pasan a formato de lista en pantallas estrechas. Navegable con teclado y con contraste WCAG 2.1 AA.

### Interfaz

Vista web "Detalle del emparejamiento":
1. **Encabezado:** datos del ítem, etiqueta de clasificación destacada (insignia), resumen de criterios, versión de reglas y fecha.
2. **Productos emparejados:** tabla paginada; cada fila se expande para mostrar la tabla de criterios.
3. **Conflictos:** sección visible solo si existen.
4. **Insuficiente:** bloque de explicación con motivos y descartes, en lugar de la tabla.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-039 (resultado mostrado), HU-035, HU-036 y HU-038 (pares), HU-037 (versión de reglas).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-08, RN-09):** la vista de criterios es independiente y enlazable por identificador del ítem; no muestra precios ni señales, que se presentan en las vistas de benchmarks y señales.
- **S-02 (Resuelto → RN-06):** paginación de 50 filas y orden por tipo y fuente como valores iniciales de diseño.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-003 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
