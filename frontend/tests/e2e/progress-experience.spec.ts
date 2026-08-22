import { expect, test, type Page } from '@playwright/test';

const captureFeedbackAudit = Boolean(
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.CAPTURE_FEEDBACK_AUDIT,
);

const signal = (status: 'sufficient' | 'limited' | 'insufficient') => ({
  status,
  counters: {},
  reason_keys: status === 'sufficient' ? ['thresholds_met'] : ['too_few_points'],
});

async function mockProgress(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const period = Number(url.searchParams.get('period_days')) || 30;
    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: { app_env: 'dev', enable_dev_auth: true, telegram_bot_username: '' },
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
          first_name: 'Анна',
          is_coach: false,
          is_admin: false,
          has_active_program: true,
          has_workout_history: true,
          onboarding: { status: 'complete', required_fields: [], missing_fields: [] },
          profile: { full_name: 'Анна Петрова', timezone: 'Europe/Moscow', kbju: null },
          trainer: null,
        },
      });
    }
    if (path.endsWith('/workouts/today')) {
      return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка не назначена' } });
    }
    if (path.endsWith('/nutrition/diary')) {
      return route.fulfill({
        json: {
          diary_date: '2030-01-30',
          timezone: 'Europe/Moscow',
          meals: [],
          totals: {
            energy_kcal: '0',
            protein_g: '0',
            fat_g: '0',
            carbs_g: '0',
            fiber_g: null,
          },
          targets: null,
          remaining: null,
        },
      });
    }
    if (path.endsWith('/workouts/progress/summary')) {
      return route.fulfill({
        json: {
          user_id: 7,
          period_days: period,
          period_start: '2030-01-01',
          period_end: '2030-01-30',
          training: {
            planned_workouts: 8,
            completed_workouts: 7,
            frequency_per_week: 1.63,
            volume_kg: 12400,
            new_personal_records: 2,
            last_completed_workout_on: '2030-01-28',
            next_workout: null,
          },
          nutrition: {
            visible: true,
            logged_days: 20,
            adherence_evaluated_days: 18,
            average_calories: 1980,
            target_calories: 2100,
            average_protein_g: 132,
            target_protein_g: 140,
            target_effective_on: '2029-12-01',
          },
          body: {
            latest_measurement: { measured_on: '2030-01-29', weight_kg: 68.4, waist_cm: 72 },
            trends: [
              {
                metric: 'weight_kg',
                first_value: 69.4,
                latest_value: 68.4,
                change: -1,
                first_measured_on: '2030-01-02',
                latest_measured_on: '2030-01-29',
                point_count: 4,
                span_days: 27,
                interpretation_status: 'available',
                points: [
                  { measured_on: '2030-01-02', value: 69.4 },
                  { measured_on: '2030-01-05', value: 69.1 },
                  { measured_on: '2030-01-22', value: 68.8 },
                  { measured_on: '2030-01-29', value: 68.4 },
                ],
              },
              {
                metric: 'waist_cm',
                first_value: 73,
                latest_value: 72,
                change: -1,
                first_measured_on: '2030-01-02',
                latest_measured_on: '2030-01-29',
                point_count: 2,
                span_days: 27,
                interpretation_status: 'insufficient_points',
                points: [
                  { measured_on: '2030-01-02', value: 73 },
                  { measured_on: '2030-01-29', value: 72 },
                ],
              },
            ],
            priority: null,
            guidance: {
              comparison_basis: 'self',
              minimum_points_for_interpretation: 3,
              minimum_span_days_for_interpretation: 14,
              consistency_tips: [],
              circumference_limitations: [],
            },
          },
          adherence: {
            formula_version: 'adherence-v1',
            overall_percent: 84,
            included_components: ['workouts', 'calories', 'protein'],
            workouts: {
              status: 'available',
              percent: 87.5,
              achieved: 7,
              evaluated: 8,
              weight: 0.4,
            },
            cardio: {
              status: 'unsupported',
              percent: null,
              achieved: 0,
              evaluated: 0,
              weight: 0.2,
            },
            calories: {
              status: 'available',
              percent: 83.3,
              achieved: 15,
              evaluated: 18,
              weight: 0.2,
            },
            protein: {
              status: 'available',
              percent: 72.2,
              achieved: 13,
              evaluated: 18,
              weight: 0.2,
            },
          },
          data_sufficiency: {
            ruleset_version: 'data-sufficiency-v1',
            workout_logging: signal('sufficient'),
            working_sets: signal('sufficient'),
            rir_coverage: signal('limited'),
            nutrition_coverage: signal('sufficient'),
            weight_trend: signal('sufficient'),
            anthropometry: signal('limited'),
            schedule_adherence: signal('sufficient'),
          },
        },
      });
    }
    if (path.endsWith('/workouts/progress/training-analytics')) {
      return route.fulfill({
        json: {
          period_days: period,
          period_start: '2030-01-01',
          period_end: '2030-01-30',
          exercise_history_limit: 20,
          completed_set_count: 28,
          reps_total: 226,
          reps_recorded_sets: 28,
          external_load_volume_kg: 12400,
          volume_recorded_sets: 24,
          exercises: [
            {
              exercise_id: 11,
              exercise_title: 'Жим штанги лёжа',
              uses_bodyweight_equipment: false,
              performed_session_count: 6,
              completed_set_count: 18,
              first_performed_on: '2030-01-03',
              last_performed_on: '2030-01-28',
              reps_total: 144,
              reps_recorded_sets: 18,
              max_external_load_kg: 62.5,
              best_set_volume_kg: 500,
              external_load_volume_kg: 7200,
              volume_recorded_sets: 18,
              history_truncated: false,
              sessions: [
                {
                  workout_id: 42,
                  workout_exercise_id: 101,
                  performed_on: '2030-01-28',
                  completed_set_count: 2,
                  reps_total: 16,
                  reps_recorded_sets: 2,
                  max_external_load_kg: 62.5,
                  external_load_volume_kg: 980,
                  volume_recorded_sets: 2,
                  sets: [
                    {
                      set_number: 1,
                      reps: 8,
                      external_load_kg: 60,
                      external_load_volume_kg: 480,
                      rir: '2',
                      set_kind: 'working',
                      reached_failure: false,
                    },
                    {
                      set_number: 2,
                      reps: 8,
                      external_load_kg: 62.5,
                      external_load_volume_kg: 500,
                      rir: null,
                      set_kind: 'working',
                      reached_failure: false,
                    },
                  ],
                },
              ],
            },
          ],
          rir: {
            completed_set_count: 28,
            recorded_set_count: 16,
            missing_set_count: 12,
            distribution: [],
          },
          primary_muscle_exposure: [
            { muscle_id: 'chest', muscle_name: 'Грудные', completed_set_count: 18 },
          ],
          secondary_muscle_exposure: [
            { muscle_id: 'triceps', muscle_name: 'Трицепс', completed_set_count: 18 },
          ],
          completed_sets_without_muscle_metadata: 0,
          data_sufficiency: {
            ruleset_version: 'data-sufficiency-v1',
            workout_logging: signal('sufficient'),
            working_sets: signal('sufficient'),
            rir_coverage: signal('limited'),
          },
        },
      });
    }
    if (path.endsWith('/check-ins/weekly/current')) {
      return route.fulfill({
        json: {
          week_start: '2030-01-28',
          week_end: '2030-02-03',
          submitted_on: '2030-01-30',
          timezone: 'Europe/Moscow',
          existing: { status: 'completed', note: null },
          summary: {
            training: { planned_workouts: 2, completed_workouts: 2 },
            nutrition: { logged_days: 3 },
            progression: { new_personal_records: 1 },
            weight_trend: null,
          },
        },
      });
    }
    if (path.endsWith('/check-ins/weekly')) {
      return route.fulfill({ json: { items: [], total: 0, limit: 4, offset: 0 } });
    }
    if (path.endsWith('/workouts/week')) {
      return route.fulfill({
        json: [
          {
            id: 43,
            scheduled_date: '2030-01-28',
            scheduled_time: '18:30:00',
            title: 'Ноги и корпус',
            status: 'completed',
            day_number: 2,
            week_number: 4,
          },
        ],
      });
    }
    if (path.endsWith('/workouts/schedule')) {
      return route.fulfill({
        json: [
          {
            id: 43,
            scheduled_date: '2030-01-28',
            scheduled_time: '18:30:00',
            title: 'Ноги и корпус',
            status: 'completed',
            day_number: 2,
            week_number: 4,
          },
        ],
      });
    }
    if (path.endsWith('/workouts/history')) {
      return route.fulfill({
        json: [
          {
            id: 43,
            scheduled_date: '2030-01-28',
            scheduled_time: '18:30:00',
            title: 'Ноги и корпус',
            status: 'completed',
            started_at: '2030-01-28T18:30:00',
            completed_at: '2030-01-28T19:20:00',
            completed_sets: 4,
            volume_kg: 1480,
            exercises: [
              {
                workout_exercise_id: 55,
                exercise_id: 11,
                title: 'Присед со штангой',
                prescribed_sets: 4,
                prescribed_reps: '8',
                sort_order: 1,
              },
            ],
            adaptations: [],
          },
        ],
      });
    }
    if (path.endsWith('/workouts/43/comments')) {
      return route.fulfill({
        json: [
          {
            id: 7,
            trainer_author_id: 70,
            client_user_id: 7,
            workout_id: 43,
            workout_exercise_id: 55,
            body: 'Держите колени по направлению носков. <script>не HTML</script>',
            body_format: 'plain_text',
            created_at: '2030-01-28T20:00:00',
            updated_at: '2030-01-28T20:05:00',
            revisions: [],
          },
        ],
      });
    }
    if (path.endsWith('/workouts/history/summary')) {
      return route.fulfill({
        json: { workouts_completed: 1, completed_sets: 4, volume_kg: 1480 },
      });
    }
    return route.fulfill({ json: [] });
  });
}

