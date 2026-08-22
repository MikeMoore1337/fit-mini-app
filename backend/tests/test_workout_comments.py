from __future__ import annotations

import asyncio
from datetime import date

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.exercise import Exercise
from fitminiapp_api.models.feedback import WorkoutComment, WorkoutCommentRevision
from fitminiapp_api.models.notification import Notification
from fitminiapp_api.models.program import UserProgram, UserWorkout, UserWorkoutExercise
from fitminiapp_api.models.user import CoachClient, User, UserProfile
from fitminiapp_api.services import worker
from fitminiapp_api.services.accounts import build_account_export


def _auth(client, telegram_user_id: int, *, is_coach: bool = False) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": is_coach},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _user_id(telegram_user_id: int) -> int:
    with get_session_context() as db:
        return db.query(User.id).filter(User.telegram_user_id == telegram_user_id).scalar()


def _add_workout(db, client_id: int, *, title: str = "Тестовая тренировка") -> tuple[int, int]:
    exercise_id = db.query(Exercise.id).order_by(Exercise.id).limit(1).scalar()
    assert exercise_id is not None
    program = UserProgram(
        user_id=client_id,
        duration_weeks=1,
        schedule_weekdays=[0],
        status="active",
        is_active=True,
    )
    db.add(program)
    db.flush()
    workout = UserWorkout(
        user_program_id=program.id,
        scheduled_date=date(2026, 8, 18),
        day_number=1,
        week_number=1,
        title=title,
        status="planned",
    )
    db.add(workout)
    db.flush()
    workout_exercise = UserWorkoutExercise(
        workout_id=workout.id,
        exercise_id=exercise_id,
        sort_order=1,
        prescribed_sets=3,
        prescribed_reps="8",
        rest_seconds=60,
    )
    db.add(workout_exercise)
    db.flush()
    return workout.id, workout_exercise.id


def test_contextual_comments_keep_chronology_plain_text_and_edit_revisions(client) -> None:
    trainer_headers = _auth(client, 26_001, is_coach=True)
    client_headers = _auth(client, 26_002)
    trainer_id = _user_id(26_001)
    client_id = _user_id(26_002)
    with get_session_context() as db:
        db.add(CoachClient(coach_user_id=trainer_id, client_user_id=client_id))
        workout_id, workout_exercise_id = _add_workout(db, client_id)

    first_body = "<script>alert('xss')</script>"
    first = client.post(
        f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments",
        headers={**trainer_headers, "Idempotency-Key": "comment-draft-0001"},
        json={"body": first_body},
    )
    assert first.status_code == 201, first.text
    first_payload = first.json()
    assert first_payload["body"] == first_body
    assert first_payload["body_format"] == "plain_text"
    assert first_payload["workout_exercise_id"] is None

    replay = client.post(
        f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments",
        headers={**trainer_headers, "Idempotency-Key": "comment-draft-0001"},
        json={"body": first_body},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == first_payload["id"]
    conflict = client.post(
        f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments",
        headers={**trainer_headers, "Idempotency-Key": "comment-draft-0001"},
        json={"body": "Другой комментарий"},
    )
    assert conflict.status_code == 409

    second = client.post(
        f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments",
        headers=trainer_headers,
        json={"body": "  Держите спину ровно.  ", "workout_exercise_id": workout_exercise_id},
    )
    assert second.status_code == 201, second.text
    assert second.json()["body"] == "Держите спину ровно."

    timeline = client.get(
        f"/api/v1/coach/clients/{client_id}/workouts",
        headers=trainer_headers,
    )
    assert timeline.status_code == 200, timeline.text
    assert timeline.json()[0]["exercises"][0]["workout_exercise_id"] == workout_exercise_id

    history = client.get(f"/api/v1/workouts/{workout_id}/comments", headers=client_headers)
    assert history.status_code == 200
    assert [row["id"] for row in history.json()] == [
        first_payload["id"],
        second.json()["id"],
    ]

    edited = client.patch(
        f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments/{first_payload['id']}",
        headers=trainer_headers,
        json={"body": "Исправленный комментарий"},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["body"] == "Исправленный комментарий"
    assert edited.json()["updated_at"] is not None
    assert edited.json()["revisions"] == [
        {
            "id": edited.json()["revisions"][0]["id"],
            "revision_number": 1,
            "body": first_body,
            "edited_by_user_id": trainer_id,
            "created_at": edited.json()["revisions"][0]["created_at"],
        }
    ]

    with get_session_context() as db:
        assert db.query(WorkoutComment).count() == 2
        assert db.query(WorkoutCommentRevision).count() == 1
        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == client_id)
            .order_by(Notification.id.asc())
            .all()
        )
        assert len(notifications) == 2
        assert notifications[1].action_url == (
            f"/app?workout_id={workout_id}&comment_id={second.json()['id']}"
            f"&workout_exercise_id={workout_exercise_id}"
        )
        export_user = db.get(User, client_id)
        assert export_user is not None
        account_export = build_account_export(db, export_user)
        assert [row["id"] for row in account_export["workout_comments"]] == [
            first_payload["id"],
            second.json()["id"],
        ]
        assert account_export["workout_comments"][0]["revisions"][0]["body"] == first_body

    endpoint = f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments"
    assert client.post(endpoint, headers=trainer_headers, json={"body": "   "}).status_code == 422
    assert (
        client.post(endpoint, headers=trainer_headers, json={"body": "a" * 2001}).status_code == 422
    )
    assert (
        client.post(
            endpoint, headers=trainer_headers, json={"body": "bad\u0000control"}
        ).status_code
        == 422
    )


