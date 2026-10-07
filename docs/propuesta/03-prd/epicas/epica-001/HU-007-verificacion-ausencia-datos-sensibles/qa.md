# Casos de Prueba — HU-007: Verificación automática de ausencia de datos personales sensibles

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la verificación de datos sensibles: comprobaciones de configuración, esquema y valores testigo; excepciones; bloqueo en pruebas automáticas; comportamiento en producción; registro de campos descartados no reconocidos; y lista de patrones vacía.

Queda fuera: la mecánica de las cargas (HU-001 a HU-004).

## Precondiciones y Datos Base

- Administrador: `admin.po@piloto.test`. Entornos: "pruebas" y "producción".
- Patrones iniciales de RN-01 y excepciones `documento_proveedor`, `proveedor_documento`.
- Listas blancas iniciales de SECOP II contratos, TVEC ítems y TVEC órdenes (sin campos prohibidos).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-06 | QA-01 |
| Escenario 2 / RN-03, RN-09 | QA-02 |
| Escenario 3 / RN-04, RN-01 | QA-03 |
| Escenario 4 / RN-05 | QA-04, QA-05 |
| Escenario 5 / RN-07 | QA-06 |
| Escenario 6 | QA-07 |
| Escenario 7 / RN-08 | QA-08 |
| Escenario 8 / RN-01 | QA-09 |
| RN-02 | QA-10, QA-11 |

---

## Casos de Prueba

### QA-01: Verificación completa aprobada

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-06
- **Pasos:**
  1. Ejecutar la verificación en el entorno de pruebas.
- **Resultado esperado:** configuración, esquema y valores testigo "Aprobada"; resultado general "Aprobada: 0 campos personales sensibles encontrados"; queda registrado con fecha, entorno y usuario; el contrato sintético ya no existe al terminar.

### QA-02: Campo prohibido en una lista blanca

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-03, RN-09
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Lista SECOP II contratos | + `tipo_de_cuenta` | patrón cuenta |
  | Lista SECOP II contratos | + `Cédula Supervisor` | normalizado `cedula_supervisor` |
  | Lista TVEC órdenes | + `banco_pago` | aplica también a TVEC |

- **Pasos:**
  1. Agregar cada campo (uno por ejecución) y ejecutar la verificación.
- **Resultado esperado:** configuración "Fallida" con "Campo prohibido en la lista blanca de {fuente}: {campo} (patrón: {patrón})"; resultado general "Fallida".

### QA-03: Columna sensible en el esquema

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-04, RN-01
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Columna | `numero_cuenta_proveedor` | coincide con cuenta |
  | Columna | `documento_representante_legal` | documento + representante |
  | Columna | `documento_entidad` | documento sin representante/supervisor/ordenador → no coincide |

- **Pasos:**
  1. Crear cada columna en una tabla de prueba y ejecutar la verificación.
- **Resultado esperado:** las dos primeras hacen fallar el esquema listando tabla, columna y patrón; la tercera no genera hallazgo.

### QA-04: Valores testigo no aparecen en ninguna capa

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Ejecutar la comprobación con valores testigo.
  2. Revisar el informe de búsqueda.
- **Resultado esperado:** se buscaron los 5 valores en base de datos, registro de rechazos (la variante sin `nombre_entidad` generó un rechazo), bitácora, logs y archivos; 0 coincidencias; "Aprobada".

### QA-05: Fuga simulada detectada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 4 / RN-05
- **Pasos:**
  1. Con un doble de prueba, hacer que la carga escriba en el log de aplicación el registro completo recibido.
  2. Ejecutar la comprobación.
- **Resultado esperado:** "Fallida", indicando la capa "logs de aplicación" y la ubicación (archivo y línea); el informe no repite el valor testigo completo.

### QA-06: Bloqueo del conjunto de pruebas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-07
- **Pasos:**
  1. Introducir el cambio de QA-02 en una rama y ejecutar el conjunto de pruebas automáticas.
- **Resultado esperado:** el conjunto falla y el cambio no puede promoverse.

### QA-07: Verificación en producción sin valores testigo

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6
- **Pasos:**
  1. Ejecutar el comando en producción.
- **Resultado esperado:** solo corren configuración y esquema; "Comprobación de valores testigo: no aplica en este entorno"; no se crea ningún contrato sintético.

### QA-08: Registro de campos descartados no reconocidos

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Pasos:**
  1. Ejecutar una carga en la que 3 contratos traen `nombre_banco_pago = Banco Ficticio S.A.`.
- **Resultado esperado:** la ejecución registra una vez "Campos descartados no reconocidos: nombre_banco_pago"; el valor "Banco Ficticio S.A." no aparece en ningún registro.

### QA-09: Lista de patrones vacía

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-01
- **Pasos:**
  1. Vaciar la lista de patrones y ejecutar la verificación; luego ejecutar una carga.
- **Resultado esperado:** ambas fallan sin procesar datos con "La lista de patrones prohibidos está vacía. Configure al menos los patrones iniciales."

### QA-10: Excepción explícita de documento del proveedor

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Lista blanca | `documento_proveedor` | exceptuado → sin hallazgo |
  | Lista blanca | `documento_proveedor_representante` | no es nombre exacto exceptuado → hallazgo |

- **Pasos:**
  1. Ejecutar la verificación con cada lista.
- **Resultado esperado:** la primera aprueba; la segunda falla por el patrón documento + representante.

### QA-11: Documento del proveedor almacenado no es hallazgo de esquema

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** RN-02, RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Columna | `documento_proveedor` | exceptuada, se almacena |
  | Columna | `tipodocproveedor` | no coincide con ningún patrón |
  | Contrato | tipo `Cédula de Ciudadanía`, documento `1012345678` | persona natural almacenada |

- **Pasos:**
  1. Ingerir el contrato en el entorno de pruebas con las columnas indicadas.
  2. Ejecutar la verificación.
- **Resultado esperado:** la comprobación de esquema aprueba sin hallazgos por `documento_proveedor` ni `tipodocproveedor`; el valor `1012345678` permanece almacenado (su ocultamiento en la interfaz del analista se verifica en HU-070, HU-075 y HU-076, no en esta historia).

---

**Total de casos:** 11
