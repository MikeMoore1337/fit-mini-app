from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.models.feedback import WorkoutComment, WorkoutCommentRevision
from fitminiapp_api.models.program import UserProgram, UserWorkout, UserWorkoutExercise
from fitminiapp_api.models.user import CoachClient, User
from fitminiapp_api.services.notifications import queue_notification


class WorkoutCommentError(Exception):
    def __init__(self, detail: str, status_code: int = 404) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _workout_for_client(db: Session, client_id: int, workout_id: int) -> UserWorkout:
    workout = (
        db.query(UserWorkout)
        .join(UserProgram, UserProgram.id == UserWorkout.user_program_id)
        .filter(UserWorkout.id == workout_id, UserProgram.user_id == client_id)
        .first()
    )
    if workout is None:
        raise WorkoutCommentError("Тренировка не найдена")
    return workout


def _active_relation(db: Session, trainer_id: int, client_id: int) -> CoachClient:
    relation = (
        db.query(CoachClient)
        .filter(
            CoachClient.coach_user_id == trainer_id,
            CoachClient.client_user_id == client_id,
            CoachClient.status == "active",
        )
        .first()
    )
    if relation is None:
        previous_relation = (
            db.query(CoachClient.id)
            .filter(
                CoachClient.coach_user_id == trainer_id,
                CoachClient.client_user_id == client_id,
            )
            .first()
        )
        if previous_relation is None:
            raise WorkoutCommentError("Контекст клиента не найден")
        raise WorkoutCommentError("Связь с клиентом завершена", status_code=409)
    return relation


def _relation_ids_for_history(db: Session, trainer_id: int, client_id: int) -> list[int]:
    relation_ids = [
        row.id
        for row in db.query(CoachClient.id)
        .filter(
            CoachClient.coach_user_id == trainer_id,
            CoachClient.client_user_id == client_id,
        )
        .all()
    ]
    if not relation_ids:
        raise WorkoutCommentError("История работы с клиентом не найдена")
    return relation_ids


def _validate_exercise_target(
    db: Session,
    workout_id: int,
    workout_exercise_id: int | None,
) -> None:
    if workout_exercise_id is None:
        return
    exists = (
        db.query(UserWorkoutExercise.id)
        .filter(
            UserWorkoutExercise.id == workout_exercise_id,
            UserWorkoutExercise.workout_id == workout_id,
        )
        .first()
    )
    if exists is None:
        raise WorkoutCommentError("Упражнение не относится к этой тренировке")


def _comment_query(db: Session):
    return db.query(WorkoutComment).options(selectinload(WorkoutComment.revisions))


def _notification_preview(body: str, limit: int = 160) -> str:
    compact = " ".join(body.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1].rstrip()}…"


