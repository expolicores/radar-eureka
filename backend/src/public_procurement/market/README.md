# Módulo `market`

Observaciones de precio de mercado (retail) para el Benchmark 2. Es dueño del esquema PostgreSQL `market`.

## Responsabilidades

- **Registro mínimo trazable** de cada observación (FR-042): tienda, referencia de origen, producto, marca/modelo, EAN, tamaño, resolución, panel, precio efectivo (y precio anterior solo como evidencia), base de IVA, vendedor, condiciones especiales, fecha y método de adquisición.
- **Histórico inmutable** (FR-053): solo inserción; una observación ya registrada (tienda + referencia) nunca se sobrescribe.
- Las reglas de uso (solo vendedor = la tienda, sin condiciones especiales, ventana de ±30 días) las aplica `comparison` al calcular el Benchmark 2.

## Capas

| Archivo | Rol |
| ------- | --- |
| `domain/observation.py` | Observación, tienda, método, base de IVA |
| `ports.py` | `RetailObservationSource` |
| `adapters/seed.py` | Observaciones **simuladas** (método `simulated`) para la demo |
| `repositories.py` | Tabla `market.observation` y consultas |
| `services.py` | Carga y lectura; única puerta de entrada |

## Pendiente para el producto real

Captura permitida de Alkosto y Falabella (sitemap / datos estructurados, con límites y suspensión), carga manual con evidencia y usuario (FR-048…FR-051) y carga por CSV (FR-052).
