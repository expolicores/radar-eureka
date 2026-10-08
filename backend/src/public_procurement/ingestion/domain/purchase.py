"""Compras públicas de televisores: contratos SECOP II y órdenes TVEC con sus ítems."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from .classification import ItemClassification, classify_item

__all__ = [
    "NATURAL_PERSON_SUPPLIER_NAME",
    "IngestionRunResult",
    "ItemClassification",
    "Panel",
    "Purchase",
    "PurchaseItem",
    "Resolution",
    "Source",
    "SourceItem",
    "SourcePurchase",
    "TvAttributes",
    "UnitPriceStatus",
    "VatBasis",
    "build_purchase",
]


class Source(StrEnum):
    SECOP_II = "secop_ii"
    TVEC = "tvec"


class UnitPriceStatus(StrEnum):
    EXPLICIT = "explicit"
    DERIVED = "derived"
    NOT_PUBLISHED = "not_published"
    PENDING_REVIEW = "pending_review"


class VatBasis(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    UNDETERMINED = "undetermined"


class Resolution(StrEnum):
    HD = "hd"
    FULL_HD = "full_hd"
    UHD_4K = "uhd_4k"
    UHD_8K = "uhd_8k"


class Panel(StrEnum):
    LED = "led"
    QLED = "qled"
    OLED = "oled"


NATURAL_PERSON_SUPPLIER_NAME = "Persona natural — documento no visible"


@dataclass(frozen=True)
class TvAttributes:
    screen_size_inches: int | None = None
    resolution: Resolution | None = None
    panel: Panel | None = None
    is_smart: bool | None = None
    brand: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class SourceItem:
    """Ítem tal como lo entrega la fuente (con atributos ya extraídos)."""

    line_number: int
    description: str
    quantity: int | None
    unit_price_cop: int | None
    unit_price_status: UnitPriceStatus
    vat_basis: VatBasis
    attributes: TvAttributes = field(default_factory=TvAttributes)


@dataclass(frozen=True)
class SourcePurchase:
    """Compra tal como la entrega la fuente.

    `id_contrato` e `identificador_de_la_orden` llegan sin transformar.
    """

    source: Source
    id_contrato: str | None
    identificador_de_la_orden: str | None
    proceso_de_compra: str | None
    entity_name: str
    entity_department: str
    entity_municipality: str | None
    supplier_name: str
    supplier_nit: str | None
    supplier_is_natural_person: bool
    object_description: str
    modality: str
    total_value_cop: int | None
    signed_on: date
    source_url: str | None
    items: tuple[SourceItem, ...]


@dataclass(frozen=True)
class PurchaseItem:
    line_number: int
    description: str
    classification: ItemClassification
    quantity: int | None
    unit_price_cop: int | None
    unit_price_status: UnitPriceStatus
    vat_basis: VatBasis
    attributes: TvAttributes


@dataclass(frozen=True)
class Purchase:
    source: Source
    id_contrato: str | None
    identificador_de_la_orden: str | None
    proceso_de_compra: str | None
    entity_name: str
    entity_department: str
    entity_municipality: str | None
    supplier_name: str
    supplier_nit: str | None
    supplier_is_natural_person: bool
    object_description: str
    modality: str
    total_value_cop: int | None
    signed_on: date
    source_url: str | None
    items: tuple[PurchaseItem, ...]

    @property
    def source_record_id(self) -> str:
        """Identificador de origen de la compra en su fuente."""
        identifier = (
            self.id_contrato if self.source is Source.SECOP_II else self.identificador_de_la_orden
        )
        if identifier is None:
            raise ValueError("purchase_without_source_identifier")
        return identifier

    @property
    def display_reference(self) -> str:
        """Referencia para mostrar: `id_contrato` en SECOP II, «Orden N» en TVEC."""
        if self.source is Source.TVEC:
            return f"Orden {self.source_record_id}"
        return self.source_record_id

    @property
    def has_tv_items(self) -> bool:
        return any(item.classification is ItemClassification.INCLUDED for item in self.items)


@dataclass(frozen=True)
class IngestionRunResult:
    source: Source
    started_at: datetime
    finished_at: datetime
    cutoff_at: datetime
    read_count: int
    new_count: int
    updated_count: int


def build_item(item: SourceItem) -> PurchaseItem:
    # Sin precio publicado no hay precio: nunca un valor por defecto.
    unit_price = (
        None if item.unit_price_status is UnitPriceStatus.NOT_PUBLISHED else item.unit_price_cop
    )
    return PurchaseItem(
        line_number=item.line_number,
        description=item.description,
        classification=classify_item(item.description),
        quantity=item.quantity,
        unit_price_cop=unit_price,
        unit_price_status=item.unit_price_status,
        vat_basis=item.vat_basis,
        attributes=item.attributes,
    )


def build_purchase(record: SourcePurchase) -> Purchase:
    """Construye la compra del dominio: clasifica ítems y aplica las reglas de privacidad."""
    if record.source is Source.SECOP_II and not record.id_contrato:
        raise ValueError("secop_purchase_without_id_contrato")
    if record.source is Source.TVEC and not record.identificador_de_la_orden:
        raise ValueError("tvec_purchase_without_identificador_de_la_orden")
    natural_person = record.supplier_is_natural_person
    return Purchase(
        source=record.source,
        id_contrato=record.id_contrato if record.source is Source.SECOP_II else None,
        identificador_de_la_orden=(
            record.identificador_de_la_orden if record.source is Source.TVEC else None
        ),
        proceso_de_compra=record.proceso_de_compra,
        entity_name=record.entity_name,
        entity_department=record.entity_department,
        entity_municipality=record.entity_municipality,
        supplier_name=NATURAL_PERSON_SUPPLIER_NAME if natural_person else record.supplier_name,
        # El documento de una persona natural es un dato L3: no entra al sistema.
        supplier_nit=None if natural_person else record.supplier_nit,
        supplier_is_natural_person=natural_person,
        object_description=record.object_description,
        modality=record.modality,
        total_value_cop=record.total_value_cop,
        signed_on=record.signed_on,
        source_url=record.source_url,
        items=tuple(build_item(item) for item in record.items),
    )
