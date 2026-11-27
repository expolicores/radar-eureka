"""Offline tests for the blind department-scoped exploration: geography subset, explicit
not-selected reasons and the funnel report. Synthetic data only."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "scripts"), str(HERE)]

import eureka_nacional_blind_report as report_module  # noqa: E402
import eureka_nacional_en01 as en01  # noqa: E402
import test_eureka_nacional_secop1_flow as stage1  # noqa: E402
from spike_licitaciones_info import SpikeError  # noqa: E402

SUBSET = en01.DEFAULT_GEOGRAPHY.with_name(
    "eureka_nacional_geography_boyaca_huila(from_licitaciones_info).v1.json"
)


def national_ids():
    return en01.load_national_locations()


# ---------------------------------------------------------------- geography subset


def test_versioned_subset_is_exactly_boyaca_and_huila_from_the_national_capture():
    # Arrange / Act
    ids, scope = en01.load_geography(SUBSET)

    # Assert
    national = national_ids()
    assert ids == tuple(i for i in national if i[:4] in {"4006", "4017"})
    assert len(ids) == 160
    assert scope["department_codes"] == {"4006": "Boyacá", "4017": "Huila"}
    assert scope["expected_departments"] == ["Boyacá", "Huila"]


def test_national_geography_is_unchanged():
    ids, scope = en01.load_geography(en01.DEFAULT_GEOGRAPHY)

    assert scope is None
    assert ids == national_ids()


def write_subset(tmp_path, mutate):
    config = json.loads(SUBSET.read_text(encoding="utf-8"))
    mutate(config)
    national = tmp_path / en01.DEFAULT_GEOGRAPHY.name
    national.write_bytes(en01.DEFAULT_GEOGRAPHY.read_bytes())
    path = tmp_path / SUBSET.name
    path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c["location_ids"].pop(),  # a municipality missing
        lambda c: c["location_ids"].append("40020001"),  # another department
        lambda c: c.update(location_count=c["location_count"] + 1),
        lambda c: c.update(derived_from_sha256="0" * 64),
        lambda c: c.update(expected_departments=["Boyacá", "Tolima"]),
        lambda c: c.update(department_codes={"4006": "Boyacá"}),
        lambda c: c.update(source="otro"),
    ],
)
def test_subset_that_is_not_derived_from_the_capture_is_rejected(tmp_path, mutate):
    with pytest.raises(SpikeError, match="departamental"):
        en01.load_geography(write_subset(tmp_path, mutate))


def run_scoped(tmp_path, monkeypatch, rows_extra):
    ids, scope = en01.load_geography(SUBSET)
    original = en01.run

    def scoped_run(client, args, settings, output, **kwargs):
        args.geography_scope = scope
        return original(client, args, settings, output, locations=ids, **kwargs)

    monkeypatch.setattr(en01, "run", scoped_run)
    try:
        return stage1.run_stage1(tmp_path, monkeypatch, include=True, secop1_rows=rows_extra)
    finally:
        monkeypatch.setattr(en01, "run", original)


def test_rows_from_other_departments_are_excluded_and_counted(tmp_path, monkeypatch):
    # Arrange: the stage-1 fixture has SECOP II rows in Boyacá and Bogotá.
    rows = [stage1.secop1_discovery_row(91, "Huila", "26-13-11111111")]

    # Act
    _, output, calls, _ = run_scoped(tmp_path, monkeypatch, rows)

    # Assert
    processes = stage1.report(output, "processes.json")
    by_department = {p["department"]: p for p in processes["processes"]}
    assert by_department["Bogotá"]["excluded_reason"] == "outside_geography_scope"
    assert by_department["Boyacá"]["excluded_reason"] is None
    assert by_department["Huila"]["excluded_reason"] is None
    assert processes["geography"]["scope"] == "departments"
    assert processes["geography"]["location_count"] == 160
    feed = [p for path, p in calls if path != stage1.DOCUMENT_ENDPOINT]
    filter_ids = feed[0]["query"]["ubicacion_filter"].split(",")
    assert len(filter_ids) == 160
    assert (
        processes["geography"]["ubicacion_filter_sha256"]
        == hashlib.sha256(",".join(filter_ids).encode("ascii")).hexdigest()
    )
    by_source = stage1.report(output, "metrics.json")["by_source"]
    assert by_source["secop2"]["excluded_by_reason"]["outside_geography_scope"] == 1


def test_not_selected_reason_names_the_quota(tmp_path, monkeypatch):
    rows = [stage1.secop1_discovery_row(90 + n, "Boyacá", f"26-13-1111111{n}") for n in range(4)]

    def limited(tmp, mp):
        def wrapped(client, args, settings, output, **kwargs):
            args.secop1_processes = 2
            return real(client, args, settings, output, **kwargs)

        real = en01.run
        mp.setattr(en01, "run", wrapped)
        try:
            return stage1.run_stage1(tmp, mp, include=True, secop1_rows=rows)
        finally:
            mp.setattr(en01, "run", real)

    _, output, _, _ = limited(tmp_path, monkeypatch)
    processes = stage1.report(output, "processes.json")["processes"]
    secop1 = [p for p in processes if p["source"] == "secop1"]
    assert sum(p["sampled"] for p in secop1) == 2
    assert [p["not_selected_reason"] for p in secop1 if not p["sampled"]] == [
        "secop1_selection_quota",
        "secop1_selection_quota",
    ]
    by_source = stage1.report(output, "metrics.json")["by_source"]
    assert by_source["secop1"]["eligible_not_selected"] == 2


# ---------------------------------------------------------------- funnel report


def result(reference, status, review, pages=()):
    return {
        "process_reference": reference,
        "status": status,
        "review_category": review,
        "review_evidence": [{"page": p} for p in pages],
    }


def synthetic_run(tmp_path):
    run = tmp_path / "en01-blind"
    run.mkdir()
    processes = [
        {
            "process_reference": "a",
            "source": "secop2",
            "excluded_reason": None,
            "sampled": True,
            "source_identity": "CO1.NTC.1",
            "department": "Boyacá",
        },
        {
            "process_reference": "b",
            "source": "secop2",
            "excluded_reason": None,
            "sampled": True,
            "source_identity": "CO1.NTC.2",
            "department": "Huila",
        },
        {
            "process_reference": "c",
            "source": "secop2",
            "excluded_reason": None,
            "sampled": False,
            "not_selected_reason": "secop2_selection_quota",
        },
        {
            "process_reference": "d",
            "source": "secop2",
            "excluded_reason": "outside_commercial_profile",
            "sampled": False,
        },
        {
            "process_reference": "e",
            "source": "secop1",
            "excluded_reason": None,
            "sampled": True,
            "source_identity": "secop1:26-13-1",
            "department": "Huila",
        },
        {
            "process_reference": "f",
            "source": "secop2",
            "excluded_reason": None,
            "sampled": True,
            "source_identity": "CO1.NTC.3",
            "department": "Boyacá",
        },
    ]
    (run / "processes.json").write_text(
        json.dumps(
            {
                "processes": processes,
                "pages": [{"provider_count": 40}],
                "cutoff": "2026-11-27",
                "recent_days": 30,
            }
        ),
        "utf-8",
    )
    (run / "experience_requirements.json").write_text(
        json.dumps(
            [
                result("a", "no_experience_required", "explicit_favorable", [4]),
                result("b", "not_resolved", "documentary_silence"),
                result("f", "not_resolved", "explicit_favorable", [7]),
                result("e", "not_resolved", "insufficient_evidence"),
            ]
        ),
        "utf-8",
    )
    (run / "documents.json").write_text(
        json.dumps(
            [
                {
                    "process_reference": "a",
                    "documents": [{"sha256": "x", "complete": True, "role": "primary"}],
                }
            ]
        ),
        "utf-8",
    )
    (run / "metrics.json").write_text(json.dumps({"status": "completed"}), "utf-8")
    stage3 = tmp_path / "en01-secop1_blind"
    stage3.mkdir()
    (stage3 / "experience_requirements.json").write_text(
        json.dumps([result("e", "no_experience_required", "explicit_favorable", [3])]), "utf-8"
    )
    (stage3 / "documents.json").write_text(
        json.dumps(
            [
                {
                    "process_reference": "e",
                    "documents": [{"sha256": "y", "complete": True, "role": "primary"}],
                }
            ]
        ),
        "utf-8",
    )
    return run, stage3


def test_report_funnel_by_source_and_favorable_definition(tmp_path):
    # Arrange
    run, stage3 = synthetic_run(tmp_path)

    # Act
    rep = report_module.build_report(run, stage3, commit="abc")

    # Assert
    secop2 = rep["by_source"]["secop2"]
    assert (secop2["discovered"], secop2["eligible"], secop2["selected"]) == (5, 4, 3)
    assert secop2["eligible_not_selected"] == {"secop2_selection_quota": 1}
    assert secop2["excluded_by_reason"] == {"outside_commercial_profile": 1}
    assert secop2["classification"] == {"no_experience_required": 1, "not_resolved": 2}
    favorable = {i["source_identity"] for i in secop2["potentially_favorable"]}
    assert favorable == {"CO1.NTC.1", "CO1.NTC.3"}  # documentary silence never counts
    secop1 = rep["by_source"]["secop1"]
    assert secop1["classification"] == {"no_experience_required": 1}  # stage 3 supersedes
    assert secop1["documents_downloaded"] == 1
    assert rep["reproducibility"]["commit"] == "abc"


def test_report_never_modifies_its_inputs(tmp_path):
    run, stage3 = synthetic_run(tmp_path)
    before = {p: p.read_bytes() for d in (run, stage3) for p in d.iterdir()}

    report_module.build_report(run, stage3)

    assert {p: p.read_bytes() for d in (run, stage3) for p in d.iterdir()} == before


def test_report_markdown_lists_sources(tmp_path):
    run, stage3 = synthetic_run(tmp_path)

    text = report_module.markdown(report_module.build_report(run, stage3, commit="abc"))

    assert "## secop1" in text
    assert "## secop2" in text
    assert "Potencialmente favorables: 2" in text
