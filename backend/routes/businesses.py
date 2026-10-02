from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas

from database import get_db


router = APIRouter(
    prefix="/businesses",
    tags=["Businesses"]
)


@router.post(
    "/",
    response_model=schemas.BusinessResponse
)
def create_business(
    business: schemas.BusinessCreate,
    db: Session = Depends(get_db)
):
    return crud.create_business(db, business)