"""Base declarativa de SQLAlchemy y fábrica de sesiones, compartidas por los módulos."""

from sqlalchemy import Engine, MetaData
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Nombres estables para restricciones e índices: las migraciones no dependen del motor.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
