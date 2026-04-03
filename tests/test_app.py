def auth(client, telegram_user_id=1001, is_coach=True):
    response = client.post('/api/v1/auth/dev-login', json={'telegram_user_id': telegram_user_id, 'is_coach': is_coach})
    assert response.status_code == 200
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_dev_login_and_me(client):
    headers = auth(client)
    response = client.get('/api/v1/me', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['telegram_user_id'] == 1001
    assert data['is_coach'] is True


def test_create_program_and_today_workout(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    exercises = client.get('/api/v1/programs/exercises', headers=headers).json()
    payload = {
        'title': 'Тестовая программа',
        'goal': 'recomposition',
        'level': 'intermediate',
        'mode': 'self',
        'assign_after_create': True,
        'days': [
            {
                'title': 'День 1',
                'exercises': [
                    {'exercise_id': exercises[0]['id'], 'prescribed_sets': 3, 'prescribed_reps': '8-10', 'rest_seconds': 90}
                ]
            }
        ]
    }
    create_res = client.post('/api/v1/programs/templates', json=payload, headers=headers)
    assert create_res.status_code == 200
    today = client.get('/api/v1/workouts/today', headers=headers)
    assert today.status_code == 200
    assert today.json()['title'] == 'День 1'


def test_workout_set_validation(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    client.post('/api/v1/programs/assign-demo', headers=headers)
    today = client.get('/api/v1/workouts/today', headers=headers).json()
    exercise = today['exercises'][0]
    bad = client.post(f"/api/v1/workouts/{today['id']}/sets", json={
        'workout_exercise_id': exercise['id'],
        'set_number': 99,
        'actual_reps': 8,
        'actual_weight': 80,
        'is_completed': True,
    }, headers=headers)
    assert bad.status_code == 400
    ok = client.post(f"/api/v1/workouts/{today['id']}/sets", json={
        'workout_exercise_id': exercise['id'],
        'set_number': 1,
        'actual_reps': 8,
        'actual_weight': 80,
        'is_completed': True,
    }, headers=headers)
    assert ok.status_code == 200


def test_mock_billing_activation(client):
    headers = auth(client, telegram_user_id=2001, is_coach=False)
    plans = client.get('/api/v1/billing/plans', headers=headers).json()
    premium = next(p for p in plans if p['code'] == 'premium')
    checkout = client.post('/api/v1/billing/checkout', json={'plan_code': premium['code']}, headers=headers)
    assert checkout.status_code == 200
    checkout_id = checkout.json()['checkout_id']
    complete = client.post(f'/api/v1/billing/mock/complete/{checkout_id}')
    assert complete.status_code == 200
    sub = client.get('/api/v1/billing/subscription', headers=headers)
    assert sub.status_code == 200
    assert sub.json()['plan_code'] == 'premium'
