# Historia #062: Registrar la evidencia completa y reproducible de cada señal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)  
**Feature:** Presentación de Evidencia Trazable  
**Prioridad:** Crítica  
**FRs relacionados:** FR-065

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que cada versión de una señal guarde un expediente de evidencia completo e inmutable (ítem, contrato, entidad, proveedor, benchmark, referencias y observaciones, fórmula, desviación, emparejamiento, base tributaria, métodos de adquisición, fecha de corte y confianza),  
**Para** poder revisar, reproducir y llevar a otra instancia la comparación exacta que originó la señal, aunque después se recalculen los benchmarks.

## Descripción

Cada vez que se crea una señal o una nueva versión de ella, el sistema guarda una **instantánea de evidencia** con todos los elementos de FR-065. La instantánea no cambia con recálculos posteriores: un recálculo produce una nueva versión con su propia instantánea. Así se cumple NFR-CAL-004 (100 % de las señales permiten regresar al contrato, al dato de origen y a cada referencia).

Si al generar la señal falta un elemento obligatorio de evidencia (por ejemplo, la copia conservada del documento de donde se extrajo el precio), la señal **no se publica** al Analista: queda "Retenida: evidencia incompleta" y se envía a la cola de revisión del Administrador.

---

## Criterios de Aceptación

### Escenario 1: Instantánea completa de una señal SECOP II

- **Dado** que se genera la versión 1 de una señal del Benchmark 1 para un ítem SECOP II con precio `explicito` extraído de la página 4 de un documento conservado
- **Cuando** el sistema registra la evidencia
- **Entonces** la instantánea contiene todos los bloques de RN-02 (ítem, contrato, entidad, proveedor, benchmark y referencia, observaciones, fórmula, desviación, regla, emparejamiento, base tributaria, métodos de adquisición, fechas de corte, confianza, origen del precio y parámetros) y la señal queda publicada como "Vigente"

### Escenario 2: Precio derivado

- **Dado** que el precio unitario del ítem es `derivado`
- **Cuando** el sistema registra la evidencia
- **Entonces** el bloque del precio incluye el indicador "Precio unitario derivado", el valor total usado, la cantidad usada y la fórmula "precio unitario = valor total del ítem / cantidad" con los valores sustituidos (ej. "18.400.000 / 8 = 2.300.000 COP")

### Escenario 3: Ítem de la TVEC

- **Dado** que el ítem proviene de la TVEC
- **Cuando** el sistema registra la evidencia
- **Entonces** el origen del precio es el registro TVEC (número de orden, línea, dataset de origen y fecha de corte), sin documento ni página

### Escenario 4: Fórmula con valores sustituidos

- **Dado** una señal con precio contratado homologado 2.750.000 COP y referencia 2.100.000 COP
- **Cuando** el sistema registra la evidencia
- **Entonces** la fórmula registrada es "Desviación = (2.750.000 − 2.100.000) / 2.100.000 × 100 = +31,0 %"

### Escenario 5: Inmutabilidad ante recálculos

- **Dado** que la versión 1 de una señal tiene su instantánea y luego un recálculo crea la versión 2
- **Cuando** se consultan ambas versiones
- **Entonces** la versión 1 conserva exactamente su instantánea original y la versión 2 tiene una instantánea nueva

### Escenario 6: Evidencia incompleta retiene la señal

- **Dado** que el precio del ítem fue extraído de un documento cuya copia conservada o hash no existe
- **Cuando** el sistema intenta registrar la evidencia
- **Entonces** la señal queda en estado "Retenida: evidencia incompleta – copia del documento de origen", no aparece para los Analistas y se crea un elemento "Evidencia incompleta de señal" en la cola de revisión del Administrador

### Escenario 7: Retención resuelta

- **Dado** una señal "Retenida: evidencia incompleta" cuya copia del documento se recupera
- **Cuando** se ejecuta el siguiente recálculo
- **Entonces** la instantánea se completa, la señal pasa a "Vigente" y el elemento de la cola se cierra con la resolución "Evidencia completada en el recálculo del {AAAA-MM-DD}"

### Escenario 8: Sin datos personales sensibles

- **Dado** que se registra cualquier instantánea
- **Cuando** se revisa su contenido
- **Entonces** no incluye datos bancarios ni documentos de identidad de representantes legales, supervisores u ordenadores del gasto

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario); proceso automático.
- **Permisos requeridos:** Ninguno para el registro. Las instantáneas no se pueden editar por ningún rol.
- **Valor de negocio:** Trazabilidad 100 % (meta del Brief) y reproducibilidad, base de la credibilidad ("evidencia antes que acusación").

### Reglas de Negocio

**RN-01 – Momento.** Se registra una instantánea al crear la versión 1 de una señal y en cada versión nueva. Las señales que solo actualizan la fecha de última evaluación no generan instantánea nueva.

