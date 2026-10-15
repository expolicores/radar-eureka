import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.extraction.repositories import (
    ContentFragmentRecord,
    ExtractionDiagnosticRecord,
    ExtractionRunRecord,
)


@pytest.fixture
def sessions():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS extraction"))
        ExtractionRunRecord.__table__.create(connection)
        ContentFragmentRecord.__table__.create(connection)
        ExtractionDiagnosticRecord.__table__.create(connection)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()
