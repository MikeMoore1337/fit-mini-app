import { expect, test, type Page } from '@playwright/test';

type SetState = {
  actual_reps: number | null;
  actual_weight: number | null;
  rir: '0' | '1' | '2' | '3' | '4+' | null;
  set_kind: 'warmup' | 'working' | 'drop' | null;
  reached_failure: boolean | null;
  is_completed: boolean;
  version: number;
};

async function mockActiveWorkout(page: Page) {
  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Europe/Moscow' });
  let finished = false;
  let failSetPatch = false;
  const sets = new Map<number, SetState>([
    [
      201,
      {
        actual_reps: null,
        actual_weight: null,
        rir: null,
        set_kind: 'working',
        reached_failure: false,
        is_completed: false,
        version: 1,
      },
    ],
    [
      202,
      {
        actual_reps: null,
        actual_weight: null,
        rir: null,
        set_kind: 'working',
        reached_failure: false,
        is_completed: false,
        version: 1,
      },
    ],
    [
      203,
      {
        actual_reps: null,
        actual_weight: null,
        rir: null,
        set_kind: 'working',
        reached_failure: false,
        is_completed: false,
        version: 1,
      },
    ],
  ]);
  const workout = () => ({
    id: 42,
    scheduled_date: today,
    title: 'Силовая база',
    status: 'in_progress',
    day_number: 1,
    week_number: 1,
    started_at: new Date(Date.now() - 12 * 60_000).toISOString(),
    completed_at: null,
    exercises: [
      {
        id: 101,
        exercise_id: 11,
        exercise_title: 'Жим штанги лёжа',
        sort_order: 1,
        prescribed_sets: 3,
        prescribed_reps: '8–10',
        rest_seconds: 90,
        notes: 'Сохраняйте устойчивое положение корпуса.',
        has_guide: true,
        sets: [...sets].map(([id, state], index) => ({
          id,
          set_number: index + 1,
          ...state,
        })),
      },
    ],
  });

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: { app_env: 'dev', enable_dev_auth: true, telegram_bot_username: 'fit_bot' },
      });
    }
    if (path.endsWith('/auth/refresh')) {
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    }
    if (path.endsWith('/auth/dev-login')) {
      return route.fulfill({ json: { access_token: 'test-token', token_type: 'bearer' } });
    }
    if (path.endsWith('/me')) {
      return route.fulfill({
        json: {
          id: 7,
          first_name: 'Тест',
          is_coach: false,
          is_admin: false,
          has_active_program: true,
          has_workout_history: true,
          onboarding: { status: 'complete', required_fields: ['goal'], missing_fields: [] },
          profile: { full_name: 'Тестовый пользователь', timezone: 'Europe/Moscow' },
          trainer: null,
        },
      });
    }
    if (path.endsWith('/workouts/today')) {
      if (finished) {
        return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка завершена' } });
      }
      return route.fulfill({ json: workout() });
    }
    if (path.endsWith('/workouts/progress/summary')) {
      return route.fulfill({
        json: {
          training: { last_completed_workout_on: finished ? today : null, next_workout: null },
          body: { latest_measurement: null, trends: [] },
          adherence: {
            formula_version: 'adherence-v1',
            overall_percent: null,
            included_components: [],
          },
        },
      });
    }
    if (path.endsWith('/nutrition/diary')) {
      return route.fulfill({
        json: {
          diary_date: today,
          timezone: 'Europe/Moscow',
          meals: [],
          totals: { energy_kcal: '0', protein_g: '0', fat_g: '0', carbs_g: '0', fiber_g: null },
          targets: null,
          remaining: null,
        },
      });
    }
    if (path.endsWith('/programs/exercises/11')) {
      return route.fulfill({
        json: {
          id: 11,
          title: 'Жим штанги лёжа',
          primary_muscle: 'Грудь',
          equipment: 'Штанга и скамья',
          primary_muscle_ids: ['chest'],
          secondary_muscle_ids: ['triceps'],
          equipment_ids: ['barbell', 'bench'],
          alternatives: [],
          difficulty_level: 'beginner',
          is_custom: false,
          is_personalized: false,
          has_guide: true,
          guide: {
            technique_steps: ['Сведите лопатки.', 'Опускайте штангу под контролем.'],
            breathing: 'Вдох при опускании, выдох после тяжёлой части подъёма.',
            common_mistakes: ['Отрыв таза от скамьи'],
            muscles: [
              {
                identifier: 'chest',
                name: 'Грудь',
                role_id: 'primary',
                role: 'Основная',
                function: 'Перемещает руку вперёд в фазе усилия.',
              },
            ],
            equipment: [
              { identifier: 'barbell', name: 'Штанга' },
              { identifier: 'bench', name: 'Скамья' },
            ],
            safety_notes: ['Используйте страховку при тяжёлых подходах.'],
            alternatives: [],
            media: [],
            images: [],
            media_reference: 'test:bench-press',
            source_name: 'Test source',
            source_url: 'https://example.com',
            source_license: 'Public domain',
            source_license_url: null,
          },
        },
      });
    }
    const setMatch = path.match(/\/workouts\/sets\/(\d+)$/);
    if (setMatch) {
      if (failSetPatch) {
        return route.fulfill({ status: 503, json: { detail: 'Сервис временно недоступен' } });
      }
      const setId = Number(setMatch[1]);
      const current = sets.get(setId)!;
      const body = request.postDataJSON() as Partial<SetState>;
      const next = {
        ...current,
        actual_reps: body.actual_reps ?? null,
        actual_weight: body.actual_weight ?? null,
        rir: body.rir ?? null,
        set_kind: body.set_kind ?? null,
        reached_failure: body.reached_failure ?? null,
        is_completed: body.is_completed ?? false,
        version: current.version + 1,
      };
      sets.set(setId, next);
      return route.fulfill({
        json: { id: setId, set_number: setId - 200, ...next },
      });
    }
    if (path.endsWith('/workouts/42/finish')) {
      finished = true;
      return route.fulfill({ status: 204, body: '' });
    }
    return route.fulfill({ json: [] });
  });

  return {
    failSetPatch(value: boolean) {
      failSetPatch = value;
    },
  };
}

