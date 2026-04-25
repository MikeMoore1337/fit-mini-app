from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_coach_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.program import CoachClientCreate
from app.services.programs import (
    ProgramError,
    add_client_for_coach,
    list_clients,
    remove_client_for_coach,
    remove_pending_client_invite,
)

router = APIRouter()


@router.get("/clients")
def coach_clients(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    return list_clients(db, current_user)


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def add_coach_client(
    payload: CoachClientCreate,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        return add_client_for_coach(
            db=db,
            coach=current_user,
            telegram_user_id=payload.telegram_user_id,
            username=payload.username,
            full_name=payload.full_name,
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client(
    client_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        remove_client_for_coach(db, current_user, client_id)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Client link not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)


@router.delete("/client-invites/{username}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coach_client_invite(
    username: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    try:
        remove_pending_client_invite(db, current_user, username)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Client invite not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
