# Historia de Usuario

**Como** Analista,
**Quiero** guardar señales y compras en mis casos de investigación como instantáneas y anotar lo que voy encontrando,
**Para** continuar la investigación otro día con la evidencia tal como la vi, aunque los benchmarks se recalculen

## Descripción

Séptimo *vertical slice* del MVP Beta: cierra el flujo de la demo *explorar → detectar señal → revisar comparación → guardar caso → continuar investigación*. Crea el módulo `investigation` (esquema propio) con casos privados del dueño, elementos guardados como **instantánea inmutable** y notas de solo inserción, y la pantalla «Mis casos» del mockup, más el botón «★ Guardar en caso» en el detalle de la señal y en la ficha de la compra.

Como el MVP Beta todavía **no tiene autenticación**, el dueño de los casos es el **usuario de demostración** («Analista demo») que entrega una dependencia de la API, reemplazable por la sesión real del módulo `identity` sin cambiar los servicios: el servicio y el repositorio ya filtran por dueño y responden 404 a casos ajenos.

HUs del backlog tomadas como referencia: HU-090/091 (crear caso desde una señal o una compra), HU-092 (guardar elementos), HU-093 (notas), HU-095 (mis casos), HU-096 (instantáneas), HU-097 (privacidad por dueño, preparada).

**No incluye:** editar o borrar notas (HU-094), autenticación ni roles, compartir casos, exportar.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** una señal o una compra abierta
- **Cuando** el Analista pulsa «★ Guardar en caso» y elige un caso existente o crea uno nuevo con título
- **Entonces** el elemento queda en el caso como **instantánea** con fecha (señal: código, ítem, precio, mediana, desviación, confianza y configuración; compra: referencia, entidad, proveedor y valor), se confirma «Guardado en el caso «…»» y el caso aparece en «Mis casos» con su número de elementos y notas y su última actividad

### Escenario 2: Validaciones

- **Dado** un caso
- **Cuando** el Analista crea un caso sin título o con más de 120 caracteres, agrega una nota vacía o de más de 5.000 caracteres, o guarda un elemento que ya está en el caso
- **Entonces** recibe un error en español (400 para datos inválidos; 422 «Ese elemento ya está guardado en el caso») y no se guarda nada

### Escenario 3: Casos Extremos

- **Dado** un caso de otro usuario, una señal inexistente o una compra inexistente
- **Cuando** el Analista intenta abrirlo o guardarla
- **Entonces** la respuesta es 404 (los casos ajenos no se distinguen de los inexistentes)

### Escenario 4: Instantáneas y notas

- **Dado** un elemento guardado y luego un recálculo que cambia la señal
- **Cuando** el Analista abre el caso
- **Entonces** ve la instantánea tal como la guardó (nunca se modifica), con enlace a la versión actual; las notas se muestran en orden cronológico con su fecha y no se editan ni se borran en este slice

### Escenario 5: Mis casos

- **Dado** varios casos
- **Cuando** el Analista abre «Mis casos»
- **Entonces** ve la lista ordenada por última actividad, puede crear un caso nuevo y al elegir uno ve sus elementos y notas, y puede agregar notas; la pantalla recuerda que los casos son privados

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (usuario de demostración mientras no haya autenticación).
- **Permisos requeridos:** dueño del caso.
- **Valor de negocio:** es lo que convierte una señal en una investigación.

### Reglas de Negocio

- Casos privados: solo el dueño los ve; un caso ajeno responde 404 (arquitectura: autorización por propietario).
- Instantáneas inmutables (solo inserción); el mismo elemento no se guarda dos veces en un caso.
- Notas de 1 a 5.000 caracteres, solo inserción en este slice.
- Título del caso de 1 a 120 caracteres.

### Interfaz

- API: `GET/POST /api/v1/cases`, `GET /api/v1/cases/{id}`, `POST /api/v1/cases/{id}/items`, `POST /api/v1/cases/{id}/notes`.
- Pantallas: «Mis casos» (`/casos` y `/casos/:id`) y el botón «★ Guardar en caso» con selector de caso en el detalle y la ficha.

### Sistemas Externos

Ninguno.

### Disparadores

- El Analista guarda una señal o una compra en un caso.
- El Analista crea un caso, abre uno o agrega una nota.

### Entidades del Dominio

- Caso de investigación
- Elemento guardado (instantánea)
- Nota

### Alcance y Continuidad

Cuando exista `identity`, la dependencia del usuario actual pasa a leer la sesión.

### Preview de Interfaz

Mockup, sección «Mis casos de investigación».

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md` (autorización por propietario, 404 a terceros; instantáneas), estándar §3 (422 para la regla de negocio, 404).
**Historias relacionadas:** #6, #7.

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
