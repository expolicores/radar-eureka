# EN-01 · Experiencia contractual en procesos de suministro

**Estado:** implementación mínima preparada. Corrida real pendiente de revisión y autorización. Las cifras de este informe quedan pendientes hasta contar con evidencia.

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

Registrar documentos, páginas, OCR, duración, volumen, llamadas IA y costos conocidos o estimados. Calcular costo por proceso resuelto y por candidato confirmado cuando existan datos. Las pruebas de regresión se compararán con el baseline del handoff. Los resultados, conclusiones y recomendaciones de iteración quedan pendientes.

## Estrategia implementada

- **Discovery.** Consulta get-info en orden descendente por FechaPublicacion, sin
  filtro geográfico ni términos enviados al proveedor. Aplica localmente el
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
reutiliza la sesión en memoria mediante CDP.

Desde la raíz del worktree experimental, en PowerShell:

```powershell
$spikePython = if (Test-Path '.\backend\.venv\Scripts\python.exe') {
    (Resolve-Path '.\backend\.venv\Scripts\python.exe').Path
} else {
    (Resolve-Path '..\COMPRAS PUBLICAS\backend\.venv\Scripts\python.exe').Path
}
$env:PYTHONPATH = (Resolve-Path '.\backend\src').Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& $spikePython '.\backend\scripts\eureka_nacional_en01.py' --processes 5 --documents 5 `
  --discovery-pages 4 --recent-days 30 --cdp-url 'http://127.0.0.1:9232' `
  --commercial-profile '.\backend\config\eureka_nacional_commercial.v1.json' `
  --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

El intérprete alternativo reutiliza dependencias Python 3.12 ya instaladas de solo
lectura. Las importaciones de la aplicación apuntan a este worktree. La CLI usa una
URL de base deshabilitada y su extractor llama al servicio compartido en dry-run.

| Tope del smoke propuesto | Valor |
|---|---:|
| Procesos seleccionados | 5. La CLI acepta 5–10. |
| Discovery | 4 páginas de hasta 30 filas, 30 días de publicación de Bogotá. |
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
