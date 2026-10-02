from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)


@router.post("/")
def register_business(
    onboarding: schemas.OnboardingRequest,
    db: Session = Depends(get_db)
):
    business, owner = crud.register_business(
        db,
        onboarding
    )

    return {
        "message": "Business registered successfully",
        "business": {
            "id": business.id,
            "name": business.name,
            "email": business.email
        },
        "owner": {
            "id": owner.id,
            "name": owner.name,
            "email": owner.email,
            "role": owner.role
        }
    }
