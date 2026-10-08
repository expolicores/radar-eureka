# Historia de Usuario

**Como** Analista,
**Quiero** consultar por API el listado de compras de televisores con búsqueda, filtros, orden y paginación, y la ficha de cada compra,
**Para** que la pantalla «Explorar compras» y, más adelante, los agentes puedan encontrar rápidamente las compras que me interesan

## Descripción

Segundo *vertical slice* del MVP Beta. Expone `/api/v1/purchases` (listado) y `/api/v1/purchases/{id}` (ficha), más `/api/v1/purchases/filters` (opciones de filtro y fecha de corte de los datos). Los datos son del módulo `ingestion` y se consultan **solo por `ingestion.services`**; el módulo `exploration` compone la respuesta y calcula el **estado del análisis** de cada compra. Los servicios de consulta quedan tipados y sin dependencias HTTP para poder exponerse después como herramientas de agentes.

HUs del backlog tomadas como referencia: HU-069 (listado), HU-070 (entidad/proveedor), HU-071 (fechas), HU-072 (territorio), HU-083 (fecha de actualización de los datos).

**No incluye:** pantallas (slice 3), señales y filtro «con señal» (slice 4), autenticación, vistas materializadas.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** las compras cargadas desde el seed
- **Cuando** se consulta `GET /api/v1/purchases` sin filtros
- **Entonces** responde 200 con la primera página (25 por defecto) ordenada por fecha de firma descendente, el total de compras y, por compra: identificador, referencia (`id_contrato` o «Orden N»), fuente, entidad, departamento, proveedor, objeto, valor, fecha de firma y estado del análisis

### Escenario 2: Validaciones

- **Dado** las compras cargadas
- **Cuando** se combinan búsqueda de texto (entidad, proveedor por nombre o NIT, objeto o referencia; sin distinguir mayúsculas ni tildes), fuente, modalidad, departamento, rango de valor (`< $20 M`, `$20 M – $100 M`, `> $100 M`), rango de fechas y orden (fecha o valor)
- **Entonces** solo se devuelven las compras que cumplen todos los criterios y el total corresponde a ese subconjunto; un parámetro inválido (p. ej. `page_size=500` o una fuente desconocida) responde **400** en *problem details* en español

### Escenario 3: Casos Extremos

- **Dado** una búsqueda sin coincidencias o un identificador de compra inexistente
- **Cuando** se consulta el listado o la ficha
- **Entonces** el listado responde 200 con 0 resultados y la ficha responde **404** en *problem details* («Compra no encontrada»)

### Escenario 4: Ficha de la compra

- **Dado** una compra existente
- **Cuando** se consulta `GET /api/v1/purchases/{id}`
- **Entonces** responde con todos sus datos y sus ítems (clasificación, cantidad, precio unitario, estado del precio, base de IVA y atributos del televisor) y la fecha de corte de los datos

### Escenario 5: Estado del análisis

- **Dado** compras con distintos datos
- **Cuando** se calcula su estado del análisis
- **Entonces** es: `excluido` si no tiene ítems de televisor; `en revisión de calidad` si algún televisor tiene precio en revisión; `sin precio unitario` si la fuente no publicó el precio; `IVA indeterminado` si no se puede determinar la base; y `pendiente de comparación` en los demás casos (la comparación llega con el slice de señales)

### Escenario 6: Opciones de filtro y frescura

- **Dado** las compras cargadas
- **Cuando** se consulta `GET /api/v1/purchases/filters`
- **Entonces** devuelve las fuentes, modalidades y departamentos existentes y la fecha de corte más reciente de la ingesta («Datos actualizados al…»)

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (y Administrador).
- **Permisos requeridos:** ninguno en el MVP Beta (la autenticación llega después); los endpoints quedan bajo `/api/v1`.
- **Valor de negocio:** encontrar compras por quién compró, a quién, qué, cuándo y dónde.

### Reglas de Negocio

- El valor del contrato es dato de referencia; el filtro de valor usa el valor total de la compra.
- Las compras sin ítems de televisor se listan, marcadas como excluidas (como en el mockup).
- La búsqueda ignora mayúsculas y tildes.
- Página por defecto 25, máximo 100.
- Estados del análisis en el orden de precedencia del Escenario 5.

### Interfaz

API REST JSON bajo `/api/v1`, errores RFC 9457 en español. Sin UI en este slice.

### Sistemas Externos

Ninguno (datos ya persistidos por el slice 1).

### Disparadores

- El Analista consulta el listado con filtros (relanzable).
- El Analista abre la ficha de una compra.
- La pantalla pide las opciones de filtro.

### Entidades del Dominio

- Compra
- Ítem de compra
- Ejecución de ingesta (fecha de corte)

### Alcance y Continuidad

Habilita el slice 3 (pantalla «Explorar compras») y el 6 (ficha). El slice 4 agrega el estado «con señal» / «comparado sin señal» y el filtro por señal.

### Preview de Interfaz

N/A

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md` (exploración de solo lectura; módulos solo por `services`), `docs/architecture/coding-standards.md`, mockup sección «Explorar».
**Historias relacionadas:** #2 (modelo y seed). Backlog: HU-069, HU-070, HU-071, HU-072, HU-083
**Lecciones aprendidas:** sin `unaccent` en el PostgreSQL embebido: la búsqueda sin tildes usa `translate()`, que es del núcleo

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
