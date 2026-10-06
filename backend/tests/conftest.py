import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.db.session import engine
from app.main import app


@pytest.fixture
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction.is_active:
            session.begin_nested()

    from sqlalchemy import event

    event.listen(session, "after_transaction_end", restart_savepoint)
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
