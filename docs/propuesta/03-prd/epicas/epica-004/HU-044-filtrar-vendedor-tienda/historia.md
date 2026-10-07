# Historia #044: Aceptar solo observaciones cuyo vendedor sea directamente la tienda

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)  
**Feature:** Aplicar Reglas de Precio de Referencia  
**Prioridad:** Crítica  
**FRs relacionados:** FR-044

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Administrador de la plataforma,  
**Quiero** que el sistema acepte solo observaciones de precio en las que el vendedor sea directamente la tienda seleccionada y descarte las de vendedores terceros del marketplace,  
**Para** que las referencias de mercado no se distorsionen por diferencias de garantía, procedencia, estado, logística o reputación de terceros.

## Descripción

Alkosto vende directamente, pero Falabella (y otras tiendas) mezclan productos propios y de terceros del marketplace (D6). La Adenda 2 (A2.4) decide que en el MVP solo se aceptan observaciones con **vendedor = la tienda**. Esta HU define la regla de aceptación de vendedor que aplican **todos los canales** (carga manual individual, búsqueda manual, carga por archivo y captura automática) antes de guardar una observación en la base propia de mercado.

La regla usa la lista de **nombres de vendedor aceptados** que cada fuente tiene en el catálogo de fuentes de mercado (configuración inicial: Alkosto → "Alkosto"; Falabella → "Falabella"; Éxito → "Éxito"; Mercado Libre → sin nombres configurados) y agrega un parámetro por fuente para el caso en que la fuente no publique el vendedor.

---

## Criterios de Aceptación

### Escenario 1: Aceptar una observación con vendedor = la tienda

- **Dado** que la fuente Falabella tiene como vendedores aceptados ["Falabella"]
- **Cuando** llega una observación de Falabella con `vendedor = " FALABELLA "`
- **Entonces** la observación supera la regla de vendedor, se guarda con `vendedor` tal como se publicó (sin espacios extremos) y con `vendedor_es_tienda = sí`

### Escenario 2: Rechazar una observación manual de un tercero

- **Dado** que el Administrador registra una observación manual de Falabella con `vendedor = "TecnoImport SAS"`
- **Cuando** el sistema aplica la regla de vendedor
- **Entonces** la observación NO se guarda y se devuelve `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: TecnoImport SAS."`

### Escenario 3: Descartar una oferta de tercero en la captura automática

- **Dado** que la captura automática de Falabella lee una página cuyo único vendedor publicado es "ElectroMundo Store"
- **Cuando** el sistema aplica la regla de vendedor
- **Entonces** no se crea ninguna observación y la ejecución de captura registra un descarte con motivo `vendedor_tercero`, el vendedor publicado y la URL; el contador "descartadas por vendedor tercero" de la ejecución aumenta en 1

### Escenario 4: Página con varias ofertas de distintos vendedores

- **Dado** que una página de producto publica dos ofertas: una de "Falabella" a 2.099.900 COP y otra de "ElectroMundo Store" a 1.950.000 COP
- **Cuando** la captura automática aplica la regla de vendedor
- **Entonces** solo se considera la oferta de "Falabella" para la observación; la oferta del tercero se registra como descarte `vendedor_tercero` y su precio no se usa en ningún campo de la observación

### Escenario 5: Fuente sin vendedor publicado y vendedor implícito habilitado

- **Dado** que Alkosto tiene `vendedor_implicito_si_ausente = sí`
- **Cuando** la captura automática lee una página de Alkosto que no publica vendedor
- **Entonces** la observación se guarda con `vendedor = "Alkosto"` (primer nombre de la lista de vendedores aceptados), `vendedor_es_tienda = sí` y `vendedor_origen = implicito`

### Escenario 6: Fuente sin vendedor publicado y vendedor implícito deshabilitado

- **Dado** que Falabella tiene `vendedor_implicito_si_ausente = no`
- **Cuando** la captura automática lee una página de Falabella sin vendedor publicado
- **Entonces** no se crea observación y la ejecución registra un descarte con motivo `vendedor_no_identificable` y la URL

### Escenario 7: Cambio en la lista de vendedores aceptados no es retroactivo

