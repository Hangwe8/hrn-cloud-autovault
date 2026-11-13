from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user
from permissions import require_roles


router = APIRouter(
    prefix="/service-records",
    tags=["Service History"]
)


@router.post(
    "/",
    response_model=schemas.ServiceRecordResponse
)
def create_service_record(
    service: schemas.ServiceRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):

    return crud.create_service_record(
        db,
        service,
        current_user.business_id
    )


@router.get(
    "/vehicle/{vehicle_id}",
    response_model=list[schemas.ServiceRecordResponse],
)
def get_service_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_service_history(
        db,
        current_user.business_id,
        vehicle_id,
    )


@router.get(
    "/{service_record_id}",
    response_model=schemas.ServiceRecordResponse
)

def get_service_record(
    service_record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    return crud.get_service_record(
        db,
        service_record_id,
        current_user.business_id

    )

@router.get(
    "/",
    response_model=schemas.ServiceRecordListResponse,
)
def get_service_records(
    page: int = 1,
    page_size: int = 25,
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_service_records(
        db,
        current_user.business_id,
        page,
        page_size,
        vehicle_id,
    )