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
