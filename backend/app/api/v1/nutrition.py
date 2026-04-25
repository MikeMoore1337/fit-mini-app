from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.nutrition import NutritionTargetResponse, NutritionTargetSave
from app.services.nutrition import NutritionError, save_nutrition_target

router = APIRouter()


@router.post("/targets", response_model=NutritionTargetResponse)
def save_target(
    payload: NutritionTargetSave,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        return save_nutrition_target(db, current_user, payload)
    except NutritionError as exc:
        detail = str(exc)
        if detail == "Target user not found":
            raise HTTPException(status_code=404, detail=detail)
        if detail == "No permission to manage this user":
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
