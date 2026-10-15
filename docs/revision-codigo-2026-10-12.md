# Revisión del código actual — 12 de octubre de 2026

## Alcance y estado

Revisión estática de los flujos principales del backend y frontend, persistencia, migraciones, configuración local, CI y código auxiliar de la raíz y de `docs/propuesta/03-prd/insumos/`. No se modificó código de producto. No es una auditoría exhaustiva de cada documento o dependencia.

El producto actual es un **MVP Beta con datos simulados**, como indica el README. El backend tiene cinco módulos funcionales: `ingestion`, `market`, `comparison`, `exploration` e `investigation`, además de `shared` y los entrypoints API/CLI. El frontend implementa exploración, señales, fichas y casos. Administración es una pantalla pendiente.

La raíz contiene infraestructura y un experimento real de descarga: `radar_eureka_prueba.py`. Los scripts D1/D4/D6 son investigaciones separadas; no alimentan automáticamente las tablas del producto. `descargas_covarachia/` contiene una respuesta JSON, dos PDF y un DOCX. No encontré `radar_eureka_prueba (1).py` en disco dentro del proyecto, aunque figura como pestaña del IDE.

## Hallazgos por prioridad

### 1. P1 — El arranque documentado apunta al puerto equivocado

**Ubicación:** `docker-compose.yml:11` y `backend/.env.example:4`.

Docker expone PostgreSQL en el puerto del host **55432**, pero el archivo de ejemplo apunta a **5432**. Seguir el README literalmente impide conectar o conecta a otra instancia que ya escuche en 5432. Los builders de pruebas también usan 5432.

**Corrección propuesta:** alinear la URL local con 55432 o restaurar el mapeo de Docker a 5432. El puerto 5432 dentro del contenedor y el de CI pueden permanecer como están.

### 2. P1 — Las pruebas de integración pueden borrar la base de desarrollo

**Ubicación:** `backend/tests/integration/conftest.py:23`, `:38` y `:58`.

Las fixtures cargan la configuración habitual, incluido `.env`, y ejecutan `alembic downgrade base` sin comprobar que la base sea exclusiva de pruebas. Ejecutar `pytest` sin seleccionar marcadores puede borrar compras, señales y casos de la demo. El README advierte del borrado, pero no existe una barrera en el código.

**Corrección propuesta:** exigir una URL de pruebas independiente, validar el destino antes del downgrade y rechazar la base habitual. No ejecuté estas pruebas durante la revisión.

### 3. P1 antes de uso multiusuario — La privacidad anunciada no existe entre visitantes

**Ubicación:** `backend/src/public_procurement/entrypoints/api/app.py:50`, `dependencies.py:17` y `frontend/src/features/cases/CasesPage.tsx:44`.

Todas las peticiones reciben el mismo `DEMO_USER_ID`, incluso con `APP_ENV=production`. Aunque los repositorios filtran correctamente por propietario, todos los visitantes comparten ese propietario. La UI afirma «Tus casos son privados: solo tú puedes verlos».

La ausencia de autenticación es una limitación declarada de la beta, no una funcionalidad olvidada del alcance actual. El problema es la promesa de privacidad y que el modo demo sigue habilitado en producción.

**Corrección propuesta:** identificar claramente los casos como compartidos en la demo y bloquear este proveedor de identidad fuera de los ambientes autorizados; incorporar autenticación y propietario real antes de uso multiusuario.

### 4. P2 — Los códigos de señal cambian entre recálculos

**Ubicación:** `backend/src/public_procurement/comparison/services.py:132` y `frontend/src/features/cases/CaseDetail.tsx:36`.

`assign_signal_codes` añade el número de línea únicamente cuando hay varias señales en la compra. La misma línea cambia de código si otra línea empieza o deja de producir señal. Los casos guardan el código previo y construyen con él el enlace «ver versión actual»; el detalle solo consulta códigos vigentes.

**Reproducción realizada:** una línea genera `SG-2026-0142`; al agregar otra señal, la primera pasa a `SG-2026-0142-1` y la nueva a `SG-2026-0142-3`.

