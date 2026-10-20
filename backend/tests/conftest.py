import os

TEST_DATABASE_URL = (
    "postgresql://localhost/hrn_autovault_test"
)

# Set this before importing the application or database engine.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

if "hrn_autovault_test" not in TEST_DATABASE_URL:
    raise RuntimeError("Refusing to run tests on a non-test database")

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from main import app
from database import engine, get_db
import models
import security


@pytest.fixture
def db():
    connection = engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False
    )

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if (
            transaction.nested
            and transaction._parent is not None
            and not transaction._parent.nested
        ):
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def test_business(db):
    business = models.Business(
        name="Test Auto Workshop",
        email="test-business@example.com"
    )

    db.add(business)
    db.flush()

    return business


@pytest.fixture
def test_user(db, test_business):
    user = models.User(
        business_id=test_business.id,
        name="Test User",
        email="test-user@example.com",
        password_hash=security.hash_password(
            "TestPassword123!"
        ),
        role="OWNER"
    )

    db.add(user)
    db.flush()

    return user


@pytest.fixture
def second_business(db):
    business = models.Business(
        name="Second Test Workshop",
        email="second-business@example.com"
    )

    db.add(business)
    db.flush()

    return business


@pytest.fixture
def second_user(db, second_business):
    user = models.User(
        business_id=second_business.id,
        name="Second User",
        email="second-user@example.com",
        password_hash=security.hash_password(
            "SecondPassword123!"
        ),
        role="OWNER"
    )

    db.add(user)
    db.flush()

    return user