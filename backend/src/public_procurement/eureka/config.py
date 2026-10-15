"""Catálogo, reglas de descubrimiento y perfil de ejecución versionados por separado."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Category:
    code: str
    label: str
    priority_unspsc: tuple[str, ...] = ()
    candidate_unspsc: tuple[str, ...] = ()
    product_terms: tuple[str, ...] = ()
    conditional: bool = False


@dataclass(frozen=True)
class Weights:
    product: int = 30
    priority_unspsc: int = 20
    candidate_unspsc: int = 10
    broad_need: int = 15
    entity: int = 10
    attractive_amount: int = 10
    simple_logistics: int = 10

    def __post_init__(self) -> None:
        if (
            min(
                self.product,
                self.priority_unspsc,
                self.candidate_unspsc,
                self.broad_need,
                self.entity,
                self.attractive_amount,
                self.simple_logistics,
            )
            < 0
        ):
            raise ValueError("Los pesos positivos no pueden ser negativos.")


@dataclass(frozen=True)
class Barrier:
    code: str
    label: str
    terms: tuple[str, ...]
    points: int

    def __post_init__(self) -> None:
        if self.points < 0:
            raise ValueError("Las penalizaciones no pueden ser negativas.")


@dataclass(frozen=True)
class ExecutionProfile:
    attractive_min_cop: int = 2_000_000
    attractive_max_cop: int = 8_000_000
    high_amount_from_cop: int = 15_000_000
    high_amount_penalty: int = 10
    outside_geography_penalty: int = 5
    simple_logistics: tuple[str, ...] = (
        "entrega única",
        "una sola entrega",
        "entrega puntual",
        "entrega en una sede",
        "sin instalación",
    )
    barriers: tuple[Barrier, ...] = (
        Barrier(
            "continuous_supply",
            "Abastecimiento continuo por revisar",
            ("abastecimiento continuo", "suministro continuo", "suministro permanente"),
            10,
        ),
        Barrier(
            "multiple_deliveries",
            "Múltiples entregas",
            ("múltiples entregas", "entregas parciales", "entregas periódicas"),
            10,
        ),
        Barrier(
            "specialized_installation",
            "Instalación especializada",
            ("instalación especializada", "instalación técnica"),
            15,
        ),
        Barrier(
            "specific_experience",
            "Experiencia específica por confirmar",
            ("experiencia específica", "experiencia mínima de"),
            10,
        ),
        Barrier(
            "mandatory_rup",
            "RUP obligatorio por confirmar",
            ("RUP obligatorio", "registro único de proponentes", "exige RUP"),
            15,
        ),
        Barrier(
            "high_guarantees", "Garantías altas", ("garantías altas", "pólizas de alto valor"), 10
        ),
        Barrier(
            "complex_logistics",
            "Logística compleja",
            ("logística compleja", "entrega en múltiples sedes", "cadena de frío"),
            15,
        ),
    )

    def __post_init__(self) -> None:
        if (
            min(
                self.attractive_min_cop,
                self.attractive_max_cop,
                self.high_amount_from_cop,
                self.high_amount_penalty,
                self.outside_geography_penalty,
            )
            < 0
        ):
            raise ValueError("Los parámetros de viabilidad no pueden ser negativos.")
        if self.attractive_min_cop > self.attractive_max_cop:
            raise ValueError("Intervalo atractivo inválido.")


CATALOG_V1 = (
    Category(
        "packaged_food",
        "Alimentos empacados y refrigerios",
        (
            "50192703",
            "50181903",
            "50181905",
            "50182001",
            "50192109",
            "50161800",
            "50161509",
            "50161511",
            "50201706",
            "50201709",
            "50131704",
            "50201700",
        ),
        ("50181700", "50181900", "50182000", "50192100", "50202300"),
        (
            "chocorramo",
            "ponqué",
            "galletas",
            "chocolatinas",
            "pasabocas",
            "refrigerios",
            "jugos",
            "bebidas",
        ),
    ),
    Category(
        "office_supplies",
        "Papelería y suministros de oficina",
        ("14111507", "14111519", "44122000", "44121600", "44122018"),
        ("14111500", "44121700", "44122100"),
        ("papelería", "resmas", "tóner", "toner", "tintas"),
    ),
    Category(
        "basic_technology",
        "Tecnología básica",
        (),
        ("52161505", "43211503", "43212105", "43211700", "45111616"),
        ("impresoras", "televisores", "pantallas", "monitores"),
    ),
    Category(
        "cleaning_cafeteria",
        "Aseo y cafetería",
        (),
        ("47131800", "47131600", "47131700", "14111705"),
        ("aseo", "cafetería"),
    ),
    Category(
        "printing_customization",
        "Impresión y personalización",
        (),
        ("82121500", "82121900", "55121700", "53103000"),
        ("camisetas", "estampados", "stickers", "señalética"),
    ),
    Category(
        "furniture_supplies",
        "Mobiliario y suministros variados",
        (),
        ("56101504",),
        ("sillas", "archivadores"),
    ),
    Category(
        "prepared_snacks",
        "Refrigerios preparados (condicional)",
        (),
        ("90101600",),
        ("refrigerios preparados", "alimentos preparados"),
        conditional=True,
    ),
)


@dataclass(frozen=True)
class DiscoveryConfig:
    version: str = "eureka-discovery-v1"
    catalog: tuple[Category, ...] = CATALOG_V1
    weights: Weights = field(default_factory=Weights)
    execution: ExecutionProfile = field(default_factory=ExecutionProfile)
    departments: tuple[str, ...] = ("Boyacá", "Casanare")
    high_priority_from: int = 60
    medium_priority_from: int = 35
    broad_terms: tuple[str, ...] = (
        "suministro de elementos",
        "materiales y útiles de oficina",
        "adquisición de bienes",
        "dotación institucional",
        "material didáctico",
        "elementos de apoyo logístico",
        "materiales para actividades",
        "suministro por demanda",
        "elementos de funcionamiento",
    )
    need_terms: tuple[str, ...] = (
        "día del colegio",
        "comunidad educativa",
        "actividades académicas",
        "actividades culturales",
        "celebración",
        "conmemoración",
        "actividades deportivas",
        "torneos",
        "jornadas deportivas",
        "encuentros",
        "capacitación",
        "reuniones institucionales",
        "bienestar estudiantil",
        "integración",
        "reconocimientos",
        "funcionamiento de dependencias",
        "apoyo a la gestión documental",
    )
    entity_terms: tuple[str, ...] = (
        "institución educativa",
        "I.E.",
        "sede rural",
        "personería",
        "concejo municipal",
        "alcaldía",
        "secretaría",
        "establecimiento penitenciario",
        "INPEC",
        "expendio",
        "hospital",
        "E.S.E.",
        "ESE",
    )
    exclusions: tuple[Barrier, ...] = (
        Barrier(
            "construction",
            "Obra o construcción compleja",
            ("construcción de", "obra civil", "ejecución de obra", "obra pública", "obra compleja"),
            15,
        ),
        Barrier("consulting", "Consultoría especializada", ("consultoría especializada",), 15),
        Barrier("supervision", "Interventoría", ("interventoría",), 15),
        Barrier(
            "professional_services", "Servicios profesionales", ("servicios profesionales",), 15
        ),
        Barrier(
            "management_services",
            "Apoyo a la gestión sin bienes",
            (
                "prestación de servicios de apoyo a la gestión",
                "servicios de apoyo a la gestión",
                "apoyo a la gestión sin bienes",
            ),
            15,
        ),
        Barrier(
            "custom_software",
            "Desarrollo de software a medida",
            ("software a medida", "desarrollo de software"),
            15,
        ),
    )
    terminal_terms: tuple[str, ...] = (
        "vencido",
        "cerrado",
        "cancelado",
        "adjudicado",
        "adjudicación",
        "terminado",
        "evaluación",
        "desierto",
        "finalizado",
    )

    def __post_init__(self) -> None:
        if not self.version or len(self.version) > 64:
            raise ValueError("La versión de reglas debe tener entre 1 y 64 caracteres.")
        if not 0 <= self.medium_priority_from < self.high_priority_from:
            raise ValueError("Umbrales de prioridad inválidos.")
        if self.execution.attractive_min_cop > self.execution.attractive_max_cop:
            raise ValueError("Intervalo de cuantía atractiva inválido.")
        if len({category.code for category in self.catalog}) != len(self.catalog):
            raise ValueError("Categorías comerciales repetidas.")


DEFAULT_CONFIG = DiscoveryConfig()
