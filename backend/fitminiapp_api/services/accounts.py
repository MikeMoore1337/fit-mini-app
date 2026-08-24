from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fitminiapp_api.models.account import AccountDataExport
from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.auth_identity import AuthActionToken, AuthIdentity, LocalCredential
from fitminiapp_api.models.billing import Payment, Subscription
from fitminiapp_api.models.check_in import WeeklyCheckIn
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.feedback import WorkoutComment, WorkoutCommentRevision
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.nutrition import EnergyCalibration, NutritionTarget
from fitminiapp_api.models.program import (
    HiddenProgramTemplate,
    ProgramRevision,
    ProgramTemplate,
    TrainingBlock,
    TrainingBlockPriorityMuscle,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.support import BotSupportCase
from fitminiapp_api.models.token import RefreshToken
from fitminiapp_api.models.user import (
    BodyMeasurement,
    CoachClient,
    CoachClientInvite,
    CoachRoleApplication,
    User,
    UserProfile,
    UserProfilePriorityMuscle,
)
from fitminiapp_api.services.account_export import build_account_export
from fitminiapp_api.services.programs import delete_template_cascade

__all__ = ["build_account_export", "delete_user_cascade"]


def _delete_user_programs(db: Session, user_program_ids: list[int]) -> None:
    if not user_program_ids:
        return
    workout_ids = [
        row.id
        for row in db.query(UserWorkout.id)
        .filter(UserWorkout.user_program_id.in_(user_program_ids))
        .all()
    ]
    workout_exercise_ids = (
        [
            row.id
            for row in db.query(UserWorkoutExercise.id)
            .filter(UserWorkoutExercise.workout_id.in_(workout_ids))
            .all()
        ]
        if workout_ids
        else []
    )
    if workout_exercise_ids:
        db.query(UserWorkoutSet).filter(
            UserWorkoutSet.workout_exercise_id.in_(workout_exercise_ids)
        ).delete(synchronize_session=False)
        db.query(UserWorkoutExercise).filter(
            UserWorkoutExercise.id.in_(workout_exercise_ids)
        ).delete(synchronize_session=False)
    if workout_ids:
        comment_ids = [
            row.id
            for row in db.query(WorkoutComment.id)
            .filter(WorkoutComment.workout_id.in_(workout_ids))
            .all()
        ]
        if comment_ids:
            db.query(Notification).filter(
                Notification.dedupe_key.in_(
                    [f"trainer_feedback:{comment_id}" for comment_id in comment_ids]
                )
            ).delete(synchronize_session=False)
            db.query(WorkoutCommentRevision).filter(
                WorkoutCommentRevision.comment_id.in_(comment_ids)
            ).delete(synchronize_session=False)
            db.query(WorkoutComment).filter(WorkoutComment.id.in_(comment_ids)).delete(
                synchronize_session=False
            )
        db.query(UserWorkout).filter(UserWorkout.id.in_(workout_ids)).delete(
            synchronize_session=False
        )
    block_ids = [
        row.id
        for row in db.query(TrainingBlock.id)
        .filter(TrainingBlock.user_program_id.in_(user_program_ids))
        .all()
    ]
    if block_ids:
        db.query(TrainingBlockPriorityMuscle).filter(
            TrainingBlockPriorityMuscle.training_block_id.in_(block_ids)
        ).delete(synchronize_session=False)
        db.query(TrainingBlock).filter(TrainingBlock.id.in_(block_ids)).delete(
            synchronize_session=False
        )
    db.query(ProgramRevision).filter(ProgramRevision.user_program_id.in_(user_program_ids)).delete(
        synchronize_session=False
    )
    db.query(UserProgram).filter(UserProgram.id.in_(user_program_ids)).delete(
        synchronize_session=False
    )


def delete_user_cascade(db: Session, user: User) -> None:
    """Delete one account while preserving other users' historical snapshots."""

    if user.telegram_user_id is not None:
        db.query(BotSupportCase).filter(
            BotSupportCase.telegram_user_id == user.telegram_user_id
        ).delete(synchronize_session=False)

    db.query(HiddenProgramTemplate).filter(HiddenProgramTemplate.user_id == user.id).delete(
        synchronize_session=False
    )
    owned_templates = (
        db.query(ProgramTemplate)
        .filter(
            or_(
                ProgramTemplate.owner_user_id == user.id,
                ProgramTemplate.created_by_user_id == user.id,
            )
        )
        .all()
    )
    for template in owned_templates:
        delete_template_cascade(db, template)
        db.flush()

    own_program_ids = [
        row.id for row in db.query(UserProgram.id).filter(UserProgram.user_id == user.id).all()
    ]
    _delete_user_programs(db, own_program_ids)
    db.query(ProgramRevision).filter(ProgramRevision.changed_by_user_id == user.id).update(
        {ProgramRevision.changed_by_user_id: None},
        synchronize_session=False,
    )
    db.query(TrainingBlock).filter(TrainingBlock.created_by_user_id == user.id).update(
        {TrainingBlock.created_by_user_id: None},
        synchronize_session=False,
    )
    remaining_comment_ids = [
        row.id
        for row in db.query(WorkoutComment.id)
        .filter(
            or_(
                WorkoutComment.trainer_author_id == user.id,
                WorkoutComment.client_user_id == user.id,
            )
        )
        .all()
    ]
    if remaining_comment_ids:
        db.query(Notification).filter(
            Notification.dedupe_key.in_(
                [f"trainer_feedback:{comment_id}" for comment_id in remaining_comment_ids]
            )
        ).delete(synchronize_session=False)
        db.query(WorkoutCommentRevision).filter(
            WorkoutCommentRevision.comment_id.in_(remaining_comment_ids)
        ).delete(synchronize_session=False)
        db.query(WorkoutComment).filter(WorkoutComment.id.in_(remaining_comment_ids)).delete(
            synchronize_session=False
        )
    db.query(UserProgram).filter(UserProgram.assigned_by_user_id == user.id).update(
        {"assigned_by_user_id": None}, synchronize_session=False
    )
    db.query(Exercise).filter(Exercise.created_by_user_id == user.id).update(
        {"created_by_user_id": None, "is_deleted": True}, synchronize_session=False
    )
    db.query(CoachClient).filter(
        or_(CoachClient.coach_user_id == user.id, CoachClient.client_user_id == user.id)
    ).delete(synchronize_session=False)
    db.query(CoachClientInvite).filter(
        or_(
            CoachClientInvite.coach_user_id == user.id,
            CoachClientInvite.client_user_id == user.id,
            CoachClientInvite.telegram_user_id == user.telegram_user_id,
            CoachClientInvite.username == user.username,
        )
    ).delete(synchronize_session=False)
    db.query(CoachRoleApplication).filter(
        CoachRoleApplication.reviewed_by_user_id == user.id
    ).update({"reviewed_by_user_id": None}, synchronize_session=False)
    db.query(CoachRoleApplication).filter(CoachRoleApplication.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(UserProfile).filter(
        UserProfile.training_preferences_updated_by_user_id == user.id
    ).update(
        {"training_preferences_updated_by_user_id": None},
        synchronize_session=False,
    )

    db.query(EnergyCalibration).filter(EnergyCalibration.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(WeeklyCheckIn).filter(WeeklyCheckIn.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(NutritionTarget).filter(NutritionTarget.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(NutritionTarget).filter(NutritionTarget.assigned_by_user_id == user.id).update(
        {"assigned_by_user_id": None}, synchronize_session=False
    )
    db.query(Notification).filter(Notification.user_id == user.id).delete(synchronize_session=False)
    db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Payment).filter(Payment.user_id == user.id).delete(synchronize_session=False)
    db.query(Subscription).filter(Subscription.user_id == user.id).delete(synchronize_session=False)
    db.query(BodyMeasurement).filter(BodyMeasurement.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(AccountDataExport).filter(AccountDataExport.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(synchronize_session=False)
    db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).delete(synchronize_session=False)
    db.query(LocalCredential).filter(LocalCredential.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(AuthActionToken).filter(AuthActionToken.user_id == user.id).delete(
        synchronize_session=False
    )
    profile_ids = [
        row.id for row in db.query(UserProfile.id).filter(UserProfile.user_id == user.id).all()
    ]
    if profile_ids:
        db.query(UserProfilePriorityMuscle).filter(
            UserProfilePriorityMuscle.profile_id.in_(profile_ids)
        ).delete(synchronize_session=False)
    db.query(UserProfile).filter(UserProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(AuditEvent).filter(AuditEvent.actor_user_id == user.id).update(
        {"actor_user_id": None}, synchronize_session=False
    )
    db.query(AuditEvent).filter(AuditEvent.target_user_id == user.id).update(
        {"target_user_id": None}, synchronize_session=False
    )
    db.delete(user)