test('progress remains clear and free of horizontal overflow at supported widths', async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  const runtimeErrors: string[] = [];
  page.on('console', (message) => {
    const expectedHttpState =
      message.text().includes('401 (Unauthorized)') || message.text().includes('404 (Not Found)');
    if (message.type() === 'error' && !expectedHttpState) {
      consoleErrors.push(message.text());
    }
  });
  page.on('pageerror', (error) => runtimeErrors.push(error.stack || error.message));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mockProgress(page);
  await page.goto('/app?section=progress');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('link', { name: 'Прогресс' }).click();
  await expect(
    page
      .getByRole('heading', { name: 'Прогресс' })
      .or(page.getByRole('heading', { name: 'Приложение не смогло продолжить работу' })),
  ).toBeVisible();
  expect(consoleErrors).toEqual([]);
  expect(runtimeErrors).toEqual([]);
  await expect(page.getByRole('heading', { name: 'Прогресс' })).toBeVisible();
  await expect(page.getByText('84%').first()).toBeVisible();

  await page.getByText('Жим штанги лёжа').click();
  await expect(page.getByText('Детали тренировки')).toBeVisible();
  await page.getByRole('tab', { name: '7 дней' }).click();
  await expect(page.getByRole('tab', { name: '7 дней' })).toHaveAttribute('aria-selected', 'true');

  for (const viewport of [
    { width: 1440, height: 1000 },
    { width: 768, height: 900 },
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
    await expect(page.getByRole('tab', { name: '30 дней' })).toBeVisible();
    await expect(
      page.getByRole('progressbar', { name: /Запланированные тренировки/ }),
    ).toBeVisible();
  }

  expect(consoleErrors).toEqual([]);
  expect(runtimeErrors).toEqual([]);
});

