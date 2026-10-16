"""Test fixtures.

The tests use a temporary SQLite database. They never touch the production
database. The fixture replaces the get_db dependency of the application.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture(name="session_factory")
def session_factory_fixture():
    """Make an empty in-memory database for one test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session_factory):
    """Give a test client that writes to the test database."""

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="sample_item")
def sample_item_fixture() -> dict:
    """Give the body of a valid item."""
    return {
        "name": "Hex bolt M8",
        "sku": "BOLT-M8-001",
        "category": "fasteners",
        "quantity": 240,
        "unit_price": 0.45,
        "reorder_level": 50,
    }
