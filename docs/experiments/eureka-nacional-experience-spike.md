# EN-01 · Experiencia contractual en procesos de suministro

**Estado:** primer smoke real parcial. Cinco procesos con inventario y experiencia contractual sin resolver.

## Pregunta e hipótesis

¿Se pueden identificar automáticamente procesos nacionales de suministro sin una barrera de experiencia contractual? La hipótesis del 80–90 % con requisito se contrastará con una muestra cuya cobertura y limitaciones queden registradas.

## Metodología prevista

1. Usar CDP y Licitaciones.info para discovery e inventario. Registrar fecha de corte, ventanas, departamentos, estados, modalidades, criterios y duplicados. Distinguir históricos de abiertos. Incluir adquisición de bienes y excluir inicialmente obras y servicios mediante criterios explícitos.
2. Priorizar invitación, pliego, estudios previos, anexos habilitantes y adendas. Guardar evidencias de paginación, filtros, fallos de acceso y documentos omitidos.
3. Descargar binarios desde SECOP mediante el descargador existente. Usar almacenamiento local, deduplicación por hash, extracción nativa y OCR por página cuando corresponda. Aplicar heurísticas y reglas primero. El uso posterior de IA requiere autorización y presupuesto.
4. Clasificar cada caso como `no_experience_required`, `experience_required`, `experience_ambiguous` o `not_resolved`. Exigir cobertura suficiente para afirmar ausencia de requisito. Registrar modificaciones, requisitos por lote y sujeto al que aplica la experiencia.
5. Registrar proceso, referencia, documento, hash, página, evidencia, método, cobertura y motivo. Revisar manualmente todos los casos clasificados sin experiencia en las primeras corridas, además de ambiguos y una muestra de exigidos y excluidos. Mantener la evidencia privada en la carpeta local de la corrida.

## Ejecución y resultados

La progresión propuesta es 5–10 procesos de humo, 30–50 candidatos exploratorios y ampliación hasta 100–200 procesos resueltos si la evidencia y los costos la justifican. Cada fase requiere límites explícitos y revisión de los resultados previos.

Registrar por corrida los parámetros, el embudo desde discovery hasta resolución, los cuatro resultados de clasificación, el denominador de cada métrica, las discrepancias humanas, errores, sesgos y ejemplos redactados. Calcular la proporción con y sin requisito entre los resueltos, la tasa de resolución entre analizados y el rendimiento sobre candidatos. Distinguir candidatos automáticos y confirmados.

Registrar documentos, páginas, OCR, duración, volumen, llamadas IA y costos conocidos o estimados. Calcular costo por proceso resuelto y por candidato confirmado cuando existan datos. Las pruebas de regresión se compararán con el baseline del handoff.

## Estrategia implementada

- **Discovery.** Consulta get-info en orden descendente por FechaPublicacion. Envía
  los 1.130 identificadores capturados como un solo `query.ubicacion_filter`
  por página. Aplica localmente el
  [perfil comercial nacional](eureka-nacional-universo-comercial.md) por UNSPSC
  verificado y evidencia textual. Conserva el motivo de inclusión o exclusión y
  los solapamientos. Prioriza procesos vigentes y mínima cuantía, con turnos entre
  departamentos dentro de cada nivel. La cobertura real y la paginación del perfil
  aún deben contrastarse en vivo.
- **Documentos.** Prioriza invitación/pliego/condiciones, adendas y estudios o
  anexos. Excluye nombres de borradores y documentos posteriores claramente
  identificados. La primera entrega procesa PDF y registra el resto del inventario,
  formatos omitidos, límites y páginas sin cobertura. Reutiliza el inventario CDP,
  el descargador seguro de SECOP y el almacén por hash.
- **Experiencia.** Una obligación explícita y aplicable al proponente en un texto
  rector puede clasificar como experiencia exigida. Para clasificar ausencia se
  exige exención explícita, páginas con cobertura completa y documentos relevantes
  cubiertos. Una coincidencia con RUP, personal o fabricante no indica por sí sola
  experiencia contractual. Contradicciones, lotes, referencias a anexos y lenguaje
  condicional producen ambigüedad. Una cobertura insuficiente produce un caso sin
  resolver. La evidencia conserva regla, documento, URL, hash, página, localizador,
  método de extracción y fragmento.
- **Medición.** La CLI registra embudo, razones de exclusión, estados de apertura,
  categorías, proporciones con numerador y denominador, descargas, bytes, páginas
  y duración. La revisión humana y los costos monetarios quedan para la corrida.

## Smoke test preparado

Ejecutar únicamente tras autorizar la corrida real. Usar un Edge CDP de loopback
dedicado a Eureka Nacional, con perfil local restringido fuera de los worktrees.
Si el puerto indicado ya pertenece a Eureka Regional, usar otro puerto.
Iniciar sesión manualmente, seleccionar el perfil autorizado de Licitaciones.info y
dejar abierta una sola pestaña de Contratos desktop. La CLI valida el endpoint y
reutiliza la sesión en memoria mediante CDP. El resolver de perfiles compartido
aplica `--profile-id`, luego `LICITACIONES_PROFILE_ID` del entorno o de
`backend/.env`, y devuelve un error si falta el ID.

Desde la raíz del worktree experimental, en PowerShell:

```powershell
$spikePython = if (Test-Path '.\backend\.venv\Scripts\python.exe') {
    (Resolve-Path '.\backend\.venv\Scripts\python.exe').Path
} else {
    (Resolve-Path '..\COMPRAS PUBLICAS\backend\.venv\Scripts\python.exe').Path
}
$env:PYTHONPATH = (Resolve-Path '.\backend\src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
if (!(Test-Path Env:LICITACIONES_PROFILE_ID) -and !(Test-Path '.\backend\.env')) {
    $regionalEnv = (Resolve-Path '..\COMPRAS PUBLICAS\backend\.env').Path
    $readCdpProfile = "import sys; from public_procurement.shared.config import Settings; from public_procurement.licitaciones_cdp.configuration import resolve_profile_id; print(resolve_profile_id(settings=Settings(_env_file=sys.argv[1], database_url='disabled://no-db')))"
    $env:LICITACIONES_PROFILE_ID = & $spikePython -c $readCdpProfile $regionalEnv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo resolver LICITACIONES_PROFILE_ID.' }
}
& $spikePython '.\backend\scripts\eureka_nacional_en01.py' --processes 5 --documents 5 `
  --discovery-pages 4 --recent-days 30 --cdp-url 'http://127.0.0.1:9232' `
  --commercial-profile '.\backend\config\eureka_nacional_commercial.v1.json' `
  --geography '.\backend\scripts\eureka_nacional_geography(from_licitaciones_info).v1.json' `
  --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

El intérprete alternativo reutiliza dependencias Python 3.12 ya instaladas de solo
lectura. Las importaciones de la aplicación apuntan a este worktree. El comando
transfiere solo el valor resuelto del perfil para el proceso actual cuando la
configuración local vive en el otro worktree. La CLI usa una
URL de base deshabilitada y su extractor llama al servicio compartido en dry-run.

| Tope del smoke propuesto | Valor |
|---|---:|
| Procesos seleccionados | 5. La CLI acepta 5–10. |
| Discovery | 4 páginas de hasta 30 filas y 30 días de publicación en hora de Bogotá. Cada página recibe el filtro completo de 1.130 ubicaciones. |
| Inventario | Hasta 10 páginas por proceso, con detección de página repetida. |
| Descargas | 5 totales, máximo 2 por proceso y 10 MiB por PDF. |
| Extracción nativa | Lectura por página de todo el PDF mientras alcance el presupuesto técnico. |
| OCR | Hasta 2 páginas por PDF y 10 por corrida, con Tesseract local en español. |
| Red | 60 créditos compartidos. Cada descarga reserva 6 por posibles redirecciones. |
| Tiempo | Presupuesto operativo de 360 s con margen antes de cada operación. CDP tiene timeout de 20 s por solicitud, descarga de 12 s, extracción nativa de 12 s y OCR de 14 s por PDF con 6 s por página. |
| IA | 0 llamadas. |

Salida en `/.local/eureka-nacional-spike/en01-*/` con procesos, inventario,
clasificaciones, métricas, errores, resumen y binarios locales. Los resultados
pueden quedar parciales por límites, sesión, paginación o faltantes documentales.
El código 2 indica resultado parcial. Los códigos CDP identifican fallos de sesión
o de contrato de la fuente. Los valores y fragmentos de los documentos son privados.

## Primer smoke real · 19 de noviembre de 2026

La corrida `en01-ms7c7hyc`, iniciada a las 22:03 hora de Bogotá desde
`11cad4d`, terminó parcial (código de salida `2`). El preflight autenticado
pasó y el endpoint devolvió cuatro respuestas válidas con el filtro explícito de
1.130 ubicaciones. Las páginas 1–4 devolvieron 30 filas cada una, con conteos del
proveedor de 31, 61, 91 y 121 respectivamente. El cambio entre páginas impide
interpretar 121 como total del universo.

| Control | Resultado |
|---|---:|
| Filas recibidas y únicas | 120 de 120 |
| Departamentos observados | 26 en el feed y 4 en los cinco seleccionados |
| Fuentes | 64 SECOP II, 54 SECOP I, 1 universidad y 1 otro portal |
| Candidatos comerciales | 19 |
| Elegibles para inventario | 8, de los cuales 4 estaban abiertos al corte |
| Seleccionados con inventario | 5 de 5 |
| Documentos inventariados | 43 |
| Descargas | 4 de 5 intentos, 2.903.078 bytes |
| Extracción | 1 página de texto nativo, 0 páginas OCR |
| Casos sin resolver | 5 de 5 |
| Recursos | 45,125 s del runner, 46 de 60 créditos de red y 0 llamadas de IA |

Los ocho elegibles se identificaron por palabras clave. Sus categorías
principales fueron ferretería (3), informática (2), uniformes y EPP (2), y
papelería (1). Hubo cuatro procesos con coincidencias en más de una categoría.
Las 120 filas incluyeron modalidad. El artefacto registró 0 filas con UNSPSC
interpretable y 0 con descripción independiente en los campos leídos.

De las 120 filas, 112 quedaron fuera del funnel documental: 66 fuera del perfil
comercial, 30 por servicio principal, 11 por fuente o inventario no compatible,
4 por falta de evidencia clara de bien físico y 1 por obra civil. Otros tres
elegibles quedaron fuera de la selección de cinco.

Se inventariaron 30 PDF, 9 DOCX, 1 XLSX y 3 formatos indeterminados. Quedaron 25
documentos sin seleccionar por presupuesto y 13 por formato. Una invitación
superó 10 MiB (`too_large`) y tres PDF superaron 12 páginas (`page_limit`). El
único PDF leído por completo fue una cotización de una página. Los cinco
inventarios produjeron `governing_documents_incomplete` y cero cláusulas
clasificables. La tasa de resolución fue 0/5. La tasa de ausencia de experiencia
entre los resueltos queda indeterminada.

### Siguiente corrida

1. Probar offline la selección de documentos rectores con nombres que comienzan
   por numeración. Esta corrida seleccionó un proyecto de pliego con prefijo
   numérico y lo trató como documento principal. Verificar también que una
   cotización genérica no desplace un rector.
2. Evaluar cómo anticipar tamaño y páginas donde existan metadatos disponibles.
   Si el documento rector supera un límite, conservar la causa y evaluar
   alternativas verificables dentro del presupuesto antes de proponer otro tope.
3. Verificar en otra corrida autorizada la cobertura documental, OCR sobre un
   documento aplicable y el significado operativo de `count`. La muestra actual
   demuestra diversidad geográfica observada y acceso a inventarios.

Los archivos de procesos, inventarios, errores, métricas, binarios y resultados
por caso permanecen en `.local/eureka-nacional-spike/en01-ms7c7hyc/`. Se ejecutó
una sola corrida real. La siguiente requiere autorización.

## EN-01.1 · Clasificación contextual offline

La selección normaliza prefijos numéricos y prioriza invitaciones, pliegos
definitivos, adendas y anexos habilitantes. Excluye cotizaciones y borradores
identificados por nombre. Usa señales de portada y conserva las marcas de
versión y fechas etiquetadas que puede reconocer. Ante un límite, prueba una
alternativa dentro de los cupos restantes. El extractor nativo y la
recuperación OCR selectiva siguen siendo los compartidos.

El motor registra `NEG_CONCLUSIVA`, `EXIGENCIA`, `NORMATIVA_CONDICIONAL` y
`OTRO`, con documento, hash, página, método y fragmento. Una respuesta breve
adquiere significado bajo su encabezado de experiencia. Se conserva la
polaridad de la doble negación y se separan hipótesis normativas, puntaje,
desempates y experiencia de terceros. Las condiciones por lote, referencias
a reglamentos o anexos y versiones contradictorias se conservan para revisión.
La fecha declarada en portada se conserva como señal, junto con la naturaleza
del documento. La resolución de supersesión requiere evidencia aplicable.

La revisión se prioriza de forma independiente del estado del proceso. Se
ordenan la evidencia favorable, las contradicciones, el silencio con cobertura,
la evidencia insuficiente y la exigencia explícita. El runner deja la cola y
las métricas de afirmaciones en el directorio local de cada corrida.

| Caso real | Evidencia nativa | Revisión | Estado del expediente aportado |
|---|---|---|---|
| Pore, PMP-005-2026 | Pág. 11, sección 15. «En este caso no se requiere de experiencia». | Favorable explícita | `not_resolved`. Inventario del proceso por corroborar. |
| El Plato, P-MC-MP-051-2026 | Pág. 13, «EXPERIENCIA: No aplica». El desempate se trató como otro criterio. | Favorable explícita | `not_resolved`. Inventario del proceso por corroborar. |
| La Capilla, ventiladores | Pág. 20, sección 3.3. «No se requiere» en estudios previos. | Favorable explícita | `not_resolved`. Falta contrastar con invitación y modificaciones aplicables. |
| Chivatá, invitación 21 | Págs. 1 y 4, menciones condicionadas y remisiones al reglamento interno. | Silencio documental y dependencia | `not_resolved`. Revisar el reglamento aplicable. |
| Chivatá, invitación 22 | Págs. 1 y 4, menciones condicionadas y remisiones al reglamento interno. | Silencio documental y dependencia | `not_resolved`. Revisar el reglamento aplicable. |

Se leyeron 5 PDF y 82 páginas con texto nativo. Se registraron 25
afirmaciones en estos casos, 3 favorables, 19 normativas o condicionales,
3 de otro tipo y 0 exigencias explícitas. El replay coincidió con las 5
etiquetas de estado y evidencia favorable. Los recuentos de falsos positivos y
negativos favorables fueron 0 y 0 en estos casos. Son semillas conocidas y
sirven como regresión. Los ejemplos sintéticos se verifican aparte.

El procesamiento local de lectura y clasificación inicial de estos PDF tomó
15,304 s. Reclasificar el texto ya extraído con la regla final tomó 0,52 s
sumando los cinco casos. La validación usó 0 páginas OCR, 0 créditos de red
y 0 llamadas de IA. Se leyó completo el material local de hasta 28 páginas
por PDF. El runner nacional conserva su tope previo de 12 páginas por PDF.

### Correcciones humanas locales

`review_queue.json` sugiere qué casos revisar. Guardar las correcciones
en JSONL bajo `.local/`, una por línea, con `case`, `inventory_complete`,
`expected_status`, `expected_favorable` y `documents`. Cada documento
incluye `document_id`, `name`, `role`, `complete` y `fragments`. Cada
fragmento contiene `text` y `source_locator` con `page_number` y
`extraction_method`. Registrar por separado el motivo de la corrección
si se necesita para revisión. Se acepta `sha256` y `url` para trazabilidad.

Con el intérprete y `PYTHONPATH` del smoke preparados, reproducir:
`& $spikePython backend/scripts/eureka_nacional_replay.py .local/en01-1-validation/review-cases.jsonl`.
El replay imprime solo conteos. `.local/en01-1-validation/results.json`
conserva la evidencia detallada de la validación real.

### Criterios para el segundo smoke

Conservar 5 procesos, ventana de 30 días, 4 páginas de 30 filas, 5 intentos
de descarga, máximo 2 por proceso, 10 MiB y 12 páginas por PDF, máximo 2
páginas OCR por PDF, 60 créditos, 360 s y 0 IA. Medir si la selección alcanza
más documentos rectores y aporta evidencia útil por crédito. Revisar los
casos favorables y las dependencias antes de inferir accesibilidad. Los PDF
largos pueden seguir bloqueando conclusiones si falta una alternativa
aplicable. La segunda corrida se ejecutó con ese presupuesto.

## Segundo smoke real · 23 de noviembre de 2026

La corrida `en01-ifqy1v2y` terminó parcial (salida `2`) con EN-01.1 desde
`6e66d57`. El preflight con el perfil configurado pasó. El lanzador local
priorizó las cinco identidades SECOP del primer smoke si estaban presentes y
eran elegibles en la consulta actual. Las cuatro páginas autorizadas
devolvieron 120 filas de 26 departamentos, sin coincidencias con esas cinco
identidades. Se eligieron cinco procesos nuevos con las reglas vigentes.
El cambio de fecha, perfil y muestra limita la comparación causal.

| Métrica | Primer smoke | Segundo smoke |
|---|---:|---:|
| Archivos etiquetados como rector | 4 | 5 |
| Invitaciones o pliegos rectores aparentes por título | 3 | 4 |
| Cotizaciones seleccionadas | 1 | 0 |
| Borradores seleccionados | 1 | 0 |
| Intentos de descarga | 5 | 5 |
| Descargas exitosas | 4 | 5 |
| Páginas nativas con texto | 1 | 0 |
| Páginas OCR | 0 | 0 |
| Afirmaciones recuperadas | 0 | 0 |
| Evidencias explícitas favorables | 0 | 0 |
| Silencio documental con cobertura | Sin métrica contextual | 0 |
| Casos contradictorios | 0 registrados | 0 |
| Casos resueltos | 0 | 0 |
| Casos sin resolver | 5 | 5 |
| Créditos de red | 46 | 46 |
| Tiempo del runner | 45,125 s | 44,609 s |
| Llamadas de IA | 0 | 0 |

Se obtuvieron los cinco inventarios, con 44 documentos. La selección dejó
fuera cinco cotizaciones. Cuatro de los cinco títulos seleccionados
correspondían aparentemente a invitaciones. El quinto era un archivo de
formatos cuyo título incluía «invitación». Se le asignó el rol de rector
aunque el inventario incluía también una invitación pública. La vigencia de
los documentos quedó sin corroborar porque no se leyó su contenido.

Se descargaron 7.061.340 bytes. Los cinco PDF superaron 12 páginas y
devolvieron `page_limit` antes de extracción nativa u OCR. Los cinco
inventarios tenían otros PDF elegibles. El reparto consumió los cinco
intentos en un documento por proceso y dejó cero intentos para alternativas.
Por ello su ejecución en vivo queda sin validar. Pasaron seis pruebas offline de alternativas y títulos numerados. Los cinco casos quedaron
con prioridad de revisión por evidencia insuficiente, sin candidatos
favorables detectados.

El ranking eligió cuatro invitaciones en esta muestra y dejó las
cotizaciones fuera. La evidencia útil recuperada fue cero en ambas corridas.
La ausencia de texto habilitante dejó sin medir una mejora de clasificación
en vivo. El diferente tamaño de los documentos impide atribuir el descenso
de páginas leídas a una regresión del extractor.

Para un próximo ensayo autorizado, distinguir archivos de formatos o anexos
de la invitación que los contiene, y definir cómo reservar un intento para
alternativas dentro del presupuesto. Conservar la evidencia de la versión y
la causa de cada límite. El detalle permanece en
`.local/eureka-nacional-spike/en01-ifqy1v2y/`. La tercera corrida requiere
autorización.


## EN-01.2 · Replay offline del segundo smoke

El lector anterior contaba las páginas y devolvía `page_limit` antes de intentar
leer la primera. Los cinco PDF ya descargados tenían entre 14 y 73 páginas.
EN-01.2 activa en el runner nacional la lectura nativa por página sin tope por
cantidad. El lector conserva los fragmentos y sus localizadores. Si se interrumpe,
recupera las páginas guardadas en el directorio temporal del lector y marca la
cobertura parcial con el motivo específico.

| Tipo de presupuesto | Política |
|---|---|
| Seguridad de extracción | 10 MiB por PDF, hasta 512 MiB por proceso lector, 12 s de límite externo del lector nativo y parada cooperativa antes del límite cuando el lector puede devolver lo recuperado. Se conservan los límites de 2 millones de caracteres y 10.000 fragmentos por PDF. Si una página falla, se conserva el texto de las demás. |
| OCR | Presupuesto independiente de 0 a 2 páginas por PDF, 2 por defecto. Solo se consideran páginas cuyo texto nativo es insuficiente. Se priorizan las adyacentes a indicios de secciones habilitantes y la portada de un rector identificado por nombre. Se conservan 6 s por página y 14 s de presupuesto OCR por PDF, más margen del supervisor. Las páginas sin indicios, fuera de presupuesto o cuyo OCR falla quedan pendientes. |
| Análisis lingüístico | EN-01.1 analiza los fragmentos por página con su segmentación por encabezados y cláusulas. El contexto no se arrastra entre fragmentos ni páginas. Cada evidencia retiene un fragmento de hasta 620 caracteres. Los cuatro estados y la prioridad humana mantienen las mismas reglas. |

El replay reutilizó los cinco PDF verificados por hash y los inventarios
guardados del segundo smoke. Se volvió a aplicar el rol por nombre para
clasificar los formatos auxiliares como soporte. La invitación rectora de ese
proceso seguía en el inventario y no estaba entre los PDF descargados. Una prueba
de regresión confirma que una invitación auténtica recibe el cupo antes que
`Formatos INVITACIÓN PÚBLICA`, incluso con prefijos numéricos.

| Métrica | Segundo smoke, extracción original | Replay offline |
|---|---:|---:|
| PDF disponibles | 5 | 5 |
| Páginas leídas con texto nativo | 0 | 218 de 218 |
| Páginas procesadas | 0 | 218 |
| Páginas que requieren OCR según el umbral de calidad | Sin evaluar | 0 |
| Páginas OCR intentadas / con texto recuperado | 0 / 0 | 0 / 0 |
| Páginas pendientes en los PDF disponibles | 218 | 0 |
| PDF con cobertura completa | 0 | 5 |
| Afirmaciones / referencias clasificadas | 0 | 63 |
| Ausencias explícitas / exigencias explícitas | 0 / 0 | 0 / 3 |
| Casos priorizados por evidencia favorable | 0 | 0 |
| Procesos resueltos / pendientes de resolución | 0 / 5 | 0 / 5 |

Las 63 detecciones se distribuyeron en 51 normativas o condicionales, 9 referencias
a otros criterios y 3 exigencias explícitas en dos procesos. Dos detecciones de
exigencia correspondían a texto repetido en páginas distintas de una misma
invitación. El clasificador devolvió dos `experience_ambiguous` por cláusulas de
aplicabilidad limitada y tres `not_resolved`. La cola dio prioridad de silencio
documental a un caso y señaló una exigencia pendiente de corroboración en otro.
Hubo tres casos con prioridad de evidencia insuficiente. No aparecieron
contradicciones entre exigencia y ausencia explícita. La cobertura de los cinco
archivos no resolvió las dependencias del inventario completo.

El replay procesó 7.061.340 bytes y recuperó 555.399 caracteres. Duró 24,531 s,
con 23,656 s acumulados de extracción y 0,859 s de clasificación. Los lectores
nativos registraron 20,016 s de CPU y el proceso coordinador registró 2,125 s.
El límite de memoria es un tope configurado. El replay no midió el pico real de
memoria. Hubo 0 errores de extracción, 0 descargas, 0 consultas CDP,
0 créditos de red y 0 llamadas de IA.

Desde la raíz del worktree experimental, con el intérprete de las pruebas y
`PYTHONPATH` apuntando al `backend/src` de este worktree:

```powershell
& $spikePython '.\backend\scripts\eureka_nacional_pdf_replay.py' `
  '.\.local\eureka-nacional-spike\en01-ifqy1v2y' --ocr-pages 2 `
  --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

El comando crea un directorio `pdf-replay-*` ignorado por Git con
`metrics.json` y `replay.json`. El segundo archivo conserva el documento,
la página, el fragmento y las dependencias para revisión humana. El próximo
smoke real requiere autorización.


## EN-01.3 · Aplicabilidad y prioridad comercial

Se evaluaron las mismas 218 páginas y los mismos inventarios del segundo smoke.
Las reglas guardan por separado el tipo de afirmación, el alcance observado, la
sección y su página, la conclusión formal y la razón de prioridad comercial.
El contexto de un encabezado explícito se puede arrastrar una página nativa
adyacente del mismo documento. Se agregó una reparación puntual del texto
`acredita r experiencia` y una regla para el imperativo `Acreditar experiencia`
bajo un encabezado explícito de experiencia general y admisibilidad.

La prioridad comercial de exigencia requiere una cláusula general en un
documento rector leído completo y un inventario disponible. Una contradicción,
una remisión documental detectada o un rector o adenda identificados y
pendientes impiden esa despriorización. Los documentos de rol aún desconocido
quedan enumerados en la cobertura y todavía pueden impedir la resolución formal.
La señal comercial no descarta procesos automáticamente ni cambia el presupuesto
de adquisición. El replay evaluó las cláusulas de la versión de cada PDF
guardada en el segundo smoke. La vigencia actual y las modificaciones
posteriores quedan sin verificar.

| Prioridad comercial | Criterio |
|---|---|
| Favorable explícita | Cláusula expresa de ausencia, con su página y motivo de corroboración si hay cobertura pendiente. |
| Silencio para revisión | Rector leído con cobertura completa, sin afirmación decisiva detectada. |
| Condición limitada o ambigua | Aplicabilidad restringida sin una obligación general independiente, evidencia contradictoria o una dependencia documental relevante. |
| Insuficiencia documental | Falta el rector, la vigencia documental no se puede corroborar o el alcance general de la exigencia sigue sin establecerse. |
| Exigencia aplicable identificada | Obligación general acreditada en el rector leído. Se baja su prioridad comercial aunque la conclusión formal siga pendiente por el inventario. |

| Resultado en la misma muestra | EN-01.2 | EN-01.3 |
|---|---:|---:|
| Detecciones totales | 63 | 63 |
| Exigencias explícitas detectadas | 3 en 2 procesos | 4 en 4 procesos |
| Ausencias explícitas / declaradas | 0 / 0 | 0 / 0 |
| Prioridad de exigencia / silencio / insuficiencia | 1 / 1 / 3 | 4 / 0 / 1 |
| Estado formal ambiguo / sin resolver | 2 / 3 | 0 / 5 |
| Procesos formalmente resueltos | 0 | 0 |

La revisión contextual separó un apartado diferencial de Mipyme de la
obligación general y distinguió reglas de proponentes plurales y desempate de
otra obligación general independiente. También recuperó una exigencia que se
había clasificado como silencio por una palabra dividida en el texto nativo.
El caso restante tiene un formato auxiliar leído y una invitación rectora
pendiente. Los cuatro casos con exigencia general mantienen `not_resolved` por
documentos de rol desconocido pendientes en sus inventarios.

El replay duró 20,953 s, con 0,688 s de clasificación, sin OCR, descargas,
consultas CDP ni llamadas de IA. Pasaron 192 pruebas offline, incluidas ocho
regresiones nuevas. Cubren el alcance de esas obligaciones, una adenda
pendiente, el formato auxiliar, el silencio, la ausencia explícita sin
corroboración y la contradicción. En esta muestra no se introdujeron falsos
positivos de ausencia. La muestra carece de un caso favorable confirmado con
el que medir sensibilidad de esa clase. Siguen pendientes las variantes de
redacción y los encabezados rotos o alejados de la cláusula. La evidencia por
página queda bajo `.local/`. Una tercera corrida real requiere autorización.


## EN-01.4 · Plan de corrida exploratoria nacional

El plan que se autorizó el 23 de noviembre de 2026 está registrado abajo. El modo optativo
`--exploratory` usa la misma fuente, los 1.130 identificadores, las 21
categorías del perfil comercial, la sesión manual de Edge CDP y el resolver
de perfiles compartido. Conserva EN-01.3, la extracción nativa completa
sujeta a sus guardas técnicas y el OCR selectivo.

| Presupuesto | Límite |
|---|---:|
| Ventana de publicación | 30 días, hora de Bogotá |
| Feed de descubrimiento | 8 páginas de 30 filas, hasta 240 filas antes de deduplicar |
| Candidatos seleccionados | Hasta 15, sin selección manual ni relleno |
| Inventario | Hasta 10 páginas por proceso con el mecanismo existente, sujeto al presupuesto global |
| Descargas SECOP | 24 intentos, hasta 3 por proceso, máximo 10 MiB por PDF |
| Extracción nativa | Sin tope por número de páginas. Se mantienen 12 s por lector, 512 MiB de memoria, 2 millones de caracteres y 10.000 fragmentos por PDF |
| OCR | Hasta 2 páginas por PDF y 48 por corrida, sujeto a indicios y presupuesto. Hasta 6 s por página y 14 s de procesamiento OCR por PDF |
| Red | 200 créditos, incluidos validación de sesión, feed, inventarios y reservas para descargar |
| Tiempo de ejecución | 720 s de presupuesto operativo. El runner deja margen antes de iniciar solicitudes o descargas |
| IA generativa | 0 llamadas |

