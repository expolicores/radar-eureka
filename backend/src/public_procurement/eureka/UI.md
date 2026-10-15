# Fase 3C — Eureka HTTP y UI

La fase conecta el read model documental existente con React. No añade migraciones, tablas,
reglas de scoring, IA ni dependencias de producto. Las oportunidades y canonical facts no se
copian ni modifican. El servidor registra el router Eureka y compone `EurekaHttpQueries` con
el mismo `EurekaDetailsService` utilizado por CLI. La metadata SECOP se lee mediante el
adaptador de ingestion; cada módulo conserva el acceso a sus propias tablas.

## Endpoints

- `GET /api/eureka/opportunities`: `{items,total,page,page_size}`; page inicia en 1,
  page_size por defecto 25, máximo 100. Filtros opcionales: priority high/medium/low,
  department (case/acentos), category (código), review_required true/false.
- `GET /api/eureka/opportunities/{opportunity_id}`: `{opportunity,details}`. La cabecera
  contiene metadata de entidad, objeto, municipio/departamento y publicación; details conserva
  las secciones del read model, su calidad y referencias de evidencia.
- `GET /api/eureka/opportunities/{opportunity_id}/evidence?canonical_fact_id=UUID`:
  hechos de soporte, documento/versión, localizadores, texto, confianza y corroboración.
  Se comprueba que el canónico pertenezca a las referencias vigentes de esa oportunidad.

El listado nunca contiene texto documental completo. Las ausencias permanecen NULL, y
un presupuesto canónico en conflicto no se sustituye silenciosamente por el precio de metadata.
Cuando no hay presupuesto canónico, el listado puede mostrar el importe publicado en SECOP.
404 indica oportunidad inexistente o evidencia ajena/no disponible; los parámetros inválidos
usan el formato problem details y código 400 de la beta. Los errores de infraestructura no
se ocultan como lista vacía. No se ejecuta extracción/consolidación desde HTTP.

## Pantallas y componentes

- `/eureka`: listado, filtros y paginación; entidad/objeto, ubicación, presupuesto, score,
  prioridad, categoría, enriquecimiento y revisión pendiente.
- `/eureka/:opportunityId`: resumen, qué se compra, ejecución, pago, requisitos y calidad.
- `EurekaPage` y `EurekaDetailPage`: las dos pantallas.
- `EvidencePanel`: acordeón nativo, con consultas React Query habilitadas solo al expandirse.
  Los textos se renderizan como texto, sin HTML, y conservan saltos de línea. Se muestran
  documento, página/párrafo/tabla/fila/columna/hoja/celda cuando existen.
- `useEureka`: consultas mediante el cliente OpenAPI existente, con caché separada por filtros,
  oportunidad y canónico. `types.ts` centraliza etiquetas y lectura defensiva de campos parciales.

Cada sección relevante dispone de “Ver evidencia”. El presupuesto, UNSPSC, plazos, productos,
ítems, póliza y observaciones mantienen sus referencias. No se descarga ni incrusta el PDF.
Los candidatos conflictivos se pueden expandir en Calidad; campos disputados no se muestran
como ganadores. “No requerida” corresponde a una negación explícita; “No determinada”/“No
determinado” indica ausencia o incertidumbre. La UI no interpreta unknown como No.

Se reutilizan React, TypeScript, Vite, React Query, paginación y estilos de la beta. La navegación
añade Eureka; las rutas de señales/compras/casos continúan iguales. La cinta de datos ficticios
se conserva en la beta y cambia a procesos SECOP al entrar a Eureka, para no etiquetar como
ficticias las entidades y cifras reales. La navegación móvil permanece accesible.

## Arranque y validación

PostgreSQL debe estar disponible en el destino de `backend/.env`. Para Docker local es 55432;
el contenedor existente de esta sesión se reactivó sin crear roles, migrar ni cargar datos.
Las fases anteriores deben haber persistido las oportunidades para que aparezcan en el listado.

