# Historia #010: Clasificar ítems candidatos contra el límite de categoría por reglas

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Clasificar Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-013, FR-014, FR-015

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que cada ítem candidato (de la TVEC o de un contrato SECOP II) se clasifique como incluido, excluido o requiere revisión con reglas explícitas del límite de categoría, registrando el criterio aplicado y el método,  
**Para** que solo los televisores de consumo comparables entren al análisis y cada decisión sea explicable y auditable.

## Descripción

El límite de categoría aprobado incluye televisores LED/QLED/OLED de consumo, Smart y convencionales, de cualquier tamaño, y excluye pantallas LED modulares, videowalls, señalización digital, monitores (incluidos los de CCTV), proyectores, pantallas interactivas o inflables, soluciones audiovisuales integrales, accesorios, servicios de mantenimiento o instalación, comodatos y otros contratos que no son compras, lotes que no corresponden al televisor y kits sin precio unitario determinable. También se excluyen los ítems cuyo precio es inseparable de instalación, obra o servicios (FR-014).

Esta historia aplica un **conjunto ordenado y versionado de reglas determinísticas** sobre la descripción de cada ítem. La primera regla que se cumple decide. Cada clasificación queda registrada con resultado, código y texto del criterio, términos que lo activaron, método "Regla", versión de reglas y fecha. Los casos ambiguos quedan "Requiere revisión" para la revisión asistida (HU-012) o manual (HU-013).

Aplica a dos orígenes de ítem: **ítems TVEC** candidatos y **ítems de contratos SECOP II** (registrados por la extracción documental o por el Administrador). La clasificación a nivel de contrato SECOP II y los contratos mixtos se tratan en la HU-011. La presencia del UNSPSC `52161505` no basta para incluir.

---

## Criterios de Aceptación

### Escenario 1: Televisor dentro del límite

- **Dado** que un ítem candidato tiene la descripción "TELEVISOR SAMSUNG 55\" UN55CU7000 SMART 4K"
- **Cuando** se ejecuta la clasificación por reglas
- **Entonces** queda `resultado = Incluido`, criterio "R10 — Televisor dentro del límite de categoría", método "Regla", versión de reglas y fecha

### Escenario 2: No es una compra

- **Dado** que un ítem tiene la descripción "Entrega en comodato de televisor 50 pulgadas"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con el criterio "R1 — No es una compra (comodato, arrendamiento o préstamo)" y término "comodato"

### Escenario 3: Ítem de contrato sin término de televisor

- **Dado** que un ítem de un contrato SECOP II tiene la descripción "Computador portátil Core i5 16 GB"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "R2 — El ítem no es un televisor"

### Escenario 4: Accesorio de televisor

- **Dado** que un ítem tiene la descripción "SOPORTE DE PARED PARA TV 32 A 70 PULGADAS" o "CONTROL REMOTO PARA TELEVISOR LG"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "R3 — Accesorio de televisor" y el término del accesorio

### Escenario 5: Servicio sobre televisores

- **Dado** que un ítem tiene la descripción "Mantenimiento preventivo de televisores del hospital"
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "R4 — Servicio sobre televisores (mantenimiento o instalación), no compra del bien"

### Escenario 6: Precio inseparable de instalación u obra

- **Dado** que un ítem tiene la descripción "Televisor 65 pulgadas incluida instalación y adecuación eléctrica" y no tiene costo de servicio discriminado
- **Cuando** se clasifica
- **Entonces** queda "Excluido" con "R5 — Precio inseparable de instalación, obra o servicio sin costo discriminado"; **y si** el ítem tiene `costo_servicio_discriminado = sí`, la regla R5 no aplica y se evalúan las siguientes

### Escenario 7: Coincidencia con un producto excluido

- **Dado** que un ítem tiene la descripción "Monitor TV 43 pulgadas para CCTV" o "Pantalla interactiva tipo smart tv 75\""
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "R6 — Coincide con un producto excluido del límite de categoría" y los términos encontrados

### Escenario 8: Lote que no menciona televisores

- **Dado** que un ítem SECOP II con descripción "Televisor 50 pulgadas" pertenece a un lote cuya descripción es "Lote 2: equipos de cómputo"
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "R7 — El lote del ítem no menciona televisores"

### Escenario 9: Kit o combo

