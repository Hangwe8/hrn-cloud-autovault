from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


@router.get(
    "/{invoice_id}",
    response_model=schemas.InvoiceResponse
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_invoice(
        db,
        invoice_id,
        current_user.business_id
    )


@router.get(
    "/{invoice_id}/balance",
    response_model=schemas.InvoiceBalanceResponse
)
def get_invoice_balance(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    )
):
    return crud.get_invoice_balance(
        db,
        invoice_id,
        current_user.business_id
    )
