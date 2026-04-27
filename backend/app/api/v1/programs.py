from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_coach_or_admin, require_user
from app.db.session import get_db
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.program import CoachClientCreate, ExerciseCatalogCreate, ProgramTemplateCreate
from app.services.programs import (
    ProgramError,
    _effective_exercise_id,
    add_client_for_coach,
    assign_template_to_self,
    build_template_response,
    create_and_optionally_assign_program,
    create_exercise,
    delete_exercise_for_user,
    delete_template_for_user,
    get_template_for_user,
    list_clients,
    list_exercises,
    list_user_templates,
    update_exercise_for_user,
    update_template_for_user,
)

router = APIRouter()


def _serialize_exercise(exercise: Exercise, current_user: User) -> dict:
    return {
        "id": _effective_exercise_id(exercise),
        "edit_target_id": exercise.id,
        "slug": exercise.slug,
        "title": exercise.title,
        "primary_muscle": exercise.primary_muscle,
        "equipment": exercise.equipment,
        "is_custom": exercise.created_by_user_id is not None
        and exercise.source_exercise_id is None,
        "is_personalized": exercise.created_by_user_id == current_user.id,
        "created_by_user_id": exercise.created_by_user_id,
        "source_exercise_id": exercise.source_exercise_id,
    }


@router.get("/exercises")
def get_exercises(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    exercises = list_exercises(db, current_user)
    return [_serialize_exercise(ex, current_user) for ex in exercises]


@router.post("/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(
    payload: ExerciseCatalogCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        exercise = create_exercise(
            db=db,
            current_user=current_user,
            title=payload.title.strip(),
            primary_muscle=payload.primary_muscle,
            equipment=payload.equipment,
            target_telegram_user_id=payload.target_telegram_user_id,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "No permission to manage this user":
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)

    return _serialize_exercise(exercise, current_user)


@router.patch("/exercises/{exercise_id}")
def edit_exercise(
    exercise_id: int,
    payload: ExerciseCatalogCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        exercise = update_exercise_for_user(
            db=db,
            current_user=current_user,
            exercise_id=exercise_id,
            title=payload.title.strip(),
            primary_muscle=payload.primary_muscle,
            equipment=payload.equipment,
            target_telegram_user_id=payload.target_telegram_user_id,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Exercise not found":
            raise HTTPException(status_code=404, detail=detail)
        if detail in {"No permission to edit exercise", "No permission to manage this user"}:
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)

    return _serialize_exercise(exercise, current_user)


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_exercise(
    exercise_id: int,
    target_telegram_user_id: int | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        delete_exercise_for_user(
            db=db,
            current_user=current_user,
            exercise_id=exercise_id,
            target_telegram_user_id=target_telegram_user_id,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Exercise not found":
            raise HTTPException(status_code=404, detail=detail)
        if detail in {"No permission to delete exercise", "No permission to manage this user"}:
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)


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
        detail = str(exc)
        if detail == "No permission to manage this user":
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)

    return {
        "template": build_template_response(template, db, current_user),
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
    return [build_template_response(item, db, current_user) for item in items]


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        template = get_template_for_user(db, current_user, template_id)
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=403, detail=detail)

    return build_template_response(template, db, current_user)


@router.patch("/templates/{template_id}")
def edit_template(
    template_id: int,
    payload: ProgramTemplateCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        template = update_template_for_user(
            db=db,
            current_user=current_user,
            template_id=template_id,
            payload=payload,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail)
        if detail in {"No permission to edit template", "No permission to manage this user"}:
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=400, detail=detail)

    return build_template_response(template, db, current_user)


@router.post("/templates/{template_id}/assign-to-me")
def assign_template_me(
    template_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        program, created = assign_template_to_self(
            db=db,
            current_user=current_user,
            template_id=template_id,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=403, detail=detail)

    return {
        "user_program_id": program.id,
        "workouts_created": created,
    }


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
    return list_clients(db, current_user)


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def add_client(
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
