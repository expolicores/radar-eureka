"""Dataset seed ficticio y determinístico de compras públicas de televisores (2023–2026).

Todas las entidades, proveedores, municipios, marcas y NIT son ficticios; los departamentos
son reales.
Incluye la compra de referencia del mockup (`CO1.PCCNTR.0000142`) y sus compras comparables.
La misma semilla produce siempre el mismo dataset.
"""

import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import cache

from ..domain.purchase import (
    Panel,
    Resolution,
    Source,
    SourceItem,
    SourcePurchase,
    TvAttributes,
    UnitPriceStatus,
    VatBasis,
)

SEED = 20261006
# 06-oct-2026 03:10 en Bogotá (UTC−5).
SEED_CUTOFF_AT = datetime(2026, 10, 6, 8, 10, tzinfo=UTC)
FIRST_DATE = date(2023, 1, 1)
LAST_DATE = date(2026, 10, 5)
SECOP_COUNT = 340
TVEC_COUNT = 925
TVEC_MODALITY = "Tienda Virtual del Estado — Grandes superficies"

DEPARTMENTS: dict[str, tuple[str, ...]] = {
    "Antioquia": ("Villa Nueva", "San Jerónimo del Monte", "El Retiro Alto"),
    "Valle del Cauca": ("San Rafael del Valle", "Puerto Claro", "La Cumbre Baja"),
    "Santander": ("Cerro Alto", "San Gil del Río", "Mesa Verde"),
    "Cundinamarca": ("Fusaguá", "La Vega Nueva", "Sasaima Alta"),
    "Atlántico": ("Puerto Sabana", "Galapa Norte"),
    "Bolívar": ("Turbaco Viejo", "María la Alta"),
    "Boyacá": ("Paipa del Lago", "Sogamoso Bajo"),
    "Nariño": ("Ipiales del Sur", "La Unión de Nariño"),
    "Tolima": ("Mariquita Nueva", "El Espinal Alto"),
    "Meta": ("Puerto Llano", "Acacías del Meta"),
    "Córdoba": ("Cereté Viejo", "Lorica del Mar"),
    "Huila": ("Garzón Alto", "La Plata Vieja"),
    "Caldas": ("Chinchiná Alta", "Villamaría del Sur"),
    "Bogotá D.C.": ("Bogotá D.C.",),
}

ENTITY_TEMPLATES: tuple[str, ...] = (
    "Alcaldía Municipal de {municipality}",
    "Institución Educativa {saint} de {municipality}",
    "E.S.E. Hospital {saint} de {municipality}",
    "Secretaría de Educación de {municipality}",
    "Concejo Municipal de {municipality}",
    "Personería Municipal de {municipality}",
    "Instituto Municipal de Deportes de {municipality}",
    "Gobernación de {department} — Secretaría de Salud (demo)",
    "Universidad Pública Demo — Sede {municipality}",
    "Policía Seccional Demo — {department}",
    "Registraduría Delegada Demo — {department}",
)
SAINTS = (
    "San José",
    "Santa Teresa",
    "La Esperanza",
    "Simón Bolívar",
    "Antonio Nariño",
    "La Inmaculada",
)

SUPPLIERS: tuple[tuple[str, str], ...] = (
    ("Tecnología Andina Demo S.A.S.", "900.000.142-1"),
    ("Distribuciones Norte Demo S.A.S.", "900.000.205-3"),
    ("Soluciones Visuales Demo S.A.S.", "900.000.233-8"),
    ("Electro Comercial Demo Ltda.", "900.000.251-0"),
    ("Multimedia del Sur Demo S.A.S.", "900.000.260-4"),
    ("Pantallas y Sistemas Demo S.A.S.", "900.000.311-7"),
    ("Comercializadora Caribe Demo S.A.S.", "900.000.327-2"),
    ("Audiovisuales del Pacífico Demo S.A.S.", "900.000.348-9"),
    ("Suministros Integrales Demo S.A.", "900.000.362-5"),
    ("Grupo Digital Llanero Demo S.A.S.", "900.000.379-1"),
    ("Innovación Educativa Demo S.A.S.", "900.000.384-6"),
    ("Dotaciones Institucionales Demo Ltda.", "900.000.402-3"),
)
TVEC_SUPPLIERS: tuple[tuple[str, str], ...] = (
    ("Gran Superficie Demo S.A.", "860.000.101-2"),
    ("Almacenes Éxito Demo S.A.", "860.000.115-9"),
    ("Hipermercados Andinos Demo S.A.", "860.000.128-4"),
    ("Electrohogar Nacional Demo S.A.", "860.000.139-0"),
)

