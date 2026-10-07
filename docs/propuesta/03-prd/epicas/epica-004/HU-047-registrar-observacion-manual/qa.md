# Casos de Prueba — HU-047: Registrar manualmente una observación de precio con evidencia adjunta

**Historia:** [historia.md](./historia.md) | **Autor:** Juan Camilo | **Fecha:** 2026-10-02

## Alcance de las Pruebas

Se prueba el canal de carga manual individual: registro exitoso, campos asignados por el sistema, validación de evidencia, ventana de fecha, vendedor y fuente, declaración de precio por unidad, errores múltiples, doble envío, identificación como manual, usuario registrador, evento auditable y permisos.

Fuera de alcance: búsqueda manual con varias ofertas (HU-048), carga por archivo (HU-049) y la presentación de evidencias dentro de las señales (épica de señales).

## Precondiciones y Datos Base

- **Usuarios:** `admin.po@prueba.local` (Administrador); `analista1@prueba.local` (Analista).
- **Catálogo:** Alkosto y Falabella con carga manual habilitada; Éxito deshabilitada. Antigüedad máxima manual = 7 días; evidencia máx. 10 MB.
- **Fecha y hora de ejecución de referencia:** 2026-10-02T12:00-05:00.
- **Formulario base (F-BASE):** Alkosto; "Televisor Samsung 55 pulgadas Crystal UHD 4K Smart"; Samsung; UN55DU7000KXZL; vendedor Alkosto; precio 1899900; URL https://www.alkosto.com/televisor-samsung-55/p/0000000000001; fecha 2026-10-02T10:00; IVA indeterminado; condición ninguna; declaración marcada; evidencia `captura-alkosto-un55.png` (450 KB).
- **Archivos de prueba:** `ficha.docx` (200 KB), `grande.png` (10,5 MB), `limite.png` (10,0 MB exactos), `vacio.png` (0 bytes), `falso.png` (texto plano renombrado), `oferta.pdf` (1 MB).

## Matriz de Cobertura

| Criterio / Regla | Casos |
|---|---|
| Escenario 1 / RN-01 / RN-04 | QA-01 |
| Escenario 2 / RN-03 | QA-02 |
| Escenario 3 / RN-03 | QA-03, QA-04 |
| Escenario 4 / RN-02 | QA-05 |
| Escenario 5 / RN-02 | QA-06 |
| Escenario 6 / RN-01 | QA-07 |
| Escenario 7 / RN-02 | QA-08 |
| RN-01 (referencia de texto, condición especial) | QA-09 |
| Escenario 8 / RN-06 | QA-10 |
| Escenario 9 / RN-05 | QA-11 |
| RN-04 | QA-12 |
| RN-07 | QA-13 |
| Escenario 10 | QA-14 |

---

## Casos de Prueba

### QA-01: Registro manual exitoso

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 1, RN-01, RN-04
- **Pasos:**
  1. Como `admin.po@prueba.local`, enviar F-BASE.
- **Resultado esperado:** mensaje `"Observación manual registrada: {id}."`; la observación tiene `metodo_adquisicion = manual`, `canal_carga = individual`, `protocolo_busqueda = no_registrado`, `registrado_por = admin.po@prueba.local`, `fecha_registro` del servidor, `es_manual = sí`, `etiqueta_origen = "Observación manual"`, `apta_para_referencia = sí` y evidencia con hash SHA-256.

### QA-02: Sin evidencia

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 2, RN-03
- **Resultado esperado:** al enviar F-BASE sin archivos: `"La observación requiere al menos una evidencia."`; no se guarda.

### QA-03: Evidencias inválidas

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Archivo | Mensaje esperado |
  | ----- | ----- |
  | ficha.docx | `"Formato de evidencia no permitido: use PNG, JPG o PDF."` |
  | grande.png | `"La evidencia supera el tamaño máximo de 10 MB."` |
  | vacio.png | `"El archivo de evidencia está vacío o dañado."` |
  | falso.png | `"Formato de evidencia no permitido: use PNG, JPG o PDF."` |
  | 6 archivos PNG válidos | `"Se admiten máximo 5 evidencias por observación."` |

### QA-04: Evidencias válidas en el límite

- **Tipo:** Borde
- **Prioridad:** Media
- **Cubre:** Escenario 3, RN-03
- **Datos de prueba:**

  | Archivos |
  | ----- |
  | limite.png (10,0 MB) |
  | oferta.pdf + 4 PNG válidos (5 archivos) |

- **Resultado esperado:** ambas observaciones se guardan con todas sus evidencias y un hash por archivo.

