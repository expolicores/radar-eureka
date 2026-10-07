# Historia #063: Ver el detalle de una señal con su comparación, su evidencia y la advertencia de no conclusión

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Presentación de Evidencia Trazable  
**Prioridad:** Crítica  
**FRs relacionados:** FR-065, FR-067, FR-062, FR-059, FR-060

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** abrir una señal y ver en una sola vista el ítem, el contrato, la comparación (referencia, fórmula, desviación y regla), las observaciones usadas con su origen, el emparejamiento, la base tributaria, la confianza y una advertencia visible de que no es una conclusión,  
**Para** evaluar rápidamente si la señal está suficientemente sustentada para merecer revisión.

## Descripción

El detalle de la señal es la pantalla central del flujo *explorar → detectar señal → revisar comparación → revisar evidencia → guardar caso*. Presenta la **instantánea de evidencia** de la versión vigente de la señal (o de una versión anterior si el Analista la elige) y muestra siempre, en la parte superior y sin posibilidad de ocultarla, la **advertencia de que la señal no constituye una conclusión ni una acusación** (FR-067).

Se llega desde la lista priorizada de señales o desde la ficha del contrato. Desde aquí parten los enlaces a la evidencia de origen (HU-064), la calificación de la señal (HU-066) y el reporte de errores (HU-067).

---

## Criterios de Aceptación

### Escenario 1: Detalle completo de una señal vigente

- **Dado** que el Analista ha iniciado sesión y existe la señal vigente SG-1 (Benchmark 1, desviación +31,0 %, confianza 100 "Alta")
- **Cuando** abre el detalle de SG-1
- **Entonces** ve, en este orden: (1) la advertencia; (2) el encabezado con "Señal que merece revisión", benchmark, desviación, nivel de confianza y fecha de corte; (3) ítem y contrato; (4) comparación; (5) observaciones; (6) estado del otro benchmark del ítem; (7) confianza con desglose; (8) historial de versiones

### Escenario 2: Advertencia siempre visible

- **Dado** que el Analista abre cualquier señal en cualquier tamaño de pantalla
- **Cuando** se carga el detalle
- **Entonces** el primer bloque visible es el texto exacto de la advertencia (RN-02), sin opción de cerrarlo u ocultarlo

### Escenario 3: Origen de cada observación

- **Dado** que la señal usa observaciones de SECOP II, TVEC y retail
- **Cuando** el Analista revisa la tabla de observaciones
- **Entonces** cada fila muestra su origen ("Contratación pública – SECOP II", "Contratación pública – TVEC" o "Retail – {tienda}"), fecha, producto, precio original, precio comparado (con IVA), tipo de emparejamiento, método de adquisición, la etiqueta "Manual" cuando aplique y el enlace "Ver evidencia"

### Escenario 4: Evidencia limitada

- **Dado** que la señal se generó con "Referencia disponible – evidencia limitada (3 de 5 observaciones mínimas)"
- **Cuando** el Analista abre el detalle
- **Entonces** la comparación muestra esa etiqueta, el texto "Evidencia limitada: no es una referencia estadística robusta", no muestra cuartiles y nunca usa la expresión "precio de mercado"

### Escenario 5: Benchmark 2 no disponible

- **Dado** que la señal es del Benchmark 1 y el Benchmark 2 del ítem está "No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)"
- **Cuando** el Analista abre el detalle
- **Entonces** el bloque "Otro benchmark del ítem" muestra "Benchmark 2 – Mercado: No disponible / evidencia insuficiente – sin observaciones de mercado en la ventana (±30 días)" y el resto del detalle del Benchmark 1 se muestra completo

### Escenario 6: Marcas de calidad visibles

- **Dado** que la comparación es "Incompleta / no confiable: base tributaria indeterminada en 6 de 8 observaciones" y el precio es `derivado`
- **Cuando** el Analista abre el detalle
- **Entonces** se muestran ambas marcas junto a la comparación: el estado tributario y "Precio unitario derivado: valor total / cantidad", además del nivel "Baja" con la nota de tope

### Escenario 7: Señal no vigente y versiones anteriores

- **Dado** que SG-1 está "No vigente" y tiene versiones 1 y 2
- **Cuando** el Analista abre el detalle y selecciona la versión 1 en el historial
- **Entonces** ve la franja "Esta señal ya no está vigente: {motivo}" y, al elegir la versión 1, la franja "Estás viendo la versión 1 del {DD/MM/AAAA}; no es la versión más reciente", con la instantánea de esa versión

### Escenario 8: Señal inexistente o retenida

- **Dado** que el identificador de señal no existe o corresponde a una señal "Retenida: evidencia incompleta"
- **Cuando** el Analista intenta abrirla
- **Entonces** ve el mensaje "La señal no existe o no está disponible." con el botón "Volver a la lista de señales"

### Escenario 9: Carga y error

- **Dado** que el Analista abre una señal
- **Cuando** la información está cargando o falla la carga
- **Entonces** mientras carga ve "Cargando señal…"; si falla, ve "No pudimos cargar la señal. Intenta de nuevo." con el botón "Reintentar"

