from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user
from permissions import require_roles

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


@router.post(
    "/",
    response_model=schemas.VehicleResponse
)
def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.create_vehicle(db, vehicle, current_user.business_id)


@router.get(
    "/",
    response_model=schemas.VehicleListResponse
)
def get_vehicles(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_vehicles(
        db,
        current_user.business_id,
        page,
        page_size,
        search,
        include_archived
    )

@router.get(
    "/{vehicle_id}",
    response_model=schemas.VehicleResponse
)

def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    return crud.get_vehicle(
        db,
        vehicle_id,
        current_user.business_id
    )

@router.patch(
    "/{vehicle_id}",
    response_model=schemas.VehicleResponse
)

def update_vehicle(
    vehicle_id: int,
    vehicle_update: schemas.VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN", "MANAGER")
    )

):
    return crud.update_vehicle(
        db,
        vehicle_id,
        vehicle_update,
        current_user.business_id
    )

@router.delete(
    "/{vehicle_id}"
)

def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN")
    )

):

    return crud.delete_vehicle(
        db,
        vehicle_id,
        current_user.business_id,
        current_user.id

    )