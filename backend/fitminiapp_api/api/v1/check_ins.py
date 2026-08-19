from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.check_in import (
    WeeklyCheckInCurrentResponse,
    WeeklyCheckInHistoryResponse,
    WeeklyCheckInResponse,
    WeeklyCheckInSubmitRequest,
)
from fitminiapp_api.services.weekly_check_ins import (
    WeeklyCheckInConflictError,
    get_current_weekly_check_in,
    list_weekly_check_ins,
    serialize_weekly_check_in,
    submit_weekly_check_in,
)

router = APIRouter()


@router.get("/weekly/current", response_model=WeeklyCheckInCurrentResponse)
def current_weekly_check_in(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return get_current_weekly_check_in(db, current_user)


@router.get("/weekly", response_model=WeeklyCheckInHistoryResponse)
def weekly_check_in_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return list_weekly_check_ins(db, current_user, limit=limit, offset=offset)


@router.post(
    "/weekly",
    response_model=WeeklyCheckInResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_weekly_check_in(
    payload: WeeklyCheckInSubmitRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        row = submit_weekly_check_in(db, current_user, payload)
    except WeeklyCheckInConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return serialize_weekly_check_in(row)
