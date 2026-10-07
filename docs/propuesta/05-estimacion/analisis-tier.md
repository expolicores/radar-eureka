# Análisis de Tier de Servicio: Seguimiento Compras Públicas

**Fecha:** 2026-10-02
**Autor:** Juan Camilo
**Estado:** Aprobado (2026-10-02)

> **Naturaleza del proyecto:** MVP propio basado en la tesis, para validar una hipótesis de producto con usuarios reales (no es una propuesta comercial). El tier se usa aquí como **nivel de rigor de ingeniería** para construirlo con los agentes del Método Ceiba. Donde la plantilla dice "cliente", se lee "propietario / PO".

---

## Documentos de Referencia

- **Brief de Alcance** (aprobado, con Adendas 1, 2 y 3): [../02-brief-alcance/brief-alcance.md](../02-brief-alcance/brief-alcance.md)
- **PRD** (aprobado conceptualmente): [../03-prd/PRD.md](../03-prd/PRD.md) · [Épicas](../03-prd/epicas.md)
- **Spikes:** [D1](../03-prd/insumos/D1-spike-secop-datos-abiertos.md) · [D4](../03-prd/insumos/D4-spike-extraccion-documental.md) · [D6](../03-prd/insumos/D6-spike-fuentes-precios-mercado.md)

---

## Recomendación

**Tier Recomendado: Professional**

La recomendación la determinan dos dimensiones de nivel **Medio**: **sensibilidad de datos** y **complejidad de integraciones**.
- **Datos:** el sistema maneja **datos personales** de los analistas registrados (correo, credenciales, casos y notas privadas) y nombres de proveedores que pueden ser **personas naturales** asociados a señales de revisión, bajo la Ley 1581 de 2012 (PRD: NFR-SEG, NFR-CUM-001; Brief: A1.4 y R3).
- **Integraciones:** depende de unas **6 dependencias externas** con protocolos mixtos: la API Socrata de datos.gov.co (contratos, archivos por año, TVEC), la descarga de documentos de SECOP, los datos estructurados de Alkosto y Falabella, el proveedor de IA multimodal y el correo para invitaciones y recuperación de contraseña. D1, D4 y D6 mostraron que estas fuentes cambian, fallan o se restringen.

Lo que Professional aporta y Essential no, en concreto para este proyecto:
- **Pruebas unitarias y de integración del flujo crítico:** ingesta → extracción → normalización → benchmark → señal → evidencia. Un error en ese flujo no es una caída: es una **señal equivocada asociada al nombre de una entidad o proveedor**, que es el principal riesgo reputacional y legal del producto (R2, R3).
- **Análisis de seguridad SCA + OWASP,** coherente con el NFR-SEG-008 ya aprobado.
- **Gestión de secretos con vault:** llaves del proveedor de IA y app token de datos.gov.co (NFR-SEG-006).
- **Logging estructurado con health checks** para operar las ingestas y capturas (NFR-OBS).

**Premium no se justifica:** no hay escala masiva, datos financieros ni de salud, SLA ni sistema transaccional crítico. Sus diferenciadores (CD automatizado, pentesting, pruebas de carga completas, FinOps/GreenOps) no reducen ningún riesgo identificado del MVP.

---

## Evaluación de Riesgo por Dimensión

