from fastapi import HTTPException, Request, status

from app.models.user import User


def get_current_user_from_request(request: Request) -> User | None:
    return getattr(request.state, "user", None)


def require_user(request: Request) -> User:
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return user


def require_coach(request: Request) -> User:
    user = require_user(request)
    if not user.is_coach and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав тренера",
        )
    return user


def require_admin(request: Request) -> User:
    user = require_user(request)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав администратора",
        )
    return user


def require_coach_or_admin(request: Request) -> User:
    user = require_user(request)
    if not user.is_coach and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return user
