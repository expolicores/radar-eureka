# Historia #074: Ver la lista priorizada de señales que merecen revisión

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Priorización de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-073

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en una sola lista todas las señales que merecen revisión, ordenadas por prioridad y con los datos clave de cada una,  
**Para** decidir rápidamente qué señal abrir primero y llegar a su evidencia en pocos pasos.

## Descripción

Esta HU entrega la vista "Señales": una lista con una fila por cada **señal que merece revisión vigente** (una señal corresponde a un ítem de televisor). La lista se prioriza por defecto con una regla explícita (nivel de confianza, luego desviación, luego fecha) y muestra, para cada señal, el ítem, el contrato u orden, la entidad, el proveedor, el precio contratado, la referencia usada, la desviación, el tipo de emparejamiento y el nivel de confianza.

Las señales las calcula el proceso de comparación de la plataforma; esta HU solo las lista. Desde cada fila el Analista puede abrir el detalle de la señal (vista de señales con su evidencia, de otra épica) o la ficha del contrato (HU-076). La lista muestra de forma visible la advertencia de que una señal no constituye una conclusión ni una acusación.

Los filtros y el orden configurable de esta lista se especifican en HU-075.

---

## Criterios de Aceptación

### Escenario 1: Abrir la lista de señales (happy path)

- **Dado** que el Analista inició sesión y existen señales vigentes
- **Cuando** abre la opción de menú "Señales"
- **Entonces** ve la lista de señales vigentes ordenada por la prioridad por defecto (RN-03), 25 por página, con el texto "{total} señales que merecen revisión" y las columnas de RN-04

### Escenario 2: Advertencia visible

- **Dado** que el Analista está en la lista de señales
- **Cuando** la lista se muestra
- **Entonces** sobre la lista aparece la advertencia "Una señal indica que un precio merece revisión. No constituye una conclusión ni una acusación sobre la entidad, el proveedor o las personas relacionadas."

### Escenario 3: Abrir el detalle de una señal

- **Dado** que el Analista ve una señal en la lista
- **Cuando** activa la acción "Ver señal" de esa fila
- **Entonces** se abre el detalle de esa señal, desde donde la evidencia de origen queda a un clic más (máximo 3 clics desde la lista hasta la evidencia)

### Escenario 4: Abrir la ficha del contrato desde una señal

- **Dado** que el Analista ve una señal en la lista
- **Cuando** activa el identificador del contrato u orden de esa fila
- **Entonces** se abre la ficha del contrato u orden posicionada en el ítem de la señal

### Escenario 5: Señal con Benchmark 2 no disponible

- **Dado** que una señal se generó contra el Benchmark 1 y el Benchmark 2 del ítem está "no disponible / evidencia insuficiente"
- **Cuando** aparece en la lista
- **Entonces** la columna "Referencia" muestra el benchmark de compras públicas usado y la señal se lista igual que las demás

### Escenario 6: Señal con comparación incompleta por base tributaria

- **Dado** que la comparación que sustenta una señal está marcada como incompleta o no confiable por base tributaria (IVA) indeterminada
- **Cuando** aparece en la lista
- **Entonces** la fila muestra la marca "IVA indeterminado — comparación incompleta" junto a la referencia

### Escenario 7: Precio unitario derivado

- **Dado** que el precio unitario del ítem de la señal es derivado (valor total del ítem / cantidad)
- **Cuando** aparece en la lista
- **Entonces** el precio contratado muestra la marca "Derivado"; si es publicado en el documento, la marca "Explícito"

### Escenario 8: No hay señales vigentes

- **Dado** que no existe ninguna señal vigente
- **Cuando** el Analista abre "Señales"
- **Entonces** ve el mensaje "Por ahora no hay señales que merezcan revisión. Puedes explorar todas las compras de televisores en Exploración." con un enlace a "Exploración"

### Escenario 9: Paginación

- **Dado** que hay más de 25 señales
- **Cuando** el Analista usa "Anterior", "Siguiente", un número de página o cambia el tamaño de página a 50 o 100
- **Entonces** se muestra el bloque correspondiente con el texto "Mostrando {desde}–{hasta} de {total}", conservando el orden; al cambiar el tamaño vuelve a la página 1

### Escenario 10: Volver a la lista conservando el estado

- **Dado** que el Analista abrió una señal o una ficha desde la página 2 de la lista
- **Cuando** vuelve con "Volver a señales" o el botón atrás del navegador
- **Entonces** la lista se muestra en la misma página, con el mismo tamaño de página, orden y filtros

### Escenario 11: Error al cargar la lista

- **Dado** que la consulta de señales falla o no responde en 15 segundos
- **Cuando** el Analista espera la lista
- **Entonces** ve "No fue posible cargar las señales. Intenta de nuevo en unos minutos." con el botón "Reintentar" (una consulta por clic)

### Escenario 12: Acceso sin sesión o con sesión expirada

- **Dado** que una persona sin sesión, o con la sesión expirada, abre o usa la lista de señales
- **Cuando** el sistema procesa la solicitud
- **Entonces** no muestra ninguna señal y redirige al inicio de sesión (con el mensaje "Tu sesión expiró. Inicia sesión de nuevo para continuar." si había expirado); tras iniciar sesión vuelve a la lista

### Escenario 13: Estado de carga

