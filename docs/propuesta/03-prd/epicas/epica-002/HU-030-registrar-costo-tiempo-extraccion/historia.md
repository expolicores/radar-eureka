# Historia #030: Registrar el costo estimado y el tiempo de procesamiento de la extracción por documento

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Operar y Medir la Extracción con IA  
**Prioridad:** Alta  
**FRs relacionados:** FR-034

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema registre, por cada documento procesado, el costo estimado de la extracción con IA y el tiempo de procesamiento, y me permita consultarlos por documento, por proceso y acumulados por mes,  
**Para** conocer los drivers de costo de la IA, verificar el objetivo de tiempo por documento y decidir el modelo con evidencia.

## Descripción

El Brief pide identificar los principales drivers de costo, y NFR-OBS-001 exige el costo estimado por documento y el acumulado mensual del componente de IA. D4 estimó ≈ USD 0,05 por contrato (sin margen) y recomendó medir el costo real en producción; NFR-PER-004 fija un objetivo inicial de ≤ 5 minutos (p95) por documento.

Esta HU registra cada solicitud al servicio de IA (modelo, tokens, imágenes, intentos, duración, resultado), calcula su costo con una tabla de tarifas configurable y lo reparte entre los documentos enviados en esa solicitud, proporcionalmente a su tamaño de entrada. También mide el tiempo de preparación determinística de cada documento. Se distribuye con prioridad **Alta** (no Crítica, como el resto de la épica) porque no bloquea el flujo documentos → datos comparables: es una capacidad de medición. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Registro de una solicitud exitosa

- **Dado** que la extracción del proceso `CO1.BDOS.1234567` envió 3 documentos en una solicitud al modelo "modelo-A", con tarifa vigente USD 2 por millón de tokens de entrada y USD 10 por millón de salida, y el servicio informó 14.800 tokens de entrada y 2.000 de salida, con duración de 38 segundos
- **Cuando** termina la solicitud
- **Entonces** se registra la solicitud con modelo, tokens, número de imágenes y de páginas de texto enviadas, inicio, fin, duración 38 s, 1 intento, resultado "éxito" y costo 0,049600 USD (14.800 × 2 / 1.000.000 + 2.000 × 10 / 1.000.000)

### Escenario 2: Reparto del costo y del tiempo por documento

- **Dado** que en la solicitud del Escenario 1 el tamaño de entrada estimado de los documentos fue: A = 6.000, B = 3.000 (texto) y C = 2 imágenes (2 × 1.500 = 3.000), total 12.000
- **Cuando** se registra el costo por documento
- **Entonces** A recibe el 50 % (0,024800 USD y 19,0 s), B el 25 % (0,012400 USD y 9,5 s) y C el 25 % (0,012400 USD y 9,5 s), cada uno marcado "repartido proporcionalmente"

### Escenario 3: Tiempo de preparación determinística por documento

- **Dado** que el documento A tardó 4,2 s en la lectura de formato y 1,8 s en la detección de páginas y generación de imágenes
- **Cuando** se consulta su registro
- **Entonces** muestra tiempo de preparación 6,0 s, tiempo de extracción con IA 19,0 s y tiempo total 25,0 s

### Escenario 4: Reintentos

- **Dado** que la solicitud falló una vez por tiempo de espera (300 s, sin tokens informados) y tuvo éxito en el segundo intento
- **Cuando** termina la solicitud
- **Entonces** se registran 2 intentos; la duración total incluye ambos intentos y las esperas; el costo del intento fallido se registra como 0 con la anotación "sin tokens informados por el servicio" y el total de la solicitud suma ambos intentos

### Escenario 5: Servicio que no informa tokens

- **Dado** que una solicitud exitosa no informa el número de tokens
- **Cuando** se calcula el costo
- **Entonces** se estima con el tamaño de entrada (caracteres de texto / 3,5 + imágenes × 1.500 tokens) y una salida de 2.000 tokens, y el costo queda marcado "estimado por tamaño"

### Escenario 6: Modelo sin tarifa configurada

- **Dado** que la solicitud usó "modelo-B" y no hay tarifa vigente para ese modelo en la fecha de la solicitud
- **Cuando** se calcula el costo
- **Entonces** el costo queda "no estimado" con el motivo "sin tarifa configurada para el modelo modelo-B"; nunca se registra como 0

### Escenario 7: Cambio de tarifa no altera registros anteriores

- **Dado** que la tarifa de "modelo-A" cambia el 2026-11-01
- **Cuando** se consultan solicitudes de octubre y de noviembre
- **Entonces** las de octubre conservan el costo calculado con la tarifa anterior y las de noviembre usan la nueva

### Escenario 8: Consulta por proceso y acumulado mensual

- **Dado** que en octubre de 2026 se procesaron 40 procesos y 280 documentos
- **Cuando** el Administrador consulta el resumen de octubre
- **Entonces** ve el costo total de IA del mes, el costo promedio y mediano por documento y por proceso, el número de documentos con costo "no estimado", la duración mediana y el percentil 95 de la duración total por documento, y el número de documentos por encima de 5 minutos

### Escenario 9: Mes sin extracciones

