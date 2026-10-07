import os

os.environ["DATABASE_URL"] = (
    "postgresql://localhost/hrn_autovault_test"
)

import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import SessionLocal
import models
import security


@pytest.fixture
def db():
    database = SessionLocal()

    try:
        yield database
    finally:
        database.rollback()
        database.close()


@pytest.fixture
def test_business(db: Session):
    business = models.Business(
        name="Test Auto Workshop",
        email="test-business@example.com"
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return business


@pytest.fixture
def test_user(db: Session, test_business):
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
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield

    db = SessionLocal()

    try:
        db.query(models.User).filter(
            models.User.email == "test-user@example.com"
        ).delete(synchronize_session=False)

        db.query(models.Business).filter(
            models.Business.email == "test-business@example.com"
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()