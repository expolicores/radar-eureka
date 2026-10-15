"""Benchmark opt-in sobre copia aislada de Covarach?a; nunca modifica desarrollo.

Requiere SEARCH_ACCEPTANCE_DATABASE_URL y revisi?n 0014 en una base *_test.
Agrega 5.000 procesos sint?ticos si la copia contiene ?nicamente el golden case.
Compara ?ndices individualmente y los restaura. No resetea ni elimina tablas.
"""

import copy
import importlib.util
import json
import os
import statistics
import time
import uuid
from pathlib import Path

from sqlalchemy import MetaData, create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from public_procurement.extraction.consolidation import digest_inputs
from public_procurement.extraction.structured_repositories import StructuredFactRecord, as_fact
from public_procurement.search.domain.query import SearchQuery
from public_procurement.search.services import SearchQueries
from public_procurement.shared.config import load_settings

settings = load_settings()
url = make_url(os.environ["SEARCH_ACCEPTANCE_DATABASE_URL"])
if (
    not url.database
    or not url.database.endswith("_test")
    or url.database == make_url(settings.database_url).database
):
    raise SystemExit("Requires a separate *_test database; development is forbidden.")
engine = create_engine(url)
metadata = MetaData()
for schema in ("ingestion", "documents", "extraction", "eureka"):
    metadata.reflect(engine, schema=schema)
names = [
    "ingestion.secop_process",
    "documents.document",
    "documents.document_process",
    "documents.document_version",
    "documents.acquisition_attempt",
    "extraction.extraction_run",
    "extraction.content_fragment",
    "extraction.structured_fact",
    "extraction.canonical_fact",
    "extraction.canonical_fact_evidence",
]
with engine.connect() as c:
    templates = {
        name: dict(c.execute(select(metadata.tables[name]).limit(1)).mappings().one())
        for name in names
    }
    templates["extraction.structured_fact"] = dict(
        c.execute(
            select(metadata.tables["extraction.structured_fact"])
            .where(metadata.tables["extraction.structured_fact"].c.fact_type == "product")
            .limit(1)
        )
        .mappings()
        .one()
    )
    templates["extraction.canonical_fact"] = dict(
        c.execute(
            select(metadata.tables["extraction.canonical_fact"])
            .where(metadata.tables["extraction.canonical_fact"].c.canonical_type == "PRODUCT")
            .limit(1)
        )
        .mappings()
        .one()
    )
    count = c.scalar(text("SELECT count(*) FROM ingestion.secop_process"))
if count == 1:
    rows = {name: [] for name in names}
    for i in range(5000):
        data = copy.deepcopy(templates)
        ids = {name: uuid.uuid4() for name in names}
        pid = ids[names[0]]
        did = ids[names[1]]
        vid = ids[names[3]]
        rid = ids[names[5]]
        fid = ids[names[6]]
        sid = ids[names[7]]
        cid = ids[names[8]]
        term = "benchmarkneedle" if i % 100 == 0 else "televisor"
        for name in names:
            data[name]["id"] = ids[name]
        data[names[0]].update(
            dataset_id="search-test",
            id_del_proceso=f"BENCH.{i}",
            title=f"Compra {term} {i}",
            description="Corpus sintético de rendimiento",
            portfolio_id=f"BENCH.{i}",
            municipality="Municipio prueba",
        )
        data[names[1]].update(
            dataset_id="search-test", id_documento=f"BENCH.{i}", portfolio_id=f"BENCH.{i}"
        )
        data[names[2]].update(document_id=did, process_id=pid, portfolio_id=f"BENCH.{i}")
        data[names[3]].update(document_id=did)
        data[names[4]].update(document_id=did, version_id=vid)
        data[names[5]].update(document_version_id=vid, fragment_count=1)
        locator = {
            "page_number": 1,
            "document_version_id": str(vid),
            "extraction_method": "ocr_text" if i % 2 else "native_pdf_text",
            "original_name": "Benchmark.pdf",
        }
        data[names[6]].update(
            extraction_run_id=rid,
            text=f"Suministro de {term}",
            normalized_text=f"suministro de {term}",
            source_locator=locator,
        )
        sources = [
            {
                "content_fragment_id": str(fid),
                "extraction_run_id": str(rid),
                "original_name": "Benchmark.pdf",
                "locator": locator,
                "text": term,
            }
        ]
        data[names[7]].update(
            process_id=pid,
            document_version_id=vid,
            content_fragment_id=fid,
            string_value=term,
            normalized_value={"name": term},
            evidence_text=term,
            source_locator={"sources": sources},
        )
        digest = digest_inputs([as_fact(StructuredFactRecord(**data[names[7]]))])
        data[names[8]].update(
            process_id=pid,
            input_digest=digest,
            canonical_value={"value": {"name": term}},
            status="confirmed",
        )
        data[names[9]].update(canonical_fact_id=cid, structured_fact_id=sid)
        for name in names:
            rows[name].append(data[name])
    with engine.begin() as c:
        for name in names:
            c.execute(metadata.tables[name].insert(), rows[name])
