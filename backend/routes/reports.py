from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

import crud
import models
import schemas

from database import get_db
from dependencies import get_current_user

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get(
    "/job-performance",
    response_model=schemas.JobPerformanceResponse
)
def job_performance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_job_performance(
        db,
        current_user.business_id
    )

@router.get(
    "/monthly-revenue",
    response_model=list[schemas.MonthlyRevenue]
)
def monthly_revenue(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_monthly_revenue(
        db,
        current_user.business_id
    )

@router.get(
    "/payment-summary",
    response_model=schemas.PaymentSummaryResponse
)
def payment_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=422,
            detail="end_date must be greater than or equal to start_date"
        )

    return crud.get_payment_summary(
        db,
        current_user.business_id,
        start_date,
        end_date
    )

@router.get(
    "/payment-reversals",
    response_model=list[schemas.PaymentReversalResponse]
)
def payment_reversals(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_payment_reversals(
        db,
        current_user.business_id,
        start_date,
        end_date
    )