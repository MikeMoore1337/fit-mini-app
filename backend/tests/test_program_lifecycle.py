from datetime import date, timedelta

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.program import UserProgram, UserWorkout
from fitminiapp_api.models.user import User


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_template(client, headers, *, sets: int = 1, assigned: bool = False) -> int:
    exercise_id = client.get("/api/v1/programs/exercises", headers=headers).json()[0]["id"]
    response = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Жизненный цикл",
            "goal": "recomposition",
            "level": "intermediate",
            "mode": "self",
            "assign_after_create": assigned,
            "days": [
                {
                    "title": "Силовая A",
                    "exercises": [
                        {
                            "exercise_id": exercise_id,
                            "prescribed_sets": sets,
                            "prescribed_reps": "8-10",
                            "rest_seconds": 90,
                            "notes": "Контролировать негативную фазу",
                        }
                    ],
                },
                {
                    "title": "Силовая B",
                    "exercises": [
                        {
                            "exercise_id": exercise_id,
                            "prescribed_sets": sets,
                            "prescribed_reps": "10",
                            "rest_seconds": 60,
                        }
                    ],
                },
            ],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["template"]["id"]


def test_recurring_schedule_snapshots_notes_and_requires_replacement_confirmation(client):
    headers = _auth(client, 91001)
    template_id = _create_template(client, headers)
    start_date = date.today() + timedelta(days=1)
    second_date = start_date + timedelta(days=2)
    next_week_start = start_date + timedelta(days=7)
    next_week_second = start_date + timedelta(days=9)

    assigned = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        headers=headers,
        json={
            "start_date": start_date.isoformat(),
            "duration_weeks": 2,
            "schedule_weekdays": [start_date.weekday(), second_date.weekday()],
        },
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["workouts_created"] == 4
    assert assigned.json()["duration_weeks"] == 2

    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 91001).one()
        program = db.query(UserProgram).filter(UserProgram.user_id == user.id).one()
        workouts = (
            db.query(UserWorkout)
            .filter(UserWorkout.user_program_id == program.id)
            .order_by(UserWorkout.scheduled_date.asc())
            .all()
        )
        assert [workout.scheduled_date.isoformat() for workout in workouts] == [
            start_date.isoformat(),
            second_date.isoformat(),
            next_week_start.isoformat(),
            next_week_second.isoformat(),
        ]
        assert [workout.week_number for workout in workouts] == [1, 1, 2, 2]
        assert workouts[0].exercises[0].notes == "Контролировать негативную фазу"
        first_workout_id = workouts[0].id
        second_workout_id = workouts[1].id

    schedule = client.get(
        "/api/v1/workouts/schedule"
        f"?date_from={start_date.isoformat()}&date_to={next_week_second.isoformat()}",
        headers=headers,
    )
    assert schedule.status_code == 200
    assert len(schedule.json()) == 4
    rescheduled = client.patch(
        f"/api/v1/workouts/{first_workout_id}/schedule",
        headers=headers,
        json={"scheduled_date": (start_date + timedelta(days=1)).isoformat()},
    )
    assert rescheduled.status_code == 200
    skipped = client.post(f"/api/v1/workouts/{second_workout_id}/skip", headers=headers)
    assert skipped.status_code == 200
    assert skipped.json()["status"] == "skipped"

    refused = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        headers=headers,
        json={"start_date": (start_date + timedelta(days=30)).isoformat()},
    )
    assert refused.status_code == 409

    replaced = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        headers=headers,
        json={
            "start_date": (start_date + timedelta(days=30)).isoformat(),
            "replace_active": True,
        },
    )
    assert replaced.status_code == 200, replaced.text


def test_finish_requires_explicit_incomplete_confirmation_and_completes_program(client):
    headers = _auth(client, 91002)
    exercise_id = client.get("/api/v1/programs/exercises", headers=headers).json()[0]["id"]
    created = client.post(
        "/api/v1/programs/templates",
        headers=headers,
        json={
            "title": "Сегодня",
            "goal": "maintenance",
            "level": "beginner",
            "mode": "self",
            "assign_after_create": True,
            "start_date": date.today().isoformat(),
            "days": [
                {
                    "title": "Сегодня",
                    "exercises": [
                        {
                            "exercise_id": exercise_id,
                            "prescribed_sets": 2,
                            "prescribed_reps": "8",
                            "rest_seconds": 60,
                            "notes": "Без боли",
                        }
                    ],
                }
            ],
        },
    )
    assert created.status_code == 200, created.text
    today = client.get("/api/v1/workouts/today", headers=headers)
    assert today.status_code == 200
    workout = today.json()
    assert workout["exercises"][0]["notes"] == "Без боли"

    assert (
        client.post(f"/api/v1/workouts/{workout['id']}/start", headers=headers).status_code == 200
    )
    first_set = workout["exercises"][0]["sets"][0]
    updated = client.patch(
        f"/api/v1/workouts/sets/{first_set['id']}",
        headers=headers,
        json={"actual_reps": 8, "actual_weight": 20, "is_completed": True},
    )
    assert updated.status_code == 200

    refused = client.post(f"/api/v1/workouts/{workout['id']}/finish", headers=headers)
    assert refused.status_code == 409
    finished = client.post(
        f"/api/v1/workouts/{workout['id']}/finish",
        headers=headers,
        json={"confirm_incomplete": True},
    )
    assert finished.status_code == 200, finished.text
    repeated_finish = client.post(
        f"/api/v1/workouts/{workout['id']}/finish",
        headers=headers,
        json={"confirm_incomplete": True},
    )
    assert repeated_finish.status_code == 409

    progress = client.get("/api/v1/workouts/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["workouts_completed"] == 1
    assert progress.json()["weekly_volume"][0]["volume_kg"] == 160.0
    assert progress.json()["personal_records"][0]["max_weight_kg"] == 20.0
    summary = client.get("/api/v1/workouts/history/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json() == {
        "workouts_completed": 1,
        "completed_sets": 1,
        "volume_kg": 160.0,
    }

    with get_session_context() as db:
        user = db.query(User).filter(User.telegram_user_id == 91002).one()
        program = db.query(UserProgram).filter(UserProgram.user_id == user.id).one()
        assert program.status == "completed"
        assert program.is_active is False
        assert program.completed_at is not None


def test_assignment_rejects_a_start_date_in_the_past(client):
    headers = _auth(client, 91003)
    template_id = _create_template(client, headers)

    response = client.post(
        f"/api/v1/programs/templates/{template_id}/assign-to-me",
        headers=headers,
        json={"start_date": (date.today() - timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 422
