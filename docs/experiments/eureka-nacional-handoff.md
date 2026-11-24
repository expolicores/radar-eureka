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
