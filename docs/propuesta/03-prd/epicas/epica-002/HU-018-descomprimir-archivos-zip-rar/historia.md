# Historia #018: Descomprimir archivos ZIP y RAR y tratar su contenido como documentos del proceso

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [De Documentos a Datos Comparables](../../../epicas.md#épica-002-de-documentos-a-datos-comparables)  
**Feature:** Obtener y Priorizar Documentos del Proceso  
**Prioridad:** Crítica  
**FRs relacionados:** FR-021

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador del MVP,  
**Quiero** que el sistema descomprima los archivos .zip y .rar descargados de un proceso y registre cada archivo contenido como un documento más del proceso,  
**Para** que las cotizaciones, ofertas y anexos empaquetados en comprimidos puedan priorizarse y leerse igual que los documentos publicados sueltos.

## Descripción

D1 y D4 encontraron que los .zip y .rar de SECOP II contienen más documentos, entre ellos cotizaciones del análisis del sector y anexos económicos con precios. Esta HU toma los comprimidos descargados en estado "contenedor por expandir" (HU-015, HU-016), extrae sus archivos con límites de seguridad y registra cada archivo interno con un identificador estable derivado del comprimido, su ruta interna, su nombre, su tipo y su hash. Los archivos internos pasan luego por la evaluación de vacíos y duplicados (HU-017) y por la priorización (HU-015), donde compiten por los cupos con los demás documentos.

Los comprimidos dentro de comprimidos se expanden hasta una profundidad configurable. Los comprimidos protegidos con contraseña no se intentan abrir. No requiere interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: Expansión de un ZIP con cotizaciones

- **Dado** que el comprimido 600010 "Cotizaciones.zip" del proceso `CO1.BDOS.1234567` está descargado y contiene "Cotizacion Alkosto.pdf", "Cotizacion proveedor 2.pdf" y "Anexo/precios.xlsx"
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** el sistema registra 3 documentos internos con identificadores `600010::Cotizacion Alkosto.pdf`, `600010::Cotizacion proveedor 2.pdf` y `600010::Anexo/precios.xlsx`, cada uno con nombre, ruta interna, extensión, tamaño, hash SHA-256, comprimido de origen, fecha de carga y URL del comprimido; el comprimido queda "expandido" y la priorización del proceso se recalcula

### Escenario 2: Expansión de un RAR

- **Dado** que el comprimido 600030 "Propuesta.rar" contiene "Oferta economica.pdf"
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** el archivo interno se registra como `600030::Oferta economica.pdf` con las mismas reglas del Escenario 1

### Escenario 3: Comprimido dentro de comprimido

- **Dado** que "Sobre2.zip" contiene "Economico.zip", que contiene "Oferta.pdf", y la profundidad máxima es 3
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** se registran `{id}::Economico.zip` como contenedor interno expandido y `{id}::Economico.zip/Oferta.pdf` como documento interno

### Escenario 4: Profundidad máxima superada

- **Dado** que un comprimido tiene 4 niveles de comprimidos anidados y la profundidad máxima es 3
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** se expanden los 3 primeros niveles, el comprimido del cuarto nivel queda "no expandido: profundidad máxima superada" y el comprimido de origen queda "expandido parcialmente"

### Escenario 5: Comprimido protegido con contraseña

- **Dado** que el comprimido 600031 "Oferta.zip" está protegido con contraseña
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** el sistema no intenta adivinar ni probar contraseñas, el comprimido queda "no elegible: archivo protegido" y se recalcula la priorización

### Escenario 6: Comprimido dañado con archivos recuperables

- **Dado** que el comprimido 600032 tiene 5 archivos, de los cuales 2 están dañados
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** se registran los 3 archivos legibles, los 2 dañados quedan anotados con "archivo interno dañado" y el comprimido queda "expandido parcialmente"; si ningún archivo es legible, el comprimido queda "no elegible: archivo dañado"

### Escenario 7: Límites de seguridad

- **Dado** que un comprimido declara 1.200 archivos, o un tamaño descomprimido total de 3 GB, o una relación de compresión de 500 a 1
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** el sistema detiene la expansión de ese comprimido al alcanzar el límite, conserva solo los archivos ya extraídos que no superen los límites, y lo marca "expandido parcialmente" con el motivo "límite de archivos superado", "límite de tamaño descomprimido superado" o "relación de compresión anómala"

### Escenario 8: Entradas que no son documentos o tienen rutas no válidas

- **Dado** que un ZIP contiene la carpeta "__MACOSX/", el archivo ".DS_Store", "Thumbs.db", una carpeta vacía y una entrada con ruta "../../config.txt"
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** esas entradas no se registran como documentos; la entrada con "../" queda anotada como "ruta no válida" y no se escribe fuera del espacio de trabajo del comprimido

### Escenario 9: Comprimido sin archivos

- **Dado** que el comprimido 600033 es válido pero no contiene archivos
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** queda "expandido" con 0 documentos internos y la anotación "comprimido sin archivos"

### Escenario 10: Otro formato comprimido

- **Dado** que el documento seleccionado es "Anexos.7z"
- **Cuando** se ejecuta la expansión de comprimidos
- **Entonces** queda "no elegible: formato de comprimido no soportado" y se recalcula la priorización

### Escenario 11: Reejecución

- **Dado** que el comprimido 600010 ya está "expandido"
- **Cuando** se ejecuta nuevamente la expansión de comprimidos
- **Entonces** no se registran documentos internos duplicados

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (en el MVP es el PO); el proceso es automático.
- **Permisos requeridos:** Rol Administrador para consultar resultados. El Analista no accede.
- **Valor de negocio:** D4 identificó que parte del precio faltante estaba en cotizaciones dentro de ZIP no procesadas (causa técnica corregible).

### Reglas de Negocio

- **RN-01 — Entrada:** documentos descargados con estado "contenedor por expandir" cuya extensión, o firma del archivo, corresponda a ZIP o RAR (incluidas las versiones 4 y 5 de RAR). La firma del contenido prevalece sobre la extensión del nombre.
- **RN-02 — Otros comprimidos:** 7z, tar, gz, bz2 y similares quedan "no elegible: formato de comprimido no soportado".
- **RN-03 — Identificador del documento interno:** `{id_documento del comprimido de primer nivel}::{ruta interna completa}`, con "/" como separador; para comprimidos anidados la ruta incluye el nombre de cada comprimido intermedio (ej. `700100::Sobre2.zip/Economico.zip/Oferta.pdf`; el primer nivel no repite su propio nombre). Es estable: la misma entrada del mismo comprimido siempre produce el mismo identificador.
- **RN-04 — Datos registrados por documento interno:** identificador (RN-03), nombre del archivo, ruta interna, extensión (sufijo del nombre en minúsculas o "desconocida"), tamaño descomprimido, hash SHA-256, id del comprimido de origen, proceso, fecha de carga y URL de origen del comprimido de primer nivel, y fecha de expansión.
- **RN-05 — Profundidad (configurable):** los comprimidos internos se expanden hasta la profundidad máxima (configuración inicial: 3 niveles, contando el comprimido publicado como nivel 1). Un comprimido que supere la profundidad queda "no expandido: profundidad máxima superada".
- **RN-06 — Límites de seguridad (configurables) por comprimido publicado, sumando todos sus niveles:** máximo 500 archivos (configuración inicial), máximo 1 GB descomprimido en total (configuración inicial) y relación de compresión máxima de 100 a 1 por entrada (configuración inicial). Al alcanzar un límite se detiene la expansión de ese comprimido, se conservan los archivos ya extraídos que no lo superan y se registra el motivo.
- **RN-07 — Protegidos:** un comprimido o entrada protegida con contraseña queda "archivo protegido". Nunca se prueban, adivinan ni solicitan contraseñas.
- **RN-08 — Dañados:** las entradas que no se pueden extraer quedan anotadas "archivo interno dañado". Si al menos una entrada se extrajo, el comprimido queda "expandido parcialmente"; si ninguna, "no elegible: archivo dañado".
- **RN-09 — Entradas ignoradas:** carpetas (con o sin contenido; su contenido sí se procesa), y archivos de sistema: cualquier ruta que contenga "__MACOSX/", nombres ".DS_Store", "Thumbs.db", "desktop.ini" y nombres que empiezan por "._". No se registran como documentos.
- **RN-10 — Rutas no válidas:** entradas con ruta absoluta, con "../" o con letra de unidad se anotan "ruta no válida", no se extraen y nunca se escribe fuera del espacio de trabajo del comprimido.
- **RN-11 — Estados del comprimido:** "expandido" (todas las entradas válidas extraídas, incluido el caso de 0 archivos, con la anotación "comprimido sin archivos"), "expandido parcialmente" (con motivo), "no elegible: archivo protegido", "no elegible: archivo dañado" o "no elegible: formato de comprimido no soportado". Un comprimido nunca se envía a la extracción con IA; solo sus archivos internos.
- **RN-12 — Continuidad del flujo:** cada documento interno registrado pasa a la evaluación de vacíos y duplicados (HU-017) y a la priorización del proceso (HU-015), que se recalcula al terminar la expansión. Los estados "no elegible" del comprimido también disparan el recalculo.
- **RN-13 — Idempotencia:** un comprimido "expandido" o "expandido parcialmente" no se vuelve a expandir salvo solicitud explícita del Administrador; una reexpansión no duplica documentos internos con el mismo identificador.

### Interfaz

Sin interfaz gráfica obligatoria. Resultados consultables por proceso y comprimido mediante consultas o registros.

### Sistemas Externos (Si aplica)

No aplica: trabaja sobre archivos ya descargados.

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

**Historias relacionadas:** HU-015 (contenedores y recalculo), HU-016 (descarga), HU-017 (vacíos y duplicados de archivos internos), HU-019 (lectura de formatos).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- El identificador del archivo interno se deriva del comprimido y la ruta interna (`{id}::{ruta}`) → RN-03.
- Límites iniciales de seguridad: profundidad 3, 500 archivos, 1 GB descomprimido y relación 100 a 1 → RN-05, RN-06.
- Solo ZIP y RAR se expanden; otros comprimidos quedan no soportados (el FR solo exige ZIP y RAR) → RN-02.
- Comprimidos protegidos no se abren y nunca se prueban contraseñas → RN-07.

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
