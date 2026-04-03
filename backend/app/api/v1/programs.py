from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.program import (
    AssignTemplateRequest,
    ClientResponse,
    ExerciseCatalogCreate,
    ExerciseCatalogCreateResponse,
    ExerciseCatalogItem,
    ProgramAssignedResponse,
    ProgramTemplateCreate,
    ProgramTemplateCreateResponse,
    ProgramTemplateResponse,
)
from app.services.programs import (
    ProgramError,
    assign_demo_program,
    assign_existing_template_to_user,
    build_template_response,
    create_and_optionally_assign_program,
    create_exercise,
    list_clients,
    list_exercises,
    list_user_templates,
)
from app.services.security import get_current_user, require_coach

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/exercises", response_model=list[ExerciseCatalogItem])
def get_exercises(db: Session = Depends(get_db), user=Depends(get_current_user)):
    del user
    return [ExerciseCatalogItem(id=i.id, title=i.title, primary_muscle=i.primary_muscle, equipment=i.equipment) for i in list_exercises(db)]

@router.post("/exercises", response_model=ExerciseCatalogCreateResponse)
def add_exercise(payload: ExerciseCatalogCreate, db: Session = Depends(get_db), user=Depends(require_coach)):
    del user
    try:
        exercise = create_exercise(db, payload.title, payload.primary_muscle, payload.equipment)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExerciseCatalogCreateResponse(
        id=exercise.id,
        title=exercise.title,
        primary_muscle=exercise.primary_muscle,
        equipment=exercise.equipment,
        slug=exercise.slug,
    )


@router.get("/templates/mine", response_model=list[ProgramTemplateResponse])
def my_templates(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [ProgramTemplateResponse(**build_template_response(item)) for item in list_user_templates(db, user)]


@router.post("/templates", response_model=ProgramTemplateCreateResponse)
def create_template(payload: ProgramTemplateCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        template, assigned_program, workouts_created, target_user = create_and_optionally_assign_program(db, user, payload)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProgramTemplateCreateResponse(
        template=ProgramTemplateResponse(**build_template_response(template)),
        assigned_program_id=assigned_program.id if assigned_program else None,
        assigned_to_telegram_user_id=target_user.telegram_user_id if assigned_program else None,
        assigned_to_name=target_user.profile.full_name if target_user.profile else None,
        workouts_created=workouts_created,
    )


@router.post("/templates/{template_id}/assign", response_model=ProgramAssignedResponse)
def assign_existing_template(template_id: int, payload: AssignTemplateRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        user_program, workouts_created, _target_user = assign_existing_template_to_user(db, user, template_id, payload.target_telegram_user_id, payload.target_full_name)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProgramAssignedResponse(program_id=user_program.id, title=user_program.template.title, workouts_created=workouts_created)


@router.get("/clients", response_model=list[ClientResponse])
def get_clients(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [
        ClientResponse(
            user_id=row.id,
            telegram_user_id=row.telegram_user_id,
            full_name=row.profile.full_name if row.profile else None,
            goal=row.profile.goal if row.profile else None,
            level=row.profile.level if row.profile else None,
            is_coach=row.is_coach,
        )
        for row in list_clients(db, user)
    ]


@router.post("/assign-demo", response_model=ProgramAssignedResponse)
def assign_program(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        program, workouts_created = assign_demo_program(db, user)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProgramAssignedResponse(program_id=program.id, title=program.template.title, workouts_created=workouts_created)
