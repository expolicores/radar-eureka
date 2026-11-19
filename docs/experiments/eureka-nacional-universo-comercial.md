# Universo comercial nacional de EN-01

**Estado.** Perfil experimental versionado y comprobado con fixtures. La corrida real
y la validación de cobertura del perfil CDP quedan pendientes de autorización.
La población de interés son bienes físicos que pueden abastecerse mediante terceros.

## Configuración regional recuperada

| Componente | Configuración y punto de aplicación |
|---|---|
| Radar regional | `backend/config/eureka_radar.v1.json` contiene categorías, términos, frases, marcas, alias, exclusiones y códigos UNSPSC. `backend/src/public_procurement/eureka/domain/radar.py` aplica las reglas locales a metadatos de título, descripción, código, departamento, fecha y fase. |
| Categorías Radar | Refrigerios y bebidas, papelería, tecnología básica, aseo y cafetería, impresión y personalización, mobiliario, refrigerios preparados, ferretería y una familia adicional de eventos solo para discovery. Se recuperaron ejemplos como TV, laptop, tóner, materiales de ferretería y equivalencias singular/plural. |
| Alcance y fases Radar | El default versionado en `shared/config.py` es Boyacá y Casanare. `docs/validacion-regiones-eureka.md` describe Bogotá como prueba temporal. Las fases preferidas son presentación de oferta y manifestación de interés. No se encontró una lista remota de modalidades en ese plan. El alcance operativo de un despliegue no se deduce del default. |
| Búsquedas CDP versionadas | `backend/scripts/licitaciones_search_plan.v1.json` contiene seis búsquedas por combinación de Boyacá y Casanare con refrigerio, papelería y aseo. El vocabulario también declara cafetería, televisor, tecnología, camiseta, impresos y ferretería. El filtro regional usa `query.Objeto` y `query.ubicacion_filter`. El plan usa el identificador de perfil ya autorizado en el adapter. |
| Validación local CDP | Contrasta departamento y objeto, separa fuentes, deduplica, aplica frescura de siete días y calcula vigencia por `FechaVencimiento` en Bogotá. Los códigos previstos se registran como intención `pending_remote_mapping`. |
| Alertas, notificaciones y búsquedas guardadas | La configuración versionada expone modos `disabled`, `file` y `resend`, destinatarios y automatización de Regional. El plan regional versionado y el identificador CDP son los perfiles de búsqueda localizables en este alcance. Los ajustes y búsquedas guardadas dentro de una cuenta del portal, destinatarios efectivos y preferencias privadas requieren revisión autenticada por el propietario. |

Los códigos regionales reutilizados incluyen papel `14111507`, portátil
`43211503`, impresora láser `43212105`, videoproyector `45111616`,
televisor `52161505`, limpieza `47131800`, camisetas `53103000` y sillas
`56101504`. El perfil también conserva `40141700` de Ferretería como una
clase regional pertinente del segmento 40. Refrigerios y servicios de impresión
o de eventos permanecen fuera de la matriz inicial.

- [Configuración de Radar](../../backend/config/eureka_radar.v1.json)
- [Plan regional CDP](../../backend/scripts/licitaciones_search_plan.v1.json)
- [Operación CDP y alertas regionales](../licitaciones-cdp-operacion.md)
- [Validación regional](../validacion-regiones-eureka.md)
- [Notificaciones](../fase-4.4-notifications.md)

## Capacidad del proveedor y alcance de la verificación

