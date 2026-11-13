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
    "/",
    response_model=schemas.InvoiceListResponse
)
def get_invoices(
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    payment_state: str | None = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_invoices(
        db,
        current_user.business_id,
        page,
        page_size,
        status,
        payment_state,
        overdue_only
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

@router.post(
    "/from-quote/{quote_id}",
    response_model=schemas.InvoiceResponse,
    status_code=201
)
def create_invoice_from_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_invoice_from_quote(
        db=db,
        quote_id=quote_id,
        business_id=current_user.business_id,
        user_id=current_user.id
    )