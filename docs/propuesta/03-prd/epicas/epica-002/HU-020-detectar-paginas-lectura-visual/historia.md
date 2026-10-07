# Historia #020: Detectar las páginas que requieren OCR o lectura multimodal

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Preparar Documentos para la Lectura  
**Prioridad:** Crítica  
**FRs relacionados:** FR-023

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema identifique, página por página, cuáles no tienen texto utilizable o contienen imágenes incrustadas relevantes (aunque también tengan texto) y las prepare como imagen para lectura visual,  
**Para** que las tablas de precios escaneadas o pegadas como imagen no se pierdan en la extracción.

## Descripción

En D4, el 34,9 % de las páginas no tenía capa de texto y el 52 % de los contratos necesitó lectura de imagen. Además, varias tablas de ítems eran imágenes incrustadas dentro de páginas que sí tenían texto (casos 4838434, 7922631, 9691113): un perfil que solo mira "página sin texto" no las detecta, y en D4 eso dejó sin precio a 2 contratos.

Esta HU evalúa cada página de la representación de cada documento preparado (HU-019) y la marca como "texto suficiente" o "requiere lectura visual", con el motivo. Las páginas que requieren lectura visual se convierten en imagen a una resolución configurable y quedan asociadas a su número de página, para que la extracción (HU-022) las lea con OCR o lectura multimodal y la evidencia cite esa página. Es un proceso determinístico, sin IA, que no requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Página escaneada sin texto utilizable

- **Dado** que la página 2 de "Oferta economica firmada.pdf" tiene 0 caracteres utilizables y el mínimo configurado es 50
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la página queda "requiere lectura visual" con el motivo "sin texto utilizable" y se genera su imagen a 110 dpi asociada a "página 2"

### Escenario 2: Página con texto y una tabla incrustada como imagen

- **Dado** que la página 4 del documento del proceso 4838434 tiene 1.200 caracteres de texto y una imagen incrustada que ocupa el 35 % del área de la página, y el umbral configurado es 10 %
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la página queda "requiere lectura visual" con el motivo "imagen incrustada", se genera su imagen y la capa de texto de la página se conserva para la extracción

### Escenario 3: Página con texto y solo logotipos pequeños

- **Dado** que una página tiene 2.000 caracteres de texto y dos logotipos que ocupan en total el 4 % del área, ninguno ≥ 10 %
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la página queda "texto suficiente" y no se genera imagen

### Escenario 4: Documento de imagen

- **Dado** que el documento "Cotizacion.jpg" está preparado como una única página marcada "imagen"
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la página queda "requiere lectura visual" con el motivo "documento de imagen" y se usa la imagen original sin reescalar por encima de su resolución

### Escenario 5: Hoja de cálculo con imagen insertada

- **Dado** que la hoja "Oferta" de un XLSX tiene una imagen insertada con una tabla de precios
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la imagen se registra como unidad "Oferta, imagen 1" con "requiere lectura visual" y motivo "imagen incrustada"; las celdas de la hoja siguen disponibles como texto

### Escenario 6: Límite de páginas visuales por proceso

- **Dado** que el proceso tiene 75 páginas que requieren lectura visual entre sus documentos seleccionados y el límite configurado es 60
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** se generan imágenes para las 60 primeras páginas según el orden de prioridad de los documentos y luego el orden de página; las 15 restantes quedan "lectura visual omitida por límite" y el proceso queda anotado con ese número

### Escenario 7: Falla al generar la imagen de una página

- **Dado** que la generación de la imagen de la página 3 de un documento falla
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** la página queda "requiere lectura visual" con la anotación "imagen no generada" y el error, y las demás páginas continúan normalmente

### Escenario 8: Indicadores por documento y por proceso

- **Dado** que terminó la detección para el proceso `CO1.BDOS.1234567`
- **Cuando** el Administrador consulta el resultado
- **Entonces** ve, por documento, el número de páginas totales, de páginas "sin texto utilizable", de páginas con "imagen incrustada" y de imágenes generadas, y para el proceso si "requirió lectura visual" (sí/no)

### Escenario 9: Página en el límite de texto

- **Dado** que una página sin imágenes tiene exactamente 50 caracteres utilizables
- **Cuando** se ejecuta la detección de lectura visual
- **Entonces** queda "texto suficiente"; con 49 caracteres queda "requiere lectura visual"

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO); el proceso es automático.
- **Permisos requeridos:** Rol Administrador para consultar resultados y modificar parámetros. El Analista no accede.
- **Valor de negocio:** Recupera precios que solo existen como imagen; D4 identificó esta causa técnica como corregible.

