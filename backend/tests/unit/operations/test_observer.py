from types import SimpleNamespace

from tests.unit.eureka.test_affinity import process
from tests.unit.eureka.test_radar_pipeline import build


def test_pipeline_observes_native_and_ocr_without_reexecuting_reused_work():
    pipeline, services = build()
    extraction = services[3]
    events = []
    pipeline.observer = lambda event, data: events.append((event, data))
    services[2].download.return_value.available = 1
    extraction.extract_process.return_value = [
        SimpleNamespace(
            document=SimpleNamespace(document_version_id="version"),
            text_length=40,
            fragment_count=2,
            error_code=None,
            status="completed",
            reused=False,
            fragments=[
                SimpleNamespace(source_locator={"extraction_method": "native_pdf_text"}),
                SimpleNamespace(source_locator={"extraction_method": "ocr_text"}),
            ],
            diagnostics={
                "status": "ocr_success",
                "required_pages": [2],
                "processed_pages": [2],
                "elapsed_seconds": 1,
            },
        )
    ]
    pipeline.enrich(process(), lambda stage: None)
    value = next(data for event, data in events if event == "extraction_result")
    assert value["native"]
    assert value["succeeded"]
    assert value["processed"] == 1
    extraction.extract_process.return_value[0].reused = True
    # Restore the normal fake discovery/detail sequence for a second enrichment.
    second, _ = build()
    second.observer = pipeline.observer
    second.documents.download.return_value.available = 1
    second.extraction.extract_process.return_value = extraction.extract_process.return_value
    events.clear()
    second.enrich(process(), lambda stage: None)
    value = next(data for event, data in events if event == "extraction_result")
    assert value["reused"]
    assert value["succeeded"]
    assert value["processed"] == value["ocr_seconds"] == 0