| Función | Evidencia y uso en EN-01 |
|---|---|
| Objeto y ubicación | El plan de CDP documenta las claves `Objeto` y `ubicacion_filter` y la comprobación local de ambos valores. El perfil nacional reutiliza ese contrato y envía en `query.ubicacion_filter` los 1.130 identificadores capturados, juntos en cada página. La pertinencia comercial se determina localmente. |
| Consulta y orden | Se reutiliza `POST /cliente/contratos/get-info/MP?perfiles=…`, con `FechaPublicacion` descendente y límite de 30. El preflight y un sondeo sin filtros ya forman parte del contrato existente. Un feed de perfil puede conservar restricciones propias configuradas por el proveedor. |
| Paginación | El payload contiene `page`, `limit` y orden. El repo documenta el cambio de página de la UI y el plan regional automatizado usa página 1. EN-01 comprueba offline paginación acotada, página repetida, fin informado, exceso de filas y pérdida de sesión. Queda por observar en el smoke la respuesta a la lista completa y a páginas mayores que 1 bajo el perfil activo. |
| UNSPSC | `UNSPSC` aparece en los campos de proceso contemplados. El repo deja pendiente la clave de filtro remoto y la codificación de su argumento. El perfil solo interpreta metadatos recibidos como códigos completos de ocho dígitos en texto, entero, lista o texto delimitado. La CLI cuenta las formas y los valores interpretables sin volcar las respuestas. La forma real y disponibilidad del campo por fuente quedan por verificar. Una columna declarada como `actividad_filter` no demuestra que sea un filtro soportado. |
| Modalidad, descripción, estado y fechas | `modalidad_filter`, `estado_agrupado` y `FechaPublicacion` aparecen como columnas, pero no hay verificación de filtros remotos por esos campos dentro del plan regional vigente. EN-01 califica localmente objeto y descripción cuando existe, `FechaPublicacion`, plazo, estado terminal explícito y modalidad textual. Si modalidad o descripción no llegan, se registra la ausencia y se usa la evidencia disponible. |
| Inventario | El endpoint documental existente conserva el límite de 10 páginas por proceso, interpreta la tabla de la respuesta y corta ante páginas repetidas o respuestas inválidas. |

No se abrió una sesión ni se consultó el portal para esta entrega. La verificación
de campos y páginas distingue el contrato observado en el repositorio, las
pruebas offline y lo que se medirá al autorizar el smoke.

- [Contrato y observación CDP](../spike-licitaciones-cdp.md)
- [Pruebas y salida del spike](eureka-nacional-experience-spike.md)

## Matriz UNSPSC nacional

Verificación contra el CSV oficial de Colombia Compra Eficiente, versión
`UNv260801`, publicada con fecha de versión 18 de marzo de 2025. Se compararon
los códigos y sus niveles contra filas de esa versión. El ZIP descargado tuvo SHA-256
`890fc7ed41e6acef904fed64811b270a99d0ad73818c211bbb511757d8b018eb`.
La matriz operativa contiene nombres, familias, clases, productos, keywords,
sinónimos, exclusiones y justificación. Los segmentos y familias son el contexto
de las clases y productos elegidos. Las clases admitidas y productos específicos
son los que activan una coincidencia por código. Una clase de contexto solo
contribuye con términos de producto. Ningún segmento ni familia por sí solo abre
el funnel.

Los drones civiles admitidos por código de producto son `25132101` agrícola,
`25132103` recreativo y `25132105` de reparto. La clase `25132100` requiere
evidencia textual de producto compatible. Se validaron y excluyeron códigos de
uso militar, policial o reconocimiento ajenos al alcance civil. La robótica
educativa usa el producto `60106214`. La prioridad B conserva la necesidad de
validar abastecimiento, garantía y especificaciones antes de cualquier oferta.

