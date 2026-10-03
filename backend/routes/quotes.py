from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_db
from dependencies import get_current_user
from permissions import require_roles


router = APIRouter(
    prefix="/quotes",
    tags=["Quotes"]
)


@router.post(
    "/",
    response_model=schemas.QuoteResponse
)
def create_quote(
    quote: schemas.QuoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.create_quote(db, quote, current_user.business_id)

@router.get(
    "/",
    response_model=schemas.QuoteListResponse
)
def get_quotes(
    page: int = 1,
    page_size: int = 25,
    status: schemas.QuoteStatus | None = None,
    job_card_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_quotes(
        db,
        current_user.business_id,
        page,
        page_size,
        status,
        job_card_id
    )

@router.get(
    "/{quote_id}",
    response_model=schemas.QuoteResponse
)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_quote(
        db,
        quote_id,
        current_user.business_id
    )

@router.patch(
    "/{quote_id}/status",
    response_model=schemas.QuoteResponse
)
def update_quote_status(
    quote_id: int,
    update: schemas.QuoteStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.update_quote_status(
        db,
        quote_id,
        update.status,
        current_user.business_id,
        current_user.id
    )

@router.post(
    "/{quote_id}/invoice",
    response_model=schemas.InvoiceResponse
)
def create_invoice_from_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN", "MANAGER"))
):
    return crud.create_invoice_from_quote(
        db,
        quote_id,
        current_user.business_id,
        current_user.id
    )

