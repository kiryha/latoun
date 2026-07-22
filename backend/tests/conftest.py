"""Pytest fixtures: isolated SQLite DB per test + FastAPI test client.

We bind a throwaway SQLite engine for each test and override the
``get_session`` dependency so route handlers use it. The real asset manifest at
``config/asset_manifest.json`` is used (it is the default), so resolution
exercises the true registry.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_session
from app.main import app
from app.seed import (
    _upsert_assignments,
    _upsert_finish_schemes,
    _upsert_materials,
    _upsert_module_types,
)


@pytest.fixture()
def db_sessionmaker(tmp_path):
    db_path = tmp_path / "test_latoun.sqlite"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )

    with TestSessionLocal() as session:
        _upsert_materials(session)
        _upsert_module_types(session)
        _upsert_finish_schemes(session)
        _upsert_assignments(session)
        session.commit()

    yield TestSessionLocal

    engine.dispose()


@pytest.fixture()
def client(db_sessionmaker):
    def _override_get_session():
        session = db_sessionmaker()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
