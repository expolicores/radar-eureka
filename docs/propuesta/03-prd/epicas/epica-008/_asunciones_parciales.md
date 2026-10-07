# Asunciones parciales — ÉPICA-008: Operación, Calidad y Medición del MVP

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo (PO) | **Total de asunciones:** 30

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| El catálogo de fuentes separa SECOP II y TVEC en sus datasets operativos (contratos, archivos, ítems, órdenes) más Alkosto y Falabella (6 fuentes) | Datos | HU-098, HU-099 | Medio | Resuelta |
| Se agrega el estado "Retrasada" (sin ejecución dentro de frecuencia + tolerancia configurable, inicial 1 hora) y se alerta | Técnico | HU-098, HU-100 | Medio | Resuelta |
| Los rechazados por validaciones de calidad no degradan el estado de una fuente; solo los errores | Negocio | HU-098 | Bajo | Resuelta |
| Relanzar = ingesta incremental estándar desde la última marca exitosa (o desde 2023-01-01 si no hay), sin rangos libres | Técnico | HU-099 | Medio | Resuelta |
| Retomar una fuente retail suspendida exige una reactivación explícita con motivo y auditoría; relanzar no levanta la suspensión ni reinicia los límites de ritmo y volumen | Seguridad | HU-099 | Alto | Resuelta |
| El canal de alerta es el correo electrónico (1 a 5 destinatarios), con bitácora consultable y aviso de recuperación | Integraciones | HU-100 | Medio | Resuelta |
| Las suspensiones retail se notifican por FR-047 y no se duplican en las alertas de falla | Negocio | HU-100 | Bajo | Resuelta |
| La "muestra suficiente" para la regla de atípicos es un parámetro configurable (`minimo_obs_atipicos`, inicial 5) | Negocio | HU-101 | Medio | Resuelta |
| Los rangos permitidos de cada parámetro son límites de cordura definidos por el PO, no valores analíticos | Negocio | HU-101, HU-102 | Bajo | Resuelta |
| Una sola configuración versionada (instantánea completa, inmutable, con concurrencia optimista) agrupa parámetros analíticos y operativos; sin vigencias futuras ni retroactividad | Técnico | HU-101, HU-102, HU-110 | Alto | Resuelta |
| El umbral de aceptación automática arranca "sin calibrar" y solo admite un valor numérico con referencia de calibración (P-15, D4-4) | Negocio | HU-102 | Alto | Resuelta |
| Las frecuencias se configuran por fuente: horas para públicas (1–168) y días para retail (1–30) | Técnico | HU-102 | Bajo | Resuelta |
| Cambiar términos o parámetros no reclasifica el histórico ni dispara procesos | Técnico | HU-102 | Medio | Resuelta |
| Los precios anormalmente bajos (FR-063) forman parte de la cola de revisión humana como cuarto tipo | Negocio | HU-103 | Medio | Resuelta |
| La cola solo se consulta; la resolución pertenece a los flujos de FR-016 y FR-032; una nueva detección no duplica un pendiente; orden por defecto: más antiguo primero | Negocio | HU-103 | Medio | Resuelta |
| Un contrato marcado aporta precisión y cobertura; un documento marcado solo aporta precisión | Datos | HU-104, HU-106, HU-107 | Medio | Resuelta |
| Un elemento con resultados de validación no puede retirarse de la muestra (evita sesgo de selección) | Negocio | HU-104 | Alto | Resuelta |
| "Diversa" se apoya en la composición visible y advertencias no bloqueantes (concentración > 50 % configurable; ausencia de casos sin precio) | Negocio | HU-104 | Medio | Resuelta |
| La verdad verificada se registra con una plantilla XLSX/CSV de dos hojas (por campo y por contrato) inspirada en la del spike D4; los resultados de D4-4 no se importan automáticamente | Datos | HU-105 | Medio | Resuelta |
| Se agrega el resultado `omitido` (presente y no extraído), que cuenta como error en el denominador; `no_verificable` se excluye; una reextracción deja la fila "requiere revalidar" | Negocio | HU-105, HU-106 | Alto | Resuelta |
| La precisión global es el agregado de los 5 campos críticos y solo "Cumple" si la global y cada campo alcanzan la meta con muestra suficiente | Negocio | HU-106 | Alto | Resuelta |
| La tabla de calibración confianza ↔ corrección (tramos de 0,10) es informativa y no fija el umbral | Negocio | HU-106 | Medio | Resuelta |
| Disponibilidad y cobertura de extracción se calculan sobre la muestra con veredicto manual; end-to-end sobre todo el universo SECOP II; TVEC aparte | Datos | HU-107 | Alto | Resuelta |
| La disponibilidad se reporta sobre candidatos (texto de NFR-CAL-003) y, como complemento, sobre contratos en categoría (comparable con D4) | Negocio | HU-107 | Medio | Resuelta |
| Un contrato cuenta como cubierto si al menos uno de sus ítems de televisor llega al resultado; "comparación utilizable" excluye en la cifra principal las comparaciones incompletas/no confiables (variante informativa aparte) | Negocio | HU-107 | Alto | Resuelta |
| La trazabilidad verifica también la copia conservada del documento y su hash; para TVEC el dato de origen es el registro TVEC; se mide sobre señales y comparaciones vigentes | Datos | HU-108 | Medio | Resuelta |
| El KPI de eficiencia usa el tiempo activo (descuenta pausas > umbral configurable, inicial 30 min); con señales intercaladas cada evento se atribuye a la señal en foco; se mide hasta la primera calificación | Negocio | HU-109, HU-110 | Alto | Resuelta |
| El KPI de señales sustentadas usa la calificación vigente por par Analista–señal y exige al menos 3 analistas distintos; la línea base manual (D2) es un parámetro versionado con fuente obligatoria | Negocio | HU-110 | Alto | Resuelta |
| Los costos de almacenamiento, cómputo y búsqueda se registran manualmente o por CSV desde las facturas, sin conversión de monedas | Datos | HU-111 | Bajo | Resuelta |
| Además de las 4 acciones de FR-094 se auditan las acciones administrativas de la épica; ninguna acción auditable se aplica sin su evento; acciones masivas generan un evento por registro; valores > 4.000 caracteres se truncan con hash y los secretos se enmascaran; consulta por defecto 30 días, máximo 366, exportación ≤ 100.000 eventos | Seguridad | HU-112, HU-113 | Alto | Resuelta |
