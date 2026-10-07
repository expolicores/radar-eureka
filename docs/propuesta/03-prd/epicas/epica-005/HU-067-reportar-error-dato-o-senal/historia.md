# Historia #067: Reportar un error en un dato o en una señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Validación Humana de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-070

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** reportar que un dato (por ejemplo, una cantidad mal leída) o una señal completa tiene un error, describiendo el problema y, si lo sé, el valor correcto,  
**Para** que el Administrador lo revise y corrija, y que las señales se apoyen en datos cada vez más confiables.

## Descripción

Los Analistas piloto no limpian datos: evalúan señales y **reportan errores** (decisión P-08). Desde el detalle de la señal o desde la vista de evidencia, el Analista abre "Reportar un error", elige sobre qué es el reporte (la señal en conjunto, un campo del ítem, el emparejamiento o una observación de referencia), el tipo de error, una descripción y opcionalmente un valor sugerido. El reporte queda en estado **"Recibido"** para que el Administrador lo gestione (HU-068).

El Analista ve el estado de sus reportes en la señal, y cualquier usuario ve un aviso cuando una señal tiene reportes abiertos.

---

## Criterios de Aceptación

### Escenario 1: Reportar una cantidad mal leída

- **Dado** que el Analista está en el detalle de la señal SG-1 cuya cantidad mostrada es 80
- **Cuando** elige "Reportar un error", objeto "Dato del ítem: Cantidad", tipo "Dato mal extraído", descripción "En la página 4 de la oferta la cantidad es 8, no 80", valor sugerido "8", y pulsa "Enviar reporte"
- **Entonces** ve "Recibimos tu reporte RE-000001. El equipo lo revisará.", el reporte queda en estado "Recibido" con el valor mostrado (80), y aparece en "Mis reportes en esta señal"

### Escenario 2: Reportar la señal completa

- **Dado** que el Analista considera que el producto comparado no es comparable
- **Cuando** elige objeto "La señal completa", tipo "Producto no comparable", con descripción válida
- **Entonces** el reporte se registra vinculado a la señal y su versión

### Escenario 3: Reportar una observación de referencia

- **Dado** que el Analista está en la evidencia de una observación de Alkosto
- **Cuando** pulsa "Reportar un error" desde esa vista
- **Entonces** el formulario se abre con el objeto "Observación de referencia: {identificador}" preseleccionado

### Escenario 4: Validaciones del formulario

- **Dado** que el Analista abre el formulario
- **Cuando** intenta enviar sin objeto, sin tipo, con descripción de menos de 10 caracteres, con descripción de más de 2.000 caracteres o con valor sugerido de más de 200 caracteres
- **Entonces** ve, junto al campo correspondiente, "Selecciona sobre qué es el reporte.", "Selecciona el tipo de error.", "Describe el error con al menos 10 caracteres.", "La descripción admite máximo 2.000 caracteres." o "El valor sugerido admite máximo 200 caracteres.", y no se envía

### Escenario 5: Reporte duplicado

- **Dado** que el Analista ya tiene un reporte abierto ("Recibido" o "En revisión") sobre el mismo objeto de la misma señal
- **Cuando** intenta enviar otro
- **Entonces** ve "Ya tienes un reporte abierto sobre este dato (RE-000001)." y no se crea un reporte nuevo

### Escenario 6: Aviso de reportes abiertos en la señal

- **Dado** que la señal SG-1 tiene 2 reportes abiertos de distintos Analistas
- **Cuando** cualquier usuario abre el detalle de SG-1
- **Entonces** ve el aviso "Esta señal tiene 2 reporte(s) de error en revisión." (sin ver el contenido de reportes ajenos)

### Escenario 7: Ver el estado y la resolución de mis reportes

- **Dado** que el Administrador cerró el reporte RE-000001 como "Corregido" con la resolución "Cantidad corregida a 8"
- **Cuando** el Analista abre la señal
- **Entonces** en "Mis reportes en esta señal" ve RE-000001 con estado "Corregido", fecha y la resolución

### Escenario 8: Error al enviar y doble envío