- **Dado** que existen observaciones de Falabella guardadas con `vendedor = "Falabella"`
- **Cuando** el Administrador agrega "falabella.com" a la lista de vendedores aceptados
- **Entonces** el cambio aplica solo a observaciones nuevas, las observaciones existentes no cambian y queda registrado quién y cuándo modificó la lista

### Escenario 8: Fuente sin vendedores aceptados configurados

- **Dado** que Mercado Libre no tiene vendedores aceptados configurados
- **Cuando** llega cualquier observación de Mercado Libre
- **Entonces** se rechaza con `"La fuente Mercado Libre no tiene vendedores aceptados configurados; no se pueden registrar observaciones."`

### Escenario 9: Usuario sin rol Administrador modifica la configuración de vendedores

- **Dado** que un usuario con rol Analista intenta modificar la lista de vendedores aceptados o el vendedor implícito de una fuente
- **Cuando** ejecuta la operación
- **Entonces** se rechaza con `"Operación permitida solo para el rol Administrador."`

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Administrador (configura la regla y carga observaciones manuales); los conectores de captura la aplican automáticamente.
- **Permisos requeridos:** rol Administrador para modificar la configuración de vendedores de una fuente.
- **Valor de negocio:** reduce los falsos positivos de señales causados por referencias retail no comparables.

### Reglas de Negocio

**RN-01 — Regla de vendedor (puerta de entrada).** Antes de guardar cualquier observación, el sistema compara el `vendedor` recibido con la lista `vendedores_aceptados` de la fuente. Se acepta solo si coincide con alguno de los nombres de la lista. Ninguna observación de un vendedor tercero entra en la base de observaciones; por eso toda observación guardada tiene `vendedor_es_tienda = sí`.

**RN-02 — Comparación de nombres.** Ambos textos se comparan después de: quitar espacios al inicio y al final, reducir espacios internos múltiples a uno, ignorar mayúsculas/minúsculas e ignorar tildes y diéresis. No se aplica coincidencia parcial ni aproximada: "Falabella" no coincide con "Falabella Outlet Tercero SAS". Las variantes válidas (ej. "falabella.com") deben agregarse explícitamente a la lista.

**RN-03 — Vendedor ausente.** Parámetro por fuente `vendedor_implicito_si_ausente` (sí/no). Configuración inicial: Alkosto = sí (D6 verificó que el vendedor es la propia tienda); Falabella = no; Éxito = no; Mercado Libre = no. Si el vendedor no viene publicado (nulo o vacío):
- Con `sí`: se asigna el primer nombre de `vendedores_aceptados` y `vendedor_origen = implicito`.
- Con `no`: captura automática → descarte con motivo `vendedor_no_identificable`; canales manuales → el campo `vendedor` es obligatorio y se aplica el error de campo ausente del registro mínimo (`"Campo obligatorio ausente: vendedor."`).
Cuando el vendedor viene publicado, `vendedor_origen = publicado`.

**RN-04 — Varias ofertas en una página.** Si una página o registro de la fuente publica varias ofertas, solo se consideran las de vendedores aceptados. Si ninguna oferta es de un vendedor aceptado, no se crea observación (descarte `vendedor_tercero`). La elección del precio entre varias ofertas de la propia tienda la define la regla de precio efectivo (HU-045).

**RN-05 — Registro de descartes en captura automática.** Cada descarte por vendedor se registra en la ejecución de captura con: `id_ejecucion`, fuente, URL, vendedor publicado (o vacío), motivo (`vendedor_tercero` | `vendedor_no_identificable`) y fecha y hora. Los descartes no son observaciones y no se usan en ningún cálculo. La ejecución expone los contadores "descartadas por vendedor tercero" y "descartadas por vendedor no identificable".

**RN-06 — Rechazo en canales manuales.** En carga manual individual, búsqueda manual y carga por archivo, una observación con vendedor no aceptado se rechaza con `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda {fuente}. Vendedor recibido: {vendedor}."` (en carga por archivo, el mensaje se asocia a la fila y la columna `vendedor`).

**RN-07 — Fuente sin vendedores aceptados.** Si la lista está vacía, toda observación de la fuente se rechaza con `"La fuente {fuente} no tiene vendedores aceptados configurados; no se pueden registrar observaciones."`

