import pytest

from public_procurement.ingestion.domain.classification import ItemClassification, classify_item


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ('Televisor Smart TV 65" 4K UHD', ItemClassification.INCLUDED),
        ("TV LED 43 pulgadas Full HD", ItemClassification.INCLUDED),
        ('Televisor 55" con soporte de pared incluido', ItemClassification.INCLUDED),
        ('Dotación: TV 50" y portátiles', ItemClassification.INCLUDED),
        ('Soporte de pared para TV 55"–75"', ItemClassification.EXCLUDED_ACCESSORY),
        ("Control remoto para televisor", ItemClassification.EXCLUDED_ACCESSORY),
        ("Mantenimiento de televisores", ItemClassification.EXCLUDED_SERVICE),
        ("Instalación de televisores en aulas", ItemClassification.EXCLUDED_SERVICE),
        ("Pantalla 4K para gimnasio", ItemClassification.UNDETERMINED),
        ('Portátil 14"', ItemClassification.UNDETERMINED),
        ("", ItemClassification.UNDETERMINED),
    ],
)
def test_classify_item_returns_expected_classification_when_description_is_given(
    description: str, expected: ItemClassification
) -> None:
    # Arrange / Act
    classification = classify_item(description)
    # Assert
    assert classification is expected