- **Dado** que la lista se está cargando
- **Cuando** aún no llega la respuesta
- **Entonces** se muestra un indicador de carga, los controles de paginación quedan deshabilitados y un lector de pantalla anuncia "Cargando señales"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador puede consultar la misma lista.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Es el inicio del recorrido principal del analista ("abre la lista priorizada de señales") y el punto desde el que se mide el acceso a la evidencia en ≤ 3 clics.

### Reglas de Negocio

- **RN-01 Contenido de la lista:** una fila por señal vigente, es decir, por ítem de televisor al que el último cálculo de comparación le generó una "señal que merece revisión". Las señales que dejan de estar vigentes tras un nuevo cálculo desaparecen de la lista. Los precios anormalmente bajos no son señales y no aparecen.
- **RN-02 Unidad:** un contrato con varios ítems con señal aparece en varias filas, una por ítem.
- **RN-03 Prioridad por defecto (configurable como regla de presentación, valor inicial):** 1) nivel de confianza de la señal de mayor a menor (Alta > Media > Baja); 2) desviación porcentual de la señal de mayor a menor; 3) fecha de compra más reciente primero; 4) identificador del contrato u orden ascendente. Esta prioridad solo ordena la revisión; no significa que una señal sea más grave que otra.
- **RN-04 Columnas:** Ítem (marca + modelo normalizado + tamaño en pulgadas; si faltan, descripción original truncada a 80 caracteres con "…"), Contrato u orden (fuente + identificador, enlace a la ficha), Entidad, Proveedor, Fecha de compra, Precio unitario contratado (con marca "Explícito" o "Derivado"), Referencia (benchmark usado — "Compras públicas" o "Mercado" — y el valor de referencia, o "Referencia disponible ({n} obs.)" cuando no hay referencia estadística agregada), Desviación (con signo, una decimal, ej. "+35,2 %"), Emparejamiento ("Mismo modelo" o "Producto equivalente") y Nivel de confianza ("Alta", "Media" o "Baja").
- **RN-05 Marcas adicionales:** "IVA indeterminado — comparación incompleta" cuando la comparación que sustenta la señal está marcada como incompleta o no confiable por base tributaria; "Derivado" / "Explícito" según el tipo de precio unitario.
- **RN-06 Datos faltantes:** campo no publicado → "Sin dato"; nunca se oculta una señal por datos de contexto faltantes (ej. proveedor sin publicar).
- **RN-07 Advertencia:** la advertencia del Escenario 2 se muestra siempre que haya al menos una señal, en la parte superior y antes de la primera fila, también en móvil.
- **RN-08 Lenguaje:** ningún texto usa "sobreprecio", "corrupción", "fraude" ni "hallazgo fiscal"; se usa "señal que merece revisión".
- **RN-09 Navegación a la evidencia:** "Ver señal" abre el detalle de la señal; la evidencia de origen (documento y página del precio, observaciones usadas) es accesible desde ese detalle con un clic, para cumplir ≤ 3 clics desde la lista.
- **RN-10 Paginación y estado:** 25 por defecto; opciones 25, 50 y 100; página, tamaño, orden y filtros en la URL; valores inválidos → valores por defecto sin error.
- **RN-11 Formatos:** fechas `DD/MM/AAAA` (hora de Colombia); pesos `$ 2.862.500`; porcentajes con coma decimal.
- **RN-12 Tiempo de respuesta:** ≤ 3 segundos (p95) en carga y paginación con el volumen del MVP y 20 usuarios concurrentes (objetivo inicial de diseño, recalibrable); error a los 15 segundos sin respuesta (valor inicial configurable).
- **RN-13 Accesibilidad y responsive (valores iniciales de diseño):** WCAG 2.1 AA (teclado, foco visible, contraste, marcas con texto además de color); escritorio desde 1366 × 768 px, tablet desde 768 px y móvil desde 360 px (tarjetas etiqueta–valor con todas las columnas y acciones); 2 últimas versiones de Chrome, Edge, Firefox y Safari.

### Interfaz

- Opción de menú "Señales".
- Encabezado "Señales que merecen revisión" con el texto de conteo y la advertencia permanente.
- Tabla con las columnas de RN-04; por fila, acción "Ver señal" y enlace del identificador del contrato u orden.
- Espacio para filtros y orden configurable (HU-075) y para la fecha de actualización de los datos (HU-083).
- Paginación "Anterior / números / Siguiente" y "Resultados por página: 25 / 50 / 100".
- Estados: carga, sin señales (con enlace a "Exploración"), error con "Reintentar".

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa las señales vigentes, referencias, desviaciones, tipo de emparejamiento, base tributaria y confianza calculadas por la plataforma, y los datos de contrato ingeridos de SECOP II y TVEC.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-075 (filtrar y ordenar la lista de señales), HU-076 (ficha del contrato), HU-079 (señales en la ficha), HU-083 (fecha de actualización)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-03):** "lista priorizada" se define como confianza descendente, luego desviación descendente, luego fecha más reciente, luego identificador; es una regla de presentación configurable que solo ordena la revisión.
- **Resuelto (RN-01, RN-02):** la lista muestra una fila por señal vigente (por ítem), según el último cálculo.
- **Resuelto (RN-09):** el detalle de la señal y su evidencia los provee la vista de señales; esta lista solo enlaza a ella.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-006 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