### QA-05: Ventana de fecha de observación

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 4, RN-02
- **Datos de prueba:**

  | fecha_observacion | Resultado |
  | ----- | ----- |
  | 2026-09-25T12:00 (7 días exactos) | Guardada |
  | 2026-09-25T11:59 (7 días y 1 minuto) | `"La fecha de observación no puede tener más de 7 días de antigüedad."` |
  | 2026-10-02T12:00 (ahora) | Guardada |
  | 2026-10-02T12:05 (futura) | `"La fecha de observación no puede ser futura."` |

### QA-06: Vendedor tercero y fuente deshabilitada

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 5, RN-02
- **Datos de prueba:**

  | Fuente | Vendedor | Mensaje esperado |
  | ----- | ----- | ----- |
  | Falabella | TecnoImport SAS | `"Solo se aceptan observaciones cuyo vendedor sea directamente la tienda Falabella. Vendedor recibido: TecnoImport SAS."` |
  | Éxito | Éxito | `"La fuente Éxito no está habilitada para el método manual."` |

### QA-07: Declaración de precio por unidad sin marcar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** Escenario 6, RN-01
- **Resultado esperado:** `"Confirme que el precio corresponde a una unidad del televisor, sin combos ni accesorios."`; no se guarda.

### QA-08: Varios errores a la vez

- **Tipo:** Negativo
- **Prioridad:** Alta
- **Cubre:** Escenario 7, RN-02
- **Datos de prueba:**

  | Campo | Valor |
  | ----- | ----- |
  | marca | (vacío) |
  | precio efectivo | 1.899.900,50 |
  | EAN | 880609552001 (12 dígitos, control erróneo) |

- **Resultado esperado:** se devuelven juntos `"Campo obligatorio ausente: marca."`, `"precio_efectivo debe ser un entero entre 1 y 999.999.999 COP."` y `"ean_gtin no es un GTIN válido."`; en formulario, los demás valores ingresados se conservan.

### QA-09: Referencia de texto y precio condicionado

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-01
- **Datos de prueba:**

  | Variante | Cambio sobre F-BASE | Resultado |
  | ----- | ----- | ----- |
  | A | referencia texto "Catálogo impreso Alkosto, octubre 2026, pág. 4" | Guardada con `tipo_referencia = texto` |
  | B | condición "tarjeta específica", detalle "Precio con tarjeta de crédito de la tienda" | Guardada con `apta_para_referencia = no` |

### QA-10: Doble envío dentro de 10 minutos

- **Tipo:** Borde
- **Prioridad:** Alta
- **Cubre:** Escenario 8, RN-06
- **Pasos:**
  1. Enviar F-BASE a las 12:00.
  2. Enviar F-BASE idéntico a las 12:03.
  3. Enviar F-BASE idéntico a las 12:11.
  4. Enviar F-BASE con precio 1899800 a las 12:04.
- **Resultado esperado:** paso 2: `"Esta observación ya fue registrada hace menos de 10 minutos ({id del paso 1})."` sin crear observación; pasos 3 y 4 crean observaciones nuevas.

### QA-11: Etiqueta manual en toda entrega

- **Tipo:** Positivo
- **Prioridad:** Alta
- **Cubre:** Escenario 9, RN-05
- **Pasos:**
  1. Leer la observación de QA-01 desde la lectura usada por la comparación y desde la consulta administrativa.
- **Resultado esperado:** ambas lecturas incluyen `etiqueta_origen = "Observación manual"`, `fecha_registro` y `registrado_por`.

### QA-12: El usuario registrador no se puede suplantar

- **Tipo:** Negativo
- **Prioridad:** Media
- **Cubre:** RN-04
- **Pasos:**
  1. Como `admin.po@prueba.local`, enviar F-BASE incluyendo `registrado_por = otro.admin@prueba.local`.
- **Resultado esperado:** la observación queda con `registrado_por = admin.po@prueba.local` (el valor enviado se ignora).

### QA-13: Evento auditable de carga manual

- **Tipo:** Positivo
- **Prioridad:** Media
- **Cubre:** RN-07
- **Resultado esperado:** tras QA-01 existe el evento `carga_manual_observacion` con `admin.po@prueba.local`, fecha y hora e `id_observacion`; los envíos rechazados no generan este evento.

### QA-14: Analista no registra observaciones

- **Tipo:** Permisos
- **Prioridad:** Alta
- **Cubre:** Escenario 10
- **Resultado esperado:** como `analista1@prueba.local`, enviar F-BASE devuelve `"Operación permitida solo para el rol Administrador."`

---

**Total de casos:** 14
