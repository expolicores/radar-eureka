# Historia de Usuario

**Como** Analista,
**Quiero** ver la lista priorizada de señales que merecen revisión, con indicadores generales y filtros,
**Para** decidir rápidamente por cuáles compras empezar a revisar, sabiendo siempre que una señal no es una conclusión

## Descripción

Quinto *vertical slice* del MVP Beta. Expone por API las señales vigentes y sus indicadores, y construye la pantalla «Señales que merecen revisión» del mockup (página de inicio de la demo). Los servicios de consulta quedan tipados y sin HTTP, listos para exponerse como herramientas de agentes.

HUs del backlog tomadas como referencia: HU-074 (lista priorizada), HU-075 (filtros y orden), HU-083 (frescura de datos), FR-064/FR-067 (lenguaje no acusatorio y advertencia).

**No incluye:** detalle de la señal (slice 6; las filas enlazan a su ruta), calificación, reporte de error, guardado en casos.

---

## Criterios de Aceptación

### Escenario 1: Flujo Principal

- **Dado** el recálculo vigente
- **Cuando** el Analista abre «Señales»
- **Entonces** ve el aviso «Una señal no es una conclusión…», la fecha de corte, cuatro indicadores (compras de TV analizadas con su desglose SECOP II / TVEC; señales vigentes con su desglose por confianza; comparaciones incompletas —IVA no comparable o comparables insuficientes—; sin información en la fuente —sin precio unitario publicado—) y la tabla de señales con Señal (código), Ítem, Entidad compradora, Proveedor, Precio unitario, Referencia (mediana pública), Desviación, Comparación (mismo modelo / equivalente), Confianza y Fecha

### Escenario 2: Validaciones (prioridad, filtros y orden)

- **Dado** la lista de señales
- **Cuando** el Analista no elige orden
- **Entonces** se ordena por **prioridad**: confianza (alta → baja) y, dentro de cada nivel, desviación de mayor a menor; puede ordenar por desviación, valor unitario o fecha, y filtrar por texto (entidad, proveedor por nombre o NIT, ítem o código), departamento, año, fuente y confianza; los filtros quedan en la URL

### Escenario 3: Casos Extremos

- **Dado** que no hay señales que cumplan los filtros, que no se ha recalculado o que la API falla
- **Cuando** se carga la pantalla
- **Entonces** se muestra el estado vacío («No hay señales que coincidan con los filtros»), cargando o error con «Reintentar», sin datos inventados

### Escenario 4: Lenguaje

- **Dado** cualquier texto de la API o de la pantalla de señales
- **Cuando** se muestra
- **Entonces** nunca usa «sobreprecio», «corrupción», «fraude» ni «hallazgo fiscal», y la página repite que solo las desviaciones al alza generan señal y que los precios anormalmente bajos van a revisión de calidad

---

## Información Recopilada

### Usuario y Contexto

- **Tipo de usuario:** Analista.
- **Permisos requeridos:** ninguno en el MVP Beta.
- **Valor de negocio:** es la puerta de entrada de la demo: muestra el producto funcionando.

### Reglas de Negocio

- Solo señales del recálculo vigente.
- Prioridad por defecto: confianza descendente y luego desviación descendente.
- Indicadores: compras analizadas = compras con al menos un ítem de televisor; incompletas = ítems con IVA no comparable o comparables insuficientes; sin información = ítems sin precio unitario publicado.
- Página de 25, máximo 100; códigos de señal tal como los asigna el recálculo.

### Interfaz

- API: `GET /api/v1/signals`, `GET /api/v1/signals/summary`.
- Pantalla: ruta `/senales` (y la raíz de la aplicación lleva a ella); fila → `/senales/:code` (detalle, slice 6).
- Confianza: barras de 3 niveles con texto (alta/media/baja), como en el mockup.

### Sistemas Externos

Ninguno.

### Disparadores

- El Analista abre la pantalla o cambia filtros, orden o página (relanzable).

### Entidades del Dominio

- Señal que merece revisión
- Compra
- Ítem de compra

### Alcance y Continuidad

El slice 6 agrega el detalle de la señal (Benchmarks 1 y 2, confianza, evidencia) y la ficha de la compra.

### Preview de Interfaz

Mockup, sección «Señales que merecen revisión».

---

## Contexto y Referencias

**Arquitectura:** `docs/architecture/index.md`, PRD FR-064/FR-067, mockup.
**Historias relacionadas:** #5 (benchmarks y señales), #4 (marco y Explorar).

---

## Definición de Terminado (Inicial)

- [ ] Funcionalidad implementada según criterios de aceptación
- [ ] Validaciones funcionando correctamente
- [ ] Mensajes implementados