test('notification deep-link opens exact workout feedback and preserves back navigation', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mockProgress(page);

  await page.goto('/app?section=today');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await expect(page.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
  await page.goto('/app?workout_id=43&comment_id=7&workout_exercise_id=55');

  await expect(page.getByRole('heading', { name: 'Прогресс' })).toBeVisible();
  await expect(
    page.getByText('Держите колени по направлению носков.', { exact: false }),
  ).toBeVisible();
  await expect(page.locator('#workout-comment-7')).toHaveClass(/is-focused/);
  await expect(page.locator('#workout-comment-7')).toHaveCount(1);
  await expect(page.getByText('Упражнение · Присед со штангой')).toBeVisible();
  await expect(page.getByText('Изменено')).toBeVisible();
  await expect(page.locator('.workout-feedback script')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const historyCard = page.locator('.workout-history-card');
  const clearHistory = historyCard.getByRole('button', { name: 'Очистить историю' });
  const clearHistoryBox = await clearHistory.boundingBox();
  const historyFeedbackBox = await historyCard.locator('.workout-feedback').boundingBox();
  expect(clearHistoryBox?.y ?? 0).toBeGreaterThan(
    (historyFeedbackBox?.y ?? 0) + (historyFeedbackBox?.height ?? 0),
  );
  expect(clearHistoryBox?.height).toBeGreaterThanOrEqual(44);
  await clearHistory.click();
  await expect(page.getByRole('dialog', { name: 'Очистить историю?' })).toBeVisible();
  await page.getByRole('button', { name: 'Отмена' }).click();
  await expect(historyCard).toHaveAttribute('open', '');
  const historyMetricBoxes = await historyCard
    .locator('.workout-history__metrics .metric')
    .evaluateAll((metrics) => metrics.map((metric) => metric.getBoundingClientRect()));
  expect(historyMetricBoxes).toHaveLength(3);
  expect(
    Math.max(...historyMetricBoxes.map((box) => box.top)) -
      Math.min(...historyMetricBoxes.map((box) => box.top)),
  ).toBeLessThan(2);
  expect(historyMetricBoxes.every((box) => box.width >= 90)).toBe(true);

  for (const viewport of [
    { width: 360, height: 800 },
    { width: 430, height: 932 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
    const metricBoxes = await historyCard
      .locator('.workout-history__metrics .metric')
      .evaluateAll((metrics) => metrics.map((metric) => metric.getBoundingClientRect()));
    expect(
      Math.max(...metricBoxes.map((box) => box.top)) -
        Math.min(...metricBoxes.map((box) => box.top)),
    ).toBeLessThan(2);
  }
  const historyRowBox = await page.locator('#workout-history-43').boundingBox();
  const feedbackBox = await page
    .locator('#workout-history-43 .workout-feedback-disclosure')
    .boundingBox();
  expect(historyRowBox).not.toBeNull();
  expect(feedbackBox).not.toBeNull();
  expect(feedbackBox!.x).toBeGreaterThanOrEqual(historyRowBox!.x);
  expect(feedbackBox!.x + feedbackBox!.width).toBeLessThanOrEqual(
    historyRowBox!.x + historyRowBox!.width + 1,
  );

  await page.getByRole('button', { name: 'Ещё', exact: true }).click();
  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await page.keyboard.press('Escape');
  await expect(page.locator('.workout-feedback').first()).toHaveCSS('color', 'rgb(238, 240, 234)');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  if (captureFeedbackAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-49/client-feedback-mobile-dark.png',
      fullPage: true,
    });
  }

  await page.goBack();
  await expect(page).toHaveURL(/\/app(?:\?section=today)?$/);
  await expect(page.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
});

test('dark progress uses one lime accent for the adherence outcome', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('app-theme', 'dark'));
  await mockProgress(page);
  await page.goto('/app?section=progress');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('link', { name: 'Прогресс' }).click();

  const summaryScore = page.locator('.progress-summary__score');
  const adherenceScore = page.locator('.progress-adherence__score');
  await expect(summaryScore).toHaveText('84%');
  await expect(adherenceScore).toHaveText('84%');

  const colors = await page.evaluate(() => ({
    summary: getComputedStyle(document.querySelector('.progress-summary__score')!).color,
    adherence: getComputedStyle(document.querySelector('.progress-adherence__score')!).color,
    accent: (() => {
      const probe = document.createElement('span');
      probe.style.color = 'var(--v2-accent-text)';
      document.body.append(probe);
      const color = getComputedStyle(probe).color;
      probe.remove();
      return color;
    })(),
  }));
  expect(colors.summary).toBe(colors.adherence);
  expect(colors.summary).toBe(colors.accent);
});

test('light progress uses the restrained green accent for the adherence outcome', async ({
  page,
}) => {
  await page.addInitScript(() => localStorage.setItem('app-theme', 'light'));
  await mockProgress(page);
  await page.goto('/app?section=progress');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('link', { name: 'Прогресс' }).click();

  const summaryScore = page.locator('.progress-summary__score');
  const adherenceScore = page.locator('.progress-adherence__score');
  await expect(summaryScore).toHaveText('84%');
  await expect(adherenceScore).toHaveText('84%');

  const colors = await page.evaluate(() => ({
    summary: getComputedStyle(document.querySelector('.progress-summary__score')!).color,
    adherence: getComputedStyle(document.querySelector('.progress-adherence__score')!).color,
    accent: (() => {
      const probe = document.createElement('span');
      probe.style.color = 'var(--v2-accent-text)';
      document.body.append(probe);
      const color = getComputedStyle(probe).color;
      probe.remove();
      return color;
    })(),
  }));
  expect(colors.summary).toBe(colors.adherence);
  expect(colors.summary).toBe(colors.accent);
});
