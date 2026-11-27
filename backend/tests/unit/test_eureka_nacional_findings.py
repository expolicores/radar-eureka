"""Offline tests for the EN-01 findings presentation layer. Synthetic documents modeled on
the structure of stored invitations; no entity-, municipality- or process-specific rules."""

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules
import eureka_nacional_findings as findings

LIST_WITHOUT_EXPERIENCE = """2.8 REQUISITOS DE ORDEN TÉCNICO DE LAS PROPUESTAS:
El proponente deberá aportar la descripción técnica de los elementos.
2.9 REQUISITOS HABILITANTES
Serán requisitos habilitantes del presente proceso de selección los siguientes:
2.9.2 REQUISITOS HABILITANTES QUE DEBERÁ APORTAR EL OFERENTE CON LA OFERTA
a) Índice general de la propuesta debidamente foliado.
b) Certificado de antecedentes disciplinarios.
c) Certificado de antecedentes fiscales.
d) Carta de presentación de la propuesta, según anexo 1.
e) Fotocopia de la cédula del representante legal.
f) Registro Único Tributario.
1. Objeto social de la persona jurídica: se verificará que esté autorizada.
g) Pago de aportes al sistema de seguridad social.
h) Pacto de integridad según anexo 6.
2.10 VALIDEZ MÍNIMA DE LA OFERTA
Las propuestas deberán tener una validez mínima de quince días."""

LETTERED_LIST = """14. DESIGNACION DE INTEGRANTES PARA LA VERIFICACION DE REQUISITOS HABILITANTES
Verificación de los requisitos habilitantes jurídicos y documentos de la propuesta:
A. REQUISITOS HABILITANTES:
1. Certificado de existencia y representación legal.
2. Diligenciar el FORMATO No. 01. Carta de presentación de la propuesta.
3. Documento de conformación del consorcio o unión temporal.
4. Diligenciar el FORMATO No. 4. Declaración de inhabilidades.
5. Certificación de pagos de aportes parafiscales. FORMATO No. 5
6. Registro Único Tributario actualizado.
B. PROPUESTA TÉCNICA:
El proponente presentará la ficha técnica."""


def fragment(text, page=1):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": "native_pdf_text"}
    )


def document(pages, role="primary", identifier="1", name=None, complete=True, **extra):
    return {
        "document_id": identifier,
        "name": name or f"{role}.pdf",
        "role": role,
        "complete": complete,
        "pages_seen": list(range(1, len(pages) + 1)) if complete else [],
        "total_pages": len(pages) if complete else None,
        "fragments": [fragment(text, page) for page, text in enumerate(pages, start=1)],
        **extra,
    }


def assess(documents, **kwargs):
    classification = rules.classify_experience(copy.deepcopy(documents))
    return classification, findings.assess_finding(classification, documents, **kwargs)


def study(identifier="2"):
    return document(["ESTUDIOS PREVIOS\nDescripción de la necesidad."], "support", identifier)


def test_closed_list_without_experience_is_priority_review_without_changing_status():
    # Arrange: list split across two pages, closed by the next sibling heading.
    head, tail = LIST_WITHOUT_EXPERIENCE.split("e) Fotocopia")
    invitation = document([head, "e) Fotocopia" + tail])

    # Act
    classification, finding = assess([invitation, study()])

    # Assert
    assert classification["status"] == "not_resolved"
    assert finding["formal_status"] == "not_resolved"
    assert finding["category"] == "priority_review"
    assert finding["label"] == "Hallazgo prioritario para revisión"
    assert finding["basis"] == "closed_habilitating_list_without_experience"
    [section] = finding["habilitating_sections"]
    assert section["closed"]
    assert section["apparently_exhaustive"]
    assert section["pages"] == [1, 2]
    assert section["terminator"].startswith("2.10 VALIDEZ")
    assert section["experience_terms"] == []
    assert section["item_count"] >= 8
    assert {"anexo 1", "anexo 6"} <= set(section["annex_references"])
    assert "Carta de presentación" in section["excerpt"]


def test_pending_study_keeps_the_process_visible_as_uncertain():
    invitation = document([LIST_WITHOUT_EXPERIENCE])
    pending_study = {**study(), "complete": False, "fragments": []}

    _, finding = assess([invitation, pending_study])

    assert finding["category"] == "uncertain"
    assert finding["visible"] is True
    assert finding["basis"] == "closed_list_with_unverified_documents"
    assert "documentos_no_verificados_por_el_sistema" in finding["warnings"]


def test_non_governing_pending_documents_do_not_lower_priority():
    invitation = document([LIST_WITHOUT_EXPERIENCE])
    cdp = document([], "unknown", "3", name="CDP", complete=False)

    _, finding = assess([invitation, study(), cdp])

    assert finding["category"] == "priority_review"
    assert finding["coverage"]["non_governing_pending"] == ["CDP"]


def test_lettered_list_with_unprocessable_format_stays_uncertain_with_human_annotation():
    # Arrange: list closed by the next letter heading; the formats package is not processable.
    invitation = document([LETTERED_LIST])
    formats = document(
        [], "support", "3", name="FORMATOS", complete=False, validation_gap="formato_no_procesable"
    )
    reviews = [
        {
            "identifiers": ["CO1.NTC.0001"],
            "observation": "no_experience_requirement_found",
            "documents_reviewed": ["FORMATOS"],
            "system_verified": False,
        }
    ]
    documents = [invitation, study(), formats]

    # Act
    classification, finding = assess(documents, identifiers=["CO1.NTC.0001"], human_reviews=reviews)
    _, without_review = assess(documents, identifiers=["CO1.NTC.0001"], human_reviews=[])

    # Assert
    assert classification["status"] == "not_resolved"
    [section] = finding["habilitating_sections"]
    assert section["closed"]
    assert section["terminator"].startswith("B. PROPUESTA")
    assert finding["category"] == without_review["category"] == "uncertain"
    assert finding["human_review"] == reviews
    assert finding["human_review_changes_category"] is False
    assert finding["coverage"]["not_verified_by_system"] == [
        {"document": "FORMATOS", "role": "support", "reason": "formato_no_procesable"}
    ]
    assert {d["document"] for d in finding["coverage"]["system_verified"]} == {
        "primary.pdf",
        "support.pdf",
    }


