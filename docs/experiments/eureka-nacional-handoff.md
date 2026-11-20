# Handoff de Eureka Nacional

## Estado de la preparación

- Línea estable `main`. Checkpoint `670b0c472978e5750195e550bf29f5644df74f14`. Objeto de tag anotado `e07d811c8e9b58250c4cb4d69f5d5eaee610ec79`.
- Rama `experiment/eureka-nacional`, creada localmente en el checkpoint. Worktree en `C:\Users\juank\Desktop\EUREKA NACIONAL`. El worktree regional conserva su cambio local en `.claude/logs/.last-sync.json`, que contiene únicamente `lastSyncTime`.
- Upstream `origin/experiment/eureka-nacional` y tag remoto `eureka-mvp-v0.1` verificados.
- La preparación incluye estos tres documentos y las exclusiones de artefactos. Esta fase generó cero corridas, cero descargas experimentales y cero consumo de IA.

## Estado de EN-01

El primer smoke real se ejecutó el 19 de noviembre de 2026 en Edge CDP dedicado
con el runner `11cad4d`. Resultado parcial, `en01-ms7c7hyc` (salida `2`). El
preflight pasó y el endpoint devolvió 120 registros únicos de 26 departamentos
en cuatro páginas. Los cinco candidatos seleccionados tuvieron inventario. De
43 documentos se intentaron cinco descargas y se obtuvieron cuatro. Una
descarga superó 10 MiB y tres PDF superaron 12 páginas. Se extrajo una página
nativa, se usaron 46 créditos de red y se registraron 0 páginas OCR y 0 llamadas
de IA. Los cinco casos siguen `not_resolved`.

El [informe agregado](eureka-nacional-experience-spike.md#primer-smoke-real--19-de-noviembre-de-2026)
contiene el funnel, los errores y las recomendaciones. El detalle permanece
bajo `.local/eureka-nacional-spike/en01-ms7c7hyc/`. Antes de solicitar otra
corrida, revisar offline la prioridad documental en títulos numerados y
cotizaciones. La siguiente ejecución requiere autorización.

## Baseline aceptada

| Control | Resultado del checkpoint |
|---|---|
| Ruff | 17 infracciones `I001` y `E501`. |
| Prettier | Falla `frontend/src/features/research/EconomicCycle.tsx`. |
| Backend local | 1.736 pasaron, 4 fallaron, 31 se omitieron y 61 quedaron fuera de la selección. Los cuatro casos CDP pasaron al fijar el reloj de las pruebas al 22 de octubre de 2026. |
| Frontend local | 207 pasaron y una prueba de `ExplorePage.test.tsx` falló en la suite completa. La repetición de ese archivo pasó 15 de 15. |
| Integración PostgreSQL | Pendiente en un entorno de pruebas aislado. |

La ejecución base de GitHub Actions es la [44119052812](https://github.com/expolicores/radar-eureka/actions/runs/44119052812). El único workflow observado ejecuta CI ante pushes de ramas y tags y ante pull requests. El workflow carece de pasos de despliegue. GitHub mostró cero entornos y despliegues y Pages desactivado. Webhooks privados, permisos e instalaciones requieren revisión administrativa. Si se aprueba atender la deuda técnica, usar `fix/mvp-ci-stability` por separado. Distinguir fallos heredados de regresiones de EN-01.

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
