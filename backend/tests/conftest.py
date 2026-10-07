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
        test_business = (
            db.query(models.Business)
            .filter(
                models.Business.email == "test-business@example.com"
            )
            .first()
        )

        second_business = (
            db.query(models.Business)
            .filter(
                models.Business.email == "second-business@example.com"
            )
            .first()
        )

        business_ids = [
            business.id
            for business in [test_business, second_business]
            if business is not None
        ]

        if business_ids:
            db.query(models.Vehicle).filter(
                models.Vehicle.business_id.in_(business_ids)
            ).delete(synchronize_session=False)
            
            db.query(models.Customer).filter(
                models.Customer.business_id.in_(business_ids)
            ).delete(synchronize_session=False)

        db.query(models.User).filter(
            models.User.email.in_([
                "test-user@example.com",
                "second-user@example.com"
            ])
        ).delete(synchronize_session=False)

        if business_ids:
            db.query(models.Business).filter(
                models.Business.id.in_(business_ids)
            ).delete(synchronize_session=False)

        db.commit()

    finally:
        db.close()

@pytest.fixture
def second_business(db: Session):
    business = models.Business(
        name="Second Test Workshop",
        email="second-business@example.com"
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return business

@pytest.fixture
def second_user(db: Session, second_business):
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
    db.commit()
    db.refresh(user)

    return user