**Corrección propuesta:** usar una identidad estable de compra e ítem, independiente del resultado de otros ítems, y conservar resolución de los enlaces anteriores.

### 5. P2 — Una actualización de ingesta puede romper las consultas de señales

**Ubicación:** `backend/src/public_procurement/ingestion/repositories.py:272` y `backend/src/public_procurement/comparison/services.py:301`, `:438`.

La ingesta elimina los ítems que ya no llegan de la fuente. Las comparaciones anteriores siguen vigentes hasta el siguiente recálculo. Tanto el listado como el detalle de señales buscan la línea con `next(...)` sin alternativa: si la línea fue eliminada, lanzan `StopIteration`, que termina en HTTP 500. Si cambian atributos en vez de eliminarse la línea, se mezclan resultados anteriores con etiquetas o IVA actuales.

**Reproducción realizada:** consultar la etiqueta de una comparación cuya línea ya no está en la compra lanza `StopIteration`.

**Corrección propuesta:** definir la invalidación de resultados al actualizar compras y guardar los atributos necesarios para presentar el resultado calculado sin depender del ítem mutable actual.

### 6. P2 — El borrador de una nota puede pasar a otro caso

**Ubicación:** `frontend/src/features/cases/CasesPage.tsx:60` y `CaseDetail.tsx:58`.

`CaseDetail` conserva `note` y `error` en estado local, y el padre no lo identifica con `key={selected.data.id}`. Al alternar entre casos ya presentes en la caché, React reutiliza el componente. Un borrador escrito en A puede aparecer en B; el envío usa el `data.id` de B.

**Corrección propuesta:** mantener borradores por identificador de caso o reiniciar el componente al cambiar de caso. Agregar una prueba con ambos casos cargados en caché.

### 7. P2 — Guardar el mismo elemento simultáneamente puede devolver 500

**Ubicación:** `backend/src/public_procurement/investigation/repositories.py:93`.

La prevención de duplicados hace primero un conteo y después un INSERT. Dos transacciones pueden observar cero y tratar de insertar el mismo elemento. La restricción única evita duplicarlo, pero la segunda transacción recibe `IntegrityError`, sin traducción al resultado `ALREADY_SAVED`; la API devuelve 500 en vez del 422 previsto. Los botones del frontend tampoco se deshabilitan durante la mutación.

**Corrección propuesta:** insertar con manejo atómico de conflicto y devolver el resultado de negocio correspondiente. Deshabilitar las acciones mientras están pendientes mejora la UX, pero no reemplaza el control del servidor.

### 8. P2 — La ingesta no deduplica registros nuevos dentro de una carga

**Ubicación:** `backend/src/public_procurement/ingestion/repositories.py:244` y `backend/src/public_procurement/market/repositories.py:96`.

El índice `existing` solo contiene lo que había antes de procesar el lote. Si una compra nueva aparece dos veces, se preparan dos INSERT y falla la restricción única, revirtiendo la carga. Mercado tiene el mismo comportamiento para observaciones repetidas dentro del lote. La idempotencia entre ejecuciones no cubre este caso.

**Corrección propuesta:** deduplicar por identidad de origen dentro del lote, definir qué hacer ante duplicados con contenido distinto y usar operaciones atómicas cuando corresponda.

### 9. P2 — El buscador de señales no refleja la navegación atrás/adelante

**Ubicación:** `frontend/src/features/signals/SignalsPage.tsx:83`.

El input usa `defaultValue={filters.q}`. Cuando cambia la URL sin desmontar la página, la consulta sí cambia, pero el texto visible no se sincroniza. Al perder el foco puede volver a escribir el filtro anterior en la URL. El buscador de Explorar ya implementa una sincronización explícita.

**Corrección propuesta:** controlar el valor y sincronizarlo con la URL, conservando el comportamiento elegido de búsqueda por Enter o pérdida de foco.

