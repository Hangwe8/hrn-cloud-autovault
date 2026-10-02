from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import models
import schemas

from database import get_db
from dependencies import get_current_user
from permissions import require_roles


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post(
    "/",
    response_model=schemas.PaymentResponse
)
def create_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(
            "OWNER",
            "ADMIN",
            "MANAGER"
        )
    )
):
    return crud.create_payment(
        db,
        payment,
        current_user.business_id,
        current_user.id
    )

@router.get(
    "/invoice/{invoice_id}",
    response_model=list[schemas.PaymentResponse]
)
def get_invoice_payments(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    )
):
    return crud.get_invoice_payments(
        db,
        invoice_id,
        current_user.business_id
    )

@router.post(
    "/{payment_id}/reverse",
    response_model=schemas.PaymentResponse
)
def reverse_payment(
    payment_id: int,
    request: schemas.PaymentReverseRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("OWNER", "ADMIN", "MANAGER")
    )
):
    return crud.reverse_payment(
        db,
        payment_id,
        request.reason,
        current_user.business_id,
        current_user.id
    )