BRANDS: dict[str, str] = {
    "Visionix": "VX",
    "Lumora": "LM",
    "Teknova": "TK",
    "Pantalix": "PX",
    "Orbis": "OB",
}


@dataclass(frozen=True)
class TvProfile:
    size: int
    resolution: Resolution
    panel: Panel
    base_price_cop: int  # precio unitario de referencia 2026, IVA incluido
    weight: int  # frecuencia relativa en las compras públicas


TV_PROFILES: tuple[TvProfile, ...] = (
    TvProfile(32, Resolution.HD, Panel.LED, 780_000, 8),
    TvProfile(43, Resolution.FULL_HD, Panel.LED, 1_250_000, 12),
    TvProfile(43, Resolution.UHD_4K, Panel.LED, 1_420_000, 10),
    TvProfile(50, Resolution.UHD_4K, Panel.LED, 1_780_000, 14),
    TvProfile(55, Resolution.UHD_4K, Panel.LED, 2_050_000, 16),
    TvProfile(55, Resolution.UHD_4K, Panel.QLED, 2_650_000, 6),
    TvProfile(65, Resolution.UHD_4K, Panel.LED, 2_850_000, 14),
    TvProfile(65, Resolution.UHD_4K, Panel.QLED, 3_450_000, 6),
    TvProfile(65, Resolution.UHD_4K, Panel.OLED, 5_300_000, 2),
    TvProfile(75, Resolution.UHD_4K, Panel.LED, 4_300_000, 6),
    TvProfile(75, Resolution.UHD_4K, Panel.QLED, 5_400_000, 3),
    TvProfile(85, Resolution.UHD_4K, Panel.LED, 6_900_000, 2),
)

# Los televisores bajan de precio con los años: un TV equivalente costaba más en 2023.
YEAR_FACTOR = {
    2023: Decimal("1.14"),
    2024: Decimal("1.08"),
    2025: Decimal("1.03"),
    2026: Decimal("1.00"),
}
# Base sin IVA con la que algunas fuentes publican el precio (solo para generar el dato del seed).
VAT_FACTOR = Decimal("1.19")
BASIS_POINTS = Decimal(10_000)

SECOP_MODALITIES: tuple[tuple[str, int], ...] = (
    ("Mínima cuantía", 45),
    ("Contratación directa", 18),
    ("Selección abreviada de menor cuantía", 15),
    ("Subasta inversa", 12),
    ("Régimen especial", 10),
)
SECOP_OBJECTS: tuple[str, ...] = (
    "Adquisición de televisores para las aulas de las sedes educativas",
    "Compra de televisores para las salas de espera",
    "Dotación de equipos audiovisuales (televisores) para las oficinas",
    "Suministro de televisores para el auditorio",
    "Adquisición de televisores para los programas de bienestar",
    "Compra de pantallas de televisión para la sala de crisis",
)
RESOLUTION_LABEL = {
    Resolution.HD: "HD",
    Resolution.FULL_HD: "Full HD",
    Resolution.UHD_4K: "4K UHD",
    Resolution.UHD_8K: "8K",
}
PANEL_LABEL = {Panel.LED: "LED", Panel.QLED: "QLED", Panel.OLED: "OLED"}


def _random_date(rng: random.Random) -> date:
    return FIRST_DATE + timedelta(days=rng.randrange((LAST_DATE - FIRST_DATE).days + 1))


def _weighted(rng: random.Random, options: tuple[tuple[str, int], ...]) -> str:
    return rng.choices([value for value, _ in options], weights=[weight for _, weight in options])[
        0
    ]


def _model_code(rng: random.Random, brand: str, profile: TvProfile) -> str:
    series = {Panel.LED: "U", Panel.QLED: "Q", Panel.OLED: "O"}[profile.panel]
    return f"{BRANDS[brand]}{profile.size}{series}{rng.randrange(5, 9)}{rng.choice('05')}00"


def _tv_description(profile: TvProfile, brand: str | None, model: str | None) -> str:
    text = (
        f'Televisor Smart TV {profile.size}", resolución {RESOLUTION_LABEL[profile.resolution]}, '
        f"panel {PANEL_LABEL[profile.panel]}"
    )
    if brand and model:
        text += f" · marca {brand} mod. {model}"
    return text


