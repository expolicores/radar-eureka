# Capacidad temporal de validación Radar

Verificación de solo lectura del 15/10/2026 sobre `p6dx-8zbt`:

- Ventana: `2026-10-05 <= fecha_de_publicacion_del < 2026-10-16`.
- Regiones: Boyacá y Casanare, sin Bogotá.
- Socrata: 1.872 filas y 1.850 valores distintos de `id_del_proceso`.
- Adapter: 1.872 filas y 1.850 identidades; nueve páginas de 200 y una de 72.
- Configuración local temporal: `EUREKA_RADAR_MAX_PROCESSES=2500`.
- El valor por defecto sigue siendo 100. No se elimina la protección global.
- La paginación existente permite 20.000 filas; no fue modificada.

El botón manual y `run-eureka-cycle` pasan el límite de Settings a Radar. El endpoint
de estado, la UI previa a ejecutar, el preflight y el snapshot de Radar muestran
el límite utilizado. Los procesos ya atendidos siguen rigiéndose por su estado;
no se fuerza su reprocesamiento ni se cambian reglas comerciales.

## Estados de Operations

El CHECK de 0016 no admite `limited` como estado del coordinador. Se conserva ese
contrato sin migración: una corrida cuyo Radar termina `limited` sin error global
se persiste como `completed_with_warnings`, con `radar_status=limited`, cobertura
incompleta y diagnóstico `radar_limited` de severidad warning. No se inventa un
fallo técnico ni se despachan notificaciones desde una cobertura incompleta.
Esos ciclos se excluyen de la consulta de último ciclo satisfactorio.

La UI muestra `Estado: limited` y «Corrida limitada», también para históricos que
guardaron `failed` exclusivamente por el límite. No modifica esos históricos.
Si existe un fallo global o del coordinador, conserva la presentación `failed`.
Los demás resultados se presentan como `completed`, `completed_with_warnings`
o `failed`; los errores por proceso conservan el tratamiento de reintento existente.
El embudo incluye el contador `limit_deferred`.

## Alcance de la comprobación

Se consultó únicamente metadata de SECOP, sin persistencia del funnel. Una prueba
unitaria de capacidad con 1.872 registros sintéticos y colaboradores en memoria
confirma que el límite de 2.500 no produce `limit_deferred`. Los históricos que
ya contienen esa razón se conservan. La confirmación sobre la próxima corrida real
corresponde a la ejecución manual del usuario; no se afirma haberla ejecutado.

El margen cubre el volumen observado, incluso si todos los registros necesitaran
atención. Socrata puede incorporar registros adicionales después del diagnóstico;
el límite finito permanece activo si el volumen llegara a superar 2.500.
