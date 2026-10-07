# Casos de Prueba — HU-065: Garantizar lenguaje no acusatorio en todos los textos generados por el sistema

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba la verificación de términos prohibidos en pruebas y en ejecución: lista inicial, normalización de mayúsculas y tildes, coincidencia por palabra completa, alcance (sistema vs. usuario y fuente), cambio de la lista con auditoría y lista inválida. Queda fuera la redacción concreta de cada pantalla.

## Precondiciones y Datos Base

- Lista inicial de RN-01. Administrador "admin.po".
- Catálogo de textos del sistema en su estado actual (sin términos prohibidos).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-04 | QA-01 |
| Escenario 2 / RN-04 | QA-02 |
| Escenario 3 / RN-01, RN-02 | QA-03 |
| Escenario 4 / RN-02 | QA-04 |
| Escenario 5 / RN-05 | QA-05 |
| Escenario 6 / RN-03 | QA-06 |
| RN-06 sin calificaciones | QA-07 |
| Escenario 7 / RN-08 | QA-08 |
| Escenario 8 / RN-07 | QA-09 |
| Permisos | QA-10 |

---

## Casos de Prueba

### QA-01: Catálogo limpio pasa la verificación

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1 / RN-04
- **Pasos:**
  1. Ejecutar la verificación automática de lenguaje.
- **Resultado esperado:** Pasa con "0 términos prohibidos encontrados en {n} textos".

### QA-02: Texto fijo con término prohibido hace fallar la verificación

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2 / RN-04
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto agregado | "Posible sobreprecio detectado" | En la etiqueta de un botón del detalle de señal |

- **Pasos:**
  1. Agregar el texto y ejecutar la verificación.
- **Resultado esperado:** Falla e informa el texto, su ubicación y el término "sobreprecio"; el despliegue no procede.

### QA-03: Variantes de mayúsculas, tildes y número

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3 / RN-01 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto | "SOBREPRECIOS" | |
  | Texto | "Corrupcion en el contrato" | Sin tilde |
  | Texto | "empresa fraudulenta" | |
  | Texto | "Hallazgos Fiscales" | Frase |

- **Pasos:**
  1. Verificar cada texto.
- **Resultado esperado:** Los cuatro se detectan.

### QA-04: Sin falsos positivos por subcadena

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 4 / RN-02
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Texto | "Precio sobre la referencia" | |
  | Texto | "Filtro antifraude de la fuente" | "fraude" como subcadena |
  | Texto | "Referencia fraccionada" | |

- **Pasos:**
  1. Verificar cada texto.
- **Resultado esperado:** Ninguno se detecta.

### QA-05: Texto compuesto de una señal con término prohibido

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5 / RN-05
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Motivo compuesto simulado | "Regla aplicada: posible fraude" | Inyectado en la plantilla de motivo |

- **Pasos:**
  1. Generar una señal con ese motivo.
  2. Abrir el detalle y consultar el log.
- **Resultado esperado:** El motivo se muestra "Texto no disponible"; la denominación es "Señal que merece revisión"; la señal se publica; el log registra señal, campo "motivo", término "fraude" y fecha-hora.

### QA-06: Datos de la fuente y textos de usuario no se alteran

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 6 / RN-03
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Objeto del contrato (SECOP II) | "Software de prevención de fraude y 2 televisores" | Dato literal |
  | Comentario de Analista | "Revisar posible sobreprecio" | Texto de usuario |

- **Pasos:**
  1. Abrir la ficha y el detalle de la señal; revisar el comentario guardado.
- **Resultado esperado:** Ambos textos se muestran literales; ninguno aparece como etiqueta, estado o calificación generada por el sistema.

### QA-07: Ninguna etiqueta ni ranking sobre entidades o proveedores

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-06
- **Pasos:**
  1. Revisar las vistas donde aparecen entidad y proveedor de SG-1 (detalle de la señal y evidencia).
- **Resultado esperado:** Solo se muestran sus datos públicos; no hay etiquetas, puntajes ni rankings de riesgo asociados.

### QA-08: Agregar un término y auditoría

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** Escenario 7 / RN-08
- **Datos de prueba:**

  | Campo | Valor | Nota |
  | ----- | ----- | ---- |
  | Término nuevo | "sobrecosto" | |
  | Texto de prueba | "Sobrecosto estimado" | |

- **Pasos:**
  1. Como "admin.po", agregar el término.
  2. Verificar el texto de prueba y consultar el log de auditoría.
- **Resultado esperado:** Se detecta "sobrecosto"; la auditoría registra "admin.po", fecha-hora, lista anterior y nueva.

### QA-09: Lista vacía o ilegible

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 8 / RN-07
- **Pasos:**
  1. Configurar la lista vacía y verificar "sobreprecio".
  2. Configurar una lista con un elemento vacío y repetir.
- **Resultado esperado:** En ambos casos se usa la lista inicial, se detecta "sobreprecio" y el log registra "Lista de términos prohibidos inválida; se usó la lista inicial".

### QA-10: Solo el Administrador cambia la lista

- **Tipo:** Permisos
- **Prioridad:** Media
- **Cubre:** Permisos requeridos
- **Pasos:**
  1. Intentar modificar la lista con el Analista "analista.piloto1".
- **Resultado esperado:** La operación no está disponible o es rechazada; la lista no cambia.

---

**Total de casos:** 10
