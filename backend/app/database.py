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

    Required so ``material_assignments`` / ``assignment_state_modules`` cascade
    correctly and foreign keys are enforced.
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


def _drop_legacy_configurations_table(bind) -> None:
    """Remove the unused legacy ``configurations`` table if it still exists."""
    inspector = inspect(bind)
    if "configurations" not in inspector.get_table_names():
        return
    with bind.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS configurations"))


def _ensure_module_type_columns(bind) -> None:
    """Add newer ``module_types`` columns on existing SQLite databases."""
    inspector = inspect(bind)
    if "module_types" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("module_types")}
    statements: list[str] = []
    if "is_customer_visible" not in existing:
        statements.append(
            "ALTER TABLE module_types "
            "ADD COLUMN is_customer_visible BOOLEAN NOT NULL DEFAULT 1"
        )
    if "sort_order" not in existing:
        statements.append(
            "ALTER TABLE module_types "
            "ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"
        )
    if not statements:
        return
    with bind.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def init_database() -> None:
    """Create all tables if they do not yet exist, then apply lightweight migrations."""
    from . import models  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)
    _drop_legacy_configurations_table(engine)
    _ensure_module_type_columns(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
