# Historia #013: Revisión y corrección manual de la clasificación de candidatos

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Clasificar Ítems de Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-016, FR-015

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP (que actúa como Revisor),  
**Quiero** revisar los candidatos que requieren revisión, corregir o confirmar la clasificación de cualquier candidato con un motivo y un comentario, y verificar la clasificación sobre una muestra aleatoria,  
**Para** que el universo de televisores sea confiable, cada corrección quede registrada con usuario y fecha, y pueda medir si la clasificación cumple la meta de acierto de la épica.

## Descripción

Las reglas y la IA dejan candidatos en "Requiere revisión" y pueden equivocarse en otros. Esta historia da al Administrador tres capacidades, sin exigir interfaz gráfica (puede hacerse por comandos, scripts o una interfaz administrativa mínima):

1. **Cola de revisión de clasificación:** lista los ítems y contratos en "Requiere revisión" con el texto, el criterio aplicado y, si existe, la sugerencia de IA.
2. **Corrección o confirmación manual:** cambia el resultado (Incluido / Excluido / Requiere revisión) de un candidato con motivo y comentario, o confirma que la clasificación vigente es correcta. Cada acción conserva el valor anterior, el nuevo, el usuario y la fecha. La clasificación manual prevalece sobre las reglas y la IA, y puede devolverse a la clasificación automática.
3. **Muestra de verificación:** selecciona al azar candidatos clasificados automáticamente para revisarlos y calcula el porcentaje de acierto (meta de la épica: ≥ 95 % en 50 candidatos).

---

## Criterios de Aceptación

### Escenario 1: Consultar la cola de revisión

- **Dado** que existen 3 candidatos en "Requiere revisión" (2 ítems y 1 contrato), uno con sugerencia de IA
- **Cuando** el Administrador consulta la cola de revisión de clasificación
- **Entonces** obtiene los 3, ordenados del más antiguo al más reciente en revisión, con: identificador, tipo (ítem TVEC / ítem SECOP II / contrato SECOP II), texto evaluado, criterio vigente, fecha de entrada a revisión y, si existe, resultado propuesto, categoría, justificación y confianza de la IA

### Escenario 2: Cola vacía

- **Dado** que no hay candidatos en "Requiere revisión"
- **Cuando** el Administrador consulta la cola
- **Entonces** obtiene "No hay candidatos pendientes de revisión de clasificación."

### Escenario 3: Corrección manual exitosa

- **Dado** que el ítem "Monitor TV 43 pulgadas para CCTV" está en "Requiere revisión" por la regla R6
- **Cuando** el Administrador lo clasifica como "Excluido" con motivo "Producto excluido: monitor o CCTV" y comentario "La ficha técnica del ítem indica monitor de vigilancia"
- **Entonces** se agrega una clasificación vigente "Excluido" con método "Manual", y queda registrado el valor anterior (resultado, criterio y método), el nuevo, el motivo, el comentario, el usuario y la fecha y hora; se muestra "Clasificación actualizada: {id} pasó de Requiere revisión a Excluido."

### Escenario 4: Corrección sobre una clasificación automática ya resuelta

- **Dado** que un ítem está "Incluido" por la regla R10
- **Cuando** el Administrador lo clasifica como "Excluido" con motivo "Accesorio" y un comentario válido
- **Entonces** la corrección se registra igual que en el Escenario 3 y su indicador `en_analisis` pasa a "no"

### Escenario 5: Efectos sobre el contrato y el análisis

- **Dado** que se corrige manualmente un ítem SECOP II o el propio contrato
- **Cuando** se guarda la corrección
- **Entonces** se recalcula la clasificación derivada del contrato (si no es manual) y el indicador `en_analisis` de los ítems afectados: un ítem SECOP II entra al análisis solo si su clasificación vigente es "Incluido" y la del contrato no es "Excluido"; un ítem TVEC solo si su clasificación vigente es "Incluido"

### Escenario 6: Validaciones de la corrección

