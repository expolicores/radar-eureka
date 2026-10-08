# Historia de Usuario

**Como** Analista,
**Quiero** abrir una señal y ver contra qué se comparó (Benchmark 1 con su distribución, Benchmark 2 con sus observaciones), por qué tiene la confianza que tiene, y la ficha completa de la compra con sus ítems,
**Para** decidir con evidencia si la compra merece una revisión más profunda, sin tener que creerle al sistema

## Descripción

Sexto *vertical slice* del MVP Beta: el corazón de la demo («revisar comparación → revisar evidencia»). Expone el detalle reproducible de una señal (FR-065) y amplía la ficha de la compra con el resultado vigente de cada ítem. La pantalla del detalle sigue el mockup: encabezado con insignias, aviso no acusatorio, Benchmark 1 con estadísticos y **gráfico de distribución** (con alternativa en tabla), Benchmark 2 con observaciones y método, desviación, confianza con penalizaciones y evidencia de origen.

HUs del backlog tomadas como referencia: HU-063 (detalle de señal con su comparación), HU-064 (navegar de la señal al contrato y a cada observación), HU-078/079 (benchmarks y señales en la ficha), HU-062 (evidencia reproducible), FR-065/FR-066/FR-067.

**No incluye:** visor de documentos ni extracción (diferidos: la sección de evidencia documental lo dice explícitamente), calificación, reporte de error, guardado en casos (slice 7).

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal (detalle de la señal)

- **Dado** una señal vigente
- **Cuando** el Analista la abre desde la lista
- **Entonces** ve el ítem y la cantidad, la compra (con enlace a su ficha), la entidad, la modalidad y la fecha; insignias «⚑ Merece revisión», confianza, tipo de emparejamiento y base de IVA; el aviso «Esta señal no constituye una conclusión ni una acusación…»; el Benchmark 1 con observaciones (y cuántas de SECOP II y TVEC), Q1, mediana, Q3, umbral, regla usada y ventana, y la distribución de precios con el precio analizado destacado; el Benchmark 2 con su estado, cada observación (tienda, producto, precio efectivo, fecha, método «Simulado») y la desviación correspondiente; la desviación frente a la mediana; y la confianza con cada penalización y la versión de la configuración

### Escenario 2: Validaciones

- **Dado** el gráfico de distribución
- **Cuando** el Analista pulsa «Ver como tabla»
- **Entonces** ve la tabla de comparables (fuente, compra, entidad, fecha, emparejamiento, precio), y cada comparable enlaza a la ficha de su compra

### Escenario 3: Casos Extremos

- **Dado** un código de señal inexistente o que ya no está vigente
- **Cuando** se abre el detalle
- **Entonces** la API responde **404** («Señal no encontrada») y la pantalla lo dice con un enlace de vuelta a la lista; y si el Benchmark 2 no tiene observaciones, se muestra «no disponible / evidencia insuficiente» sin ocultar el Benchmark 1

### Escenario 4: Ficha de la compra

- **Dado** una compra
- **Cuando** el Analista abre su ficha (desde Explorar, desde una señal o desde un comparable)
- **Entonces** ve los datos clave (entidad, proveedor y NIT —o «documento no visible»—, objeto, modalidad, valor con la nota «dato de referencia; no se usa como precio unitario», fecha, ubicación, proceso), los ítems con su clasificación, cantidad, precio unitario, estado del precio, base de IVA y **resultado vigente** (con enlace a la señal si la hay), y la fecha de corte

### Escenario 5: Evidencia de origen

- **Dado** que la extracción documental no está activa en el MVP Beta
- **Cuando** el Analista busca la evidencia documental de la señal
- **Entonces** el detalle lo indica explícitamente («Los documentos del proceso se incorporan con la extracción documental; esta señal usa el precio publicado en datos abiertos (simulados)»), sin documentos ni hashes inventados

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista.
- **Permisos requeridos:** ninguno en el MVP Beta.
- **Valor de negocio:** sin detalle verificable, una señal no se puede usar.

### Reglas de Negocio

- Solo el resultado **vigente** de cada ítem; el detalle muestra la versión de la configuración (`analitica-v1`).
- Lenguaje no acusatorio y advertencia visible (FR-064, FR-067).
- El Benchmark 2 con evidencia limitada no se presenta como «precio de mercado» (FR-059).
- Observaciones de mercado marcadas como simuladas por su método.

### Interfaz

- API: `GET /api/v1/signals/{code}`; `GET /api/v1/purchases/{id}` incluye el resultado por ítem.
- Pantallas: `/senales/:code` y `/compras/:id`.
- Gráfico: franja de puntos (SECOP II círculo, TVEC rombo, compra analizada destacada), caja Q1–Q3, líneas de mediana y umbral, con descripción accesible y alternativa en tabla.

### Sistemas Externos

Ninguno (documentos diferidos).

### Disparadores

- El Analista abre una señal, una ficha o alterna gráfico/tabla.

### Entidades del Dominio

- Señal que merece revisión
- Comparación de ítem
- Compra
- Ítem de compra
- Observación de mercado

### Alcance y Continuidad

El slice 7 agrega «Guardar en caso» desde el detalle y la ficha.

### Preview de Interfaz

Mockup, secciones «Detalle de señal» y «Ficha del contrato».

---

## Contexto y Referencias

**Arquitectura:** PRD FR-059, FR-062, FR-065…FR-067; mockup.
**Historias relacionadas:** #3, #5, #6.

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
