# ÉPICA-007: Espacio de Investigación del Analista

**Volver a:** [Índice de Épicas](../../epicas.md)

---

## Resumen

Permite al analista convertir señales en investigaciones: crear casos, guardar señales, contratos y evidencias, escribir notas y retomar el trabajo después. Los casos son privados y guardan una instantánea de la evidencia, de modo que no cambian si se recalculan los benchmarks.

Incluye el registro por invitación, inicio y cierre de sesión (con expiración configurable por inactividad, inicial 30 minutos), recuperación de contraseña, roles Analista/Administrador y la aceptación de términos de uso y de la política de tratamiento de datos personales (Ley 1581 de 2012), que son requisitos de la decisión de acceso con login.

**Prioridad:** Crítica  
**FRs cubiertos:** FR-077, FR-078, FR-079, FR-080, FR-081, FR-082, FR-083, FR-084, FR-085, FR-086, FR-087  
**Total HU:** 14 historias  
**Estado:** ✅ Generadas y Aprobadas

---

## Features y Historias de Usuario

### Feature 1: Gestionar Acceso por Invitación

- [HU-084: Emitir invitación de registro para un Analista](./HU-084-emitir-invitacion-registro-analista/historia.md)
- [HU-085: Registrar cuenta de Analista mediante invitación con aceptación de términos y política de datos](./HU-085-registrar-cuenta-analista-por-invitacion/historia.md)

### Feature 2: Autenticar y Proteger la Sesión

- [HU-086: Iniciar sesión con correo y contraseña](./HU-086-iniciar-sesion-correo-contrasena/historia.md)
- [HU-087: Cerrar sesión y expirar la sesión por inactividad](./HU-087-cerrar-sesion-y-expirar-por-inactividad/historia.md)
- [HU-088: Recuperar la contraseña por correo electrónico](./HU-088-recuperar-contrasena-por-correo/historia.md)
- [HU-089: Aplicar los roles Analista y Administrador con permisos diferenciados](./HU-089-aplicar-roles-analista-administrador/historia.md)

### Feature 3: Crear y Organizar Casos de Investigación

- [HU-090: Crear un caso de investigación desde una señal](./HU-090-crear-caso-desde-senal/historia.md)
- [HU-091: Crear un caso de investigación desde un contrato](./HU-091-crear-caso-desde-contrato/historia.md)
- [HU-092: Guardar señales, contratos y evidencias en un caso existente](./HU-092-guardar-elementos-en-caso-existente/historia.md)

### Feature 4: Documentar Casos con Notas

- [HU-093: Agregar notas a un caso](./HU-093-agregar-nota-a-caso/historia.md)
- [HU-094: Editar y eliminar notas de un caso](./HU-094-editar-y-eliminar-notas-de-caso/historia.md)

### Feature 5: Consultar y Retomar Casos Propios

- [HU-095: Listar mis casos de investigación](./HU-095-listar-mis-casos/historia.md)
- [HU-096: Abrir y retomar un caso con su evidencia conservada como instantánea](./HU-096-abrir-y-retomar-caso-con-instantanea/historia.md)
- [HU-097: Restringir el acceso a casos, elementos y notas únicamente a su autor](./HU-097-restringir-acceso-casos-a-su-autor/historia.md)

---

## Matriz de Trazabilidad

| HU | FR | Rol Principal | Valor de Negocio |
|---|---|---|---|
| HU-084 | FR-083, FR-086 | Administrador | Solo personas autorizadas acceden al piloto, sin registro público |
| HU-085 | FR-083, FR-087 | Analista invitado | Alta controlada de analistas con autorización verificable de tratamiento de datos (Ley 1581) |
| HU-086 | FR-084 | Analista | Acceso con login al espacio privado de investigación |
| HU-087 | FR-084 | Analista | Protege casos y notas en equipos desatendidos (expiración configurable, inicial 30 min) |
| HU-088 | FR-085 | Analista | Recupera el acceso sin depender del Administrador |
| HU-089 | FR-086 | Administrador | Separa operación y revisión de datos del uso por analistas piloto |
| HU-090 | FR-077, FR-081 | Analista | Convierte una señal en una investigación persistente con evidencia inmutable |
| HU-091 | FR-077, FR-081 | Analista | Inicia investigaciones desde la exploración de contratos |
| HU-092 | FR-078, FR-081 | Analista | Reúne señales, contratos y evidencias del caso como instantáneas |
| HU-093 | FR-079 | Analista | Registra hipótesis y próximos pasos en el caso |
| HU-094 | FR-079 | Analista | Mantiene las notas del caso vigentes |
| HU-095 | FR-080, FR-082 | Analista | Encuentra y retoma investigaciones propias |
| HU-096 | FR-080, FR-081 | Analista | Retoma el caso con la evidencia intacta tras recálculos |
| HU-097 | FR-082 | Analista | Confidencialidad de las investigaciones verificada al 100 % |

---

## Exclusiones Explícitas de Esta Épica

- NO incluye casos compartidos ni colaboración entre analistas.
- NO incluye login social (Google, Microsoft) ni SSO.
- NO incluye exportación del expediente (candidata, ÉPICA-009).
- NO incluye publicación de casos ni un canal de denuncia a entes de control.

---

**Última actualización:** 2026-10-02  
**Generado por:** Workflow generar-historias-usuario

> **Método Ceiba generar hus** v6.1.95 | Modelo: claude-opus-5-5 | Usuario: Juan Camilo | Fecha: 2026-10-02
