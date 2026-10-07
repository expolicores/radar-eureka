# Asunciones Parciales — ÉPICA-004: Referencias de Mercado Trazables

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo (PO) | **Total de asunciones:** 30

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| El registro mínimo "marca/modelo" exige ambos campos; una observación sin modelo identificable no se guarda (en captura: descarte `modelo_no_identificable`) | Datos | HU-042, HU-050, HU-051, HU-052 | Alto | Resuelta |
| La condición de IVA nunca se infiere: si la fuente no la declara es `indeterminado`; el IVA por defecto de captura por fuente es configurable con valor inicial `indeterminado` hasta que el PO documente la verificación | Datos | HU-042, HU-047, HU-050, HU-051, HU-052 | Alto | Resuelta |
| Catálogo de fuentes: Alkosto y Falabella con carga manual habilitada; Éxito y Mercado Libre registrados sin carga manual y sin captura automática; nombres de fuentes públicas (SECOP, TVEC) reservados | Negocio | HU-042, HU-044 | Medio | Resuelta |
| Límites de formato del registro mínimo (longitudes, precio entero 1–999.999.999 COP, tamaño 10–120", enumeraciones de resolución y tecnología, solo COP) | Datos | HU-042, HU-047, HU-049 | Medio | Resuelta |
| `apta_para_referencia` como campo derivado: solo vigente y sin condición especial | Negocio | HU-042, HU-043, HU-046 | Alto | Resuelta |
| La carga semiautomática (archivo) se identifica como método `manual` con `canal_carga = archivo` | Negocio | HU-042, HU-049 | Medio | Resuelta |
| Inmutabilidad implementada como solo inserción: corrección = anulación con motivo + nueva observación vinculada; anulación irreversible | Datos | HU-043 | Alto | Resuelta |
| Dentro de un mismo contexto (ejecución, búsqueda o lote) no se crean dos observaciones con la misma URL; entre contextos siempre se crea una nueva | Datos | HU-043, HU-048, HU-049, HU-050 | Medio | Resuelta |
| Las observaciones no tienen purga ni expiración en el MVP | Datos | HU-043 | Bajo | Resuelta |
| La consulta directa del histórico es solo para el Administrador; el Analista ve observaciones a través de la evidencia de las señales | Seguridad | HU-043 | Bajo | Resuelta |
| "Descartar" un vendedor tercero significa no guardarlo como observación; en captura se registra solo como descarte de la ejecución | Negocio | HU-044, HU-050, HU-052 | Medio | Resuelta |
| Vendedor implícito por fuente cuando no se publica (Alkosto sí, según D6; Falabella, Éxito y Mercado Libre no) | Integraciones | HU-044, HU-051, HU-052 | Medio | Resuelta |
| Coincidencia de vendedor exacta tras normalizar espacios, mayúsculas y tildes; sin coincidencia aproximada | Negocio | HU-044 | Medio | Resuelta |
| Con varios precios generales vigentes, el efectivo es el menor y el mayor queda como precio anterior | Negocio | HU-045, HU-052 | Medio | Resuelta |
| Precio anterior menor o igual al efectivo: rechazo en canales manuales; se omite con advertencia en captura | Datos | HU-045, HU-047, HU-049 | Bajo | Resuelta |
| El precio efectivo corresponde a una unidad, sin envío, instalación ni combos; los canales manuales exigen declararlo | Negocio | HU-045, HU-047, HU-048, HU-049 | Medio | Resuelta |
| Precios con centavos se redondean al peso con advertencia | Datos | HU-045 | Bajo | Resuelta |
| Las observaciones con condición especial se guardan como evidencia, pero no son aptas; con varias condiciones se marca `otra` | Negocio | HU-046, HU-052 | Alto | Resuelta |
| Detección de condiciones por mapeo del conector y palabras clave configurables evaluadas solo sobre el rótulo del precio | Integraciones | HU-046, HU-052 | Medio | Resuelta |
| Antigüedad máxima de una observación manual: 7 días (configurable), para no convertir la carga manual en fuente de precios históricos externos | Negocio | HU-047, HU-048, HU-049 | Alto | Resuelta |
| Evidencias manuales: PNG, JPG o PDF; 1 a 5 archivos de máximo 10 MB (configurables); verificación del tipo real del contenido | Técnico | HU-047, HU-048, HU-049 | Medio | Resuelta |
| Protección ante doble envío de 10 minutos en carga individual y búsqueda; rechazo de paquete CSV con el mismo hash | Técnico | HU-047, HU-048, HU-049 | Bajo | Resuelta |
| Búsqueda manual atómica, con evidencia de la página de resultados, declaración de completitud, ofertas descartadas con motivo y registro de búsquedas sin ofertas | Negocio | HU-048, HU-049 | Alto | Resuelta |
| Carga CSV en paquete .zip con evidencias; UTF-8, coma, RFC 4180, máx. 1.000 filas y 100 MB; aceptación parcial por fila, grupos de búsqueda todo o nada; procesamiento asíncrono desde 30 s | Técnico | HU-049 | Medio | Resuelta |
| Habilitación de la captura en producción exige registrar la revisión de términos de uso; en entornos de validación no; la captura contra fuentes reales exige la suspensión automática implementada | Seguridad | HU-050, HU-053 | Alto | Resuelta |
| Criterio conservador de `robots.txt`: si no se puede leer, no se hacen más solicitudes; `Crawl-delay` mayor prevalece; programación inicial lunes 02:00 hora de Colombia | Integraciones | HU-050 | Medio | Resuelta |
| Filtros de televisor individual por términos de exclusión configurables, descarte de productos agotados y ejecución fallida si > 50 % de páginas con error o sin datos estructurados | Integraciones | HU-050, HU-051, HU-052 | Medio | Resuelta |
| El patrón de URL de televisores de cada conector es un parámetro obligatorio que el Administrador registra al habilitarlo (D6 no documentó el patrón) | Integraciones | HU-051, HU-052 | Medio | Resuelta |
| Falabella: reutilización de sitemaps por `lastmod`, el SKU interno no se usa como EAN y el precio CMR es condición `tarjeta_especifica` | Integraciones | HU-052 | Medio | Resuelta |
| Suspensión ante un solo 403/429, marcadores de CAPTCHA y patrones de login configurables; notificación por correo (≤ 1 h, reintentos cada 15 min) y reactivación manual con nota, sin ejecución inmediata | Seguridad | HU-053 | Alto | Resuelta |
