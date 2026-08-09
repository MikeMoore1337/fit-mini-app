from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fitminiapp_api.api.dependencies.auth import require_coach_or_admin, require_user
from fitminiapp_api.db.session import get_db
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.program import (
    AssignTemplateSelfRequest,
    ClientResponse,
    ExerciseCatalogCreate,
    ExerciseCatalogItem,
    ExerciseGuide,
    ProgramAssignmentResponse,
    ProgramTemplateCreate,
    ProgramTemplateCreateResponse,
    ProgramTemplateResponse,
)
from fitminiapp_api.services.exercise_catalog import (
    _effective_exercise_id,
    create_exercise,
    delete_exercise_for_user,
    list_exercises,
    update_exercise_for_user,
)
from fitminiapp_api.services.exercise_guides import get_exercise_guide
from fitminiapp_api.services.program_common import ProgramError, assignment_error_status
from fitminiapp_api.services.programs import (
    assign_template_to_self,
    build_template_response,
    build_template_responses,
    create_and_optionally_assign_program,
    delete_template_for_user,
    get_template_for_user,
    list_clients,
    list_hidden_example_templates,
    list_user_templates,
    restore_example_template_for_user,
    update_template_for_user,
)

router = APIRouter()


def _serialize_exercise(
    exercise: Exercise,
    current_user: User,
    *,
    include_guide: bool = False,
) -> dict:
    guide = get_exercise_guide(exercise)
    return {
        "id": _effective_exercise_id(exercise),
        "edit_target_id": exercise.id,
        "slug": exercise.slug,
        "title": exercise.title,
        "primary_muscle": exercise.primary_muscle,
        "equipment": exercise.equipment,
        "difficulty_level": exercise.difficulty_level,
        "is_custom": exercise.created_by_user_id is not None
        and exercise.source_exercise_id is None,
        "is_personalized": exercise.created_by_user_id == current_user.id,
        "created_by_user_id": exercise.created_by_user_id,
        "source_exercise_id": exercise.source_exercise_id,
        "has_guide": guide is not None,
        "guide": guide if include_guide else None,
    }


@router.get("/exercises", response_model=list[ExerciseCatalogItem])
def get_exercises(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    exercises = list_exercises(db, current_user)
    return [_serialize_exercise(ex, current_user) for ex in exercises]


@router.get("/exercises/{exercise_id}/guide", response_model=ExerciseGuide)
def get_exercise_guide_details(
    exercise_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    exercise = next(
        (
            row
            for row in list_exercises(db, current_user)
            if _effective_exercise_id(row) == exercise_id
        ),
        None,
    )
    if exercise is None:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    guide = get_exercise_guide(exercise)
    if guide is None:
        raise HTTPException(status_code=404, detail="Техника упражнения не заполнена")
    return guide


@router.post(
    "/exercises",
    response_model=ExerciseCatalogItem,
    status_code=status.HTTP_201_CREATED,
)
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
            difficulty_level=payload.difficulty_level,
            target_telegram_user_id=payload.target_telegram_user_id,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "No permission to manage this user":
            raise HTTPException(status_code=403, detail=detail)
        raise HTTPException(status_code=assignment_error_status(detail), detail=detail)

    return _serialize_exercise(exercise, current_user)


@router.patch("/exercises/{exercise_id}", response_model=ExerciseCatalogItem)
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
            difficulty_level=payload.difficulty_level,
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


@router.post("/templates", response_model=ProgramTemplateCreateResponse)
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


@router.get("/templates/mine", response_model=list[ProgramTemplateResponse])
def my_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    items = list_user_templates(db, current_user)
    return build_template_responses(items, db, current_user)


@router.get("/templates/hidden", response_model=list[ProgramTemplateResponse])
def hidden_templates(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    items = list_hidden_example_templates(db, current_user)
    return build_template_responses(items, db, current_user)


@router.post("/templates/{template_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_template(
    template_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        restore_example_template_for_user(db, current_user, template_id)
    except ProgramError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates/{template_id}", response_model=ProgramTemplateResponse)
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


@router.patch("/templates/{template_id}", response_model=ProgramTemplateResponse)
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


@router.post(
    "/templates/{template_id}/assign-to-me",
    response_model=ProgramAssignmentResponse,
)
def assign_template_me(
    template_id: int,
    payload: AssignTemplateSelfRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        program, created = assign_template_to_self(
            db=db,
            current_user=current_user,
            template_id=template_id,
            start_date=payload.start_date if payload else None,
            duration_weeks=payload.duration_weeks if payload else 1,
            schedule_weekdays=payload.schedule_weekdays if payload else None,
            replace_active=payload.replace_active if payload else False,
        )
    except ProgramError as exc:
        detail = str(exc)
        if detail == "Template not found":
            raise HTTPException(status_code=404, detail=detail)
        error_status = assignment_error_status(detail)
        if error_status != 400:
            raise HTTPException(status_code=error_status, detail=detail) from exc
        raise HTTPException(status_code=403, detail=detail) from exc

    return {
        "user_program_id": program.id,
        "workouts_created": created,
        "status": program.status,
        "start_date": program.start_date,
        "duration_weeks": program.duration_weeks,
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


@router.get("/clients", response_model=list[ClientResponse])
def clients(
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    return list_clients(db, current_user)
