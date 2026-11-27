"""Offline tests for the findings presentation inside the blind funnel report."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eureka_nacional_blind_report as report_module
import eureka_nacional_findings_recompute as recompute_module
import test_eureka_nacional_blind_scope as scope


def finding(category, effort="lectura_humana", reviews=()):
    return {
        "finding": {
            "category": category,
            "basis": f"basis_{category}",
            "formal_status": "not_resolved",
            "review_effort": effort,
            "needs_human_attention": category
            in {"priority_review", "uncertain", "experience_indications"},
            "coverage": {
                "system_verified": [{"document": "Invitación"}],
                "not_verified_by_system": [
                    {"document": "FORMATOS", "reason": "formato_no_procesable"}
                ]
                if effort == "formato_no_soportado"
                else [],
            },
            "resolution_actions": ["Revisar."],
            "human_review": list(reviews),
        },
        "stored_status": "not_resolved",
    }


def run_with_priorities(tmp_path):
    run, stage3 = scope.synthetic_run(tmp_path)
    discovery = json.loads((run / "processes.json").read_text("utf-8"))
    priorities = {"a": "B", "b": "A", "c": "A", "e": "C", "f": "A"}
    for process in discovery["processes"]:
        process["commercial_priority"] = priorities.get(process["process_reference"])
        process["entity_name"] = f"Entidad {process['process_reference']}"
    (run / "processes.json").write_text(json.dumps(discovery), "utf-8")
    return run, stage3


def test_findings_are_ordered_by_category_then_commercial_priority(tmp_path):
    # Arrange
    run, stage3 = run_with_priorities(tmp_path)
    findings = {
        "a": finding("uncertain"),
        "b": finding("uncertain", effort="formato_no_soportado"),
        "e": finding("priority_review"),
        "f": finding("experience_indications"),
    }

    # Act
    presentation = report_module.build_report(run, stage3, findings=findings)["findings"]

    # Assert: category first, then A/B/C inside each category.
    ordered = [(i["category"], i["process_reference"]) for i in presentation["ordered"]]
    assert ordered == [
        ("priority_review", "e"),
        ("uncertain", "b"),
        ("uncertain", "a"),
        ("experience_indications", "f"),
    ]
    assert presentation["counts"]["Hallazgo prioritario para revisión"] == 1
    assert presentation["counts"]["Experiencia exigida"] == 0


def test_documentary_categories_never_remove_processes_from_traceability(tmp_path):
    run, stage3 = run_with_priorities(tmp_path)
    findings = {key: finding("experience_indications") for key in "abef"}

    presentation = report_module.build_report(run, stage3, findings=findings)["findings"]

    visibility = presentation["visibility"]
    assert visibility["analyzed"] == visibility["visible"] == 4
    assert visibility["excluded_by_documentary_category"] == 0
    assert visibility["excluded_for_non_documentary_reasons"] == {"secop2_selection_quota": 1}
    [quota] = presentation["without_documentary_analysis"]
    assert quota["reason"] == "secop2_selection_quota"
    assert quota["commercial_priority"] == "A"


def test_attention_table_separates_human_review_from_system_coverage(tmp_path):
    run, stage3 = run_with_priorities(tmp_path)
    review = {
        "observation": "no_experience_requirement_found",
        "documents_reviewed": ["FORMATOS"],
        "recorded_on": "2026-11-27",
        "system_verified": False,
    }
    findings = {"b": finding("uncertain", "formato_no_soportado", [review])}

    report = report_module.build_report(run, stage3, findings=findings)
    text = report_module.markdown(report)

    [item] = [i for i in report["findings"]["attention"] if i["process_reference"] == "b"]
    assert item["documents_complete"] == ["Invitación"]
    assert item["documents_missing"] == [
        {"document": "FORMATOS", "reason": "formato_no_procesable"}
    ]
    assert item["human_review"] == [review]
    assert "## Hallazgos (capa de presentación)" in text
    assert "(no verificado por el sistema)" in text
    assert "Elegibles sin análisis documental" in text


def test_report_without_recomputed_findings_is_unchanged(tmp_path):
    run, stage3 = scope.synthetic_run(tmp_path)

    report = report_module.build_report(run, stage3)

    assert report["findings"] is None
    assert "Hallazgos (capa" not in report_module.markdown(report)


def test_recompute_layers_inventories_and_records_gaps_without_network(tmp_path):
    # Arrange: stage 3 replaces stage 1; no receipts exist, so nothing is extracted.
    root = tmp_path
    run, stage3 = scope.synthetic_run(root)
    (stage3 / "documents.json").write_text(
        json.dumps(
            [
                {
                    "process_reference": "e",
                    "documents": [
                        {
                            "document_id": "1",
                            "name": "Invitación",
                            "role": "primary",
                            "extension": "pdf",
                        },
                        {
                            "document_id": "2",
                            "name": "FORMATOS",
                            "role": "support",
                            "extension": "",
                        },
                    ],
                }
            ]
        ),
        "utf-8",
    )

    # Act
    rows = recompute_module.recompute(
        run, runner=None, settings=None, secop1_results=stage3, root=root
    )

    # Assert
    [row] = [r for r in rows if r["process_reference"] == "e"]
    assert row["evidence_layer"] == "secop1_stage3"
    gaps = {d["name"]: d["validation_gap"] for d in row["documents"]}
    assert gaps == {"Invitación": "no_descargado", "FORMATOS": "formato_no_procesable"}
    assert row["finding"]["visible"] is True
    assert row["finding"]["category"] == "uncertain"


def test_recompute_output_is_never_overwritten(tmp_path):
    path = tmp_path / recompute_module.OUTPUT_FILE
    recompute_module.write_new(path, {"rows": []})

    with pytest.raises(FileExistsError):
        recompute_module.write_new(path, {"rows": []})


def test_receipt_fallback_uses_the_content_address_never_the_provider_path(tmp_path):
    sha_held, sha_missing = "ab" + "1" * 62, "cd" + "2" * 62
    run = tmp_path / "en01-one"
    (run / "binaries" / "sha256" / "ab").mkdir(parents=True)
    (run / "binaries" / "sha256" / "ab" / sha_held).write_bytes(b"%PDF-1.4")
    documents = [
        {
            "document_id": "1",
            "extension": "pdf",
            "sha256": sha_held,
            "relative_path": "/2020/INVMC/proveedor.pdf",
        },
        {
            "document_id": "2",
            "extension": "pdf",
            "sha256": sha_missing,
            "relative_path": "/2020/INVMC/otro.pdf",
        },
    ]
    (run / "documents.json").write_text(
        json.dumps([{"process_reference": "x", "documents": documents}]), "utf-8"
    )

    receipts = recompute_module.held_receipts(tmp_path)

    assert receipts["1:pdf"][1]["storage_path"] == f"sha256/ab/{sha_held}"
    assert receipts["1:pdf"][1]["observed_size"] == 8
    assert "2:pdf" not in receipts
