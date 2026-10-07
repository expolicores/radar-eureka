# Historia #029: Activar o desactivar la extracción con IA por configuración sin afectar las funciones determinísticas

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Operar y Medir la Extracción con IA  
**Prioridad:** Crítica  
**FRs relacionados:** FR-033

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** desactivar y reactivar la extracción con IA mediante una opción de configuración, sin redesplegar la aplicación,  
**Para** controlar el costo o detener la IA ante un problema de calidad o del proveedor, manteniendo operativas la ingesta, la exploración, la TVEC y la comparación sobre datos ya extraídos.

## Descripción

El principio del producto es que la base determinística funciona sin IA y la IA amplía la cobertura. NFR-EVO-003 exige que la desactivación sea una opción de configuración, sin redespliegue.

Esta HU define un interruptor "extracción con IA" (activa / inactiva). Cuando está inactiva, el sistema no inicia ninguna llamada a servicios de IA (extracción ni lectura multimodal); los procesos que necesitaban extracción quedan "pendiente de extracción (IA desactivada)" y se procesan cuando se reactiva, sin perderse. Todo lo demás sigue funcionando: listado, priorización, descarga, descompresión, lectura de formatos, detección de páginas, base tributaria, precio derivado, suficiencia, aritmética, umbral, revisión humana y el resto del producto sobre datos ya extraídos. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Desactivar la extracción con IA

- **Dado** que la extracción con IA está activa
- **Cuando** el Administrador la cambia a inactiva con el comentario "Pausa por revisión de calidad"
- **Entonces** el cambio aplica sin redespliegue a partir de la siguiente extracción que vaya a iniciar, y se registran usuario, fecha y hora, valor anterior, valor nuevo y comentario

### Escenario 2: Procesos que requieren extracción con la IA inactiva

- **Dado** que la extracción con IA está inactiva y el proceso `CO1.BDOS.1234567` llega a "documentos preparados"
- **Cuando** se ejecuta la extracción programada
- **Entonces** no se realiza ninguna llamada al servicio de IA y el proceso queda "pendiente de extracción (IA desactivada)"

### Escenario 3: Extracción en curso al desactivar

- **Dado** que una extracción del proceso `CO1.BDOS.5555555` está en curso cuando el Administrador desactiva la IA
- **Cuando** se completa el cambio
- **Entonces** la extracción en curso termina normalmente y registra su resultado, y no se inicia ninguna otra

### Escenario 4: Funciones determinísticas siguen operando

- **Dado** que la extracción con IA está inactiva
- **Cuando** se ejecutan la ingesta, el listado, la priorización, la descarga, la descompresión, la lectura de formatos y la detección de páginas, y el Administrador valida y corrige ítems ya extraídos
- **Entonces** todas esas operaciones funcionan igual que con la IA activa, y los ítems ya extraídos y aceptados siguen disponibles para comparación

### Escenario 5: Reactivación

- **Dado** que hay 12 procesos "pendiente de extracción (IA desactivada)"
- **Cuando** el Administrador reactiva la extracción con IA
- **Entonces** en la siguiente ejecución programada los 12 procesos se extraen, en orden de antigüedad de su llegada a "documentos preparados", sin perder ninguno

### Escenario 6: Reextracción solicitada con la IA inactiva

- **Dado** que la extracción con IA está inactiva
- **Cuando** el Administrador solicita la reextracción de un proceso
- **Entonces** la solicitud se registra y el proceso queda "pendiente de extracción (IA desactivada)", con el mensaje "La extracción con IA está desactivada; la solicitud se ejecutará cuando se reactive"

### Escenario 7: Consulta del estado

- **Dado** que el Administrador consulta el estado de la extracción con IA
- **Cuando** obtiene la información
- **Entonces** ve el estado actual, la fecha y el usuario del último cambio, el comentario y el número de procesos "pendiente de extracción (IA desactivada)"

### Escenario 8: Valor de configuración inválido

- **Dado** que el Administrador intenta asignar el valor "parcial" al interruptor
- **Cuando** guarda la configuración
- **Entonces** el cambio se rechaza con "Valor no permitido: use 'activa' o 'inactiva'" y se conserva el valor anterior