- **Dado** que el Administrador envía una corrección
- **Cuando** el candidato no existe, no es candidato, el resultado o el motivo no están en las listas permitidas, el comentario tiene menos de 10 o más de 500 caracteres, o el resultado y el motivo son iguales a los vigentes
- **Entonces** no se registra nada y se muestra, según el caso: "No existe el candidato {id}.", "Solo se puede clasificar un candidato; {id} está marcado como No candidato.", "El resultado debe ser Incluido, Excluido o Requiere revisión.", "El motivo no pertenece a la lista de motivos permitidos.", "El comentario es obligatorio y debe tener entre 10 y 500 caracteres." o "La clasificación indicada es igual a la vigente; no se registró ningún cambio."

### Escenario 7: Confirmación sin cambio

- **Dado** que un candidato tiene una clasificación vigente correcta
- **Cuando** el Administrador la confirma con un comentario opcional
- **Entonces** se registra un evento de revisión de tipo "Confirmación" con usuario, fecha y hora, sin cambiar el resultado vigente; si estaba en "Requiere revisión", la confirmación se rechaza con "Un candidato en Requiere revisión no se puede confirmar; clasifíquelo como Incluido o Excluido."

### Escenario 8: La clasificación manual prevalece

- **Dado** que un candidato tiene clasificación vigente manual
- **Cuando** se ejecuta una reclasificación por reglas o la clasificación asistida por IA
- **Entonces** su clasificación vigente no cambia

### Escenario 9: Devolver a clasificación automática

- **Dado** que un candidato tiene clasificación vigente manual
- **Cuando** el Administrador ejecuta "devolver a clasificación automática" con un comentario válido
- **Entonces** se registra el evento con usuario y fecha, el candidato pasa a "Pendiente de clasificación" y se reclasifica con las reglas vigentes; su historial se conserva

### Escenario 10: Generar una muestra de verificación

- **Dado** que existen al menos 50 candidatos con clasificación vigente "Incluido" o "Excluido" de método "Regla", "IA" o "Derivado de ítems"
- **Cuando** el Administrador genera una muestra de tamaño 50
- **Entonces** se seleccionan 50 candidatos al azar entre ellos, se registra la muestra con identificador, fecha, semilla de aleatoriedad, tamaño y lista de candidatos, y cada candidato de la muestra queda "Pendiente de verificación"

### Escenario 11: Muestra con población insuficiente o tamaño inválido

- **Dado** que la población elegible tiene menos candidatos que el tamaño pedido, o el tamaño está fuera de 10 a 500
- **Cuando** el Administrador genera la muestra
- **Entonces** no se crea y se muestra "La población elegible tiene {n} candidatos; el tamaño de la muestra debe estar entre 10 y {mínimo entre 500 y n}."

### Escenario 12: Resultado de la verificación

- **Dado** que en una muestra de 50 el Administrador confirmó 48 y corrigió 2
- **Cuando** consulta el resultado de la muestra
- **Entonces** obtiene "Muestra {id}: revisados 50 de 50. Confirmados: 48. Corregidos: 2. Acierto: 96,0 % (meta de la épica: ≥ 95 %)." y la lista de los corregidos con su valor anterior y nuevo

### Escenario 13: Acceso restringido

- **Dado** que un usuario con rol Analista intenta consultar la cola, corregir, confirmar o generar una muestra
- **Cuando** ejecuta la acción
- **Entonces** se deniega y no se registra ningún cambio

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP, que en el MVP es el PO y actúa como Revisor.
- **Permisos requeridos:** rol Administrador para todas las acciones. El Analista no corrige clasificaciones (reporta errores por el mecanismo de corrección de otra épica).
- **Valor de negocio:** asegura que el universo y el denominador de la cobertura sean correctos, y mide el criterio de aceptación de la épica (≥ 95 % de acierto en 50 candidatos al azar).

### Reglas de Negocio

