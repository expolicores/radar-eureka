"""Median benchmark and signed comparison; no commercial decisions."""

from datetime import datetime
from decimal import Decimal
from statistics import median
from urllib.parse import urlsplit

from .matching import canonical_url
from .schemas import (
    MarketObservation,
    PrivateMarketBenchmark,
    ProductIdentity,
    PublicProduct,
    PublicVsPrivateComparison,
)
from .urls import extract_mco_listing_id as extract_mco_listing_id

TEMPORAL_LIMITATION = (
    "Benchmark privado capturado en fecha actual; no representa necesariamente el precio "
    "de mercado vigente en la fecha de la compra pública."
)


def marketplace_listing_id(observation: MarketObservation) -> str | None:
    if observation.source == "mercadolibre" and observation.listing_id:
        return observation.listing_id
    return extract_mco_listing_id(str(observation.url))


def source_group(observation: MarketObservation) -> str:
    host = urlsplit(str(observation.url)).hostname or observation.retailer
    if (
        observation.source == "mercadolibre"
        or host == "mercadolibre.com.co"
        or host.endswith(".mercadolibre.com.co")
    ):
        return "mercadolibre"
    return host.removeprefix("www.")


def aggregate(
    product: ProductIdentity, observations: list[MarketObservation], now: datetime
) -> PrivateMarketBenchmark:
    # Search/cache prices remain audit evidence even if an upstream caller marked a match valid.
    observations = [
        o.model_copy(update={"valid_for_benchmark": False})
        if o.price_evidence_level == "snippet_price"
        else o
        for o in observations
    ]
    unique: list[MarketObservation] = []
    duplicates = []
    seen: dict[tuple[str, ...], str] = {}
    sellers: dict[tuple[str, str], str] = {}
    ordered = sorted(
        observations,
        key=lambda o: (
            not o.valid_for_benchmark,
            {
                "api_verified_price": 0,
                "page_verified_price": 1,
                "shopping_provider_price": 2,
                "snippet_price": 3,
            }[o.price_evidence_level],
            -o.discovery_score,
            o.match_level != "exact",
            -o.captured_at.timestamp(),
            o.listing_id or str(o.url),
        ),
    )
    for observation in ordered:
        listing = marketplace_listing_id(observation)
        url = canonical_url(str(observation.url))
        keys: list[tuple[str, ...]] = [("url", url)]
        if listing:
            keys.append(("listing", listing))
        if (
            observation.source_type in {"web_search", "shopping_provider"}
            and observation.valid_for_benchmark
            and source_group(observation) != "mercadolibre"
        ):
            keys.append(
                (
                    "retailer_model_price",
                    source_group(observation),
                    product.model,
                    str(observation.price),
                )
            )
        previous = next((seen[k] for k in keys if k in seen), None)
        seller_key = (observation.seller_id or "", product.model)
        if (
            previous is None
            and observation.source == "mercadolibre"
            and observation.valid_for_benchmark
        ):
            previous = sellers.get(seller_key)
        if previous is not None:
            for existing in unique:
                if (existing.listing_id or canonical_url(str(existing.url))) == previous:
                    existing.discovered_queries = list(
                        dict.fromkeys(
                            [
                                *existing.discovered_queries,
                                *observation.discovered_queries,
                            ]
                        )
                    )
            duplicates.append(
                observation.model_copy(
                    update={
                        "valid_for_benchmark": False,
                        "duplicate_of": previous,
                        "notes": [*observation.notes, "duplicate_listing_or_seller"],
                    }
                )
            )
            continue
        reference = observation.listing_id or url
        for key in keys:
            seen[key] = reference
        if observation.source == "mercadolibre" and observation.valid_for_benchmark:
            sellers[seller_key] = reference
        unique.append(observation.model_copy(deep=True))
    valid = [o for o in unique if o.valid_for_benchmark and o.price is not None]
    prices = [o.price for o in valid if o.price is not None]
    groups = {source_group(o) for o in valid}
    retailers = len(groups)
    seller_count = len({o.seller_id for o in valid if o.source == "mercadolibre" and o.seller_id})
    sufficiency = "insufficient_market_evidence"
    if len(prices) >= 3:
        sufficiency = (
            "sufficient_diverse_market_evidence"
            if retailers >= 2
            else "marketplace_concentrated_evidence"
            if groups == {"mercadolibre"}
            else "limited_source_diversity"
        )
    limitations = [
        TEMPORAL_LIMITATION,
        "Precios listados por las fuentes; stock, "
        "envío, impuestos y condiciones finales de compra no verificados en checkout.",
    ]
    if len(prices) < 3:
        limitations.append("insufficient_market_evidence")
    if retailers < 3:
        limitations.append("limited_retailer_diversity")
    if sufficiency == "marketplace_concentrated_evidence":
        limitations.append("marketplace_concentrated_evidence_not_diverse_benchmark")
    if any(o.availability == "unknown" for o in valid):
        limitations.append("availability_unknown")
    return PrivateMarketBenchmark(
        brand=product.brand,
        model=product.model,
        captured_at=now,
        benchmark_status="ready" if len(prices) >= 3 else "insufficient_market_evidence",
        valid_observations_count=len(prices),
        retailers_count=retailers,
        observations_count=len(unique),
        independent_sources_count=retailers,
        distinct_sellers_count=seller_count,
        evidence_sufficiency=sufficiency,
        duplicates=duplicates,
        min_price=min(prices) if prices else None,
        median_price=median(prices) if prices else None,
        max_price=max(prices) if prices else None,
        confidence=min(0.65, len(prices) / 10, retailers / 5),
        observations=unique,
        limitations=limitations,
    )


def compare(
    product: PublicProduct, benchmark: PrivateMarketBenchmark
) -> PublicVsPrivateComparison | None:
    reference = benchmark.median_price
    if (
        benchmark.benchmark_status != "ready"
        or benchmark.evidence_sufficiency != "sufficient_diverse_market_evidence"
        or not reference
        or reference <= 0
        or benchmark.min_price is None
        or benchmark.max_price is None
    ):
        return None
    difference = product.public_unit_price - reference
    return PublicVsPrivateComparison(
        public_process_identity=product.public_process_identity,
        public_entity=product.public_entity,
        brand=product.brand,
        model=product.model,
        public_unit_price=product.public_unit_price,
        public_price_stage=product.public_price_stage,
        public_price_date=product.public_price_date,
        public_evidence_ref=product.public_evidence_ref,
        private_min_price=benchmark.min_price,
        private_median_price=reference,
        private_max_price=benchmark.max_price,
        valid_market_observations=benchmark.valid_observations_count,
        retailers_count=benchmark.retailers_count,
        market_captured_at=benchmark.captured_at,
        time_gap_days=Decimal(
            str((benchmark.captured_at - product.public_price_date).total_seconds())
        )
        / Decimal(86400),
        absolute_difference=difference,
        percentage_difference=difference / reference * 100,
        confidence=benchmark.confidence,
        limitations=benchmark.limitations,
    )
