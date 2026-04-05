from app.api.dependencies.auth import require_user
from app.db.session import get_db
from app.models.program import (
    ProgramTemplate,
    ProgramTemplateDay,
    ProgramTemplateExercise,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from app.models.user import User, UserProfile
from app.schemas.program import ProgramTemplateCreate
from app.services.programs import (
    ProgramError,
    assign_demo_program,
    build_template_response,
    create_and_optionally_assign_program,
    create_exercise,
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
    exercises = list_exercises(db)
    return [
        {
            "id": ex.id,
            "slug": ex.slug,
            "title": ex.title,
            "primary_muscle": ex.primary_muscle,
            "equipment": ex.equipment,
        }
        for ex in exercises
    ]


@router.post("/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(
    payload: dict,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_coach and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    try:
        exercise = create_exercise(
            db=db,
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
    }


@router.post("/templates")
def create_template(
    payload: ProgramTemplateCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        template, assigned_program, workouts_created, target_user = create_and_optionally_assign_program(
            db=db,
            current_user=current_user,
            payload=payload,
        )
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    target_profile = db.query(UserProfile).filter(UserProfile.user_id == target_user.id).first()

    return {
        "template": build_template_response(template),
        "assigned_program_id": assigned_program.id if assigned_program else None,
        "workouts_created": workouts_created,
        "target_user": {
            "id": target_user.id,
            "telegram_user_id": target_user.telegram_user_id,
            "full_name": target_profile.full_name if target_profile else None,
        },
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
    template = db.query(ProgramTemplate).filter(ProgramTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    can_delete = (
        current_user.is_admin
        or current_user.is_coach
        or template.owner_user_id == current_user.id
        or template.created_by_user_id == current_user.id
    )

    if not can_delete:
        raise HTTPException(status_code=403, detail="Нет прав на удаление шаблона")

    user_programs = db.query(UserProgram).filter(UserProgram.template_id == template.id).all()
    user_program_ids = [item.id for item in user_programs]

    if user_program_ids:
        workouts = db.query(UserWorkout).filter(UserWorkout.user_program_id.in_(user_program_ids)).all()
        workout_ids = [item.id for item in workouts]

        if workout_ids:
            workout_exercises = db.query(UserWorkoutExercise).filter(UserWorkoutExercise.workout_id.in_(workout_ids)).all()
            workout_exercise_ids = [item.id for item in workout_exercises]

            if workout_exercise_ids:
                db.query(UserWorkoutSet).filter(
                    UserWorkoutSet.workout_exercise_id.in_(workout_exercise_ids)
                ).delete(synchronize_session=False)

                db.query(UserWorkoutExercise).filter(
                    UserWorkoutExercise.id.in_(workout_exercise_ids)
                ).delete(synchronize_session=False)

            db.query(UserWorkout).filter(
                UserWorkout.id.in_(workout_ids)
            ).delete(synchronize_session=False)

        db.query(UserProgram).filter(
            UserProgram.id.in_(user_program_ids)
        ).delete(synchronize_session=False)

    days = db.query(ProgramTemplateDay).filter(ProgramTemplateDay.program_id == template.id).all()
    day_ids = [item.id for item in days]

    if day_ids:
        db.query(ProgramTemplateExercise).filter(
            ProgramTemplateExercise.day_id.in_(day_ids)
        ).delete(synchronize_session=False)

        db.query(ProgramTemplateDay).filter(
            ProgramTemplateDay.id.in_(day_ids)
        ).delete(synchronize_session=False)

    db.delete(template)
    db.commit()


@router.get("/clients")
def clients(
    current_user: User = Depends(require_user),
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


@router.post("/assign-demo")
def assign_demo(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        program, created = assign_demo_program(db, current_user)
    except ProgramError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "user_program_id": program.id,
        "workouts_created": created,
    }
