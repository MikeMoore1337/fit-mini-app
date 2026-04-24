from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.services.security import get_current_user


def require_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_coach(user: User = Depends(require_user)) -> User:
    if not user.is_coach and not user.is_admin:
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


def require_coach_or_admin(user: User = Depends(require_user)) -> User:
    if not user.is_coach and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return user