**RN-08 — Cambios de configuración.** Solo el Administrador modifica `vendedores_aceptados` (1 a 10 nombres, de 2 a 100 caracteres cada uno, sin duplicados según RN-02) y `vendedor_implicito_si_ausente`. Los cambios no son retroactivos y generan un evento auditable `cambio_catalogo_fuente` con usuario, fecha y hora, valor anterior y valor nuevo. Nombre duplicado en la lista: `"El vendedor {nombre} ya está en la lista de la fuente {fuente}."` Más de 10 nombres: `"La lista de vendedores aceptados admite de 1 a 10 nombres."` Nombre fuera de longitud: `"Cada nombre de vendedor debe tener entre 2 y 100 caracteres."`

### Interfaz

No requiere pantalla propia (nota del Dominio 12 del PRD). La configuración se realiza mediante la operación administrativa del catálogo de fuentes (interfaz mínima, comando o script, a definir en arquitectura). Los mensajes de rechazo se devuelven en la respuesta de la operación de carga correspondiente.

### Sistemas Externos (Si aplica)

Aplica a los datos de vendedor que publican Alkosto y Falabella (campo de vendedor de los datos estructurados de producto, cuando existe) y a los que digita el Administrador.

---

## Contexto y Referencias

**Épica origen:** [Referencias de Mercado Trazables](../../../epicas.md#épica-004-referencias-de-mercado-trazables)

**Exclusiones de la Épica:**
- NO incluye Mercado Libre ni Éxito como fuentes automáticas (Adenda 2); solo carga manual si el Administrador lo decide.
- NO incluye vendedores terceros de marketplace.
- NO incluye fuentes externas de precios históricos (archivos web, sitios de seguimiento).
- NO incluye evasión de CAPTCHA, bloqueos ni autenticación.
- NO incluye alertas de cambio de precio para usuarios.

**Historias relacionadas:** HU-042 (catálogo de fuentes y base), HU-045 (precio efectivo entre varias ofertas), HU-047, HU-048, HU-049 (canales manuales), HU-050, HU-051, HU-052 (captura automática).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

1. **Descartar = no guardar como observación:** las ofertas de terceros no entran a la base; en captura automática se registran solo como descartes de la ejecución. Resuelta (RN-01, RN-05).
2. **Vendedor implícito:** cuando la fuente no publica el vendedor, se usa un parámetro por fuente (inicial: Alkosto sí, demás no), sustentado en D6. Resuelta (RN-03).
3. **Coincidencia exacta normalizada** de nombres de vendedor, sin coincidencia aproximada. Resuelta (RN-02).

---

## Validación INVEST

- [x] **Independiente:** Esta HU puede implementarse sin dependencias bloqueantes de otras HU
- [x] **Negociable:** Describe QUÉ se necesita, no CÓMO implementarlo (detalles técnicos son negociables)
- [x] **Valiosa:** Aporta valor tangible al negocio o usuario final (beneficio claro)
- [x] **Estimable:** El equipo puede estimar esfuerzo (scope claro, no ambiguo)
- [x] **Pequeña:** Completable en pocos días/persona (no excede 1 sprint)
- [x] **Testeable:** Criterios de aceptación permiten verificar cuándo está terminada

## Validación Anti-Ambigüedad

- [x] **Auto-contenida:** Un desarrollador puede implementar esta HU leyendo SOLO este archivo
- [x] **Reglas completas:** Todas las reglas de negocio incluyen formatos, rangos, límites y comportamiento ante nulos
- [x] **Errores explícitos:** El comportamiento ante cada tipo de error está documentado (mensaje, acción, redirección)
- [x] **Edge cases cubiertos:** Criterios de aceptación incluyen casos borde y estados vacíos
- [x] **Supuestos resueltos:** No quedan supuestos pendientes de validación
- [x] **Datos claros:** Origen, formato y proveedor de cada dato están especificados

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes de usuario implementados
- [ ] Pruebas funcionales pasando

---

## Registro de Cambios

| Fecha | Versión | Descripción | Autor |
|-------|---------|-------------|-------|
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-004 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
