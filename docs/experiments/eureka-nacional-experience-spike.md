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

**Preparada. Requiere autorización antes de ejecutar.** El modo optativo
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