def _existing_idempotent_comment(
    db: Session,
    trainer_id: int,
    *,
    idempotency_key: str | None,
    client_id: int,
    workout_id: int,
    workout_exercise_id: int | None,
    body: str,
) -> WorkoutComment | None:
    if idempotency_key is None:
        return None
    existing = (
        _comment_query(db)
        .filter(
            WorkoutComment.trainer_author_id == trainer_id,
            WorkoutComment.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing is None:
        return None
    if (
        existing.client_user_id != client_id
        or existing.workout_id != workout_id
        or existing.workout_exercise_id != workout_exercise_id
        or existing.body != body
    ):
        raise WorkoutCommentError(
            "Ключ повторной отправки уже использован для другого комментария",
            status_code=409,
        )
    return existing


def create_workout_comment(
    db: Session,
    trainer: User,
    *,
    client_id: int,
    workout_id: int,
    workout_exercise_id: int | None,
    body: str,
    idempotency_key: str | None = None,
) -> WorkoutComment:
    replay = _existing_idempotent_comment(
        db,
        trainer.id,
        idempotency_key=idempotency_key,
        client_id=client_id,
        workout_id=workout_id,
        workout_exercise_id=workout_exercise_id,
        body=body,
    )
    if replay is not None:
        return replay

    relation = _active_relation(db, trainer.id, client_id)
    workout = _workout_for_client(db, client_id, workout_id)
    _validate_exercise_target(db, workout.id, workout_exercise_id)

    comment = WorkoutComment(
        coach_client_id=relation.id,
        trainer_author_id=trainer.id,
        client_user_id=client_id,
        workout_id=workout.id,
        workout_exercise_id=workout_exercise_id,
        idempotency_key=idempotency_key,
        body=body,
    )
    db.add(comment)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        replay = _existing_idempotent_comment(
            db,
            trainer.id,
            idempotency_key=idempotency_key,
            client_id=client_id,
            workout_id=workout_id,
            workout_exercise_id=workout_exercise_id,
            body=body,
        )
        if replay is None:
            raise WorkoutCommentError("Комментарий не удалось сохранить", status_code=409)
        return replay

    client = db.query(User).filter(User.id == client_id, User.is_active.is_(True)).first()
    if client is not None:
        action_url = (
            f"/app?workout_id={workout.id}&comment_id={comment.id}"
            "&return_to=%2Fapp%3Fsection%3Dprofile%23profile-notifications"
        )
        if workout_exercise_id is not None:
            action_url += f"&workout_exercise_id={workout_exercise_id}"
        queue_notification(
            db,
            client,
            category="trainer_comment",
            title="Комментарий тренера к тренировке",
            body=f"К тренировке «{workout.title}»: {_notification_preview(body)}",
            dedupe_key=f"trainer_feedback:{comment.id}",
            action_url=action_url,
        )

    db.commit()
    return _comment_query(db).filter(WorkoutComment.id == comment.id).one()


def list_client_workout_comments(
    db: Session,
    client: User,
    workout_id: int,
) -> list[WorkoutComment]:
    _workout_for_client(db, client.id, workout_id)
    return (
        _comment_query(db)
        .filter(
            WorkoutComment.client_user_id == client.id,
            WorkoutComment.workout_id == workout_id,
        )
        .order_by(WorkoutComment.created_at.asc(), WorkoutComment.id.asc())
        .all()
    )


def list_trainer_workout_comments(
    db: Session,
    trainer: User,
    *,
    client_id: int,
    workout_id: int,
) -> list[WorkoutComment]:
    _workout_for_client(db, client_id, workout_id)
    relation_ids = _relation_ids_for_history(db, trainer.id, client_id)
    return (
        _comment_query(db)
        .filter(
            WorkoutComment.coach_client_id.in_(relation_ids),
            WorkoutComment.client_user_id == client_id,
            WorkoutComment.workout_id == workout_id,
        )
        .order_by(WorkoutComment.created_at.asc(), WorkoutComment.id.asc())
        .all()
    )


def edit_workout_comment(
    db: Session,
    trainer: User,
    *,
    client_id: int,
    workout_id: int,
    comment_id: int,
    body: str,
) -> WorkoutComment:
    relation = _active_relation(db, trainer.id, client_id)
    _workout_for_client(db, client_id, workout_id)
    comment = (
        db.query(WorkoutComment)
        .filter(
            WorkoutComment.id == comment_id,
            WorkoutComment.coach_client_id == relation.id,
            WorkoutComment.trainer_author_id == trainer.id,
            WorkoutComment.client_user_id == client_id,
            WorkoutComment.workout_id == workout_id,
        )
        .with_for_update()
        .first()
    )
    if comment is None:
        raise WorkoutCommentError("Комментарий не найден")
    if comment.body == body:
        return _comment_query(db).filter(WorkoutComment.id == comment.id).one()

    next_revision = len(comment.revisions) + 1
    edited_at = now_msk_naive()
    db.add(
        WorkoutCommentRevision(
            comment_id=comment.id,
            revision_number=next_revision,
            body=comment.body,
            edited_by_user_id=trainer.id,
            created_at=edited_at,
        )
    )
    comment.body = body
    comment.updated_at = edited_at
    db.commit()
    return _comment_query(db).filter(WorkoutComment.id == comment.id).one()


def serialize_workout_comment(comment: WorkoutComment) -> dict:
    return {
        "id": comment.id,
        "trainer_author_id": comment.trainer_author_id,
        "client_user_id": comment.client_user_id,
        "workout_id": comment.workout_id,
        "workout_exercise_id": comment.workout_exercise_id,
        "body": comment.body,
        "body_format": "plain_text",
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "revisions": [
            {
                "id": revision.id,
                "revision_number": revision.revision_number,
                "body": revision.body,
                "edited_by_user_id": revision.edited_by_user_id,
                "created_at": revision.created_at,
            }
            for revision in comment.revisions
        ],
    }
