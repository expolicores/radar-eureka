# Asunciones Parciales — ÉPICA-007: Espacio de Investigación del Analista

**Fecha:** 2026-10-02 | **Autor:** Juan Camilo (PO) | **Total de asunciones:** 22

> Supuestos resueltos durante la generación de las HU de esta épica (IDs temporales). El consolidador los integrará al archivo global de asunciones.

| Asunción | Categoría | HUs Relacionadas (IDs temporales) | Impacto | Estado |
|---|---|---|---|---|
| La invitación tiene vigencia configurable, valor inicial 7 días (rango 1 a 30) | Seguridad | HU-084, HU-085 | Medio | Resuelta |
| Reinvitar un correo con invitación pendiente reemplaza la anterior (máximo una pendiente por correo) | Negocio | HU-084 | Bajo | Resuelta |
| El Administrador puede revocar invitaciones pendientes | Negocio | HU-084, HU-085 | Bajo | Resuelta |
| Las invitaciones solo crean cuentas Analista; los Administradores se aprovisionan por procedimiento técnico, sin pantalla, y siempre debe existir al menos uno | Seguridad | HU-084, HU-089 | Medio | Resuelta |
| No se emiten invitaciones ni se habilita el registro sin versión vigente publicada de la política de datos (y de los términos, para el registro) | Negocio | HU-084, HU-085 | Alto | Resuelta |
| Política de contraseña: mínimo configurable inicial 10, máximo 128, distinta del correo, sin reglas de composición | Seguridad | HU-085, HU-088, HU-089 | Medio | Resuelta |
| El registro pide solo nombre visible (2 a 80 caracteres) además de correo y contraseña (minimización de datos) | Datos | HU-085 | Bajo | Resuelta |
| La aceptación de términos y política se registra con versión, fecha, hora y medio; la reaceptación ante nuevas versiones queda fuera (no está en FR-087) | Negocio | HU-085 | Medio | Resuelta |
| Tras registrarse o restablecer la contraseña no hay inicio de sesión automático | UI-UX | HU-085, HU-088 | Bajo | Resuelta |
| Bloqueo temporal configurable ante intentos fallidos (5 intentos en 15 min, 15 min de bloqueo), con mensaje genérico | Seguridad | HU-086 | Medio | Resuelta |
| Página de inicio tras login: lista priorizada de señales; se permiten sesiones simultáneas | UI-UX | HU-086 | Bajo | Resuelta |
| Expiración por inactividad configurable (inicial 30, rango 5 a 480 min) con aviso previo configurable (inicial 2 min); solo cuentan acciones del usuario | Seguridad | HU-087 | Medio | Resuelta |
| Enlace de restablecimiento: 60 min configurable, de un solo uso, máximo 3 solicitudes por hora; el cambio cierra todas las sesiones y se avisa por correo | Seguridad | HU-088 | Medio | Resuelta |
| El Administrador puede usar funciones de investigación sobre sus propios casos, pero no accede a casos ajenos | Seguridad | HU-089, HU-097 | Alto | Resuelta |
| Funciones sin grupo declarado en la matriz de permisos se tratan como administrativas | Seguridad | HU-089 | Bajo | Resuelta |
| El caso tiene título (3 a 120) con sugerencia automática y descripción opcional (hasta 1.000) | UI-UX | HU-090, HU-091, HU-092 | Bajo | Resuelta |
| Contenido de la instantánea de señal, contrato y evidencia definido desde FR-065, FR-074, FR-075 y FR-024; datos ausentes como "No disponible" | Datos | HU-090, HU-091, HU-092, HU-096 | Alto | Resuelta |
| "Contrato" incluye órdenes de compra TVEC con ficha; las señales del contrato se resumen en su instantánea sin guardarse como elementos de señal | Negocio | HU-091 | Medio | Resuelta |
| "Evidencia" es el documento de origen de un dato o una observación de referencia de un benchmark; sin duplicados en un mismo caso; máximo configurable de 100 elementos por caso | Negocio | HU-092 | Medio | Resuelta |
| Renombrar o eliminar casos, quitar elementos y buscar dentro de "Mis casos" no están en los FRs y quedan fuera del MVP | Negocio | HU-090, HU-092, HU-095 | Medio | Resuelta |
| Notas de texto plano, 1 a 5.000 caracteres, máximo configurable 200 por caso, eliminación definitiva sin historial, con control de edición concurrente | UI-UX | HU-093, HU-094 | Bajo | Resuelta |
| Casos ajenos e inexistentes reciben la misma respuesta ("No encontramos este caso."); identificadores aleatorios; indicadores sobre casos solo agregados | Seguridad | HU-095, HU-096, HU-097 | Alto | Resuelta |