def _market_price(
    rng: random.Random, profile: TvProfile, signed_on: date, spread_bp: tuple[int, int]
) -> int:
    """Precio con dispersión `spread_bp` en puntos básicos (10.000 = precio de referencia)."""
    factor = Decimal(rng.randint(*spread_bp)) / BASIS_POINTS
    price = Decimal(profile.base_price_cop) * YEAR_FACTOR[signed_on.year] * factor
    return int(price.to_integral_value(ROUND_HALF_UP))


def _round(value: int, step: int) -> int:
    return max(step, (value + step // 2) // step * step)


def _entity(rng: random.Random) -> tuple[str, str, str | None]:
    department = rng.choice(list(DEPARTMENTS))
    municipality = rng.choice(DEPARTMENTS[department])
    template = rng.choice(ENTITY_TEMPLATES)
    name = template.format(
        municipality=municipality, department=department, saint=rng.choice(SAINTS)
    )
    return name, department, municipality


def _attributes(profile: TvProfile, brand: str | None, model: str | None) -> TvAttributes:
    return TvAttributes(
        screen_size_inches=profile.size,
        resolution=profile.resolution,
        panel=profile.panel,
        is_smart=True,
        brand=brand,
        model=model,
    )


def _secop_purchase(rng: random.Random, number: int) -> SourcePurchase:
    signed_on = _random_date(rng)
    entity_name, department, municipality = _entity(rng)
    natural_person = rng.random() < 0.08
    supplier_name, supplier_nit = rng.choice(SUPPLIERS)
    modality = _weighted(rng, SECOP_MODALITIES)
    items: list[SourceItem] = []
    total = 0

    if rng.random() < 0.03:
        # Contrato de servicio: no es compra de televisores, queda excluido por las reglas.
        value = _round(rng.randrange(1_500_000, 9_000_000), 10_000)
        items.append(
            SourceItem(
                1,
                "Mantenimiento preventivo y correctivo de televisores",
                None,
                None,
                UnitPriceStatus.NOT_PUBLISHED,
                VatBasis.UNDETERMINED,
            )
        )
        object_description = "Mantenimiento de televisores de la entidad"
        total = value
    else:
        profile = rng.choices(TV_PROFILES, weights=[p.weight for p in TV_PROFILES])[0]
        quantity = rng.choice((1, 1, 2, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20))
        roll = rng.random()
        if roll < 0.05:
            spread = (14_500, 19_500)  # desviación alta: generará señal
        elif roll < 0.06:
            spread = (3_000, 4_500)  # precio anormalmente bajo: revisión de calidad
        else:
            spread = (9_200, 12_200)
        unit_price = _round(_market_price(rng, profile, signed_on, spread), 1_000)
        brand = rng.choice(list(BRANDS)) if rng.random() < 0.35 else None
        model = _model_code(rng, brand, profile) if brand else None

        status_roll = rng.random()
        vat_roll = rng.random()
        vat = (
            VatBasis.INCLUDED
            if vat_roll < 0.82
            else VatBasis.EXCLUDED
            if vat_roll < 0.88
            else VatBasis.UNDETERMINED
        )
        stated_price = (
            int((Decimal(unit_price) / VAT_FACTOR).to_integral_value(ROUND_HALF_UP))
            if vat is VatBasis.EXCLUDED
            else unit_price
        )
        if spread[0] < 5_000:
            status = UnitPriceStatus.PENDING_REVIEW
        elif status_roll < 0.55:
            status = UnitPriceStatus.EXPLICIT
        elif status_roll < 0.68:
            status = UnitPriceStatus.DERIVED
        else:
            status = UnitPriceStatus.NOT_PUBLISHED
        items.append(
            SourceItem(
                1,
                _tv_description(profile, brand, model),
                quantity,
                stated_price,
                status,
                vat,
                _attributes(profile, brand, model),
            )
        )
        total += stated_price * quantity
        object_description = rng.choice(SECOP_OBJECTS)

        extra = rng.random()
        if extra < 0.18:
            accessory_price = _round(rng.randrange(90_000, 320_000), 1_000)
            items.append(
                SourceItem(
                    2,
                    f'Soporte de pared para TV {profile.size}"',
                    quantity,
                    accessory_price,
                    UnitPriceStatus.EXPLICIT,
                    vat,
                )
            )
            total += accessory_price * quantity
        elif extra < 0.26:
            service_price = _round(rng.randrange(80_000, 250_000), 1_000)
            items.append(
                SourceItem(
                    2,
                    "Instalación y configuración de los televisores",
                    quantity,
                    service_price,
                    UnitPriceStatus.EXPLICIT,
                    vat,
                )
            )
            total += service_price * quantity
        elif extra < 0.30:
            laptop_price = _round(rng.randrange(2_200_000, 3_600_000), 1_000)
            items.append(
                SourceItem(
                    2,
                    'Portátil 14" para docentes',
                    quantity,
                    laptop_price,
                    UnitPriceStatus.EXPLICIT,
                    vat,
                )
            )
            total += laptop_price * quantity
            object_description = "Dotación tecnológica: televisores y portátiles"

    return SourcePurchase(
        source=Source.SECOP_II,
        id_contrato=f"CO1.PCCNTR.{number:07d}",
        identificador_de_la_orden=None,
        proceso_de_compra=f"CO1.REQ.{number + 3_100_000:07d}",
        entity_name=entity_name,
        entity_department=department,
        entity_municipality=municipality,
        supplier_name=supplier_name,
        # Un documento real nunca llega aquí; el de persona natural tampoco se guarda (dominio).
        supplier_nit=None if natural_person else supplier_nit,
        supplier_is_natural_person=natural_person,
        object_description=object_description,
        modality=modality,
        total_value_cop=total,
        signed_on=signed_on,
        source_url=None,
        items=tuple(items),
    )


def _tvec_purchase(rng: random.Random, number: int) -> SourcePurchase:
    signed_on = _random_date(rng)
    entity_name, department, municipality = _entity(rng)
    supplier_name, supplier_nit = rng.choice(TVEC_SUPPLIERS)
    profile = rng.choices(TV_PROFILES, weights=[p.weight for p in TV_PROFILES])[0]
    brand = rng.choice(list(BRANDS))
    model = _model_code(rng, brand, profile)
    quantity = rng.choice((1, 1, 1, 2, 2, 3, 4, 5, 6, 10))
    spread = (14_000, 16_000) if rng.random() < 0.012 else (8_600, 10_600)
    unit_price = _round(_market_price(rng, profile, signed_on, spread), 100)
    description = (
        f'TV {profile.size}" {RESOLUTION_LABEL[profile.resolution]} '
        f"{PANEL_LABEL[profile.panel]} Smart "
        f"· {brand} mod. {model}"
    )
    item = SourceItem(
        1,
        description,
        quantity,
        unit_price,
        UnitPriceStatus.EXPLICIT,
        VatBasis.INCLUDED,
        _attributes(profile, brand, model),
    )
    return SourcePurchase(
        source=Source.TVEC,
        id_contrato=None,
        identificador_de_la_orden=str(number),
        proceso_de_compra=None,
        entity_name=entity_name,
        entity_department=department,
        entity_municipality=municipality,
        supplier_name=supplier_name,
        supplier_nit=supplier_nit,
        supplier_is_natural_person=False,
        object_description=(
            f'TV {profile.size}" {RESOLUTION_LABEL[profile.resolution]} Smart ×{quantity}'
        ),
        modality=TVEC_MODALITY,
        total_value_cop=unit_price * quantity,
        signed_on=signed_on,
        source_url=None,
        items=(item,),
    )


def _reference_purchases() -> list[SourcePurchase]:
    """Compra de referencia del mockup y sus 14 compras comparables (65", 4K, LED, Smart)."""
    profile = TvProfile(65, Resolution.UHD_4K, Panel.LED, 0, 0)
    reference = SourcePurchase(
        source=Source.SECOP_II,
        id_contrato="CO1.PCCNTR.0000142",
        identificador_de_la_orden=None,
        proceso_de_compra="CO1.REQ.0031026",
        entity_name="Alcaldía Municipal de San Rafael del Valle",
        entity_department="Valle del Cauca",
        entity_municipality="San Rafael del Valle",
        supplier_name="Tecnología Andina Demo S.A.S.",
        supplier_nit="900.000.142-1",
        supplier_is_natural_person=False,
        object_description=(
            "Adquisición de televisores para las aulas de las sedes educativas del municipio"
        ),
        modality="Mínima cuantía",
        total_value_cop=39_600_000,
        signed_on=date(2026, 8, 14),
        source_url=None,
        items=(
            SourceItem(
                1,
                'Televisor Smart TV 65", resolución 4K UHD, panel LED, Wi-Fi y Bluetooth',
                8,
                4_950_000,
                UnitPriceStatus.EXPLICIT,
                VatBasis.INCLUDED,
                _attributes(profile, None, None),
            ),
            SourceItem(
                2,
                'Soporte de pared para TV 55"–75"',
                8,
                None,
                UnitPriceStatus.NOT_PUBLISHED,
                VatBasis.INCLUDED,
            ),
        ),
    )
    comparables = (
        (
            2_350_000,
            Source.TVEC,
            "Instituto Departamental de Ejemplo",
            "Antioquia",
            date(2026, 3, 12),
        ),
        (
            2_480_000,
            Source.SECOP_II,
            "Alcaldía Municipal de Villa Nueva",
            "Antioquia",
            date(2026, 3, 28),
        ),
        (
            2_550_000,
            Source.TVEC,
            "Policía Seccional Demo — Santander",
            "Santander",
            date(2026, 4, 9),
        ),
        (2_610_000, Source.TVEC, "Registraduría Delegada Demo — Meta", "Meta", date(2026, 4, 22)),
        (
            2_690_000,
            Source.SECOP_II,
            "Institución Educativa Simón Bolívar de Cerro Alto",
            "Santander",
            date(2026, 5, 5),
        ),
        (
            2_750_000,
            Source.TVEC,
            "Gobernación de Ejemplo — Secretaría de Educación",
            "Boyacá",
            date(2026, 5, 18),
        ),
        (2_820_000, Source.SECOP_II, "Hospital Regional del Norte", "Atlántico", date(2026, 6, 2)),
        (2_900_000, Source.TVEC, "Secretaría de Salud Demo", "Huila", date(2026, 6, 16)),
        (
            2_980_000,
            Source.SECOP_II,
            "Alcaldía Municipal de Puerto Claro",
            "Valle del Cauca",
            date(2026, 6, 30),
        ),
        (3_050_000, Source.TVEC, "Ministerio Demo — Regional Caribe", "Bolívar", date(2026, 7, 11)),
        (
            3_150_000,
            Source.SECOP_II,
            "Universidad Pública Demo — Sede Cereté Viejo",
            "Córdoba",
            date(2026, 7, 24),
        ),
        (3_290_000, Source.TVEC, "Fiscalía Seccional Demo — Tolima", "Tolima", date(2026, 8, 5)),
        (
            3_400_000,
            Source.SECOP_II,
            "Alcaldía Municipal de Cerro Alto",
            "Santander",
            date(2026, 8, 19),
        ),
        (3_600_000, Source.SECOP_II, "Concejo Distrital Demo", "Bogotá D.C.", date(2026, 9, 1)),
    )
    purchases = [reference]
    for index, (price, source, entity, department, signed_on) in enumerate(comparables):
        quantity = 2 + index % 4
        description = 'Televisor Smart TV 65", resolución 4K UHD, panel LED'
        item = SourceItem(
            1,
            description,
            quantity,
            price,
            UnitPriceStatus.EXPLICIT,
            VatBasis.INCLUDED,
            _attributes(profile, None, None),
        )
        is_secop = source is Source.SECOP_II
        supplier_name, supplier_nit = (SUPPLIERS if is_secop else TVEC_SUPPLIERS)[(index + 1) % 4]
        purchases.append(
            SourcePurchase(
                source=source,
                id_contrato=f"CO1.PCCNTR.{200 + index:07d}" if is_secop else None,
                identificador_de_la_orden=None if is_secop else str(166_000 + index),
                proceso_de_compra=f"CO1.REQ.{40_000 + index:07d}" if is_secop else None,
                entity_name=entity,
                entity_department=department,
                entity_municipality=None,
                supplier_name=supplier_name,
                supplier_nit=supplier_nit,
                supplier_is_natural_person=False,
                object_description=(
                    "Adquisición de televisores de 65 pulgadas"
                    if is_secop
                    else f'TV 65" 4K UHD Smart ×{quantity}'
                ),
                modality="Mínima cuantía" if is_secop else TVEC_MODALITY,
                total_value_cop=price * quantity,
                signed_on=signed_on,
                source_url=None,
                items=(item,),
            )
        )
    return purchases


@cache
def generate_seed_purchases() -> tuple[SourcePurchase, ...]:
    rng = random.Random(SEED)  # noqa: S311 — datos de demostración, no criptografía
    purchases = _reference_purchases()
    secop_numbers = rng.sample(range(1_000, 990_000), SECOP_COUNT)
    tvec_numbers = rng.sample(range(100_000, 165_000), TVEC_COUNT)
    purchases.extend(_secop_purchase(rng, number) for number in secop_numbers)
    purchases.extend(_tvec_purchase(rng, number) for number in tvec_numbers)
    return tuple(purchases)
