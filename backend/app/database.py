"""SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite disables FK enforcement by default; turn it on per connection.

    Required so ``material_assignments`` rows cascade-delete with their finish
    scheme and so material foreign keys are enforced.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _create_engine():
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _migrate_configuration_finish_scheme(bind) -> None:
    """Migrate the legacy ``configurations.material_code`` column.

    Earlier iterations stored a single global ``material_code`` per saved
    configuration. Configurations now store ``finish_scheme_code``. Existing
    values map one-to-one (``brass`` -> ``brass`` finish scheme, etc.), so a
    plain column rename preserves the data. New databases already have the
    correct column and are skipped.
    """
    inspector = inspect(bind)
    if "configurations" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("configurations")}
    if "finish_scheme_code" in columns or "material_code" not in columns:
        return
    with bind.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE configurations "
                "RENAME COLUMN material_code TO finish_scheme_code"
            )
        )


def init_database() -> None:
    """Create all tables if they do not yet exist, then apply lightweight migrations."""
    from . import models  # noqa: F401  (ensure models are registered)

    # Migrate the legacy column before create_all so the rebuilt schema is
    # consistent for both fresh and existing databases.
    _migrate_configuration_finish_scheme(engine)
    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
