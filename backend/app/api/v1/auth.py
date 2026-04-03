from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import DevLoginRequest, TelegramInitRequest, TokenPairResponse
from app.services.security import (
    AuthError,
    create_refresh_token,
    decode_token,
    get_or_create_debug_user,
    get_or_create_user_from_telegram,
    issue_token_pair,
    verify_telegram_init_data,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram/init", response_model=TokenPairResponse)
def telegram_init(payload: TelegramInitRequest, db: Session = Depends(get_db)):
    try:
        user_payload = verify_telegram_init_data(payload.init_data)
        user = get_or_create_user_from_telegram(db, user_payload)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenPairResponse(**issue_token_pair(user))


@router.post("/dev-login", response_model=TokenPairResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    user = get_or_create_debug_user(db, payload.telegram_user_id, payload.full_name, payload.is_coach)
    return TokenPairResponse(**issue_token_pair(user))


@router.post("/refresh", response_model=TokenPairResponse)
def refresh_token(payload: TokenPairResponse, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    from app.models.user import User

    user = db.query(User).filter(User.id == int(data["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenPairResponse(**issue_token_pair(user))
