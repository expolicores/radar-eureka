"""Offline tests for focused validation of authorized pending documents. Synthetic data only."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "scripts"), str(HERE)]

import eureka_nacional_cdp_stream as streaming  # noqa: E402
import eureka_nacional_en01 as en01  # noqa: E402
import eureka_nacional_secop1_acquire as acquire  # noqa: E402
import eureka_nacional_secop1_flow as flow  # noqa: E402
import eureka_nacional_targeted_documents as targeted  # noqa: E402

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage  # noqa: E402

CONSTANCIA = "26-13-11111111"
SECOP = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId="
REQUIRED = "El proponente deberá acreditar experiencia contractual con dos contratos ejecutados."
WAIVED = "No se exige experiencia contractual al proponente."
PDF = b"%PDF-1.7\n" + b"0" * 2000 + b"\n%%EOF\n"


def secop1_doc(name, number, role, displayed="250 KB"):
    path = f"/2020/2020Q2/2026/DA/1/{CONSTANCIA}/DA_PROCESO_{CONSTANCIA}_1_{number}.pdf"
    return {
        "document_id": f"secop1:{CONSTANCIA}:{hashlib.sha256(path.encode()).hexdigest()}",
        "name": name,
        "extension": "pdf",
        "role": role,
        "role_hint": None,
        "relative_path": path,
        "displayed_size": displayed,
        "displayed_size_bytes": flow.displayed_size_bytes(displayed),
        "complete": False,
    }


def secop2_doc(name, number, role, extension="pdf"):
    return {
        "document_id": str(number),
        "name": name,
        "extension": extension,
        "role": role,
        "role_hint": None,
        "url": SECOP + str(number),
        "complete": False,
    }


def store(run, doc, body=PDF):
    storage = LocalBinaryStorage(run / "binaries")
    stored = storage.store(
        [body],
        original_name="x.pdf",
        content_type="application/pdf",
        expected_size=len(body),
        max_bytes=en01.DOCUMENT_BYTES,
    )
    receipts = flow.load_receipts(run)
    receipts[f"{doc['document_id']}:{doc['extension']}"] = {
        "storage_path": stored.storage_path,
        "sha256": stored.sha256,
        "observed_size": stored.observed_size,
        "content_type": "application/pdf",
    }
    (run / flow.RECEIPTS_FILE).write_text(json.dumps(receipts), "utf-8")


def source_run(root, *, formatos=True):
    run = root / "en01-blind"
    run.mkdir()
    s1 = [
        secop1_doc("Invitación", 1, "primary"),
        secop1_doc("ESTUDIOS PREVIOS", 2, "support"),
        secop1_doc("ANALISIS DEL SECTOR", 3, "unknown"),
    ]
    s2 = [
        secop2_doc("INVITACION PUBLICA", 11, "primary"),
        secop2_doc("ESTUDIO PREVIO Y ANEXOS", 12, "support"),
    ]
    if formatos:
        s2.insert(0, secop2_doc("FORMATOS", 10, "support", extension=""))
    processes = [
        {
            "process_reference": "p1",
            "source": "secop1",
            "source_identity": f"secop1:{CONSTANCIA}",
            "entity_name": "Concejo",
            "commercial_priority": "A",
        },
        {
            "process_reference": "p2",
            "source": "secop2",
            "source_identity": "CO1.NTC.9",
            "entity_name": "Fondo",
            "commercial_priority": "A",
        },
    ]
    (run / "processes.json").write_text(json.dumps({"processes": processes}), "utf-8")
    (run / "documents.json").write_text(
        json.dumps(
            [
                {"process_reference": "p1", "documents": s1},
                {"process_reference": "p2", "documents": s2},
            ]
        ),
        "utf-8",
    )
    store(run, s1[0])
    store(run, s2[-2])
    return run, s1, s2


def approved(s1, s2):
    return targeted.batch_digest(
        [
            ["secop1", CONSTANCIA, s1[1]["document_id"], s1[1]["relative_path"]],
            ["secop2", "CO1.NTC.9", "12", SECOP + "12"],
        ]
    )


def planned(tmp_path, **kwargs):
    run, s1, s2 = source_run(tmp_path, **kwargs)
    digest = approved(s1, s2)
    target = tmp_path / "en01-target_blind"
    plan = targeted.build_plan(run, target, [s1[1]["document_id"], "12"], digest)
    return run, target, plan, digest, s1, s2


# ---------------------------------------------------------------- plan


def test_plan_binds_the_approved_digest_and_prepares_the_secop1_queue(tmp_path):
    # Arrange / Act
    _run, target, plan, digest, s1, _ = planned(tmp_path)

    # Assert
    assert plan["batch_sha256"] == digest
    assert [i["name"] for i in plan["items"]] == ["ESTUDIOS PREVIOS", "ESTUDIO PREVIO Y ANEXOS"]
    queue = flow.load_queue(target)
    assert [i["document_id"] for i in queue["items"]] == [s1[1]["document_id"]]
    items, recorded = acquire.plan_batch(queue, target)
    assert (len(items), recorded) == (1, 0)
    assert plan["network_requests"] == 0


def test_plan_rejects_a_batch_different_from_the_approved_one(tmp_path):
    run, s1, s2 = source_run(tmp_path)

    with pytest.raises(ValueError, match="hash aprobado"):
        targeted.build_plan(
            run, tmp_path / "en01-target_x", [s1[1]["document_id"]], approved(s1, s2)
        )
    assert not (tmp_path / "en01-target_x").exists()


@pytest.mark.parametrize("document_id", ["999", "10"])  # unknown, unsupported format
def test_plan_rejects_unknown_or_unsupported_documents(tmp_path, document_id):
    run, s1, s2 = source_run(tmp_path)

    with pytest.raises(ValueError, match="Documento"):
        targeted.build_plan(run, tmp_path / "en01-target_x", [document_id], approved(s1, s2))


def test_plan_is_never_overwritten_and_tampering_is_detected(tmp_path):
    run, target, _plan, digest, s1, _ = planned(tmp_path)

    with pytest.raises(FileExistsError):
        targeted.build_plan(run, target, [s1[1]["document_id"], "12"], digest)
    data = json.loads((target / targeted.PLAN_FILE).read_text(encoding="utf-8"))
    data["items"][1]["locator"] = SECOP + "13"
    (target / targeted.PLAN_FILE).write_text(json.dumps(data), "utf-8")
    with pytest.raises(ValueError, match="alterado"):
        targeted.load_plan(target, digest)


# ---------------------------------------------------------------- SECOP II acquisition


class Fakes:
    def __init__(self, direct_status=403, direct_code="http_error", stream_error=None):
        self.direct_calls = self.stream_calls = 0
        self.stream_limits = []
        self.direct_status, self.direct_code, self.stream_error = (
            direct_status,
            direct_code,
            stream_error,
        )

    def runner(self, direct_ok=False):
        def download(_client, document, storage, _settings, *, diagnostics):
            self.direct_calls += 1
            if direct_ok:
                return storage.store(
                    [PDF],
                    original_name="x.pdf",
                    content_type="application/pdf",
                    expected_size=len(PDF),
                    max_bytes=en01.DOCUMENT_BYTES,
                )
            if self.direct_status is not None:
                diagnostics["http_status"] = self.direct_status
            raise en01.AcquisitionError(self.direct_code, "rechazado")

        spike = SimpleNamespace(
            LocalBinaryStorage=LocalBinaryStorage,
            SpikeDocument=en01.spike.SpikeDocument,
            download_document=download,
        )
        return SimpleNamespace(
            spike=spike,
            DownloadState=en01.DownloadState,
            verify_document_type=en01.verify_document_type,
            DOCUMENT_BYTES=en01.DOCUMENT_BYTES,
            AcquisitionError=en01.AcquisitionError,
        )

    def streaming(self):
        def stream(
            document, storage, marker, diagnostics, *, cdp_url, max_bytes=en01.DOCUMENT_BYTES
        ):
            self.stream_calls += 1
            self.stream_limits.append(max_bytes)
            if self.stream_error:
                diagnostics["error"] = self.stream_error
                raise en01.AcquisitionError(self.stream_error, "rechazado")
            return storage.store(
                [PDF],
                original_name="x.pdf",
                content_type="application/pdf",
                expected_size=len(PDF),
                max_bytes=en01.DOCUMENT_BYTES,
            )

        return SimpleNamespace(
            MARKER_NAME=streaming.MARKER_NAME,
            validate_target=streaming.validate_target,
            fallback_eligible=streaming.fallback_eligible,
            download_stream_pdf=stream,
        )


def run_acquire(target, digest, fakes, *, direct_ok=False, settings=None):
    return targeted.acquire_secop2(
        target,
        digest,
        runner=fakes.runner(direct_ok),
        streaming=fakes.streaming(),
        client=targeted.DirectOnlyClient(),
        settings=settings,
        cdp_url="http://127.0.0.1:9232",
    )


def test_stream_is_used_only_after_direct_403_and_leaves_a_receipt(tmp_path):
    # Arrange
    _, target, _, digest, _, _ = planned(tmp_path)
    fakes = Fakes()

    # Act
    report = run_acquire(target, digest, fakes)

    # Assert
    assert (fakes.direct_calls, fakes.stream_calls) == (1, 1)
    assert report[0]["outcome"] == "stored"
    assert report[0]["mechanism"] == "edge_cdp_stream_authorized_support"
    assert "12:pdf" in flow.load_receipts(target)


def test_direct_success_needs_no_stream(tmp_path):
    _, target, _, digest, _, _ = planned(tmp_path)
    fakes = Fakes()

    report = run_acquire(target, digest, fakes, direct_ok=True)

    assert (fakes.direct_calls, fakes.stream_calls) == (1, 0)
    assert report[0]["mechanism"] == "direct"


@pytest.mark.parametrize(("status", "code"), [(500, "http_error"), (None, "timeout")])
def test_errors_other_than_403_never_use_the_stream(tmp_path, status, code):
    _, target, _, digest, _, _ = planned(tmp_path)
    fakes = Fakes(direct_status=status, direct_code=code)

    report = run_acquire(target, digest, fakes)

    assert fakes.stream_calls == 0
    assert report[0]["outcome"] == "rejected"
    assert flow.load_receipts(target) == {}


def test_stream_size_rejection_is_recorded_without_receipt(tmp_path):
    _, target, _, digest, _, _ = planned(tmp_path)
    fakes = Fakes(stream_error="declared_size_limit")

    report = run_acquire(target, digest, fakes)

    assert report[0]["outcome"] == "rejected"
    assert report[0]["reason"] == "declared_size_limit"
    assert flow.load_receipts(target) == {}


def test_each_document_has_a_single_attempt(tmp_path):
    _, target, _, digest, _, _ = planned(tmp_path)
    first = Fakes(stream_error="protocol_error")
    run_acquire(target, digest, first)
    again = Fakes()

    report = run_acquire(target, digest, again)

    assert (again.direct_calls, again.stream_calls) == (0, 0)
    assert report[0]["outcome"] == "attempt_recorded"


def test_preventive_marker_blocks_acquisition(tmp_path):
    _, target, _, digest, _, _ = planned(tmp_path)
    (target.parent / streaming.MARKER_NAME).write_text("x", encoding="utf-8")
    fakes = Fakes()

    with pytest.raises(ValueError, match="Marcador"):
        run_acquire(target, digest, fakes)
    assert fakes.direct_calls == 0


# ---------------------------------------------------------------- joint analysis


def fake_extract(texts):
    def extract(document, stored, storage, settings, entry, *, ocr_pages, page_plan):
        text = texts.get(document.original_name, "Texto sin relacion con el tema.")
        frag = SimpleNamespace(
            text=text, source_locator={"page_number": 1, "extraction_method": "native_pdf_text"}
        )
        entry.update(
            total_pages=1,
            pages_seen=[1],
            ocr_pages=[],
            ocr_success_pages=[],
            native_pages=[1],
            pending_pages=[],
            status="native_success",
            error_code=None,
            extraction_seconds=0.1,
            fragments=[frag],
            cover_metadata={},
            content_complete=True,
            complete=True,
        )

    return extract


def analysis(tmp_path, texts, **kwargs):
    _run, target, _, digest, s1, s2 = planned(tmp_path, **kwargs)
    store(target, s1[1])
    store(target, s2[-1])
    runner = SimpleNamespace(
        spike=en01.spike,
        StoredBinary=en01.StoredBinary,
        verify_document_type=en01.verify_document_type,
        DOCUMENT_BYTES=en01.DOCUMENT_BYTES,
        extract_document=fake_extract(texts),
    )
    results = targeted.analyze(
        target, digest, runner=runner, settings=None, budget=flow.OcrBudget()
    )
    return {r["process_reference"]: r for r in results}, target, digest, runner


def test_requirement_in_the_study_is_reported_without_a_formal_conclusion(tmp_path):
    results, *_ = analysis(tmp_path, {"ESTUDIOS PREVIOS": REQUIRED})

    assert results["p1"]["validation_reading"] == "experiencia_exigida_sin_conclusion_formal"
    assert results["p1"]["status"] == "not_resolved"


def test_unprocessable_formats_keep_silence_insufficient(tmp_path):
    results, *_ = analysis(tmp_path, {})

    p2 = results["p2"]
    assert p2["validation_reading"] == "evidencia_insuficiente"
    assert p2["unresolved_dependencies"] == [
        {"document": "FORMATOS", "reason": "formato_no_procesable"}
    ]


def test_full_coverage_silence_is_reported_as_such_never_as_absence(tmp_path):
    results, *_ = analysis(tmp_path, {}, formatos=False)

    assert results["p2"]["validation_reading"] == "silencio_documental_con_cobertura_suficiente"
    assert results["p2"]["status"] != "no_experience_required"


def test_explicit_waiver_in_the_study_still_needs_corroboration(tmp_path):
    results, *_ = analysis(tmp_path, {"ESTUDIO PREVIO Y ANEXOS": WAIVED}, formatos=False)

    assert results["p2"]["validation_reading"] == ("ausencia_explicita_pendiente_de_corroboracion")


def test_analysis_is_offline_and_never_overwritten(tmp_path):
    _, target, digest, runner = analysis(tmp_path, {})

    data = json.loads((target / targeted.RESULTS_FILE).read_text(encoding="utf-8"))
    assert data["network_requests"] == 0
    with pytest.raises(ValueError, match="ya existe"):
        targeted.analyze(target, digest, runner=runner, settings=None, budget=flow.OcrBudget())


# ---------------------------------------------------------------- exceptional size ceiling

MIB = 1024 * 1024


def governing_plan(tmp_path, limit_mib=16, document="11"):
    run, _s1, _s2 = source_run(tmp_path)
    item = ["secop2", "CO1.NTC.9", document, SECOP + document]
    digest = targeted.batch_digest([[*item, limit_mib * MIB]])
    target = tmp_path / "en01-target_blind_r16"
    plan = targeted.build_plan(
        run, target, [document], digest, max_bytes_by_document={document: limit_mib * MIB}
    )
    return run, target, plan, digest


def test_ceiling_applies_only_to_the_named_governing_document_and_joins_the_digest(tmp_path):
    # Arrange / Act
    _run, _target, plan, digest = governing_plan(tmp_path)

    # Assert
    [item] = plan["items"]
    assert item["max_bytes"] == 16 * MIB
    assert item["current_role"] == "primary"
    assert plan["batch_sha256"] == digest
    default_digest = targeted.batch_digest([["secop2", "CO1.NTC.9", "11", SECOP + "11"]])
    assert digest != default_digest


def test_default_plans_keep_their_previous_digest(tmp_path):
    _run, _target, plan, digest, _s1, _s2 = planned(tmp_path)

    assert all("max_bytes" not in item for item in plan["items"])
    assert plan["batch_sha256"] == digest


@pytest.mark.parametrize(
    ("document", "limit_mib"),
    [("12", 16), ("11", 17), ("11", 10)],  # support document, above 16 MiB, not exceptional
)
def test_ceiling_is_rejected_outside_a_governing_document_or_range(tmp_path, document, limit_mib):
    run, _s1, _s2 = source_run(tmp_path)
    item = ["secop2", "CO1.NTC.9", document, SECOP + document]
    limit = limit_mib * MIB
    digest = targeted.batch_digest([[*item, limit]] if limit != 10 * MIB else [item])

    with pytest.raises(ValueError, match=r"(?i)limite"):
        targeted.build_plan(
            run,
            tmp_path / "en01-target_x",
            [document],
            digest,
            max_bytes_by_document={document: limit if limit != 10 * MIB else 9 * MIB},
        )


def test_ceiling_for_a_document_outside_the_lot_is_rejected(tmp_path):
    run, _s1, _s2 = source_run(tmp_path)
    digest = targeted.batch_digest([["secop2", "CO1.NTC.9", "11", SECOP + "11"]])

    with pytest.raises(ValueError, match="fuera del lote"):
        targeted.build_plan(
            run, tmp_path / "en01-target_x", ["11"], digest, max_bytes_by_document={"12": 16 * MIB}
        )


def test_tampering_with_the_ceiling_is_detected(tmp_path):
    _run, target, plan, digest = governing_plan(tmp_path)
    plan["items"][0]["max_bytes"] = 15 * MIB
    (target / targeted.PLAN_FILE).write_text(json.dumps(plan), "utf-8")

    with pytest.raises(ValueError, match="alterado"):
        targeted.load_plan(target, digest)


def test_prior_attempts_of_the_same_document_are_listed_in_the_new_plan(tmp_path):
    run, _s1, _s2 = source_run(tmp_path)
    earlier = tmp_path / "en01-target_blind" / "targeted_attempts"
    earlier.mkdir(parents=True)
    (earlier / "a.json").write_text(
        json.dumps({"document_id": "11", "outcome": "rejected", "reason": "declared_size_limit"}),
        "utf-8",
    )
    item = ["secop2", "CO1.NTC.9", "11", SECOP + "11", 16 * MIB]

    plan = targeted.build_plan(
        run,
        tmp_path / "en01-target_blind_r16",
        ["11"],
        targeted.batch_digest([item]),
        max_bytes_by_document={"11": 16 * MIB},
    )

    [attempt] = plan["prior_attempts"]["11"]
    assert attempt["reason"] == "declared_size_limit"
    assert attempt["run"] == "en01-target_blind"


def test_acquisition_passes_the_ceiling_only_for_the_authorized_document(tmp_path):
    _run, target, _plan, digest = governing_plan(tmp_path)
    fakes = Fakes()
    copies = []
    settings = SimpleNamespace(model_copy=lambda update: copies.append(update) or update)

    report = run_acquire(target, digest, fakes, settings=settings)

    assert copies == [{"document_max_bytes": 16 * MIB, "extraction_max_bytes": 16 * MIB}]
    assert fakes.stream_limits == [16 * MIB]
    assert report[0]["max_bytes"] == 16 * MIB
    assert report[0]["outcome"] == "stored"


def test_default_acquisition_keeps_the_10_mib_ceiling(tmp_path):
    _, target, _, digest, _, _ = planned(tmp_path)
    fakes = Fakes()

    run_acquire(target, digest, fakes)

    assert fakes.stream_limits == [10 * MIB]


def headers_event(length):
    return {
        "responseStatusCode": 200,
        "responseHeaders": [
            {"name": "Content-Type", "value": "application/pdf"},
            {"name": "Content-Length", "value": str(length)},
        ],
    }


def test_declared_size_is_checked_against_the_document_ceiling():
    twelve = 12 * MIB
    diagnostics = {}

    with pytest.raises(streaming.RejectionError, match="declared_size_limit"):
        streaming.response_length(headers_event(twelve), diagnostics=diagnostics)
    assert diagnostics["declared_bytes"] == twelve
    assert streaming.response_length(headers_event(twelve), max_bytes=16 * MIB) == twelve
    with pytest.raises(streaming.RejectionError, match="declared_size_limit"):
        streaming.response_length(headers_event(17 * MIB), max_bytes=16 * MIB)


@pytest.mark.parametrize("limit", [9 * 1024 * 1024, 17 * 1024 * 1024, "16"])
def test_stream_ceiling_outside_the_allowed_range_is_rejected(limit):
    with pytest.raises(streaming.RejectionError, match="invalid_size_limit"):
        streaming.stream_limit(limit)


def test_plan_carries_an_incomplete_inventory_flag(tmp_path):
    run, _s1, _s2 = source_run(tmp_path)
    cases = json.loads((run / "documents.json").read_text("utf-8"))
    for case in cases:
        if case["process_reference"] == "p2":
            case["inventory_complete"] = False
    (run / "documents.json").write_text(json.dumps(cases), "utf-8")
    target = tmp_path / "en01-target_blind"

    targeted.build_plan(
        run, target, ["12"], targeted.batch_digest([["secop2", "CO1.NTC.9", "12", SECOP + "12"]])
    )

    [case] = json.loads((target / "documents.json").read_text("utf-8"))
    assert case["inventory_complete"] is False