| Dimensión | Nivel | Tier Mínimo | Evidencia |
|---|---|---|---|
| Criticidad del Sistema | **Bajo** | Essential | PRD NFR-DIS-001: "99 % mensual … objetivo inicial de ingeniería del piloto — sin SLA contractual"; Brief: "No existe una fecha externa ni un evento que obligue a lanzar". Una caída afecta solo la experiencia del piloto y no la operación de terceros. *Nota:* la criticidad de **exactitud** (señales correctas) es mayor que la de disponibilidad; se cubre en las dimensiones 2 y 5 y con las pruebas del flujo crítico. |
| Sensibilidad de Datos | **Medio** | **Professional** | Brief A1.4: el dataset de contratos trae "banco, tipo y número de cuenta, y documentos de identidad … Estos campos no se ingieren ni se muestran"; Brief: "tratamiento de datos de personas naturales contratistas y de los usuarios registrados (Ley 1581 de 2012)"; PRD FR-082: casos accesibles solo por su autor; NFR-CUM-001: política de tratamiento de datos; R3: riesgo legal y reputacional por nombres en señales. Son datos personales (PII), no financieros ni de salud. |
| Escala de Usuarios | **Bajo** | POC / Essential | Brief: "validación con 3–5 usuarios"; PRD FR-083: registro **por invitación**; NFR-PER-003: "capacidad inicial de 20 usuarios concurrentes … objetivo inicial de diseño del piloto". |
| Evolución y Mantenibilidad | **Medio** | Essential / Professional | Brief: "arquitectura evolutiva … extensible a nuevas fuentes, análisis y capacidades IA"; roadmap con nuevas categorías, agente de investigación, RAG y detección proactiva; PRD NFR-EVO-001/002: nueva fuente o categoría sin rediseño. Es un producto real que se espera iterar, no un demo descartable; no es todavía el core de un negocio con equipo creciente. |
| Complejidad de Integraciones | **Medio** | **Professional** | PRD Dominios 1, 3 y 6 y Factores de complejidad: datos.gov.co/SODA (contratos `jbjy-vk9h`, archivos por año, TVEC `usqp-5nsn`/`rgxm-mmea`), descarga de documentos SECOP, Alkosto y Falabella (sitemaps + schema.org, con suspensión ante bloqueos, FR-047), proveedor de IA multimodal y correo. Protocolos mixtos (API, descarga de archivos, páginas con datos estructurados, API de IA) y dependencias externas que cambian sin aviso (R4, R6, R10). Sin sistemas legacy ni sincronización bidireccional, por eso no es Alto. |

**Factor contextual — Presión de Tiempo/Presupuesto:** **Baja presión.** Brief: "Presupuesto, costo operativo, fecha objetivo, dedicación semanal y ventana de urgencia no son restricciones de diseño en esta etapa". No hay presión que justifique bajar del tier recomendado. Según la regla de la dimensión 6, se podría considerar un tier superior, pero Premium no aporta reducción de riesgo relevante para este MVP (ver análisis). El costo variable de IA es bajo (D4: ≈ USD 0,05 por contrato con Sonnet 5.5, sin margen).

---

## Análisis Comparativo para el PO

### POC / Vibeeng

- **Gana:** máxima velocidad para mostrar el flujo de punta a punta; mínima ceremonia.
- **Pierde:**
  - Sin arquitectura limpia, lo que choca con NFR-EVO-001/002 (agregar fuentes y categorías sin rediseño).
  - Sin CI.
  - Secretos en `.env` o en el código, incompatible con NFR-SEG-006.
  - Sin pruebas de seguridad, aunque el piloto maneja cuentas y notas privadas.
  - Al iterar, exige reescritura parcial o total.
- **Veredicto:** **subdimensionado.** Sirvió como enfoque para los spikes D1, D4 y D6, pero el MVP debe desplegarse con usuarios reales, datos personales y evolución esperada.

### Essential

- **Gana:**
  - Arquitectura limpia y documentación de arquitectura, que sostienen la evolución hacia nuevas fuentes, categorías y el agente.
  - CI.
  - Pruebas unitarias de la lógica core (reglas de comparación, precio derivado, IVA, umbrales).
  - OWASP básico.
  - Variables de entorno para secretos.
  - Análisis básico de carga con IA, suficiente para 20 concurrentes.
- **Pierde:**
  - **Sin pruebas de integración del flujo crítico**, justo donde están los riesgos principales: un cambio en un dataset o en una fuente retail puede romper la cadena ingesta → extracción → señal sin que se detecte.
  - **Sin SCA** (dependencias de PDF, OCR, ZIP y clientes HTTP con vulnerabilidades conocidas).
  - **Sin vault** para las llaves del proveedor de IA.
  - **Sin logging estructurado ni health checks**, que necesitan las ingestas diarias y las capturas suspendibles.