**RN-02 – Contenido obligatorio de la instantánea (FR-065).**
1. **Ítem:** identificador, descripción, marca, modelo, tamaño (pulgadas), resolución, tecnología, Smart, cantidad, precio unitario original, tipo de precio (`explicito`/`derivado`), base tributaria original, precio homologado.
2. **Contrato u orden:** SECOP II: `id_contrato`, `proceso_de_compra`, modalidad, fecha de firma y URL pública del proceso. TVEC: número de orden y línea, fecha de la orden.
3. **Entidad:** nombre y NIT.
4. **Proveedor:** nombre del proveedor adjudicado tal como lo publica la fuente.
5. **Benchmark:** "Benchmark 1 – Contratación pública" o "Benchmark 2 – Mercado"; estado de la referencia; n; mínimo; mediana; Q1, Q3, IQR cuando aplican; ventana aplicada (y si fue ampliada).
6. **Observaciones:** por cada una: identificador, origen ("Contratación pública – SECOP II", "Contratación pública – TVEC" o "Retail – {tienda}"), producto, fecha, precio original, base, precio homologado, tipo de emparejamiento, método de adquisición, indicador "Manual" y referencia de evidencia (identificador de contrato/orden, URL o captura).
7. **Fórmula y desviación:** texto con valores sustituidos (RN-03) y desviación redondeada.
8. **Regla de señal aplicada** y, si aplica, motivo de no aplicación de la regla de atípicos.
9. **Emparejamiento:** tipo del conjunto y criterios usados (atributos que coincidieron).
10. **Base tributaria:** estado tributario de la comparación, valores convertidos y tarifa usada.
11. **Métodos de adquisición:** conteo de observaciones por método (API / dataset / feed / sitemap-datos estructurados / extracción web / manual).
12. **Fechas de corte:** fecha de corte de cada fuente pública usada (SECOP II, TVEC) y fecha de la observación de mercado más reciente usada; formato AAAA-MM-DD.
13. **Confianza:** puntaje, nivel, desglose por factor y nota de tope si existe.
14. **Origen del precio contratado:** SECOP II: identificador del documento, nombre, URL original, hash de la copia conservada, ubicación (página, u hoja y celda), fecha de descarga; para precio derivado, además valor total usado, cantidad usada y fórmula. TVEC: orden, línea, dataset y fecha de corte.
15. **Parámetros** analíticos usados y **fecha-hora** de la instantánea.

**RN-03 – Formato de la fórmula.** "Desviación = ({precio} − {referencia}) / {referencia} × 100 = {±d,d} %", con valores en COP con separador de miles "." y coma decimal.

**RN-04 – Inmutabilidad.** Una instantánea no se modifica ni se elimina. Las correcciones de datos producen recálculo y nueva versión.

**RN-05 – Completitud.** Son obligatorios los bloques 1–15; dentro de ellos, los campos que la fuente no publica se registran como "No publicado por la fuente" (ej. modelo ausente), salvo los de trazabilidad crítica: identificador del contrato u orden, identificador de cada observación y, para SECOP II, documento, hash de la copia y ubicación del precio. Si falta uno de trazabilidad crítica, la señal queda "Retenida: evidencia incompleta – {elemento faltante}", no visible para Analistas, y se crea (o actualiza, sin duplicar) un elemento "Evidencia incompleta de señal" en la cola de revisión. Al completarse en un recálculo, pasa a "Vigente" y el elemento se cierra con "Evidencia completada en el recálculo del {AAAA-MM-DD}".

**RN-06 – Datos personales.** La instantánea nunca incluye banco, tipo o número de cuenta ni documentos de identidad de representantes legales, supervisores u ordenadores del gasto.

**RN-07 – Respaldo.** Las instantáneas forman parte de los datos respaldados del sistema.

### Interfaz

Sin interfaz propia. La instantánea vigente se muestra en el detalle de la señal (HU-063) y es la base de la navegación a la evidencia (HU-064).

### Sistemas Externos (Si aplica)

No consulta fuentes en el momento del registro: usa datos y copias ya almacenados.

---

## Contexto y Referencias

**Épica origen:** [Señales que Merecen Revisión, con Evidencia](../../../epicas.md#épica-005-señales-que-merecen-revisión-con-evidencia)

**Exclusiones de la Épica:**
- NO incluye señales que no son de precio (concentración, contratación directa, presupuesto vs. contratado): candidatas post-MVP (ÉPICA-009).
- NO incluye rankings de entidades ni de proveedores.
- NO incluye conclusiones automáticas ni lenguaje acusatorio.
- NO incluye detección proactiva con alertas automáticas.
- NO incluye contraste con antecedentes de Contraloría o prensa (RAG).

**Historias relacionadas:** HU-059 (señal y versiones), HU-061 (confianza), HU-063 (detalle), HU-064 (navegación).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **Retener señales con evidencia crítica incompleta** en vez de publicarlas: resuelto en RN-05 para cumplir NFR-CAL-004 (100 %).
- **Proveedor solo por nombre** en la instantánea (minimización de datos): resuelto en RN-02.4 y RN-06.

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
