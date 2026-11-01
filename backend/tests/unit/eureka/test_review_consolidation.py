"""Read-model equivalence is supported by exact persisted provider references."""

import copy
from datetime import timedelta

from .test_human_review import NOW, observation, service


def pair(n=1):
    local, official = f"licitaciones_info:1086005:{n}", f"secop1:26-13-{100 + n}"
    old = observation(n, id_ultima_fase=None, process_reference=local, key_config="secopI")
    new = observation(
        n,
        id_ultima_fase=None,
        source_identity=official,
        process_reference=local,
        key_config="secopI",
        provider_source="secop1",
    )
    new["run_at"] = NOW + timedelta(hours=1)
    return local, official, old, new


def test_exact_provider_reference_merges_history_assessments_alert_and_oldest_date():
    local, official, old, new = pair()
    new["result"]["manual_review_reasons"] = ["source_metadata_review", "missing_documents"]
    svc, repo, _ = service([old, new])
    repo.data["ratings"] = {
        local: {
            "review_first_seen_at": NOW - timedelta(days=1),
            "review_first_seen_origin": "observed",
            "manual_rating": "high",
            "manual_note": "Historical human note",
            "reviewed_at": NOW,
        },
        official: {
            "review_first_seen_at": NOW,
            "review_first_seen_origin": "observed",
            "manual_rating": "medium",
            "manual_note": "Current human note",
            "reviewed_at": NOW + timedelta(hours=2),
        },
    }
    repo.data["alerts"] = [{"id": "alert", "canonical_identity": local, "snapshot": {}}]
    before = copy.deepcopy(repo.data)
    rows = svc.rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["canonical_identity"] == official
    assert set(row["equivalent_identities"]) == {local, official}
    assert {h["observed_identity"] for h in row["history"]} == {local, official}
    assert len(row["history"]) == 2
    assert row["review_first_seen_at"] == NOW - timedelta(days=1)
    assert row["manual_rating"] == "medium"
    assert row["manual_note"] == "Current human note"
    assert {a["manual_note"] for a in row["manual_assessments"]} == {
        "Historical human note",
        "Current human note",
    }
    assert row["has_alert"]
    assert row["alert_ids"] == ["alert"]
    assert svc.list({})["total"] == 0
    assert svc.list({"include_excluded": True, "has_alert": True})["total"] == 0
    assert row["manual_review_reasons"] == ["missing_documents"]
    assert not any("Fuente distinta" in message for message in row["review_explanations"])
    assert svc.get(local)["canonical_identity"] == official
    assert repo.data == before


def test_no_equivalence_from_similar_code_object_or_different_provider_reference():
    _, _, old, new = pair()
    new["result"]["metadata"]["process_reference"] = "licitaciones_info:1086005:999"
    svc, _, _ = service([old, new])
    assert svc.list({})["total"] == 2


def test_ambiguous_provider_reference_never_equates_ntc_req_or_distinct_official_ids():
    _, _, old, new = pair()
    other = copy.deepcopy(new)
    other["result"]["metadata"]["source_identity"] = "secop1:26-13-999"
    svc, _, _ = service([old, new, other])
    assert svc.list({})["total"] == 3


def test_secop_ii_exact_reference_is_supported_without_ntc_req_inference():
    local, _, old, new = pair()
    new["result"]["metadata"]["source_identity"] = "CO1.NTC.123"
    svc, _, _ = service([old, new])
    row = svc.list({})["items"][0]
    assert row["canonical_identity"] == "secop:CO1.NTC.123"
    assert local in row["equivalent_identities"]
    assert svc.list({})["total"] == 1


def test_sort_and_pagination_after_consolidation_and_no_source_reason():
    local, official, old, new = pair()
    other = observation(2)
    svc, repo, _ = service([old, new, other])
    repo.data["ratings"] = {
        local: {"review_first_seen_at": NOW - timedelta(days=1)},
        official: {"review_first_seen_at": NOW + timedelta(days=1)},
        "secop:CO1.NTC.2": {"review_first_seen_at": NOW},
    }
    assert svc.list({"page_size": 1})["items"][0]["canonical_identity"] == "secop:CO1.NTC.2"
    row = svc.list({"page_size": 1, "page": 2})["items"][0]
    assert row["canonical_identity"] == official
    assert row["manual_review_reasons"] == []
    assert row["no_alert_reason"] == "Diferido por límite de procesamiento"
    assert row["review_explanations"] == ["Diferido por límite de procesamiento"]
    assert not row["requires_manual_document_review"]