- **RN-01 Candidatos:** ítems TVEC, ítems SECOP II y contratos SECOP II con candidatura "Candidato". Los "No candidato" no se clasifican.
- **RN-02 Cola de revisión:** candidatos con clasificación vigente "Requiere revisión"; orden por fecha de entrada a revisión ascendente; filtros opcionales por tipo de candidato y por código de criterio; muestra la última sugerencia de IA si existe.
- **RN-03 Resultados permitidos:** Incluido, Excluido, Requiere revisión.
- **RN-04 Motivos permitidos (lista cerrada):** Televisor de consumo; Producto excluido: videowall o pantalla modular; Producto excluido: señalización digital; Producto excluido: monitor o CCTV; Producto excluido: proyector; Producto excluido: pantalla interactiva o inflable; Producto excluido: solución audiovisual integral; Accesorio; Servicio de mantenimiento o instalación; No es una compra; Lote que no corresponde al televisor; Kit sin precio unitario determinable; Precio inseparable de instalación, obra o servicio; Información insuficiente; Contrato con al menos un televisor (solo contratos).
- **RN-05 Comentario:** obligatorio en correcciones y en "devolver a clasificación automática" (10 a 500 caracteres, sin contar espacios de los extremos); opcional en confirmaciones (máximo 500).
- **RN-06 Registro de la corrección:** evento con `tipo = Corrección`, `resultado_anterior`, `criterio_anterior`, `metodo_anterior`, `resultado_nuevo`, `motivo`, `comentario`, `usuario`, `fecha_hora`, `metodo = Manual`. La clasificación vigente pasa a ser la manual. Los eventos no se modifican ni se eliminan.
- **RN-07 Precedencia:** mientras la vigente sea manual, las reglas y la IA no la reemplazan. Una nueva corrección manual sí la reemplaza (con su propio evento).
- **RN-08 Devolver a automática:** evento `tipo = Devolución a automática` con usuario, fecha y comentario; el candidato vuelve a "Pendiente de clasificación" y se reclasifica de inmediato con las reglas vigentes (y luego, si queda en revisión, es elegible para la IA).
- **RN-09 Confirmación:** evento `tipo = Confirmación` con usuario, fecha y comentario opcional; no cambia resultado ni método vigentes; no aplica a "Requiere revisión" (Escenario 7).
- **RN-10 Estado tras la corrección:** "Incluido" o "Excluido" → `estado_clasificacion = Clasificado`; "Requiere revisión" → "En revisión".
- **RN-11 Efectos (recalculados al guardar):** clasificación derivada del contrato SECOP II si su vigente no es manual (≥ 1 ítem Incluido → Incluido; todos Excluido → Excluido; otro caso → Requiere revisión); `en_analisis` de los ítems según el Escenario 5; `apto_gestion_documental` del contrato = sí si su vigente es Incluido o Requiere revisión.
- **RN-12 Muestra de verificación:** población elegible = candidatos con vigente "Incluido" o "Excluido" de método distinto de "Manual". Tamaño entero entre 10 y 500 (valor por defecto: 50) y no mayor que la población. Selección aleatoria simple sin reemplazo; se registra la semilla para reproducirla. Un candidato puede estar en varias muestras.
- **RN-13 Verificación:** cada candidato de la muestra se resuelve con una Confirmación (cuenta como acierto) o una Corrección (cuenta como error). Acierto = confirmados / (confirmados + corregidos) × 100, con 1 decimal; se calcula sobre los revisados y se informa también cuántos faltan. Meta de referencia de la épica: ≥ 95 %.
- **RN-14 Permisos:** solo el rol Administrador ejecuta las acciones de esta historia.

### Interfaz

No requiere interfaz gráfica (nota de implementación del Dominio 12 del PRD). Comandos o interfaz administrativa mínima para: consultar la cola, corregir, confirmar, devolver a automática, generar muestra y consultar el resultado de la muestra. Los mensajes son los indicados en los escenarios.

### Sistemas Externos (Si aplica)

No aplica.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-010 (reglas de ítem), HU-011 (contratos y mixtos), HU-012 (sugerencias de IA).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La corrección manual requiere motivo y comentario para ser auditable → resuelto con lista cerrada de motivos y comentario obligatorio (RN-04, RN-05).
- El criterio de la épica de "revisión manual de 50 candidatos al azar ≥ 95 %" necesita un mecanismo → resuelto con la muestra de verificación (RN-12, RN-13).
- Una clasificación manual puede necesitar deshacerse → resuelto con "devolver a clasificación automática" (RN-08).
- La cola general de revisión humana y el log de auditoría global pertenecen a la operación del MVP → aquí solo la cola de clasificación y el historial propio de cada candidato.

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