- **Dado** que el envío falla o el Analista pulsa "Enviar reporte" dos veces seguidas
- **Cuando** se procesa
- **Entonces** ante falla ve "No pudimos enviar tu reporte. Intenta de nuevo." conservando lo escrito; ante doble pulsación se crea un solo reporte

### Escenario 9: Cancelar

- **Dado** que el Analista abrió el formulario y escribió datos
- **Cuando** pulsa "Cancelar"
- **Entonces** el formulario se cierra sin crear reporte

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (principal). El Administrador también puede crear reportes.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Mecanismo de corrección exigido para reducir el riesgo legal y reputacional y mejorar la calidad de las señales.

### Reglas de Negocio

**RN-01 – Puntos de entrada.** Botón "Reportar un error" en el detalle de la señal y en la vista de evidencia (precio contratado u observación). Desde la evidencia, el objeto llega preseleccionado.

**RN-02 – Objeto del reporte** (obligatorio, uno):
- "La señal completa".
- "Dato del ítem: {campo}", con campo ∈ {Precio unitario, Cantidad, Marca, Modelo, Tamaño, Resolución, Tecnología, Smart, Base tributaria (IVA), Clasificación como televisor}.
- "Emparejamiento del producto".
- "Observación de referencia: {identificador}" (lista de observaciones de la versión vista).

**RN-03 – Tipo de error** (obligatorio, uno): "Dato mal extraído", "Producto no comparable", "Observación de referencia incorrecta", "Base tributaria incorrecta", "Otro".

**RN-04 – Campos de texto.** Descripción: obligatoria, 10 a 2.000 caracteres tras recortar espacios. Valor sugerido: opcional, máximo 200 caracteres.

**RN-05 – Registro.** Identificador "RE-" + 6 dígitos consecutivos (RE-000001, RE-000002…); estado inicial "Recibido"; usuario; fecha-hora; ítem; señal y versión (si el reporte se hizo desde una señal); objeto; valor mostrado al momento del reporte (copiado de la instantánea); tipo; descripción; valor sugerido. Se registra también en el log de auditoría (acción "creación de reporte de error").

**RN-06 – Duplicados.** No se permite un segundo reporte abierto ("Recibido" o "En revisión") del mismo usuario sobre el mismo objeto de la misma señal. Mensaje: "Ya tienes un reporte abierto sobre este dato ({id})." Un doble envío crea un solo reporte.

**RN-07 – Aviso público.** Si la señal tiene ≥ 1 reporte abierto (de cualquier usuario), su detalle muestra "Esta señal tiene {n} reporte(s) de error en revisión.", con n = número de reportes abiertos. El contenido de reportes ajenos no es visible para los Analistas.

**RN-08 – Mis reportes.** En el detalle de la señal, el bloque "Mis reportes en esta señal" lista los reportes del usuario con identificador, objeto, estado (Recibido / En revisión / Corregido / Descartado), fecha de creación y, si está cerrado, fecha de cierre y resolución. Si no tiene reportes, el bloque no se muestra.

**RN-09 – Mensajes.** Éxito: "Recibimos tu reporte {id}. El equipo lo revisará." Error: "No pudimos enviar tu reporte. Intenta de nuevo." Validaciones: los de RN-04 y el Escenario 4.

**RN-10 – Efecto.** Crear un reporte no cambia ningún dato, benchmark ni señal; los cambios ocurren solo si el Administrador corrige el dato por los mecanismos de revisión.

### Interfaz

Formulario modal "Reportar un error" con: objeto (lista), tipo (lista), descripción (área de texto con contador "{n}/2.000"), valor sugerido (texto), botones "Enviar reporte" y "Cancelar". Bloques en el detalle de la señal: aviso de reportes abiertos y "Mis reportes en esta señal". Accesible por teclado; funcional desde 360 px.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-063 (detalle de la señal), HU-064 (evidencia), HU-068 (gestión de reportes).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Catálogo de objetos y tipos de error**: resuelto en RN-02/RN-03.
- **Aviso visible de reportes abiertos** a todos los usuarios, sin contenido ajeno: resuelto en RN-07.
- **Puntos de entrada limitados al detalle de la señal y a la evidencia** en esta HU: resuelto en RN-01.

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
