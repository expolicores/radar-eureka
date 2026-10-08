# Casos de Prueba — Historia #2: Modelo de compras de televisores y datos seed

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-07

## Alcance de las Pruebas

**Se prueba:** la clasificación por reglas de los ítems, la carga desde la fuente seed (volumen, campos, idempotencia, bitácora), los estados explícitos de datos faltantes, la privacidad de personas naturales y los montos enteros.
**Queda fuera:** API, pantallas, señales, conector real de Socrata.

## Precondiciones y Datos Base

| Dato | Valor | Nota |
| ---- | ----- | ---- |
| Base de datos | PostgreSQL con migraciones hasta la última revisión | Embebido en local, PostgreSQL 16 en CI |
| Fuente | Adaptador seed del puerto `PublicDataSource` | Determinístico: la misma semilla produce el mismo dataset |
| Compra de referencia | `CO1.PCCNTR.0000142` · Alcaldía Municipal de San Rafael del Valle · Tecnología Andina Demo S.A.S. · 8 × $4.950.000 IVA incluido · firmada 2026-08-14 | Caso del mockup |

## Matriz de Cobertura

| Criterio / Regla | Casos |
| ---------------- | ----- |
| Escenario 1: carga completa | QA-01, QA-02 |
| Escenario 2: clasificación por reglas | QA-03 |
| Escenario 3: idempotencia y montos enteros | QA-04 |
| Escenario 4: estados explícitos | QA-05 |
| Escenario 5: privacidad | QA-06 |
| Regla: identidad fuente + identificador sin transformar | QA-02, QA-04 |

---

## Casos de Prueba

### QA-01: La carga seed registra el volumen esperado de compras con sus ítems

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1
- **Pasos:**
  1. Ejecutar la carga desde la fuente seed sobre una base vacía.
  2. Contar compras por fuente y revisar fechas, ítems y bitácora.
- **Resultado esperado:** entre 1.000 y 1.500 compras, con contratos SECOP II y órdenes TVEC; fechas entre 2023-01-01 y la fecha de corte; cada compra con al menos un ítem; una ejecución por fuente (SECOP II y TVEC) en la bitácora, con leídos = nuevos = compras de esa fuente y fecha de corte.

### QA-02: La compra de referencia del mockup queda completa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / identidad
- **Pasos:**
  1. Buscar la compra `CO1.PCCNTR.0000142` de SECOP II.
- **Resultado esperado:** entidad, departamento Valle del Cauca, proveedor con NIT 900.000.142-1, modalidad «Mínima cuantía», valor $39.600.000, fecha 2026-08-14; ítem de televisor incluido (8 × $4.950.000, IVA incluido, 65", 4K) y ítem de soporte excluido como accesorio.

### QA-03: Las reglas clasifican cada tipo de ítem

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 2
- **Datos de prueba:**

  | Descripción | Clasificación esperada |
  | ----------- | ---------------------- |
  | Televisor Smart TV 65" 4K UHD | incluido |
  | TV LED 43 pulgadas Full HD | incluido |
  | Soporte de pared para TV 55"–75" | excluido · accesorio |
  | Mantenimiento de televisores | excluido · servicio |
  | Instalación de televisores en aulas | excluido · servicio |
  | Pantalla 4K para gimnasio | dudoso |
  | Portátil 14" | dudoso |

- **Resultado esperado:** cada descripción recibe la clasificación de la tabla.

### QA-04: Relanzar la carga no duplica datos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 3
- **Precondiciones:** QA-01 ejecutado.
- **Pasos:**
  1. Ejecutar la carga seed de nuevo.
- **Resultado esperado:** el número de compras e ítems no cambia; la bitácora tiene 2 ejecuciones por fuente y las segundas registran 0 nuevos; los montos son enteros.

### QA-05: Los datos faltantes quedan como estado explícito

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4
- **Pasos:**
  1. Revisar los ítems incluidos del seed por estado de precio y de IVA.
- **Resultado esperado:** hay ítems con precio `no publicado` (sin valor), con IVA `indeterminado` y `en revisión`; ningún ítem `no publicado` tiene precio unitario.

### QA-06: No se guarda el documento de personas naturales

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5
- **Pasos:**
  1. Revisar las compras con proveedor persona natural.
- **Resultado esperado:** el proveedor aparece como «Persona natural — documento no visible» y su documento es nulo; ninguna columna guarda un documento de persona natural.

---

**Total de casos:** 6
