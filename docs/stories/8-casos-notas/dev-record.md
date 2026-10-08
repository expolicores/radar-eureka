## Dev Agent Record — Dev-Rápido

### Debug Log

| # | Tipo | Descripción | Resolución |
|---|------|-------------|------------|
| 1 | Lint | ruff N818: las excepciones deben terminar en `Error` | Renombradas (`CaseNotFoundError`, `ReferenceNotFoundError`, `InvalidCaseDataError`) |
| 2 | API | El título genérico del 409 decía «Conflicto de versión» y los errores de validación del cuerpo hablaban de «parámetro» | Título del 409 «Conflicto»; «campo» para datos del cuerpo JSON y «parámetro» para la URL |
| 3 | Test | El mensaje de nota vacía desaparece al enviar una nota válida; el test que unía ambas conductas fallaba | Separado en dos tests (una conducta por test) |
| 4 | Test | El test del marco usaba «Mis casos» como sección pendiente | Ahora usa «Administración» (sigue pendiente) |

### Completion Notes

- ⚡ Dev-Rápido: módulo `investigation` (esquema `investigation`, migración `0005`): casos privados por dueño (un caso ajeno responde 404), elementos guardados como **instantáneas inmutables** (señal: código, ítem, precio, mediana, desviación, confianza, configuración; compra: referencia, entidad, proveedor, valor, estado) armadas con `comparison.services` y `exploration.services`, notas de solo inserción (1–5.000 caracteres; su texto no se registra en logs), última actividad. API `/api/v1/cases` (listar, crear, abrir, guardar elemento, agregar nota). Usuario de demostración inyectado por la raíz de composición (`app.state.current_user_provider`), reemplazable por `identity`. SPA: «Mis casos» (lista por última actividad, crear caso, instantáneas con enlace a la versión actual, notas) y «★ Guardar en caso» (elegir caso o crear uno) en el detalle de la señal y en la ficha.
- ✅ Verificado: ruff, mypy, **6 contratos** import-linter, `alembic check`; **209 tests de backend (1 omitido)**; **42 de Vitest**; ESLint, Prettier, `tsc`, build. Prueba manual de la API sobre la demo: instantáneas de señal y compra, duplicado, nota, 400 y 404.
- 🧪 Cobertura QA: 10/10 (incluida la privacidad con un segundo dueño y la inmutabilidad de la instantánea tras un recálculo).
- 📝 Decisión autónoma: el proveedor del usuario actual vive en `app.state` y lo lee la API del módulo (no `entrypoints/api/dependencies` desde el módulo, que violaría las capas).

### File List

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| Creado | `backend/src/public_procurement/investigation/**` (7 archivos) | Módulo de casos |
| Creado | `backend/alembic/versions/0005_investigation_schema.py` | Esquema `investigation` |
| Modificado | `backend/src/public_procurement/entrypoints/api/{app,dependencies,errors}.py` | Cableado, usuario demo, títulos y textos de error |
| Modificado | `backend/alembic/env.py`, `backend/pyproject.toml` | Metadata y contratos (capa `investigation`) |
| Creado | `backend/tests/unit/investigation/*`, `backend/tests/integration/test_cases.py` | Tests |
| Creado | `frontend/src/features/cases/*` (4), `frontend/src/components/SaveToCaseButton{,.test}.tsx` | Pantallas y botón |
| Modificado | `frontend/src/{App.tsx,App.test.tsx,styles.css,api/client.ts,test/api.ts}`, `frontend/src/features/{signal-detail/SignalDetailPage,purchase/PurchaseDetailPage}.tsx`, `frontend/src/api/{openapi.json,schema.ts}` | Rutas, estilos, tipos, simulador de API con método y cuerpo, botón integrado |
| Modificado | `README.md` | Estado del MVP Beta, recorrido de la demo y cómo reiniciarla |

### Revisión del diff

Herramienta: propia + revisor de estándares independiente — el revisor descartó por dudosas las validaciones locales de título y nota en la SPA (ayuda de interfaz; la regla la impone el backend).

| # | Categoría | Hallazgo | Archivo | Resultado |
|---|-----------|----------|---------|-----------|
| 1 | estandares | La regla «sin duplicados» se modelaba como excepción, no como estado del dominio | `backend/src/public_procurement/investigation/domain/case.py` | ✅ Aplicado (`SaveResult`) |
| 2 | estandares | El repositorio comunicaba el duplicado lanzando una excepción | `backend/src/public_procurement/investigation/repositories.py` | ✅ Aplicado (devuelve `SaveResult`) |
| 3 | estandares | El duplicado respondía 409 (reservado a conflicto de versión) en lugar de 422 (regla de negocio) | `backend/src/public_procurement/investigation/api.py` | ✅ Aplicado (422; SPA y tests ajustados) |

Revisar primero: `backend/src/public_procurement/investigation/api.py` (escrituras y usuario actual) · `backend/alembic/versions/0005_investigation_schema.py` (migración)

### Métricas Dev-Rápido

- Tiempo sesión IA: 15 min
- Tareas manuales DoD: 0 min
- Tiempo total: 15 min