def test_comment_permissions_owner_exercise_and_former_trainer_history(client) -> None:
    first_trainer_headers = _auth(client, 26_101, is_coach=True)
    client_headers = _auth(client, 26_102)
    unrelated_trainer_headers = _auth(client, 26_103, is_coach=True)
    other_client_headers = _auth(client, 26_104)
    first_trainer_id = _user_id(26_101)
    client_id = _user_id(26_102)
    unrelated_trainer_id = _user_id(26_103)
    other_client_id = _user_id(26_104)
    with get_session_context() as db:
        first_relation = CoachClient(
            coach_user_id=first_trainer_id,
            client_user_id=client_id,
        )
        db.add(first_relation)
        db.flush()
        workout_id, workout_exercise_id = _add_workout(db, client_id)
        other_workout_id, other_exercise_id = _add_workout(
            db, other_client_id, title="Чужая тренировка"
        )
        first_relation_id = first_relation.id

    endpoint = f"/api/v1/coach/clients/{client_id}/workouts/{workout_id}/comments"
    created = client.post(
        endpoint,
        headers=first_trainer_headers,
        json={"body": "Комментарий первого тренера", "workout_exercise_id": workout_exercise_id},
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    assert client.get(endpoint, headers=unrelated_trainer_headers).status_code == 404
    assert (
        client.post(
            endpoint, headers=unrelated_trainer_headers, json={"body": "Нет доступа"}
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/workouts/{workout_id}/comments", headers=other_client_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            endpoint,
            headers=first_trainer_headers,
            json={"body": "Неверное упражнение", "workout_exercise_id": other_exercise_id},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/coach/clients/{client_id}/workouts/{other_workout_id}/comments",
            headers=first_trainer_headers,
            json={"body": "Чужая тренировка"},
        ).status_code
        == 404
    )

    with get_session_context() as db:
        relation = db.get(CoachClient, first_relation_id)
        assert relation is not None
        relation.status = "ended"
        relation.ended_reason = "removed_by_client"
        db.add(
            CoachClient(
                coach_user_id=unrelated_trainer_id,
                client_user_id=client_id,
            )
        )

    assert (
        client.post(
            endpoint, headers=first_trainer_headers, json={"body": "После отзыва"}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"{endpoint}/{comment_id}",
            headers=first_trainer_headers,
            json={"body": "После отзыва"},
        ).status_code
        == 409
    )
    former_history = client.get(endpoint, headers=first_trainer_headers)
    assert former_history.status_code == 200
    assert [row["id"] for row in former_history.json()] == [comment_id]

    new_comment = client.post(
        endpoint,
        headers=unrelated_trainer_headers,
        json={"body": "Комментарий нового тренера"},
    )
    assert new_comment.status_code == 201
    assert [row["id"] for row in client.get(endpoint, headers=first_trainer_headers).json()] == [
        comment_id
    ]
    client_history = client.get(f"/api/v1/workouts/{workout_id}/comments", headers=client_headers)
    assert [row["id"] for row in client_history.json()] == [comment_id, new_comment.json()["id"]]


def test_comment_notification_delivery_uses_context_deep_link_and_handles_unlinked_client(
    client, monkeypatch
) -> None:
    trainer_headers = _auth(client, 26_201, is_coach=True)
    linked_client_headers = _auth(client, 26_202)
    del linked_client_headers
    trainer_id = _user_id(26_201)
    linked_client_id = _user_id(26_202)
    with get_session_context() as db:
        unlinked = User(username="unlinked_comment_client")
        db.add(unlinked)
        db.flush()
        db.add(UserProfile(user_id=unlinked.id, full_name="Клиент без Telegram"))
        db.add_all(
            [
                CoachClient(coach_user_id=trainer_id, client_user_id=linked_client_id),
                CoachClient(coach_user_id=trainer_id, client_user_id=unlinked.id),
            ]
        )
        linked_workout_id, _ = _add_workout(db, linked_client_id)
        unlinked_workout_id, _ = _add_workout(db, unlinked.id)
        unlinked_client_id = unlinked.id

    linked = client.post(
        f"/api/v1/coach/clients/{linked_client_id}/workouts/{linked_workout_id}/comments",
        headers=trainer_headers,
        json={"body": "Проверьте темп движения"},
    )
    unlinked = client.post(
        f"/api/v1/coach/clients/{unlinked_client_id}/workouts/{unlinked_workout_id}/comments",
        headers=trainer_headers,
        json={"body": "Комментарий останется в приложении"},
    )
    assert linked.status_code == 201
    assert unlinked.status_code == 201

    delivered: list[tuple[int, str, str | None]] = []

    async def fake_send(_http_client, chat_id, text, *, open_app_path=None):
        delivered.append((chat_id, text, open_app_path))

    monkeypatch.setattr(worker, "send_telegram_message", fake_send)
    asyncio.run(worker.run_once(sync_reminders=False))

    assert delivered == [
        (
            26_202,
            "Комментарий тренера к тренировке\n\n"
            "К тренировке «Тестовая тренировка»: Проверьте темп движения",
            f"/app?workout_id={linked_workout_id}&comment_id={linked.json()['id']}",
        )
    ]
    with get_session_context() as db:
        unlinked_notification = (
            db.query(Notification).filter(Notification.user_id == unlinked_client_id).one()
        )
        assert unlinked_notification.status == "cancelled"
        assert unlinked_notification.last_error == "telegram_identity_not_linked"
        assert unlinked_notification.action_url == (
            f"/app?workout_id={unlinked_workout_id}&comment_id={unlinked.json()['id']}"
        )
