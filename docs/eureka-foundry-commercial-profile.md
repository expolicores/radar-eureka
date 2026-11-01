# Eureka Assistant — perfil comercial vivo y recomendaciones sustentadas

Implementado `get_eureka_commercial_profile()` como sexta tool sin parámetros,
read-only, strict=true y additionalProperties=false. No usa DB, consultas externas,
scoring ni adquisición documental: proyecta configuración validada mediante
`eureka.services.get_eureka_commercial_profile(settings)`.

## Fuentes y semántica

- Regiones: `Settings.eureka_radar_regions`.
- Familias, etiquetas y pesos: catálogo indicado por `Settings.eureka_radar_config_path`.
  Se recarga el catálogo en cada lectura; no se mantiene una copia en el prompt.
  Las familias discovery_only se presentan separadas de las comerciales.
- Monto preferido: `Settings.eureka_preferred_budget_max`, con moneda COP.
  Superarlo exige revisión y no es una exclusión automática por monto.
- Tope de la bandeja: configuración existente de `review_fit`; se identifica su
  alcance como Merecen Revisión. No se confunde con el monto preferido ni con alertas.
- Complejidad: review_terms y límites configurados de ejecución/pago.
- Provenance: versión, fingerprint del catálogo, nombre de archivo y nombres de
  settings. No se entrega el objeto Settings completo, conexiones ni credenciales.

Valores observados al implementar: Boyacá/Casanare, preferido 30.000.000 COP,
tope de revisión 100.000.000 COP. El catálogo real tiene ocho familias comerciales,
incluyendo mobiliario y refrigerios preparados condicionales, más una familia solo
de discovery. No se eliminaron categorías para ajustar la salida a un ejemplo.
Los pesos se informan como priority_weight, sin inventar otro scoring o ranking.

El archivo de catálogo se vuelve a leer sin caché de la tool. Los settings efectivos
corresponden a la instancia del backend/CLI; cambios de variables de entorno requieren
recrear esa instancia, como sucede en el resto de Eureka.

## Política y comprobación local

Para preguntas de investigación/priorización, la primera function call solicitada
es el perfil comercial. Luego se obtiene la corrida y se consultan alertas nuevas
y candidatos según corresponda. Las peticiones solo de resumen conservan la lectura
ligera de get_latest_cdp_run.

La política exige relevancia comercial antes que monto absoluto, respetar deadline,
evidencia y complejidad. No contiene valores concretos de regiones/categorías/topes;
esa información se obtiene de la sexta tool.

Antes de recomendar concretamente 1–3 casos pide detalle de cada uno y evidencia
cuando hay incertidumbre documental. La comprobación de respaldo del runtime busca
los códigos/identidades de casos mencionados en la respuesta y exige las lecturas
correspondientes. No consulta automáticamente todos los candidatos ni implementa un
segundo scoring. Detalle ausente o evidencia vacía no autorizan inventar información.
La comprobación por menciones es conservadora, no un verificador semántico infalible
del lenguaje generado; la fidelidad de una nueva respuesta real sigue pendiente.

Se mantienen 12 calls, 13 turnos, presupuesto temporal y hasta dos recordatorios
para respuestas prematuras. No hay frontend, escrituras DB ni herramientas nuevas
de adquisición, OCR o Web Search.

## Foundry y validación

Versión remota creada/verificada: **8**, basada en la versión actual **7**, mismo
modelo `gpt-4.1-mini-eureka`. Se preservó el contenido base de instrucciones,
actualizando la sección delimitada de investigación. No había valores comerciales
fijos en las instrucciones base. Las versiones anteriores quedan intactas.

Tools almacenadas:

1. get_latest_cdp_run
2. get_eureka_commercial_profile
3. get_run_alerts
4. get_run_review_candidates
5. get_process_detail
6. get_process_evidence

SHA-256 de instrucciones:
`10152f6b4f3240e0ae0f875418a8af05f5183b1a1b81147c20e5ce2d6e5bdd4d`.

**56 tests del agente y 346 tests afectados pasan**, Ruff/formato/mypy y los 13
contratos de importación pasan. Casos cubiertos: cambios del catálogo, settings
distintos de defaults, monto preferido no excluyente, perfil primero, schema sin
parámetros, detalle obligatorio de casos mencionados y evidencia condicional.

No se ejecutó otra pregunta real ni se crearon conversaciones/respuestas en este
cambio. Solo se registró/verificó la versión del agente y se leyó configuración local.

Evidencia sanitizada:
`backend/.local/audits/foundry-commercial-profile/updated-version.json`,
`tool-schemas.json`, `profile-example.json`.

Comando para una futura prueba autorizada, desde backend:

```powershell
.\.venv\Scripts\python.exe scripts/eureka_foundry_spike.py --agent-version 8 "Revisa la última corrida CDP y dime si viste algo interesante para mí."
```
