# Eureka Nacional

Eureka Regional conserva en `main` el MVP funcional para compras públicas, con operación principalmente en Boyacá, Santander y Casanare. El checkpoint histórico y base del experimento es `670b0c472978e5750195e550bf29f5644df74f14`, marcado con el tag anotado `eureka-mvp-v0.1`. Eureka Nacional se desarrolla en `experiment/eureka-nacional`.

EN-01 pregunta si podemos identificar a escala nacional procesos de suministro donde la experiencia contractual no sea una barrera de entrada. La percepción inicial del 80–90 % de procesos con requisito es una hipótesis por medir. La suficiencia documental sobre experiencia aporta una señal comercial. La elegibilidad integral requiere evaluación adicional.

El [perfil comercial nacional](eureka-nacional-universo-comercial.md) acota la
muestra a bienes comercializables por terceros. Separa prioridades A y B,
conserva familias regionales pertinentes y combina coincidencias UNSPSC
verificadas con objeto y descripción. La oferta y la disponibilidad de los
bienes requieren validación comercial.

La cobertura de discovery usa los 1.130 identificadores internos capturados en
Licitaciones.info, conservados en
`backend/scripts/eureka_nacional_geography(from_licitaciones_info).v1.json`.
Cada página reutiliza `query.ubicacion_filter` con la lista completa, separada
por comas.

El descubrimiento nacional será una capacidad común para participación
tradicional, adquisición estratégica de experiencia contractual e
intermediación multiproducto. EN-01 prepara esa capacidad mediante un solo
flujo experimental.

## Arquitectura y alcance

- Reutilizar `LicitacionesInfoSource` en `backend/src/public_procurement/licitaciones_cdp/adapters.py`, y `PageClient` y `fetch_inventory` en `backend/scripts/licitaciones_cdp_runtime.py`. Usar el mecanismo autorizado de `backend/scripts/licitaciones_auth.py`.
- La fuente de discovery e inventario de EN-01 es Licitaciones.info vía CDP. Contrastar después con Socrata si aporta valor. La cobertura nacional, la paginación y el flujo vivo requieren validación.
- Reutilizar `backend/src/public_procurement/documents/ports.py`, `SecopDownloader` en `documents/adapters/secop.py`, `LocalBinaryStorage` en `documents/adapters/local_storage.py` y la extracción híbrida de `extraction/adapters/hybrid.py` con Tesseract `spa`. Las rutas abreviadas parten de `backend/src/public_procurement/`.
- La orquestación experimental será manual y aislada. Los servicios regionales con persistencia, el scheduler, las migraciones, los agentes regionales, la UI y los despliegues quedan fuera del alcance de EN-01.
- Acotar procesos, documentos, páginas, OCR, duración, llamadas de IA y costo antes de cada corrida. La implementación mínima está autorizada. La corrida real y el consumo de IA se autorizan por separado.

## Privacidad y custodia

El propietario decidió mantener el repositorio público y posponer el saneamiento del historial como actividad independiente. Se aceptó el checkpoint funcional con los hallazgos históricos y la deuda de CI. La revisión documental histórica permanece como pendiente de seguridad ajeno a EN-01. Los archivos del plan y del inventario se conservan fuera del control de versiones.

Escribir artefactos en `/.local/eureka-nacional-spike/<run-id>/` dentro del worktree experimental. Mantener perfiles autenticados, credenciales, cookies, tokens y logs sensibles en almacenamiento local restringido fuera de los worktrees. Versionar únicamente código, pruebas, documentación técnica y métricas agregadas revisadas. Revisar el índice de cada commit. El estado heredado del historial no autoriza incorporar nuevos originales, datos personales ni artefactos privados.
