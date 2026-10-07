# Historia #036: Emparejar como mismo modelo por EAN/GTIN

**Estado:** Borrador (PO)  
**Release:** Release MVP  
**Épica:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)  
**Feature:** Emparejar por Mismo Modelo  
**Prioridad:** Crítica  
**FRs relacionados:** FR-037

Escrita por el flujo generar-historias-usuario (Método Ceiba) — MVP propio, no comercial

---

## Historia de Usuario

**Como** Analista que investiga contratación pública,  
**Quiero** que dos televisores con el mismo código EAN/GTIN válido se emparejen como mismo modelo,  
**Para** aprovechar el identificador de producto cuando existe en ambos lados, aunque la marca o el modelo no se hayan podido normalizar.

## Descripción

Alkosto publica el EAN en sus datos estructurados; la TVEC y la mayoría de documentos de SECOP II no lo traen (D6). Cuando ambos lados de un par tienen un EAN/GTIN válido e idéntico, el par es **mismo modelo** (FR-037), complementando el emparejamiento por marca y modelo normalizado.

Esta HU (1) valida y normaliza el EAN/GTIN de cada producto normalizado y lo guarda en el campo `ean` del esquema común, y (2) genera los pares `MISMO_MODELO` con `criterio = EAN`. Un SKU interno de la tienda no es un EAN y no se usa. Proceso de backend, determinístico y sin interfaz gráfica.

---

## Criterios de Aceptación

### Escenario 1: EAN válido en una observación retail

- **Dado** que una observación retail tiene identificador de tipo EAN con valor `8806095512341` y dígito de control válido
- **Cuando** se ejecuta la normalización del EAN
- **Entonces** `ean = 08806095512341` (GTIN de 14 dígitos), con el valor original y el campo de origen registrados

### Escenario 2: Formatos equivalentes de EAN

- **Dado** que los valores originales son `8806 0955 12341`, `8-806095-512341` y `08806095512341`
- **Cuando** se normalizan
- **Entonces** los tres quedan con `ean = 08806095512341`

### Escenario 3: EAN inválido

- **Dado** que el identificador de tipo EAN es `8806095512346` (dígito de control incorrecto), `880609551` (9 dígitos, longitud no permitida), o `88O6095512345` (contiene una letra)
- **Cuando** se normaliza
- **Entonces** `ean` queda nulo con motivo `EAN_INVALIDO` y el valor original se conserva

### Escenario 4: SKU interno no es EAN

- **Dado** que una observación de Falabella trae un identificador de tipo SKU `881234567`
- **Cuando** se normaliza
- **Entonces** `ean` queda nulo con motivo `IDENTIFICADOR_NO_ES_EAN`, aunque el valor sea numérico

### Escenario 5: Par mismo modelo por EAN

- **Dado** que el ítem objetivo SECOP II SEC-2401-I1 tiene `ean = 08806095512341` (extraído de una ficha técnica) y la observación RET-3401 tiene el mismo `ean`, y la marca o el modelo de alguno de los dos es nulo
- **Cuando** se ejecuta el emparejamiento
- **Entonces** se registra el par `MISMO_MODELO` con `criterio = EAN`

### Escenario 6: Coincidencia por EAN y por marca y modelo

- **Dado** que un par coincide en EAN y también en marca y modelo normalizado
- **Cuando** se ejecuta el emparejamiento
- **Entonces** existe un único par vigente `MISMO_MODELO` con `criterio = MARCA_MODELO_Y_EAN`

### Escenario 7: EAN igual con marcas distintas o atributos contradictorios

- **Dado** que un par tiene el mismo `ean` pero las marcas son no nulas y distintas, o el tamaño, la resolución o la tecnología son no nulos y distintos
- **Cuando** se ejecuta el emparejamiento
- **Entonces** el par se registra como `INSUFICIENTE_NO_CONFIABLE` con motivo `CONFLICTO_ATRIBUTOS` y el detalle de cada atributo en conflicto

### Escenario 8: EAN distinto con marca y modelo iguales

- **Dado** que un par coincide en marca y modelo normalizado y ambos tienen EAN válidos pero distintos
- **Cuando** se ejecuta el emparejamiento
- **Entonces** el par sigue siendo `MISMO_MODELO` con `criterio = MARCA_MODELO` y en sus criterios se registra `ean_distinto = sí` con ambos valores

### Escenario 9: EAN en un solo lado

- **Dado** que solo uno de los dos productos tiene `ean`
- **Cuando** se ejecuta el emparejamiento por EAN
- **Entonces** no se genera par por EAN; el par solo puede formarse por marca y modelo o por equivalencia

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista (beneficiario). El proceso lo ejecuta el sistema.
- **Permisos requeridos:** no hay parámetros configurables propios de esta HU, salvo la lista compartida de atributos de control de conflicto, que solo modifica el Administrador.
- **Valor de negocio:** amplía los emparejamientos de mayor confianza sin depender de la calidad del texto del modelo.

### Reglas de Negocio

