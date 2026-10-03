from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user
from permissions import require_roles


router = APIRouter(
    prefix="/job-cards",
    tags=["Job Cards"]
)


@router.post(
    "/",
    response_model=schemas.JobCardResponse
)
def create_job_card(
    job_card: schemas.JobCardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.create_job_card(db, job_card, current_user.business_id, current_user.id)


@router.get(
    "/",
    response_model=schemas.JobCardListResponse
)
def get_job_cards(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    status: schemas.JobStatus | None = None,
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_job_cards(
        db,
        current_user.business_id,
        page,
        page_size,
        search,
        status,
        vehicle_id
    )

@router.get(

    "/{job_card_id}",

    response_model=schemas.JobCardResponse

)

def get_job_card(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_job_card(
        db,
        job_card_id,
        current_user.business_id
    )

@router.patch(
    "/{job_card_id}/status",
    response_model=schemas.JobCardResponse
)
def update_job_card_status(
    job_card_id: int,
    update: schemas.JobCardStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.update_job_card_status(
        db,
        job_card_id,
        update.status,
        update.final_cost,
        update.assigned_staff_id,
        current_user.business_id,
        current_user.id
    )
