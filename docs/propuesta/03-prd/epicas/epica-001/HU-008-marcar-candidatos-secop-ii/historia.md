# Historia #008: Marcar candidatos a televisor en contratos SECOP II

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)  
**Feature:** Identificar Candidatos a Televisor  
**Prioridad:** Crítica  
**FRs relacionados:** FR-011

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema marque como candidato todo contrato SECOP II cuyo UNSPSC principal sea `52161505` y/o cuyo objeto o descripción contenga los términos definidos, registrando por qué fue marcado,  
**Para** tener un conjunto de candidatos explícito y explicable sobre el cual aplicar la clasificación estricta, sin perder contratos de televisores que no usan el código UNSPSC.

## Descripción

Las cargas de SECOP II traen contratos con un prefiltro amplio y los dejan con candidatura "Pendiente de marcación". Esta historia aplica la **regla precisa de candidatura**: UNSPSC principal `52161505` **y/o** coincidencia de términos como palabras completas (no como fragmentos: "TV" no coincide dentro de "TVEC") en el objeto del contrato o la descripción del proceso.

Cada contrato queda "Candidato" (con el motivo: UNSPSC, texto o ambos, y los términos encontrados) o "No candidato". Los candidatos quedan "Pendiente de clasificación" para la clasificación estricta. Ser candidato **no** significa que el contrato compre televisores: D4 mostró que el 28 % de los candidatos no lo son.

---

## Criterios de Aceptación

### Escenario 1: Candidato por UNSPSC y texto

- **Dado** que un contrato pendiente tiene `unspsc_principal = V1.52161505` y objeto "Adquisición de televisores 65 pulgadas"
- **Cuando** se ejecuta la marcación
- **Entonces** queda `candidatura = Candidato`, `motivo_candidatura = UNSPSC y texto`, `terminos_encontrados = [televisor]` en el campo "objeto", `estado_clasificacion = Pendiente de clasificación` y la fecha y versión de la marcación

### Escenario 2: Candidato solo por texto

- **Dado** que un contrato tiene UNSPSC `V1.43211500` y objeto "Compra de 52 equipos de cómputo y 1 smart tv"
- **Cuando** se ejecuta la marcación
- **Entonces** queda "Candidato" con motivo "Texto" y términos encontrados "smart tv" y "tv"

### Escenario 3: Candidato solo por UNSPSC

- **Dado** que un contrato tiene UNSPSC `V1.52161505` y objeto "Mantenimiento preventivo de equipos audiovisuales" sin ningún término
- **Cuando** se ejecuta la marcación
- **Entonces** queda "Candidato" con motivo "UNSPSC" y sin términos encontrados

### Escenario 4: Coincidencia parcial que no es término

- **Dado** que un contrato sin UNSPSC `52161505` tiene objeto "Compra en la TVEC de suministros de aseo" o "Servicio de televisión por cable"
- **Cuando** se ejecuta la marcación
- **Entonces** queda "No candidato" con el motivo "No cumple UNSPSC ni términos", porque "tvec" y "television" no son términos configurados

### Escenario 5: Contrato que deja de ser candidato

- **Dado** que un contrato era "Candidato" y una actualización de la fuente eliminó el UNSPSC y los términos
- **Cuando** se ejecuta la marcación
- **Entonces** pasa a "No candidato", se registra el evento "Dejó de ser candidato" con la fecha y la candidatura anterior, y su historial de clasificación se conserva sin cambios

### Escenario 6: Candidato con texto modificado y clasificación existente

- **Dado** que un contrato "Candidato" ya clasificado por regla o IA vuelve a "Pendiente de marcación" por un cambio de objeto y sigue siendo candidato
- **Cuando** se ejecuta la marcación
- **Entonces** su `estado_clasificacion` vuelve a "Pendiente de clasificación"; si su clasificación vigente es manual, la clasificación se mantiene y se marca `texto_cambio_tras_clasificacion_manual = sí`

### Escenario 7: Ejecución automática y manual

- **Dado** que terminó una carga de SECOP II (exitosa o fallida) que dejó contratos "Pendiente de marcación"
- **Cuando** termina la carga
- **Entonces** la marcación se ejecuta automáticamente sobre los pendientes; y el Administrador también puede ejecutarla por comando

### Escenario 8: Cambio de términos y remarcación total

- **Dado** que el Administrador cambia la lista de términos
- **Cuando** guarda una lista válida y ejecuta el comando de remarcación total
- **Entonces** se crea una nueva versión de términos y todos los contratos SECOP II (no solo los pendientes) se marcan de nuevo con esa versión

### Escenario 9: Lista de términos inválida

- **Dado** que el Administrador intenta guardar una lista de términos vacía, con un término de menos de 2 o más de 50 caracteres tras normalizar
- **Cuando** guarda la configuración
- **Entonces** se rechaza con "La lista de términos debe tener al menos un término de 2 a 50 caracteres" y se conserva la versión anterior

