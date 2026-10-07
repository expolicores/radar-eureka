# Historia #065: Garantizar lenguaje no acusatorio en todos los textos generados por el sistema

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Presentación de Evidencia Trazable  
**Prioridad:** Crítica  
**FRs relacionados:** FR-064

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador (PO) responsable del producto,  
**Quiero** que ningún texto generado por el sistema denomine una señal, ni etiquete a un contrato, entidad, persona o empresa, con términos acusatorios, y que esto se verifique automáticamente con una lista configurable de términos prohibidos,  
**Para** cumplir el principio "mostrar hechos, no acusar" y reducir el riesgo legal y reputacional por proveedores o entidades nombrados en las señales.

## Descripción

Las desviaciones de precio se denominan siempre **"señal que merece revisión"**. Esta HU establece:
1. Una **lista configurable de términos prohibidos** (configuración inicial: los cuatro términos del PRD y sus variantes).
2. Una **verificación automática en las pruebas** que recorre todos los textos fijos y plantillas de la interfaz y de las señales, y falla si encuentra un término prohibido (NFR-CUM-007: 0 textos generados con esos términos).
3. Una **verificación en ejecución** de los textos que el sistema compone para cada señal (denominación, regla, motivos, advertencia), que impide publicar un texto con un término prohibido.

No aplica a textos escritos por usuarios (comentarios, notas, reportes) ni a datos públicos mostrados literalmente tal como los publica la fuente (por ejemplo, el objeto de un contrato), siempre que el sistema no los use como etiqueta o calificación propia.

---

## Criterios de Aceptación

### Escenario 1: Verificación de textos fijos en las pruebas

- **Dado** que el catálogo de textos de la interfaz y de las señales no contiene términos prohibidos
- **Cuando** se ejecuta la verificación automática de lenguaje
- **Entonces** la verificación pasa e informa "0 términos prohibidos encontrados en {n} textos"

### Escenario 2: Detección de un término prohibido en un texto fijo

- **Dado** que un desarrollador agrega el texto "Posible sobreprecio detectado"
- **Cuando** se ejecuta la verificación automática
- **Entonces** la verificación falla e informa el texto, su ubicación y el término encontrado ("sobreprecio")

### Escenario 3: Variantes de mayúsculas, tildes y plural

- **Dado** textos con "SOBREPRECIOS", "Corrupcion" (sin tilde), "fraudulenta" y "Hallazgos Fiscales"
- **Cuando** se ejecuta la verificación
- **Entonces** los cuatro se detectan como términos prohibidos

### Escenario 4: Sin falsos positivos por coincidencia parcial

- **Dado** los textos "Precio sobre la referencia", "Filtro antifraude de la fuente" y "Referencia fraccionada"
- **Cuando** se ejecuta la verificación
- **Entonces** no se detecta ningún término, porque la búsqueda es por palabra o frase completa

### Escenario 5: Verificación en ejecución de los textos de una señal

- **Dado** que al componer el texto de una señal (regla o motivo) el resultado contiene un término prohibido
- **Cuando** el sistema va a guardar la versión de la señal
- **Entonces** reemplaza ese texto por "Texto no disponible", mantiene la denominación "Señal que merece revisión", registra el error en el log con el identificador de la señal, el campo y el término, y la señal se publica con el resto de su evidencia

### Escenario 6: Textos de usuario y datos de la fuente

- **Dado** que el objeto de un contrato publicado en SECOP II contiene la palabra "fraude" (ej. "Software de prevención de fraude") y un comentario de un Analista contiene "posible sobreprecio"
- **Cuando** se muestran en el sistema
- **Entonces** el objeto se muestra literal como dato de la fuente, el comentario se conserva tal como lo escribió el usuario, y ninguno de los dos se usa como etiqueta o calificación del sistema

### Escenario 7: Cambio de la lista de términos

- **Dado** que el Administrador agrega el término "sobrecosto" a la lista
- **Cuando** se ejecuta la siguiente verificación de pruebas o de ejecución
- **Entonces** "sobrecosto" se detecta, y el cambio queda en el log de auditoría con usuario, fecha y valores anterior y nuevo

### Escenario 8: Lista vacía o inválida

- **Dado** que la lista configurada queda vacía o no se puede leer
- **Cuando** se ejecuta la verificación
- **Entonces** se usa la lista inicial y se registra "Lista de términos prohibidos inválida; se usó la lista inicial"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (PO); beneficia a todos los usuarios y a las personas y empresas nombradas en los datos.
- **Permisos requeridos:** Solo el Administrador modifica la lista (por configuración; no requiere interfaz gráfica).
- **Valor de negocio:** Condición de cumplimiento para el paso a usuarios piloto (riesgo R8, principio de presentación del Brief).

### Reglas de Negocio

**RN-01 – Lista inicial de términos prohibidos** (configurable): sobreprecio, sobreprecios, corrupción, corrupto, corrupta, corruptos, corruptas, fraude, fraudes, fraudulento, fraudulenta, fraudulentos, fraudulentas, hallazgo fiscal, hallazgos fiscales.

**RN-02 – Comparación.** Sin distinguir mayúsculas y minúsculas ni tildes (á=a, é=e, í=i, ó=o, ú=u, ü=u; ñ se conserva). Coincidencia por palabra o frase completa (delimitada por inicio/fin de texto, espacio o signo de puntuación); no por subcadena.

**RN-03 – Alcance de la verificación.** Todos los textos generados por el sistema: etiquetas, títulos, botones, mensajes, estados, advertencias, denominación de señales, textos de reglas y motivos, textos de la cola de revisión, plantillas de correo y textos de exportación si existieran. Excluidos: contenido escrito por usuarios y datos de fuentes externas mostrados literalmente.

**RN-04 – Verificación en pruebas.** Forma parte del conjunto de pruebas automáticas que se ejecuta antes de cada despliegue; si encuentra un término, la prueba falla con: texto, ubicación (pantalla o componente) y término. No se despliega con la prueba fallida.

**RN-05 – Verificación en ejecución.** Antes de guardar una versión de señal, se verifican sus textos compuestos (denominación, regla, motivos, etiquetas de estado). Si alguno contiene un término prohibido: se reemplaza por "Texto no disponible", se registra en el log (señal, campo, término, fecha-hora) y se publica la señal. La denominación es siempre el texto fijo "Señal que merece revisión".

**RN-06 – Sin calificaciones sobre personas o empresas.** El sistema no asigna a entidades, proveedores ni personas ninguna etiqueta, puntaje ni ranking de riesgo; solo muestra sus datos públicos y las señales de sus ítems.

**RN-07 – Lista inválida.** Lista vacía, ilegible o con elementos vacíos → lista inicial completa y mensaje en log "Lista de términos prohibidos inválida; se usó la lista inicial".

**RN-08 – Auditoría.** Cada cambio de la lista se registra en el log de auditoría con usuario, fecha-hora, valor anterior y nuevo.

### Interfaz

Sin interfaz propia. La lista se gestiona por configuración; los resultados se ven en el reporte de pruebas y en el log.

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

**Historias relacionadas:** HU-059 (denominación de la señal), HU-063 (advertencia y textos del detalle).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Variantes incluidas en la lista inicial** (plurales y género): resuelto en RN-01.
- **Textos de usuarios y datos literales de fuentes fuera de la verificación**: NFR-CUM-007 habla de textos generados por el sistema; resuelto en RN-03.
- **Verificación también en ejecución** para los textos compuestos de señales: resuelto en RN-05.

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
