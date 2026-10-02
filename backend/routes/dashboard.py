from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

import crud
import models
import schemas

from database import get_db
from dependencies import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/summary",
    response_model=schemas.DashboardSummaryResponse
)
def get_dashboard_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_dashboard_summary(
        db,
        current_user.business_id,
        start_date,
        end_date
    )

@router.get(
    "",
    response_model=schemas.DashboardResponse
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_dashboard(
        db,
        current_user.business_id
    )