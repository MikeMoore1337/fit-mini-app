from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.user import User
from fitminiapp_api.services.root_admin import has_verified_root_identity
from fitminiapp_api.services.security import get_current_user


def require_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_coach(user: User = Depends(require_user)) -> User:
    if not user.is_coach:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав тренера",
        )
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав администратора",
        )
    return user


def require_root_admin(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> User:
    if not has_verified_root_identity(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется подтверждённая Root-сессия Telegram",
        )
    return user