def test_section_not_closed_in_read_text_is_not_priority():
    unclosed = LIST_WITHOUT_EXPERIENCE.split("2.10 VALIDEZ")[0]

    _, finding = assess([document([unclosed]), study()])

    assert finding["category"] == "uncertain"
    assert finding["basis"] == "no_closed_habilitating_list"
    assert "lista_habilitante_no_cerrada_en_texto_leido" in finding["warnings"]


def test_uppercase_items_continuing_the_list_do_not_close_it_early():
    text = "\n".join(
        [
            "5. REQUISITOS HABILITANTES",
            "1. CARTA DE PRESENTACIÓN DE LA PROPUESTA",
            "2. REGISTRO ÚNICO TRIBUTARIO",
            "3. CERTIFICADO DE ANTECEDENTES FISCALES",
            "4. CERTIFICADO DE ANTECEDENTES DISCIPLINARIOS",
            "5. CÉDULA DEL REPRESENTANTE LEGAL",
            "6. PAGO DE APORTES PARAFISCALES",
            "7. CERTIFICACIONES DE CONTRATOS EJECUTADOS",
            "6. FORMA DE PAGO",
            "El pago se hará contra entrega.",
        ]
    )

    _, finding = assess([document([text]), study()])

    [section] = finding["habilitating_sections"]
    assert section["closed"]
    assert section["terminator"].startswith("6. FORMA DE PAGO")
    assert section["experience_terms"]
    assert finding["category"] != "priority_review"


def test_capacity_terms_in_the_list_prevent_priority():
    text = LIST_WITHOUT_EXPERIENCE.replace(
        "f) Registro Único Tributario.", "f) Indicadores financieros de capacidad financiera."
    )

    _, finding = assess([document([text]), study()])

    assert finding["category"] == "uncertain"
    assert "lista_habilitante_menciona_experiencia_o_capacidad" in finding["warnings"]


def test_explicit_requirement_is_still_experience_required():
    text = LIST_WITHOUT_EXPERIENCE + (
        "\n3. EXPERIENCIA DEL PROPONENTE\nEl proponente deberá acreditar experiencia en dos "
        "contratos ejecutados cuyo objeto sea similar."
    )

    classification, finding = assess([document([text]), study()])

    assert classification["status"] == "experience_required"
    assert finding["category"] == "experience_required"


def test_experience_inside_the_list_is_never_priority_even_without_formal_conclusion():
    text = LIST_WITHOUT_EXPERIENCE.replace(
        "f) Registro Único Tributario.",
        "f) El proponente deberá acreditar experiencia en contratos ejecutados similares.",
    )

    classification, finding = assess([document([text]), study()])

    assert classification["status"] == "not_resolved"
    assert finding["category"] == "uncertain"
    assert finding["basis"] == "habilitating_list_mentions_experience"


def test_formal_waiver_is_confirmed():
    text = LIST_WITHOUT_EXPERIENCE + "\nNo se exige experiencia contractual al proponente."

    classification, finding = assess([document([text]), study()])

    assert classification["status"] == "no_experience_required"
    assert finding["category"] == "confirmed"


def test_prose_mention_of_verification_is_not_a_section():
    text = "Se designa a quien realizará la verificación de los requisitos habilitantes."

    _, finding = assess([document([text]), study()])

    assert finding["habilitating_sections"] == []
    assert finding["category"] == "uncertain"
    assert "sin_lista_habilitante_detectada" in finding["warnings"]


def test_wrapped_prose_starting_with_the_heading_words_is_not_a_section():
    text = "\n".join(
        [
            "El comité verificará el cumplimiento de los",
            "requisitos habilitantes y evaluará las ofertas recibidas:",
            "a) Revisión de documentos.",
            "b) Verificación de precios.",
            "c) Publicación del informe.",
            "2.14 EXPEDICIÓN DE ADENDAS:",
        ]
    )

    _, finding = assess([document([text]), study()])

    assert finding["habilitating_sections"] == []
    assert finding["category"] == "uncertain"


def test_assessment_never_mutates_the_classification():
    documents = [document([LIST_WITHOUT_EXPERIENCE]), study()]
    classification = rules.classify_experience(copy.deepcopy(documents))
    snapshot = copy.deepcopy(classification)

    findings.assess_finding(classification, documents)

    assert classification == snapshot


def test_every_category_is_visible():
    cases = [
        [document([LIST_WITHOUT_EXPERIENCE]), study()],
        [document(["Sin secciones."])],
        [document([], complete=False)],
    ]

    for documents in cases:
        _, finding = assess(documents)
        assert finding["visible"] is True


def test_repository_human_reviews_are_annotations_only():
    reviews = findings.load_human_reviews()

    assert reviews
    assert all(review["system_verified"] is False for review in reviews)
    assert findings.human_reviews_for(["CO1.NTC.11284005"], reviews)
    assert findings.human_reviews_for(["secop1:26-13-14851414"], reviews)
