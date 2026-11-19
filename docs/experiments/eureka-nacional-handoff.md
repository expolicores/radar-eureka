# Handoff de Eureka Nacional

## Estado de la preparación

- Línea estable `main`. Checkpoint `670b0c472978e5750195e550bf29f5644df74f14`. Objeto de tag anotado `e07d811c8e9b58250c4cb4d69f5d5eaee610ec79`.
- Rama `experiment/eureka-nacional`, creada localmente en el checkpoint. Worktree en `C:\Users\juank\Desktop\EUREKA NACIONAL`. El worktree regional conserva su cambio local en `.claude/logs/.last-sync.json`, que contiene únicamente `lastSyncTime`.
- Upstream `origin/experiment/eureka-nacional` y tag remoto `eureka-mvp-v0.1` verificados.
- La preparación incluye estos tres documentos y las exclusiones de artefactos. Esta fase generó cero corridas, cero descargas experimentales y cero consumo de IA.

## Estado de EN-01

El 19 de noviembre de 2026 se verificaron el tag anotado publicado, el checkpoint de
`main` y la rama remota. La implementación mínima vive en
`backend/scripts/eureka_nacional_en01.py` y las reglas determinísticas en
`backend/scripts/eureka_nacional_experience.py`. No se abrió una sesión real ni se
realizaron consultas a Licitaciones.info, descargas SECOP ni llamadas de IA.

El [informe de EN-01](eureka-nacional-experience-spike.md) contiene la estrategia,
los límites y el comando del smoke test. Continuar con una corrida real de cinco
procesos únicamente tras la revisión y autorización del propietario. Revisar las
clasificaciones de ausencia antes de interpretar el rendimiento comercial.

## Baseline aceptada

| Control | Resultado del checkpoint |
|---|---|
| Ruff | 17 infracciones `I001` y `E501`. |
| Prettier | Falla `frontend/src/features/research/EconomicCycle.tsx`. |
| Backend local | 1.736 pasaron, 4 fallaron, 31 se omitieron y 61 quedaron fuera de la selección. Los cuatro casos CDP pasaron al fijar el reloj de las pruebas al 22 de octubre de 2026. |
| Frontend local | 207 pasaron y una prueba de `ExplorePage.test.tsx` falló en la suite completa. La repetición de ese archivo pasó 15 de 15. |
| Integración PostgreSQL | Pendiente en un entorno de pruebas aislado. |

La ejecución base de GitHub Actions es la [44119052812](https://github.com/expolicores/radar-eureka/actions/runs/44119052812). El único workflow observado ejecuta CI ante pushes de ramas y tags y ante pull requests. El workflow carece de pasos de despliegue. GitHub mostró cero entornos y despliegues y Pages desactivado. Webhooks privados, permisos e instalaciones requieren revisión administrativa. Si se aprueba atender la deuda técnica, usar `fix/mvp-ci-stability` por separado. Distinguir fallos heredados de regresiones de EN-01.

## Verificación de EN-01

- 26 pruebas de EN-01 pasaron en local, con respuestas CDP simuladas, almacenamiento
  por hash y lectura nativa y OCR real en español de fixtures versionados.
- La selección de regresión documental y CDP pasó 312 pruebas compartidas y
  reprodujo las cuatro fallas dependientes de fecha de la baseline.
- Ruff y la comprobación de formato pasaron en los tres archivos Python nuevos.
- La validación de cobertura, autenticación y paginación del proveedor queda para
  el smoke test real. Las salidas de prueba se guardaron en .local y quedan fuera de Git.

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
