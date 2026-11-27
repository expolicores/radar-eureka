# Handoff de Eureka Nacional

## Estado de la preparación

- Línea estable `main`. Checkpoint `670b0c472978e5750195e550bf29f5644df74f14`. Objeto de tag anotado `e07d811c8e9b58250c4cb4d69f5d5eaee610ec79`.
- Rama `experiment/eureka-nacional`, creada localmente en el checkpoint. Worktree en `C:\Users\juank\Desktop\EUREKA NACIONAL`. El worktree regional conserva su cambio local en `.claude/logs/.last-sync.json`, que contiene únicamente `lastSyncTime`.
- Upstream `origin/experiment/eureka-nacional` y tag remoto `eureka-mvp-v0.1` verificados.
- La preparación incluye estos tres documentos y las exclusiones de artefactos. Esta fase generó cero corridas, cero descargas experimentales y cero consumo de IA.

## Estado de EN-01

El primer smoke real se ejecutó el 19 de noviembre de 2026 en Edge CDP dedicado
con el runner `11cad4d`. Resultado parcial, `en01-ms7c7hyc` (salida `2`).
El endpoint devolvió 120 procesos únicos de 26 departamentos en cuatro páginas.
Se identificaron 19 candidatos comerciales, 8 elegibles para inventario y 5
seleccionados. Se inventariaron 43 documentos y se completaron 4 de 5 descargas.
El runner tardó 45,125 segundos y consumió 46 créditos de red y 0 llamadas de IA.

Se extrajo una página nativa y 0 páginas OCR. Una invitación superó 10 MiB y
tres PDF superaron 12 páginas. Los cinco casos quedaron `not_resolved` y hubo
0 procesos documentalmente resueltos. Los valores `count` por página fueron
31, 61, 91 y 121. El tamaño del universo nacional sigue indeterminado.