- **Dado** que un ítem tiene la descripción "KIT TELEVISOR 43 + BARRA DE SONIDO"
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "R8 — Kit o combo: verificar que el precio unitario del televisor sea determinable"; **y si** el ítem tiene `precio_unitario_discriminado = no`, queda "Excluido" con "R8 — Kit sin precio unitario determinable"

### Escenario 10: Accesorio incluido con el televisor

- **Dado** que un ítem tiene la descripción "Televisor 55 pulgadas con soporte de pared"
- **Cuando** se clasifica
- **Entonces** queda "Requiere revisión" con "R9 — Accesorio incluido en el ítem sin precio discriminado"

### Escenario 11: Clasificación manual vigente

- **Dado** que un ítem tiene una clasificación vigente con método "Manual"
- **Cuando** se ejecuta la clasificación por reglas o una reclasificación total
- **Entonces** el ítem no se reclasifica y se cuenta como "Omitido por clasificación manual"

### Escenario 12: Reclasificación con nueva versión de reglas

- **Dado** que el Administrador guarda una nueva versión de listas de términos de las reglas
- **Cuando** ejecuta el comando de reclasificación total
- **Entonces** todos los ítems candidatos sin clasificación manual se reclasifican con la nueva versión, cada cambio de resultado agrega un evento al historial (el anterior se conserva) y el resumen muestra cuántos cambiaron de resultado

### Escenario 13: Lista de términos de regla inválida

- **Dado** que el Administrador intenta guardar una lista de reglas con un término de menos de 2 o más de 50 caracteres
- **Cuando** guarda
- **Entonces** se rechaza con "Los términos de las reglas deben tener entre 2 y 50 caracteres: {término}" y se conserva la versión vigente

### Escenario 14: Sin ítems pendientes

- **Dado** que no hay ítems en "Pendiente de clasificación"
- **Cuando** se ejecuta la clasificación
- **Entonces** termina sin cambios y registra "No hay ítems pendientes de clasificación."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); la clasificación automática la ejecuta el sistema.
- **Permisos requeridos:** rol Administrador para reclasificar y cambiar reglas.
- **Valor de negocio:** D4 mostró que el 28 % de los candidatos no son compras de televisores (la mitad con UNSPSC `52161505`); sin esta clasificación, las señales se construirían sobre productos no comparables. Meta de la épica: ≥ 95 % de acierto en una revisión de 50 candidatos al azar.

### Reglas de Negocio

- **RN-01 Ítems a clasificar:** (a) ítems TVEC con candidatura "Candidato"; (b) ítems de contratos SECOP II con candidatura "Candidato", registrados con al menos `descripcion_item` y, si existen, `lote_descripcion`, `costo_servicio_discriminado` (sí/no/nulo) y `precio_unitario_discriminado` (sí/no/nulo). Se clasifican los que están en "Pendiente de clasificación".
- **RN-02 Normalización:** la de la marcación de candidatos (minúsculas, sin tildes, caracteres no alfanuméricos → espacio, espacios colapsados). Los términos coinciden como palabras completas; la última palabra admite sufijos "s" o "es".
- **RN-03 Términos de televisor (T):** la lista vigente de candidatura (valor inicial: "televisor", "smart tv", "tv").
- **RN-04 Listas de términos por regla (configurables y versionadas; valores iniciales):**
  - **No compra (NC):** comodato, arrendamiento, alquiler, prestamo, en calidad de prestamo.
  - **Accesorios (AC):** soporte, base, rack, cable, hdmi, control, control remoto, antena, decodificador, convertidor, mueble, protector, forro.
  - **Servicios (SV):** mantenimiento, reparacion, servicio, instalacion, montaje, configuracion, diagnostico.
  - **Servicio u obra inseparable (SI):** instalacion, instalado, instalada, montaje, obra, adecuacion, cableado.
  - **Productos excluidos (PE):** videowall, video wall, pantalla modular, modulo led, senalizacion digital, digital signage, cartelera digital, monitor, cctv, circuito cerrado, videovigilancia, proyector, video beam, videobeam, pantalla interactiva, tablero interactivo, tactil, touch, inflable, solucion audiovisual, sistema audiovisual.
  - **Kits (KT):** kit, combo, paquete.
  - **Conectores de accesorio incluido (CI):** con, incluye, incluido, mas.
  - **Accesorios que se venden aparte (AA):** soporte, rack, mueble, antena, decodificador, barra de sonido, protector. Los elementos que normalmente vienen con el televisor (control remoto, cable de poder, base) no están en esta lista, para que "televisor con control remoto" no vaya a revisión.
  Cada término tiene de 2 a 50 caracteres tras normalizar (Escenario 13). Una lista puede quedar vacía; en ese caso su regla nunca se cumple.
