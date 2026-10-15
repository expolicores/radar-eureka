# Regiones temporales para validar el funnel

Diagnóstico de solo lectura al **14 de octubre de 2026, 23:54–23:57 America/Bogota**.
Dataset oficial `p6dx-8zbt`, campo de región utilizado por Radar: `departamento_entidad`.

Valor exacto observado: **`Distrito Capital de Bogotá`**. “Bogotá D.C.” es la etiqueta
de la región solicitada; no se usa ese texto como literal del filtro SECOP.

## Configuración temporal

Se modificó únicamente EUREKA_RADAR_REGIONS en backend/.env, ignorado por Git:

```dotenv
EUREKA_RADAR_REGIONS="Boyacá,Casanare,Distrito Capital de Bogotá"
```

Clasificación documental:

```json
{
  "normal_commercial_scope": ["Boyacá", "Casanare"],
  "validation_region": "Distrito Capital de Bogotá",
  "validation_region_label": "Bogotá D.C.",
  "decision": "temporary_validation_only"
}
```

Bogotá se añade para validar volumen/funnel; su permanencia en el alcance comercial
normal queda pendiente. No se añadieron aliases, normalizaciones ni reglas para
interpretar variantes de su nombre. Se utiliza el valor exacto del dataset.

No se cambiaron defaults de regiones en código/.env.example, fecha inicial, scoring,
UNSPSC, términos, aliases, exclusiones, presupuesto, catálogo, Eureka o reglas de alertas.
Se verificaron hashes de los archivos de consulta, lógica comercial y configuración.
Se recargó el backend sin corrida activa para que el botón use la nueva configuración.
La fábrica API carga efectivamente las tres regiones; notifications sigue disabled.

## Diagnóstico progresivo

Ventana congelada para todas las consultas:
`2026-10-13 <= fecha_de_publicacion_del < 2026-10-15`.
El 15 es límite exclusivo. No se consultó el día 15 ni se cambió la fecha inicial.

| Etapa | Registros |
| --- | ---: |
| A. Fecha solamente | 5 |
| B. Fecha + Boyacá | 0 |
| C. Fecha + Casanare | 0 |
| D. Fecha + Distrito Capital de Bogotá | 0 |
| E. Fecha + Boyacá/Casanare/Bogotá | 0 |
| F. E + estado: no existe filtro remoto de estado | 0 |
| G. F + fase: no existe filtro remoto de fase | 0 |
| H. G + otros filtros remotos: ninguno adicional | 0 |

Se ejecutó count(*) en cada etapa, sin límite de página que recorte los conteos.
Se capturó el WHERE construido por el adapter actual. Estado y fase se seleccionan
como campos, pero no están en su WHERE; por tanto F/G/H mantienen la misma consulta
regional. Los controles locales de fase/exclusión/afinidad permanecen intactos y no
se ejecutaron para estos conteos. El cursor :id, ORDER BY y LIMIT son paginación.
Radar no agrega filtro remoto de precio, UNSPSC o palabras comerciales.

WHERE regional efectivo:

```sql
lower(departamento_entidad) IN ('boyacá','casanare','distrito capital de bogotá')
AND fecha_de_publicacion_del >= '2026-10-13'
AND fecha_de_publicacion_del < '2026-10-15'
```

## Investigación del cero antes de continuar el funnel

Bogotá también devuelve cero antes de filtros locales. Se contrastó:

- Igualdad exacta del departamento y lower(): ambas devuelven 0 en la ventana.
- Fechas explícitas T00:00:00 frente a literales YYYY-MM-DD: ambas devuelven 5 a nivel nacional.
- Esquema oficial: departamento_entidad=text; fecha_de_publicacion_del=calendar_date.
- Petición de primera página real del adapter, con los campos seleccionados,
  ORDER BY :id y LIMIT=200: devuelve `[]`, consistente con el count regional.
- Igualdad regional sin fechas: reconoce históricamente Boyacá (258.017), Casanare
  (115.267) y Distrito Capital de Bogotá (2.627.840). El literal regional sí coincide.

Últimas fechas disponibles de publicación y última publicación, para las tres regiones:
**2026-10-12**, anteriores al inicio 2026-10-13. El máximo nacional es 2026-10-13.
Metadatos del dataset: rowsUpdatedAt=2026-10-14T16:36:31-05:00.

Los cinco registros de la ventana nacional corresponden a:

| ID SECOP | Departamento |
| --- | --- |
| CO1.REQ.11194040 | Magdalena |
| CO1.REQ.11194138 | Magdalena |
| CO1.REQ.11194035 | Magdalena |
| CO1.REQ.11195860 | Guainía |
| CO1.REQ.11194917 | Valle del Cauca |

Conclusión acotada a las respuestas observadas: no se detectó defecto de construcción
en estos predicados; el cero ocurre en la intersección fecha/región de la fuente.
No es causado por el catálogo, scoring o filtros comerciales locales. Añadir Bogotá
no aporta volumen en esta ventana. **No se continuó el funnel ni se inició un ciclo.**

## Evidencia reproducible

Agregados oficiales consultados:

- [Departamentos y valores exactos](https://www.datos.gov.co/resource/p6dx-8zbt.json?%24select=departamento_entidad%2Ccount%28%2A%29+AS+registros&%24group=departamento_entidad&%24limit=100).
- [Esquema y metadatos oficiales](https://www.datos.gov.co/api/views/p6dx-8zbt.json).

Respuestas crudas, URLs completas y parámetros de cada etapa se conservan en
backend/.local/operations45/region_validation/: discovery.json, progressive.json,
investigation.json, configuration.json y protected_hashes.json. Son archivos de
diagnóstico ignorados por Git; no procesos o alertas persistidos.

Las cifras son una instantánea y pueden variar con nuevas publicaciones/cargas.
Para retirar validation_region basta restaurar únicamente EUREKA_RADAR_REGIONS a
Boyacá,Casanare en .env y recargar el backend cuando no haya ciclo activo.