### Escenario 10: Usuario no autenticado

- **Dado** que un visitante sin sesión abre el enlace de una señal
- **Cuando** intenta acceder
- **Entonces** es redirigido al inicio de sesión y, tras iniciar sesión, vuelve al detalle de esa señal

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (principal); el Administrador también puede consultar.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Es donde se valida la hipótesis: el Analista decide si la señal está sustentada (KPI ≥ 70 % de señales sustentadas).

### Reglas de Negocio

**RN-01 – Fuente de datos.** Todo lo que se muestra proviene de la instantánea de evidencia de la versión seleccionada (por defecto, la más reciente). El bloque "Otro benchmark del ítem" muestra el estado vigente del otro benchmark.

**RN-02 – Advertencia (FR-067).** Texto exacto: "Esta es una señal que merece revisión: indica una diferencia de precio frente a las referencias disponibles. No constituye una conclusión ni una acusación sobre el contrato, la entidad o el proveedor. Revisa cantidades, especificaciones, documentos y referencias antes de sacar conclusiones." Se muestra arriba de todo, en todas las versiones y estados de la señal, y no se puede cerrar.

**RN-03 – Bloques.**
1. Advertencia.
2. Encabezado: "Señal que merece revisión", estado (Vigente / No vigente), benchmark, desviación con signo, nivel y puntaje de confianza, fecha de corte de los datos, versión.
3. Ítem y contrato: descripción, marca, modelo, tamaño, resolución, tecnología, Smart, cantidad, precio unitario original y tipo (con la marca "Precio unitario derivado: valor total / cantidad" si aplica), entidad, proveedor, contrato u orden, modalidad, fecha de compra y enlace "Ver en la fuente oficial".
4. Comparación: precio comparado (con IVA), referencia y su etiqueta de estado, fórmula con valores sustituidos, regla aplicada y motivo de no aplicación de atípicos, ventana usada, tipo de emparejamiento y criterios, estado tributario, conversiones aplicadas, y, en referencia estadística, n, mínimo, Q1, mediana, Q3 y máximo con una representación gráfica de la distribución que marque la posición del precio contratado.
5. Observaciones: tabla según el escenario 3, ordenada por precio comparado ascendente.
6. Otro benchmark del ítem: estado, referencia y desviación si existen.
7. Confianza: nivel, puntaje, desglose de los 6 factores y nota de tope.
8. Historial de versiones: número, fecha (DD/MM/AAAA) y desviación de cada versión.

**RN-04 – Formatos.** Montos: "$ 2.750.000" (COP, sin decimales, separador de miles "."). Porcentajes: 1 decimal con coma y signo ("+31,0 %"). Fechas: DD/MM/AAAA. Campos sin dato: "No publicado por la fuente".

**RN-05 – Lenguaje.** Las únicas etiquetas de referencia permitidas son las de los benchmarks ("Referencia estadística", "Referencia disponible – evidencia limitada", "Referencia estadística de mercado", "Referencia de mercado disponible – evidencia limitada", "No disponible / evidencia insuficiente"). No se usa "precio de mercado" ni ningún término de la lista de términos prohibidos.

**RN-06 – Visibilidad.** Las señales "Retenidas: evidencia incompleta" no se muestran; se tratan como inexistentes para el usuario (Escenario 8).

**RN-07 – Mensajes.** Carga: "Cargando señal…". Error: "No pudimos cargar la señal. Intenta de nuevo." + "Reintentar". Inexistente: "La señal no existe o no está disponible." + "Volver a la lista de señales". No vigente: "Esta señal ya no está vigente: {motivo}". Versión anterior: "Estás viendo la versión {n} del {DD/MM/AAAA}; no es la versión más reciente".

**RN-08 – Rendimiento y accesibilidad.** Carga del detalle ≤ 3 s (p95) con el volumen del MVP y hasta 20 usuarios concurrentes (objetivo inicial de ingeniería). Diseño desde 1366 × 768 px, funcional desde 768 px y 360 px sin perder bloques (en pantallas pequeñas la tabla de observaciones se puede desplazar horizontalmente). Contraste y navegación por teclado WCAG 2.1 AA.

### Interfaz

Vista "Detalle de la señal" con los 8 bloques de RN-03. Acciones visibles: "Ver evidencia" en cada observación y en el precio contratado, "Ver en la fuente oficial", "Calificar señal" y "Reportar un error" (sus comportamientos se definen en las HUs correspondientes).

### Sistemas Externos (Si aplica)

El enlace "Ver en la fuente oficial" abre la URL pública del proceso en SECOP II (o la referencia de la TVEC) en una pestaña nueva; no se consulta la fuente para construir la vista.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-062 (instantánea), HU-064 (evidencia de origen), HU-065 (lenguaje), HU-066 (calificación), HU-067 (reporte de error).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Texto exacto de la advertencia**: resuelto en RN-02 (sin términos prohibidos).
- **Consulta de versiones anteriores** de la señal desde el detalle: resuelto en RN-03.8/RN-07.
- **Formatos de presentación** (COP, porcentaje, fecha DD/MM/AAAA): resuelto en RN-04.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-005 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