with engine.begin() as c:
    c.execute(text("ANALYZE"))
spec = importlib.util.spec_from_file_location(
    "migration", Path(__file__).resolve().parents[1] / "alembic/versions/0014_transversal_search.py"
)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)
sqls = {
    "ingestion.ix_search_process_fts": (
        "SELECT id FROM ingestion.secop_process WHERE "
        "to_tsvector('spanish'::regconfig, "
        "public.search_normalize_v1(coalesce(title,'')||' "
        "'||coalesce(description,'')||' '||coalesce(reference,'')||' "
        "'||coalesce(id_del_proceso,'')||' '||coalesce(entity_name,'')||' "
        "'||coalesce(department,'')||' '||coalesce(municipality,'')||' "
        "'||coalesce(category_code,''))) @@ to_tsquery('spanish','benchmarkneedle:*')"
    ),
    "extraction.ix_search_canonical_fts": (
        "SELECT process_id FROM extraction.canonical_fact WHERE "
        "to_tsvector('spanish'::regconfig,public.search_normalize_v1("
        "public.search_values_v1(canonical_value->'value'))) "
        "@@ to_tsquery('spanish','benchmarkneedle:*')"
    ),
    "extraction.ix_search_structured_fts": (
        "SELECT process_id FROM extraction.structured_fact WHERE "
        "to_tsvector('spanish'::regconfig,public.search_normalize_v1(coalesce(string_value,'')||' "
        "'||public.search_values_v1(normalized_value))) @@ "
        "to_tsquery('spanish','benchmarkneedle:*')"
    ),
    "extraction.ix_search_fragment_fts": (
        "SELECT id FROM extraction.content_fragment WHERE "
        "to_tsvector('spanish'::regconfig,public.search_normalize_v1(normalized_text)) "
        "@@ to_tsquery('spanish','benchmarkneedle:*')"
    ),
}
report = {"corpus": {}, "indexes": {}, "api": {}}


def plan(sql):
    with engine.connect() as c:
        return c.scalar(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql))[0]


def nodes(value):
    found = []
    if isinstance(value, dict):
        if "Index Name" in value:
            found.append(value["Index Name"])
        for child in value.values():
            found.extend(nodes(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(nodes(child))
    return found


for name, sql in sqls.items():
    with engine.begin() as c:
        c.execute(text("DROP INDEX " + name))
    try:
        absent = plan(sql)
    finally:
        with engine.begin() as c:
            c.execute(text(migration.INDEXES[name]))
    present = plan(sql)
    report["indexes"][name] = {
        "with_ms": present["Execution Time"],
        "without_ms": absent["Execution Time"],
        "used": nodes(present),
        "plan_with": present,
        "plan_without": absent,
    }
    print(
        name,
        report["indexes"][name]["with_ms"],
        report["indexes"][name]["without_ms"],
        nodes(present),
    )
with engine.connect() as c:
    for name in names:
        report["corpus"][name] = c.scalar(select(func.count()).select_from(metadata.tables[name]))
    for name in sqls:
        report["indexes"][name]["bytes"] = c.scalar(
            text("SELECT pg_relation_size(to_regclass(:name))"), {"name": name}
        )
queries = SearchQueries(sessionmaker(engine), settings)
for name, query in {
    "selective_page1": SearchQuery(q="benchmarkneedle"),
    "selective_page2": SearchQuery(q="benchmarkneedle", page=2),
    "filters_only": SearchQuery(municipality="Covarachía"),
    "out_of_range": SearchQuery(q="benchmarkneedle", page=99),
}.items():
    samples = []
    for _ in range(10):
        started = time.perf_counter()
        result = queries.search(query)
        samples.append((time.perf_counter() - started) * 1000)
    report["api"][name] = {
        "p50_ms": statistics.median(samples),
        "p95_ms": sorted(samples)[-1],
        "samples": samples,
        "total": result["total"],
        "items": len(result["items"]),
    }
    print(name, report["api"][name])
Path(".local/search43").mkdir(parents=True, exist_ok=True)
Path(".local/search43/performance.json").write_text(
    json.dumps(report, default=str, indent=2), encoding="utf-8"
)