- **Dado** que en un mes la extracción con IA estuvo desactivada
- **Cuando** el Administrador consulta el resumen de ese mes
- **Entonces** ve costo 0,00 USD, 0 documentos y la anotación "sin extracciones en el periodo"

### Escenario 10: Tarifa inválida

- **Dado** que el Administrador intenta registrar una tarifa negativa o sin fecha de vigencia
- **Cuando** guarda la tarifa
- **Entonces** se rechaza con "La tarifa debe ser un número mayor o igual que 0 y tener fecha de inicio de vigencia"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO).
- **Permisos requeridos:** Solo el Administrador consulta costos y tiempos y configura tarifas. El Analista no accede.
- **Valor de negocio:** Hace visible el costo por documento (NFR-OBS-001) y el tiempo por documento (NFR-PER-004), insumos para elegir modelo por precisión y costo.

### Reglas de Negocio

- **RN-01 — Registro por solicitud:** por cada solicitud al servicio de IA: proceso, documentos incluidos, modelo, tokens de entrada y de salida informados por el servicio, número de imágenes y de páginas de texto enviadas, número de intentos, inicio y fin de cada intento, duración total (desde el primer envío hasta la última respuesta, incluidas las esperas entre intentos) en segundos con 1 decimal, resultado ("éxito" o "fallo" con motivo) y costo.
- **RN-02 — Costo de un intento:** `tokens de entrada × tarifa de entrada / 1.000.000 + tokens de salida × tarifa de salida / 1.000.000`, en USD, guardado con 6 decimales y mostrado con 4. El costo de la solicitud es la suma de sus intentos.
- **RN-03 — Tokens no informados:** en un intento exitoso sin tokens informados, se estiman: entrada = caracteres de texto enviados / 3,5 + imágenes × 1.500; salida = 2.000; el costo se marca "estimado por tamaño". En un intento fallido sin tokens informados, su costo es 0 con la anotación "sin tokens informados por el servicio". Los factores 3,5, 1.500 y 2.000 son configurables (configuración inicial tomada de D4).
- **RN-04 — Tarifas (configurables):** por modelo: tarifa de entrada y de salida (USD por millón de tokens, número ≥ 0 con hasta 4 decimales) y fecha de inicio de vigencia. Se usa la tarifa vigente en la fecha de inicio de la solicitud. Sin tarifa vigente: costo "no estimado" con el motivo "sin tarifa configurada para el modelo {modelo}"; nunca 0. Tarifa inválida: "La tarifa debe ser un número mayor o igual que 0 y tener fecha de inicio de vigencia". Los registros ya calculados no cambian al modificar tarifas.
- **RN-05 — Reparto por documento:** el costo y la duración de una solicitud se reparten entre sus documentos en proporción a su tamaño de entrada estimado: caracteres de texto del documento / 3,5 + imágenes del documento × 1.500. Cada parte se marca "repartido proporcionalmente". Si la solicitud contiene un solo documento, recibe el 100 %. Los redondeos se ajustan en el documento de mayor tamaño (en empate, el primero en el orden de prioridad) para que la suma coincida con el total.
- **RN-06 — Tiempo de preparación:** por documento se registra la duración de la lectura de formato y de la detección de páginas y generación de imágenes. Tiempo total por documento = preparación + parte de la extracción con IA.
- **RN-07 — Consultas:** a) por documento: costo, marcas, tiempos de preparación, de IA y total; b) por proceso: suma de sus documentos y de sus solicitudes; c) por mes (calendario, zona horaria de Colombia): costo total de IA, costo promedio y mediano por documento y por proceso, documentos con costo "no estimado", duración mediana y percentil 95 del tiempo total por documento, y número de documentos con tiempo total mayor que el objetivo configurable (configuración inicial: 300 segundos). Un mes sin solicitudes muestra 0,00 USD, 0 documentos y "sin extracciones en el periodo".
- **RN-08 — Nulos:** un documento sin extracción con IA (ej. no elegible o con IA desactivada) tiene costo de IA nulo y no cuenta en los promedios de costo; sí registra su tiempo de preparación si lo tuvo.
- **RN-09 — Conservación:** los registros de costo y tiempo no se eliminan durante el MVP.

### Interfaz

Sin interfaz gráfica obligatoria: consultas, reporte o vista administrativa mínima (NFR-OBS-001 admite UI, consulta o reporte). El mensaje de RN-04 se devuelve en la respuesta de la operación de configuración.

### Sistemas Externos (Si aplica)

- **Componente de extracción con IA:** informa (cuando lo hace) los tokens de entrada y salida de cada solicitud.

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

**Historias relacionadas:** HU-019, HU-020 (tiempos de preparación), HU-022 (solicitudes de extracción), HU-029 (IA desactivada).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Una solicitud de IA cubre varios documentos; el costo y el tiempo se reparten por tamaño de entrada estimado → RN-05.
- Factores de estimación iniciales tomados de D4 (3,5 caracteres por token, 1.500 tokens por imagen, 2.000 de salida) → RN-03.
- Costos en USD con tarifa vigente por modelo y fecha; sin tarifa el costo es "no estimado", nunca 0 → RN-04.
- Prioridad Alta (no Crítica) porque es medición y no bloquea el flujo principal.

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