- **RN-05 Reglas en orden (la primera que se cumple decide):**

  | Código | Condición | Resultado | Criterio |
  |---|---|---|---|
  | R1 | Contiene algún término NC | Excluido | No es una compra (comodato, arrendamiento o préstamo) |
  | R2 | No contiene ningún término T | Excluido | El ítem no es un televisor |
  | R3 | Un término AC aparece antes del primer término T (el accesorio es el producto principal del ítem) | Excluido | Accesorio de televisor |
  | R4 | Un término SV aparece antes del primer término T | Excluido | Servicio sobre televisores (mantenimiento o instalación), no compra del bien |
  | R5 | Un término SI aparece después del primer término T y `costo_servicio_discriminado` ≠ sí | Excluido | Precio inseparable de instalación, obra o servicio sin costo discriminado |
  | R6 | Contiene algún término PE | Requiere revisión | Coincide con un producto excluido del límite de categoría |
  | R7 | `lote_descripcion` no nula y sin términos T | Requiere revisión | El lote del ítem no menciona televisores |
  | R8a | Contiene algún término KT y `precio_unitario_discriminado` = no | Excluido | Kit sin precio unitario determinable |
  | R8b | Contiene algún término KT (otro caso) | Requiere revisión | Kit o combo: verificar que el precio unitario del televisor sea determinable |
  | R9 | Después del primer término T aparece un término CI seguido (a no más de 3 palabras) de un término AA, o aparece el símbolo "+" seguido de un término AA | Requiere revisión | Accesorio incluido en el ítem sin precio discriminado |
  | R10 | Ninguna anterior | Incluido | Televisor dentro del límite de categoría |

  El símbolo "+" de R9 se evalúa sobre el texto antes de normalizar. Para R5, `costo_servicio_discriminado` nulo se trata como "no".
- **RN-06 Registro de la clasificación:** cada clasificación agrega un evento con: `resultado` (Incluido / Excluido / Requiere revisión), `criterio_codigo`, `criterio_texto`, `terminos_coincidentes`, `metodo = Regla`, `version_reglas`, `fecha_hora`. La clasificación vigente es el último evento. Los eventos no se modifican ni se eliminan.
- **RN-07 Precedencia de la clasificación manual:** si la clasificación vigente tiene método "Manual", las reglas no la reemplazan (Escenario 11).
- **RN-08 Disparo:** automático al terminar la marcación de candidatos sobre los "Pendiente de clasificación"; manual por comando (pendientes o reclasificación total). La reclasificación total solo agrega un evento cuando el resultado o el criterio cambian.
- **RN-09 Estado de clasificación:** tras clasificar, `estado_clasificacion` = "Clasificado" (si es Incluido o Excluido) o "En revisión" (si es Requiere revisión).
- **RN-10 Resumen:** "Clasificación por reglas: {n} evaluados. Incluidos: {n}. Excluidos: {n}. Requiere revisión: {n}. Omitidos por clasificación manual: {n}. Cambiaron de resultado: {n}." y totales por código de criterio.
- **RN-11 Lenguaje:** los criterios describen el producto o la naturaleza del ítem; no califican a la entidad ni al proveedor.

### Interfaz

No requiere interfaz gráfica. Comandos "clasificar ítems pendientes" y "reclasificar todos los ítems"; configuración de listas por archivo o comando. Resumen en consola o log (RN-10).

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre ítems ya registrados en el sistema.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-008, HU-009 (candidatos), HU-011 (contratos SECOP II y contratos mixtos), HU-012 (sugerencia con IA), HU-013 (corrección manual).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El PRD define las categorías del límite pero no los términos que las detectan → resuelto con listas iniciales configurables y versionadas (RN-04).
- Algunas exclusiones no pueden decidirse solo con texto (monitor vs. televisor, lote, kit) → resuelto: se envían a "Requiere revisión" en lugar de excluir (R6, R7, R8b, R9).
- Los ítems SECOP II llegan desde la extracción documental (otra épica) o por registro del Administrador → resuelto: esta historia define los campos mínimos que necesita (RN-01) sin depender de cómo se crearon.
- Un accesorio incluido sin precio discriminado no siempre invalida el ítem → resuelto como "Requiere revisión" (R9).

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-001 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