El [informe agregado](eureka-nacional-experience-spike.md#primer-smoke-real--19-de-noviembre-de-2026)
contiene el funnel, los errores y las recomendaciones. El detalle permanece
bajo `.local/eureka-nacional-spike/en01-ms7c7hyc/`. Antes de solicitar otra
corrida, revisar offline la prioridad documental en títulos numerados y
cotizaciones. La siguiente ejecución requiere autorización.

## Preparación y validación offline de EN-01.1

La selección documental normaliza títulos numerados, excluye cotizaciones y
proyectos identificados, y prueba alternativas dentro de los presupuestos
existentes. El clasificador contextual deja estados oficiales y prioridad de
revisión independientes. El replay local permite reproducir correcciones
humanas. Ver [método y validación de EN-01.1](eureka-nacional-experience-spike.md#en-011--clasificación-contextual-offline).

Cinco PDF locales y 82 páginas nativas. Pore p. 11, El Plato p. 13 y La Capilla
p. 20 produjeron evidencia favorable. Chivatá 21 y 22, págs. 1 y 4, mantuvieron
dependencias de reglamento. Los cinco expedientes aportados quedaron
`not_resolved`. Todo el detalle está en `.local/en01-1-validation/`. La segunda corrida se resume a continuación.

## Segundo smoke real de EN-01.1

El 23 de noviembre de 2026 se ejecutó `en01-ifqy1v2y` desde `6e66d57`.
El preflight pasó. El lanzador local buscó la cohorte anterior entre las
cuatro páginas autorizadas y obtuvo cero coincidencias. Se analizaron cinco
procesos nuevos con 44 documentos inventariados y cinco descargas exitosas.

Los cinco PDF superaron el límite de 12 páginas. Resultado parcial,
`not_resolved` en cinco casos, con 0 páginas nativas, 0 OCR, 0 afirmaciones
y 0 IA. Se consumieron 46 créditos y 44,609 s. La exclusión de cotizaciones
funcionó. Un archivo de formatos fue etiquetado como rector. Los intentos se
agotaron antes de probar alternativas. El detalle está en
`.local/eureka-nacional-spike/en01-ifqy1v2y/`.

Ver la [comparación agregada](eureka-nacional-experience-spike.md#segundo-smoke-real--23-de-noviembre-de-2026).
Próxima revisión offline: distinguir formatos auxiliares y prever un cupo de
alternativa dentro del presupuesto. Una tercera corrida requiere autorización.

## Replay offline de EN-01.2

Se reutilizaron los cinco PDF del segundo smoke y su inventario. El runner de
EN-01 extrae por página sin rechazar el PDF por extensión en páginas. Mantiene
topes técnicos de tamaño, memoria y tiempo, preserva texto ya recuperado y
registra cualquier cobertura pendiente. El OCR sigue siendo selectivo e
independiente, con hasta dos páginas por PDF. Los títulos que comienzan por
formatos o formularios auxiliares se tratan como soporte, por debajo de una
invitación rectora.

Se recuperaron 218 de 218 páginas con texto nativo, sin OCR ni páginas pendientes
en esos cinco archivos. Hubo 63 detecciones, incluidas tres exigencias explícitas
en dos procesos, y ninguna ausencia explícita. Dos casos quedaron ambiguos y
tres sin resolución. Ninguno se resolvió con la cobertura del inventario
disponible. El replay duró 24,531 s y consumió cero créditos de red y cero
llamadas de IA. El detalle local está en
`.local/eureka-nacional-spike/pdf-replay-4mc754as/`.

El [informe agregado](eureka-nacional-experience-spike.md#en-012--replay-offline-del-segundo-smoke)
incluye el comando de replay y sus límites. La invitación rectora que figuraba
en el inventario del caso de formatos queda pendiente de revisión. Este trabajo
usó los archivos ya descargados. La siguiente corrida real requiere autorización.

## Evaluación contextual offline de EN-01.3

Sobre los mismos cinco PDF se identificaron cuatro exigencias generales en
cuatro rectores. La prioridad comercial bajó en esos casos y la clasificación
formal quedó `not_resolved` por cobertura pendiente del inventario. Se
recuperó una exigencia omitida por una palabra dividida y se separaron las
cláusulas de Mipyme, proponentes plurales y desempate de las obligaciones
generales. En el quinto caso subsiste la insuficiencia documental porque
solo se leyó un formato auxiliar.

Se conservaron los cuatro estados formales. No hubo ausencias explícitas ni
procesos resueltos en esta muestra. El
[informe agregado](eureka-nacional-experience-spike.md#en-013--aplicabilidad-y-prioridad-comercial)
documenta el criterio y la comparación. El resultado por documento queda en
`.local/eureka-nacional-spike/pdf-replay-xbkkmdul/`. Pasaron 192 pruebas
offline. Se usó exclusivamente el material local, con cero OCR, consultas
CDP, descargas o llamadas de IA. La próxima corrida real requiere autorización.

## Corrida exploratoria EN-01.4 preparada

El [plan de ejecución](eureka-nacional-experience-spike.md#en-014--plan-de-corrida-exploratoria-nacional)
incluye comando, selección y métricas. El modo `--exploratory` se ejecutó
una vez con autorización. Propone hasta 15 procesos, 30 días, ocho páginas de 30 filas,
24 intentos de descarga y tres por proceso, 10 MiB por PDF, OCR selectivo de
hasta dos páginas por PDF, 200 créditos, 720 s y cero llamadas de IA. La
extracción nativa sigue sin tope por cantidad de páginas.

Registrar por separado clasificación formal, prioridad comercial, motivos de
parada y cobertura pendiente. Reservar hasta cuatro intentos para corroborar
ausencias explícitas y conservar hasta tres casos despriorizados para revisión
humana. La evaluación usa el perfil comercial, la cobertura geográfica y el
clasificador ya aceptados.

El [resultado agregado](eureka-nacional-experience-spike.md#en-014--resultados-de-la-primera-corrida-exploratoria)
registra 240 procesos únicos, 37 candidatos comerciales, 22 elegibles y 15
analizados. Hubo 17 PDF descargados, 12 rectores, 641 páginas con texto nativo
y 0 OCR. La conclusión formal fue una exigencia confirmada, con 14 casos
pendientes. Siete tuvieron prioridad comercial de exigencia y ninguno tuvo
ausencia explícita o favorable. Se usaron 160 créditos y 179,141 s, sin IA.
La salida fue parcial por tres descargas sobre el umbral de tamaño.

El cotejo offline encontró requisitos de experiencia en los tres silencios
del runner. Mantener la salida original y usar esos casos como regresiones
del siguiente incremento. El detalle y la muestra de tres despriorizados
están en `.local/eureka-nacional-spike/en01-le73ddhz/`. Una nueva corrida
requiere autorización.

## Corrección offline de EN-01.4

Los tres silencios de la corrida exploratoria se recuperaron con reglas
acotadas para un imperativo, una exigencia indirecta y una tabla con
requisitos por tamaño empresarial. La prioridad de exigencia aplicable
pasó de siete a nueve casos. El caso de la tabla pasó a revisión de alcance
limitado. Se mantuvieron una resolución formal, 14 casos pendientes y cero
ausencias explícitas o confirmadas en la muestra. Los restantes 12 casos
conservaron su salida. Los cinco PDF de control mantuvieron su evidencia
y prioridad. Pasaron 198 pruebas offline.

El [informe](eureka-nacional-experience-spike.md#en-014--corrección-offline-de-los-silencios-documentales)
describe las reglas y la comparación. Se recomienda mantener el presupuesto
de la exploratoria ya ejecutada, con 15 procesos, 24 intentos, 200 créditos y
720 s de tope. La siguiente corrida requiere autorización.

## Lote exploratorio de procesos nuevos

La corrida única del 24 de noviembre cargó 20 avisos históricos de los dos smoke
y la primera exploratoria. El [resultado agregado](eureka-nacional-experience-spike.md#en-01--lote-exploratorio-de-procesos-nuevos)
registra 240 avisos únicos, 29 candidatos comerciales, 20 elegibles y 15
analizados sin solapamiento. Los 17 PDF aportaron 401 páginas nativas; hubo
tres recuperaciones OCR y 137 páginas pendientes. El costo fue 160 créditos
y 185,250 s, sin IA.

La salida automática dejó seis casos ambiguos y nueve sin resolver.
Detectó exigencias en cinco procesos, cero ausencias explícitas y un
silencio cuyo rector contenía una exigencia en la pág. 12. El cotejo
offline se registró sin alterar la decisión automática. La corrida terminó
parcial por tres descargas que excedieron 10 MiB.

El detalle queda en `.local/eureka-nacional-spike/en01-hb4_beb5/`. Para
excluir este lote en una selección futura, añadir su nombre local a los
historiales con `--exclude-analyzed-from`. Cualquier corrida real adicional
requiere autorización.

## Ajuste focalizado tras el segundo lote

Se recuperó el requisito de experiencia incluido entre paréntesis en
un encabezado numerado. Pasó de silencio a exigencia aplicable para
revisión comercial y mantuvo `not_resolved` por cobertura pendiente.
El replay de 17 PDF verificó que los otros 14 casos conservaron evidencia,
estado formal y prioridad. El total formal sigue en seis ambiguos y
nueve sin resolver. Pasaron 207 pruebas y los cinco controles históricos
conservaron sus resultados.

El [diagnóstico agregado](eureka-nacional-experience-spike.md#en-01--cotejo-focalizado-del-segundo-lote)
registra siete procesos sin rector descargado, tres descargas sobre
10 MiB y 137 páginas pendientes por selección OCR. Una prueba focalizada
recuperó cuatro páginas de cuatro, incluida la que faltaba en un rector
mixto. La evidencia detallada queda en
`.local/eureka-nacional-spike/pdf-replay-gp4u608c/` y
`.local/eureka-nacional-spike/coverage-audit-pe6hrnob/`.
Cualquier otra corrida real requiere autorización.

## Incremento de cobertura documental

El [informe](eureka-nacional-experience-spike.md#en-01--incremento-de-cobertura-documental)
documenta dos candidatos adicionales a rector por metadatos: una invitación
DOCX y otra con título truncado. Sus binarios siguen pendientes. El lector
DOCX aislado se reutiliza y la portada define si un título ambiguo
corresponde a un rector. Los dos rectores parciales se reprocesaron offline
con el mismo cupo por PDF; el total OCR pasó de tres a cuatro páginas
recuperadas y las pendientes bajaron de 137 a 136. Se conservaron las
clasificaciones formales y las prioridades.

La muestra se preparó con la exclusión de 35 avisos
históricos y los mismos topes documentales, 200 créditos y 720 s. Después
de las ocho páginas base podrá pedirse una novena y hasta una décima con
`--conditional-extra-feed-pages 2` solo si faltan candidatos elegibles.
Esa ejecución real se registró en el apartado siguiente.

## Corrida nacional con extensión condicional del feed

El [resultado agregado](eureka-nacional-experience-spike.md#en-01--corrida-nacional-con-extensión-condicional-del-feed)
registra la única ejecución autorizada de `84eae31`. Se usaron las dos
páginas adicionales. Hubo 300 filas, 299 avisos únicos, 37 candidatos
comerciales, 26 elegibles antes de aplicar el historial y 14 analizados
tras excluir 12 avisos de los 35 históricos. Los 14 avisos analizados
eran nuevos. Hubo 16 PDF, ocho rectores y una página recuperada con OCR.
Tres descargas superaron 10 MiB. No hubo un DOCX rector elegible.

Los 14 casos quedaron pendientes formalmente, con dos ambiguos y 12 sin
resolver. No hubo ausencias explícitas ni candidatos favorables. El cotejo
offline encontró cláusulas de experiencia en los cuatro silencios del
runner y conservó la clasificación automática original. El costo fue
154 créditos y 216,094 s, sin IA. Los resultados y los fragmentos del
cotejo se conservan en `.local/eureka-nacional-spike/en01-jocj50yr/`.
Cualquier otra corrida real requiere autorización.

## Continuidad técnica y registro de MPNE

El [cotejo técnico](eureka-nacional-experience-spike.md#en-01--cuatro-omisiones-y-manejo-documental-acotado)
recuperó las cuatro exigencias omitidas. Tres quedaron con prioridad
de exigencia aplicable y una mantuvo revisión por remisión a una tabla.
Se validó por portada un título concatenado, se reutilizó el lector
DOCX para adendas y se probó un tope optativo de 16 MiB para PDF rectores.
El valor predeterminado permanece en 10 MiB. Pasaron 224 pruebas offline.
Un rector de 121 páginas quedó parcial por tiempo en el replay local,
con 113 páginas recuperadas y la decisión conservada.

El [registro MPNE](eureka-nacional-experience-spike.md#hipótesis-exploratoria-futura--modelo-de-propensión-a-no-exigir-experiencia-mpne)
queda como hipótesis futura basada en cinco observaciones manuales de
cuatro entidades. El registro reutiliza los artefactos actuales para
procesos exigidos, favorables y pendientes. Se preservan los criterios
de descubrimiento y el historial de 49 avisos. No se ejecutó una nueva
corrida nacional. Cualquier corrida real posterior requiere autorización.

## Corrida con piloto de 16 MiB para PDF rectores

El [informe agregado](eureka-nacional-experience-spike.md#en-01--corrida-con-piloto-de-16-mib-para-pdf-rectores)
registra la única corrida autorizada con `938f038`. Se aplicaron los
49 avisos históricos y se usaron las dos páginas condicionales. De 300
avisos únicos se obtuvieron 42 candidatos comerciales, 28 elegibles
antes del historial y 12 nuevos con inventario. Se excluyeron 16
coincidencias históricas.

Los 20 intentos de descarga terminaron con `http_error`, incluidos
10 PDF rectores con el tope de 16 MiB y 10 intentos con el tope ordinario.
El estado HTTP específico no quedó en los artefactos. No se recibió
texto contractual. Los 12 procesos quedaron sin resolver y con
insuficiencia documental. El piloto queda sin evaluación y se mantiene
el registro de evidencia pendiente por proceso. El costo fue de 156
créditos y 117,516 s, sin OCR ni IA.

Las observaciones MPNE se guardaron junto a los resultados en
`.local/eureka-nacional-spike/en01-hsxjhqpg/`, diferenciando fuente,
inferencia y faltante. No se hizo otra corrida. Cualquier ejecución
real posterior requiere autorización.

## Diagnóstico de descargas SECOP

El [diagnóstico](eureka-nacional-experience-spike.md#en-01--diagnóstico-offline-de-adquisición-secop)
verificó que los 20 `http_error` ocurrieron antes de leer el archivo.
Hubo 59 descargas exitosas de 69 intentos en cinco corridas previas con el
mismo host y ruta archivados. Los artefactos del piloto no conservan el
estado HTTP ni la cadena de redirecciones. El código del adaptador no
cambió al habilitar el piloto de 16 MiB.

El runner conserva diagnóstico HTTP seguro en los artefactos locales.
La [sonda autorizada](eureka-nacional-experience-spike.md#resultado-de-la-sonda-autorizada-en-moniquirá)
hizo un solo GET directo al PDF rector archivado de Moniquirá. Recibió HTTP
403 en las cabeceras, con `HTTPError`, `text/html` y sin redirecciones.
No se descargó un archivo ni se repitió el intento. La causa detrás de
la denegación sigue indeterminada y el resultado no se extrapola al lote.

Antes de refrescar los 12 inventarios, validar con autorización el enlace
vigente del mismo documento y el acceso permitido. Después, recuperar los
rectores de los procesos ya descubiertos sin repetir la búsqueda. No hubo
consulta de feed, inventario ni recuperación adicional.

## Alternativa Edge para adquisición de EN-01

La [implementación experimental](eureka-nacional-experience-spike.md#en-01--alternativa-acotada-de-descarga-mediante-edge)
conserva `urllib` y permite un piloto optativo de lectura limitada con
Edge tras 403. La transferencia requiere tamaño declarado y se
cancela al superar la guarda o el plazo. La vía permanece desactivada
por defecto hasta comprobar Fetch/CORS con una prueba real autorizada.
Pasaron 262 pruebas offline.

La [validación real de Moniquirá](eureka-nacional-experience-spike.md#validación-real-de-fetch-en-moniquirá)
confirmó el enlace vigente del rector 896148933. El GET directo devolvió
HTTP 403. Edge Fetch se activó y CDP registró MissingAllowOriginHeader,
sin lectura del cuerpo y con limpieza confirmada. Ninguna vía guardó
el PDF. Los dos intentos respetaron el plazo observado de 12 s por
intento. No hubo nuevas consultas al feed ni descargas de otros procesos.

Tras recargar Edge, el inventario devolvió el mismo enlace y reaparecieron
HTTP 403 en urllib y MissingAllowOriginHeader en Fetch. La repetición
terminó tras dos intentos, sin PDF ni consultas al feed.

La reanudación mantiene los 12 procesos pendientes de en01-hsxjhqpg,
sus claves y su estado local. Fetch sigue desactivado por defecto. La
recuperación está pendiente y requiere autorización adicional. El piloto
terminó en los dos intentos concedidos.

## Evaluación offline de descarga nativa con Edge CDP

El [laboratorio de Edge](eureka-nacional-experience-spike.md#evaluación-offline-de-descarga-nativa-con-edge-cdp)
validó el clic, los eventos por GUID, el staging aislado y la cancelación
cuando ya existe un GUID. Una respuesta rápida sin tamaño declarado
transfirió 12 MiB antes de poder cancelar. Una respuesta que demoró las
cabeceras agotó el plazo sin proporcionar GUID. El mecanismo nativo no
se recomienda para adquisición automática con los topes vigentes.

La alternativa es verificar e incorporar copias autorizadas ya disponibles,
con el inventario y los recibos de EN-01 por DocumentId. La copia local
de Moniquirá tiene firma PDF, 595.065 bytes y 22 páginas. Todavía no se
incorporó. Se ejecutaron cinco casos de laboratorio en loopback y 134
regresiones pasaron, con una omitida. No hubo solicitudes a SECOP,
consultas al feed ni reanudación de los 12 procesos.

## Importación asistida y reanudación offline

El [procedimiento del importador](eureka-nacional-experience-spike.md#importación-asistida-y-reanudación-offline)
recibe un manifiesto local por referencia y DocumentId. Valida contra el
inventario y conserva recibos, cobertura y extracciones reutilizables.
Los 12 inventarios están disponibles en el lote en01-hsxjhqpg.

Se importó sólo el rector 896148933 de Moniquirá. Se leyeron las 22
páginas nativas, sin OCR. La página 11 exige dos contratos relacionados.
El caso queda explicit_requirement en prioridad comercial y not_resolved
como conclusión formal, con tres documentos pendientes. La repetición
reutilizó el binario y la extracción. Los otros 11 siguen sin importar.
Pasaron 164 pruebas, con una omitida y cero solicitudes de red. El estado
de importación se conserva localmente en en01-manual_hsxjhqpg.

## Laboratorio offline de streaming con Edge CDP

El [laboratorio y la sonda propuesta](eureka-nacional-experience-spike.md#laboratorio-offline-de-streaming-con-edge-cdp)
validaron el clic entre dos orígenes locales, la pausa de cabeceras y la
lectura por bloques vía CDP. Tras los rechazos de tamaño, tiempo,
integridad y pérdida de respuesta del canal no se almacenaron archivos.
Una simulación de cierre incierto bloqueó la siguiente adquisición hasta
destruir el contexto y crear uno nuevo. La lectura de EN-01 quedó acotada
a 10 MiB y la espera a 12 s. El tráfico de los búferes de Edge y del
sistema operativo queda fuera de ese control.

Se mantiene el runner sin cambios. Una sonda de un solo intento sobre
Moniquirá 896148933 queda propuesta y requiere autorización posterior.
No se llamó a SECOP, inventarios ni feed. Los otros 11 procesos siguen
pendientes. Pasaron 164 regresiones y una quedó omitida.

## Sonda real de streaming con Edge CDP

La [sonda de Moniquirá](eureka-nacional-experience-spike.md#resultado-de-la-sonda-real-de-streaming-en-moniquirá)
interceptó HTTP 200 para el rector 896148933 en un único GET. Leyó
595.065 bytes hasta EOF en 1,203 s. Tamaño, firma PDF y SHA-256 coincidieron
con la copia manual. Se confirmaron el cierre del flujo, el aborto de
la navegación interceptada y el cierre de la pestaña desechable. No
hubo reintentos ni consultas al feed o inventarios.

El mecanismo queda validado para ese documento. El runner sigue sin
cambios. Los 11 procesos restantes siguen pendientes. El informe
propone hasta tres rectores de tres procesos archivados como siguiente
lote, con autorización separada, sin repetir discovery.

## Piloto de recuperación CDP Streaming en tres procesos archivados

El [piloto](eureka-nacional-experience-spike.md#piloto-de-recuperación-cdp-streaming-en-tres-procesos-archivados)
recuperó tres PDF de Caicedonia, Maicao y la Registraduría. Tres GET
HTTP 200, tres cierres confirmados y 1.326.876 bytes verificados. La
extracción recuperó 78 páginas nativas, con cero OCR y cero IA.
El estado formal quedó not_resolved en los tres. La revisión
encontró un falso silencio en Caicedonia y una rebaja de rector a
soporte por el encabezado de plantilla en la Registraduría. Maicao
quedó con prioridad de exigencia aplicable.

Los binarios y recibos se conservan localmente. Ocho procesos aún
carecen de copia recuperada del rector. No hubo reintentos, consultas
al feed, refresco de inventarios ni cambios en el runner. La
recuperación progresiva necesita una autorización adicional.

## Correcciones offline y recuperación preparada

El [replay y comando](eureka-nacional-experience-spike.md#correcciones-offline-de-caicedonia-y-la-registraduría)
confirman exigencia aplicable en Caicedonia (pág. 8) y la Registraduría
(pág. 11). El estado de ambos sigue not_resolved. Maicao conserva su
prioridad. El corpus de cinco casos conocidos conservó los resultados
de control. Pasaron 177 pruebas y una quedó omitida.

El plan de en01-hsxjhqpg detectó cuatro recibos verificados y seis
rectores PDF elegibles. Pacho y La Estrella siguen pendientes de rector
verificable. Se recomienda autorizar primero un lote de hasta tres
procesos. urllib va primero y CDP Streaming se habilita sólo ante un 403
directo, con HTTP 200 PDF, tamaño declarado y cierre verificable.
No se ejecutaron recuperaciones ni consultas nuevas.

## Recuperación acotada ejecutada en tres procesos

El [lote autorizado](eureka-nacional-experience-spike.md#resultado-de-la-recuperación-acotada-de-el-espinal-bogotá-y-puerto-gaitán)
recuperó los PDF de El Espinal, Bogotá y Puerto Gaitán. Los tres
403 directos de urllib activaron CDP Streaming. Hubo tres HTTP 200,
tres archivos verificados, 21 créditos y tres cierres confirmados.
Se leyeron 58 páginas nativas y 2 por OCR. Puerto Gaitán mantiene
39 páginas pendientes. No hubo feed, inventarios, reintentos ni IA.

El Espinal tiene prioridad de exigencia aplicable y sigue
not_resolved. Bogotá quedó experience_ambiguous, con alcance pendiente
de corroborar. Puerto Gaitán quedó not_resolved por evidencia
insuficiente. Ningún caso presenta ausencia confirmada. Los tres
recibos se reconocieron al releer el plan local. Quedan tres
rectores PDF elegibles y dos procesos pendientes de identificar
rector. No se ejecutó otro lote.

## Recuperación de Rionegro y Chitaraque

El [lote del 26 de noviembre](eureka-nacional-experience-spike.md#recuperación-de-rionegro-y-chitaraque-26-de-noviembre-de-2026)
intentó dos rectores. urllib devolvió dos HTTP 403 directos. CDP
guardó el PDF de Rionegro, 595.319 bytes verificados y 2 de 12
páginas por OCR. Chitaraque se rechazó en cabeceras por superar
10 MiB declarados, con cierre confirmado y cero bytes leídos.
Se usaron 14 créditos y 13,452 s de adquisición. Ambos quedaron
not_resolved con prioridad de evidencia insuficiente.

Pendientes de adquisición: Chitaraque por tamaño, Yumbo por aviso
sin rector confirmado y Pacho y La Estrella sin rector PDF
inequívoco en el inventario archivado. Pendientes de OCR:
Rionegro con 10 páginas y Puerto Gaitán con 39. Puerto Gaitán
conserva su estado de evidencia insuficiente con 2 de 41 páginas
procesadas. No se descargó de nuevo ni se amplió su OCR.
No hubo feed, inventarios nuevos, reintentos ni IA.

## Cierre offline de cobertura documental

La [revisión de los PDF locales](eureka-nacional-experience-spike.md#cierre-offline-de-cobertura-documental-26-de-noviembre-de-2026)
encontró la experiencia mínima de Puerto Gaitán en las páginas
15 y 16 y la experiencia específica de Rionegro en las páginas
11 y 4. No se ejecutó OCR adicional. La cobertura automática sigue
2/41 y 2/12 respectivamente. Ambos siguen not_resolved con evidencia
insuficiente. Las cláusulas identificadas visualmente quedan como
evidencia para el replay dirigido.

Chitaraque supera 10 MiB. El tamaño exacto no se conservó y su
compatibilidad con 16 MiB queda por comprobar. El plan marca Yumbo
como aviso pendiente de corroboración. Pacho conserva el anexo con
referencia coincidente como pista. La Estrella requiere el pliego
definitivo. El runner registra el tamaño declarado antes de rechazarlo.
No hubo solicitudes nuevas ni exploración nacional.

## Validación offline de OCR dirigido

El [replay](eureka-nacional-experience-spike.md#validación-offline-de-ocr-dirigido)
procesó sólo Puerto Gaitán 15 y 16 y Rionegro 4 y 11. La cobertura
acumulada pasó a 4/41 y 4/12 respectivamente. En ambos siguen
not_resolved y evidencia insuficiente. Tesseract recuperó las
cláusulas, pero el clasificador las trató como condicionales,
también con transcripciones visuales corregidas. El OCR de
Rionegro deformó el sujeto de la cláusula. Una prueba con mandato
reconocido y PDF parcial mantuvo el resultado formal abierto.

Se propone incorporar señales de índice y estructura al selector
existente manteniendo dos páginas OCR por PDF, y validar las reglas
generales de obligación antes de la siguiente exploración. Los
artefactos quedan localmente en en01-directed-ocr_lxj95tq1. No
hubo acceso a CDP, SECOP, feed ni descargas.

## Obligaciones contractuales y selección OCR

El [replay](eureka-nacional-experience-spike.md#obligaciones-contractuales-y-selección-ocr)
elevó Puerto Gaitán y Rionegro de evidencia insuficiente a exigencia
aplicable, con not_resolved formal. En Puerto Gaitán se reconoce el
contrato ejecutado de la página 15. En Rionegro la lista de la
página 4 corrobora la cláusula de la página 11 con sujeto
dañado por OCR. El requisito formal de cobertura permanece.

El selector incorpora marcadores pertinentes, además de los
índices y encabezados nativos. La prueba de maquetación no
seleccionó las cláusulas principales en estos dos escaneos y no
quedó activa. Pasaron 195 pruebas y una quedó omitida. Se
recomienda una nueva muestra acotada con los límites vigentes
cuando se autorice. No se ejecutó ninguna consulta, descarga
ni exploración.

## Muestra nacional del 26 de noviembre

La [muestra](eureka-nacional-experience-spike.md#muestra-nacional-del-26-de-noviembre-de-2026)
aplicó 61 identidades históricas recalculadas y seleccionó 15 avisos
SECOP II nuevos. Nueve páginas devolvieron 270 filas, 269 avisos
distintos, 24 candidatos de suministro y 16 elegibles. Se
inventariaron dos procesos con 10 documentos y dos rectores por
título. Tres rechazos HTTP 403 de urllib activaron el corte
preventivo. El CLI nacional aún carece de integración con la vía
CDP Streaming validada en recuperación. No se activó Fetch.

Los dos casos con inventario quedaron not_resolved y evidencia
insuficiente. Quedaron 13 seleccionados sin inventario y los 15
pendientes de evidencia. No hubo texto para comprobar exigencias,
ausencias ni errores del clasificador. Se usaron 33 créditos y
45,468 s, con cero OCR y cero IA. El resultado y el registro MPNE
local se conservan en en01-abu8_p7u. Para retomar esta muestra,
reutilizar la selección archivada con una nueva autorización.

## Resiliencia integrada y auditoría offline del descubrimiento

El [informe](eureka-nacional-experience-spike.md#resiliencia-integrada-y-auditoría-offline-del-descubrimiento)
registra el streaming compartido por los dos comandos de EN-01.
El runner usa urllib primero y activa --edge-stream-fallback sólo
para PDF rector tras HTTP 403 directo. Mantiene el cupo, cierre
verificado, recibos y corte preventivo. Pasaron 201 pruebas offline,
con una omitida.

Entre 269 avisos hubo 165 SECOP II, 83 SECOP I, 17 de otros portales
y cuatro de universidades. Ocho avisos pasaron el prefiltro comercial
pero quedaron fuera por fuente documental, incluidos cinco SECOP I.
Uno de régimen especial SECOP II entró en la muestra y otro quedó fuera
por cupo. Los filtros comerciales siguen intactos.

El plan offline confirmó 15 procesos reanudables: dos con inventario
previo y 13 sin inventario. Se propone empezar por los dos primeros
bajo autorización nueva, sin feed. No se realizaron descargas ni
consultas durante este incremento.

## Reanudación controlada y SECOP I

La [reanudación](eureka-nacional-experience-spike.md#reanudación-de-yumbo-y-el-peñol-desde-d753731)
obtuvo el inventario de Yumbo y se detuvo al activar streaming.
El runner síncrono de Playwright ya tiene un bucle activo y
asyncio.run falló antes de iniciar la transferencia. No se
alcanzó El Peñol. Se usaron nueve créditos, con cero bytes,
OCR o IA. No hubo feed, preflight del runner ni otro lote.
Quedó la marca preventiva y se verificó que no quedaran
pestañas de transferencia. Se propone aislar el bucle de
streaming y verificarlo offline antes de solicitar otro intento.

La [auditoría SECOP I](eureka-nacional-experience-spike.md#auditoría-técnica-offline-de-secop-i)
confirmó cinco constancias y metadatos comerciales, sin enlaces
oficiales persistidos ni inventarios. Se propone validar un
inventario por constancia y hasta un rector PDF. Después se
reutilizarían la interfaz documental, el ranking, la extracción
y el clasificador de EN-01. Pasaron 21 pruebas del agregador.
No hubo consultas ni cambios de código para SECOP I.

## Plan aplicado para el segundo smoke

1. Normalizar prefijos de orden y separadores en títulos antes de asignar roles.
   Probar con una invitación numerada, un proyecto de pliego numerado y una
   cotización. Exigir evidencia de vigencia para tratar un rector como definitivo.
2. Priorizar rector vigente, invitación o pliego definitivo, y anexos habilitantes.
   Incorporar adendas aplicables que modifiquen la cláusula relevante. Reservar
   los cupos habilitantes para esas fuentes y excluir cotizaciones de esa cola.
3. Cuando un documento exceda tamaño o páginas, registrar la causa y considerar
   el siguiente rector o anexo aplicable dentro del presupuesto restante. Un
   intento fallido consume su cupo. Con cobertura insuficiente, conservar
   `not_resolved` y el motivo. Con evidencia concluyente, conservar versión,
   página y cláusula para revisión humana.
4. Validar offline con inventarios y fixtures locales. Comparar cobertura,
   causas de descarte y créditos por caso resuelto frente al primer smoke.
   La siguiente corrida requiere autorización.

Límites propuestos, iguales al primer smoke: 5 procesos, 30 días, hasta 4 páginas
de 30 filas, 5 intentos de descarga (máximo 2 por proceso y 10 MiB por PDF), 12
páginas por PDF, 2 páginas OCR por PDF, 60 créditos de red, 360 segundos y 0
llamadas de IA.

## Baseline aceptada

| Control | Resultado del checkpoint |
|---|---|
| Ruff | 17 infracciones `I001` y `E501`. |
| Prettier | Falla `frontend/src/features/research/EconomicCycle.tsx`. |
| Backend local | 1.736 pasaron, 4 fallaron, 31 se omitieron y 61 quedaron fuera de la selección. Los cuatro casos CDP pasaron al fijar el reloj de las pruebas al 22 de octubre de 2026. |
| Frontend local | 207 pasaron y una prueba de `ExplorePage.test.tsx` falló en la suite completa. La repetición de ese archivo pasó 15 de 15. |
| Integración PostgreSQL | Pendiente en un entorno de pruebas aislado. |

La ejecución base de GitHub Actions es la [44119052812](https://github.com/expolicores/radar-eureka/actions/runs/44119052812). El único workflow observado ejecuta CI ante pushes de ramas y tags y ante pull requests. El workflow carece de pasos de despliegue. GitHub mostró cero entornos y despliegues y Pages desactivado. Webhooks privados, permisos e instalaciones requieren revisión administrativa. Si se aprueba atender la deuda técnica, usar `fix/mvp-ci-stability` por separado. Distinguir fallos heredados de regresiones de EN-01.

## Perfil CDP configurable

EN-01 usa `resolve_profile_id` del repositorio antes de abrir CDP. La precedencia
es `--profile-id`, `LICITACIONES_PROFILE_ID` en el entorno o en `backend/.env`,
y error si falta. El mismo ID se usa en el preflight, las consultas y las
referencias de procesos. El [comando del smoke](eureka-nacional-experience-spike.md#smoke-test-preparado)
muestra cómo cargar el valor desde el `.env` existente cuando se trabaja desde
el worktree experimental.

El propietario confirmó que el preflight del nuevo perfil devolvió
`status: healthy`, `profile_available: true` y `get_info_status: 200`.
La autenticación sigue siendo manual en Edge CDP. La próxima corrida de EN-01
requiere autorización.

## Perfil comercial nacional

El [informe del universo comercial](eureka-nacional-universo-comercial.md)
recupera los filtros regionales y valida la matriz oficial UNSPSC UNv260801.
El archivo de configuración es
`backend/config/eureka_nacional_commercial.v1.json`. La CLI lo aplica antes del
inventario y registra cobertura de metadatos, coincidencias, categorías, motivos
de exclusión, muestra de revisión y costo operativo. La modalidad de mínima
cuantía y el estado abierto ordenan la selección.

La verificación del perfil encontró 127 nodos en el catálogo oficial. Pasaron
43 pruebas de EN-01 y 312 de regresión compartida. Las cuatro pruebas CDP
dependientes de fecha de la baseline quedaron fuera de esta selección. Ruff y
formato pasaron en los archivos Python modificados.

En el primer smoke, las coincidencias elegibles provinieron de palabras clave. El campo UNSPSC estuvo ausente en las 120 filas.

## Cobertura geográfica explícita

La configuración `backend/scripts/eureka_nacional_geography(from_licitaciones_info).v1.json`
coincide con el adjunto del propietario y conserva el orden de sus 1.130
identificadores únicos. EN-01 valida el archivo antes de conectar a CDP y
reutiliza `build_process_payload`. Cada página envía la lista completa en
`query.ubicacion_filter`. El perfil comercial y el pipeline documental
conservan sus reglas.

La cadena exacta transmitida contiene 1.129 comas y tiene SHA-256
`f4f1d02fd12e1738402c8ef4a261ff1d13a427198f26293b0d024fa8afd0619b`.
Pasaron 134 pruebas offline de EN-01, del constructor compartido y del plan regional. Ruff y formato pasaron en los archivos Python modificados.

El endpoint aceptó el filtro explícito y devolvió cuatro páginas de 30 filas únicas. Los conteos del proveedor variaron por página.
El [comando actualizado](eureka-nacional-experience-spike.md#smoke-test-preparado)
indica explícitamente la ruta de la captura.

## Verificación de EN-01

- 26 pruebas de EN-01 pasaron en local, con respuestas CDP simuladas, almacenamiento
  por hash y lectura nativa y OCR real en español de fixtures versionados.
- La selección de regresión documental y CDP pasó 312 pruebas compartidas y
  reprodujo las cuatro fallas dependientes de fecha de la baseline.
- Ruff y la comprobación de formato pasaron en los tres archivos Python nuevos.
- Las pruebas offline y la corrida real generaron salidas locales excluidas de Git.

## Verificación reproducible

Desde este worktree:

```powershell
git status --short --branch
git log -1 --oneline
git worktree list
git cat-file -t refs/tags/eureka-mvp-v0.1
git rev-parse 'refs/tags/eureka-mvp-v0.1^{}'
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git ls-remote origin refs/heads/main refs/heads/experiment/eureka-nacional refs/tags/eureka-mvp-v0.1 'refs/tags/eureka-mvp-v0.1^{}'
git check-ignore -v -- .local/eureka-nacional-spike/probe.pdf backend/scripts/.local/storage_state.candidate.json
git diff --cached --name-status
```

Registrar el commit, pruebas, artefactos y cambios de fase en este archivo.

## Trabajador de Streaming y preparación de SECOP I

El runner nacional y la recuperación comparten el trabajador
aislado de EN-01. La llamada síncrona puede ejecutarse con el
bucle de Playwright activo. El trabajador conserva los topes de
transferencia y el padre verifica su salida, el archivo y el
cierre de Edge antes de publicar. La marca preventiva sigue
bloqueando adquisiciones si el cierre de la pestaña es incierto.
La marca de la corrida anterior se conservó durante esta fase.

Quedan dos planes pendientes de autorización. Para Yumbo y
El Peñol, comprobar y registrar primero la recuperación segura de
la sesión local y usar el comando archivado de dos procesos sin
feed ni preflight del feed. Para SECOP I, usar sólo la constancia
26-13-14852794 de Casabianca, una ficha oficial y hasta un PDF
rector verificable con 10 MiB, 12 s y dos páginas OCR. Los
[procedimientos y criterios de parada](eureka-nacional-experience-spike.md#corrección-del-bucle-y-próximas-pruebas-controladas)
quedan en el informe. No se ejecutó ninguno de los dos planes.


### Estado de la reanudación autorizada

Los controles locales no encontraron transferencias pendientes
del intento anterior. El arranque supervisado de Contratos no
obtuvo el cliente Axios y se detuvo con la marca preventiva
conservada. Cero inventarios, descargas, OCR y clasificaciones
nuevas. La ejecución única de Yumbo y El Peñol sigue pendiente
de que el propietario deje una sola pestaña funcional en
Contratos desde Edge CDP dedicado. Al abrirla, verificar el
estado local y aplicar el procedimiento de reanudación con la
selección archivada y el feed bloqueado.


### Resultado del lote único de Yumbo y El Peñol

La pestaña de Contratos pasó el preflight. Se archivó la marca
anterior tras verificar el cierre y se ejecutó la única
reanudación autorizada. Ambos inventarios devolvieron cinco
documentos. Las invitaciones recibieron HTTP 403 directo sin
redirección por urllib. Ambos trabajadores arrancaron desde el
runner real y terminaron con TimeoutError antes de abrir una
pestaña de adquisición. No quedó un cierre incierto.

El lote consumió cuatro intentos, 18 créditos y 29,578 s.
Cero descargas, recibos, páginas, OCR e IA. Ambos procesos
siguen not_resolved con evidencia insuficiente. El siguiente
diagnóstico es offline y debe localizar el paso exacto del
timeout al arrancar el trabajador. La autorización de este
lote se utilizó y SECOP I sigue pendiente.


### Diagnóstico offline del trabajador y siguiente cobertura

En Edge aislado se reprodujo el timeout en la conexión CDP
cuando una navegación interceptada esperaba al runner
bloqueado. La corrección mantiene activos los eventos de
Playwright mientras concluye el proceso hijo. El mismo
trabajador pasó de la conexión CDP a la búsqueda de contexto
en la prueba sintética. Los registros de la última
reanudación no permiten atribuirle esa causa con certeza.
La traza nueva registra el paso exacto de arranque, y el
corte por cierre incierto y fallo generalizado sigue activo.

Yumbo y El Peñol quedan cerrados por ahora. La próxima
validación de cobertura propuesta es una sola ficha SECOP I
de Casabianca MC-SPM-055-2026, constancia 26-13-14852794, y
hasta un rector verificable, con autorización previa. El
[procedimiento y los criterios de parada](eureka-nacional-experience-spike.md#próxima-capacidad-de-cobertura-secop-i)
quedan en el informe. No hubo consultas SECOP ni feed en
este incremento.


### Resultado de la primera prueba oficial de SECOP I

La consulta HTTPS única de Casabianca MC-SPM-055-2026,
constancia 26-13-14852794, recibió HTTP 403 en 0,687 s.
Se detuvo en cabeceras. No hubo inventario verificable,
rector identificado, adquisición de PDF, OCR ni clasificación
nueva. El caso queda not_resolved por evidencia insuficiente.

La autorización del intento se utilizó. Una futura prueba
separada debe confirmar una ruta oficial accesible para esa
constancia antes de intentar un solo rector. Se mantiene el
pipeline EN-01 para cualquier archivo verificado. El
[resultado y propuesta mínima](eureka-nacional-experience-spike.md#prueba-real-de-ficha-secop-i-de-casabianca)
quedan en el informe.


### Resultado de la navegación SECOP I en Edge

La única navegación a Casabianca MC-SPM-055-2026, constancia
26-13-14852794, devolvió HTTP 200 en 1,219 s. Se verificaron
entidad, referencia y cinco documentos. INVITACION, de
1,80 MB según la ficha, es el único rector identificado
por título. El control documental invoca reCAPTCHA. Como
esa adquisición no está validada con los límites de EN-01,
se detuvo la prueba sin descarga, OCR ni clasificación
documental. La pestaña quedó cerrada y la causa del 403
del GET directo anterior sigue sin determinar.

El caso queda not_resolved. La opción acotada siguiente es
una importación asistida desde el control oficial con
autorización separada. El
[resultado y límites de cobertura](eureka-nacional-experience-spike.md#navegación-controlada-en-edge-a-la-ficha-secop-i-de-casabianca)
quedan en el informe.


### SECOP I mediante el inventario de Licitaciones.info

El JavaScript ya cargado confirmó que las rutas relativas se
envían por formulario POST con el campo ruta al servicio
oficial VerDocumento. El normalizador offline valida
identidad, formato y metadatos y reutiliza el ranking EN-01.
La adquisición automática sigue desactivada. El CDP del
laboratorio pudo leer y cerrar un POST sintético y rechazar
tamaño excesivo, falta de longitud y redirecciones. Falta
verificar la pestaña de destino del control real y la
respuesta oficial dentro de las guardas.

La propuesta pendiente de autorización usa únicamente la
constancia 26-13-14853238, con una solicitud de inventario,
un solo PDF rector, 10 MiB, 12 s y dos páginas OCR. El
[diagnóstico y procedimiento](eureka-nacional-experience-spike.md#inventarios-secop-i-de-licitacionesinfo)
quedan en el informe. No se realizaron llamadas al
proveedor ni descargas reales.


### Resultado de la sonda POST de Encino

En Licitaciones.info, la constancia 26-13-14853238 corresponde
a Encino MC-014-2026. El único inventario devolvió HTTP 200 y
seis PDF con fase nula explícita. La invitación de 5,39 MB
quedó primera por título. El control se activó una sola vez.
La pestaña emergente no se pudo vincular al origen y la
limpieza del supervisor la reanudó fuera de la intercepción.
La descarga nativa dejó un archivo de 5.651.103 bytes que
no se incorporó a EN-01. Sin recibo ni análisis, el caso
sigue not_resolved y la marca de cierre incierto se conserva.

La próxima mejora admisible es el parser de inventario
offline y una regresión del cierre que pruebe que un destino
no identificado no puede emitir el POST. Mantener desactivada
la descarga automática. El
[resultado de la sonda](eureka-nacional-experience-spike.md#sonda-real-secop-i-por-formulario-post-en-encino)
documenta los límites observados y el alcance de una
validación futura. No se autoriza un nuevo intento a partir
de este resultado.


### Guarda offline de pestañas para SECOP I

Se reprodujo en Edge aislado el formulario _blank sin
acceso al origen y su descarga nativa. La guarda de EN-01
abre una pestaña en blanco en un contexto desechable con
las descargas nativas denegadas. Verifica origen y marco y
exige el acuse de Fetch antes de permitir el envío en la
prueba. Cierra el contexto sin reanudar destinos y retiene
la marca si queda incierto el cierre del contexto o del
trabajador.

Pasaron seis regresiones focalizadas, 245 pruebas
existentes y el laboratorio de Streaming. La marca real de
Encino se conservó. La descarga automática sigue
desactivada hasta verificar un modo de usar la sesión
autorizada dentro de un contexto desechable y prearmar el
destino del formulario oficial. El
[resultado del laboratorio](eureka-nacional-experience-spike.md#cierre-seguro-de-una-pestaña-secop-i-en-un-contexto-desechable)
documenta el bloqueo, el alcance de las guardas y la
condición pendiente. La prueba real no se repitió.


### Compatibilidad offline de sesión y formulario SECOP I

En Edge aislado, una sesión sintética de otro contexto no
estuvo disponible en el contexto desechable. El login por
la interfaz dentro del contexto protegido sí funcionó.
El mismo formulario HTML, enviado desde una pestaña
asociada con Fetch preparado, produjo un solo POST
interceptado entre dos sitios loopback y un PDF
sintético verificado. Se mantuvieron la denegación de
descargas nativas, el cierre comprobado y el bloqueo
preventivo. La marca real de Encino sigue en su sitio.

El flujo es viable en el laboratorio con una sesión
establecida dentro del contexto protegido. Sigue por
validar el login real y la aceptación del POST oficial
con la pestaña prearmada. El control original que crea
el destino _blank continúa desactivado para adquisiciones
automáticas. El
[procedimiento de una sonda](eureka-nacional-experience-spike.md#sonda-única-propuesta-pendiente-de-autorización)
queda pendiente de autorización. La contingencia disponible
es la importación asistida de un PDF verificado.


### Resultado del preflight protegido de Encino

Tras el login manual, la pestaña de Contratos presentó
el cliente del portal, pero get-config-user no
acreditó la sesión en el contexto desechable. El titular
reportó un aviso de URL inexistente. La causa sigue
indeterminada. Se bloquearon siete solicitudes del feed.

La sonda se detuvo con cero POST documentales y cero
inventarios. El contexto y el trabajador cerraron y se
retiró la marca propia. No se probó el POST oficial ni
se ejecutaron extracción o clasificación. Se mantiene
not_resolved. El
[detalle del preflight](eureka-nacional-experience-spike.md#sonda-final-secop-i-detenida-en-el-preflight-de-sesión)
quedó en el informe.


### Preflight pasivo de SECOP I listo, sin sonda real

El diagnóstico pasivo descartó la construcción de URL y
la sesión como causa. En el contexto desechable, la
propia aplicación recibió 200 de get-config-user y de
todo el arranque. El aviso «No encuentro URL» proviene
del get-info bloqueado por la guarda. El 404 anterior
queda sin reproducir.

El preflight ya no hace peticiones propias, y la sonda
local v2 conecta al Edge dedicado del puerto 9232. Está
pendiente confirmar el perfil infoexpress, que sólo se
puede verificar en la próxima sesión real a partir del
get-info bloqueado. Una única prueba real de SECOP I
requiere autorización explícita.
[Detalle del preflight](eureka-nacional-experience-spike.md#preflight-pasivo-de-secop-i).


### Preflight v2 real: sesión válida, perfil no confirmado

La sesión del contexto desechable fue válida y todos los errores
observados se atribuyen al feed bloqueado por la guarda. El
get-info/MP de la aplicación llevaba varios perfiles, por lo que
infoexpress no quedó confirmado y la sonda no quedó lista para
adquirir. No hubo descargas, inventarios ni POST. Repetir la
prueba requiere una nueva autorización.
[Detalle](eureka-nacional-experience-spike.md#corrida-real-del-preflight-v2-sin-adquisición).


### Cierre seguro y perfiles diferenciados (offline)

El preflight reporta only_configured, configured_with_others,
without_configured o absent/undetermined, sin identificadores. La
adquisición exige only_configured. La sonda local registra el
cierre en cualquier desenlace y sólo libera el marcador con
evidencia completa de cierre seguro. La próxima corrida real debe
hacerse con sólo infoexpress seleccionado en la UI y requiere
autorización.
[Detalle](eureka-nacional-experience-spike.md#correcciones-offline-cierre-seguro-y-diagnóstico-de-perfiles).


### Preflight real listo con infoexpress

La sesión es válida, el perfil es only_configured con un solo
perfil, el feed estuvo bloqueado y el cierre fue seguro, con el
marcador liberado. ready_for_acquisition fue true. No se descargó
nada. La única descarga SECOP I de Encino queda pendiente de
autorización explícita.
[Detalle](eureka-nacional-experience-spike.md#verificación-real-del-perfil-infoexpress-preflight-listo).


### Descarga SECOP I de Encino: POST interceptado, PDF sin tamaño declarado

El preflight volvió a quedar listo y se reenvió un único POST
interceptado. VerDocumento respondió 200 application/pdf sin
Content-Length. La sonda lo rechazó sin leer el cuerpo: cero
bytes, ningún archivo y ninguna descarga nativa. El cierre fue
seguro y el marcador se liberó. pdf-attempt.lock agota el intento.
Antes de otra ronda hay que decidir si conviene aceptar respuestas
sin tamaño declarado o usar la importación asistida existente.
[Detalle](eureka-nacional-experience-spike.md#adquisición-secop-i-de-encino-detenida-por-tamaño-no-declarado).


### SECOP I sin Content-Length: streaming acotado listo (offline)

`read_secop1_pdf` acepta PDF sin tamaño declarado dentro de 10 MiB
y 12 s. Exige cierre verificado del flujo, `%PDF-`, `%%EOF` cerca
del final y SHA-256, y no escribe nada hasta aceptar. El
laboratorio aislado lo validó con Edge real en tres variantes: por
bloques, con cierre de conexión y truncada, que se rechaza. Edge
no señala la truncación, así que `%%EOF` es la única defensa y no
garantiza integridad. La sonda local quedó preparada en modo
`--acquire`, pero `pdf-attempt.lock` bloquea el intento hasta que
se autorice expresamente archivarlo.
[Detalle](eureka-nacional-experience-spike.md#streaming-acotado-de-secop-i-sin-content-length-offline).


### PDF de Encino recuperado por SECOP I

La invitación de MC-014-2026 (constancia 26-13-14853238) se
recuperó con un único POST interceptado, sin Content-Length:
5.651.103 bytes, `%PDF-1.4`, `%%EOF` y SHA-256
`174e63c9…6fddd`. Está en staging local por hash. El cierre fue
seguro, el marcador se liberó y no hubo descargas nativas. La
siguiente fase es integrar esta descarga con la extracción y la
clasificación de experiencia, y requiere autorización.
[Detalle](eureka-nacional-experience-spike.md#segunda-adquisición-secop-i-de-encino-pdf-recuperado).


### Encino clasificado: not_resolved por cobertura insuficiente

La invitación recuperada es un escaneo de 36 páginas sin texto
nativo. Con el límite de dos páginas de OCR se leyeron las páginas
1 y 2: identidad confirmada, objeto y alcance, sin menciones de
experiencia. El clasificador devolvió not_resolved con
governing_documents_incomplete y review_priority 4. La prioridad
comercial no está determinada porque no hay registro de
descubrimiento guardado. Para resolver el caso hace falta
autorizar más OCR sobre la invitación. Para incorporar SECOP I al
flujo nacional falta, además:

- Una política de OCR para escaneos largos.
- Un registro de intentos por documento.
- Descubrimiento persistido con prioridad comercial.
- La integración del preflight con login manual en el runner.

[Detalle](eureka-nacional-experience-spike.md#primera-clasificación-documental-secop-i-encino).


### SECOP I integrado al runner en tres etapas (offline)

- `--include-secop1` y `--secop1-processes`, como máximo 5,
  añaden inventario y cola de PDF rectores. SECOP II queda
  idéntico con la opción desactivada.
- `eureka_nacional_secop1_acquire.py <corrida>` hace un login,
  el preflight, una confirmación ligada al hash del lote y como
  máximo 5 POST con registro de intento por documento.
- `eureka_nacional_secop1_flow.py <corrida>` hace la reanudación
  offline con OCR selectivo: 12 páginas por rector y 60 páginas o
  6 minutos por corrida.

Pendiente: autorizar la primera corrida nacional controlada.
[Detalle](eureka-nacional-experience-spike.md#integración-experimental-de-secop-i-en-el-runner-nacional-offline).


### Corrida nacional integrada: SECOP I bloqueado por el cortacircuitos de SECOP II

En en01-xgcp5mgp, SECOP I fue el 31 % del descubrimiento: 75 de
240 procesos, con 8 elegibles y 5 seleccionados. Pero el
cortacircuitos de descargas de SECOP II, abierto por un 403
directo generalizado y por rectores de más de 10 MiB, detuvo la
corrida antes del inventario SECOP I: la cola quedó vacía. SECOP
II dio 6 procesos analizados y todos not_resolved. Hace falta
autorizar una corrección para desacoplar las etapas antes de
seguir.
[Detalle](eureka-nacional-experience-spike.md#primera-corrida-nacional-integrada-etapa-1-en01-xgcp5mgp).


### Lote SECOP I recuperado, pendiente de aprobación

Se recuperaron los inventarios de los 5 procesos SECOP I
seleccionados en en01-xgcp5mgp, con 5 peticiones y sin feed. Se
encolaron 5 invitaciones; lote `a9871484…53b5c614`. La de
Sutatenza mide 22,68 MB y excede el límite. No hubo descargas ni
POST.
[Detalle](eureka-nacional-experience-spike.md#corrección-de-orquestación-y-recuperación-de-inventarios-secop-i).
