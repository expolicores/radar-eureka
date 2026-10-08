# Historia de Usuario

**Como** Analista de Seguimiento Compras Públicas,
**Quiero** que el sistema tenga registradas las compras públicas de televisores (contratos SECOP II y órdenes TVEC) con sus ítems clasificados, cargadas desde una fuente de datos simulada y realista,
**Para** poder explorar, comparar y revisar compras en la demo del MVP Beta con el mismo modelo que usará el producto cuando se conecte a datos.gov.co

## Descripción

Primer *vertical slice* del MVP Beta. Crea el módulo `ingestion` con su modelo persistente (compras, ítems y bitácora de ingesta) y lo alimenta con un **dataset seed ficticio y determinístico** a través del puerto `PublicDataSource`, que en el producto real implementará el adaptador de Socrata (SECOP II / TVEC). La clasificación de cada ítem (televisor incluido, accesorio excluido, servicio excluido o dudoso) la hacen **reglas determinísticas del dominio**, no el seed.

HUs del backlog tomadas como referencia (solo lo indispensable): HU-001/HU-003/HU-004 (carga de contratos y órdenes con entidad y fecha), HU-006 (bitácora de ejecuciones), HU-007 (sin datos personales sensibles), HU-010/HU-011 (clasificación por reglas a nivel de ítem, contratos mixtos).

**Incluye:** módulo `ingestion` (dominio, puerto, adaptador seed, repositorio, servicio), migración del esquema `ingestion`, dataset seed, comando de carga, script de PostgreSQL embebido para desarrollo local.
**No incluye:** API ni pantallas (slices 2 y 3), benchmarks y señales (slice 4), documentos y extracción, conector real de Socrata, carga incremental programada, validaciones de calidad con catálogo de rechazos.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** una base de datos PostgreSQL con las migraciones aplicadas
- **Cuando** se ejecuta la carga desde la fuente seed
- **Entonces** quedan registradas entre 1.000 y 1.500 compras de televisores (contratos SECOP II y órdenes TVEC entre 2023 y 2026) con su entidad, departamento, proveedor, objeto, modalidad, valor, fecha de firma e ítems; cada ítem queda clasificado por las reglas; y la bitácora registra la ejecución con leídos, nuevos, actualizados y fecha de corte

### Escenario 2: Validaciones

- **Dado** un ítem cuya descripción corresponde a un televisor (p. ej. «Televisor Smart TV 65" 4K UHD»), a un accesorio (p. ej. «Soporte de pared para TV 55"–75"»), a un servicio (p. ej. «Mantenimiento de televisores») o a algo ambiguo (p. ej. «Pantalla 4K para gimnasio»)
- **Cuando** las reglas de clasificación lo evalúan
- **Entonces** queda respectivamente como `incluido`, `excluido · accesorio`, `excluido · servicio` o `dudoso`; solo los incluidos cuentan como compra de televisor

### Escenario 3: Casos Extremos

- **Dado** que la carga seed ya se ejecutó
- **Cuando** se ejecuta de nuevo
- **Entonces** no se duplica ninguna compra ni ítem (la identidad es la fuente más su identificador de origen, sin transformar), la bitácora registra una segunda ejecución con 0 nuevos, y los montos se guardan como enteros en COP

### Escenario 4: Datos faltantes como estado explícito

- **Dado** compras del seed donde la fuente no publica el precio unitario, donde el IVA no se puede determinar o donde el precio está en revisión de calidad
- **Cuando** se cargan
- **Entonces** el ítem guarda el estado explícito (`no publicado`, `IVA indeterminado`, `en revisión`) y el precio unitario queda vacío o marcado, nunca con un valor por defecto

### Escenario 5: Privacidad

- **Dado** un contrato cuyo proveedor es una persona natural
- **Cuando** se carga
- **Entonces** el documento de identidad del proveedor no se guarda en ninguna tabla y el proveedor se muestra como «Persona natural — documento no visible»

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (consumidor de los datos en los slices siguientes); el Administrador ejecuta la carga.
- **Permisos requeridos:** ninguno en este slice (sin API).
- **Valor de negocio:** base de datos navegable para la demo y modelo definitivo sobre el que se conectará la ingesta real.

### Reglas de Negocio

- La identidad de una compra es `fuente + identificador de origen`: `id_contrato` en SECOP II e `identificador_de_la_orden` en TVEC, sin transformar.
- Clasificación por reglas del ítem: accesorio (soporte, base, cable, control) y servicio (mantenimiento, instalación, reparación) excluyen aunque mencionen «televisor»; «televisor»/«TV»/«Smart TV» incluyen; «pantalla», «monitor» o «display» sin «televisor» quedan como dudosos.
- Montos en COP como enteros; el valor del contrato es dato de referencia y no se usa como precio unitario.
- Falta de dato = estado explícito: precio unitario `explícito`, `derivado`, `no publicado` o `en revisión`; base de IVA `incluido`, `excluido` o `indeterminado`. Nunca se asume IVA del 19 %.
- Personas naturales: sin documento de identidad almacenado.
- Todos los nombres de entidades, proveedores y municipios del seed son ficticios o están marcados como tales; los departamentos son reales.

### Interfaz

Sin interfaz de usuario. Carga por comando: `uv run python -m public_procurement.entrypoints.cli load-seed`.

### Sistemas Externos

- **SECOP II / TVEC (datos.gov.co):** simulados con el adaptador seed del puerto `PublicDataSource`. Sin red.
- **PostgreSQL:** embebido (`pgserver`) para desarrollo local en este equipo; PostgreSQL 16 en Docker o gestionado en los demás entornos.

### Disparadores

- El Administrador ejecuta la carga desde la fuente seed (se puede relanzar).

### Entidades del Dominio

- Compra (contrato SECOP II u orden TVEC)
- Ítem de compra
- Ejecución de ingesta

### Alcance y Continuidad

- Habilita los slices 2 (API de exploración) y 4 (benchmarks y señales).
- El conector Socrata real reemplaza al adaptador seed sin cambiar el dominio, el servicio ni la persistencia.

### Preview de Interfaz

N/A

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md`, `docs/architecture/coding-standards.md`, `docs/propuesta/06-mockups/mockup-demo-seguimiento-compras-publicas.html`
**Historias relacionadas:** #1 (R0 scaffold). Backlog: HU-001, HU-003, HU-004, HU-006, HU-007, HU-010, HU-011
**Lecciones aprendidas:** el PostgreSQL embebido no trae extensiones contrib (`pg_trgm`, `unaccent`): no se usan en este slice

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