### Escenario 10: Sin contratos pendientes

- **Dado** que no hay contratos "Pendiente de marcación"
- **Cuando** se ejecuta la marcación
- **Entonces** termina sin cambios y registra "No hay contratos SECOP II pendientes de marcación."

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador del MVP (PO); la marcación automática la ejecuta el sistema.
- **Permisos requeridos:** rol Administrador para ejecución manual y cambio de términos.
- **Valor de negocio:** define el conjunto de candidatos que es el punto de partida del universo y del denominador de los indicadores de cobertura.

### Reglas de Negocio

- **RN-01 Normalización de texto:** minúsculas; eliminación de tildes y diéresis (á→a, ñ se conserva como n); todo carácter que no sea letra o dígito se reemplaza por espacio; espacios múltiples colapsados; recorte de extremos. Ejemplo: "GSF01-SMART TV LG 43\"" → "gsf01 smart tv lg 43".
- **RN-02 Coincidencia de término:** un término normalizado (una o varias palabras) coincide si aparece en el texto normalizado como secuencia de palabras completas; la última palabra del término admite además los sufijos "s" o "es". Ej.: "televisor" coincide con "televisor" y "televisores"; "tv" coincide con "tv" y "tvs", no con "tvec"; "smart tv" coincide con "smart tv" y "smart tvs".
- **RN-03 Términos:** lista configurable y versionada (valor inicial: "televisor", "smart tv", "tv"). Cada término tiene de 2 a 50 caracteres tras normalizar; la lista no puede quedar vacía; términos repetidos tras normalizar se guardan una vez.
- **RN-04 Campos evaluados:** `objeto` (objeto del contrato) y `descripcion_proceso`. Un campo nulo se trata como texto vacío.
- **RN-05 UNSPSC:** se toma `unspsc_principal`, se elimina el prefijo `V1.` si existe y espacios; coincide si el resultado es exactamente `52161505`. Valor nulo o con otro formato → no coincide.
- **RN-06 Resultado:** "Candidato" si coincide UNSPSC o algún término; `motivo_candidatura` = "UNSPSC", "Texto" o "UNSPSC y texto"; `terminos_encontrados` = lista de términos con el campo donde se encontraron. Si no coincide nada → "No candidato" con motivo "No cumple UNSPSC ni términos". Se registran `fecha_marcacion` y `version_terminos`.
- **RN-07 Efecto sobre la clasificación:** un contrato que queda "Candidato" pasa a `estado_clasificacion = Pendiente de clasificación`, salvo que su clasificación vigente sea manual (Escenario 6). Un "No candidato" no entra a clasificación.
- **RN-08 Pérdida de candidatura:** regla del Escenario 5; los contratos nunca se eliminan.
- **RN-09 Disparo:** automático al terminar cada carga de SECOP II sobre los contratos "Pendiente de marcación"; manual por comando (pendientes o remarcación total). Remarcación total solo por comando.
- **RN-10 Idempotencia:** marcar dos veces el mismo contrato sin cambios de texto ni de términos produce el mismo resultado y no genera eventos nuevos.
- **RN-11 Resumen:** "Marcación SECOP II: {n} evaluados. Candidatos: {n} (UNSPSC: {n}; Texto: {n}; Ambos: {n}). No candidatos: {n}. Dejaron de ser candidatos: {n}."

### Interfaz

No requiere interfaz gráfica. Comandos "marcar candidatos SECOP II" (pendientes) y "remarcar todos los candidatos SECOP II"; configuración de términos por archivo o comando. Resumen en consola o log (RN-11).

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre los contratos ya ingeridos desde datos.gov.co.

---

## Contexto y Referencias

**Épica origen:** [Universo de Compras Públicas de Televisores](../../../epicas.md#épica-001-universo-de-compras-públicas-de-televisores)

**Exclusiones de la Épica:**
- NO incluye SECOP I (Adenda 1).
- NO incluye categorías distintas a televisores.
- NO incluye el dataset de Procesos (`p6dx-8zbt`) como unidad base.
- NO incluye adiciones, modificaciones ni ejecución del contrato (ciclo de vida).
- NO incluye scraping del portal SECOP.

**Historias relacionadas:** HU-001, HU-002 (cargas SECOP II), HU-009 (candidatos TVEC), HU-011 (clasificación de contratos SECOP II).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- "TV" como subcadena genera falsos positivos (ej. "TVEC") → resuelto con coincidencia de palabras completas (RN-02).
- "Televisores" debe coincidir con "televisor" → resuelto con sufijos de plural (RN-02).
- "Televisión" no es un término definido y suele referirse a servicios → no se agrega; es configurable (RN-03).
- Qué pasa con un contrato clasificado que deja de ser candidato → resuelto en RN-08 sin eliminar historial.

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