test('active workout keeps one obvious next action through logging, timer and finish', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 390, height: 844 });
  await mockActiveWorkout(page);

  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();

  const firstSet = page.locator('[data-workout-set-id="201"]');
  await expect(firstSet).toHaveAttribute('aria-current', 'step');
  await firstSet.getByRole('spinbutton', { name: 'Вес, Жим штанги лёжа, подход 1' }).fill('40');
  await firstSet.getByRole('spinbutton', { name: 'Повторы, Жим штанги лёжа, подход 1' }).fill('8');
  await firstSet.getByRole('button', { name: 'Завершить: Жим штанги лёжа, подход 1' }).dblclick();

  const secondSet = page.locator('[data-workout-set-id="202"]');
  await expect(secondSet).toHaveAttribute('aria-current', 'step');
  await expect(secondSet.getByText('Предыдущий подход: 40 кг × 8')).toBeVisible();
  await expect(page.getByRole('timer').filter({ hasText: 'Отдых' })).toContainText(
    'Дальше: Жим штанги лёжа, подход 2',
  );

  await secondSet.getByText('Дополнительно').click();
  await secondSet.getByLabel('Вид подхода').selectOption('drop');
  await secondSet.getByRole('button', { name: '2 — ещё примерно 2 повтора' }).click();
  await secondSet.getByRole('spinbutton', { name: 'Вес, Жим штанги лёжа, подход 2' }).fill('35');
  await secondSet.getByRole('spinbutton', { name: 'Повторы, Жим штанги лёжа, подход 2' }).fill('9');
  await secondSet.getByRole('button', { name: 'Завершить: Жим штанги лёжа, подход 2' }).click();

  const thirdSet = page.locator('[data-workout-set-id="203"]');
  await expect(thirdSet).toHaveAttribute('aria-current', 'step');
  await thirdSet.getByRole('spinbutton', { name: 'Вес, Жим штанги лёжа, подход 3' }).fill('32.5');
  await thirdSet.getByRole('spinbutton', { name: 'Повторы, Жим штанги лёжа, подход 3' }).fill('10');
  await thirdSet.getByRole('button', { name: 'Завершить: Жим штанги лёжа, подход 3' }).click();

  await expect(page.getByText('Все подходы выполнены')).toBeVisible();
  await expect(page.getByText('Синхронизировано')).toBeVisible();
  await page.getByRole('button', { name: 'Завершить тренировку' }).click();
  await expect(page.getByRole('heading', { name: 'Тренировка завершена' })).toBeVisible();
});

test('active workout has touch-size controls and no horizontal overflow', async ({ page }) => {
  await mockActiveWorkout(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();
  const exercise = page.locator('.active-workout-exercise').first();
  await expect(exercise).toHaveCSS('border-radius', '16px');
  await expect(exercise).toHaveCSS('border-top-color', 'rgb(158, 224, 43)');
  await expect(exercise).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  const guideButton = page.getByRole('button', { name: 'Техника' });
  await expect(guideButton).toHaveText('Техника');
  await guideButton.click();
  await expect(page.getByRole('heading', { name: 'Техника выполнения' })).toBeVisible();
  await page.getByRole('button', { name: 'Закрыть карточку упражнения' }).click();

  for (const viewport of [
    { width: 1280, height: 900 },
    { width: 390, height: 844 },
    { width: 360, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    await expect
      .poll(() =>
        page.evaluate(
          () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
        ),
      )
      .toBe(true);
    const box = await page
      .getByRole('button', { name: 'Завершить: Жим штанги лёжа, подход 1' })
      .boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
  }
});

test('save failure stays compact, keeps controls open and retries explicitly', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const server = await mockActiveWorkout(page);
  server.failSetPatch(true);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();

  const firstSet = page.locator('[data-workout-set-id="201"]');
  await firstSet.getByRole('spinbutton', { name: 'Вес, Жим штанги лёжа, подход 1' }).fill('40');
  await expect(page.getByText('Требуется действие')).toBeVisible();
  await expect(
    firstSet.getByRole('button', { name: 'Завершить: Жим штанги лёжа, подход 1' }),
  ).toBeEnabled();

  server.failSetPatch(false);
  await page.getByRole('button', { name: 'Повторить' }).click();
  await expect(page.getByText('Синхронизировано')).toBeVisible();
});
