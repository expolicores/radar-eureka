# Registro de Cambios — HU-056: Homologar la base tributaria (IVA) y marcar comparaciones incompletas

| Fecha | Fase | Descripción | Autor |
|-------|------|-------------|-------|
| 2026-10-02 | Creación | Historia creada por workflow generar-historias-usuario | Juan Camilo (PO) |
| 2026-10-05 | Versión 1.1 | Decisión PO: se elimina la conversión de valores sin IVA con tarifa general (19 %) y el parámetro `tarifa_iva_general`. Un valor sin IVA solo se convierte con el IVA o la tarifa explícitos del documento, registrando evidencia (documento y página/hoja/celda); sin tarifa explícita no se convierte y la comparación queda incompleta/no confiable (motivo: posibles exenciones o tarifas diferenciales, p. ej. San Andrés, halladas en el spike D4). Historia: Escenario 2 reescrito, nuevo Escenario 4 (tarifa explícita), escenarios renumerados (5–10), RN-02/03/04/05/06/08, valor de negocio y supuestos ajustados. QA: QA-02, QA-10 y QA-11 reescritos, nuevo QA-04, QA-13 sin tarifa general, casos renumerados (14 en total) | Juan Camilo (PO) |
