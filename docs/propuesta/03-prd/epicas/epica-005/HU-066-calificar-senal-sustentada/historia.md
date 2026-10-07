# Historia #066: Calificar una señal como suficientemente sustentada para merecer revisión

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Validación Humana de Señales  
**Prioridad:** Crítica  
**FRs relacionados:** FR-069

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** calificar una señal como "suficientemente sustentada para merecer revisión" o "no suficientemente sustentada", con un comentario opcional,  
**Para** dejar mi juicio sobre la calidad de la evidencia y alimentar la medición de si el producto genera señales útiles.

## Descripción

Desde el detalle de una señal vigente, el Analista elige una de dos calificaciones y puede escribir un comentario. La calificación se guarda por Analista y por **versión** de la señal, porque si la señal se recalcula la evidencia cambia. Estas calificaciones son el insumo del KPI de validación humana (meta: ≥ 70 % de las señales calificadas como sustentadas por al menos 3 usuarios del perfil de diseño); el cálculo y la presentación del KPI se hacen en la épica de operación y medición.

Calificar "sustentada" no significa que exista una irregularidad: significa que la señal tiene evidencia suficiente para que valga la pena revisarla.

---

## Criterios de Aceptación

### Escenario 1: Calificar como sustentada

- **Dado** que el Analista "analista.piloto1" está en el detalle de la versión vigente de la señal SG-1 y no la ha calificado
- **Cuando** elige "Suficientemente sustentada para merecer revisión", escribe "Mismo modelo, 7 compras TVEC cercanas" y pulsa "Guardar calificación"
- **Entonces** ve "Tu calificación quedó registrada." y el bloque muestra "Tu calificación: Suficientemente sustentada para merecer revisión" con fecha y comentario

### Escenario 2: Calificar sin comentario

- **Dado** el mismo contexto
- **Cuando** elige "No suficientemente sustentada" sin comentario y guarda
- **Entonces** la calificación se guarda con comentario vacío

### Escenario 3: Guardar sin elegir opción

- **Dado** que el Analista no ha elegido ninguna opción
- **Cuando** pulsa "Guardar calificación"
- **Entonces** ve "Selecciona una calificación." y no se guarda nada

### Escenario 4: Comentario demasiado largo

- **Dado** que el Analista escribe un comentario de 1.001 caracteres
- **Cuando** intenta guardar
- **Entonces** ve "El comentario admite máximo 1.000 caracteres." y no se guarda; con 1.000 caracteres se guarda

### Escenario 5: Cambiar la calificación

- **Dado** que el Analista ya calificó la versión vigente como "No suficientemente sustentada"
- **Cuando** la cambia a "Suficientemente sustentada para merecer revisión" y guarda
- **Entonces** su calificación vigente para esa versión es la nueva, y el cambio queda en el historial con fecha-hora (sin crear una segunda calificación vigente)

### Escenario 6: Nueva versión de la señal

- **Dado** que el Analista calificó la versión 1 y la señal pasó a la versión 2
- **Cuando** abre la señal
- **Entonces** ve "Calificaste la versión anterior: {calificación}. La señal cambió; puedes calificar la versión actual." y el formulario vacío para la versión 2; la calificación de la versión 1 se conserva

### Escenario 7: Señal no vigente o versión anterior

- **Dado** que la señal está "No vigente" o el Analista está viendo una versión que no es la más reciente
- **Cuando** busca calificarla
- **Entonces** el formulario no está disponible y se muestra "Esta señal ya no está vigente; no se puede calificar." o "Solo se califica la versión más reciente de la señal.", respectivamente

### Escenario 8: Administrador

- **Dado** que el usuario tiene rol Administrador
- **Cuando** abre el detalle de una señal o intenta registrar una calificación
- **Entonces** no ve el formulario y, si intenta registrarla por otro medio, se rechaza con "Solo los analistas pueden calificar señales."

### Escenario 9: Error al guardar y doble envío

- **Dado** que el guardado falla o el Analista pulsa "Guardar calificación" dos veces seguidas
- **Cuando** se procesa la acción
- **Entonces** ante falla ve "No pudimos guardar tu calificación. Intenta de nuevo." conservando lo escrito; ante doble pulsación queda una sola calificación registrada

### Escenario 10: Calificaciones de otros Analistas

- **Dado** que otro Analista calificó la misma señal
- **Cuando** "analista.piloto1" abre el detalle
- **Entonces** no ve la calificación ni el comentario del otro Analista

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (usuario de diseño del piloto).
- **Permisos requeridos:** Sesión iniciada con rol Analista. El Administrador no califica; puede consultar todas las calificaciones para la medición.
- **Valor de negocio:** Insumo directo del KPI de validación humana (NFR-CAL-007).

### Reglas de Negocio

**RN-01 – Valores.** Exactamente dos: "Suficientemente sustentada para merecer revisión" y "No suficientemente sustentada". Obligatorio elegir uno.

**RN-02 – Comentario.** Opcional; texto libre de 0 a 1.000 caracteres después de quitar espacios al inicio y al final; si solo tiene espacios se guarda vacío. Contador visible "{n}/1.000".

**RN-03 – Unicidad.** Una calificación vigente por (Analista, señal, versión). Cambiarla reemplaza la vigente y guarda la anterior en el historial con fecha-hora. Un doble envío no crea registros duplicados.

**RN-04 – Elegibilidad.** Solo se califica la versión más reciente de una señal en estado "Vigente". Señales "No vigente" o versiones anteriores: formulario no disponible con el mensaje correspondiente (Escenario 7).

**RN-05 – Rol.** Solo el rol Analista registra calificaciones. Intentos de otro rol → "Solo los analistas pueden calificar señales."

**RN-06 – Privacidad entre Analistas.** Cada Analista ve solo su propia calificación. El Administrador puede consultar todas (por consulta o reporte), sin interfaz específica en esta HU.

**RN-07 – Datos registrados.** Identificador de la señal, versión, benchmark, identificador del Analista, valor, comentario, fecha-hora de creación y de última modificación, e historial de cambios.

**RN-08 – Mensajes.** Éxito: "Tu calificación quedó registrada." Falta de opción: "Selecciona una calificación." Comentario largo: "El comentario admite máximo 1.000 caracteres." Error: "No pudimos guardar tu calificación. Intenta de nuevo." Versión anterior calificada: "Calificaste la versión anterior: {calificación}. La señal cambió; puedes calificar la versión actual."

**RN-09 – Lenguaje.** Los textos del formulario no usan términos acusatorios; el comentario del Analista se guarda tal como lo escribió.

### Interfaz

Bloque "Califica esta señal" en el detalle de la señal, debajo de la confianza: dos opciones excluyentes, campo de comentario con contador, botón "Guardar calificación" y, si existe, "Tu calificación: {valor}" con fecha (DD/MM/AAAA) y comentario, editable mientras la versión siga vigente. Accesible por teclado.

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

**Historias relacionadas:** HU-059 (versiones de la señal), HU-063 (detalle de la señal).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Calificación por versión de la señal**: resuelto en RN-03/RN-04.
- **El Administrador no califica** (para no sesgar el KPI de usuarios del perfil de diseño): resuelto en RN-05.
- **Calificaciones independientes entre Analistas** (no se ven las de otros): resuelto en RN-06.
- **Longitud máxima del comentario (1.000 caracteres)**: resuelto en RN-02.

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
