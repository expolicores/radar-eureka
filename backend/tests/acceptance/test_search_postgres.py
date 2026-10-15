"""Opt-in PostgreSQL checks. Rollback only on a separately named test database."""

import copy
import os
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from public_procurement.documents.repositories import (
    AcquisitionAttemptRecord,
    DocumentVersionRecord,
)
from public_procurement.extraction.repositories import ContentFragmentRecord, ExtractionRunRecord
from public_procurement.extraction.search_queries import snapshots
from public_procurement.ingestion.process_repositories import SecopProcessRecord
from public_procurement.search.domain.query import SearchQuery
from public_procurement.search.services import SearchQueries, build_search_service
from public_procurement.shared.config import load_settings


@pytest.fixture
def session():
    value = os.environ.get("SEARCH_ACCEPTANCE_DATABASE_URL")
    if not value:
        pytest.skip("SEARCH_ACCEPTANCE_DATABASE_URL required (isolated test database)")
    url = make_url(value)
    development = make_url(load_settings().database_url)
    assert url.database.endswith("_test")
    assert url.database != development.database
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(connection) as session:
            yield session
        transaction.rollback()
    engine.dispose()


def clone(record, **changes):
    values = {c.name: copy.deepcopy(getattr(record, c.name)) for c in record.__table__.columns}
    values.update(id=uuid.uuid4(), **changes)
    return type(record)(**values)


def golden(session):
    return session.scalar(
        select(SecopProcessRecord).where(SecopProcessRecord.id_del_proceso == "CO1.REQ.11172521")
    )


@pytest.mark.parametrize(
    "query",
    [
        SearchQuery(q="jugo hit"),
        SearchQuery(q="chocorramo"),
        SearchQuery(q="refrigerios"),
        SearchQuery(q="50192703"),
        SearchQuery(q="Covarachía"),
        SearchQuery(q="Boyacá"),
        SearchQuery(budget_min=2000000, budget_max=3000000),
    ],
)
def test_golden_queries_keep_score(session, query):
    query = query.model_copy(update={"municipality": "Covarachía"})
    result = build_search_service(session, load_settings()).search(query)
    assert result["total"] == 1
    assert result["items"][0]["score"] == 65


def test_new_current_version_invalidates_old_extraction_and_canonical(session):
    process = golden(session)
    data = snapshots(session, [process.id], None)[process.id]
    assert data["canonical"]
    current_ids = {f["document_version_id"] for f in data["structured"]}
    versions = session.scalars(
        select(DocumentVersionRecord).where(DocumentVersionRecord.id.in_(current_ids))
    ).all()
    for version in versions:
        new = clone(version, sha256=uuid.uuid4().hex * 2)
        session.add(new)
        session.flush()
        old = session.scalar(
            select(AcquisitionAttemptRecord).where(
                AcquisitionAttemptRecord.version_id == version.id
            )
        )
        session.add(clone(old, version_id=new.id, finished_at=old.finished_at + timedelta(days=1)))
    session.flush()
    data = snapshots(session, [process.id], None)[process.id]
    assert data["canonical"] == []
    assert data["structured"] == []
    assert (
        build_search_service(session, load_settings()).search(
            SearchQuery(q="jugo hit", municipality="Covarachía")
        )["total"]
        == 0
    )


def test_new_extraction_invalidates_old_facts_but_preserves_current_text(session):
    process = golden(session)
    data = snapshots(session, [process.id], None)[process.id]
    current_ids = {f["document_version_id"] for f in data["structured"]}
    for run in session.scalars(
        select(ExtractionRunRecord).where(ExtractionRunRecord.document_version_id.in_(current_ids))
    ).all():
        new = clone(
            run,
            extractor_name="search-history-test",
            finished_at=run.finished_at + timedelta(days=1),
            fragment_count=1,
        )
        session.add(new)
        session.flush()
        fragment = session.scalar(
            select(ContentFragmentRecord).where(ContentFragmentRecord.extraction_run_id == run.id)
        )
        session.add(
            clone(
                fragment,
                extraction_run_id=new.id,
                text="nuevofragmentotest",
                normalized_text="nuevofragmentotest",
                ordinal=0,
            )
        )
    session.flush()
    result = build_search_service(session, load_settings()).search(
        SearchQuery(q="nuevofragmentotest", municipality="Covarachía")
    )
    assert result["total"] == 1
    assert result["items"][0]["match_type"] == "extracted_text_match"


def test_database_normalization_and_readonly_transaction(session):
    assert (
        session.scalar(text("SELECT public.search_normalize_v1('Covarachía Boyacá')"))
        == "covarachia boyaca"
    )
    service = build_search_service(session, load_settings())
    result = service.search(SearchQuery(q="benchmarkneedle"))
    assert result["total"] == len(
        {
            row["process_id"]
            for row in service.search(SearchQuery(q="benchmarkneedle", page_size=100))["items"]
        }
    )
    assert service.search(SearchQuery(q="benchmarkneedle", page=99))["items"] == []


def test_native_and_ocr_equal_rank_deduplicate_process(session):
    process = session.scalar(
        select(SecopProcessRecord).where(SecopProcessRecord.id_del_proceso == "BENCH.0")
    )
    data = snapshots(session, [process.id], {"q": "benchmarkneedle:*"})[process.id]
    fragment = session.get(ContentFragmentRecord, uuid.UUID(data["text"][0]["id"]))
    fragment.text = fragment.normalized_text = "simetriaocr"
    fragment.source_locator = {**fragment.source_locator, "extraction_method": "native_pdf_text"}
    other = clone(
        fragment,
        ordinal=fragment.ordinal + 1,
        source_locator={**fragment.source_locator, "extraction_method": "ocr_text"},
    )
    session.add(other)
    session.flush()
    result = build_search_service(session, load_settings()).search(SearchQuery(q="simetriaocr"))
    assert result["total"] == 1
    assert result["items"][0]["score"] is None
    reasons = result["items"][0]["matches"]
    assert {r["locator"]["extraction_method"] for r in reasons} == {"native_pdf_text", "ocr_text"}
    assert {r["rank"] for r in reasons} == {2}


@pytest.mark.parametrize(
    ("query", "total"),
    [
        (SearchQuery(q="refrigerios", department="Boyacá", municipality="Covarachía"), 1),
        (SearchQuery(q="refrigerios", department="Casanare", municipality="Covarachía"), 0),
        (SearchQuery(budget_max=1000000, municipality="Covarachía"), 0),
        (SearchQuery(unspsc="50192703", municipality="Covarachía"), 1),
        (SearchQuery(published_from="2026-10-08", municipality="Covarachía"), 0),
        (SearchQuery(published_to="2026-10-07", municipality="Covarachía"), 1),
    ],
)
def test_structured_filter_combinations(session, query, total):
    assert build_search_service(session, load_settings()).search(query)["total"] == total


def test_http_query_database_transaction_is_enforced_readonly(session):
    engine = create_engine(session.get_bind().engine.url)
    observed = []

    def inspect_transaction(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("SELECT to_regprocedure"):
            cursor.execute("SHOW transaction_read_only")
            readonly = cursor.fetchone()[0]
            cursor.execute("SHOW transaction_isolation")
            observed.append((readonly, cursor.fetchone()[0]))

    event.listen(engine, "before_cursor_execute", inspect_transaction)
    try:
        SearchQueries(sessionmaker(engine), load_settings()).search(SearchQuery(q="jugo hit"))
    finally:
        event.remove(engine, "before_cursor_execute", inspect_transaction)
        engine.dispose()
    assert observed == [("on", "repeatable read")]
