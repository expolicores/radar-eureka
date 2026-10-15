"""FTS español y normalización: sin tablas nuevas ni DML de negocio.

Revision ID: 0014_transversal_search
Revises: 0013_ocr_diagnostics
"""

from alembic import op

revision = "0014_transversal_search"
down_revision = "0013_ocr_diagnostics"
branch_labels = None
depends_on = None

INDEXES = {
    "ingestion.ix_search_process_fts": """CREATE INDEX ix_search_process_fts
        ON ingestion.secop_process USING gin
        (to_tsvector('spanish'::regconfig, public.search_normalize_v1(
         coalesce(title,'') || ' ' || coalesce(description,'') || ' ' ||
         coalesce(reference,'') || ' ' || coalesce(id_del_proceso,'') || ' ' ||
         coalesce(entity_name,'') || ' ' || coalesce(department,'') || ' ' ||
         coalesce(municipality,'') || ' ' || coalesce(category_code,''))))""",
    "extraction.ix_search_canonical_fts": """CREATE INDEX ix_search_canonical_fts
        ON extraction.canonical_fact USING gin
        (to_tsvector('spanish'::regconfig, public.search_normalize_v1(
         public.search_values_v1(canonical_value->'value'))))""",
    "extraction.ix_search_structured_fts": """CREATE INDEX ix_search_structured_fts
        ON extraction.structured_fact USING gin
        (to_tsvector('spanish'::regconfig, public.search_normalize_v1(
         coalesce(string_value,'') || ' ' ||
         public.search_values_v1(normalized_value))))""",
    "extraction.ix_search_fragment_fts": """CREATE INDEX ix_search_fragment_fts
        ON extraction.content_fragment USING gin
        (to_tsvector('spanish'::regconfig, public.search_normalize_v1(normalized_text)))""",
}


def upgrade():
    op.execute("""CREATE FUNCTION public.search_normalize_v1(value text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
        SELECT trim(regexp_replace(regexp_replace(normalize(lower(coalesce(value,'')),NFKD),
            U&'[\\0300-\\036f]', '', 'g'), '[^a-z0-9]+', ' ', 'g')) $$""")
    op.execute("""CREATE FUNCTION public.search_values_v1(value jsonb) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
        SELECT coalesce(string_agg(item #>> '{}',' '),'') FROM
            jsonb_path_query(coalesce(value,'null'::jsonb),
                '$.** ? (@.type() == "string" || @.type() == "number")') AS item $$""")
    for sql in INDEXES.values():
        op.execute(sql)


def downgrade():
    for name in reversed(INDEXES):
        op.execute(f"DROP INDEX {name}")
    op.execute("DROP FUNCTION public.search_values_v1(jsonb)")
    op.execute("DROP FUNCTION public.search_normalize_v1(text)")