### Reglas de Negocio

- **RN-01 — Entrada:** documentos "preparado" (HU-019) con su representación por página (PDF y documentos de texto paginados), por hoja (hojas de cálculo) o de imagen.
- **RN-02 — Caracteres utilizables:** letras y dígitos de la capa de texto de la página, sin contar espacios, signos de puntuación ni caracteres de control.
- **RN-03 — Sin texto utilizable (configurable):** una página con menos caracteres utilizables que el mínimo (configuración inicial: 50) queda "requiere lectura visual", motivo "sin texto utilizable". Con exactamente el mínimo, no aplica este motivo.
- **RN-04 — Imagen incrustada (configurable):** una página con al menos una imagen incrustada que ocupe un porcentaje del área de la página mayor o igual al umbral (configuración inicial: 10 %) queda "requiere lectura visual", motivo "imagen incrustada", aunque tenga texto. Las imágenes por debajo del umbral (logotipos, firmas, sellos pequeños) no activan la regla, aunque su suma lo supere.
- **RN-05 — Ambos motivos:** si se cumplen RN-03 y RN-04, se registran ambos motivos.
- **RN-06 — Documentos de imagen:** JPG y PNG siempre "requiere lectura visual", motivo "documento de imagen"; se usa la imagen original (si su lado mayor supera 4.000 píxeles se reduce proporcionalmente a 4.000).
- **RN-07 — Hojas de cálculo:** cada imagen insertada en una hoja se registra como unidad "{hoja}, imagen N" (N desde 1 por hoja, en el orden del archivo) con "requiere lectura visual", motivo "imagen incrustada". Las celdas siguen como texto.
- **RN-08 — Imagen de la página (configurable):** para cada página que requiere lectura visual se genera una imagen de la página completa a la resolución configurada (configuración inicial: 110 dpi, valor que en D4 produjo imágenes legibles), asociada al identificador del documento y al número de página. La capa de texto de la página, si existe, se conserva y se entrega también a la extracción.
- **RN-09 — Límite por proceso (configurable):** máximo de páginas con lectura visual por proceso (configuración inicial: 60). Se asignan en el orden de prioridad de los documentos (HU-015) y luego por número de página. Las que exceden quedan "lectura visual omitida por límite", y el proceso queda anotado con el número de páginas omitidas.
- **RN-10 — Fallas:** si no se puede generar la imagen de una página, la página queda "requiere lectura visual" con la anotación "imagen no generada" y el error; no detiene las demás páginas.
- **RN-11 — Resultado registrado:** por página o unidad: clasificación ("texto suficiente" o "requiere lectura visual"), motivos, caracteres utilizables, número y porcentaje de imágenes incrustadas, imagen generada (sí/no) y resolución. Por documento: páginas totales, páginas por motivo e imágenes generadas. Por proceso: "requirió lectura visual" (sí si al menos una página o unidad la requiere) y páginas omitidas por límite.
- **RN-12 — Validación de parámetros:** mínimo de caracteres: entero 0–1.000; umbral de imagen: 1–100 %; resolución: 72–300 dpi; límite por proceso: entero 1–500. Fuera de rango se rechaza con el mensaje "Valor fuera de rango para {parámetro}: debe estar entre {mín} y {máx}" y se conserva el valor anterior.
- **RN-13 — Sin IA:** la detección y la generación de imágenes no usan IA y funcionan aunque la extracción con IA esté desactivada.

### Interfaz

Sin interfaz gráfica obligatoria. Resultados y parámetros consultables y configurables mediante consultas, configuración o una vista administrativa mínima.

### Sistemas Externos (Si aplica)

No aplica.

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

**Historias relacionadas:** HU-019 (representación e imágenes incrustadas), HU-022 (lectura con OCR o multimodal), HU-030 (costo por documento).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- Umbrales iniciales: 50 caracteres utilizables por página e imagen incrustada ≥ 10 % del área → RN-03, RN-04.
- Resolución inicial de 110 dpi, la usada en D4 con imágenes legibles → RN-08.
- Límite inicial de 60 páginas con lectura visual por proceso, para controlar costo → RN-09.
- Las imágenes insertadas en hojas de cálculo también se tratan como unidades de lectura visual → RN-07.

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