Los dos smoke usaron 46 créditos cada uno y duraron 45,125 s y 44,609 s.
Cada uno consultó cuatro páginas de feed e inventarió cinco procesos. Para
dimensionar la ampliación, 2 créditos de preflight + 8 de feed + 30 de
inventarios a dos páginas por proceso + 144 para 24 intentos de descarga a
seis créditos por intento suman 184. Los 16 restantes dan margen para
inventarios más largos. Los 720 s cubren el trabajo serial adicional, la
pausa entre operaciones y la lectura completa y OCR eventual. Los valores
son topes operativos y no una previsión de consumo. El tope de 10 MiB deja
hasta 240 MiB de PDF en disco si los 24 intentos producen archivos del tamaño
máximo, más los artefactos y el espacio temporal del extractor.

### Muestreo y progresión documental

1. Usar la paginación y deduplicación actuales. Aplicar la pertinencia
   comercial y la ventana temporal ya configuradas. Seleccionar procesos SECOP
   II con inventario disponible, primero abiertos y después de vigencia
   indeterminada, con su estado explícito. Excluir cerrados. Dentro del mismo
   rango, alternar departamentos y seguir la prioridad comercial existente.
2. Reservar un primer intento por cada proceso pendiente, mientras alcance el
   presupuesto. Ordenar los PDF por rol y versión visible, con invitaciones o
   pliegos rectores primero y adendas antes de anexos. El segundo intento
   ordinario puede usar un rector o una alternativa si hace falta. Reservar
   hasta cuatro intentos adicionales del total para corroborar ausencias
   explícitas.
3. Si EN-01.3 encuentra una exigencia general aplicable, guardar su evidencia,
   el motivo de parada y la cobertura pendiente. Despriorizar comercialmente
   incluso si la conclusión formal requiere corroboración. Una contradicción,
   una remisión relevante o una adenda o rector identificado pendiente bloquean
   la parada comercial por exigencia según EN-01.3.
4. Si se detecta ausencia explícita, subir el caso en la cola y buscar los PDF
   pertinentes que queden dentro de los límites, priorizando rectores, adendas
   y anexos habilitantes, de experiencia o estudios previos. Un formato auxiliar
   por sí solo no basta. Si hay silencio y no quedan rectores elegibles, dejar
   el caso como secundario. Una conclusión formal de ausencia requiere
   corroboración suficiente.
5. Conservar localmente hasta tres casos despriorizados para revisión humana,
   favoreciendo departamentos distintos. Guardar referencia, documento, página,
   fragmento, razón de parada y cobertura pendiente.

### Comando tras autorización

Desde la raíz del worktree experimental, con la pestaña de contratos abierta en
el Edge CDP dedicado y con el perfil configurado por el mecanismo compartido:

```powershell
$spikePython = if (Test-Path '.\backend\.venv\Scripts\python.exe') {
    (Resolve-Path '.\backend\.venv\Scripts\python.exe').Path
} else {
    (Resolve-Path '..\COMPRAS PUBLICAS\backend\.venv\Scripts\python.exe').Path
}
$env:PYTHONPATH = (Resolve-Path '.\backend\src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython '.\backend\scripts\eureka_nacional_en01.py' --exploratory `
  --processes 15 --recent-days 30 --discovery-pages 8 --documents 24 --ocr-pages 2 `
  --cdp-url 'http://127.0.0.1:9232' --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

Usar la precedencia `--profile-id`, `LICITACIONES_PROFILE_ID` del entorno o
`backend/.env`, y error si falta. Los valores por defecto del modo smoke y su
presupuesto de 60 créditos se conservan.

### Resultados y límites de interpretación

Registrar filas, únicos, candidatos comerciales, elegibles, seleccionados y
analizados, intentos y rectores descargados, bytes, páginas nativas, OCR y
páginas pendientes. Informar requisitos y ausencias explícitas por proceso,
silencio, contradicciones, no resueltos, clasificación formal, prioridad
comercial y sus motivos de parada, tiempo total, tiempo de extracción, CPU del
coordinador y de lectores nativos, y créditos consumidos. Estos datos quedan
en `.local/eureka-nacional-spike/`. Publicar solo agregados.

El feed puede repetir páginas, entregar menos candidatos elegibles o
agotarse antes de las ocho páginas. Los valores `count` no determinan el
tamaño del universo. Los inventarios paginados, PDF fuera de límites o adendas
sin cubrir pueden consumir presupuesto o dejar casos pendientes. La
corroboración depende de los nombres y del formato de los anexos disponibles.
El uso de complementos sigue el orden de procesos y la reserva de intentos.
Ni el número de ausencias ni la cobertura geográfica observada se asumirán por
adelantado. La muestra será exploratoria y no representativa de Colombia.


## EN-01.4 · Resultados de la primera corrida exploratoria

Se ejecutó una vez el 23 de noviembre de 2026 con el runner publicado en
`2de3a32`. Pasó la validación del perfil compartido y el endpoint aceptó
el filtro de 1.130 ubicaciones. El runner terminó con salida `2`
(parcial por tres PDF que superaron el umbral de 10 MiB). Los 15 procesos
seleccionados se analizaron. No se repitió la corrida.

### Embudo y cobertura

| Tramo | Resultado |
|---|---:|
| Páginas del feed | 8 de 8, 30 filas cada una |
| Filas / únicos / duplicados | 240 / 240 / 0 |
| Departamentos observados / seleccionados según la fuente | 31 / 9 |
| Candidatos en el perfil comercial | 37 |
| Con inventario elegible / seleccionados / analizados | 22 / 15 / 15 |
| Categorías comerciales representadas en la selección | 11 de 21 |
| Inventarios / documentos registrados | 15 / 111 |
| Intentos de descarga / descargas exitosas / rectores descargados | 20 / 17 / 12 |
| PDF con cobertura completa / con algún texto | 15 / 16 |
| Páginas informadas / con texto nativo / con cobertura útil | 651 / 641 / 640 |
| Páginas pendientes / intentos de OCR | 11 / 0 |

Los valores `count` fueron 31, 61, 91, 121, 151, 181, 211 y 241. La
paginación se detuvo por presupuesto de feed. Los 203 registros que no
pasaron el perfil comercial se distribuyeron en 135 fuera del perfil,
60 de servicio principal, cinco de bien poco claro, dos de salud compleja
y uno de vehículos completos. Entre los 37 candidatos comerciales,
15 quedaron fuera por capacidad de inventario de la fuente y siete elegibles
quedaron fuera del cupo. Los 15 seleccionados figuraban abiertos en la fuente.
Cinco coincidían con el segundo smoke y diez eran adicionales a esa muestra.
El valor de `count` y esta selección no permiten estimar el universo nacional.

Los tres intentos fallidos por tamaño fueron dos invitaciones y un estudio
previo. No hubo errores técnicos de extracción. Las once páginas con texto
nativo insuficiente quedaron pendientes porque la política OCR no seleccionó
ninguna. Un archivo titulado como pliego final fue excluido por tener una
portada que lo identificaba como proyecto de pliego.

### Decisión formal y señales comerciales

| Resultado | Casos |
|---|---:|
| Experiencia exigida, formalmente resuelta | 1 |
| Ausencia confirmada / ausencia explícita identificada | 0 / 0 |
| Formalmente ambiguos / sin resolver | 3 / 11 |
| Exigencias explícitas detectadas en bruto / procesos con detecciones | 13 / 9 |
| Exigencia aplicable y despriorizada comercialmente | 7 |
| Silencio para revisión / alcance limitado o ambiguo / insuficiencia | 3 / 3 / 2 |
| Contradicciones detectadas / candidatos favorables | 0 / 0 |
| Casos despriorizados guardados para revisión | 3 |

La salida automática detuvo el análisis documental en seis casos por
exigencia aplicable y en uno por conclusión formal. Tres pararon en silencio
secundario y cinco por el cupo ordinario. No se usó la reserva de intentos de
corroboración porque no se detectaron ausencias explícitas.

Un cotejo posterior de los PDF locales encontró cláusulas de experiencia
en los tres silencios del runner. Dos se expresaban con un imperativo o
una construcción indirecta y una estaba en una tabla de requisitos
diferenciales por tamaño empresarial. Se conserva la salida automática
y se registran estas omisiones por separado. Las detecciones en bruto
también requieren revisión, porque pueden incluir requisitos de experiencia
del personal, además de los del oferente.

### Costo y siguiente incremento

Se procesaron 17.971.247 bytes descargados. La corrida tomó 179,141 s,
con 65,814 s acumulados de extracción, 55,563 s de CPU de lectores nativos y
10,906 s de CPU del coordinador. Consumió 160 créditos, cero páginas OCR y
cero llamadas de IA. El promedio global fue 10,67 créditos, 11,94 s de
ejecución y 4,43 s de CPU registrada por proceso analizado. No hay costo
unitario por candidato favorable porque el denominador fue cero.

Para el siguiente incremento, convertir en regresiones offline los tres
silencios cotejados y el requisito del personal, medir su efecto con los
rectores ya guardados y conservar las comprobaciones sobre falsos positivos
de ausencia. Verificar la versión cuando título y portada discrepen. En los
casos bloqueados por tamaño, priorizar alternativas rectoras ya inventariadas
dentro del presupuesto aprobado. La corrida no justifica cambiar los topes ni
hacer inferencias estadísticas sobre Colombia.

Los PDF, los fragmentos por página, la cola y la muestra de auditoría quedan
en `.local/eureka-nacional-spike/en01-le73ddhz/`. Una nueva corrida real
requiere autorización.


## EN-01.4 · Corrección offline de los silencios documentales

Se revisaron las páginas objetivo y los PDF guardados de la corrida
exploratoria. La salida original se conserva como línea base. Se agregaron
tres regresiones con fragmentos reales y se conservaron los cuatro estados
formales y la prioridad comercial independiente.

| Patrón observado | Causa de la omisión | Regla aplicada y efecto |
|---|---|---|
| Imperativo en dos apartados de experiencia | El encabezado repetido de página quedó unido al primer imperativo. La regla no reconocía «aportar» como obligación. | Separar la línea de obligación y reconocer el imperativo cuando identifica experiencia general o específica y una cantidad de contratos. Dos exigencias generales del oferente. |
| Exigencia indirecta dentro de una sección de experiencia | El verbo «exigir» aparecía en una construcción indirecta con una omisión ortográfica. | Reconocer esa construcción bajo un encabezado explícito de experiencia cuando exige al oferente acreditar contratos. Una exigencia general del oferente. |
| Tabla de acreditación por tamaño empresarial | El encabezado contenía «experiencia» y las filas solo especificaban qué comprobantes anexar. | Mantener el contexto del encabezado para las filas, conservar la página y registrar ambas obligaciones como alcance limitado. Las notas de la página siguiente mantienen sus condiciones propias. |

Los tres casos partían de `not_resolved` y silencio para revisión. En el
replay, dos quedan con exigencia aplicable y estado formal `not_resolved`
por cobertura documental pendiente. El tercero queda
`experience_ambiguous` por alcance diferenciado y pasa a revisión de
condición limitada. Sus dos filas cuentan como detecciones de exigencia
de alcance limitado y no sustentan por sí solas una obligación general.
La clasificación y la prioridad de los otros 12 procesos no cambiaron.

| Métrica | Salida original | Replay offline |
|---|---:|---:|
| Silencios documentales | 3 | 0 |
| Detecciones brutas de exigencia | 13 | 18 |
| Prioridad de exigencia aplicable | 7 | 9 |
| Prioridad limitada o ambigua | 3 | 4 |
| Prioridad de insuficiencia | 2 | 2 |
| Formalmente resueltos / pendientes | 1 / 14 | 1 / 14 |
| Formalmente ambiguos / sin resolver | 3 / 11 | 4 / 10 |
| Ausencias explícitas / confirmadas en esta muestra | 0 / 0 | 0 / 0 |

Los cuatro controles históricos abarcaron cinco PDF y 82 páginas. Las tres
señales favorables conservaron evidencia y prioridad sin confirmación formal.
Ambas invitaciones del cuarto control mantuvieron silencio y remisiones
al reglamento. La revisión página por página no encontró detecciones nuevas
ni evidencia modificada en los controles. Pasaron 198 pruebas offline.
El replay procesó 17 PDF con 641 páginas de texto nativo y cero consultas
CDP, descargas, OCR o llamadas de IA.

Para la siguiente exploración se recomienda mantener hasta 15 procesos en
30 días, ocho páginas de 30 filas, 24 intentos y tres por proceso, 10 MiB
por PDF, OCR selectivo de dos páginas por PDF y 48 en total, 200 créditos,
720 s y cero llamadas de IA. Mantener la extracción nativa sin tope de
páginas por cantidad. La última ejecución usó 20 intentos, 160 créditos
y 179,141 s. Hay margen operativo para comprobar el ajuste en otra muestra
sin elevar los topes. La regla de tabla cubre el encabezado y las filas
observados. Otros diseños requieren validación aparte. La exploración
ampliada queda pendiente de autorización.


## EN-01 · Lote exploratorio de procesos nuevos

Se ejecutó una única corrida el 24 de noviembre de 2026 con el clasificador
aceptado en `731e0ac` y el filtro histórico de `29d4afc`. El runner
carga las filas con resultado de cada historial local antes de conectar
CDP y las cruza con el feed por aviso SECOP II `CO1.NTC`. Una referencia
del agregador o una referencia de fase sin aviso comparable no garantiza
la novedad. Esta ejecución cargó 25 resultados históricos correspondientes
a 20 avisos únicos. Se verificó que ninguno reapareció en el feed y que los
15 avisos analizados eran distintos entre sí y del historial. Se mantuvieron
los límites de EN-01.4 y los 1.130 identificadores geográficos.

| Embudo | Resultado |
|---|---:|
| Páginas / registros / únicos / duplicados | 8 / 240 / 240 / 0 |
| Departamentos en el feed / en la muestra | 25 / 8 |
| Candidatos comerciales / elegibles para inventario | 29 / 20 |
| Coincidencias con el historial / identidades no comparables entre elegibles | 0 / 0 |
| Seleccionados / analizados | 15 / 15 |
| Categorías en la muestra | 7 de 21 |
| Inventarios / documentos registrados | 15 / 117 |
| Intentos de descarga / PDF guardados / rectores | 20 / 17 / 8 |
| PDF con algún texto / cobertura completa | 13 / 11 |
| Páginas informadas / con texto nativo / pendientes | 538 / 401 / 137 |
| Páginas OCR intentadas / con recuperación | 3 / 3 |

Los 15 seleccionados figuraban abiertos. Quedaron cinco elegibles fuera
del cupo. De los 29 candidatos comerciales, nueve fueron excluidos por
capacidad de inventario de su fuente. El feed llegó al tope de ocho
páginas; los valores `count` subieron de 31 a 241 y siguen sin determinar
el tamaño del universo. El runner salió con código `2` por tres intentos
de descarga que superaron 10 MiB. No hubo fallos técnicos de extracción.

| Resultado automático | Casos |
|---|---:|
| Experiencia exigida / ausencia confirmada | 0 / 0 |
| Formalmente ambiguos / sin resolver | 6 / 9 |
| Detecciones brutas de exigencia / procesos con detecciones | 8 / 5 |
| Casos despriorizados por exigencia aplicable | 0 |
| Ausencia explícita / contradicciones | 0 / 0 |
| Prioridad de condición limitada / insuficiencia / silencio | 6 / 8 / 1 |

El cotejo offline de las 20 páginas del rector del único silencio encontró
en la pág. 12, numeral 5.5, una exigencia de mínimo dos contratos de objeto
igual o similar, cada uno por al menos el 100 % del presupuesto oficial.
La obligación está entre paréntesis en un encabezado numerado. Se conserva
la salida automática y se registra el hallazgo aparte. Hubo cero silencios
corroborados y cero candidatos favorables. Las detecciones de exigencia
quedaron como evidencia trazable de casos con condiciones, remisiones o
cobertura pendiente. No se reejecutó el runner ni se ajustó el clasificador
en este lote.

La corrida usó **160 créditos, 185,250 s, tres páginas OCR y cero llamadas
de IA**. Los 17 PDF sumaron 21.258.244 bytes. La extracción acumuló 67,359 s;
la CPU fue 49,484 s en lectores nativos y 12,297 s en el coordinador. El
promedio global fue 10,67 créditos y 12,35 s transcurridos por proceso.
El costo unitario por candidato favorable queda indefinido. Se verificaron
los topes y el solapamiento con los historiales en los artefactos locales.
El resultado por proceso, la cobertura y la evidencia quedan en
`.local/eureka-nacional-spike/en01-hb4_beb5/`. Se publican cifras agregadas.

`--exclude-analyzed-from CORRIDA` puede repetirse con cada nombre local.
Se probó offline con los historiales de los dos smoke y la primera
exploratoria. Pasaron 203 pruebas antes de la ejecución. Tras la corrida,
se comprobó con cinco pruebas focalizadas que la opción también acepta
los nombres con guion bajo generados por el runner. Incluir el historial
de este lote en una futura selección excluiría 35 avisos únicos. Una
nueva corrida real requiere autorización.


## EN-01 · Cotejo focalizado del segundo lote

El único silencio automático correspondía a un requisito habilitante
incluido entre paréntesis en un encabezado numerado. El segmentador unía
ese encabezado, que se extendía por varias líneas, a la tabla anterior.
Además, la obligación se expresaba como un mínimo de contratos, sin
uno de los verbos reconocidos. La corrección separa el encabezado
explícito de experiencia mínima para participar y reconoce el mínimo
de contratos cuyo objeto se especifica allí. Conserva página y sección.
No generaliza la regla a una mención de experiencia, a un ejemplo o
a una modalidad opcional.

El replay sobre los 17 PDF locales conservó la clasificación y la
prioridad de los otros 14 procesos. El caso corregido pasó de silencio
a exigencia aplicable en prioridad comercial y conservó `not_resolved`
por cobertura documental pendiente. Las detecciones brutas de exigencia
pasaron de ocho en cinco procesos a nueve en seis. La clasificación
formal se mantuvo en seis ambiguos y nueve sin resolver, con cero
ausencias explícitas o confirmadas. El replay empleó 84,875 s, con el
mismo OCR selectivo, cero créditos de red y cero IA.

### Cotejo de las cinco detecciones originales

| Evidencia observada | Motivo de la prioridad que se conservó |
|---|---|
| Dos contratos de confección o suministro en un rector completo | La sección genérica no identificó alcance general en la regla vigente. Una nota remite a otro numeral de la misma invitación y activa la comprobación de dependencia. |
| Dos contratos generales y dos distintos para experiencia específica | El rector tenía alcance general reconocido, pero le faltaba una página. Además, el estudio previo superó 10 MiB. |
| Hasta tres certificaciones para equipo de protección personal | Es una obligación de acreditación. El encabezado registrado no establece el alcance general en la regla y el expediente distingue reglas según el tipo de empresa. |
| El oferente deberá acreditar experiencia y podrá hacerlo con un máximo de dos contratos | «Podrá» indica el medio previsto para acreditar. El encabezado no tipificó el alcance general y el documento contiene otras condiciones de aplicación limitada. |
| Inscripción en el RUP de los contratos relacionados en un formulario | Es una condición específica de acreditación. El rector remite a estudios previos pendientes y no se amplió esta señal a una obligación general confirmada. |

### Cobertura documental y comprobación OCR

Siete de los 15 procesos quedaron sin rector descargado. De los ocho
rectores guardados, seis tuvieron cobertura completa y dos parcial.
En cinco inventarios no se identificó un rector por título, aunque uno
contenía una posible invitación con nombre truncado. Un rector identificado
era DOCX y quedó fuera de la selección PDF. Otro rector identificado
superó 10 MiB. Los otros dos archivos que superaron el umbral fueron
un estudio previo y un paquete precontractual de rol indeterminado.

Las 137 páginas pendientes pertenecen a seis PDF. Todas tenían texto
nativo insuficiente y quedaron fuera de la selección OCR. Se concentraron
en un estudio previo de 55 páginas, otro de 38 y un rector escaneado con
35 páginas pendientes. Las nueve restantes pertenecían a un CDP, un
conjunto de cotizaciones con anexos y una página de índice de un rector
mixto. No hubo interrupciones de extracción que explicaran ese faltante.

La prueba focalizada recuperó texto útil en cuatro de cuatro páginas
locales, en 30,172 s. Conservar conjuntamente esa evidencia reduciría
las pendientes a 133 y completaría las páginas del rector mixto. Su
página recuperada era un índice. La muestra de páginas no acredita una
tasa extrapolable al resto ni modifica las clasificaciones del replay.
Se conservaron las guardas de tiempo, tamaño y calidad y el OCR se
ejecutó sobre una página objetivo por PDF en la prueba.

Pasaron 207 pruebas offline. Los cinco PDF de control conservaron
sus afirmaciones, páginas y prioridades. Las tres señales favorables
siguen pendientes de confirmación formal y los controles de silencio
condicionado conservan sus remisiones. Los resultados y la prueba OCR
quedan en `.local/`. No hubo CDP, descargas SECOP ni otra corrida real.

Para la siguiente exploración, mantener ocho páginas de feed por defecto
y considerar hasta dos adicionales, previa autorización, solo si la
exclusión histórica deja menos de 15 candidatos elegibles. Agregarían
hasta dos créditos de feed dentro de los mismos 200 y 720 s, con los
mismos límites documentales. Priorizar la cobertura antes de aumentar
la muestra. Probar el ranking de títulos truncados con validación por
portada y la reutilización del lector DOCX aislado para rectores
identificados. Para escaneados, usar un índice, un encabezado vecino o
la página siguiente a una portada útil para escoger el segundo cupo OCR.
Estas son propuestas para un incremento posterior. Las guardas siguen
vigentes.


## EN-01 · Incremento de cobertura documental

Se contrastaron los siete inventarios sin rector descargado y los dos
rectores parciales del segundo lote. Los metadatos permiten colocar dos
archivos adicionales al frente de sus inventarios. Uno es una invitación
DOCX que antes quedaba fuera por formato. El otro exhibe un título
truncado de invitación. El título truncado da prioridad de selección y el
rol queda pendiente hasta validarlo en portada. Una portada que identifica
un proyecto, aviso, formato, estudio o solicitud de información conserva
su función documental. En particular, la solicitud de información a
proveedores quedó identificada en una portada cuyo título ocupaba dos
líneas. Cada archivo conserva el origen del rol y su unidad de cobertura.

| Comprobación sobre los siete casos sin rector | Antes | Después |
|---|---:|---:|
| Nuevos candidatos a rector que encabezan el inventario | 0 | 2 |
| Rectores adicionales confirmados en PDF o DOCX local | 0 | 0 |
| Archivo de rol ambiguo identificado como solicitud de información | 0 | 1 |

Los dos candidatos nuevos siguen pendientes de descarga. Entre los
otros cinco casos, dos archivos excedieron la guarda de 10 MiB y dos
inventarios solo tenían proyectos de pliego con sus soportes. El quinto
era la solicitud de información a proveedores. Para el DOCX rector se
reutiliza el lector aislado existente. Una prueba con un DOCX generado
verificó la extracción de párrafos y celdas y sus localizadores sin
asignar páginas ficticias. Los archivos DOCX se limitan a candidatos
rectores. El alcance validado comprende texto de párrafos y tablas.

El OCR prioriza referencias explícitas a páginas y entradas de índice
de experiencia o requisitos habilitantes, seguidas de vecinos de
encabezados pertinentes. Solo se eligen páginas cuyo texto nativo es
insuficiente. En un rector completamente ilegible se limita la alternativa
a portada y continuación. El índice sirve como pista para seleccionar
páginas. La evidencia conserva la página física extraída.

| Cobertura sobre los mismos 17 PDF | Antes | Después |
|---|---:|---:|
| Páginas con texto nativo | 401 | 401 |
| Páginas OCR recuperadas | 3 | 4 |
| Páginas útiles | 401 | 402 |
| Páginas pendientes | 137 | 136 |
| PDF con cobertura completa | 11 | 11 |

En el rector completamente escaneado se recuperaron las páginas 1 y 2,
frente a solo la 1. En el rector mixto, la página de índice con referencias
de experiencia (2) sustituyó la página 1 en el cupo de OCR y se conservó
la 3. Sigue faltando una página del rector mixto. Los 15 casos conservaron
su clasificación y prioridad. El límite permanece en dos páginas de OCR
por PDF y 48 por corrida. Los resultados locales no implican que el
resto de las páginas pendientes deba procesarse indiscriminadamente.

### Parámetros preparados para la corrida nacional

El runner y el filtro histórico se prepararon para una muestra
acotada. Se verifican 35 avisos históricos y se mantienen el resolver
compartido, las 1.130 ubicaciones, las 21 categorías, el clasificador y sus
cuatro estados. Las dos novedades de inventario requieren validación
operativa cuando se disponga de sus archivos.

Mantener hasta 15 procesos en 30 días, ocho páginas de 30 filas, 24
intentos de descarga y tres por proceso, 10 MiB por archivo, extracción
nativa completa con guardas, OCR selectivo de dos páginas por PDF y
48 en total, 200 créditos, 720 s y cero llamadas de IA. La opción
`--conditional-extra-feed-pages 2` permite una novena y una décima
página solo al seguir por debajo de los 15 elegibles después de excluir el
historial. Se evalúa de nuevo el cupo tras la novena. Se respetan los
finales de paginación de la fuente y los mismos topes de red y tiempo.
La opción está desactivada por defecto.

Comando preparado para después de la autorización, desde la raíz del worktree
con el intérprete y `PYTHONPATH` del plan anterior:

```powershell
& $spikePython '.\backend\scripts\eureka_nacional_en01.py' --exploratory `
  --processes 15 --recent-days 30 --discovery-pages 8 --conditional-extra-feed-pages 2 `
  --documents 24 --ocr-pages 2 `
  --exclude-analyzed-from en01-ms7c7hyc --exclude-analyzed-from en01-ifqy1v2y `
  --exclude-analyzed-from en01-le73ddhz --exclude-analyzed-from en01-hb4_beb5 `
  --cdp-url 'http://127.0.0.1:9232' --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

Pasaron 217 pruebas offline, con artefactos locales y feed simulado.
El replay detallado está en `.local/eureka-nacional-spike/pdf-replay-1hupshc1/`.
No hubo consultas CDP, descargas SECOP, IA ni una nueva corrida nacional.


## EN-01 · Corrida nacional con extensión condicional del feed

Se ejecutó una vez el 24 de noviembre de 2026 con el runner de `84eae31`
y cuatro historiales locales. Pasó el preflight CDP con el resolver
compartido y se aplicó el filtro de 1.130 ubicaciones y 21 categorías. Al
faltar candidatos elegibles después de aplicar los historiales, el runner
utilizó la novena y la décima página. Quedaron 14 procesos elegibles y
se analizaron todos. Las referencias SECOP examinadas eran nuevas
respecto de los 35 avisos históricos.

| Embudo y cobertura | Resultado |
|---|---:|
| Feed y registros | 8 páginas base + 2 condicionales, 300 filas |
| Únicos / duplicados | 299 / 1 |
| Departamentos observados / en la muestra | 28 / 7 |
| Candidatos comerciales / elegibles antes del historial | 37 / 26 |
| Coincidencias históricas excluidas / elegibles nuevos | 12 / 14 |
| Seleccionados / analizados | 14 / 14 |
| Abiertos / vigencia indeterminada según la fuente | 9 / 5 |
| Categorías en la muestra | 9 de 21 |
| Inventarios / documentos registrados | 14 / 87 |
| Intentos / descargas exitosas / rectores reconocidos | 19 / 16 / 8 |
| Archivos con cobertura completa / con texto | 14 / 15 |
| Páginas informadas / con texto nativo / útiles / pendientes | 414 / 372 / 373 / 41 |
| Páginas OCR intentadas / recuperadas | 1 / 1 |

De los 299 registros únicos, 262 quedaron fuera del perfil comercial:
177 fuera del perfil, 71 con servicio principal, 13 con objeto de bien
poco claro y uno de obra civil. De los 37 candidatos, 11 quedaron fuera
por capacidad de inventario y 12 por coincidencia histórica. Los
valores del campo `count` avanzaron de 31 a 301 en incrementos de 30;
la paginación terminó por presupuesto de feed. Esta muestra no permite
estimar el universo nacional.

Los 16 archivos guardados fueron PDF. Los DOCX inventariados eran
auxiliares y no se seleccionaron como rectores. La prueba operativa con
un DOCX rector sigue pendiente. Un archivo con título concatenado
permaneció de rol desconocido. La portada permitió descartar otro
archivo como cotización. Seis procesos quedaron sin rector reconocido
descargado y otro tuvo un rector parcial. Las 41 páginas pendientes se
concentraron en un análisis de sector escaneado (33) y un rector (8).
El estado de ejecución fue parcial por el tamaño de la muestra y tres
intentos superiores a 10 MiB. Hubo cero errores técnicos de extracción.

### Resultado formal y prioridad comercial

| Resultado | Casos |
|---|---:|
| Experiencia exigida formalmente / ausencia confirmada | 0 / 0 |
| Formalmente ambiguos / sin resolver | 2 / 12 |
| Detecciones brutas de exigencia / procesos con detecciones | 13 / 3 |
| Exigencia aplicable despriorizada / contradicciones detectadas | 0 / 0 |
| Prioridad limitada o ambigua / insuficiencia / silencio automático | 2 / 8 / 4 |
| Ausencia explícita / candidatos favorables | 0 / 0 |

El cotejo posterior encontró obligaciones de acreditar experiencia en
los cuatro rectores clasificados como silencio automático. Se observaron
instrucciones con «debe aportar», un imperativo de certificación y
cláusulas vinculadas a un formulario o tabla. Los fragmentos y páginas
quedaron en un registro offline separado. Se preservó la salida
automática y hubo cero silencios corroborados entre los cuatro
candidatos así marcados. Hubo exigencias en los PDF leídos, faltantes
de cobertura y omisiones de reconocimiento. Los 14 casos permanecen
pendientes de decisión formal. La reserva para corroborar ausencias
explícitas no se utilizó.

### Costo y evidencia local

Se consumieron 154 créditos y 216,094 s, con cero llamadas de IA.
El promedio fue 11,00 créditos y 15,44 s transcurridos por proceso.
Las descargas sumaron 18.713.649 bytes. El extractor acumuló 50,530 s,
con 41,266 s de CPU de lectores nativos y 14,156 s de CPU del coordinador.
El costo unitario por candidato favorable queda indefinido al ser cero
el número de candidatos. No se repitió la corrida.

El detalle de los procesos, la evidencia y el cotejo de silencios
permanecen en `.local/eureka-nacional-spike/en01-jocj50yr/`.


## EN-01 · Cuatro omisiones y manejo documental acotado

Se cotejaron los cuatro silencios del lote anterior con los mismos
PDF, páginas e inventarios. La regla ahora reconoce el mandato de
aportar contratos en una sección de condiciones de experiencia,
el encabezado de experiencia del oferente que cita un formulario
numerado, el imperativo de certificar contratos bajo un apartado
rotulado por letra y el mandato de aportar evidencia remitida a la
tabla anterior. Esta última referencia sigue registrada como dependencia
y mantiene el caso en revisión ambigua.

Las detecciones de exigencia pasaron de **13 en tres procesos a 17 en
siete**. Tres silencios pasaron a prioridad comercial de exigencia
aplicable y conservaron `not_resolved`. El cuarto pasó a
`experience_ambiguous` por la remisión a la tabla. El total formal
quedó en tres ambiguos, once sin resolver y cero resueltos, con cero
ausencias explícitas. El replay de los 16 PDF conservó 113 de 121
páginas de un rector antes de alcanzar la guarda de tiempo. Esa
extracción parcial dejó ocho páginas adicionales pendientes frente
a la corrida original. La guarda y el texto recuperado se conservaron.

Se agregó una pista de selección para un título concatenado de
invitación. La portada con palabras partidas permitió confirmar el
rector y distinguir el estudio previo asociado. El nuevo rector
mantiene un silencio automático pendiente de revisión. Su texto
combina una facultad de solicitar certificaciones y otra mención de
acreditar un contrato. El reconocimiento de portada acredita el rol,
mientras la ambigüedad de las cláusulas sigue abierta.

EN-01 reutiliza el lector aislado de DOCX tanto para rectores como
para adendas identificadas. Se conservan los localizadores de párrafo
y celda. Los 16 archivos del lote eran PDF, por lo que la validación
DOCX sigue siendo offline. El tope predeterminado continúa en **10 MiB**.
El modo exploratorio admite `--governing-pdf-max-mib 16` únicamente
para un PDF rector o candidato a rector. Se aplica al intento
original y a su extracción, con los mismos créditos, tiempos, memoria,
OCR y cantidad de intentos. El máximo teórico para 24 archivos de ese
tamaño es 384 MiB de PDF. El resto conserva el tope de 10 MiB. Un PDF
local de prueba de más de 11 MiB fue rechazado con la configuración
base y leído con el tope optativo. Los archivos reales rechazados
por tamaño no están en el almacenamiento local y su recuperabilidad
sigue sin medir.

Pasaron 224 pruebas offline. Pore, El Plato, La Capilla (ventiladores)
y las dos invitaciones de Chivatá conservaron sus estados, prioridades
y fragmentos de control. El replay parcial se guarda en
`.local/eureka-nacional-spike/pdf-replay-tfk59178/`. No hubo CDP,
descargas, IA ni otra corrida nacional.

Para la siguiente exploración autorizada, mantener hasta 15 procesos
nuevos y los presupuestos vigentes, con los 49 avisos de los cinco
historiales en la exclusión. Conservar el perfil comercial, la
geografía y el descubrimiento actuales. Si se autoriza probar el tope
optativo, medir rectores adicionales recuperados, bytes y paradas de
extracción. Mantener la salida formal, el criterio comercial y la
evidencia de cobertura para comparar lotes.

## Hipótesis exploratoria futura · Modelo de Propensión a No Exigir Experiencia (MPNE)

La hipótesis plantea explorar si algunos atributos documentados aparecen
con distinta frecuencia en procesos con y sin exigencia de experiencia.
El punto de partida son cinco observaciones favorables de una búsqueda
manual previamente filtrada: El Plato, La Capilla (ventiladores),
Chivatá 21, Chivatá 22 y Pore. Corresponden a cuatro entidades independientes.
Los cinco presupuestos reportados están por debajo de COP 20 millones;
las observaciones corresponden a mínima cuantía o régimen especial, con
suministro o compraventa de bienes, y entidades de tipo alcaldía,
institución educativa o personería. La selección manual está sesgada,
carece de denominador representativo y no permite inferir probabilidades.
Los dos casos de Chivatá conservan el silencio condicionado y la remisión
al reglamento en el resultado documental. La observación manual y la
conclusión formal se registran por separado.

| Variable exploratoria | Registro con los artefactos existentes |
|---|---|
| Presupuesto, modalidad y fecha de publicación | Conservar el valor de la fuente en `processes.json` y su procedencia. Si la fuente no informa un valor interpretable, registrar el faltante. |
| Tipo de contrato y tipo de entidad | Usar la declaración explícita si existe. Si se deducen del objeto o del nombre de la entidad, rotularlos como inferencia y conservar el texto que la sustenta. |
| Categoría comercial del bien | Conservar la categoría y el método del perfil comercial actual. La etiqueta del prefiltro es una clasificación derivada. |
| Plazo de ejecución | Registrar plazo y unidad cuando el documento los indique. La fecha límite de oferta no es el plazo de ejecución. |
| Pago y lugar de entrega | Registrar únicamente lo que conste en el texto extraído, con documento y localizador. Mantener faltantes en los demás casos. |

Aplicar el mismo registro a los procesos con experiencia exigida, a los
favorables y a los pendientes. Distinguir observaciones de fuente,
inferencias y faltantes. Mantener el aviso SECOP único, el vínculo a la
corrida y las afirmaciones con su documento, página o localizador.
Para una evaluación futura, usar etiquetas formales corroboradas y
conservar aparte los casos ambiguos, provisionales y sin resolver.
Agrupar por entidad al evaluar para tener en cuenta casos de una misma
institución. La recolección reutiliza las salidas actuales, sin
infraestructura adicional.

MPNE queda como hipótesis registrada. El presupuesto, la modalidad,
la entidad, el tipo de contrato y las categorías no cambian el
descubrimiento ni la prioridad de selección. No hay un puntaje
predictivo, entrenamiento ni integración de IA. La comparación se hará
cuando haya suficientes casos positivos y negativos con evidencia.


## EN-01 · Corrida con piloto de 16 MiB para PDF rectores

Se ejecutó una vez el 24 de noviembre de 2026 con el runner de `938f038`,
el resolver compartido de perfil y la exclusión de 49 avisos históricos.
La sesión CDP permitió consultar el feed y los inventarios con el filtro
de 1.130 ubicaciones y el perfil de 21 categorías. Se usaron las dos
páginas adicionales porque faltaban candidatos elegibles. El runner
cerró la selección con 12 procesos nuevos.

| Embudo | Resultado |
|---|---:|
| Feed y filas | 8 páginas iniciales + 2 condicionales, 300 filas |
| Avisos únicos / duplicados | 300 / 0 |
| Departamentos del feed / en la muestra | 31 / 7 |
| Candidatos comerciales / elegibles antes del historial | 42 / 28 |
| Coincidencias históricas excluidas / elegibles nuevos | 16 / 12 |
| Seleccionados / con inventario | 12 / 12 |
| Abiertos / vigencia indeterminada | 11 / 1 |
| Categorías representadas | 7 |
| Documentos inventariados | 73 |

Los valores `count` fueron de 31 a 301 en incrementos de 30. La
paginación se detuvo por el presupuesto de diez páginas. Se excluyeron
258 avisos antes de la elegibilidad documental por perfil, servicio
principal u objeto poco claro. Entre los 42 candidatos comerciales,
14 quedaron fuera por capacidad de inventario y 16 por coincidencia
histórica. Los 12 seleccionados no se solaparon con el historial.

### Adquisición, piloto y decisión comercial

| Intentos | Límite | Resultado |
|---|---:|---|
| 10 PDF rectores por título | 16 MiB | 10 `http_error`, 0 descargas |
| 10 PDF restantes | 10 MiB | 10 `http_error`, 0 descargas |

El artefacto conserva el código genérico `http_error` y carece del
estado HTTP específico. No se registraron rechazos por tamaño. Sin
archivos recibidos no se pudo medir cuántos rectores habría recuperado
el piloto, el tamaño real de los documentos ni su cobertura. Hubo
cero páginas abiertas, cero OCR, cero paradas de extracción por
tiempo y cero DOCX rectores procesados. Los DOCX del inventario eran
auxiliares. La corrida terminó parcial por el tamaño de la muestra y
los 20 errores de descarga.

Los 12 procesos quedaron `not_resolved` formalmente y con prioridad
comercial de evidencia insuficiente. La cobertura pendiente comprende
los documentos del inventario. Hubo cero casos clasificados como silencio,
cero detecciones de exigencia o ausencia explícita, y cero candidatos
favorables. Estas cifras reflejan falta de acceso al texto contractual
en esta corrida. No se alteraron topes ni se repitieron consultas o
descargas fuera del runner.

### Registro exploratorio y costo

Se guardó un registro MPNE local para los 12 procesos. Presupuesto,
modalidad y publicación se conservaron como observaciones de la fuente.
Se conservaron las categorías como etiquetas derivadas del perfil. Se
registraron nueve tipos de entidad y siete tipos de contrato como
inferencias, con tres y cinco faltantes. El plazo de ejecución, el pago
y el lugar de entrega quedaron faltantes en los 12 procesos, dado que
no se obtuvo texto contractual. Cinco presupuestos informados estaban
por debajo de COP 20 millones. Las modalidades fueron ocho de mínima
cuantía, tres de régimen especial y una de selección abreviada por
subasta inversa. Estas cifras describen la muestra y no informan
propensión, porque sus 12 resultados carecen de evidencia contractual.
El registro se generó después de la selección, sin filtros ni puntuación.

Se consumieron 156 créditos en 117,516 s, con 6,938 s de CPU del
coordinador y cero CPU de extracción. Se reservaron 120 créditos para
20 intentos de descarga según el mecanismo vigente. El promedio fue
13 créditos y 9,79 s transcurridos por proceso inventariado. Hubo cero
llamadas de IA. El costo unitario por candidato favorable queda
indefinido. Los inventarios, errores, decisiones y observaciones MPNE
quedan en `.local/eureka-nacional-spike/en01-hsxjhqpg/`.


## EN-01 · Diagnóstico offline de adquisición SECOP

En la corrida del piloto de tamaño se obtuvieron 12 inventarios y los
20 intentos de descarga produjeron `http_error`. Diez fueron PDF rectores
con tope de 16 MiB y diez usaron el tope ordinario de 10 MiB. Se verificaron
cero bytes guardados, cero páginas abiertas y cero errores de extracción.
El archivo de errores solo conserva etapa, código de aplicación e
identificadores internos de proceso y documento. No se encontraron
estados HTTP, excepciones subyacentes, cuerpos ni trazas de redirección
en los artefactos de esa corrida.

El inventario obtiene los documentos mediante
`POST /cliente/contratos/obtener-documentos-proceso` en Licitaciones.info.
Para descargar el binario, el runner llama al `SecopDownloader`, que hace
un GET HTTPS directo con `urllib` a la URL recibida del inventario.
La sesión CDP se usa para el inventario. El GET directo no transfiere
credenciales ni cookies del navegador. En los 20 enlaces archivados se
conservó el host `community.secop.gov.co` y la ruta
`/Public/Archive/RetrieveFile/Index`, con una referencia `DocumentId`.

El adaptador emitía `http_error` cuando `urllib` levantaba un
`HTTPError` distinto de una redirección manejada o cuando la respuesta
obtenida tenía estado distinto de 200. Ambas ramas ocurren antes de
leer el cuerpo del archivo. El tamaño, el transporte, el contenido
HTML recibido con 200 y las redirecciones bloqueadas tienen códigos
distintos. La evidencia apunta a una respuesta HTTP que el GET directo
no pudo aceptar. El estado exacto, la causa de esa respuesta y la
existencia de redirecciones previas siguen indeterminados.

En las cinco corridas previas se guardaron 59 archivos de 69 intentos.
Los diez intentos fallidos de descarga se registraron como `too_large`.
El host, la ruta y la clave de referencia archivados coinciden con los
de la corrida fallida. El adaptador y el mecanismo de inventario no
cambiaron al introducir el piloto. Como el inventario archiva una URL
depurada, los artefactos no permiten comprobar parámetros adicionales
del enlace original si los hubo. No hay evidencia de una regresión del
tope de tamaño o del código de descarga.

### Diagnóstico seguro

El adaptador entrega al runner una traza por intento con etapa, estado
HTTP si existe, tipo de excepción, tipo subyacente de transporte si
existe, medio de contenido y motivo de rechazo. Cada redirección
conserva su estado y clasifica el destino como otra ruta SECOP,
recuperación de archivo, bloqueado o faltante. El medio se normaliza
mediante una lista de tipos conocidos y el resto se marca como
`other`. Se conserva la traza en el inventario y, cuando corresponde,
en el error local. No se incluyen URLs, cuerpos, valores de cabeceras,
cookies, tokens, autorizaciones ni texto de excepciones. No se
modificaron los límites, el resolvedor de perfil ni las reglas de
selección. Pasaron 248 pruebas offline, con respuestas HTTP, transporte,
redirecciones, contenido y sonda simulados.

### Procedimiento de la sonda de un PDF archivado

La selección offline verificó un único PDF rector fallido para la
referencia de Moniquirá `CM-MC-004-2026` en el inventario local. Una
vez autorizada la prueba, ejecutar desde la raíz del worktree con
el intérprete del plan de EN-01:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\backend\src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython '.\backend\scripts\eureka_nacional_download_probe.py' `
  en01-hsxjhqpg --process-code 'CM-MC-004-2026' --attempts 1
