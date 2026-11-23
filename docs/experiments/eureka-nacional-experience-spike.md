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
| Extracción nativa | Hasta 12 páginas por PDF y 60 páginas de documento por corrida. |
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
