# Historia #082: Ver los motivos de información insuficiente del contrato en la ficha

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)  
**Feature:** Seguimiento del Procesamiento y Frescura de Datos  
**Prioridad:** Crítica  
**FRs relacionados:** FR-075

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** ver en la ficha por qué un contrato o alguno de sus ítems no tiene información suficiente para compararse, distinguiendo si el límite viene de la fuente o del procesamiento,  
**Para** entender qué falta, no interpretar la ausencia de señal como ausencia de riesgo y saber si vale la pena revisar el documento por mi cuenta.

## Descripción

Esta HU construye, dentro de la ficha del contrato (HU-076), la sección **"Motivos de información insuficiente"**. Reúne los motivos registrados por la plataforma a nivel de contrato (por ejemplo, proceso sin documentos publicados) y a nivel de ítem (por ejemplo, no se logró extraer cantidad y precio unitario), y los agrupa en dos categorías:

- **Limitación de la fuente:** la fuente no publica el dato (por ejemplo, el documento solo trae valores globales o el formato está en blanco).
- **Limitación del procesamiento:** el dato podría estar publicado pero la plataforma no lo obtuvo o no lo extrajo (por ejemplo, error de lectura o extracción pendiente de revisión).

Esta separación permite distinguir *la fuente no publica el dato* de *el producto no extrae un dato que sí estaba publicado*. La HU solo presenta los motivos ya registrados por otros procesos; no los calcula.

---

## Criterios de Aceptación

### Escenario 1: Contrato con ítems sin información suficiente (happy path)

- **Dado** que uno o más ítems del contrato están marcados como "información insuficiente" con motivo registrado
- **Cuando** el Analista abre la sección "Motivos de información insuficiente"
- **Entonces** ve los motivos agrupados en "Limitación de la fuente" y "Limitación del procesamiento", cada uno con el texto del catálogo de RN-02, el ítem afectado (o "Todo el contrato") y, cuando exista, el documento relacionado

### Escenario 2: Motivo a nivel de contrato

- **Dado** que el proceso no tiene documentos publicados
- **Cuando** se muestra la sección
- **Entonces** aparece en "Limitación de la fuente" el motivo "La fuente no ha publicado documentos para este proceso." con alcance "Todo el contrato"

### Escenario 3: Motivo con documento relacionado

- **Dado** que un motivo se registró sobre un documento concreto (ej. formato en blanco)
- **Cuando** se muestra el motivo
- **Entonces** incluye "Documento: {nombre}" con la acción "Abrir en SECOP II" cuando el documento tenga URL oficial

### Escenario 4: Motivo desconocido para el catálogo

- **Dado** que el motivo registrado no corresponde a ningún código del catálogo de RN-02
- **Cuando** se muestra el motivo
- **Entonces** aparece en "Limitación del procesamiento" con el texto "Motivo registrado: {texto original}"

### Escenario 5: Comparación incompleta por base tributaria

- **Dado** que la comparación de un ítem quedó incompleta porque la base tributaria es indeterminada
- **Cuando** se muestra la sección
- **Entonces** aparece en "Limitación de la fuente" el motivo "No se pudo determinar si el precio incluye IVA; la comparación se marca como incompleta."

### Escenario 6: Sin comparables suficientes

- **Dado** que un ítem tiene precio pero no tiene observaciones comparables en la ventana máxima del Benchmark 1
- **Cuando** se muestra la sección
- **Entonces** aparece en "Limitación de la fuente" el motivo "No hay compras públicas comparables en la ventana de comparación." para ese ítem

### Escenario 7: Contrato sin motivos

- **Dado** que el contrato no tiene ningún motivo de información insuficiente registrado
- **Cuando** el Analista abre la sección
- **Entonces** ve "No hay motivos de información insuficiente registrados para este contrato."

### Escenario 8: Contrato aún en procesamiento

- **Dado** que el contrato no ha terminado de procesarse y todavía no tiene motivos
- **Cuando** el Analista abre la sección
- **Entonces** ve "El contrato aún está en procesamiento; los motivos de información insuficiente, si los hay, aparecerán al terminar."

### Escenario 9: Acceso desde el estado de procesamiento o desde un ítem

- **Dado** que el Analista activa "Ver motivos" en el estado de procesamiento o en la tarjeta de un ítem
- **Cuando** se navega a la sección
- **Entonces** la vista se desplaza a la sección y, si viene de un ítem, resalta los motivos de ese ítem

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista que investiga contratación pública; el Administrador también puede consultar la sección.
- **Permisos requeridos:** Sesión iniciada con rol Analista o Administrador.
- **Valor de negocio:** Hace explícito el límite de la información (en SECOP II, alrededor de la mitad de los contratos en categoría no publica precio unitario) y evita conclusiones equivocadas por ausencia de datos.

### Reglas de Negocio

