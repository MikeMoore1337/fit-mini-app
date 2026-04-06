from app.api.dependencies.auth import require_coach_or_admin, require_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.program import ProgramTemplateCreate
from app.services.programs import (
    ProgramError,
    build_template_response,
    create_and_optionally_assign_program,
    create_exercise,
    delete_template_for_user,
    list_clients,
    list_exercises,
    list_user_templates,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/exercises")
def get_exercises(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    exercises = list_exercises(db, current_user)
    return [
        {
            "id": ex.id,
            "slug": ex.slug,
            "title": ex.title,
            "primary_muscle": ex.primary_muscle,
            "equipment": ex.equipment,
            "is_custom": ex.created_by_user_id is not None,
            "created_by_user_id": ex.created_by_user_id,
        }
        for ex in exercises
    ]


@router.post("/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(
    payload: dict,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        exercise = create_exercise(
            db=db,
            current_user=current_user,
            title=(payload.get("title") or "").strip(),
            primary_muscle=(payload.get("primary_muscle") or "").strip(),
            equipment=(payload.get("equipment") or "").strip(),
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "id": exercise.id,
        "slug": exercise.slug,
        "title": exercise.title,
        "primary_muscle": exercise.primary_muscle,
        "equipment": exercise.equipment,
        "is_custom": True,
        "created_by_user_id": exercise.created_by_user_id,
    }


@router.post("/templates")
def create_template(
    payload: ProgramTemplateCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        template, assigned_program, workouts_created, target_user = (
            create_and_optionally_assign_program(
                db=db,
                current_user=current_user,
                payload=payload,
            )
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "template": build_template_response(template),
        "assigned_program_id": assigned_program.id if assigned_program else None,
        "workouts_created": workouts_created,
        "target_user": target_user,
    }


@router.get("/templates/mine")
def my_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    items = list_user_templates(db, current_user)
    return [build_template_response(item) for item in items]


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_template_for_user(db, current_user, template_id)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=403, detail=detail)


@router.get("/clients")
def clients(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    items = list_clients(db, current_user)
    return [
        {
            "id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "username": user.username,
            "full_name": user.profile.full_name if user.profile else None,
            "goal": user.profile.goal if user.profile else None,
            "level": user.profile.level if user.profile else None,
        }
        for user in items
    ]