### Escenario 9: Cambio sin efecto

- **Dado** que la extracción con IA ya está inactiva
- **Cuando** el Administrador la cambia de nuevo a inactiva
- **Entonces** el sistema responde "La extracción con IA ya está inactiva" y no registra un cambio

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO).
- **Permisos requeridos:** Solo el Administrador cambia o consulta el interruptor. El Analista no accede.
- **Valor de negocio:** Cumple FR-033 y NFR-EVO-003: la IA se puede apagar sin afectar el producto, controlando costo y riesgo.

### Reglas de Negocio

- **RN-01 — Interruptor:** parámetro "extracción con IA" con valores "activa" o "inactiva". Configuración inicial: "activa". Otro valor: "Valor no permitido: use 'activa' o 'inactiva'".
- **RN-02 — Sin redespliegue:** el cambio se aplica leyendo la configuración vigente al inicio de cada extracción; no requiere reiniciar ni redesplegar.
- **RN-03 — Alcance de la desactivación:** con el interruptor inactivo no se inicia ninguna llamada a servicios de IA de esta épica (extracción de ítems y lectura de OCR o multimodal con IA). Las llamadas ya en curso terminan y registran su resultado.
- **RN-04 — Procesos pendientes:** los procesos que requieren extracción (nuevos o con reextracción solicitada) quedan "pendiente de extracción (IA desactivada)", conservando la fecha en que llegaron a "documentos preparados" o en que se solicitó la reextracción. No se pierden ni se descartan.
- **RN-05 — Funciones no afectadas:** con la IA inactiva siguen operando: ingesta de SECOP II y TVEC, listado, priorización, descarga, evaluación de vacíos y duplicados, descompresión, lectura de formatos, detección de páginas que requieren lectura visual y generación de imágenes, determinación de base tributaria, precio derivado, suficiencia, comprobación aritmética, umbral de aceptación, revisión humana, conservación de evidencia y todo uso de datos ya extraídos (exploración, comparación, señales).
- **RN-06 — Reactivación:** al reactivar, la siguiente ejecución programada procesa los pendientes por orden de antigüedad (fecha de RN-04, la más antigua primero).
- **RN-07 — Reextracción con IA inactiva:** se registra la solicitud, el proceso queda pendiente y se responde "La extracción con IA está desactivada; la solicitud se ejecutará cuando se reactive".
- **RN-08 — Registro:** cada cambio efectivo guarda usuario, fecha y hora, valor anterior, valor nuevo y comentario opcional (máximo 500 caracteres). Un cambio al mismo valor responde "La extracción con IA ya está {estado}" y no se registra.
- **RN-09 — Consulta:** estado actual, último cambio (usuario, fecha, comentario) y número de procesos pendientes por IA desactivada.

### Interfaz

Sin interfaz gráfica obligatoria: el interruptor se cambia por configuración (tabla, variable de configuración leída en ejecución, comando) o vista administrativa mínima. Los mensajes de RN-01, RN-07 y RN-08 se devuelven en la respuesta de la operación.

### Sistemas Externos (Si aplica)

- **Componente de extracción con IA** (no recibe solicitudes mientras el interruptor está inactivo).

---

## Contexto y Referencias

**Épica origen:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)

**Exclusiones de la Épica:**
- NO incluye el agente de investigación (siguiente incremento agéntico, post-MVP).
- NO incluye la extracción y comparación de precios de múltiples oferentes (FR-026, pospuesta por D4).
- NO incluye la extracción de cláusulas contractuales, garantías ni condiciones de entrega.
- NO incluye procesar todos los documentos de cada proceso, solo los priorizados.
- NO incluye la extracción de categorías distintas a televisores.
- NO incluye la base de conocimiento RAG sobre los documentos.

**Historias relacionadas:** HU-022 (extracción), HU-014 a HU-021 y HU-023 a HU-028 (funciones que siguen operando sin IA).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- La desactivación también detiene la lectura de OCR o multimodal con IA; la preparación determinística sigue → RN-03, RN-05.
- Las extracciones en curso terminan; solo se impide iniciar nuevas → RN-03.
- Los pendientes se procesan por orden de antigüedad al reactivar → RN-06.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-002 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