- [Versión implementada del clasificador](https://www.colombiacompra.gov.co/archivos/glosario/clasificador-de-bienes-y-servicios)
- [Catálogo oficial descargado](https://www.colombiacompra.gov.co/wp-content/uploads/2025/05/codigos-UNSPSC.zip)
- [Configuración nacional ejecutable](../../backend/config/eureka_nacional_commercial.v1.json)

| Prioridad | Categoría | Familias | Clases habilitadas | Productos | Clases de contexto |
|---|---|---|---|---|---|
| A | Tecnología, informática y periféricos | `43210000` | `43211500`, `43211600`, `43211700`, `43212100` | `43211503`, `43212105` | — |
| A | Electrónica y audiovisuales | `45110000`, `52160000` | `45111600`, `45111700`, `52161500` | `45111616`, `52161505` | — |
| A | Papelería y suministros de oficina | `14110000`, `44100000`, `44120000` | `14111500`, `44121600`, `44121700`, `44122000`, `44122100`, `44103100` | `14111507`, `14111519`, `44122018` | — |
| A | Ferretería y herramientas | `27110000`, `31160000`, `31210000`, `40140000` | `27111700`, `27112700`, `27113200`, `31161500`, `31211500`, `40141700` | — | — |
| A | Material educativo, didáctico y escolar | `60100000`, `60120000`, `60140000` | `60101000`, `60101100`, `60101300`, `60121500`, `60141300` | — | — |
| A | Robótica educativa | `60100000` | — | `60106214` | `60106200` |
| A | Aseo y limpieza | `14110000`, `47130000` | `47131500`, `47131600`, `47131700`, `47131800` | `14111705` | — |
| A | Dotación personal, uniformes y protección personal | `46180000`, `53100000` | `53102700`, `53103000`, `46181600`, `46181800`, `46181900`, `46182000` | `46181504`, `46181701` | — |
| A | Implementos deportivos | `49160000`, `49220000` | `49161500`, `49161600`, `49161700`, `49221500` | — | — |
| B | Drones comerciales civiles | `25130000` | — | `25132101`, `25132103`, `25132105` | `25132100` |
| B | Mobiliario institucional | `56100000`, `56120000` | `56101700`, `56121700` | `56101504` | `56101500` |
| B | Electrodomésticos | `52140000` | `52141500`, `52141600` | — | — |
| B | Iluminación y suministros eléctricos | `26120000`, `39110000`, `39120000` | `26121600`, `39111500`, `39111600`, `39121400`, `39121700` | — | — |
| B | Videovigilancia | `46170000` | — | `46171610` | `46171600` |
| B | Instrumentos musicales | `60130000` | `60131000`, `60131300`, `60131400` | — | — |
| B | Instrumentación y equipos de medición | `41110000` | `41111500`, `41111600`, `41112200`, `41113600` | — | — |
| B | Utensilios y pequeños equipos gastronómicos | `48100000`, `52150000` | `48101800`, `52151600`, `52151700`, `52152000` | — | — |
| B | Equipos de comunicaciones | `43190000` | `43191500`, `43191600` | — | — |
| B | Repuestos automotrices seleccionados | `25170000` | `25171500`, `25172500` | — | — |
| B | Dotaciones institucionales | `52120000`, `55120000` | `52121500`, `52121700`, `55121700` | — | — |
| B | Empaques y almacenamiento | `24110000`, `24120000` | `24112000`, `24112400`, `24121500` | — | — |

## Funnel y métricas del smoke

1. Obtener una muestra exploratoria del feed nacional del perfil. Conservar
   conteos por página, referencia y motivos, con ventana local de 30 días
   por `FechaPublicacion` en Bogotá.
2. Aplicar evidencia de UNSPSC y texto de forma independiente. Cuando el código
   falte o sea genérico, una frase comercial con evidencia de bien físico puede
   habilitar el candidato. Un servicio principal o compra claramente excluida
   se retira antes del inventario. El suministro con instalación accesoria,
   el detergente para un servicio de aseo y los repuestos para vehículos pueden
   entrar si el bien físico sigue siendo el objeto principal.
3. Deduplicar por identidad SECOP exacta y, de forma subsidiaria, por referencia
   estable del proveedor. Registrar el solapamiento si un mismo proceso coincide
   en varias categorías. Asignar una sola categoría principal para candidatos,
   métricas de resultados y costo. La asignación prioriza A y, dentro de la
   prioridad, la evidencia por ambos métodos. Las coincidencias de discovery
   pueden aparecer en varias categorías. No hay búsquedas independientes por
   categoría en el smoke.
4. Priorizar vigentes, luego estado desconocido y luego históricos. Dentro del
   estado, dar prioridad a mínima cuantía y después a A sobre B. Distribuir
   turnos entre departamentos dentro de cada nivel. La modalidad y la vigencia
   ordenan la muestra, sin inferir experiencia ni disponibilidad.
5. Inventariar solo candidatos elegibles, procesar documentos habilitantes y
   generar evidencia de experiencia. Contabilizar descubrimientos y
   coincidencias por código, palabras o ambos, candidatos por familia
   comercial y familia UNSPSC observada, proporciones resueltas y sin
   experiencia, y candidatos abiertos. Guardar una muestra de hasta dos
   exclusiones por motivo para revisión humana. Medir costo aproximado como
   tiempo, créditos de red, descargas y OCR por categoría. El costo monetario
   queda sin estimar mientras falten tarifas verificadas.

El smoke conserva los límites de **5 procesos, 4 páginas de 30 filas, 5
descargas, 12 páginas por PDF, 2 páginas OCR por PDF, 60 créditos de red,
360 segundos y 0 llamadas de IA**. Los resultados corresponden al universo
comercial observado bajo esos límites. El informe de EN-01 contiene el comando y
el aislamiento de sesión y artefactos. [Comando del smoke](eureka-nacional-experience-spike.md#smoke-test-preparado)
