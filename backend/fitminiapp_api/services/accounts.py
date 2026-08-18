from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from fitminiapp_api.models.audit import AuditEvent
from fitminiapp_api.models.auth_identity import AuthActionToken, AuthIdentity, LocalCredential
from fitminiapp_api.models.billing import Payment, Subscription
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.notification import Notification, NotificationSetting
from fitminiapp_api.models.nutrition import NutritionTarget
from fitminiapp_api.models.program import (
    HiddenProgramTemplate,
    ProgramTemplate,
    UserProgram,
    UserWorkout,
    UserWorkoutExercise,
    UserWorkoutSet,
)
from fitminiapp_api.models.token import RefreshToken
from fitminiapp_api.models.user import (
    BodyMeasurement,
    CoachClient,
    CoachClientInvite,
    CoachRoleApplication,
    User,
    UserProfile,
)
from fitminiapp_api.services.programs import delete_template_cascade


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
        db.query(UserWorkout).filter(UserWorkout.id.in_(workout_ids)).delete(
            synchronize_session=False
        )
    db.query(UserProgram).filter(UserProgram.id.in_(user_program_ids)).delete(
        synchronize_session=False
    )


def delete_user_cascade(db: Session, user: User) -> None:
    """Delete one account while preserving other users' historical snapshots."""

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
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(synchronize_session=False)
    db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).delete(synchronize_session=False)
    db.query(LocalCredential).filter(LocalCredential.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(AuthActionToken).filter(AuthActionToken.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(UserProfile).filter(UserProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(AuditEvent).filter(AuditEvent.actor_user_id == user.id).update(
        {"actor_user_id": None}, synchronize_session=False
    )
    db.query(AuditEvent).filter(AuditEvent.target_user_id == user.id).update(
        {"target_user_id": None}, synchronize_session=False
    )
    db.delete(user)


def build_account_export(db: Session, user: User) -> dict:
    """Build a portable export without secrets or data owned by managed clients."""

    programs = (
        db.query(UserProgram)
        .options(
            joinedload(UserProgram.template),
            joinedload(UserProgram.workouts)
            .joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.exercise),
            joinedload(UserProgram.workouts)
            .joinedload(UserWorkout.exercises)
            .joinedload(UserWorkoutExercise.sets),
        )
        .filter(UserProgram.user_id == user.id)
        .order_by(UserProgram.assigned_at.asc(), UserProgram.id.asc())
        .all()
    )
    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user.id)
        .order_by(BodyMeasurement.measured_on.asc(), BodyMeasurement.id.asc())
        .all()
    )
    nutrition = db.query(NutritionTarget).filter(NutritionTarget.user_id == user.id).first()
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.asc(), Notification.id.asc())
        .all()
    )
    relations = (
        db.query(CoachClient)
        .filter(or_(CoachClient.coach_user_id == user.id, CoachClient.client_user_id == user.id))
        .order_by(CoachClient.created_at.asc(), CoachClient.id.asc())
        .all()
    )
    coach_applications = (
        db.query(CoachRoleApplication)
        .filter(CoachRoleApplication.user_id == user.id)
        .order_by(CoachRoleApplication.created_at.asc(), CoachRoleApplication.id.asc())
        .all()
    )
    audit_events = (
        db.query(AuditEvent)
        .filter(or_(AuditEvent.actor_user_id == user.id, AuditEvent.target_user_id == user.id))
        .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
        .all()
    )

    profile = user.profile
    return {
        "exported_at": datetime.now(UTC),
        "account": {
            "id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.created_at,
            "is_coach": user.is_coach,
            "is_admin": user.is_admin,
        },
        "profile": (
            {
                "full_name": profile.full_name,
                "birth_date": profile.birth_date,
                "goal": profile.goal,
                "level": profile.level,
                "height_cm": profile.height_cm,
                "weight_kg": profile.weight_kg,
                "workouts_per_week": profile.workouts_per_week,
                "cardio_trainings_per_week": profile.cardio_trainings_per_week,
                "timezone": profile.timezone,
            }
            if profile
            else None
        ),
        "nutrition": (
            {
                column.name: getattr(nutrition, column.name)
                for column in NutritionTarget.__table__.columns
                if column.name not in {"user_id", "assigned_by_user_id"}
            }
            if nutrition
            else None
        ),
        "measurements": [
            {
                column.name: getattr(row, column.name)
                for column in BodyMeasurement.__table__.columns
                if column.name != "user_id"
            }
            for row in measurements
        ],
        "programs": [
            {
                "id": program.id,
                "title": program.template.title if program.template else "Архивная программа",
                "assigned_at": program.assigned_at,
                "start_date": program.start_date,
                "duration_weeks": program.duration_weeks,
                "status": program.status,
                "completed_at": program.completed_at,
                "workouts": [
                    {
                        "id": workout.id,
                        "scheduled_date": workout.scheduled_date,
                        "title": workout.title,
                        "status": workout.status,
                        "started_at": workout.started_at,
                        "completed_at": workout.completed_at,
                        "exercises": [
                            {
                                "exercise_id": exercise.exercise_id,
                                "title": exercise.exercise.title if exercise.exercise else None,
                                "notes": exercise.notes,
                                "sets": [
                                    {
                                        "set_number": workout_set.set_number,
                                        "actual_reps": workout_set.actual_reps,
                                        "actual_weight": workout_set.actual_weight,
                                        "rir": workout_set.rir,
                                        "is_completed": workout_set.is_completed,
                                    }
                                    for workout_set in exercise.sets
                                ],
                            }
                            for exercise in workout.exercises
                        ],
                    }
                    for workout in program.workouts
                ],
            }
            for program in programs
        ],
        "coaching_relationships": [
            {
                "id": relation.id,
                "role": "coach" if relation.coach_user_id == user.id else "client",
                "status": relation.status,
                "created_at": relation.created_at,
                "accepted_at": relation.accepted_at,
                "ended_at": relation.ended_at,
                "ended_reason": relation.ended_reason,
            }
            for relation in relations
        ],
        "coach_role_applications": [
            {
                "id": application.id,
                "status": application.status,
                "source": application.source,
                "created_at": application.created_at,
                "reviewed_at": application.reviewed_at,
            }
            for application in coach_applications
        ],
        "notification_settings": (
            {
                "workout_reminders_enabled": setting.workout_reminders_enabled,
                "reminder_hour": setting.reminder_hour,
            }
            if setting
            else None
        ),
        "notifications": [
            {
                "id": row.id,
                "channel": row.channel,
                "title": row.title,
                "body": row.body,
                "scheduled_for": row.scheduled_for,
                "status": row.status,
                "created_at": row.created_at,
                "sent_at": row.sent_at,
            }
            for row in notifications
        ],
        "audit_events": [
            {
                "id": event.id,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "details": event.details,
                "created_at": event.created_at,
            }
            for event in audit_events
        ],
    }
