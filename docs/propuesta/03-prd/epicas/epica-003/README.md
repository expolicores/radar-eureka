# ÉPICA-003: Normalización y Emparejamiento de Televisores

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Hace comparables televisores descritos de formas muy distintas (especificaciones genéricas de SECOP II, textos sin normalizar de la TVEC y nombres comerciales retail con EAN). Lleva cada televisor a un esquema común (marca, modelo normalizado, tamaño, resolución, tecnología, Smart y generación) y lo empareja como **mismo modelo** (marca + modelo normalizado sintácticamente, o EAN/GTIN) o como **producto equivalente** (características técnicas configuradas), con criterios visibles. Si no hay comparables, el resultado es **insuficiente / no confiable**: nunca se relajan los criterios para forzar una referencia (Adenda 2, A2.7).

**Prioridad:** Crítica  
**FRs cubiertos:** FR-035, FR-036, FR-037, FR-038, FR-039, FR-040  
**Total HU:** 11 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Normalizar Atributos al Esquema Común

- [HU-031: Normalizar marca, tamaño y resolución al esquema común](./HU-031-normalizar-marca-tamano-resolucion/historia.md)
- [HU-032: Normalizar tecnología de pantalla, Smart y generación del televisor](./HU-032-normalizar-tecnologia-smart-generacion/historia.md)

### Feature 2: Normalizar Códigos de Modelo

- [HU-033: Identificar el código de modelo en el registro de origen](./HU-033-identificar-codigo-modelo-origen/historia.md)
- [HU-034: Normalizar sintácticamente el código de modelo](./HU-034-normalizar-sintaxis-codigo-modelo/historia.md)

### Feature 3: Emparejar por Mismo Modelo

- [HU-035: Emparejar como mismo modelo por marca y modelo normalizado](./HU-035-emparejar-mismo-modelo-marca-modelo/historia.md)
- [HU-036: Emparejar como mismo modelo por EAN/GTIN](./HU-036-emparejar-mismo-modelo-ean-gtin/historia.md)

### Feature 4: Emparejar por Equivalencia Técnica

- [HU-037: Configurar las reglas de equivalencia por categoría](./HU-037-configurar-reglas-equivalencia/historia.md)
- [HU-038: Emparejar productos equivalentes por características técnicas](./HU-038-emparejar-productos-equivalentes/historia.md)

### Feature 5: Clasificar y Explicar el Emparejamiento

- [HU-039: Clasificar el resultado de emparejamiento de cada ítem](./HU-039-clasificar-resultado-emparejamiento/historia.md)
- [HU-040: Consultar los criterios de emparejamiento de un ítem](./HU-040-consultar-criterios-emparejamiento/historia.md)
- [HU-041: Verificar que ningún emparejamiento use criterios relajados](./HU-041-verificar-criterios-no-relajados/historia.md)

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-031 | FR-035 | Analista | Marca, tamaño y resolución homogéneos y trazables para comparar fuentes heterogéneas |
| HU-032 | FR-035 | Analista | Tecnología, Smart y generación sin valores asumidos, base de la equivalencia |
| HU-033 | FR-035, FR-036 | Analista | Solo códigos de modelo reales (sin códigos internos ni referencias del pliego) |
| HU-034 | FR-036, FR-035 | Analista | Mismo código escrito distinto se reconoce, sin fusionar variantes (`PSA`/`PSB`) |
| HU-035 | FR-037 | Analista | Comparación de mayor confianza: misma marca y modelo, con control de conflictos |
| HU-036 | FR-037 | Analista | Mismo modelo por EAN/GTIN válido cuando existe en ambos lados |
| HU-037 | FR-038, FR-040 | Administrador | Reglas de equivalencia explícitas, versionadas y con piso no relajable |
| HU-038 | FR-038, FR-040 | Analista | Equivalentes para compras especificadas por características, sin relajar criterios |
| HU-039 | FR-039 | Analista | 100 % de los ítems con clasificación única y resumen de criterios |
| HU-040 | FR-039 | Analista | Criterios visibles por producto emparejado para juzgar la comparación |
| HU-041 | FR-040, FR-039 | Administrador | Evidencia de no relajación y medición de exactitud con muestra manual |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye un catálogo maestro de fabricantes ni una integración con bases de datos de productos (GS1, fabricantes).
- NO incluye la equivalencia entre categorías distintas.
- NO incluye la estimación de precio por depreciación o antigüedad del modelo.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
