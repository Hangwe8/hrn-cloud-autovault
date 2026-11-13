from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user
from permissions import require_roles


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.post(
    "/",
    response_model=schemas.CustomerResponse
)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.create_customer(db, customer, current_user.business_id)

@router.get(
    "/",
    response_model=schemas.CustomerListResponse
)
def get_customers(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if include_archived and current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view archived customers."
        )
    
    return crud.get_customers(
        db,
        current_user.business_id,
        page,
        page_size,
        search,
        include_archived
    )

@router.patch(
    "/{customer_id}",
    response_model=schemas.CustomerResponse
)

def update_customer(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN", "MANAGER")
    )

):

    return crud.update_customer(
        db,
        customer_id,
        customer_update,
        current_user.business_id
    )

@router.delete(
    "/{customer_id}"
)

def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN")
    )
):

    return crud.delete_customer(
        db,
        customer_id,
        current_user.business_id,
        current_user.id

    )

@router.post(
    "/{customer_id}/restore",
    response_model=schemas.CustomerResponse
)
def restore_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN")
    )
):
    return crud.restore_customer(
        db,
        customer_id,
        current_user.business_id,
        current_user.id
    )

@router.get(
    "/{customer_id}/vehicles",
    response_model=schemas.CustomerVehicleSummaryResponse
)
def get_customer_vehicle_summary(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_customer_vehicle_summary(
        db,
        current_user.business_id,
        customer_id
    )

@router.get(
    "/{customer_id}",
    response_model=schemas.CustomerResponse
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_customer(
        db,
        customer_id,
        current_user.business_id
    )

@router.get(
    "/{customer_id}",
    response_model=schemas.CustomerResponse
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_customer(
        db,
        customer_id,
        current_user.business_id
    )