```

El comando usa el enlace depurado ya guardado para esa referencia y
no abre CDP, feed ni inventarios. El tope de la sonda es 10 MiB y 12 s
por intento, con las mismas validaciones de destino y un máximo de
seis solicitudes del adaptador por intento, incluidas redirecciones.
El presupuesto de la prueba es de hasta dos intentos de adquisición
sobre el mismo documento. Se recomienda empezar con uno y reservar
el segundo para un dato que siga faltando. La sonda guarda su salida
y el archivo, si se recibe, bajo `.local/`. Si el enlace original
dependía de parámetros descartados al archivar, la prueba solo describe
el enlace público conservado. El resultado se registra en el apartado siguiente.

Para recuperar los documentos de los 12 procesos, conservar sus
avisos y claves de inventario originales. Tras aclarar el estado
HTTP con la sonda, reutilizar los inventarios guardados si los
enlaces siguen siendo válidos. Si es necesario refrescarlos,
consultar únicamente esos 12 inventarios con autorización,
priorizar rectores pendientes y reanudar su análisis con las
guardas vigentes. No se necesita repetir el descubrimiento nacional.


### Resultado de la sonda autorizada en Moniquirá

Se ejecutó un único intento del procedimiento sobre el PDF rector ya
inventariado. Se conservaron los topes de 10 MiB y 12 s. El GET directo
recibió **HTTP 403**, excepción `HTTPError`, en `response_headers`, con
tipo normalizado `text/html` y motivo `http_error`. No hubo redirecciones.
El archivo no se descargó. La traza local guarda exclusivamente los campos
autorizados. Se retiraron de la salida de la sonda el hash y el tiempo
por intento, junto con los campos redundantes. El cambio de registro se
verificó con siete pruebas focalizadas offline.

El hecho confirmado es que el GET directo al enlace archivado fue
denegado al recibir las cabeceras. El enlace no fue utilizable para
descargar el PDF por ese mecanismo en esta prueba. El 403 no identifica
qué política, credencial, estado del enlace o intermediario motivó la
denegación. Tampoco establece que los 20 errores históricos fueran 403.
Un segundo GET idéntico no distinguiría esas explicaciones y no se hizo.

No se justifica actualizar en bloque los enlaces de los 12 inventarios
basándose en este único 403. Para retomarlos con autorización, comprobar
primero el enlace vigente de Moniquirá en su inventario existente y
validar una descarga por el mecanismo de acceso autorizado. Si el
enlace cambió, refrescar solo los inventarios que lo necesiten. Si se
mantiene el 403 también con el enlace vigente, aclarar el acceso antes de
consumir más intentos. Una vez recuperada la descarga, usar los avisos
y las claves ya guardadas y procesar primero los rectores pendientes con
las guardas existentes. No se consultaron el feed ni inventarios, y no
se ejecutó la recuperación de los 12 procesos.


## EN-01 · Alternativa acotada de descarga mediante Edge

En la prueba autorizada de Moniquirá, el enlace de inventario coincidió
con el archivado. Un solo clic desde Edge recibió HTTP 200, sin
redirecciones, y el PDF fue idéntico a la copia manual de 595.065 bytes.
El GET archivado anterior había recibido 403 mediante `urllib`. La
diferencia comprobada fue el contexto del navegador. Esa prueba no
establece cuál de sus propiedades influyó en el resultado.

EN-01 conserva `urllib` como vía principal. El indicador optativo
`--edge-download-fallback` solo considera continuar mediante Edge si
el descargador registra `http_error` con HTTP 403, el tipo esperado
es PDF o DOCX y queda cupo. La alternativa utiliza la URL vigente
entregada por el inventario, valida la ruta SECOP y el
`DocumentId`, y deja los demás parámetros en memoria. La solicitud
se hace desde la pestaña de Contratos de Edge con sus credenciales
administradas por el navegador. Las trazas guardan mecanismo, estado,
etapa y motivo. No registran la URL completa, cookies ni tokens.

El lector alternativo usa un GET de navegador con redirecciones
deshabilitadas y `AbortController`. Acepta una respuesta directa HTTP
200 con tamaño declarado dentro del tope. Si falta el tamaño,
se rechaza la respuesta. Lee el cuerpo por bloques, cancela cuando
supera el tamaño declarado o se agota el plazo y comprueba el formato
antes de publicar. El almacenamiento compartido verifica tamaño,
estructura mínima y hash. El candado de volumen es de 10 MiB por
defecto y respeta el tope ya autorizado para un rector si la corrida
lo habilita. El plazo máximo de la vía Edge es de 12 s. Si se pierde
CDP o no se confirma la cancelación, se suspende Edge para el resto
de la ejecución.

Un intento Edge consume un intento documental adicional y un crédito
del presupuesto existente. El intento directo conserva sus créditos
y ambos cuentan frente a los topes nacionales y por proceso. El
runner registra fallos por documento y detiene la adquisición si hay
tres fallos consecutivos repartidos entre al menos dos procesos.
La alternativa queda **desactivada por defecto**. La descarga
normal de Edge comprobada en Moniquirá no demuestra que SECOP permita
la lectura por Fetch entre orígenes. Si CORS bloquea la respuesta, se
registra el rechazo y no se cambia de mecanismo. El límite de bytes
se aplica a lo leído y almacenado, con cancelación en el navegador.
Los buffers internos de la red del navegador quedan fuera del control
del runner. Si CDP se bloquea, Python puede tardar en recibir el acuse
del temporizador del navegador. Estas limitaciones requieren validar
la alternativa con un piloto autorizado antes de usarla en un lote.

### Reanudación acotada de los 12 procesos

La opción `--resume-inventory-from` utiliza la selección y las claves
guardadas de una corrida local. Omite el discovery y el preflight
que consultaría el feed. Solo refresca inventarios de los procesos
pendientes seleccionados. Los binarios ya guardados se verifican por
hash, tamaño y tipo antes de reutilizarlos. Se conserva el avance
y las resoluciones en un directorio local de reanudación ligado a
la corrida original. Las reanudaciones de un mismo lote deben
ejecutarse de forma serial para compartir correctamente ese avance.

La prueba prevista quedó sustituida por la validación puntual siguiente. El
runner genérico de reanudacion seleccióna los pendientes por orden. Limitarlo
a un proceso no fija la selección en Moniquirá.

Pasaron 262 pruebas offline. Las regresiones cubren éxito, fallos de
ambas vías, activación solo ante HTTP 403, presupuesto de intento,
cancelación, tamaño, plazo, tipo, reutilización y reanudación sin
feed. Una simulación offline ejecutó el JavaScript de control y
verificó la señal de aborto por tamaño declarado, sobrelectura y plazo.


### Validación real de Fetch en Moniquirá

El 24 de noviembre de 2026 se validó el PDF rector de CM-MC-004-2026,
DocumentId 896148933, contra el inventario vigente del mismo proceso. El
enlace coincidió con el archivado y no tenía parámetros adicionales.
Hubo dos consultas a la primera página de ese inventario, ambas HTTP 200.
La primera se detuvo localmente antes de descargar porque el título vigente
omitía el sufijo .pdf. El segundo paso verificó ruta, identificador único y
formato, y confirmó que los títulos coincidían al ignorar dicho sufijo.

| Intento | Vía | Observación | Tiempo |
| --- | --- | --- | ---: |
| 1 | urllib | HTTP 403 en cabeceras, HTTPError, text/html, sin redirecciones | 2,422 s |
| 2 | Edge CDP Fetch | edge_fetch_rejected antes de leer el cuerpo. CDP registró MissingAllowOriginHeader | 0,625 s |

Sólo el 403 activó el fallback. Fetch no expuso código HTTP a la página y la
limpieza del lector quedó confirmada. CDP identificó una respuesta sin la
cabecera CORS requerida para leer el recurso desde Licitaciones.info. La
descarga anterior por clic había devuelto un PDF de 595.065 bytes. Esa
navegación y Fetch tienen distintos requisitos de acceso al cuerpo. La causa
del 403 de urllib sigue indeterminada.

Ambos intentos finalizaron dentro de los 12 s por intento y no se almacenaron
bytes de PDF. En esta prueba no se pudo verificar la integridad del archivo
ni ejercitar la guarda de 10 MiB durante una transferencia. La fase que
incluyó los dos intentos y la consulta de inventario tardó 5,687 s y consumió
8 créditos del runner. El prechequeo anterior sumó una consulta y un crédito.
Las trazas depuradas quedaron en el almacenamiento local excluido de Git.

El resultado deja Fetch desactivado por defecto y la recuperación de los
12 procesos pendiente. No se consultó el feed nacional ni se procesaron
otros documentos. Cualquier siguiente prueba o recuperación requiere
autorización adicional.

### Repetición tras recargar Edge

Tras la recarga manual, una consulta al inventario respondió HTTP 200 y
confirmó el mismo enlace. urllib devolvió HTTP 403 en 2,531 s.
Edge Fetch volvió a registrar MissingAllowOriginHeader en 0,579 s,
con limpieza confirmada. Se conservó la traza depurada localmente.
Se completaron los dos intentos en 5,734 s totales y 8 créditos,
sin PDF guardado ni consultas al feed.


### Evaluación offline de descarga nativa con Edge CDP

La descarga por clic se puede automatizar y observar. Los eventos de CDP
permiten controlar qué archivo se conserva y solicitar la cancelación, con
un margen entre la transferencia y su notificación. Bajo el límite actual
de 10 MiB de transferencia y 12 s por intento, el control resulta
insuficiente para habilitar la vía automática.

#### Secuencia observada

En el laboratorio, el clic sobre un enlace produjo una descarga nativa
entre dos orígenes locales sin leer el cuerpo desde JavaScript. Para una
adquisición autorizada, se usaría el control visible o un enlace de
inventario validado por HTTPS, host, ruta, DocumentId exacto y referencia
del proceso. Los parámetros de la URL se conservarían en memoria. El evento
Browser.downloadWillBegin se correlaciona con el marco esperado y el enlace
validado. Si hay un destino final distinto o no se puede establecer esa
correspondencia, se descarta el archivo. Esa verificación de identidad no
impide por sí sola que una redirección ya haya iniciado tráfico.

Browser.setDownloadBehavior con allowAndName y eventsEnabled habilita
un directorio temporal por intento y usa el GUID como nombre. El ajuste
abarca el contexto de navegador, incluidas sus otras pestañas, y requiere
uso exclusivo del Edge dedicado y restaurar el comportamiento anterior
al terminar. Un contexto nuevo de laboratorio no comparte la sesión
autorizada. Browser.downloadProgress informa bytes y estado por GUID.
Usar sólo el archivo regular esperado dentro del directorio temporal al
recibir completed. La ruta opcional del evento puede faltar, y el archivo
debe comprobarse en disco. Browser.cancelDownload requiere el GUID y
debe confirmarse con el estado canceled. La orden por sí sola no confirma
que se haya retirado el archivo parcial.

[Protocolo Browser de CDP](https://chromedevtools.github.io/devtools-protocol/tot/Browser/)

#### Pruebas offline y límites observados

Edge 158.0.4370.33 ejecutó un laboratorio temporal con perfil aislado,
dos servidores de loopback y archivos sintéticos. Los plazos reducidos
del laboratorio forzaron los casos de error. El presupuesto de EN-01
sigue siendo de 10 MiB y 12 s.

| Caso | Resultado |
| --- | --- |
| PDF válido de 431 bytes | Inicio asociado con el enlace y marco correctos, archivo GUID, estado completed, una página y SHA-256 idéntico al de la prueba |
| 12 MiB declarados | CDP permitió cancelar al ver el total antes de contabilizar bytes de cuerpo |
| 12 MiB rápidos sin tamaño declarado | El primer progreso que mostró bytes ya registraba 12 MiB. Una ejecución incluso dejó un archivo de ese tamaño en staging tras canceled |
| Pausa en el cuerpo después del inicio | El plazo disparó la cancelación por GUID y el caso terminó sin archivo final |
| Respuesta sin cabeceras al vencer el plazo | No hubo evento de inicio ni GUID sobre el cual ordenar la cancelación |

CDP carece de un tope de bytes de transporte y un plazo estricto para la
descarga nativa. Un sondeo de disco tampoco adelanta los eventos ni vacía
los buffers del navegador. El plazo local permite detectar y descartar un
resultado tardío. La confirmación de cancelación puede llegar después del
plazo y, antes del GUID o si se pierde CDP, no puede garantizarse. Tras un
fallo sin cancelación confirmada, se detiene la adquisición, se aísla el
staging y se comprueba su limpieza antes de continuar. Pasaron 134
regresiones de EN-01 y Edge y una quedó omitida.

#### Continuidad con archivos locales

La alternativa simple es incorporar copias que el operador ya haya
descargado por el portal. La copia disponible de Moniquirá, CM-MC-004-2026 y
DocumentId 896148933, se verificó en solo lectura. Tiene firma PDF,
595.065 bytes y 22 páginas. No se incorporó al estado de reanudación.

Antes de conservar una copia, asociarla explícitamente con la referencia y
DocumentId del inventario y documentar el origen de esa asociación. El nombre
del archivo y su hash no acreditan por sí solos la identidad contractual.
Comprobar tamaño real, firma y lectura estructural del PDF o DOCX esperado.
Almacenar mediante LocalBinaryStorage y verificar el SHA-256 y tamaño al
abrirlo. Reutilizar el recibo de DownloadState por DocumentId y extensión
antes de solicitar otra copia. Serializar la reanudación de en01-hsxjhqpg y
conservar las razones de rechazo por documento, sin volver al feed.

En una adquisición posterior, tres fallos consecutivos repartidos entre al
menos dos procesos activarían el corte existente. La pérdida de sesión,
de correlación o de control de cancelación exigiría parar antes. No se
propone otra sonda real de descarga nativa: repetir el clic con el PDF de
Moniquirá no resolvería los límites demostrados en laboratorio. Los 12
procesos siguen pendientes. Esta evaluación usó solo archivos locales y
loopback, sin tráfico al feed ni a SECOP.


### Importación asistida y reanudación offline

El importador lee la selección y los inventarios archivados. El manifiesto
asocia la referencia SECOP y el DocumentId con una copia de disco que el
operador identificó en el portal. Se verifica ese par contra el inventario,
aunque el nombre local sea distinto. El almacenamiento existente comprueba
firma y estructura básica y permite reabrir el archivo con verificación de
tamaño, SHA-256 y tipo.

El flujo registra procedencia manual, cobertura y evidencia con locadores.
Reutiliza el extractor, OCR selectivo y los cuatro estados formales de EN-01.
Los archivos faltantes quedan pendientes y pueden impedir una conclusión
formal. Se mantienen 10 MiB por archivo, 24 documentos acumulados por lote
y 3 por proceso. Cada ejecución mantiene 2 páginas OCR por PDF, hasta 48
derivadas del tope documental, y el plazo de 720 s, con el margen existente
para iniciar extracción. Usa cero créditos de red y cero llamadas de IA.

#### Validación con Moniquirá

Se importó exclusivamente el rector 896148933 de CM-MC-004-2026.
El archivo de 595.065 bytes produjo texto nativo en sus 22 páginas,
sin OCR ni páginas pendientes dentro del PDF. La página 11, sección
Experiencia general, exige al menos dos contratos ejecutados
satisfactoriamente cuyo objeto o alcance esté relacionado con el objeto
a contratar. La prioridad comercial es explicit_requirement. El estado
formal sigue not_resolved con requirement_requires_corroboration
porque el inventario conserva tres documentos sin importar.

La ejecución tomó 3,969 s, con 3,703 s de extracción. La repetición
verificó el archivo y reutilizó el recibo y la extracción en 0,171 s.
Quedó un solo binario por hash, con cero errores. El lote conserva
los 12 inventarios y los otros 11 procesos siguen sin copias importadas.
Pasaron 164 pruebas offline, una quedó omitida y Ruff pasó.

#### Incorporación de las siguientes copias

1. Consultar processes.json y documents.json en
   .local/eureka-nacional-spike/en01-hsxjhqpg. Para cada copia manual,
   tomar el process_reference de la fila y el document_id de su inventario.
2. Agregar una fila al manifiesto local. Ambos identificadores son cadenas.
   La ruta file puede ser absoluta o relativa al directorio del manifiesto.
   Se pueden presentar sólo las copias nuevas. El recibo anterior permite
   incorporar al resultado las copias ya importadas.

```json
[
  {
    "process_reference": "referencia-exacta-del-archivo-processes.json",
    "document_id": "12345",
    "file": "copias/Invitacion.pdf"
  }
]
```

3. Ejecutar desde el worktree experimental con spikePython apuntando al
   Python del entorno existente.

```powershell
$env:PYTHONPATH = (Resolve-Path './backend/src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython './backend/scripts/eureka_nacional_manual_import.py' `
  --resume-inventory-from en01-hsxjhqpg `
  --manifest './.local/eureka-nacional-spike/manual-en01-hsxjhqpg.json' `
  --tesseract 'C:/Program Files/Tesseract-OCR/tesseract.exe'
```

La salida persistente está en .local/eureka-nacional-spike/en01-manual_hsxjhqpg.
Revisar review_queue.json, experience_requirements.json, documents.json y
errors.json. El manifiesto, los binarios y los resultados detallados
quedan fuera de Git. Si se ofrece un archivo distinto para un DocumentId
ya registrado, se conserva la copia verificada anterior y se registra el
conflicto. Tras una interrupción del sistema, si queda .import.lock,
comprobar que no hay otro importador activo antes de quitarlo. No se
consultó SECOP, CDP ni el feed durante la validación.


### Laboratorio offline de streaming con Edge CDP

El laboratorio independiente eureka_nacional_cdp_stream_lab.py usa Edge
158.0.4370.33 con un perfil temporal y dos orígenes HTTP de loopback.
El clic inicia una navegación normal con el gestor de descargas
deshabilitado en el contexto. La sesión CDP de la pestaña intercepta
la respuesta del enlace exacto en la etapa de cabeceras y comprueba
método, URL y marco. Fetch.takeResponseBodyAsStream y las lecturas
secuenciales IO.read entregan bloques de hasta 64 KiB. El cuerpo
sintético verificado se guarda con LocalBinaryStorage y se reabre
por hash y tamaño. El laboratorio no se conecta al Edge autenticado,
no ejecuta JavaScript fetch() y no se integra al runner.

| Caso | Resultado observado |
| --- | --- |
| PDF válido de 431 bytes | HTTP 200, EOF, SHA-256 de la copia sintética, firma PDF y un archivo verificado. IO.close, aborto de la navegación interceptada y cierre de la pestaña confirmados. |
| 12 MiB con tamaño declarado | Rechazo al recibir cabeceras. 0 bytes leídos por EN-01 y cierre de la pestaña confirmado. |
| 12 MiB sin tamaño declarado | Parada en 10.485.760 bytes leídos por EN-01. Cierre de la pestaña confirmado y cero archivos. |
| Cuerpo detenido y cabeceras tardías | Cada caso agotó el plazo de 12 s en la fase correspondiente. Cierre confirmado en ambos y cero archivos. |
| PDF truncado | Se leyó la respuesta corta y se rechazó por integridad. Cero archivos. |
| Canal de la pestaña sin respuesta durante el streaming | La orden de desconexión no recibió acuse en la ventana de 0,75 s. El canal independiente del navegador cerró la pestaña y confirmó el cierre. Cero archivos. |
| Cierre incierto | Se simuló que el canal independiente no podía confirmar el cierre. La siguiente adquisición se rechazó antes de navegar. Tras destruir el contexto temporal, se creó otro y se verificó un PDF sintético. |

En errores durante el cuerpo, el laboratorio cierra la pestaña con un
canal CDP independiente. El cierre se trata como fase separada con una
ventana de confirmación de 2 s. Un acuse de cierre de pestaña no mide los
bytes ya recibidos por Edge o el sistema operativo ni confirma cuándo
se interrumpió el envío del servidor. El tope de 10 MiB se aplica al
cuerpo que entrega CDP a EN-01. El reloj de 12 s detiene la espera
y excluye resultados tardíos. Una respuesta sin longitud que alcanza
10 MiB sin EOF se rechaza en ese punto. La diferencia entre abortar
una navegación ya leída y cerrar una pestaña con cuerpo pendiente se
conserva en la traza. La pérdida simultánea de confirmación se inyectó
en laboratorio. No se provocó una caída total de Edge.

Para repetir desde el worktree experimental, con spikePython apuntando
al entorno existente:

```powershell
$env:PYTHONPATH = (Resolve-Path './backend/src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython './backend/scripts/eureka_nacional_cdp_stream_lab.py'
```

Pasaron los ocho escenarios del laboratorio, la comprobación de bloqueo
y la de recuperación. Pasaron 164 regresiones de EN-01 y adquisición,
con una omitida. Ruff y su comprobación de formato pasaron.

#### Sonda real propuesta, pendiente de autorización

La prueba offline sustenta una sonda de un solo intento sobre el rector
896148933 de CM-MC-004-2026. Usar el enlace archivado ya confirmado,
conservar su identidad y utilizar una pestaña desechable en el Edge
dedicado y autorizado. Limitar la intercepción al destino esperado,
sin reintentos ni redirecciones adicionales. No consultar feed ni
inventarios. Si no se puede preservar el contexto autorizado y
aislar el cierre, detenerse antes de navegar.

Mantener 10 MiB de lectura y 12 s de adquisición, con limpieza acotada y
bloqueo si el cierre queda incierto. Comparar tamaño, firma y SHA-256 con
la copia local de 595.065 bytes. Registrar estado HTTP, etapa, bytes,
plazo y estado de cierre sin guardar URL completa, cabeceras ni datos
de sesión. El éxito requiere identidad verificable, el mismo contenido
y cierre confirmado. El laboratorio no realizó esa sonda, solicitudes
a SECOP ni recuperaciones de los otros 11 procesos.


#### Resultado de la sonda real de streaming en Moniquirá

La sonda autorizada del 24 de noviembre de 2026 usó el enlace archivado
validado de CM-MC-004-2026, DocumentId 896148933. Se abrió una pestaña
desechable desde el origen autorizado del Edge dedicado. La pausa CDP
en la etapa de solicitud permitió continuar un único GET exacto y
exigir la pausa de su respuesta. Se observó una solicitud al destino.
No hubo reintentos, consultas al inventario ni consultas al feed.

| Comprobación | Resultado |
| --- | --- |
| Respuesta interceptada | HTTP 200, application/pdf, longitud declarada de 595.065 bytes |
| Cuerpo | Lectura hasta EOF, 595.065 bytes en 1,203 s |
| Comparación local | Mismo tamaño, firma PDF y SHA-256 que la copia manual verificada |
| Cierre | Acuses de IO.close y aborto de la navegación interceptada. Cierre de la pestaña confirmado en 0,063 s |
| Límites | 10 MiB aceptados por EN-01 y 12 s de adquisición |

Se reutilizó la lectura por bloques y el cierre independiente del laboratorio.
La sonda dejó una traza depurada en el almacenamiento local excluido de Git.
La copia de referencia se conservó como único binario para el análisis.
La sesión original de Edge siguió disponible. La adquisición está validada
para este PDF y enlace. Quedan por validar otros formatos, encaminamientos
y respuestas de SECOP. Los límites se aplican a los bytes aceptados y a
la espera de EN-01. El cierre de la pestaña no mide el tráfico que ya
entró en los búferes del navegador o el sistema operativo.

#### Continuidad propuesta para los 11 procesos pendientes

Con autorización separada, empezar con un lote de hasta tres procesos
distintos de en01-hsxjhqpg, un rector por proceso y tres intentos totales.
Reutilizar la selección archivada, los recibos por DocumentId y el
almacenamiento por hash. Dejar Moniquirá fuera de futuras descargas
por su recibo existente. Usar enlaces cuya identidad y completitud
puedan verificarse. Si un enlace está incompleto, dejar constancia y
omitirlo hasta autorizar, si se requiere, el refresco de ese inventario.
No se necesita repetir el discovery.

Habilitar el candidato a streaming sólo en EN-01 y de forma optativa.
Mantener un documento por vez, 10 MiB aceptados y 12 s de adquisición
por intento. Reutilizar las guardas de extracción y OCR selectivo de
hasta dos páginas por PDF y cero IA. Marcar el documento pendiente
si falla la validación. Bloquear tras un cierre incierto y detener el
piloto ante tres fallos consecutivos repartidos en al menos dos procesos
o al agotar el cupo. Publicar sólo métricas agregadas. Cualquier
continuación hacia los otros pendientes requerirá evaluar el piloto y
obtener autorización. El runner y los 11 procesos siguen sin cambios.


### Piloto de recuperación CDP Streaming en tres procesos archivados

El piloto seleccionó tres PDF identificados como rectores por el inventario
de en01-hsxjhqpg, con un candidato de título explícito por proceso y sin
recibo o hash persistido en las corridas anteriores. Los enlaces se
validaron localmente por HTTPS, ruta e identificador. La identidad del
destino se comprobó de nuevo al interceptar la respuesta. Moniquirá
quedó excluido por su recibo de importación.

| Proceso | DocumentId | HTTP | Bytes | Adquisición | Cobertura del PDF | Clasificación formal y prioridad automática |
| --- | --- | --- | ---: | ---: | --- | --- |
| Caicedonia 2026-351 | 896141381 | 200 | 393.913 | 1,141 s | 20/20 páginas nativas | not_resolved, documentary_silence |
| Maicao MC-MM-038-2026 | 896113617 | 200 | 426.892 | 0,703 s | 37/37 páginas nativas | not_resolved, explicit_requirement |
| Fondo Rotatorio de la Registraduría MC-IP-04-2026- FRR | 896145730 | 200 | 506.071 | 1,234 s | 21/21 páginas nativas | not_resolved, insufficient_evidence |

Se leyó cada respuesta hasta EOF. Coincidieron los tamaños declarados y
observados. Los tres binarios pasaron firma PDF, estructura básica y
relectura por SHA-256. En los tres se confirmaron cierre del flujo,
aborto de la navegación interceptada y cierre de la pestaña. Los
SHA-256 completos, recibos, cobertura y trazas depuradas quedaron en
.local/eureka-nacional-spike/en01-cdp-pilot_cj40v9j7, excluido de Git.
Los tres GET sumaron 1.326.876 bytes y 3,078 s de adquisición. El
piloto completo tardó 19,891 s, con 78 páginas nativas, cero OCR y
cero IA. No hubo reintentos ni nuevas consultas a inventarios o feed.

**Revisión offline de las discrepancias**

- Caicedonia, página 8. El documento sitúa en requisitos mínimos
  habilitantes la instrucción de anexar al menos tres certificaciones
  de experiencia en contratos similares ejecutados. El clasificador
  leyó las frases como condicionales de alcance indeterminado y asignó
  silencio. La evidencia amerita revisar ese falso silencio. Quedan
  dos documentos sin analizar y la invitación remite a estudios previos.
- Maicao, páginas 14 y 15. La invitación expone requisitos de
  experiencia para el proponente y distingue cómo acreditarla para
  mipymes, empresas de mujeres y otros oferentes. La prioridad
  automática es exigencia aplicable. Diez documentos no excluidos
  quedaron pendientes y el estado formal sigue abierto.
- Registraduría, páginas 1 y 11. El encabezado de plantilla dice
  Formato Invitación Pública. Debajo, la portada identifica de forma
  expresa la Invitación Pública 04 de 2026 FRR y su objeto para Boyacá.
  La regla de portada rebajó automáticamente el rector a soporte.
  La página 11 exige acreditar contratos ejecutados de objeto similar
  por una suma al menos igual al presupuesto oficial. La prioridad
  automática sigue insuficiente y corresponde revisar esa decisión.
  Cinco documentos quedaron pendientes.

Tres de tres adquisiciones en un intento, junto con la sonda anterior,
justifican proponer recuperación progresiva de PDF con la misma ruta,
esos límites y el mismo corte ante cierre incierto. Los resultados
cubren archivos menores de 0,5 MiB con longitud declarada. Quedan
sin validar DOCX, PDF más grandes, redirecciones y respuestas sin
longitud en SECOP. La muestra verifica adquisición bajo estas
condiciones. Las discrepancias de clasificación requieren revisión
separada. Los tres procesos mantienen corroboración pendiente y
otros ocho siguen sin una copia recuperada de su rector. Un lote
posterior requiere autorización nueva. No se cambió el runner.


### Correcciones offline de Caicedonia y la Registraduría

La regla nueva exige un mandato de anexar o presentar en la oferta un
número de certificaciones de experiencia sobre contratos ejecutados.
Conserva las guardas para negaciones, sujetos limitados y referencias
condicionales. La portada con encabezado de plantilla Formato Invitación
Pública confirma el rector cuando también identifica una invitación
numerada y contiene la sección Objeto. Una plantilla auxiliar o portada
de estudios previos conserva su tratamiento.

| Proceso | Evidencia del PDF local | Prioridad antes | Prioridad después | Estado formal |
| --- | --- | --- | --- | --- |
| Caicedonia 2026-351 | Pág. 8. Al menos tres certificaciones en la oferta por contratos similares ejecutados. | Silencio documental | Exigencia aplicable | not_resolved, corroboración pendiente |
| Registraduría MC-IP-04-2026-FRR | Pág. 1. Invitación numerada con objeto propio. Pág. 11. Hasta dos certificaciones o acta de liquidación de contratos similares ejecutados por una suma al menos igual al presupuesto oficial. | Evidencia insuficiente | Exigencia aplicable | not_resolved, corroboración pendiente |

Se releyeron los 78 folios nativos del piloto, con cero OCR. Maicao
conservó estado y prioridad. El corpus local de Pore, El Plato, La Capilla
y las dos invitaciones de Chivatá coincidió en los 5 casos, con cero falsos
positivos y cero falsos negativos de evidencia favorable. Pasaron 177
pruebas offline, una quedó omitida y Ruff pasó. El replay y los fragmentos
quedaron localmente en en01-reclassification_zcywlw4q.

### Recuperación acotada preparada, pendiente de autorización

eureka_nacional_stream_recovery.py planifica a partir de en01-hsxjhqpg
y valida los recibos con el almacenamiento por SHA-256. El plan actual
excluye del tráfico Moniquirá, Caicedonia, Maicao y la Registraduría.
De los ocho pendientes, seis tienen un rector PDF único y enlace
archivado con identidad verificable. Pacho MC-039-2026 y La Estrella
SI 026 2026 quedan pendientes de identificar un PDF rector. El modo de
planificación no abre Edge ni consulta el portal.

La ejecución requiere seleccionar hasta tres referencias por lote. Primero
usa SecopDownloader, con un proceso supervisado y 12 s de plazo.
Sólo un 403 directo sin redirección habilita el streaming. El GET de
Edge se limita al enlace archivado exacto y al documento esperado.
Streaming acepta respuesta directa HTTP 200 de PDF, sin compresión,
con tamaño declarado positivo hasta 10 MiB. Rechaza DOCX, redirecciones,
respuestas de longitud desconocida y otros tipos. El plazo de
adquisición es de 12 s más una fase separada de confirmación de cierre.
El tope de bytes se aplica a EN-01. Los búferes de Edge y del sistema
operativo quedan fuera de esa medición.

El runner conserva un recibo por DocumentId, un registro de intentos
durable y las clasificaciones y cobertura localmente. Un intento previo
no se repite automáticamente. El lote se detiene ante cierre incierto o
tres fallos consecutivos repartidos en al menos dos procesos. La guarda
de cierre queda registrada en disco para la siguiente invocación.

**Lote inicial recomendado.** RE-006-2026 (El Espinal), CFDM-27-2026
(Bogotá) y MC-SEAM-102-2026 (Puerto Gaitán), un rector por proceso.
Por lote, hasta tres vías directas y tres alternativas, 21 créditos
como máximo (6 por llamada directa y 1 por GET de Edge), hasta 30 MiB
de archivos aceptados, 72 s acumulados de adquisición y 6 páginas OCR.
El límite operativo del runner es 720 s y 0 llamadas de IA.
Para los seis actualmente elegibles, en dos lotes separados, los
máximos agregados serían 12 vías, 42 créditos, 60 MiB aceptados,
144 s de adquisición y 12 páginas OCR. Los otros dos quedan fuera de
esos presupuestos hasta identificar sus rectores.

Plan offline ya verificado:

```powershell
$env:PYTHONPATH = (Resolve-Path './backend/src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython './backend/scripts/eureka_nacional_stream_recovery.py' `
  --resume-inventory-from en01-hsxjhqpg
```

Comando pendiente de autorización para el primer lote:

```powershell
& $spikePython './backend/scripts/eureka_nacional_stream_recovery.py' `
  --resume-inventory-from en01-hsxjhqpg `
  --process 'RE-006-2026' --process 'CFDM-27-2026' --process 'MC-SEAM-102-2026' `
  --tesseract 'C:/Program Files/Tesseract-OCR/tesseract.exe' --execute
```

El comando de ejecución y su combinación de vías se verificaron con
pruebas offline de enrutamiento, idempotencia y cierre. La ruta
contra SECOP conserva la evidencia de las sondas anteriores.
Esta fase terminó con el plan y las regresiones, sin consultas CDP,
inventarios, feed ni descargas reales.


### Resultado de la recuperación acotada de El Espinal, Bogotá y Puerto Gaitán

Se ejecutó una sola vez el comando autorizado de 4152844 el 24 de
noviembre de 2026. El inventario provino de en01-hsxjhqpg. Los
tres GET directos con urllib recibieron HTTP 403 en cabeceras,
sin redirecciones. Cada 403 activó un único GET en Edge CDP Streaming.
Las tres respuestas fueron HTTP 200 y se leyeron hasta EOF.
En todos los casos coincidieron los tamaños declarados y observados,
se verificaron firma PDF y SHA-256 al reabrir el archivo, y se
confirmaron el cierre del flujo y el cierre de la pestaña.

| Proceso | DocumentId | Bytes verificados | urllib / CDP | Cobertura del rector |
| --- | --- | ---: | ---: | --- |
| El Espinal RE-006-2026 | 896145404 | 489.274 | 3,672 s / 1,266 s | 48 de 48 páginas nativas |
| Bogotá CFDM-27-2026 | 896092556 | 540.269 | 3,390 s / 0,844 s | 10 de 10 páginas nativas |
| Puerto Gaitán MC-SEAM-102-2026 | 896045300 | 2.630.258 | 3,500 s / 1,234 s | 2 de 41 páginas por OCR. Quedaron 39 pendientes. |

| Proceso | Estado formal | Prioridad comercial | Evidencia y límites de cobertura |
| --- | --- | --- | --- |
| El Espinal | not_resolved | explicit_requirement | Págs. 7 y 14. Exige un contrato o certificación de objeto o actividades relacionados. La pág. 7 indica al menos el 100 % del presupuesto oficial. Quedaron 16 elementos no excluidos del inventario sin revisar. |
| Bogotá | experience_ambiguous | limited_or_ambiguous | Pág. 6, numeral 19. La tabla menciona hasta tres certificaciones o contratos similares, ejecutados en los tres años anteriores, por una suma de al menos el 100 % del presupuesto oficial. La pág. 8 menciona requisitos de experiencia entre las causales de rechazo. El clasificador mantuvo alcance limitado y la lectura de la tabla requiere corroboración. Quedaron 3 elementos del inventario sin revisar. |
| Puerto Gaitán | not_resolved | insufficient_evidence | Las págs. 1 y 2 produjeron texto OCR sin una afirmación decisiva. Quedaron 39 páginas del rector escaneado y tres documentos complementarios sin analizar. |

El lote consumió 21 créditos presupuestarios por seis GET efectivos y
aceptó 3.659.801 bytes. La suma de adquisición fue de 13,906 s
(10,562 s de la vía directa supervisada y 3,344 s de streaming).
La extracción sumó 14,688 s y 5,938 s de CPU nativa.
De 99 páginas totales, se recuperaron 58 nativas y 2 por OCR.
Hubo tres rechazos HTTP en la vía directa, cero fallos finales de
recuperación o extracción, cero reintentos, cero IA y cero solicitudes
al feed o a inventarios. Quedaron cero ausencias explícitas o
confirmadas. El caso con cobertura parcial quedó como evidencia
insuficiente.

La relectura del plan offline marcó los tres rectores como
already_verified. Los recibos, hashes, trazas depuradas y evidencia
detallada quedaron excluidos de Git en
.local/eureka-nacional-spike/en01-stream_hsxjhqpg. No quedó un cierre
incierto. Permanecen tres candidatos con rector PDF elegible y otros
dos pendientes de identificar un rector PDF verificable. Una
recuperación posterior requiere autorización nueva.


### Recuperación de Rionegro y Chitaraque, 26 de noviembre de 2026

La revisión del inventario archivado y los recibos dejó dos invitaciones
PDF con enlace e identidad verificables. El runner marcaba como elegible
Yumbo, pero el título archivado identifica un aviso de invitación pública.
El documento quedó fuera del lote por falta de confirmación de su carácter
rector. Se reabrió el perfil Edge dedicado de EN-01 y se confirmó la
sesión HTTP 200 en Licitaciones.info con el feed y los inventarios
bloqueados durante la operación.

| Proceso | DocumentId | urllib / CDP Streaming | Resultado y cobertura | Estado formal y prioridad comercial |
| --- | --- | --- | --- | --- |
| Rionegro, 492-2026-OC | 896109474 | HTTP 403 directo sin redirección / HTTP 200 | 595.319 bytes, firma PDF y SHA-256 verificados. 2 de 12 páginas por OCR, 10 pendientes, sin páginas nativas. | not_resolved, evidencia insuficiente. Las páginas 1 y 2 no aportaron afirmaciones decisivas. |
| Chitaraque, MC-045-2026 | 896089636 | HTTP 403 directo sin redirección / HTTP 200 | Tamaño declarado superior a 10 MiB. Rechazo en cabeceras, sin leer el cuerpo ni guardar el PDF. La traza conserva el motivo y omite la longitud exacta por la forma actual del registro. | not_resolved, evidencia insuficiente. No hubo extracción. |

Se confirmó el cierre del flujo completo y la pestaña de Rionegro.
En Chitaraque, se cerró la pestaña con la respuesta pausada en
cabeceras. Las dos transferencias dejaron cierre verificable y
ninguna requirió reintentos. Hubo dos rechazos de la vía directa y un
rechazo final por tamaño. El comando cerró con código 2 por el
resultado parcial.

Se usaron 14 créditos del presupuesto por 4 GET a SECOP, 595.319
bytes aceptados y 13,452 s acumulados de adquisición (11,125 s
directos y 2,327 s por CDP). El comando tardó 34,656 s. La
extracción de Rionegro tardó 8,062 s y usó 2 páginas OCR.
Hubo cero consultas al feed o inventarios y cero llamadas de IA.
El recibo, hash y evidencia se conservaron en el directorio local
en01-stream_hsxjhqpg, excluido de Git.

**Pendientes de adquisición y cobertura**

- Chitaraque conserva un intento registrado y el rector pendiente
  por exceso de tamaño. El runner no repite el intento automáticamente.
- Yumbo IP-CMC-IMVY-012-2026 tiene un aviso y estudios previos.
  Falta identificar el rector con certeza.
- Pacho MC-039-2026 y La Estrella SI 026 2026 siguen sin rector PDF
  inequívoco en el inventario archivado. En La Estrella figura un
  proyecto de pliegos.
- Rionegro tiene el PDF verificado y 10 páginas pendientes de OCR
  o revisión. Su cobertura sólo permite evidencia insuficiente.
- Puerto Gaitán MC-SEAM-102-2026 mantiene 2 de 41 páginas con OCR y
  39 pendientes. El estado formal sigue not_resolved y la prioridad
  comercial es evidencia insuficiente. No se reclasifica como silencio
  ni ausencia de experiencia. No se descargó ni se procesó de nuevo.

Los dos casos del lote quedaron sin conclusión formal sobre experiencia.
No se amplió OCR, tamaño ni alcance de la recuperación.


### Cierre offline de cobertura documental, 26 de noviembre de 2026

Se inspeccionaron visualmente las 53 páginas de los dos PDF locales.
Ninguno tiene capa de texto, marcadores ni índice navegable. Las primeras
dos páginas de cada archivo ya se habían procesado por OCR. La revisión
local ubicó los numerales impresos sin consumir OCR adicional ni cambiar
las clasificaciones automáticas guardadas.

| Proceso | Cobertura actual | Páginas prioritarias en un replay posterior | Evidencia visible |
| --- | --- | --- | --- |
| Puerto Gaitán MC-SEAM-102-2026 | 2/41 por OCR, 39 pendientes | Primero 15 y 16. Para corroboración posterior, 17 y 36. | La página 15, numeral 13.2 Experiencia mínima, exige un contrato ejecutado y finalizado de suministro relacionado por un valor al menos igual al presupuesto oficial. La 16 detalla la acreditación. La 17 remite al Anexo de Experiencia, cuyo formato aparece en la 36. El formulario complementa la cláusula. |
| Rionegro 492-2026-OC | 2/12 por OCR, 10 pendientes | Primero 11 y 4. Revisar la 3 como contexto de apertura de los requisitos habilitantes. | La página 11, numeral 16.14 Experiencia, exige aportar experiencia específica verificable relacionada con el objeto. La 4 lista la experiencia del proponente, remite al Anexo 3 y solicita certificados. Los umbrales y el alcance quedan por corroborar. |

Las referencias anteriores son observaciones visuales que orientan una
revisión de exigencia. En los resultados automáticos ambos procesos
siguen not_resolved con prioridad insufficient_evidence. No se inferió
silencio ni ausencia de experiencia. La limitación comprobada fue de
cobertura y selección de páginas. Las dos páginas iniciales dejaron
fuera las cláusulas. El clasificador todavía no ha recibido el texto de
las páginas prioritarias. Las vistas quedaron fuera de Git, localmente
en en01-ocr-map_ghwq8tcx.

#### Acceso y verificación pendiente

| Proceso | Evidencia archivada | Decisión |
| --- | --- | --- |
| Chitaraque MC-045-2026 | El rechazo declarado de 10 MiB ocurrió al recibir las cabeceras y antes de leer el cuerpo. El antecedente de 16 MiB en el inventario es un límite configurado del intento que falló por HTTP. | Se sabe que supera 10 MiB. Los artefactos revisados no permiten determinar si cabe en 16 MiB. El piloto ampliado se justifica sólo si se verifica por separado que el tamaño declarado está en ese intervalo y se autoriza expresamente. |
| Yumbo IP-CMC-IMVY-012-2026 | El título archivado dice Aviso de invitación pública y también hay estudios previos. Su enlace identifica un documento concreto. | Requiere corroborar que el contenido es una invitación con requisitos exigibles. Sigue fuera de selección automática. |
| Pacho MC-039-2026 | El Anexo complementario coincide con la referencia, pero su título es auxiliar. Los estudios archivados mencionan Semillas 2025. | El anexo es una pista para corroborar. Hace falta identificar el documento que rige el proceso de 2026. |
| La Estrella SI 026 2026 | Figuran aviso, estudio previo y proyecto de pliegos; el inventario no identifica pliego definitivo. | Mantener pendiente hasta verificar el rector definitivo. |

Se ajustó el plan de reanudación de EN-01 para distinguir avisos
archivados de invitaciones confirmadas. El plan reasigna Yumbo a
notice_needs_corroboration. La adquisición ahora conserva el valor
numérico declarado antes de aplicar el límite, sin registrar las
cabeceras completas. Las pruebas cubren ambos lados de 16 MiB y
que un aviso nunca desplace una invitación identificada. El cambio
mejora la selección y la observabilidad. La clasificación y el tope
vigente de 10 MiB quedaron intactos.

Para la siguiente exploración, validar primero un replay OCR local
con dos páginas dirigidas por PDF, conservando y distinguiendo la
cobertura acumulada. Si el replay confirma la evidencia, proponer
una muestra nacional de hasta 15 avisos nuevos con la exclusión
histórica, 1.130 ubicaciones y 21 categorías. Conservar 10 MiB,
dos páginas OCR por PDF y el resto del presupuesto aprobado. Medir
cobertura habilitante separadamente de páginas leídas, y mantener
los escaneos sin sección verificada como evidencia insuficiente.
No se consultó SECOP, inventarios ni feed durante este incremento.


### Validación offline de OCR dirigido

Se reabrieron los dos PDF locales por SHA-256 y se usó la extracción de
EN-01 con Tesseract en español. La selección del replay se fijó a las
cuatro páginas autorizadas. Se ejecutó OCR en dos páginas por PDF,
sin reintentos ni OCR sobre otras páginas. No hubo errores de ejecución.
La evidencia de este replay quedó en un resultado separado. Las cifras
acumuladas incluyen las dos páginas ya procesadas en cada PDF.

| Proceso | Páginas nuevas | Cobertura acumulada | Estado formal antes y después | Prioridad antes y después |
| --- | --- | --- | --- | --- |
| Puerto Gaitán MC-SEAM-102-2026 | 15 y 16 | 2/41 a 4/41, 37 pendientes | not_resolved | Evidencia insuficiente |
| Rionegro 492-2026-OC | 4 y 11 | 2/12 a 4/12, 8 pendientes | not_resolved | Evidencia insuficiente |

**Puerto Gaitán.** La página 15 conserva en el OCR el numeral de
experiencia mínima, la acreditación por contrato ejecutado y finalizado
y el umbral del presupuesto oficial. Hay ruido en el encabezado y
alrededor de la cantidad. La página 16 conserva el procedimiento de
acreditación mediante certificación o copia del contrato con el acta.
El clasificador leyó la primera cláusula como normativa condicional
de alcance indeterminado.

**Rionegro.** La página 4 conserva las referencias al Anexo 3 y a
certificados de experiencia. En la página 11, Tesseract transcribió
el sujeto como El aroma en vez de El proponente, pero conservó
la obligación de aportar experiencia específica, verificable y
relacionada con el objeto. El clasificador registró las tres
menciones como normativas condicionales.

Los controles con transcripción visual corregida también dieron
normativa condicional. La regla actual no reconoce las formas
se acreditará en un contrato o deberá aportar su experiencia
en esos contextos. El OCR de Rionegro introdujo además un error
en el sujeto. Un control positivo con una formulación ya
reconocida produjo EXIGENCIA y mantuvo not_resolved y evidencia
insuficiente al marcar la cobertura como parcial. La selección
dirigida resolvió qué páginas leer en estos dos PDF. Quedan por
validar la calidad del sujeto OCR, el reconocimiento de las
obligaciones y el criterio que separa una exigencia provisional
de una conclusión formal.

La extracción tomó 14,937 s en total. Las cuatro páginas quedaron
registradas con locador, método y evidencia. Los resultados y
controles quedaron en en01-directed-ocr_lxj95tq1, excluido de Git.
Se usaron cero créditos de red y no se cambió el clasificador,
el presupuesto OCR ni las clasificaciones persistidas de la
recuperación original.

#### Mejora mínima propuesta antes de explorar

Extender el selector existente para priorizar destinos de
marcadores PDF o índices con títulos de experiencia o requisitos
habilitantes, manteniendo su búsqueda actual en texto nativo.
En escaneos sin texto ni marcadores, probar que una de las dos
plazas se asigne al cuerpo en vez de a dos páginas contiguas de
portada. Usar una vista previa de baja resolución para localizar
cambios de sección, descartando encabezados repetidos y anexos
cuando puedan distinguirse por estructura. Las vistas previas
se usan sólo para señales de maquetación. No se añade una pasada
de reconocimiento de texto. El límite sigue en dos páginas OCR
por PDF.

Probar el selector offline sin suministrarle los números de
página conocidos. Medir si alcanza la cláusula, la tasa de
exigencias mal tratadas como condicionales y el costo. El ajuste
lingüístico futuro debe reconocer mandatos equivalentes de
forma general y conservar las guardas de cobertura formal.
Un escaneo sin señal suficiente queda para revisión. La siguiente
exploración nacional queda pendiente de autorización.


### Obligaciones contractuales y selección OCR

El clasificador reconoce mandatos explícitos de aportar, acreditar,
demostrar o certificar experiencia cuando el sujeto es el oferente.
También reconoce la construcción pasiva que atribuye la experiencia al
proponente y exige un contrato ejecutado. Las guardas conservan el alcance
de supuestos, excepciones, sujetos distintos del oferente y medios
de acreditación. Cuando OCR daña el sujeto, una obligación en el
encabezado de experiencia de un rector requiere concordancia con una
lista de experiencia del proponente y sus certificados en otra página.
Se conserva el fragmento OCR original. Una exigencia general en rector
parcial puede elevar la prioridad de revisión si no hay conflicto,
dependencia, condición limitada ni otro rector o adenda pendiente. La
cobertura incompleta mantiene el estado formal not_resolved.

| Caso | Evidencia reelaborada por OCR | Prioridad anterior y actual | Estado formal |
| --- | --- | --- | --- |
| Puerto Gaitán MC-SEAM-102-2026 | Pág. 15. La experiencia del proponente se acreditará por un contrato ejecutado y finalizado, relacionado con el suministro, por al menos el presupuesto oficial. La pág. 16 describe medios de acreditación. | Evidencia insuficiente a exigencia aplicable | not_resolved, 4/41 páginas acumuladas y 37 pendientes |
| Rionegro 492-2026-OC | Pág. 11. Mandato de aportar experiencia específica verificable relacionada con el objeto. El sujeto dañado en OCR se corroboró con la lista de experiencia del proponente y certificados de la pág. 4. | Evidencia insuficiente a exigencia aplicable | not_resolved, 4/12 páginas acumuladas y 8 pendientes |

El nuevo replay volvió a leer exclusivamente las páginas 15 y 16,
y 4 y 11, respectivamente. Las cuatro se recuperaron. La extracción
sumó 17,188 s. No se detectó ausencia de experiencia. La prioridad
nueva se conserva en el replay, separado de las decisiones históricas.
Los fragmentos, locadores y resultados quedaron localmente en
en01-context-ocr_6lacneav.

#### Señales del selector

Se incorporó lectura acotada de destinos de marcadores PDF titulados
Experiencia o Requisitos habilitantes. El selector conserva su lectura
de índices impresos y encabezados a partir del texto nativo. Sólo
prioriza destinos de páginas visitadas que requieren OCR. Una prueba
con marcadores pertinentes e irrelevantes comprobó que los primeros
desplazan la portada y que se respeta el máximo de dos páginas.

Los dos PDF locales son escaneos sin texto ni marcadores. El selector
sin indicaciones eligió 1 y 2 en los dos casos. La prueba experimental
sin texto comparó vistas de baja resolución y puntuó líneas cortas con
tinta densa separadas del cuerpo por espacios. Produjo 7 y 5 para
Puerto Gaitán, y 1 y 3 para Rionegro. Ninguna pareja alcanzó las
cláusulas principales. La maquetación sólo aporta una señal estructural
y la heurística no se activó. La selección automática de páginas
relevantes para escaneos sin señales sigue pendiente. Se mantiene
el presupuesto de dos páginas OCR por PDF.

Pasaron 195 pruebas offline y una quedó omitida. El replay de los
cinco casos conocidos (Pore, El Plato, La Capilla y Chivatá 21 y 22)
no mostró discrepancias ni falsos positivos o negativos de evidencia
favorable. Los controles nuevos cubren condiciones, alcance diferenciado,
terceros, instrucciones de acreditación, negaciones, rector parcial
y adenda pendiente. No hubo CDP, SECOP, consultas al feed, nuevas
descargas ni IA.

Los dos casos se interpretan correctamente cuando la cláusula está
disponible y se guarda como prioridad de revisión. Se recomienda
autorizar una siguiente muestra nacional de hasta 15 procesos nuevos
con exclusión histórica, universo comercial y presupuestos vigentes.
Medir por separado adquisición, cobertura habilitante y clasificación.
Los escaneos con cobertura limitada quedan abiertos. La nueva
exploración requiere autorización.


### Muestra nacional del 26 de noviembre de 2026

Se ejecutó una sola exploración nacional desde 3dfd326, con el perfil
comercial de 21 categorías y las 1.130 ubicaciones. El resolver compartido
cargó el perfil desde la configuración local. Los arranques preliminares
se detuvieron por configuración del perfil, aislamiento del chequeo del
portal y disponibilidad del cliente de la pestaña. Ninguno envió una
página de la muestra ni consultó inventarios. Un arranque que llegó al
chequeo registró 2 créditos del runner. En la ejecución final el
arranque del portal, el chequeo del perfil, el feed y los inventarios
respondieron HTTP 200. La guarda de la pestaña dejó pasar únicamente las
solicitudes de la muestra al feed.

| Embudo | Resultado |
| --- | ---: |
| Historial recalculado con seis corridas locales | 61 identidades SECOP II |
| Feed | 9 páginas de 30 filas, con una condicional |
| Filas / avisos distintos / departamentos observados | 270 / 269 / 29 |
| Coincidencias con el historial en la respuesta y en la muestra | 0 / 0 |
| Prefiltro de suministro / elegibles para inventario | 24 / 16 |
| Nuevos seleccionados / abiertos reportados / departamentos de la muestra | 15 / 14 / 10 |
| Procesos con inventario / documentos / rectores identificados por título | 2 / 10 / 2 |
| Intentos documentales / rectores recuperados / archivos procesados | 3 / 0 / 0 |

El feed se detuvo al alcanzar el cupo tras la novena página. Los count de
la fuente aumentaron de 31 a 271 al paginar. La muestra no establece el
tamaño del universo. De los 15 seleccionados, hubo cuatro en ferretería,
cuatro en mobiliario, tres en informática, dos en papelería, uno en
deportes y uno en aseo.

| Proceso con inventario | Estado formal | Prioridad comercial | Motivo de parada |
| --- | --- | --- | --- |
| Yumbo, MC-RF-016-2026 | not_resolved | Evidencia insuficiente | Cupo ordinario de dos intentos. Fallaron el rector y un soporte. |
| El Peñol, Antioquia, MC-039-2026 | not_resolved | Evidencia insuficiente | El intento del rector completó tres fallos consecutivos entre dos procesos y abrió el corte preventivo. |

Los tres GET directos con urllib recibieron HTTP 403 en cabeceras,
sin redirecciones y antes de leer un PDF. No se activó fallback.
El CLI nacional todavía expone la alternativa JavaScript Fetch
y el streaming validado vive en el comando de recuperación. Esa
opción nacional quedó desactivada conforme al alcance autorizado.
Los otros 13 seleccionados quedaron pendientes de inventario y
sin clasificación. Los 15 permanecen pendientes de evidencia.

Se verificaron cero secciones de experiencia o requisitos
habilitantes. No hubo exigencias ni ausencias explícitas detectadas,
casos de silencio evaluable, contradicciones ni candidatos
favorables con corroboración pendiente. Sin texto contractual
no fue posible medir errores de clasificación por cotejo ni
evaluar la frecuencia de oportunidades sin experiencia.
La limitación observada fue la adquisición.

La muestra usó 33/200 créditos, 45,468 s del runner y 49,094 s
de ejecución supervisada. Hubo cero bytes documentales aceptados,
cero OCR y cero llamadas de IA. El registro MPNE de los 15
seleccionados guarda presupuesto, modalidad y fecha observados.
Registra categoría derivada, tipo de entidad inferido en 11 y
tipo de contrato inferido en 8. Plazo, pago y lugar de entrega
quedaron faltantes. Estos campos no participaron en el filtrado
ni en el orden de la muestra. Los resultados detallados y los
15 avisos seleccionados se conservan localmente en en01-abu8_p7u.

La próxima autorización puede centrarse en recuperar primero los
dos rectores de inventarios disponibles y en integrar la vía CDP
Streaming a la adquisición nacional bajo las guardas ya validadas.
Los otros 13 requieren inventario. Continuar desde la selección
archivada evita repetir discovery. No se hizo otro lote ni otra
exploración.


### Resiliencia integrada y auditoría offline del descubrimiento

#### Adquisición compartida

El runner nacional conserva urllib y comparte ahora con el recuperador
el módulo de streaming validado en los pilotos. Se habilita con
--edge-stream-fallback. El nombre anterior del indicador es un alias de
streaming. La ruta activa no invoca JavaScript Fetch. Streaming se
habilita por documento tras HTTP 403 directo sin redirección, con
cupo de tiempo, crédito e intento, para un PDF rector cuyo enlace
identifica únicamente el DocumentId en la ruta autorizada de SECOP.
Los avisos de invitación sin corroborar y los archivos auxiliares
quedan fuera de esta alternativa.

La respuesta debe ser PDF HTTP 200, con longitud positiva, sin
compresión y hasta 10 MiB. Se leen bloques de hasta 64 KiB dentro
de 12 s de adquisición. La limpieza tiene una ventana separada y
se verifica por el canal de navegador. Se conserva la firma PDF,
la verificación de tamaño y SHA-256 y el recibo para reutilizar el
binario. El intento alternativo usa una plaza del presupuesto
documental y un crédito adicional. El tope del streaming mide
bytes aceptados por EN-01. Los buffers de navegador y sistema
operativo quedan fuera de esa medición.

Se mantiene el corte tras tres fallos documentales consecutivos
repartidos en al menos dos procesos. Un cierre incierto detiene
de inmediato la adquisición y conserva la marca local compartida
que impide continuar los dos comandos. Se guarda el mecanismo y
el diagnóstico depurado junto al documento. DOCX, redirecciones,
respuestas sin tamaño y el piloto de 16 MiB siguen fuera del
streaming. El runner conserva sus topes de feed, tiempo y OCR.

Las pruebas usaron transporte simulado. Verificaron el segundo
cupo tras 403, el rechazo de destinos, formatos y redirecciones
no habilitados, el recibo reutilizable, el cierre incierto y la
reanudación sin feed. Pasaron 201 pruebas y una quedó omitida.
No hubo consultas a CDP, SECOP, inventarios ni feed.

#### Embudo archivado por fuente

| Fuente detectada | Avisos únicos | Fuera del perfil | Servicio principal | Bienes no claros | Pasan prefiltro comercial | Excluidos por inventario de la fuente | Elegibles | Seleccionados |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SECOP II | 165 | 97 | 47 | 5 | 16 | 0 | 16 | 15 |
| SECOP I | 83 | 52 | 23 | 3 | 5 | 5 | 0 | 0 |
| Otros portales | 17 | 10 | 3 | 2 | 2 | 2 | 0 | 0 |
| Universidades | 4 | 2 | 1 | 0 | 1 | 1 | 0 | 0 |
| Total | 269 | 161 | 74 | 10 | 24 | 8 | 16 | 15 |

El discovery identifica las cuatro fuentes. La selección exige
SECOP II con claves documentales verificables. SECOP I y otras
fuentes quedan excluidas de la recuperación de EN-01 aun cuando el
objeto pase el perfil comercial. En el código, el filtro explícito por
fuente se evalúa junto con la capacidad de inventario. El historial
comparable utiliza identidades CO1.NTC. Es una restricción técnica
de adquisición e identidad que reduce la cobertura del objetivo
comercial nacional. Se conservó tal cual.

Régimen Especial es una modalidad. Hubo 23 avisos, 20 en SECOP II
y tres en SECOP I. Dos SECOP II de régimen especial fueron elegibles
y uno entró en la muestra. No hay una exclusión por modalidad: la
mínima cuantía tiene preferencia en el orden. Se ordena primero
por vigencia (abierto antes que desconocido), luego por modalidad
preferida y prioridad comercial, con rotación por departamento
dentro de cada grupo. Los filtros habrían descartado procesos cerrados
o fuera de 30 días. En esta corrida no se aplicó ninguna de esas
dos exclusiones ni se encontró coincidencia con las 61 identidades
históricas. Entre los elegibles hubo 14 abiertos y dos con vigencia
desconocida. La muestra contiene 10 de mínima cuantía, cuatro de
selección abreviada y uno de régimen especial.

Las 21 categorías, 1.130 ubicaciones, exclusiones comerciales y MPNE
conservan su configuración. El contraste con el universo comercial
acordado es la restricción estructural por fuente y la disponibilidad
de metadatos. El feed no trajo UNSPSC ni descripciones en las 270
filas. En esta muestra la clasificación comercial dependió de palabras
clave del objeto. El perfil tampoco permite deducir del archivo qué
ofertas nunca devolvió el proveedor.

El feed paró por cupo tras nueve páginas. Se observó un elegible
sin seleccionar, de régimen especial con vigencia desconocida y
prioridad B. El count final de 271 superó las 270 filas recibidas y
el proveedor no indicó fin de paginación. El límite de páginas y
el cupo pudieron dejar elegibles fuera. El total no es estimable
con los artefactos. El detalle queda en discovery_audit_offline.json
dentro del directorio de la corrida, fuera de Git.

#### Reanudación acotada propuesta

El lector de la selección archivada recupera los 15 avisos pendientes.
Ordena primero los dos que ya tienen resultado de inventario
y luego los 13 que no alcanzaron esa etapa. Los que ya obtuvieron
una conclusión formal en la reanudación se excluyen y los recibos se
verifican por hash antes de descargar. Se consultan sólo inventarios de
la selección archivada. Se omiten el feed y su preflight.

Propuesta inicial para autorizar: hasta dos procesos, Yumbo y El
Peñol, con 8 plazas de presupuesto documental que preservan la
reserva existente de corroboración. El tope por proceso es tres
intentos y hasta dos OCR por PDF. Mantener 10 MiB, 200 créditos y
720 s como techos vigentes y dejar los otros 13 para una evaluación
posterior. El indicador de streaming es explícito.

```powershell
$env:PYTHONPATH = (Resolve-Path './backend/src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython './backend/scripts/eureka_nacional_en01.py' `
  --exploratory --resume-inventory-from en01-abu8_p7u `
  --processes 2 --documents 8 --ocr-pages 2 --edge-stream-fallback `
  --cdp-url 'http://127.0.0.1:9232' `
  --tesseract 'C:/Program Files/Tesseract-OCR/tesseract.exe'
```

El comando queda pendiente de autorización. La integración nacional
actual se verificó offline. No se recuperó ninguno de los 15 ni se
repitió el descubrimiento.


### Auditoría técnica offline de SECOP I

En en01-abu8_p7u, cinco de los 83 avisos SECOP I superaron el
prefiltro comercial. Los cinco conservan identidad secop1 con
numConstancia, referencia, entidad, objeto, departamento, fecha,
presupuesto, modalidad, categoría derivada e identificadores
internos del agregador. Tres conservan fecha límite y aparecen
abiertos en el snapshot. En dos la vigencia figura desconocida.
No hay idUltimaFase, UNSPSC, enlace oficial persistido ni
inventario para ninguno de los cinco.

| Referencia | Departamento | Modalidad | Categoría derivada | Vigencia archivada |
| --- | --- | --- | --- | --- |
| MC-050-2026 | Tolima | Mínima cuantía | Ferretería | Abierto |
| S.A.S.I-002-2026 | Tolima | Subasta inversa | Informática | Desconocida |
| SASI-006-2026 | Risaralda | Subasta inversa | Repuestos | Desconocida |
| MC-SPM-055-2026 | Tolima | Mínima cuantía | Informática | Abierto |
| MC-049-2026 | Tolima | Mínima cuantía | Papelería | Abierto |

El runner obtiene la constancia de la referencia de origen antes
de retirar el enlace raw. Su normalizador de URL reutiliza la
validación de descarga SECOP II y no guarda el enlace de SECOP I.
El test de identidad del agregador muestra el patrón
contratos.gov.co/consultas/detalleProceso.do con numConstancia.
La constancia permite formular una URL candidata para verificación
posterior. El archivo no acredita vigencia del enlace, HTML
actual ni URLs de sus documentos.

**Infraestructura reutilizable.** El agregador conserva identidad
SECOP I y admite revisión con metadatos cuando la estrategia
documental no está verificada. Su interfaz acepta una capacidad
explícita. La implementación de inventario CDP requiere tres
claves, incluida idUltimaFase. El parser documental actual
requiere la URL permitida y DocumentId. El descargador y el
streaming de SECOP II están limitados a community.secop.gov.co.
Ninguna de esas piezas ofrece una ruta probada para adquirir
los cinco expedientes.

El adaptador Socrata existente modela identidad documental,
paginación y detección de inconsistencias. Apunta a dmgg-8hin,
con llave de proceso o contrato correspondiente al esquema de
SECOP II. La documentación D1 anota f789-7hwg para procesos de
SECOP I y ps88-5e3v para sus archivos. Los artefactos locales no
validan la llave de unión ni cobertura de ese inventario documental.
Se reutilizarían SourceDocument y los patrones de validación
con una política de solicitudes compatible con los topes de EN-01.

**Propuesta acotada, sin implementación ni consultas a SECOP I.**

1. Con autorización separada, tomar una constancia que apareciera
   abierta. Verificar identidad y vigencia contra el expediente
   oficial. Comprobar si su página aporta un inventario por
   numConstancia o si conviene el catálogo público de archivos.
   Exigir unión por identidad oficial y enlaces verificables.
2. Reutilizar el ranking de EN-01 para invitaciones y pliegos
   definitivos. Validar portada, versión e identidad si el título
   es ambiguo. Usar estudios previos como soporte y anexos
   habilitantes y adendas para corroboración. Separar avisos
   y borradores de los documentos rectores.
3. Tras validar la adquisición, añadir sólo una estrategia
   optativa por fuente en EN-01 y una llave documental que
   incluya la constancia. Reutilizar la interfaz documental,
   almacenamiento por SHA-256, extractor, OCR selectivo y
   clasificador contextual. Conservar rol, página o locador
   y cobertura. El expediente sin rector queda abierto y
   la prioridad comercial se mantiene separada.
4. Mantener el camino SECOP II y sus hosts autorizados. Validar
   host, redirecciones y formato de SECOP I por separado.
   En el piloto inicial, un inventario por constancia y hasta
   un PDF rector, con 10 MiB, 12 s y hasta dos páginas OCR.

Pasaron las 21 pruebas offline del agregador, incluidas identidad
por constancia y rechazo de inventario sin capacidad verificada.
No se consultó SECOP I ni se implementó un adaptador nuevo.


### Reanudación de Yumbo y El Peñol desde d753731

El 26 de noviembre de 2026 se ejecutó una sola vez el comando
aprobado de reanudación con la selección archivada de en01-abu8_p7u.
Los arranques de la pestaña que no expusieron el cliente del portal
se detuvieron antes del comando y no enviaron inventarios. La
pestaña operativa usó el cliente Axios de la aplicación sin alias.
Su inicialización normal obtuvo HTTP 200. La guarda no envió
el feed y el runner no ejecutó su preflight.

| Proceso | Resultado |
| --- | --- |
| Yumbo MC-RF-016-2026 | Dos respuestas de inventario HTTP 200. El rechazo directo compatible con 403 sin redirección activó la rama de fallback. La ejecución se interrumpió antes de iniciar el streaming. |
| El Peñol MC-039-2026 | La ejecución no alcanzó su inventario. |

La integración llamó asyncio.run desde el runner síncrono de
Playwright, que ya ejecuta un bucle en el mismo hilo. Python
devolvió RuntimeError y avisó que la corrutina stream_pdf nunca
fue esperada. El problema se reprodujo offline con un bucle
activo. El paso por la rama de fallback acredita el criterio que
lo activó. El error interrumpió la persistencia del caso individual,
por lo que no quedó un diagnóstico HTTP por documento en esta
reanudación. El registro marca una plaza de Edge reservada.
No hubo GET de streaming, bytes, recibos, OCR ni IA. La verificación
local de Edge encontró cero pestañas al terminar.

El runner consumió 9 créditos presupuestarios y 6,375 s. La
ejecución supervisada tardó 10,047 s. No se emitió ninguna
clasificación nueva. Los resultados históricos de ambos
procesos permanecen not_resolved y evidencia insuficiente.
La traza local se conserva en en01-resume_abu8_p7u. Se
mantuvo la marca preventiva que se creó al entrar al fallback.
No se relanzó el lote ni se consultaron los otros 13 procesos.

El ajuste propuesto es aislar la adquisición asíncrona en un
trabajador con su propio bucle y conexión CDP. Mantener los
topes y publicar el diagnóstico antes de salir ante un fallo
de integración. Una regresión debe iniciar el fallback desde
un llamador con bucle activo y verificar que el trabajador
respeta cierre y límites. Antes de reutilizar la marca local
hay que verificar que el nuevo flujo deja un estado seguro.
Una nueva ejecución de Yumbo y El Peñol requiere autorización
adicional.


### Corrección del bucle y próximas pruebas controladas

El runner síncrono de Playwright ya tiene un bucle activo en su
hilo. CDP Streaming ahora se ejecuta en un proceso hijo de EN-01
con su propio bucle y conexión CDP. El runner nacional y el de
recuperación conservan la misma función de adquisición. El
intercambio con el trabajador usa entrada estándar y devuelve
estados depurados y metadatos del binario. Los recibos siguen
permitiendo reutilizar archivos verificados sin nuevas solicitudes.

El trabajador conserva un solo GET, el límite de adquisición de
12 s, el tamaño declarado obligatorio entre 1 byte y 10 MiB y
lecturas de hasta 64 KiB por bloque. El padre supervisa hasta 35 s
incluidos arranque y cierre, dentro de la reserva de 38 s del
runner. Sólo conserva el archivo definitivo si tiene confirmación
de cierre del flujo y de la pestaña, confirmación de cancelación de
la navegación interceptada, salida del trabajador y verificación
local de firma PDF, tamaño y SHA-256. El archivo intermedio se
limpia al terminar. Si el trabajador sale sin acreditar que cerró
la pestaña o que no abrió ninguna, la marca preventiva permanece.
Terminar el proceso hijo verifica su salida como proceso de Python.
El cierre de Edge y sus búferes internos requiere confirmación
independiente del navegador.

Las regresiones offline finalizaron con 207 pruebas aprobadas y
una omitida. El fallback simulado se invocó desde el contexto real
de Playwright síncrono con bucle activo, usando un proceso hijo
sintético. Se verificaron aceptación, cancelación, salida del
trabajador, SHA-256, limpieza temporal, bloqueo tras timeout o
cierre incierto, reutilización por recibo y contabilidad de
intentos y créditos en ambos flujos.

El laboratorio de Edge aislado en loopback aprobó diez escenarios.
Verificó un PDF válido, rechazo de sobrepeso declarado y de
contenido truncado, corte por demora de cuerpo o cabeceras a
12,015 y 12,016 s, pérdida de CDP, bloqueo por cierre incierto y
recuperación controlada. También verificó el tope al leer una
respuesta sintética sin tamaño declarado. En producción, ese
tipo de respuesta se rechaza antes de leer el cuerpo.

**Yumbo y El Peñol.** Con autorización nueva, revisar primero en
loopback el estado de Edge, la ausencia de un trabajador anterior y
de una pestaña temporal pendiente. Conservar la marca de la
interrupción anterior hasta verificar el estado y registrar el
desbloqueo explícito. Si no puede verificarse, detenerse antes de
enviar solicitudes. Ejecutar una sola vez el comando de
[reanudación acotada](#reanudación-acotada-propuesta). Debe incluir
únicamente Yumbo MC-RF-016-2026 y El Peñol MC-039-2026,
sin feed ni preflight del feed. Verificar los recibos existentes
antes de adquirir. Mantener los límites del comando y el fallback
únicamente tras un 403 directo sin redirección en un PDF elegible.
Las ocho plazas preservan la reserva de corroboración y el tope de
tres intentos por proceso permite como máximo seis intentos
documentales en ese lote. Registrar solicitudes y créditos,
vía documental, bytes, SHA-256, cierres, cobertura y conclusión.
Detener la adquisición si reaparece un cierre incierto o se activa
el corte por fallos generalizados.

**SECOP I.** Seleccionar la constancia `26-13-14852794`,
Casabianca MC-SPM-055-2026, uno de los cinco candidatos archivados
que pasaron el prefiltro. Su aviso aparecía abierto y registraba
cierre el 1 de diciembre de 2026 a las 17:30 de Bogotá, el más
tardío entre los tres abiertos con fecha archivada. La vigencia
actual y el acceso documental requieren validación.

1. Con autorización separada, consultar una sola ficha oficial
   usando la URL candidata deducida del patrón probado offline
   `https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=26-13-14852794`.
   Verificar HTTPS, origen oficial, constancia, referencia, entidad
   y vigencia. Detenerse ante redirección a otro host, error,
   expediente distinto o falta de un inventario verificable en esa
   ficha. No probar catálogos, búsquedas ni otros expedientes.
2. Elegir una invitación vigente o un rector inequívoco por título,
   tipo y versión. Dejar estudios previos, anexos habilitantes,
   avisos o borradores como soporte cuando no acrediten ser el
   documento rector. Exigir que el enlace pertenezca al inventario
   y que su destino oficial se pueda verificar antes de adquirir.
   Si hay identidad o rol ambiguos, detenerse.
3. Autorizar como máximo un intento de descarga directa del PDF,
   hasta 10 MiB y 12 s, sin reintentos ni reutilización del
   fallback específico de SECOP II. Si se recibe, verificar firma,
   integridad básica, tamaño, SHA-256 y portada cuando corresponda.
   Asociar el archivo local con la constancia y la identidad
   documental verificada. Entregar ese binario y sus metadatos a
   `extract_document` para usar extracción nativa completa y
   hasta dos páginas de OCR selectivo. Usar el clasificador
   contextual y guardar procedencia, rol, página, fragmento y
   cobertura. La prioridad comercial y el estado formal se reportan
   por separado. Un solo rector puede dejar corroboración pendiente.
   IA generativa en cero.

Estas pruebas reales requieren permisos independientes. La
corrección offline no ejecutó la reanudación ni consultó SECOP I.


### Verificación previa a la reanudación autorizada desde b41bff8

La selección archivada comienza con Yumbo MC-RF-016-2026 y
El Peñol MC-039-2026. Antes de retirar la marca preventiva se
verificó Edge dedicado en loopback. El navegador no tenía
pestañas ni destinos temporales de adquisición. No se encontró
ningún trabajador de Streaming. El historial interno de Edge
mostró un elemento completado y 18 retirados, sin estados
activos o pendientes entre los elementos registrados. La pestaña
local utilizada para esa comprobación se cerró. El registro de
la ejecución interrumpida seguía con cero documentos recuperados
y cero análisis.

El intento supervisado de preparar la pestaña se detuvo al agotar
la espera por el cliente Axios de la aplicación. El supervisor
bloqueó la petición automática al feed y otras tres solicitudes
POST ajenas al inventario autorizado. No se iniciaron el runner,
los inventarios ni los intentos documentales de la reanudación.
La marca original se conservó y el arranque no consumió créditos
de EN-01. Sigue pendiente la comprobación del trabajador contra
la sesión autorizada.

| Proceso | Intentos documentales nuevos | Cobertura y clasificación |
| --- | ---: | --- |
| Yumbo MC-RF-016-2026 | 0 | Sin extracción nueva. Sigue not_resolved con evidencia insuficiente. |
| El Peñol MC-039-2026 | 0 | Sin extracción nueva. Sigue not_resolved con evidencia insuficiente. |

El procedimiento operativo requiere que el propietario entre
manualmente a Contratos y deje una sola pestaña funcional en
el Edge dedicado. La comprobación de preparación es local y no
envía inventarios. Una vez lista la pestaña, comprobar otra vez
que no haya un trabajador ni un destino de adquisición abierto,
archivar la marca anterior y ejecutar la única reanudación
autorizada para ambos procesos. La prueba SECOP I sigue
independiente y pendiente de autorización.


### Resultado de la reanudación real con el trabajador de b41bff8

El 26 de noviembre de 2026, el Edge dedicado expuso una única
pestaña de Contratos con el cliente de la aplicación disponible.
La pestaña adicional era la página del portal que abrió
Contratos. El supervisor local distinguió esa relación de una
pestaña de adquisición. La vista interna de descargas sólo
mostró estados terminales. No había trabajadores de Streaming.
Se preservaron la marca y los artefactos anteriores en un
directorio local de respaldo antes de ejecutar el lote.

Se ejecutó una sola reanudación con la selección archivada.
Cuatro solicitudes de inventario correspondieron exclusivamente
a los dos procesos autorizados. El feed y su preflight se
omitieron. Cada inventario devolvió cinco documentos. En ambos
casos se priorizó la invitación pública.

| Proceso | Intentos y mecanismo | Cobertura | Estado formal y prioridad |
| --- | --- | --- | --- |
| Yumbo MC-RF-016-2026 | Dos. urllib devolvió HTTP 403 sin redirección. El trabajador CDP terminó con TimeoutError antes de abrir una pestaña de adquisición. | Una invitación priorizada entre cinco documentos. 0 descargados, 0 páginas. | not_resolved, evidencia insuficiente. 9 créditos y 14,843 s. |
| El Peñol MC-039-2026 | Dos. urllib devolvió HTTP 403 sin redirección. El trabajador CDP terminó con TimeoutError antes de abrir una pestaña de adquisición. | Una invitación priorizada entre cinco documentos. 0 descargados, 0 páginas. | not_resolved, evidencia insuficiente. 9 créditos y 14,719 s. |

El trabajador se invocó desde el runner real con Playwright
síncrono y salió en ambos casos, superando el error anterior de
bucle activo. La adquisición mediante Streaming sigue sin
validarse en este runner. Las trazas registraron protocol_error
y TimeoutError de Playwright, con tab_opened falso y cero
solicitudes de Streaming reenviadas. El fallo ocurrió antes
de la apertura de una pestaña de adquisición. La traza no
identifica el paso exacto del arranque que agotó el tiempo.
El navegador seguía mostrando únicamente las dos pestañas
originales al terminar. Se comprobó que no quedaban
trabajadores ni una marca de cierre incierto. Al no haber
archivos, no se generaron recibos ni se verificó un flujo de
cuerpo. Tampoco hubo extracción u OCR.

Resultado parcial, código 2. En total, dos procesos
inventariados, cuatro intentos documentales, dos fallbacks,
18 créditos, 29,578 s de ejecución, 0,281 s de CPU del
runner padre, 0 bytes, 0 páginas y 0 llamadas de IA. La
selección se detuvo por el cupo ordinario de documentos.

Como siguiente diagnóstico, instrumentar offline los pasos de
arranque del trabajador y reproducir la conexión concurrente
de dos clientes al mismo Edge aislado en loopback. Distinguir
arranque del cliente, conexión CDP y creación de sesión del
navegador usando estados depurados. Cualquier nueva adquisición
documental requiere autorización. No se consultó SECOP I.


### Diagnóstico offline del timeout de arranque

La traza de 43afe55 acredita la salida de ambos trabajadores
antes de abrir una pestaña de adquisición y con cero GET
reenviados. En ese momento todavía no se registraba el paso
exacto de arranque. Las sondas independientes de Moniquirá y
del piloto de tres procesos sí interceptaron documentos.
Operaban sin un cliente de Playwright síncrono bloqueado
mientras conservaba una ruta activa sobre la página inicial.

Se reprodujo esa diferencia en Edge aislado y loopback. El
segundo cliente CDP se conectó con el primero abierto y en
reposo, con una ruta inactiva y con una solicitud sintética
de subrecurso pendiente. Cuando una navegación sintética
quedó interceptada por la ruta y el hilo padre esperó de
forma bloqueante, la conexión CDP del hijo agotó el tiempo.
Al volver a despachar rutas en el padre, el segundo cliente
pudo conectarse.

| Trabajo controlado con el proceso hijo real | Resultado |
| --- | --- |
| Navegación pendiente y espera bloqueante | `TimeoutError` en `cdp_connect`. 9,359 s de pared en el laboratorio, cero rutas atendidas durante la espera y cero GET de adquisición. |
| Misma navegación, con el despacho de eventos del padre activo | La ruta se atendió y el hijo pasó a `context_lookup` en 3,953 s de pared. Terminó con `authorized_tab_unavailable` al encontrar únicamente el origen sintético. Cero GET de adquisición. |

En ambas pruebas terminó el trabajador, no se abrió la
pestaña de adquisición y se retiró la marca. Se comprobó una
causa concreta para el timeout reproducido. Los registros de
Yumbo y El Peñol no permiten demostrar que esa condición
estaba presente durante su reanudación.

El runner nacional ahora espera al mismo proceso hijo en un
hilo auxiliar, mientras el hilo que posee Playwright despacha
sus eventos. La vía independiente conserva la espera directa.
La traza identifica el arranque del driver, la conexión CDP,
la búsqueda del contexto existente, la sesión CDP del
navegador, apertura y validación de la pestaña, sesión CDP de
página, configuración de la interceptación y preparación del
enlace. También conserva la etapa de adquisición y el tipo de
excepción. Un proceso eliminado por el supervisor sin
respuesta conserva el bloqueo preventivo y sólo acredita el
timeout del trabajador.

Se mantienen un GET por fallback, los topes de tiempo, tamaño,
intentos y créditos, y el criterio HTTP 403 directo sin
redirección. Un fallo seguro queda registrado en su documento
y permite seguir con el proceso siguiente. La marca de cierre
incierto detiene el lote de inmediato. Tres fallos
consecutivos que cubren al menos dos procesos activan el corte
existente. La prueba con un fallo de arranque seguido de una
adquisición simulada verifica la continuación, la reutilización
por recibo y el bloqueo posterior cuando el cierre es incierto.

Pasaron 231 pruebas offline de EN-01, almacenamiento y
agregador, incluida la prueba OCR con Tesseract local.
También pasaron los diez escenarios del laboratorio de
Streaming, incluidos cancelación, exceso de tamaño, pérdida
de CDP, rechazo de PDF incompleto y bloqueo por cierre
incierto. Las pruebas usaron respuestas sintéticas o archivos
locales.

#### Próxima capacidad de cobertura SECOP I

Se volvió a confirmar offline que cinco candidatos SECOP I
quedaron excluidos por capacidad documental. Para una primera
validación separada, mantener sólo Casabianca MC-SPM-055-2026,
constancia `26-13-14852794`. El archivo registra el cierre
para el 1 de diciembre de 2026 a las 17:30 de Bogotá. El
estado vigente debe verificarse en la ficha oficial.

Con autorización, consultar una sola ficha oficial derivada
del patrón local por constancia, conforme al
[procedimiento preparado](#corrección-del-bucle-y-próximas-pruebas-controladas).
Si identidad y rector son verificables, realizar como máximo
un GET de un PDF rector, 10 MiB y 12 s, y conservar metadatos,
integridad y cobertura. Aplicar extracción nativa y hasta
dos páginas de OCR selectivo con el clasificador existente.
Informar por separado estado formal y prioridad comercial.
Detenerse si la ficha o el enlace no son verificables, si
el documento no es rector o si se excede una guarda. Esta
fase no implementó un adaptador ni usó la vía CDP de SECOP II
para SECOP I. Yumbo y El Peñol quedan cerrados para este
incremento y sus descargas no se repitieron.


### Prueba real de ficha SECOP I de Casabianca

El 26 de noviembre de 2026 se consultó una sola vez la ficha
oficial candidata del Municipio de Casabianca, Tolima, proceso
MC-SPM-055-2026, constancia 26-13-14852794. Se usó un GET
HTTPS directo al endpoint de detalle documentado en el plan.
Se mantuvo la validación TLS normal y no se habilitaron
redirecciones ni reintentos. La respuesta a ese GET fue HTTP
403 con Content-Type text/html en la etapa de cabeceras.
La prueba duró 0,687 s. No se leyó el cuerpo de la respuesta.

La identidad del proceso coincide con los datos del archivo
local de discovery, que registra modalidad de mínima cuantía,
presupuesto de COP 40.000.000 y cierre previsto para el 1 de
diciembre de 2026 a las 17:30 de Bogotá. La ficha no pudo
confirmar esos datos ni su vigencia. El 403 tampoco permite
determinar el motivo del rechazo ni la disponibilidad de la
ficha mediante una sesión normalmente autorizada.

| Comprobación | Resultado |
| --- | --- |
| Ficha oficial por GET directo | HTTP 403. Cero bytes de cuerpo leídos. |
| Inventario y rector | Sin inventario oficial verificable. No se identificó rector. |
| Adquisición documental | Cero intentos de PDF, cero archivos y cero recibos. |
| Extracción y clasificación | Cero páginas nativas, OCR e IA. Estado de cobertura not_resolved por evidencia insuficiente, sin clasificación nueva del motor ni conclusión sobre experiencia. |

El registro técnico y el marcador del intento único quedan
locales. No se probaron enlaces alternativos ni otros
procesos. No se tocó el feed, Yumbo ni El Peñol.

**Incremento mínimo propuesto.** Con autorización separada,
verificar primero si la ficha o un inventario oficial de esta
misma constancia es accesible mediante navegación normal.
Si existe un rector inequívoco y una ruta autorizada, validar
un solo PDF con 10 MiB, 12 s y hasta dos páginas OCR. Si sólo
es viable la descarga manual, verificar la procedencia e
identidad y entregar el archivo local al almacenamiento por
SHA-256 y al extractor EN-01. Conservar constancia, identidad
documental, rol, cobertura y evidencia por página. Cuando se
haya comprobado un enlace o inventario repetible, agregar
únicamente resolución de identidad e inventario por fuente
y reutilizar almacenamiento, extracción, OCR, clasificador y
prioridad comercial. Mantener separada la adquisición SECOP
II hasta medir el mecanismo de SECOP I. Sin evidencia
documental el proceso sigue abierto para revisión.


### Navegación controlada en Edge a la ficha SECOP I de Casabianca

La prueba del 26 de noviembre de 2026 usó el Edge CDP dedicado
para el proceso MC-SPM-055-2026 del Municipio de Casabianca,
Tolima, constancia 26-13-14852794. Playwright agotó la espera
al conectar antes de navegar. DevTools respondió en loopback
y se utilizó Page.navigate del mismo CDP para abrir la ficha
en una pestaña aislada. Se envió un solo GET de detalle.
La navegación devolvió HTTP 200, Content-Type text/html y
DOM cargado en 1,219 s. La ficha mostró la referencia
y la entidad esperadas. Se verificó el cierre de la pestaña
de la prueba al terminar.

Se observaron cinco documentos en la ficha.

| Tipo mostrado | Documento | Tamaño mostrado |
| --- | --- | --- |
| Invitación | INVITACION | 1,80 MB |
| Documento Adicional | ESTUDIOS PREVIOS | 675 KB |
| Documento Adicional | ESTUDIO DEL SECTOR | 1,49 MB |
| Documento Adicional | PLAN DE COMPRAS | 128 KB |
| Documento Adicional | BANCO DE PROYECTOS | 129 KB |

La invitación fue el único candidato a rector por título.
El contenido contractual y su formato real siguen pendientes
de confirmación. Se observó que su control oficial invoca
reCAPTCHA antes de abrir el archivo y que no expone un
enlace de descarga directa en el control. Los mecanismos
validados por EN-01 no cubren ese flujo con las guardas
acordadas de 10 MiB y 12 s. La prueba se detuvo sin activar
el control ni usar una ruta alternativa. Hubo cero intentos
de descarga, cero bytes de PDF, cero páginas, cero OCR y
cero IA. El estado sigue not_resolved por evidencia
insuficiente. No se ejecutó el clasificador sobre un archivo.

El 403 del GET directo anterior y el 200 de la navegación
Edge son observaciones bajo mecanismos distintos. El ensayo
no aisló qué condición produjo el 403. La validación del
control documental es un hallazgo separado y no explica
por sí sola la respuesta de la ficha.

Para ampliar cobertura, el siguiente paso acotado sería
obtener la invitación por el control oficial con intervención
humana autorizada y verificar su procedencia e identidad
antes de reutilizar almacenamiento, extracción, OCR y
clasificador de EN-01. El acceso a la ficha y al inventario
queda demostrado para esta constancia. La adquisición
automática de documentos de SECOP I sigue pendiente de una
ruta autorizada y verificable dentro de los límites. No se
amplió la implementación ni se consultaron otros procesos.


### Inventarios SECOP I de Licitaciones.info

Se leyó el JavaScript que ya estaba cargado en Edge mediante
CDP local. No se recargó la pestaña ni se llamó al proveedor.
El componente AccionesDocumentos.js confirma que
openDocumentoSecop1 pasa la ruta relativa a descargaUnicaSecop1.
En la rama Colombia, el componente envía un formulario POST
al servicio HTTPS oficial de contratos.gov.co, ruta
/consultas/VerDocumento. El formulario envía la ruta sin
reconstruirla, como valor del campo ruta, con destino _blank.
El código maneja aparte enlaces de almacenamiento que ya son
absolutos. La reproducción manual del propietario acredita
que el control funciona para su ejemplo. La ruta relativa se
trata como dato del formulario y no se convierte en URL pública.

El código de inventario del proveedor usa
/cliente/contratos/obtener-documentos-proceso y envía
idContrato, id_fuente_contract, idUltimaFase y page. Después
lee cantidad y documentos.campos. Las claves provienen del
evento de ficha del proveedor. Los avisos SECOP I archivados
sin idUltimaFase no permiten deducir ese valor ni practicar
una solicitud autorizada. No se verificó en vivo el formato
exacto de una fila SECOP I ni el valor admitido para una fase
faltante. El parser SECOP II sigue dedicado a sus enlaces
RetrieveFile con DocumentId.

**Validación de inventario disponible offline.** El módulo
eureka_nacional_secop1_inventory recibe un JSON local normalizado
con constancia, process_reference y documents. Cada documento
aporta name, extension, size_bytes en bytes exactos o null y
relative_path. La constancia debe aparecer como segmento
exacto de la ruta y coincidir con la del nombre de archivo
cuando éste contiene el patrón de proceso. La extensión
declarada debe concordar con el sufijo. Las rutas absolutas,
de red, con parámetros, codificaciones o recorrido de
directorios se rechazan. Una fila inválida no invalida las
demás. Se deduplican rutas idénticas y se excluyen metadatos
conflictivos para la misma ruta. La salida conserva un
identificador estable derivado de la constancia y del SHA-256
de la ruta, sin publicar la ruta. Ese hash identifica la fila.
El SHA-256 del binario debe calcularse sobre el archivo
real. Se reutiliza el ranking de EN-01 por título y se
conserva cobertura pendiente. El tamaño declarado en el
inventario es preliminar. Un valor faltante queda registrado
y un valor superior a 10 MiB queda fuera de ese presupuesto.

Para validar un archivo local preparado en ese formato, fijar
PYTHONPATH a backend/src y ejecutar desde el worktree experimental
python backend/scripts/eureka_nacional_secop1_inventory.py con
la ruta al JSON local. El normalizador carece de operaciones
de navegador o red y marca explícitamente la adquisición
automática como desactivada. No se conecta al runner nacional
ni modifica el parser de SECOP II.

**Laboratorio de POST sintético.** Una navegación por
formulario entre dos orígenes loopback permitió verificar
por CDP destino, método, marco y un campo ruta exacto antes
de continuar un único POST. La respuesta PDF de 431 bytes
se leyó por bloques con las guardas existentes y coincidió
por SHA-256 con la muestra. Se confirmaron EOF, cierre del
flujo, aborto de la navegación interceptada y cierre de la
pestaña. Las respuestas con longitud declarada por encima de
10 MiB, sin longitud o con redirección se rechazaron sin leer
el cuerpo. Se confirmó el cierre en los cuatro escenarios.
Se reutilizaron response_length, read_stream y close_target.
El laboratorio no valida el destino _blank creado por el
componente real, tiempos de la sesión autorizada, respuesta
del servicio oficial ni el comportamiento ante sus controles
de acceso. El gestor nativo aún carece de un límite estricto
sobre los bytes transferidos y no se habilitó como alternativa.

Pasaron 245 pruebas offline, incluidas las 14 regresiones
del nuevo normalizador y la prueba de OCR local. La ruta de
ejemplo proporcionada por el propietario también pasó el
cotejo offline de constancia, formato y rol. El tamaño
exacto no estaba en el ejemplo.

**Propuesta de una sola constancia.** Con autorización nueva,
usar 26-13-14853238, el ejemplo que el propietario ya verificó
manualmente. Confirmar primero la identidad del proceso en
su ficha de Licitaciones.info y usar exclusivamente las claves
documentales de esa ficha. Leer un solo inventario inicial
de ese proceso, validar la fila de invitación y cotejar sus
metadatos y ruta con la constancia. Antes de activar el
control oficial, verificar que la interceptación puede quedar
armada en la pestaña de destino. Si no puede verificarse,
detenerse sin solicitar el PDF. Si las guardas están listas,
permitir un único POST coincidente, sin redirecciones ni
reintentos, con un máximo de 10 MiB aceptados y 12 s. Ante
CAPTCHA, autenticación adicional, destino no previsto o
cierre incierto, detener el procedimiento. El tope de la
sonda es una solicitud de inventario y un intento documental
con un único POST. Registrar método, resultado, cierre y
consumo sin rutas completas, tokens ni cabeceras sensibles.

Si se recupera el PDF, verificar firma, estructura básica,
tamaño y SHA-256 con LocalBinaryStorage y su relectura
verificada. Registrar un recibo que asocie constancia,
identidad de la ruta y hash del binario. Reutilizarlo en
lugar de duplicar la adquisición. Pasar el archivo a la
extracción EN-01, mantener hasta dos páginas OCR y aplicar
reconocimiento de portada, clasificador y prioridad
comercial. Mantener la cobertura pendiente de documentos
complementarios cuando corresponda. El tope de EN-01 protege
bytes aceptados y tiempo de adquisición. No mide todos los
búferes de Edge o del sistema. Esta fase no ejecutó esa
prueba ni realizó descargas reales.


### Sonda real SECOP I por formulario POST en Encino

El 26 de noviembre de 2026, la sesión de Licitaciones.info
ya tenía en memoria un registro de SECOP I con la constancia
26-13-14853238. Confirmó Municipio de Encino, Santander, y
la referencia MC-014-2026. Se envió una sola solicitud
autenticada de inventario al endpoint existente con las claves
observadas. idUltimaFase tenía el valor explícito null en ese
registro. El endpoint devolvió HTTP 200 y declaró seis filas.
No se volvió a consultar el feed ni se dedujo una fase.

| Documento | Formato | Tamaño mostrado |
| --- | --- | --- |
| Invitación | PDF | 5,39 MB |
| Estudios previos | PDF | 4,55 MB |
| Estudios del sector | PDF | 1,88 MB |
| CDP | PDF | 151 KB |
| BPIN | PDF | 225 KB |
| PAA | PDF | 239 KB |

Las filas correspondieron a las columnas Nombre, Tipo,
Tamaño, Fecha publicación del documento y Documento. En
las seis, el control del documento llamó al componente del
proveedor y la ruta incluía la constancia exacta. Se usó el
ranking existente y la invitación fue el único rector por
título. La ficha indica un tamaño visual redondeado. La
longitud HTTP exacta y el contenido quedaron sin verificar.

Antes de invocar el control real se probó en Edge aislado
la pausa automática de la pestaña emergente y la captura
del POST sintético antes de enviarlo. En la sesión real se
habilitó esa pausa y se invocó una sola vez el control
oficial. Apareció un destino nuevo que el protocolo local
no pudo asociar con la pestaña de origen. El supervisor
registró unexpected_new_target en la etapa paused_popup.
La guarda no continuó ningún POST vía Fetch. El código
temporal de limpieza reanudó el destino no identificado
al retirar la autoasociación. Esa acción dejó la descarga
fuera de la intercepción.

Edge registró una descarga nativa completada y la inspección
local encontró un archivo nuevo de 5.651.103 bytes cuyo
nombre coincide con el rector elegido. Se creó 0,861 s
después de iniciar el intento según los metadatos locales.
En la prueba no se observó el código HTTP ni la longitud
declarada y no se acreditó la aplicación efectiva de las
guardas de 10 MiB y 12 s. Tampoco se verificaron la firma,
SHA-256 y cierre del flujo de adquisición. El archivo
nativo quedó fuera del corpus de EN-01 y no se abrió ni se
movió. Cero archivos aceptados por CDP, recibos, páginas
procesadas, OCR y llamadas de IA. El caso queda
not_resolved por evidencia insuficiente.

La inspección posterior encontró únicamente la pestaña
original de Licitaciones.info y descargas en estado
terminal entre las registradas. Se conservó la marca
preventiva porque el cierre de la transferencia controlada
no se verificó. Hubo una sola activación del control, sin
reintentos ni uso de mecanismos alternativos. Las trazas,
rutas y el detalle local del inventario quedan fuera de Git.

**Recomendación.** La prueba acredita disponibilidad del
inventario SECOP I mediante Licitaciones.info para esta
constancia. Usar el contrato observado como fixture depurado
para extender primero el parser experimental con claves
de expediente verificadas, incluso fase nula sólo cuando
provenga del registro exacto. La adquisición automática
debe seguir desactivada. Antes de otra sonda, demostrar en
un laboratorio entre orígenes que un destino sin identidad
confirmada permanece bloqueado durante el cierre y
desactivar la autoasociación sólo tras verificar que no puede
salir el POST. Una vez acreditado ese control, validar una
sola constancia con autorización nueva. Integrar la
adquisición al descubrimiento sólo después de comprobar el
límite, recibo, extracción y clasificación en ese flujo.


### Cierre seguro de una pestaña SECOP I en un contexto desechable

Se reprodujo en Edge aislado, con dos orígenes loopback,
la condición que invalidó la sonda de Encino. Un formulario
sintético con destino _blank abrió una pestaña sin acceso al
origen. Con el gestor nativo habilitado, el servidor recibió
el POST y Edge notificó una descarga completada aunque la
pestaña carecía de una asociación verificable. La prueba usa
noopener para producir esa condición. La traza real de Encino
sigue sin identificar por qué faltó esa asociación.

La guarda experimental de SECOP I reutiliza el patrón
existente de abrir una pestaña en blanco, verificarla y
armar Fetch antes de enviar el formulario. Se exige un
contexto desechable propio y se confirma por CDP que existe.
Se deniega la descarga nativa a nivel de ese contexto antes
de abrir la pestaña. Se verifica el origen no opaco, la
relación con la pestaña de origen, el contexto y el marco
antes de aceptar el acuse de Fetch.enable. La guarda no
ejecuta el formulario y sigue fuera del runner nacional.

En la limpieza se cierra el contexto entero sin reanudar
destinos ni revocar la denegación nativa. Se confirma que el
identificador del contexto y sus destinos desaparecieron.
La marca sólo se retira cuando se acredita ese cierre y
la salida del trabajador. Si alguna comprobación falla,
se conserva la marca y se impide iniciar otro intento bajo
ese marcador. Se mantuvo la marca real de Encino.

| Regresión | Resultado offline |
| --- | --- |
| Formulario _blank sin guarda y sin acceso al origen | Un POST sintético y descarga nativa completada. |
| Pestaña asociada, contexto propio y Fetch armado | Un POST sintético verificado, 431 bytes, SHA-256 concordante y cierre del flujo. |
| Pestaña sin origen verificable | Rechazo antes del envío. Cero POST. Contexto y pestañas cerrados. |
| Pestaña cerrada antes de activar Fetch | Rechazo antes del envío. Cero POST. Contexto cerrado. |
| Respuesta no interceptada, inyectada sólo en laboratorio | CDP notificó cancelación nativa. El servidor sintético recibió el POST deliberado. Cero archivos nativos conservados. |
| Cierre incierto simulado y salida del trabajador | La marca bloqueó una segunda adquisición. En los cierres verificados se mantuvo hasta confirmar la salida del trabajador. |

Pasaron las seis regresiones focalizadas con
RUN_EN01_POPUP_LAB=1 y 245 pruebas de EN-01 y del agregador.
También pasaron los diez escenarios del laboratorio de
Streaming existente. Se conservaron los límites de 10 MiB,
12 s, los créditos e intentos y el formato de recibos.
Se reutilizaron la lectura por bloques y el almacenamiento
verificado. Las pruebas de recibos cubrieron reutilización e
idempotencia, sin crear recibos de SECOP I reales.

**Conclusión para otra sonda.** La guarda funciona en el
contexto aislado probado. La denegación nativa impide guardar
una respuesta que llegue al navegador. El control anterior
al formulario es el que impide el envío de un POST desde
una pestaña sin verificar. La denegación nativa por sí
sola no acredita ausencia de tráfico o de bytes en búferes.
Antes de considerar otra sonda real, falta demostrar la
sesión autorizada y que el formulario original queda en
un destino prearmado dentro de un contexto cuya disposición
se pueda verificar. El control del proveedor que abre por
sí mismo _blank sigue desactivado para adquisiciones
automáticas. La sesión real y el archivo nativo anterior
quedaron fuera de esta fase. No se emitieron solicitudes
a SECOP, Licitaciones.info ni al feed.


### Compatibilidad offline de sesión y formulario SECOP I

El contrato se cotejó contra la inspección ya registrada de
AccionesDocumentos.js. Para una ruta relativa, la rama
Colombia construye y envía inmediatamente un formulario POST
a /consultas/VerDocumento, con un campo oculto ruta y
destino _blank. El código documentado no recibe un destino
preabierto ni expone una preparación separada del envío.
Invocar ese control sin cambios vuelve a delegar la creación
del destino al navegador. La prueba de Encino demuestra el
riesgo de depender de que ese destino se asocie a tiempo.

**Resultado del laboratorio.** Se usó Edge aislado y dos
sitios sintéticos loopback. Una sesión emitida por el
formulario de login del primer contexto no se compartió con
el contexto desechable. En el contexto protegido, el mismo
login por interfaz estableció una sesión nueva en el
navegador. La respuesta mostró una cookie sintética HttpOnly
y de ámbito de host. Se comprobó el acceso por HTTP a la
página protegida sin extraer ni copiar su cookie. Cerrar el
contexto protegido eliminó su sesión. El primer contexto
siguió autenticado y otro contexto nuevo comenzó sin sesión.

Desde la página sintética autenticada se abrió una pestaña
en blanco. Conservó el origen y la asociación con la
página inicial. El formulario HTML en esa pestaña mantuvo
el método POST y el campo ruta. Navegó a un segundo sitio
loopback, con el Origin esperado y Sec-Fetch-Site cross-site.
La cookie del proveedor sintético no llegó al segundo sitio.
Ese sitio no requería una sesión propia. Sus requisitos
reales de cookies, cabeceras u otras comprobaciones quedan
pendientes.

Fetch quedó armado antes de enviar el formulario. Se
verificaron método, marco, destino y dato antes de continuar.
El servidor sintético registró cero solicitudes antes de
la autorización de CDP y recibió un solo POST. La respuesta
de 431 bytes se leyó con las guardas existentes y su
SHA-256 coincidió con la muestra. Se confirmaron cierre
del flujo, aborto de la navegación interceptada y
disposición del contexto. Las regresiones también cubren
el rechazo de un destino no asociado, la cancelación
nativa y el bloqueo ante cierre incierto. Se mantuvo la
marca real de Encino durante toda la validación.

**Conclusión.** El flujo es técnicamente viable si la
autenticación legítima se establece por la interfaz dentro
del propio contexto desechable y el envío usa el mismo
contrato HTML en una pestaña ya preparada. El inicio de
sesión preexistente en otro contexto permanece aislado.
El control del proveedor que crea y envía a _blank de
inmediato sigue fuera del alcance de la guarda. El laboratorio
no acredita que Licitaciones.info permita el inicio de
sesión en ese contexto ni que VerDocumento acepte allí el
POST. La descarga automática permanece desactivada.

Pasaron 252 pruebas offline del conjunto de EN-01 y
agregador, con RUN_EN01_POPUP_LAB=1 y RUN_REAL_OCR=1.
Se incluyeron los siete casos de pestañas SECOP I,
presupuestos y reuso de recibos. El cambio no agrega
transporte, dependencias ni un punto de entrada real.

#### Sonda única propuesta, pendiente de autorización

1. Antes de cualquier acceso, resolver el estado de la marca
   anterior sólo después de verificar que no quedan
   transferencias ni cierres pendientes. Reservar el intento
   y crear un contexto desechable dedicado con descargas
   nativas denegadas.
2. Iniciar sesión manualmente por la interfaz normal dentro
   del contexto bajo prueba. Verificar el origen y el acceso
   autorizado a una sola constancia acordada. Si la sesión
   no puede establecerse o la constancia no puede
   identificarse sin ejecutar el feed, detenerse. Usar un
   inventario ya verificado o consultar como máximo una vez
   el inventario de esa constancia, con las claves de su
   ficha. Elegir un rector inequívoco y verificar su ruta.
3. Abrir una pestaña en blanco asociada. Exigir el acuse de
   Fetch y verificar marco, método, endpoint oficial y un
   único campo ruta. Enviar el formulario HTML con el
   contrato observado desde esa pestaña ya armada. No
   invocar el control que crea un destino nuevo a la vez
   que lo envía. Permitir un solo POST documental de 12 s
   y hasta 10 MiB aceptados. Ante redirección, CAPTCHA,
   sesión adicional, longitud no válida o cierre incierto,
   detener el intento sin reintentos.
4. Verificar cierre del flujo, pestañas, contexto y
   trabajador. Conservar la marca si el cierre es incierto.
   Guardar únicamente el PDF con firma, tamaño y SHA-256
   verificados y un recibo asociado. Reutilizar extracción
   y clasificación con hasta dos páginas OCR y cero IA.
   Publicar sólo el resultado depurado.

Si la sesión real no puede establecerse dentro de ese
contexto, la contingencia ya disponible es la importación
asistida de un PDF obtenido por el control oficial y
verificado por procedencia e identidad. No se probaron
portales ni se ejecutó la sonda real en esta fase.


### Sonda final SECOP I detenida en el preflight de sesión

Para la sonda de Encino, constancia 26-13-14853238, se
verificaron localmente los estados terminales de las
descargas anteriores y la ausencia de destinos de
adquisición. Se archivó la marca de la sonda anterior
y se abrió un contexto desechable con una marca propia,
las descargas nativas denegadas y el feed bloqueado.

El propietario inició sesión manualmente e informó que
el portal mostró una URL inexistente. En la inspección
posterior, se observó una única pestaña de Contratos con
el cliente del portal disponible y sin el mensaje de
error en el contenido de la página. La guarda bloqueó
siete solicitudes del feed. El diagnóstico no permite
determinar si esas solicitudes causaron el aviso.

La comprobación de get-config-user desde la pestaña no
acreditó una sesión válida. El preflight devolvió
authorized_session_unverified. El registro depurado
conservó el resultado booleano de la comprobación.
No se conservó un estado HTTP ni la respuesta, por lo
que queda indeterminado si falló la autenticación, la
ruta o la respuesta esperada por el cliente.

La sonda se detuvo antes de preparar el formulario.
Hubo cero consultas de inventario, cero intentos
documentales, cero POST a VerDocumento, cero bytes
aceptados, cero páginas procesadas, cero OCR y cero IA.
La clasificación histórica de Encino permanece
not_resolved por evidencia insuficiente. Se verificaron
el cierre del contexto y la salida del trabajador.
Se retiró sólo la marca propia de esta sonda. No hubo
descargas o corridas adicionales.

La compatibilidad del formulario permanece demostrada
con la sesión sintética. En la sesión real, el bloqueo
observado fue anterior a la adquisición, al verificar
el acceso autenticado en el contexto desechable.


### Diagnóstico pasivo del 404 de get-config-user

Se ejecutó una única corrida autorizada sin adquisición.
Antes de conectar se verificó en el sistema operativo
que el puerto 9232 pertenecía a un único Edge, sólo en
loopback, con el perfil dedicado de Eureka Nacional y
sin bandera de automatización. El contexto desechable
se creó dentro de ese Edge con la guarda existente,
descargas nativas denegadas, el feed bloqueado y los
hosts oficiales de SECOP bloqueados. Se registraron
sólo estado, origen y ruta.

Observado tras el login manual y la entrada a Contratos
desde la UI: la propia aplicación pidió get-config-user
y recibió 200, igual que get-contadores,
get-contadores-perfiles-nuevos, fuentes-contratos,
get-estados-proceso, colores y broadcasting. No hubo
ninguna respuesta 404. Los únicos fallos fueron cuatro
get-info/MP abortados por la guarda. window.axios no
tiene baseURL y la URL efectiva coincide con la que
respondió 200. navigator.webdriver fue false. El
titular vio el aviso «No encuentro URL».

Conclusión: se descartan la construcción de URL y el
estado de sesión. El aviso corresponde a la
inicialización incompleta por el feed bloqueado, no a
un fallo de autenticación. El 404 de la llamada propia
anterior queda sin reproducir, porque ese diagnóstico
no conservó la URL final y no se repitió la llamada.
El perfil no pudo compararse: el parámetro perfiles no
se registró por diseño. En ese momento el Edge dedicado
no tenía una pestaña de Contratos para comparar. Hubo
cero POST, cero inventarios, cero descargas y cero
consultas voluntarias al feed. El contexto se cerró y
se verificó.


### Preflight pasivo de SECOP I

El módulo `eureka_nacional_secop1_preflight.py`
sustituye la llamada propia a get-config-user por la
clasificación de lo que ya hizo la aplicación en el
contexto desechable. Para declarar la sesión válida
exige:

- Una pestaña desktop de Contratos sin query.
- La petición de arranque de get-config-user, posterior
  al documento de Contratos, con 200 JSON en el host de
  Contratos.
- La ausencia de formulario de login y de respuestas
  401 o 419.
- El cliente del portal disponible.

La navegación vale como legítima sólo si el script
abrió nada más que la portada pública. El perfil se
compara en memoria con `LICITACIONES_PROFILE_ID` a
partir del get-info/MP que la aplicación intenta y la
guarda bloquea. Sólo se registra match, mismatch,
absent, multiple o undetermined, nunca el ID. Un
perfil no confirmado impide la adquisición. El aviso
reconoce «No existe URL» y «No encuentro URL». Si
coincide con el feed bloqueado sin otros errores del
proveedor, se atribuye al bloqueo y no a la sesión. En
cualquier otro caso queda inexplicado y detiene la
sonda.

La sonda local v2 conecta al Edge dedicado por CDP,
nunca cierra el navegador y por omisión sólo ejecuta el
preflight. La adquisición exige `--acquire`, un
veredicto listo y la confirmación del titular. El
bloqueo de hosts oficiales sólo se retira en ese punto.
Fuera del bloque de sesión, la adquisición es idéntica
a la validada offline. Las pruebas offline cubren las
reglas del veredicto, el reconocimiento del aviso, la
comparación categórica del perfil, la clasificación de
solicitudes y la verificación del Edge dedicado. No se
ejecutó la sonda real.


### Corrida real del preflight v2, sin adquisición

Se verificaron antes de empezar el Edge dedicado del puerto 9232,
la rama experimental y la ausencia de un marcador previo. La sonda
corrió en modo preflight_only, sin `--acquire` y sin
confirmed-post.flag. El titular inició sesión y abrió Contratos
desde la UI del contexto desechable.

Veredicto: la sesión fue válida y la navegación fue por la UI. La
guarda bloqueó un get-info/MP. Hubo cero errores del proveedor
no atribuibles a la guarda, cero inventarios, cero solicitudes
oficiales y cero POST. En el momento de la captura no había aviso
de URL visible. El perfil resultó `multiple` con fuente `query`:
la aplicación pidió el feed para más de un perfil a la vez. No se
registró si el ID configurado estaba entre ellos, así que el
perfil infoexpress no quedó confirmado. ready_for_acquisition fue
false, con razón profile_multiple.

El contexto cerró y quedó verificado. Las pestañas habituales no
se tocaron. Un defecto de la sonda local hizo que el retorno
anticipado omitiera closure.json, y el marcador propio quedó
presente. Se retiró después de comprobar su contenido, el cierre
verificado y la salida 0 del trabajador.


### Correcciones offline: cierre seguro y diagnóstico de perfiles

El preflight distingue ahora cuatro situaciones del perfil enviado
por la aplicación en el get-info/MP bloqueado:

- only_configured: sólo el perfil configurado.
- configured_with_others: el configurado junto con otros.
- without_configured: uno o varios perfiles, sin el configurado.
- absent o undetermined_no_feed_request.

Sólo salen la categoría, el número de perfiles distintos, si la
selección cambió y la fuente (query o body). Nunca salen IDs, URLs
ni cuerpos. Se evalúa la última solicitud, que corresponde a la
selección vigente en la UI. La adquisición sigue exigiendo
only_configured: exactamente un perfil y que coincida con
`LICITACIONES_PROFILE_ID`. La corrida real anterior corresponde a
configured_with_others o a without_configured; no se reclasificó.

Cierre: la sonda local escribe la evidencia de cierre en su
finally más externo, también cuando ready_for_acquisition es false
y ante excepciones. La evidencia sólo marca como verdaderos los
hechos verificados: marcador propio, contexto cerrado según la
comprobación CDP de la guarda y desconexión de CDP sin error. El
padre borra closure.json antes de lanzar al trabajador, para que
una evidencia antigua nunca autorice la liberación. Retira el
marcador preventivo sólo si la evidencia es completa, el
trabajador salió con 0 y el contenido es el de la guarda. Los
flags de operador se consumen al cerrar. La decisión de liberación
es una función pura versionada con pruebas offline. Un arnés
temporal con dobles en memoria ejercitó la sonda local en cinco
escenarios de cierre, sin navegador ni red. No hubo login, feed,
inventario, POST ni descargas.


### Verificación real del perfil infoexpress: preflight listo

Se ejecutó una única corrida en modo preflight_only, sin `--acquire`
y sin confirmed-post.flag, con el Edge dedicado del puerto 9232
verificado antes de empezar. La evidencia de la corrida anterior se
archivó en una subcarpeta local. El titular inició sesión, entró a
Contratos desde la UI del contexto desechable y dejó seleccionado
sólo infoexpress, nombre que confirmó visualmente.

Veredicto: sesión válida, navegación por la UI, perfil
only_configured con profile_count 1 y fuente query. La selección
cambió durante la sesión y la última solicitud tenía sólo el
perfil configurado. La guarda bloqueó siete get-info/MP. La vista
quedó vacía, con un aviso de falta de conexión: la aplicación
interpreta el aborto como pérdida de red. Hubo cero errores del
proveedor, cero solicitudes oficiales, cero inventarios, cero POST
y cero descargas. ready_for_acquisition fue true.

El contexto cerró y quedó verificado, CDP se desconectó sin error
y el trabajador salió con 0. El marcador se liberó con evidencia
completa y los flags de operador se consumieron. Las pestañas
habituales no se tocaron. En paralelo, el titular abrió Contratos
en una ventana de incógnito ajena a la sonda, que sí consultó el
feed; no fue una consulta de la sonda.


### Adquisición SECOP I de Encino detenida por tamaño no declarado

Se autorizó una única adquisición real de la invitación de Encino
(MC-014-2026, constancia 26-13-14853238). Se repitió el preflight
con login manual y sólo infoexpress seleccionado: sesión válida,
only_configured, profile_count 1 y ready_for_acquisition true. El
titular confirmó el POST y luego se creó confirmed-post.flag. Se
reutilizó el inventario conservado, con seis documentos y una
única fila primaria en PDF.

La interceptación CDP quedó armada antes del envío. Se reenvió un
único POST a VerDocumento, con la identidad y el cuerpo
verificados. La respuesta fue HTTP 200 con content-type
application/pdf y sin codificación, pero no traía Content-Length.
El adaptador exige un tamaño declarado. La sonda rechazó la
respuesta con missing_declared_size a los 1,7 segundos, sin leer
el cuerpo: cero bytes, ningún archivo en staging. No hubo
reintentos ni redirecciones. No apareció ninguna descarga nativa
en Descargas ni en `.local` posterior al intento.

El contexto cerró y quedó verificado, CDP se desconectó sin error
y el trabajador salió con 0. El marcador preventivo se liberó con
evidencia completa. pdf-attempt.lock permanece y agota el único
intento autorizado. No hubo nuevas consultas al feed ni
inventarios, y no se ejecutaron OCR, extracción ni clasificación.
El documento no queda listo para extracción.

Hallazgo: VerDocumento entrega el PDF sin tamaño declarado,
probablemente con transferencia por bloques. La regla de tamaño
declarado, heredada de SECOP II, impide aceptarlo tal como está.


### Streaming acotado de SECOP I sin Content-Length (offline)

Revisión: `read_stream` ya admitía una longitud desconocida. Lee
por bloques de 64 KiB, corta en 10 MiB, exige el fin del flujo,
cierra el handle y aborta la navegación. Sólo compara contra el
tamaño declarado cuando existe. `response_length` rechaza todo lo
que no sea 200 `application/pdf` sin codificación, un tamaño
inválido o uno declarado mayor que 10 MiB. El almacenamiento
escribe en un temporal y luego lo renombra. El rechazo por falta
de Content-Length estaba sólo en la sonda local.

Cambio: `eureka_nacional_secop1_pdf.read_secop1_pdf` reutiliza
esas dos funciones. Mide el plazo restante de los 12 s y convierte
cualquier error del flujo CDP en un rechazo. Valida el cuerpo
completo:

- Cierre verificado del flujo y cuadre de los bytes contados.
- Cuerpo no vacío, como máximo 10 MiB, y tamaño igual al
  declarado si lo hay.
- Firma `%PDF-` sobre el cuerpo completo y `%%EOF` en los últimos
  1024 bytes.
- Tamaño recibido, origen del tamaño (declarado o recibido) y
  SHA-256.

No escribe nada. La sonda local guarda sólo los bytes aceptados.
Después compara hash y tamaño con lo guardado y borra el archivo
si no cuadran. Siguen rechazándose las redirecciones, los tipos
incorrectos, la compresión y los tamaños declarados excesivos. Se
conservó una copia de la versión ejecutada en la corrida real.

Pruebas: 25 pruebas unitarias con un CDP falso. En el laboratorio
aislado, con Edge headless y servidor sintético en loopback, se
probaron tres respuestas sin Content-Length: por bloques, con fin
por cierre de conexión y por bloques truncada. Las dos primeras se
aceptaron con SHA-256 correcto. La truncada se rechazó y no hubo
descargas nativas en ningún caso.

Hallazgo: ante el flujo truncado, Edge informó por CDP un fin de
flujo normal tras 215 bytes, sin error. Sólo la falta de `%%EOF`
lo detectó. Riesgo residual: un corte justo después de un `%%EOF`
intermedio, por ejemplo en un PDF con actualizaciones
incrementales, pasaría la validación. La extracción posterior
debe tratar el documento como no garantizado. No se ejecutó
ninguna sonda real. `pdf-attempt.lock` permanece intacto y
bloquea un nuevo intento hasta que se autorice expresamente
archivarlo.


### Segunda adquisición SECOP I de Encino: PDF recuperado

El titular autorizó un segundo intento único. El pdf-attempt.lock
anterior se archivó con su SHA-256 junto a la evidencia de la
corrida de las 21:52, sin borrarse. El titular inició sesión, dejó
sólo infoexpress y confirmó el POST. Preflight: sesión válida,
only_configured, profile_count 1 y dos get-info/MP bloqueados.

Se reutilizó el inventario conservado y se armó la interceptación
CDP antes del envío. Salió un único POST a VerDocumento, con la
identidad y el cuerpo verificados. La respuesta fue 200
application/pdf sin Content-Length. La lectura por streaming
terminó con fin de flujo verificado y navegación abortada en 2,2
segundos:

- 5.651.103 bytes recibidos, por debajo del límite de 10 MiB.
- Origen del tamaño: received_undeclared.
- Firma `%PDF-1.4` y `%%EOF` en los últimos 1024 bytes.
- SHA-256
  `174e63c957f77eee893fa1d0dd699d32a013405b64c25517f9c5e6fdc606fddd`.

El archivo se guardó en staging por hash y una verificación
independiente posterior confirmó hash, tamaño, firma y marca
final. No quedaron temporales.

Las descargas nativas siguieron denegadas: no apareció nada en
Descargas. El contexto cerró y quedó verificado, CDP se desconectó
sin error, el trabajador salió con 0 y el marcador preventivo se
liberó. El nuevo pdf-attempt.lock agota este intento. Hubo cero
consultas nuevas al feed o a inventarios, sin reintentos, y no se
ejecutaron OCR, extracción ni clasificación. `%%EOF` no garantiza
integridad absoluta.


### Primera clasificación documental SECOP I: Encino

Se procesó sólo el PDF recuperado de la invitación de MC-014-2026.
Antes de extraer, se comprobó la traza de la adquisición: un POST,
un intento, flujo cerrado, firma, `%%EOF`, tamaño dentro del
límite, cierre seguro y SHA-256 coincidente con el archivo en
staging. El tamaño recibido, 5.651.103 bytes, equivale a los
5,39 MB que mostraba el inventario.

Se usó el extractor existente con un máximo de dos páginas de OCR
y el clasificador existente, sin cambios de reglas.
extraction-attempt.lock limita esta extracción a una única
ejecución.

Resultado: el PDF tiene 36 páginas y es escaneado, sin texto
nativo en ninguna. El OCR en español procesó las páginas 1 y 2 en
8,8 segundos y quedaron 34 pendientes. La identidad quedó
confirmada en el texto: aparecen MC-014-2026 y el Municipio de
Encino. La página 1 contiene el aviso de invitación de mínima
cuantía y la justificación de la modalidad. La página 2 contiene
las condiciones generales, con el objeto (adquisición de
elementos para el sistema penitenciario y carcelario, convenio
con el INPEC EPMSC Socorro) y el alcance. Ninguna de las dos
menciona experiencia y el clasificador no registró evidencia.

Estado formal: not_resolved, con razón
governing_documents_incomplete, revisión insufficient_evidence y
review_priority 4. La invitación quedó incompleta y los otros
cinco documentos del inventario no se descargaron. Prioridad
comercial: no determinada. Encino no figura en las corridas de
descubrimiento guardadas, porque provenía de un registro en
memoria de la sesión, y calcularla exigiría consultar el feed.
No hubo IA, descargas, POST, inventarios ni consultas al feed.
`%%EOF` y SHA-256 no se consideran garantía absoluta de
integridad.


### Integración experimental de SECOP I en el runner nacional (offline)

SECOP I se incorpora en tres etapas, sin arquitectura nueva y
detrás de `--include-secop1`, desactivado por defecto.

Etapa 1, en el runner y con la sesión habitual. La selección
admite procesos SECOP I con una cuota separada
(`--secop1-processes`, máximo 5). La cuota es un tope y no se
rellena. Un proceso se admite sólo si pasó los filtros
comerciales vigentes, tiene constancia válida, idContrato e
id_fuente_contract, y su fase existe o figura explícitamente como
null en el registro del proveedor. En otro caso se excluye con
`secop1_inventory_keys_unverified`.

Hace una sola petición de inventario por proceso al endpoint
existente. El parser nuevo valida el contrato real observado en
Encino: Nombre, Tipo, Tamaño, Fecha y Documento, con
`openDocumentoSecop1`. La paginación se detiene al alcanzar la
cantidad declarada. Si alguna fila no es válida, se registra la
incidencia y el proceso no entra en la cola. Se encola sólo el
PDF rector, uno por proceso, en `secop1_queue.json`, con un hash
de lote. Las métricas por fuente van en `by_source`. En esta
etapa no hay descargas.

Etapa 2, `eureka_nacional_secop1_acquire.py`. Generaliza la sonda
validada: Edge dedicado verificado, contexto desechable con
descargas nativas denegadas, login manual, preflight pasivo y una
única confirmación del titular, ligada al hash exacto del lote.
Como máximo hay cinco POST. Antes de cada uno se crea en exclusiva
un registro de intento por documento, que nunca se repite. Cada
PDF se lee con streaming acotado (10 MiB, 12 s, `%PDF-`, `%%EOF`
y SHA-256) y se guarda con un recibo en el formato que usa el
runner. Un fallo aislado no detiene el lote. Lo detienen dos
fallos consecutivos, un error inesperado o un cierre incierto.
El marcador preventivo sólo se libera con evidencia completa de
cierre.

Etapa 3, `eureka_nacional_secop1_flow.py`, offline. Extrae y
clasifica sólo a partir de recibos verificados y escribe en un
directorio nuevo sin modificar la corrida de origen. Política de
OCR para PDF rectores escaneados:

- Pasadas de dos páginas, dentro del límite de 14 s del OCR
  existente.
- Primero se leen las páginas que el propio texto señala como
  requisitos habilitantes o experiencia (índice, referencia a una
  página o título). Si no hay ninguna, se lee de forma secuencial
  y conservadora.
- Como máximo 12 páginas por documento y 60 páginas o 6 minutos
  por corrida.
- La búsqueda se detiene ante una exigencia explícita.

La cobertura parcial deja el documento incompleto y el
clasificador, sin cambios, mantiene `not_resolved`.

Validación: 399 pruebas de la suite nacional y 30 de laboratorio
aislado. Las pruebas de etapa 1 corren el runner con datos
mixtos. Con la opción desactivada, una comparación contra el
código anterior dio salidas idénticas en seis archivos, en las
llamadas al proveedor y en las descargas. Con la opción activada,
SECOP II no cambia y sólo se añade la petición de inventario
SECOP I con la fase null.

El laboratorio de lote, con Edge headless y servidor sintético,
probó una respuesta PDF por bloques, una HTML y una truncada. Se
guardó la primera, se rechazaron las otras dos y el lote se
detuvo sin enviar el cuarto POST. No hubo descargas nativas y el
recibo fue aceptado por la caché del runner. El trabajador real
se probó con dobles en memoria: ejecuta el lote sólo con
preflight listo y confirmación exacta, y lo rechaza si hay otros
perfiles o si el navegador no es el dedicado.

La suite unitaria completa tiene 7 fallos ajenos a este trabajo,
que también fallan en el commit base. No hubo login, feed,
inventarios, POST ni descargas reales.


### Primera corrida nacional integrada, etapa 1 (en01-xgcp5mgp)

Parámetros autorizados: `--exploratory --processes 10
--documents 20 --edge-stream-fallback --include-secop1
--secop1-processes 5`, ocho páginas, 30 días y filtros sin
cambios. Antes se verificaron el Edge dedicado, una única pestaña
de Contratos y la ausencia de marcadores. El feed se consultó con
el perfil configurado.

Descubrimiento: 240 procesos únicos. De ellos, 75 eran de SECOP I
(31 %), 164 de SECOP II y 1 de otro portal.

| Fuente | Elegibles | Comercial fuera | Servicio principal | Objeto no claro | Seleccionados |
| --- | --- | --- | --- | --- | --- |
| SECOP I | 8 | 52 | 14 | 1 | 5 |
| SECOP II | 20 | 104 | 36 | 4 | 10 |

Los ocho SECOP I elegibles traían la fase null de forma explícita
y pasaron la verificación de claves. Siete son de mínima cuantía.
Encino no figura entre ellos.

SECOP II: se analizaron 6 de los 10 seleccionados. Todas las
descargas directas recibieron HTTP 403. El streaming por Edge
recuperó 3 PDF, pero rechazó dos rectores que declaraban 11,3 MB
y 24,4 MB, por encima del límite de 10 MiB. Otras dos descargas
quedaron sin respaldo porque no eran rectoras. Tras tres fallos
en dos procesos se abrió el cortacircuitos de descargas
(`download_circuit_open`) y la corrida terminó como parcial a los
96 segundos, con 69 de 200 créditos. Resultado: 6 not_resolved
(5 por evidencia insuficiente y 1 por silencio documental),
ningún resuelto y 0 páginas de OCR.

SECOP I: la etapa de inventario no se ejecutó. El cortacircuitos
de descargas de SECOP II detuvo la corrida antes del bucle de
SECOP I. Los cinco procesos quedaron seleccionados sin inventario
y la cola quedó vacía. No hubo POST ni descargas SECOP I. Es un
defecto de orquestación de la integración: un fallo de descargas
de una fuente impidió la etapa sin descargas de la otra.


### Corrección de orquestación y recuperación de inventarios SECOP I

Corrección A: con `--include-secop1`, sólo el cortacircuitos de
descargas SECOP II se aplaza hasta después de los inventarios
SECOP I, y luego se vuelve a lanzar. El resto de topes de
créditos o tiempo, la sesión y el cierre incierto siguen
deteniendo de inmediato. Sin la opción, el runner se comporta
exactamente igual que antes; la comparación contra el código
anterior lo confirmó también con el cortacircuitos abierto.

Corrección B: `--secop1-inventory-from` con `--secop1-constancia`
inventaría sólo procesos ya seleccionados en una corrida
persistida y dentro de una lista explícita. No sondea la sesión,
porque ese sondeo consulta el feed, ni repite el descubrimiento o
los filtros, ni descarga. El cliente queda limitado a una petición
por constancia y cada proceso a una página, para que un proceso
paginado no gaste el crédito de otro. Pruebas: 418 en la suite
nacional y 30 de laboratorio.

Operación real única (en01-secop1inv_xgcp5mgp): 5 inventarios con
5 peticiones, cero consultas al feed, cero descargas y cero POST.
Los cinco tenían la Invitación como único rector por título, así
que se encolaron 5. Ningún proceso quedó excluido. Hash del lote:
`a9871484328a9e8e48ea2eb9a9899c8129918201b34e40fc0668c23a53b5c614`.

| Constancia | Entidad | Rector | Tamaño mostrado | Documentos |
| --- | --- | --- | --- | --- |
| 26-13-14853244 | Sutatenza, Boyacá | Invitación, PDF | 22,68 MB | 5 |
| 26-13-14853220 | Concejo de Taraira, Vaupés | Invitación, PDF | 2,10 MB | 4 |
| 26-13-14853212 | Jericó, Boyacá | Invitación, PDF | 742 KB | 6 |
| 26-13-14853190 | Fómeque, Cundinamarca | Invitación, PDF | 539 KB | 3 |
| 26-13-14853123 | Montelíbano, Córdoba | Invitación, PDF | 602 KB | 3 |

La invitación de Sutatenza supera ampliamente los 10 MiB, de modo
que su adquisición se rechazaría por tamaño. Queda pendiente la
revisión del lote por el titular antes de cualquier descarga.


### Regla de tamaño mostrado y lote SECOP I de cuatro documentos

Regla general de admisión a la cola automática: si el tamaño
mostrado por el proveedor, en unidades binarias y redondeado,
supera estrictamente 10 MiB, el rector no entra en la cola y se
registra `displayed_size_over_limit`. Un tamaño desconocido o
ilegible no se inventa: el documento se admite, se marca con
`displayed_size_known: false` y sigue sujeto al límite estricto
sobre los bytes recibidos. Los valores justo en el límite también
se admiten, y deciden los bytes leídos. El proceso, su inventario
y su elegibilidad comercial se conservan, y el estado de
experiencia queda not_resolved. La regla también se aplica en la
etapa 1.

La regeneración offline (`--rebuild-queue`) vuelve a derivar la
cola desde los inventarios guardados, sin peticiones. Archiva la
cola anterior, registra cada decisión y se niega a ejecutarse si
el lote ya tiene intentos. Pruebas: 66 del módulo, 431 de la suite
nacional y 30 de laboratorio. SECOP II sigue idéntico al código
anterior.

Resultado sobre en01-secop1inv_xgcp5mgp, sin ninguna petición: se
excluyó Sutatenza (26-13-14853244, 22,68 MB) por tamaño mostrado.
Taraira, Jericó, Fómeque y Montelíbano permanecen en la cola, en el
mismo orden y sin otro cambio que el nuevo indicador de tamaño
conocido. max_posts es 4. Hash nuevo:
`2c2ca83d59997e2e224823894db5f633c8620e93866457f58230df6284ace69d`.
El anterior, `a9871484…`, quedó archivado. Los archivos de
procesos e inventarios conservan su hash. Pendiente: validación
del hash por el titular antes de la etapa 2.


### Etapa 2: adquisición SECOP I por lote (cuatro PDF)

Verificaciones previas:

- Todos los módulos, incluido `public_procurement`, se importaron
  desde el worktree nacional, con PYTHONPATH en formato Windows.
- El hash de la cola coincidía con el aprobado.
- No había intentos, recibos ni marcador previos.
- El Edge dedicado del puerto 9232 estaba verificado.

El titular inició sesión en el contexto desechable y dejó sólo
infoexpress. El preflight dio sesión válida, only_configured,
profile_count 1 y ready_for_acquisition true, con dos get-info/MP
bloqueados. La confirmación se creó con el hash exacto del lote,
`2c2ca83d…6284ace69d`.

| Constancia | Entidad | Mostrado | Recibido | SHA-256 | Tiempo |
| --- | --- | --- | --- | --- | --- |
| 26-13-14853220 | Concejo de Taraira | 2,10 MB | 2.203.048 B | `8603a0ac…04d658a4` | 2,4 s |
| 26-13-14853212 | Alcaldía de Jericó | 742 KB | 759.314 B | `bd4c8b02…3dea85888` | 1,1 s |
| 26-13-14853190 | Alcaldía de Fómeque | 539 KB | 551.665 B | `0807d1d8…8d6dc97a` | 1,0 s |
| 26-13-14853123 | Alcaldía de Montelíbano | 602 KB | 616.229 B | `58a8ea9d…dc9333a6585` | 1,1 s |

Resultado: cuatro POST, uno por documento y sin reintentos.
Respuesta HTTP 200 sin Content-Length en los cuatro, con fin de
flujo verificado, firma `%PDF-1.7` y `%%EOF`. Los cuatro se
guardaron, con cuatro recibos y cuatro registros de intento
finalizados con el hash del lote. Una verificación independiente
posterior confirmó tamaño y SHA-256 contra el almacenamiento. Los
tamaños recibidos coinciden con los mostrados en el inventario.

No hubo descargas nativas ni temporales. El contexto se cerró y
quedó verificado, CDP se desconectó, el trabajador salió con 0 y
el marcador se liberó con evidencia completa. Las pestañas
habituales no se tocaron. Hubo cero consultas al feed y a
inventarios, cero OCR y cero clasificación. Sutatenza no se
incluyó.


### Etapa 3: extracción y clasificación offline de cuatro procesos SECOP I

Salida en en01-secop1_secop1inv_xgcp5mgp: cero peticiones de red,
cero llamadas de IA y 22 segundos. Se usaron los cuatro recibos,
verificados contra el almacenamiento, sin rechazos. Los cuatro
PDF tenían texto nativo: 185 páginas, 184 leídas y 0 páginas de
OCR. El clasificador, sin cambios, devolvió not_resolved en los
cuatro.

| Constancia | Páginas | Nativo | Pendiente | Estado y razón | Evidencia principal |
| --- | --- | --- | --- | --- | --- |
| 26-13-14853220 Taraira | 75 | 74 | p. 43 | not_resolved, governing_documents_incomplete | p. 30: «Experiencia General oferente en máximo un (01) contrato» (Formato 3) |
| 26-13-14853212 Jericó | 42 | 42 | ninguna | not_resolved, no_decisive_clause | p. 17: «se tendrá en cuenta como requisito habilitante la experiencia»; p. 16 remite al estudio previo |
| 26-13-14853190 Fómeque | 34 | 34 | ninguna | not_resolved, requirement_requires_corroboration | p. 14, EXIGENCIA: «El proponente debe acreditar UN (1) contrato…» |
| 26-13-14853123 Montelíbano | 34 | 34 | ninguna | not_resolved, no_decisive_clause | p. 15: «Certificado de experiencia de al menos un contrato de objeto similar»; p. 21 remite al anexo de experiencia |

Prioridad comercial: A en los cuatro, por coincidencia de
categoría por palabras clave (papelería, informática, ferretería y
uniformes/EPP) en procesos abiertos de mínima cuantía. La
prioridad comercial es independiente del estado formal.

Lectura para revisión humana, no un estado formal: los cuatro
documentos contienen indicios de exigencia de experiencia. Ninguno
es favorable. El clasificador no los resolvió porque la exigencia
está en formatos o anexos, remite al estudio previo o requiere
corroboración del alcance del proponente.

Defecto observado en la política de OCR de la etapa 3: la primera
pasada pide las páginas 1 y 2 aunque tengan texto nativo. En
Taraira, esa pasada no realizó OCR y el bucle se detuvo como
`ocr_no_progress` sin leer la página 43, la única que requería
OCR, aunque quedaba presupuesto. La cobertura quedó registrada
correctamente como incompleta y el resultado se mantuvo
not_resolved. Corrección propuesta: planificar desde las páginas
que realmente requieren OCR. No se aplicó ni se repitió la
extracción.


### Corrección del planificador OCR y reevaluación de Taraira

Corrección: la pasada 0 lee sólo texto nativo y no consume
presupuesto de OCR. Las pasadas siguientes planifican
exclusivamente entre las páginas sin texto utilizable: primero las
señaladas por las reglas de relevancia existentes, luego la ventana
inicial y después en orden. Una página intentada o que el
extractor no procesa no vuelve a planificarse, y se eliminó la
parada por falta de progreso. Los presupuestos no cambian y la
cobertura real queda registrada, con candidatas y páginas
planificadas sin procesar. Se añadió `--only-constancia` para
reevaluar un documento de la cola en un directorio propio.

Pruebas: 73 del módulo, con documentos mixtos (nativas,
escaneadas, en blanco y rechazadas por el extractor) y el caso de
Taraira; 437 de la suite nacional y 30 de laboratorio. SECOP II
sigue idéntico al código anterior.

Reevaluación de Taraira (26-13-14853220), offline, con el PDF y el
recibo ya guardados: 75 de 75 páginas, la 43 por OCR en una sola
pasada, cobertura completa y 59 páginas de presupuesto restantes.
La página 43 no contiene evidencia de experiencia. El estado sigue
en not_resolved, pero la razón pasa de
governing_documents_incomplete a document_dependency: la p. 30
remite al Formato 3 de experiencia. Revisión documentary_silence,
prioridad 2. No se tocaron los otros tres procesos.

### Análisis del clasificador: Fómeque y Montelíbano (sin cambios)

Fómeque (p. 14), «El proponente debe acreditar UN (1) contrato…».
El clasificador la reconoce como EXIGENCIA, pero no concluye por
dos causas independientes:

1. Alcance `unspecified`. El título de la sección es «EXPERIENCIA
   DEL PROPONENTE», y las reglas sólo reconocen como sección
   general «experiencia general/específica/habilitante…» o
   «experiencia del proponente – formulario No. N». El sujeto es
   el proponente y la frase no tiene limitaciones, así que es un
   probable falso negativo por un patrón de sección demasiado
   estrecho.
2. Documento posiblemente rector pendiente. «ANALISIS DEL SECTOR»
   tiene rol unknown y no se descargó, y la regla exige que no
   quede ningún documento rector posible sin leer. Es prudencia
   razonable en general, pero excesiva para un título que por
   definición es un estudio de mercado, no un pliego ni una adenda.

Montelíbano (p. 15), «Certificado de experiencia de al menos un
contrato de objeto similar». Es una fila de una lista de
documentos, fusionada con «Pacto Anticorrupción», sin verbo de
obligación ni título de sección capturado. La regla de listas sólo
reconoce un formato numerado concreto. La prudencia es en parte
necesaria, porque sin el encabezado de la tabla no se sabe si la
lista es habilitante o puntuable, aunque el Anexo de experiencia
de la p. 21 lo sugiere. Hace falta verificar a mano el encabezado
de la tabla antes de proponer una regla.

Ajustes propuestos, no implementados:

- Ampliar el reconocimiento de sección general a «experiencia del
  proponente/oferente», manteniendo las exclusiones por limitación
  o hipótesis de cada frase.
- Tratar como no rectores «análisis/estudio del sector», «CDP o
  certificado de disponibilidad presupuestal», «PAA» y «BPIN». Así
  aparecen en los seis inventarios SECOP I observados.
- Montelíbano: sólo revisión humana por ahora.


### Ajustes A y B del clasificador y cierre del piloto SECOP I

A. Un patrón estrecho, `BIDDER_SECTION`, reconoce como sección
general del proponente «experiencia del proponente/oferente», con
numeración y puntuación variables. Se aplica a la sección o al
encabezado de la cláusula, y sólo da alcance general a una
cláusula que ya es EXIGENCIA. Un encabezado nunca crea una
exigencia. Las cláusulas condicionales, hipotéticas, puntuables,
dirigidas a terceros, no aplicables o limitadas conservan su
lectura, y así lo verifican las pruebas negativas.

B. Un documento pendiente de rol desconocido con título claramente
no rector (análisis o estudio del sector, CDP, certificado de
disponibilidad presupuestal, PAA, plan anual de adquisiciones o
BPIN) ya no bloquea una exigencia explícita en una invitación
completa. El rol no cambia: si se lee y su portada indica adenda,
vuelve a bloquear. Los pendientes genéricos desconocidos, las
adendas y los rectores siguen bloqueando, y la conclusión
favorable sigue exigiendo todos los documentos. Por diseño, B sólo
puede volver más desfavorable un resultado, nunca producir uno
favorable. La trazabilidad queda en
`document_coverage.non_governing_pending`.

Pruebas: 32 nuevas, positivas y negativas. En total, 470 de la
suite nacional y 30 de laboratorio, sin regresiones. Impacto
estimado en 96 resultados históricos: 3 podrían cambiar de estado
con B (Fómeque y dos procesos SECOP II en en01-le73ddhz y
en01-manual_hsxjhqpg). No se modificaron.

Reevaluación de Fómeque (26-13-14853190), offline, con el PDF y el
recibo guardados: 34 de 34 páginas nativas. Resultado:
experience_required, explicit_bidder_requirement, revisión
explicit_requirement y prioridad 5. Evidencia en la p. 14, sección
«EXPERIENCIA DEL PROPONENTE», alcance general: «El proponente debe
acreditar UN (1) contrato y/o certificación… FERRETERÍA Y/O
ELEMENTOS PARA ACUEDUCTOS». El «ANALISIS DEL SECTOR» figura como
pendiente no rector. La prioridad comercial A se mantiene.

Montelíbano (26-13-14853123), revisión documental offline de las
páginas 14 a 16, sin reclasificar. La fila «Certificado de
experiencia de al menos un contrato de objeto similar… Se
acreditará con la certificación expedida por el contratante…»
pertenece a las tablas «Persona jurídica. Debe anexar con la
propuesta: CUMPLE / NO CUMPLE» (p. 14, bajo DOCUMENTOS JURÍDICOS)
y «Persona natural. Debe anexar con la propuesta: CUMPLE / NO
CUMPLE» (p. 15). La evidencia documental basta para sostener, en
revisión humana, una exigencia habilitante para todo proponente.
El estado automático sigue not_resolved: el encabezado obligatorio
y la fila están separados en la tabla, y no se crearon reglas
nuevas.


### Preparación de la exploración ciega en Boyacá y Huila (offline)

Geografía: la captura nacional sólo contiene identificadores. Su
estructura es «40» + un código de departamento de Licitaciones.info
+ municipio, con 32 códigos. El código 4006 corresponde a Boyacá
porque coincide con los 123 identificadores capturados para Eureka
Regional. El 4017 corresponde a Huila por inferencia: 37
identificadores, igual que sus 37 municipios, y posición 17 del
orden alfabético, que también cuadra con Antioquia (125), Santander
(87) y Córdoba (30).

El archivo versionado
`eureka_nacional_geography_boyaca_huila(from_licitaciones_info).v1.json`
tiene 160 ubicaciones. Sólo se acepta si es exactamente el
subconjunto nacional de los códigos declarados. Como la parte de
Huila es inferida, cada fila del feed se verifica contra
TextoDepartamento: las de otro departamento se excluyen como
`outside_geography_scope` y se cuentan.

Cuotas: el runner selecciona como máximo 15 procesos SECOP II en
modo exploratorio y 5 SECOP I. En en01-xgcp5mgp quedaron fuera por
cuota 10 SECOP II y 3 SECOP I elegibles. Con `--include-secop1`,
cada elegible no seleccionado lleva `not_selected_reason` y se
cuenta por fuente.

Informe: `eureka_nacional_blind_report.py` genera un embudo por
fuente: descubiertos, exclusiones, elegibles, seleccionados,
elegibles no seleccionados, inventarios, descargas, rector
completo, clasificación, revisión y potencialmente favorables
(no_experience_required o explicit_favorable; el silencio no
cuenta). Incluye datos de reproducibilidad: commit, corte,
geografía, perfil comercial y límites. No modifica sus entradas.

Pruebas: 14 nuevas; 484 de la suite nacional y 30 de laboratorio.
Sin las opciones nuevas, la salida es idéntica al código anterior.

Nota vigente: los ajustes A y B del clasificador compartido podrían
cambiar dos resultados históricos de SECOP II (en01-le73ddhz y
en01-manual_hsxjhqpg). No se reprocesan.


### Exploración ciega Boyacá + Huila, etapa 1 (en01-uc9h1l8y)

La geografía se verificó contra el JSON de ubicaciones de
Licitaciones.info aportado por el titular: departamento 40060 con
123 códigos de 8 dígitos y departamento 40170 con 37 códigos de 7
dígitos. Coincidió exactamente con el archivo versionado.

Parámetros: `--exploratory --processes 15 --documents 24
--discovery-pages 8 --recent-days 30 --edge-stream-fallback
--include-secop1 --secop1-processes 5 --ocr-pages 2` y la
geografía de Boyacá y Huila. Se usaron 84 de 200 créditos en 127 s
y la corrida terminó como parcial.

Cobertura: se leyeron 240 avisos en 8 páginas y el proveedor seguía
reportando más. Los avisos leídos se publicaron entre el 24-11 a
las 16:06 y el 26-11 a las 18:25, es decir, unos dos días de la
ventana de 30. Cuatro filas eran de otros departamentos o de
alcance nacional y se excluyeron como `outside_geography_scope`.

| Fuente / departamento | Descubiertos | Elegibles | Seleccionados | No seleccionados por cuota |
| --- | --- | --- | --- | --- |
| SECOP II Boyacá | 132 | 13 | 10 | 3 |
| SECOP II Huila | 44 | 9 | 5 | 4 |
| SECOP I Boyacá | 55 | 8 | 5 | 3 |
| SECOP I Huila | 4 | 0 | 0 | 0 |

Las principales exclusiones fueron fuera del perfil comercial (140)
y servicio principal (58).

SECOP II: el 403 directo fue generalizado. Edge recuperó 4 PDF y
rechazó un rector de 11,3 MB. Después se abrió el cortacircuitos y
quedaron 6 seleccionados sin analizar. Resultados de los 9
analizados:

- 7 not_resolved.
- El Cocuy, experience_ambiguous por cláusulas de proponentes
  plurales sobre la «experiencia solicitada».
- DTAO-FONAM (Huila, ferretería), not_resolved por silencio
  documental. La invitación de 18 páginas está completa y no tiene
  ninguna mención de experiencia; quedan pendientes los formatos y
  el estudio previo.

SECOP I: 5 inventarios y 4 rectores en cola (Jericó, Panqueba y dos
de Betéitiva). Sutatenza quedó excluido por tamaño mostrado. Hash
del lote:
`a2f83173735c7dbf894d738095dcbc8aa99111cac5e77db5895a3c16fa66f156`.
La invitación de Jericó ya tiene un recibo verificado en
en01-secop1inv_xgcp5mgp, pero la etapa 2 no reutiliza recibos de
otras corridas: queda pendiente de revisión.

Sin favorables formales. No hubo POST SECOP I ni etapa 2.


### Decisiones tras la búsqueda ciega: recibos, cobertura y cortacircuitos

1. Reutilización de recibos SECOP I (implementada, `f50922d`).
   `--reuse-receipts` reutiliza un recibo de otra corrida sólo si se
   cumplen todas estas condiciones:

   - El mismo `document_id` (constancia más ruta exacta), constancia,
     extensión y ruta figuran en una cola de la corrida de origen.
   - Un intento finalizado como stored registra el mismo SHA-256 y
     tamaño.
   - El binario se verifica por tamaño y hash, tiene `%PDF-` y
     `%%EOF`, y encaja con el tamaño mostrado dentro del redondeo.

   La copia se vuelve a calcular al guardarse y la fuente nunca se
   modifica. Pruebas: 10 nuevas, que incluyen el rechazo por misma
   constancia y título con otra ruta, sin procedencia, intento sin
   coincidencia, binario alterado, sin `%%EOF` y tamaño mostrado
   incoherente. Suite nacional: 494; laboratorio: 30.

   Aplicada offline a en01-uc9h1l8y: Jericó (26-13-14853212) quedó
   resuelto con el recibo de en01-secop1inv_xgcp5mgp (SHA-256
   `bd4c8b02…`, 759.314 bytes) y la fuente conservó su hash. Nueva
   cola con 3 documentos nuevos (Panqueba 26-13-14852082, Betéitiva
   26-13-14851419 y 26-13-14851414); max_posts 3; hash
   `c610064ca584ea7770c1ff424287b706fc138a0f537a01d92954a811550d0eb4`.
   El lote anterior, `a2f83173…`, quedó archivado.

2. Cobertura temporal (sólo análisis). El payload capturado sólo
   filtra por `query.ubicacion_filter`, ordenado de forma descendente
   por FechaPublicacion, y la documentación registra que no hay
   verificación de filtros remotos por fecha. Las subventanas no son
   verificables offline. La paginación cuesta 1 crédito por cada 30
   avisos, con unos 2,1 s de espaciado:

   - 240 avisos cubrieron unas 50 horas, unos 4,8 por hora.
   - 30 días son unos 3.400 avisos: unas 115 páginas y créditos, y
     unos 4 minutos sólo de descubrimiento.
   - 10 días son unas 38 páginas.

   La mínima cuantía cierra en días, de modo que el valor útil se
   concentra en los avisos recientes. Propuesta, por pasos:

   a. Capturar con Network el payload de la UI con un filtro de
      fecha. Si existe un campo remoto, se podrían hacer subventanas
      verificables.
   b. Si no existe, un modo sólo de descubrimiento con un presupuesto
      propio de páginas. Pararía cuando una página completa no aporte
      procesos abiertos, guardaría una instantánea deduplicada con
      cobertura por página y procesaría después lotes desde esa
      instantánea sin volver a consultar el feed.

   Riesgo: se desconoce si el proveedor limita la profundidad de
   paginación.

3. Cortacircuitos SECOP II (sólo diagnóstico).
   `DownloadState.record_failure` cuenta cualquier fallo de descarga
   y se abre con 3 fallos en al menos 2 procesos. En en01-uc9h1l8y
   los 4 fallos contados fueron:

   - 1 rechazo por tamaño tras un Streaming con 200 (11,3 MB).
   - 2 respuestas 403 directas en documentos no rectores, sin
     Streaming autorizado.
   - 1 respuesta 403 en un rector sin intento de Streaming, porque la
     descarga directa agotó el cupo del proceso y no se registró
     `edge_skipped`.

   Ninguno fue de infraestructura. El Streaming recuperó 4 de 5
   rectores. En todas las corridas: 7 recuperados por Streaming, 3
   rechazos por tamaño, 2 errores de protocolo del Streaming y 8
   respuestas 403 sin Streaming aplicable.

   Corrección mínima propuesta, no implementada: clasificar cada
   fallo en el punto de captura.

   - Los rechazos por tamaño, los 403 en documentos sin Streaming
     autorizado y los Streaming omitidos por cupo o duración no
     cuentan para el cortacircuitos. Se registran con métricas
     propias y con `edge_skipped` explícito.
   - Cuentan, con el mismo umbral, los fallos efectivos: Streaming
     intentado que falla por otra causa (protocolo, respuesta
     inesperada, tiempo agotado o interrupción) y errores directos
     que no son 403.
   - La sesión, el cierre incierto y la seguridad siguen deteniendo
     de inmediato.

   Ni se desactiva el cortacircuitos ni se cambian los 10 MiB.


### Etapa 2 de la búsqueda ciega: tres PDF SECOP I y Jericó reutilizado

Lote aprobado `c610064c…550d0eb4`: 3 documentos, con login manual
y sólo infoexpress. Preflight: sesión válida, only_configured,
profile_count 1, dos get-info/MP bloqueados y cero errores del
proveedor. La confirmación quedó ligada al hash exacto.

| Constancia | Entidad | Mostrado | Recibido | SHA-256 | Tiempo |
| --- | --- | --- | --- | --- | --- |
| 26-13-14852082 | Alcaldía de Panqueba | 769 KB | 787.646 B | `5188312a…b69b7dde` | 1,8 s |
| 26-13-14851419 | Concejo de Betéitiva | 559 KB | 572.916 B | `619adbc0…d74c3bc5` | 0,7 s |
| 26-13-14851414 | Concejo de Betéitiva | 552 KB | 565.475 B | `ea0da155…a9058b9bd` | 0,8 s |

SHA-256 completos en `download_receipts.json` de en01-uc9h1l8y.

Tres POST, cero reintentos y cero rechazos. Respuesta 200 sin
Content-Length, `%PDF-1.7` y `%%EOF` en los tres. Los tamaños
coinciden con los mostrados y hay tres intentos stored con el hash
del lote. Jericó no se descargó: se usa su recibo reutilizado y
verificado.

No hubo descargas nativas. El contexto se cerró y quedó
verificado, el trabajador salió con 0 y el marcador se liberó.
Hubo cero consultas al feed o inventarios, cero OCR y cero
clasificación.


### Corrección del cortacircuitos SECOP II y captura del filtro de fechas

Cortacircuitos (implementado): cada fallo de descarga se clasifica
como `size_rejection`, `access_restricted_no_fallback`,
`fallback_skipped` o `infrastructure`, y queda en
`errors[].failure_kind` y en las métricas `download_<tipo>`. Sólo
`infrastructure` alimenta el cortacircuitos, con el umbral de 3
fallos en 2 procesos. Cuando un rector elegible no recibe Streaming
por haber agotado el cupo, se registra
`edge_skipped=document_allowance`. Sesión, seguridad y cierre
incierto siguen deteniendo de inmediato, y el límite sigue en 10 MiB.

Pruebas: 15 nuevas. Una prueba propia escribía el marcador en el
directorio compartido de pytest; se aisló y se eliminaron los
marcadores de los temporales de prueba. Totales: suite nacional 509
y laboratorio 30. Con salidas idénticas en el escenario normal; en el
escenario con cortacircuitos sólo se añaden `failure_kind` y la
métrica `download_infrastructure`.

Cobertura: instrucciones para capturar a mano el payload del filtro de
fechas en
[eureka-nacional-captura-filtro-fechas.md](eureka-nacional-captura-filtro-fechas.md).


### Etapa 3 de la búsqueda ciega: cuatro procesos SECOP I

La etapa 3 ahora también analiza los documentos resueltos por un
recibo reutilizado, que conservan su identidad de la cola archivada
y registran `receipt_origin` (`3a3661e`). Antes de extraer se
verificaron identidad, tamaño, SHA-256, firma, `%%EOF`, coherencia
con el tamaño mostrado y procedencia de los cuatro PDF. Ejecución
offline: cero peticiones, cero IA y 21 s. Se leyeron 125 de 126
páginas, con una página de OCR.

| Constancia | Páginas | Estado y razón | Revisión | Evidencia principal | Dependencias |
| --- | --- | --- | --- | --- | --- |
| 26-13-14852082 Panqueba | 26/26 nativas | not_resolved, no_decisive_clause | documentary_silence, prioridad 2 | p. 13, en «Experiencia específica»: los contratos de experiencia específica deben diferir de los de experiencia general, y los soportes de experiencia «NO SERÁN SUBSANABLES… causal de rechazo»; verificación de experiencia «HÁBIL O NO HÁBIL» | Otro documento rector pendiente («INVITACIÓN PÚBLICA»), estudios previos |
| 26-13-14851419 Betéitiva | 31/32; la p. 32 se pasó por OCR sin texto | not_resolved, governing_documents_incomplete | insufficient_evidence, prioridad 4 | p. 9, en «Requisitos habilitantes»: «Se debe contratar con una persona… que acredite experiencia en la ejecución de mínimo… dos (02) contratos» | p. 32 sin texto; estudios previos; análisis del sector y CDP, no rectores |
| 26-13-14851414 Betéitiva | 26/26 nativas | not_resolved, no_decisive_clause | documentary_silence, prioridad 2 | Ninguna mención de experiencia en la invitación | Estudios previos pendientes; análisis del sector y CDP, no rectores |
| 26-13-14853212 Jericó (reutilizado) | 42/42 nativas | not_resolved, no_decisive_clause | documentary_silence, prioridad 2 | p. 17: «se tendrá en cuenta como requisito habilitante la experiencia» y «la entidad solicita que el oferente acredite…»; p. 19: presentar contrato y acta de liquidación | p. 16 remite al estudio previo |

Prioridad comercial A en los cuatro: informática o papelería, en
mínima cuantía.

Ningún favorable confirmado. Hay un candidato a revisión humana:
26-13-14851414. Su invitación completa no contiene ninguna mención
de experiencia, pero el estudio previo está pendiente y puede
contener la exigencia, así que no se declara ausencia. Los otros
tres muestran indicios de exigencia sin conclusión formal: en
Panqueba y Jericó la evidencia es ambigua o remite a otro
documento, y en 26-13-14851419 la exigencia se redacta de forma
impersonal y la cobertura es incompleta.

Embudo actualizado de en01-uc9h1l8y:

- SECOP I: 5 seleccionados, 4 PDF y 5 not_resolved, Sutatenza
  incluido.
- SECOP II: 15 seleccionados y 8 analizados, con 7 not_resolved y 1
  experience_ambiguous. Corrige el «9 analizados» del informe de
  etapa 1.
- Favorables formales: 0.


### Validación focalizada de dos candidatos: lote documental propuesto

Revisión sin peticiones de los inventarios y recibos guardados. No
existen copias reutilizables de los documentos pendientes en
ninguna corrida.

| Candidato | Documento indispensable | Identidad | Tamaño mostrado | Mecanismo |
| --- | --- | --- | --- | --- |
| Betéitiva 26-13-14851414 (SECOP I) | ESTUDIOS PREVIOS (apoyo) | `secop1:26-13-14851414:8d5c9bbb…aa06d3b`, ruta `…/DA_PROCESO_26-13-14851414_21509215_140899271.pdf` | 250 KB | POST interceptado del lote SECOP I (login, preflight, confirmación ligada al hash, 10 MiB y 12 s) |
| DTAO-FONAM CO1.NTC.11284005 (SECOP II) | ESTUDIO PREVIO Y ANEXOS (apoyo) | DocumentId `897735547` | SECOP II no lo informa | Descarga directa y, ante un 403, Streaming por Edge (10 MiB y 12 s). Requiere autorizar el Streaming para un documento de apoyo. |

Hash del lote de dos documentos:
`aaed35635bbbd6d124332102a4191b120983e7773b80317aa82e95f9883598f9`.

No indispensables:

- Betéitiva: análisis del sector y CDP.
- FONAM: «FORMATOS», que no tiene extensión reconocida y no es
  procesable por el pipeline.

Pendiente: la aprobación del lote antes de cualquier descarga.


### Herramientas de validación focalizada (offline) y procedimiento de adquisición

`eureka_nacional_targeted_documents.py` (`cc70841`) tiene tres pasos:

- `plan`, offline: resuelve los documentos desde los inventarios
  guardados, exige el hash aprobado y crea un directorio propio con
  la cola SECOP I.
- `acquire-secop2`, real: una descarga directa por documento y, sólo
  ante un 403 y sólo para documentos del plan, el Streaming
  validado. Registra un intento exclusivo y un recibo, y respeta el
  marcador preventivo.
- `analyze`, offline: extrae todos los documentos disponibles de
  cada candidato y traduce la salida del clasificador, sin cambios,
  a lecturas explícitas: exigida, exigida sin conclusión formal,
  ausencia explícita, ausencia pendiente de corroboración, silencio
  con cobertura suficiente o evidencia insuficiente.

Los formatos no procesables quedan como dependencia no resuelta.
Pruebas: 17 nuevas; 527 de la suite nacional y 30 de laboratorio.

`plan` se ejecutó sin peticiones sobre en01-uc9h1l8y y reprodujo el
hash aprobado
`aaed35635bbbd6d124332102a4191b120983e7773b80317aa82e95f9883598f9`.
La cola SECOP I derivada (en01-target_uc9h1l8y) tiene 1 documento:
el estudio previo de Betéitiva, con hash
`892d8ebc2cbbdec12674a65012db8b5dad1c03b3d1fcb911f4fb72a2cd482734`.

Procedimiento de la única adquisición real (pendiente de
autorización):

1. Verificaciones previas.
2. SECOP II: `acquire-secop2`, con una petición directa y, sólo si
   hay 403, un Streaming, desde la pestaña habitual de Contratos.
3. SECOP I: `eureka_nacional_secop1_acquire.py en01-target_uc9h1l8y`,
   con login, infoexpress, preflight, confirmación del hash
   `892d8ebc…` y 1 POST.
4. Verificación de recibos y parada antes del análisis.

Límites: 10 MiB y 12 s por documento, sin reintentos.

Riesgos: los «FORMATOS» de FONAM no son procesables y su lectura
quedará como mucho en evidencia insuficiente. El tamaño del estudio
previo y anexos de FONAM es desconocido y podría superar el límite.
