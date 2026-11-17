"""Versioned research contracts; monetary arithmetic uses Decimal."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class ProductIdentity(BaseModel):
    brand: str = Field(min_length=2)
    model: str = Field(min_length=4, pattern=r"^[A-Za-z0-9-]+$")
    canonical_model: str | None = None
    product_type: str | None = None
    size: str | None = None
    capacity: str | None = None
    dimensions: str | None = None
    product_family: str | None = None
    expected_domain_id: str | None = None
    expected_catalog_product_id: str | None = None
    relevant_attributes: dict[str, str] = Field(default_factory=dict)

    @field_validator("model")
    @classmethod
    def specific_model(cls, value: str) -> str:
        if not any(c.isdigit() for c in value) or not any(c.isalpha() for c in value):
            raise ValueError("Se requiere referencia específica")
        return value.upper()


class PublicPriceEvidence(ProductIdentity):
    public_process_identity: str = Field(min_length=1)
    public_process_code: str = Field(min_length=1)
    public_entity: str = Field(min_length=1)
    public_product_description: str = Field(min_length=1)
    public_unit_price: Decimal = Field(gt=0, allow_inf_nan=False)
    public_price_date: datetime | None = None
    public_evidence_ref: str = Field(min_length=1)
    public_document: str = Field(min_length=1)
    public_page_reference: str = Field(min_length=1)
    price_origin: Literal["explicit", "calculated"]
    price_tax_basis: Literal["unknown", "excludes_vat", "includes_vat"] = "unknown"
    evidence_warnings: list[str] = Field(default_factory=list)
    public_document_url: HttpUrl | None = None
    contract_identifier: str | None = None
    supplier: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    item_total: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    evidence_text: str | None = None
    document_heading_process_code: str | None = None

    @model_validator(mode="after")
    def preserve_document_conflicts(self) -> Self:
        if (
            self.document_heading_process_code
            and self.document_heading_process_code.strip().casefold()
            != self.public_process_code.strip().casefold()
            and "document_process_reference_mismatch" not in self.evidence_warnings
        ):
            self.evidence_warnings.append("document_process_reference_mismatch")
        return self

    @field_validator("public_price_date")
    @classmethod
    def aware_date(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("La fecha pública requiere zona horaria")
        return value


class PublicProduct(PublicPriceEvidence):
    public_price_stage: Literal["contract", "awarded", "accepted_offer"]
    public_price_date: datetime = Field(...)


class PublicOffer(PublicPriceEvidence):
    """Documented offer, never promoted implicitly to purchase evidence."""

    public_price_stage: Literal["offer"] = "offer"


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: HttpUrl
    query: str
    captured_at: datetime
    search_provider: str
    provider_reference: str | None = None
    source_urls: list[HttpUrl] = Field(default_factory=list)


class ApiEvidence(BaseModel):
    source: Literal["mercadolibre", "serpapi"] = "mercadolibre"
    site_id: Literal["MCO"] | None = "MCO"
    endpoint: str
    captured_at: datetime
    response: dict[str, object]


class PageEvidence(BaseModel):
    kind: Literal["direct_page"] = "direct_page"
    candidate: SearchResult | ApiEvidence
    final_url: HttpUrl
    captured_at: datetime
    http_status: int
    content_sha256: str
    extracted_fields: dict[str, object]
    evidence_text: str
    extraction_sources: list[str]


class RejectionReason(StrEnum):
    WRONG_MODEL = "wrong_model"
    WRONG_SIZE = "wrong_size"
    WRONG_PRODUCT_TYPE = "wrong_product_type"
    WRONG_BRAND = "wrong_brand"
    ACCESSORY_OR_REPLACEMENT = "accessory_or_replacement"
    GENERIC_PAGE = "generic_page"
    NO_PRICE = "no_price"
    AMBIGUOUS_PRICE = "ambiguous_price"
    CURRENCY_UNKNOWN = "currency_unknown"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    STALE_OR_CACHE_ONLY = "stale_or_cache_only"
    VERIFICATION_FAILED = "verification_failed"


class MarketObservation(BaseModel):
    retailer: str
    market_product_title: str
    brand: str | None
    model: str | None
    price: Decimal | None
    currency: str | None = "COP"
    availability: Literal["available", "unavailable", "unknown"] = "unknown"
    url: HttpUrl
    captured_at: datetime
    source_type: Literal["web_search", "marketplace_api", "shopping_provider"] = "web_search"
    source: str = "web_search"
    discovery_method: str = "deterministic"
    extraction_method: str = "search_snippet"
    price_evidence_level: Literal[
        "api_verified_price", "page_verified_price", "shopping_provider_price", "snippet_price"
    ] = "snippet_price"
    verification_status: Literal[
        "not_attempted", "verified", "rejected", "blocked", "failed", "weak"
    ] = "not_attempted"
    rejection_reason: RejectionReason | None = None
    marketplace: str | None = None
    listing_id: str | None = None
    seller_id: str | None = None
    seller_name: str | None = None
    official_store_id: str | None = None
    catalog_product_id: str | None = None
    product_id: str | None = None
    shipping: str | dict[str, object] | None = None
    currency_inferred: bool = False
    provider_metadata: dict[str, object] = Field(default_factory=dict)
    domain_id: str | None = None
    web_source_kind: (
        Literal["retailer_web", "marketplace_web", "manufacturer_web", "other_web"] | None
    ) = None
    condition: str | None = None
    provider_status: str | None = None
    available_quantity_reference: int | None = None
    duplicate_of: str | None = None
    page_type: str = "unknown"
    discovery_score: int = 0
    discovered_queries: list[str] = Field(default_factory=list)
    match_level: Literal["exact", "high", "partial", "reject"]
    match_reason: str
    promotion_detected: bool = False
    notes: list[str] = Field(default_factory=list)
    evidence: SearchResult | ApiEvidence | PageEvidence
    valid_for_benchmark: bool = False


class PrivateMarketBenchmark(BaseModel):
    brand: str
    model: str
    captured_at: datetime
    benchmark_status: Literal["ready", "insufficient_market_evidence"]
    valid_observations_count: int
    retailers_count: int
    observations_count: int = 0
    independent_sources_count: int = 0
    distinct_sellers_count: int = 0
    evidence_sufficiency: Literal[
        "sufficient_diverse_market_evidence",
        "marketplace_concentrated_evidence",
        "insufficient_market_evidence",
        "limited_source_diversity",
    ] = "insufficient_market_evidence"
    duplicates: list[MarketObservation] = Field(default_factory=list)
    min_price: Decimal | None
    median_price: Decimal | None
    max_price: Decimal | None
    confidence: float
    observations: list[MarketObservation]
    limitations: list[str]


class PublicVsPrivateComparison(BaseModel):
    public_process_identity: str
    public_entity: str
    brand: str
    model: str
    public_unit_price: Decimal
    public_price_stage: str
    public_price_date: datetime
    public_evidence_ref: str
    private_min_price: Decimal
    private_median_price: Decimal
    private_max_price: Decimal
    valid_market_observations: int
    retailers_count: int
    market_captured_at: datetime
    time_gap_days: Decimal
    absolute_difference: Decimal
    percentage_difference: Decimal
    confidence: float
    limitations: list[str]
