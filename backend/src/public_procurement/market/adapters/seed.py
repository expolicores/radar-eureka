"""Adaptador seed del puerto `RetailObservationSource`: observaciones de mercado SIMULADAS.

Los precios son ficticios; cada observación queda marcada con el método `simulated`.
Lo reemplazan la captura permitida (sitemap / datos estructurados) y la carga manual.
"""

import random
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import cache

from ..domain.observation import AcquisitionMethod, MarketObservation, MarketVatBasis, Store

SEED = 20261007
FIRST_DATE = date(2023, 1, 3)
LAST_DATE = date(2026, 10, 5)
BASIS_POINTS = Decimal(10_000)
YEAR_FACTOR = {
    2023: Decimal("1.14"),
    2024: Decimal("1.08"),
    2025: Decimal("1.03"),
    2026: Decimal("1.00"),
}
# Probabilidad de que una tienda no tenga observación en una fecha (huecos de la captura).
GAP_PROBABILITY = {Store.ALKOSTO: Decimal("0.35"), Store.FALABELLA: Decimal("0.65")}
BRANDS = {"Visionix": "VX", "Lumora": "LM", "Teknova": "TK", "Pantalix": "PX", "Orbis": "OB"}
RESOLUTION_LABEL = {"hd": "HD", "full_hd": "Full HD", "uhd_4k": "4K UHD"}
PANEL_LABEL = {"led": "LED", "qled": "QLED", "oled": "OLED"}


@dataclass(frozen=True)
class RetailProfile:
    size: int
    resolution: str
    panel: str
    reference_price_cop: int  # precio efectivo de referencia en 2026, IVA incluido


RETAIL_PROFILES: tuple[RetailProfile, ...] = (
    RetailProfile(32, "hd", "led", 799_900),
    RetailProfile(43, "full_hd", "led", 1_299_900),
    RetailProfile(43, "uhd_4k", "led", 1_499_900),
    RetailProfile(50, "uhd_4k", "led", 1_899_900),
    RetailProfile(55, "uhd_4k", "led", 2_199_900),
    RetailProfile(55, "uhd_4k", "qled", 2_799_900),
    RetailProfile(65, "uhd_4k", "led", 3_099_900),
    RetailProfile(65, "uhd_4k", "qled", 3_599_900),
    RetailProfile(65, "uhd_4k", "oled", 5_699_900),
    RetailProfile(75, "uhd_4k", "led", 4_599_900),
    RetailProfile(75, "uhd_4k", "qled", 5_799_900),
    RetailProfile(85, "uhd_4k", "led", 7_299_900),
)


def _retail_price(rng: random.Random, profile: RetailProfile, observed_on: date) -> int:
    """Precio «terminado en 900», como suele publicarse en retail."""
    factor = Decimal(rng.randint(9_000, 10_800)) / BASIS_POINTS
    price = Decimal(profile.reference_price_cop) * YEAR_FACTOR[observed_on.year] * factor
    rounded = int((price / 100_000).to_integral_value(ROUND_HALF_UP)) * 100_000
    return max(rounded - 100, 99_900)


def _observation(
    rng: random.Random, store: Store, profile: RetailProfile, observed_on: date, sequence: int
) -> MarketObservation:
    brand = rng.choice(list(BRANDS))
    series = {"led": "U", "qled": "Q", "oled": "O"}[profile.panel]
    model = f"{BRANDS[brand]}{profile.size}{series}{rng.randrange(5, 9)}000"
    price = _retail_price(rng, profile, observed_on)
    return MarketObservation(
        store=store,
        source_reference=f"SIM-{store.value.upper()}-{sequence:06d}",
        product_description=(
            f'TV {profile.size}" {RESOLUTION_LABEL[profile.resolution]} '
            f"{PANEL_LABEL[profile.panel]} Smart · {brand} mod. {model}"
        ),
        brand=brand,
        model=model,
        ean=None,
        screen_size_inches=profile.size,
        resolution=profile.resolution,
        panel=profile.panel,
        effective_price_cop=price,
        list_price_cop=price + 300_000 if rng.random() < 0.3 else None,
        vat_basis=MarketVatBasis.INCLUDED,
        # Vendedores terceros y precios con condiciones especiales se registran y se descartan.
        seller_is_store=rng.random() >= 0.05,
        has_special_conditions=rng.random() < 0.05,
        observed_on=observed_on,
        method=AcquisitionMethod.SIMULATED,
    )


@cache
def generate_seed_observations() -> tuple[MarketObservation, ...]:
    rng = random.Random(SEED)  # noqa: S311 — datos de demostración, no criptografía
    observations: list[MarketObservation] = []
    sequence = 0
    for store in Store:
        for profile in RETAIL_PROFILES:
            observed_on = FIRST_DATE + timedelta(days=rng.randrange(0, 10))
            while observed_on <= LAST_DATE:
                if Decimal(rng.randint(0, 99)) / 100 >= GAP_PROBABILITY[store]:
                    sequence += 1
                    observations.append(_observation(rng, store, profile, observed_on, sequence))
                observed_on += timedelta(days=rng.randrange(14, 29))
    return tuple(observations)


class SeedRetailObservationSource:
    def fetch_observations(self) -> Iterable[MarketObservation]:
        return generate_seed_observations()