```bash
# Terminal backend
cd backend
uv run uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload

# Terminal frontend
cd frontend
npm run dev
# Abrir http://localhost:5173/eureka
```

El OpenAPI se exporta con `backend/scripts/export_openapi.py`, sin conexiones DB. El cliente
se regenera con `npm run generate:api`. El script fija openapi-typescript 7.13.0 y TypeScript
5.9.3 para satisfacer la dependencia par del generador; no cambia la versión del compilador
del frontend ni añade una biblioteca UI. Las herramientas temporales de navegador/generación
se instalaron únicamente en `backend/.local/ui-validation`, ignorado por git.

Se validó el caso **CO1.REQ.11172521** a través de HTTP con transacciones PostgreSQL de solo
lectura, y en Edge headless mediante Vite/proxy/backend reales. Recorrido comprobado: listado
→ detalle → expandir Productos → Estudios Previos Firmados.pdf, página 3, texto de Hit 200 ml.
También se comprobó móvil de 390 px, sin overflow horizontal ni errores JavaScript.

Resultado visible:

- Score **65 → 65**, prioridad alta → alta, estado Consolidado, revisión pendiente de vigencia.
- Jugo Hit 200 ml y Chocorramo tradicional 65 g.
- 400 PACK; unitario 5200 COP, total y presupuesto 2080000 COP; UNSPSC 50192703.
- Ejecución 5 días calendario desde firma; entrega en I.E. San Luis Beltrán, Covarachía.
- Pago único, 100%, 30 días calendario desde aprobación de factura.
- Póliza no requerida; RUP/experiencia y número de entregas no determinados.
- 0 conflictos, 18 canónicos, 39 hechos estructurados; los tres campos ausentes conservados.
- Nota de discovery sobre falta de fecha de cierre, sin afirmar que el proceso siga abierto.

Se compararon todas las columnas de la oportunidad antes/después de las consultas HTTP: iguales,
incluyendo fecha de evaluación y configuración. No se ejecutaron pruebas destructivas contra
desarrollo. Las pruebas de API aíslan sus servicios; las pruebas frontend simulan HTTP y cubren
navegación, datos completos/parciales, requisitos, conflictos, carga, error y evidencia diferida.

## Límites y Fase 4

El listado está orientado al volumen local actual: filtra/proyecta oportunidades usando servicios
existentes, sin join SQL entre módulos ni índice de búsqueda nuevo. Para volumen alto habrá que
optimizar consultas por lotes y paginación antes de añadir más filtros. Los contratos generados
tipan la envoltura HTTP; algunos campos canónicos son JSON flexible y se leen defensivamente.

La API sigue la frontera de acceso local de la beta. La evidencia puede contener datos personales;
una publicación para varios usuarios requerirá políticas de acceso/exposición y auditoría.
No se implementó render de PDF, búsqueda por artículos/marcas, alertas, IA, Foundry, RAG, agentes,
OCR, rentabilidad ni recomendación de participar. La Fase 4 requiere definir su alcance y las
políticas de uso antes de añadir razonamiento o ampliar el producto.

## Archivos

Backend nuevos: `eureka/api.py`, `eureka/UI.md`, `tests/unit/eureka/test_api.py`.
Modificados: `eureka/ports.py`, `repositories.py`, `adapters/ingestion.py`, `services.py` y
`entrypoints/api/app.py` (rutas de módulos relativas a `backend/src/public_procurement/`).

Frontend nuevos, dentro de `frontend/src/features/eureka/`: `types.ts`, `useEureka.ts`,
`EurekaPage.tsx`, `EurekaDetailPage.tsx`, `EvidencePanel.tsx`, `EurekaPage.test.tsx`.
Modificados: `frontend/src/App.tsx`, `app/AppShell.tsx`, `styles.css`, `api/openapi.json`,
`api/schema.ts`, `frontend/package.json` y el README de la raíz.