- **RN-01 Origen de los motivos:** motivos registrados por la plataforma a nivel de contrato (obtención de documentos) y a nivel de ítem (extracción marcada como "información insuficiente", base tributaria indeterminada, falta de comparables). Cada motivo tiene un código, un alcance (contrato o ítem) y, opcionalmente, un documento relacionado.
- **RN-02 Catálogo de presentación:**

  | Código | Texto mostrado | Categoría |
  |---|---|---|
  | `sin_documentos` | La fuente no ha publicado documentos para este proceso. | Limitación de la fuente |
  | `documento_en_blanco` | Los documentos relevantes publicados están en blanco o sin diligenciar. | Limitación de la fuente |
  | `solo_valor_global` | Los documentos publicados solo presentan valores globales; no hay precio unitario ni datos para derivarlo. | Limitación de la fuente |
  | `oferta_no_publicada` | La oferta adjudicada no está publicada en los documentos del proceso. | Limitación de la fuente |
  | `sin_cantidad` | Los documentos no indican la cantidad de televisores. | Limitación de la fuente |
  | `precio_no_derivable` | El precio unitario no puede derivarse: el valor incluye otros bienes o servicios, o los televisores no son homogéneos. | Limitación de la fuente |
  | `iva_indeterminado` | No se pudo determinar si el precio incluye IVA; la comparación se marca como incompleta. | Limitación de la fuente |
  | `sin_comparables` | No hay compras públicas comparables en la ventana de comparación. | Limitación de la fuente |
  | `error_descarga` | No se pudieron obtener los documentos priorizados. | Limitación del procesamiento |
  | `error_lectura` | No se pudo leer el documento (formato no soportado o archivo dañado). | Limitación del procesamiento |
  | `extraccion_pendiente_revision` | Los datos extraídos están pendientes de revisión humana. | Limitación del procesamiento |
  | `extraccion_no_encontrada` | No se lograron extraer la cantidad y el precio unitario de los documentos procesados. | Limitación del procesamiento |

- **RN-03 Motivos desconocidos:** un código no incluido en el catálogo se muestra como "Motivo registrado: {texto original}" en "Limitación del procesamiento"; si no hay texto original, "Motivo registrado sin descripción".
- **RN-04 Agrupación y orden:** primero "Limitación de la fuente" y luego "Limitación del procesamiento"; dentro de cada grupo, primero los motivos de "Todo el contrato" y luego por orden del ítem. Un mismo motivo para varios ítems se muestra una vez con la lista de ítems afectados.
- **RN-05 Alcance:** "Todo el contrato" o el nombre del ítem (producto normalizado o descripción original truncada a 80 caracteres).
- **RN-06 Documento relacionado:** se muestra el nombre y "Abrir en SECOP II" (pestaña nueva) si tiene URL oficial; sin URL, solo el nombre.
- **RN-07 Cobertura:** la sección existe en el 100 % de las fichas de registros visibles; si no hay motivos, muestra el estado del Escenario 7 u 8 según el estado de procesamiento (en procesamiento = alguna etapa "En curso o pendiente").
- **RN-08 Lenguaje:** los motivos describen límites de información; nunca sugieren irregularidad ni usan "sobreprecio", "corrupción", "fraude" o "hallazgo fiscal".
- **RN-09 Rendimiento y accesibilidad (valores iniciales de diseño):** dentro del objetivo de la ficha de ≤ 3 segundos (p95) con 20 usuarios concurrentes; WCAG 2.1 AA (grupos con títulos, lectura ordenada, foco al llegar desde "Ver motivos"); en móvil desde 360 px cada motivo es una tarjeta.

### Interfaz

- Sección "Motivos de información insuficiente" con dos grupos titulados "Limitación de la fuente ({n})" y "Limitación del procesamiento ({n})".
- Por motivo: texto, alcance, documento relacionado y acción "Abrir en SECOP II" cuando aplique.
- Mensajes de estado de los Escenarios 7 y 8.
- Destinos de los enlaces "Ver motivos" del estado de procesamiento y de las tarjetas de ítems.

### Sistemas Externos (Si aplica)

No consulta sistemas externos. Usa los motivos registrados por los procesos de obtención de documentos, extracción y comparación, y la URL oficial de los documentos (SECOP II) para el enlace de salida.

---

## Contexto y Referencias

**Épica origen:** [Exploración y Ficha del Contrato](../../../epicas.md#épica-006-exploración-y-ficha-del-contrato)

**Exclusiones de la Épica:**
- NO incluye fichas de entidad ni de proveedor (candidatas, ÉPICA-009).
- NO incluye dashboards nacionales ni de otras categorías.
- NO incluye exploración pública anónima.
- NO incluye la consulta conversacional (chatbot).

**Historias relacionadas:** HU-076 (estructura de la ficha), HU-077 (ítems con información insuficiente), HU-081 (estado de procesamiento)

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Resuelto (RN-02, RN-03):** catálogo de motivos con texto y categoría (fuente / procesamiento) y tratamiento explícito de motivos no catalogados.
- **Resuelto (RN-04):** agrupación en "Limitación de la fuente" y "Limitación del procesamiento", alineada con la separación entre disponibilidad en la fuente y cobertura de extracción.

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