### 10. P2 — El experimento de descarga puede dejar archivos incompletos con nombre válido

**Ubicación:** `radar_eureka_prueba.py:66`, `:71` y `:75`.

Se escribe directamente sobre el archivo final. Si la conexión falla después de recibir parte del documento, se imprime el error pero queda el PDF/DOCX parcial. Reejecutar también trunca el archivo previo antes de completar la nueva descarga. La lectura de cabecera carga el archivo completo con `read_bytes()`, aunque solo necesita 12 bytes.

**Corrección propuesta:** descargar a un temporal, validar y mover al destino al terminar; leer solo la cabecera y establecer un límite de tamaño. La comprobación de dominio solo cubre la URL inicial y `allow_redirects=True` puede salir de ese dominio, por lo que también conviene validar cada redirección antes de seguirla.

## Observaciones del código auxiliar y de operación

- `docs/propuesta/03-prd/epicas/_consolidar_hus.py:9` usa una ruta absoluta del usuario `juan.sierra`. Además, modifica documentación antes de intentar abrir esa plantilla en la línea 87: en este equipo puede fallar después de realizar cambios parciales. Debe resolver rutas desde el repositorio y validar entradas antes de escribir.
- `docs/propuesta/03-prd/insumos/d1-scripts/d1g.py:3` recorre `docs/*` y trata todo lo que no termina en `.xlsx` como PDF. La carpeta actual contiene directorios y otros archivos; el script ya no corresponde a esa estructura.
- `d4a_muestra_documentos.py:36` silencia fallos de consulta y puede registrar cero documentos cuando la consulta falló. `d4b_perfil_documentos.py:54` descomprime entradas ZIP sin limitar bytes o proporción de expansión. Son scripts de investigación, no adaptadores listos para incorporar al producto.
- El CI verifica backend y frontend, pero no los scripts de la raíz y de los spikes ni la correspondencia automática entre OpenAPI exportado y cliente generado.
- `docs/architecture/index.md` aún dice «todavía no existe código de producto», mientras el README describe la beta implementada. Conviene actualizar ese estado y distinguir claramente arquitectura objetivo e implementación vigente.
- El listado de señales carga y filtra todas las señales en memoria; los casos ejecutan consultas adicionales de conteo por cada caso. Es aceptable para la demo pequeña, pero debe medirse antes de aumentar el volumen.
- No hay conector real de ingesta, procesamiento documental integrado, autenticación, worker/cola ni despliegue completo. Son pendientes declarados del alcance, no errores de compilación.

## Verificación ejecutada

| Comprobación | Resultado |
| --- | --- |
| Backend: pytest sin integración | **152 pasaron**, 58 excluidas por marcador |
| Backend: Ruff | Correcto |
| Backend: mypy | Correcto en 63 archivos fuente |
| Backend: import-linter | 6 contratos cumplidos |
| Frontend: Vitest | **42 pruebas pasaron**, 8 archivos |
| Frontend: ESLint | Correcto |
| Frontend: Prettier check | Correcto |
| Frontend: build TypeScript + Vite | Correcto |
| Reproducción del cambio de código de señal | Confirmado |
| Reproducción de consulta de línea eliminada | Confirmado: `StopIteration` |

Vitest y el build requirieron ejecución aprobada fuera del sandbox para escribir sus archivos temporales. Las pruebas del backend emitieron avisos de deprecación de TestClient/httpx y de permisos de la caché de pytest, sin fallos.

No ejecuté migraciones, pruebas de integración, seeds ni scripts que descargan datos o reescriben documentación. No validé el comportamiento de proveedores externos ni vulnerabilidades publicadas de dependencias. Los hallazgos de concurrencia se obtuvieron por inspección del flujo y de las restricciones; no se reprodujeron contra PostgreSQL.

Prioridad de trabajo sugerida: alinear el arranque y proteger la base de pruebas; corregir identidad y vigencia de señales; corregir notas y guardado concurrente; después integrar el experimento real mediante adaptadores y actualizar la documentación de estado.
