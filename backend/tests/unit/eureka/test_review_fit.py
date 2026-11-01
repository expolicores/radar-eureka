import copy
from decimal import Decimal

import pytest
from sqlalchemy import select

from public_procurement.eureka import review_fit as fit_module
from public_procurement.eureka.review_cleanup import cleanup_plan, execute_cleanup
from public_procurement.eureka.review_policy import admission, default_config
from public_procurement.eureka.review_repositories import ManualProcessReviewRecord
from public_procurement.eureka.review_services import project

from .test_human_review import NOW, observation, service
from .test_review_admission_cleanup import cleanup_db as cleanup_db_fixture

cleanup_db = cleanup_db_fixture  # register the shared isolated SQL fixture

LEGAL_OBJECT = (
    "BRINDAR ASISTENCIA JURÍDICA DENTRO DE LAS DIFERENTES ACTUACIONES ADMINISTRATIVAS "
    "REQUERIDAS EN EL DESARROLLO Y EJECUCION DEL PROYECTO FORTALECIMIENTO DE "
    "INSTRUMENTOS; HERRAMIENTAS Y PROCESOS DE PLAN"
)


def test_reported_legal_false_positive_is_not_hardware_even_with_score_and_ocr_warning():
    item = observation(source="socrata", object=LEGAL_OBJECT)["result"]
    item.update(decision={"snapshot": {"score": 80}}, coverage_incomplete=True)
    result = admission(item)
    assert not result["review_candidate"]
    assert result["review_fit_rejected_reason"] == "review_rejected_irrelevant_service"


@pytest.mark.parametrize("amount", [100000001, "199906000", Decimal("158754963"), 500137849])
def test_over_100_million_is_out_of_review_even_with_real_goods_or_document_warning(amount):
    item = observation(amount=amount)["result"]
    item.update(coverage_incomplete=True, decision={"snapshot": {"score": 99}})
    assert admission(item)["review_rejected_reason"] == "review_rejected_budget_limit"


@pytest.mark.parametrize("amount", [100000000, "5785850", None])
def test_actual_goods_up_to_limit_or_unknown_amount_remain_candidates(amount):
    item = observation(object="Compra de impresora y suministro de tóner", amount=amount)["result"]
    assert admission(item)["review_candidate"]


@pytest.mark.parametrize(
    "text",
    [
        "CONSTRUCCIÓN DEL NUEVO POZO PROFUNDO",
        "ELABORACIÓN DE ESTUDIOS Y DISEÑOS DE INFRAESTRUCTURA",
        "PRESTAR SERVICIOS LOGÍSTICOS EN LA CELEBRACIÓN DEL DÍA DE LA FAMILIA",
        "CAPACITACION EOT",
        "PRESTACIÓN DE SERVICIO DE ALQUILER DE IMPRESORAS",
        "MANTENIMIENTO PREVENTIVO Y CORRECTIVO DE COMPUTADORES E IMPRESORAS",
    ],
)
def test_no_goods_intent_is_not_rescued_by_incidental_keywords_or_score(text):
    item = observation(object=text)["result"]
    item["decision"] = {"snapshot": {"score": 35}}
    assert not admission(item)["review_candidate"]


@pytest.mark.parametrize(
    "text",
    [
        "SUMINISTRO DE BIENES PARA LA CELEBRACIÓN DEL DÍA DULCE DE LA NIÑEZ",
        "SUMINISTRO DE PAPELERÍA Y ÚTILES DE OFICINA",
        "ELEMENTOS DE FERRETERIA PARA EL MANTENIMIENTO LOCATIVO",
        "COMPRA DE COMPUTADOR PORTÁTIL",
        "Adquirir material didáctico y pedagógico",
        "SERVICIO DE DISEÑO E IMPRESIÓN DE PAPELERÍA TIMBRADA",
        "Compra de papelería para la oficina de asesoría jurídica",
    ],
)
def test_real_goods_and_supported_physical_fulfillment_are_not_lost(text):
    assert admission(observation(object=text)["result"])["review_candidate"]


def test_review_budget_limit_is_configurable_without_changing_scoring(monkeypatch):
    policy = fit_module.load_review_fit_config()
    monkeypatch.setattr(
        fit_module,
        "load_review_fit_config",
        lambda: policy.model_copy(update={"max_amount_cop": 50000000}),
    )
    assert not admission(observation(amount=60000000)["result"])["review_candidate"]


def test_latest_amount_and_object_cannot_be_rescued_by_old_eligible_history():
    first = observation()
    latest = copy.deepcopy(first)
    latest["result"]["metadata"].update(amount=230000000, object=LEGAL_OBJECT)
    svc, repo, _ = service([first, latest])
    assert svc.list({})["total"] == 0
    row = svc.list({"include_excluded": True})["items"][0]
    assert row["review_fit_rejected_reason"] == "review_rejected_budget_limit"
    assert len(repo.data["observations"]) == 2


def test_fit_cleanup_preserves_human_work_and_external_alerts(
    cleanup_db,
):
    sessions, _, _ = cleanup_db
    rows = [observation(n, amount=200000000) for n in (1, 2)]
    for obs in rows:
        obs["result"].update(manual_review_reasons=["missing_documents"], coverage_incomplete=True)
    with sessions.begin() as s:
        s.get(ManualProcessReviewRecord, "secop:CO1.NTC.2").manual_note = "Conservar trabajo humano"

    def rebuild():
        with sessions() as s:
            from public_procurement.eureka.review_repositories import ReviewRepository

            ratings = {
                r.canonical_identity: ReviewRepository.rating(r)
                for r in s.scalars(select(ManualProcessReviewRecord))
            }
        data = {
            "observations": rows,
            "ratings": ratings,
            "opportunities": {},
            "alerts": [
                {"id": "existing-alert", "canonical_identity": "secop:CO1.NTC.1", "snapshot": {}}
            ],
        }
        return cleanup_plan(data, project(data, {}, NOW))

    plan = rebuild()
    assert [r["identity"] for r in plan["delete"]] == ["secop:CO1.NTC.1"]
    assert plan["protected_count"] == 1
    assert execute_cleanup(sessions, plan, rebuild)["deleted"] == 1
    with sessions() as s:
        assert (
            s.get(ManualProcessReviewRecord, "secop:CO1.NTC.2").manual_note
            == "Conservar trabajo humano"
        )


def test_existing_commercial_catalog_and_water_term_are_unchanged():
    catalog = default_config()
    food = next(f for f in catalog.families if f.category == "packaged_food")
    assert "agua" in food.terms
