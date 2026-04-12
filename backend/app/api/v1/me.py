from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse
from app.services.profile import update_profile
from app.services.security import get_current_user

router = APIRouter()


@router.get("", response_model=UserResponse)
def read_me(user=Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_coach=user.is_coach,
        is_admin=user.is_admin,
        profile=UserProfileResponse(
            full_name=user.profile.full_name if user.profile else None,
            goal=user.profile.goal if user.profile else None,
            level=user.profile.level if user.profile else None,
            height_cm=user.profile.height_cm if user.profile else None,
            weight_kg=user.profile.weight_kg if user.profile else None,
            workouts_per_week=user.profile.workouts_per_week if user.profile else None,
        )
        if user.profile
        else None,
    )


@router.patch("/profile", response_model=UserResponse)
def patch_profile(
    payload: UserProfileUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    user = update_profile(db, user, payload)
    return read_me(user)