- **Veredicto:** viable solo aceptando riesgos explícitos. Cubre bien las dimensiones 1, 3 y 4, pero **queda por debajo** de lo que piden las dimensiones 2 y 5.

### Professional

- **Gana:**
  - Todo lo de Essential.
  - **Pruebas unitarias y de integración del flujo crítico**, que dan confianza en que cada señal y su evidencia son correctas (NFR-CAL-004 a 006).
  - **SCA + OWASP**, alineado con NFR-SEG-008.
  - **Vault o gestor de secretos**.
  - **Logging estructurado y health checks**, base de NFR-OBS-002 (alerta de ingesta fallida).
  - QA manual del flujo crítico.
  - Prueba de carga del flujo crítico con un máximo de 10 concurrentes, coherente con el piloto.
  - Ambiente de desarrollo con paridad.
- **Pierde (aceptable):**
  - Sin CD automatizado: los despliegues manuales o semiautomáticos bastan para un piloto.
  - Sin pentesting ni ethical hacking.
  - Sin APM completo.
  - Ninguno de estos es un riesgo relevante para el piloto por invitación.
- **Veredicto:** **dimensionado correctamente.** Cubre el máximo de las dimensiones de riesgo sin sobreingeniería.

### Premium

- **Gana:**
  - CD totalmente automatizado.
  - Pruebas de carga completas con profiling.
  - Pentesting y ethical hacking.
  - APM con alertas y dashboards.
  - Rotación automática de secretos.
  - FinOps y GreenOps en el code review.
- **Pierde:** mayor esfuerzo y tiempo antes de llegar a usuarios reales, lo que agrava el riesgo R5 (alcance inflado) y retrasa la validación de la hipótesis (D5).
- **Veredicto:** **sobredimensionado.** No hay escala masiva, datos financieros ni de salud, SLA ni sistema transaccional. Reevaluar solo si el producto evoluciona a acceso público abierto, publicación de investigaciones o uso institucional por organismos de control.

---

## Riesgos si se Elige un Tier Inferior al Recomendado

Si se construye en **Essential** en lugar de Professional:

1. **Señales incorrectas no detectadas.** Sin pruebas de integración del flujo crítico, una regresión en la extracción, el emparejamiento o la regla de IVA puede producir una señal equivocada asociada a una entidad o un proveedor. Es el escenario de mayor impacto reputacional y legal (R2, R3), y el piloto no tiene acompañamiento jurídico permanente.
2. **Rupturas silenciosas por dependencias externas.** Los datasets de datos.gov.co, el endpoint de documentos y los datos de Alkosto y Falabella pueden cambiar sin aviso. Sin pruebas de integración ni logging estructurado, la ingesta o la captura pueden dejar de funcionar o cargar datos parciales sin alerta (NFR-OBS-002).
3. **Exposición de datos personales.** Sin SCA, las librerías de procesamiento de documentos (PDF, imágenes, ZIP) y los clientes HTTP pueden traer vulnerabilidades conocidas. Al procesar archivos de terceros, ese es un vector real. Afecta las cuentas, los casos y las notas privadas de los analistas (Ley 1581).
4. **Llaves de IA expuestas.** Con variables de entorno simples en lugar de vault, aumenta el riesgo de filtración de credenciales del proveedor de IA y de datos.gov.co.
5. **Deuda que pagará la siguiente fase.** Antes de abrir el acceso, agregar categorías o incorporar el agente habría que construir las pruebas de integración y la observabilidad que se omitieron.

**Construir en POC** suma a lo anterior la falta de arquitectura limpia, CI y seguridad básica. Sería necesario reescribir antes de cualquier evolución.

---

## Preguntas Aclaratorias Resueltas

Ninguna. Toda la información se extrajo del Brief (con Adendas 1, 2 y 3), el PRD, las épicas y los spikes D1, D4 y D6.

---

**Estado:** Aprobado (2026-10-02)
**Última actualización:** 2026-10-02