**RN-01 — Origen del EAN.** Solo se usan identificadores cuyo tipo, según el registro de origen, sea EAN, GTIN, UPC o código de barras: campo de identificador de la observación retail con ese tipo, o campo EAN/GTIN extraído de un documento de SECOP II. Un identificador de tipo SKU, código interno o sin tipo → `ean` nulo, `IDENTIFICADOR_NO_ES_EAN`. Sin identificador → nulo, `EAN_NO_INFORMADO`. La TVEC no aporta EAN salvo que su registro lo traiga con tipo explícito.

**RN-02 — Normalización.** Quitar espacios y guiones; el resultado debe tener solo dígitos y una longitud de 8, 12, 13 o 14; se completa con ceros a la izquierda hasta 14 dígitos (GTIN-14). Cualquier otro carácter o longitud → nulo, `EAN_INVALIDO`.

**RN-03 — Dígito de control.** Se valida el dígito de control GS1 (módulo 10: sobre los 13 primeros dígitos del GTIN-14, de derecha a izquierda, pesos alternos 3 y 1; el dígito de control es `(10 − (suma mod 10)) mod 10`). Si no coincide → nulo, `EAN_INVALIDO`. No se consulta ningún servicio externo (GS1 ni fabricantes).

**RN-04 — Ítems objetivo y candidatos.** Iguales a los del emparejamiento por marca y modelo: objetivo = producto vigente y activo `SECOP_II` o `TVEC`; candidato = otro producto vigente y activo de la misma categoría (`SECOP_II`, `TVEC`, `RETAIL`) con `id_origen` distinto.

**RN-05 — Mismo modelo por EAN.** `ean` no nulo en ambos y exactamente igual → `MISMO_MODELO`, `criterio = EAN`. Si además coinciden marca y `modelo_normalizado` (no nulos) → un solo par con `criterio = MARCA_MODELO_Y_EAN`.

**RN-06 — Control de conflicto.** Si `ean` coincide pero `marca` es no nula en ambos y distinta, o algún atributo de la lista de control (**configuración inicial:** `tamano_pulgadas`, `resolucion`, `tecnologia`) es no nulo en ambos y distinto → `INSUFICIENTE_NO_CONFIABLE`, motivo `CONFLICTO_ATRIBUTOS`, con detalle `atributo: valor objetivo vs valor candidato`. Nulos → `NO_EVALUADO`, no bloquean.

**RN-07 — EAN distinto.** Si un par es `MISMO_MODELO` por marca y modelo y ambos tienen `ean` distinto, el tipo no cambia; se registra `ean_distinto = sí` con ambos valores como información en los criterios.

**RN-08 — Registro, recálculo e idempotencia.** El par se registra con los mismos campos que el emparejamiento por marca y modelo (objetivo, candidato, tipo, criterio, criterios evaluados, motivo, versiones, `version_reglas`, fecha, `vigente`), con un solo par vigente por {objetivo, candidato}. Un cambio de `ean` genera nueva versión del producto y recálculo de sus pares; los reemplazados pasan a `vigente = no`. Reejecutar sin cambios no crea registros.

**RN-09 — Tolerancia a errores.** Un error en un registro no detiene el lote; se registra y se reintenta.

### Interfaz

Sin interfaz gráfica. Consultable por consulta a la base; visualización para el Analista en HU-040.

### Sistemas Externos (Si aplica)

No aplica. No se integra con GS1 ni con bases de fabricantes (exclusión de la épica).

---

## Contexto y Referencias

**Épica origen:** [Normalización y Emparejamiento de Televisores](../../../epicas.md#épica-003-normalización-y-emparejamiento-de-televisores)

**Exclusiones de la Épica:**
- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

**Historias relacionadas:** HU-031 (producto normalizado), HU-035 (mismo modelo por marca y modelo), HU-039 (clasificación), HU-040 (consulta de criterios).

---

## Supuestos

> Elementos inferidos por la IA que NO estaban explícitos en el PRD o la Épica. Todos los supuestos han sido resueltos: convertidos en reglas de negocio explícitas o eliminados mediante reformulación. Si aparece algún supuesto no resuelto, esta HU NO está lista para desarrollo.

- **S-01 (Resuelto → RN-01):** solo se usa como EAN un identificador declarado como EAN/GTIN/UPC por el origen; el SKU interno (ej. Falabella) no se usa aunque sea numérico.
- **S-02 (Resuelto → RN-02, RN-03):** el EAN se normaliza a GTIN-14 y se valida con el dígito de control GS1, sin consultar servicios externos.
- **S-03 (Resuelto → RN-06, RN-07):** EAN igual con marca o atributos contradictorios → insuficiente/no confiable; EAN distinto con marca y modelo iguales sigue siendo mismo modelo (FR-037 usa "o"), con la diferencia visible.

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
| 2026-10-02 | 1.0 | Historia generada desde Épica ÉPICA-003 | Juan Camilo (PO) |

---

> **Método Ceiba estimar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-05
