import { expect, test, type Page } from '@playwright/test';

const captureAudit = Boolean(
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.CAPTURE_COACH_AUDIT,
);

const clients = [
  {
    id: 11,
    invite_id: null,
    telegram_user_id: 3011,
    username: 'anna_runner',
    full_name: 'Анна Петрова',
    goal: 'maintenance',
    level: 'intermediate',
    height_cm: 168,
    weight_kg: 62,
    workouts_per_week: 3,
    cardio_trainings_per_week: 1,
    timezone: 'Europe/Moscow',
    kbju: null,
    status: 'active',
  },
  {
    id: 12,
    invite_id: null,
    telegram_user_id: 3012,
    username: 'boris_long',
    full_name: 'Борис Александрович С Очень Длинной Фамилией',
    goal: 'muscle_gain',
    level: 'beginner',
    height_cm: 190,
    weight_kg: 92,
    workouts_per_week: 2,
    cardio_trainings_per_week: 0,
    timezone: 'Europe/Moscow',
    kbju: null,
    status: 'active',
  },
  {
    id: 13,
    invite_id: null,
    telegram_user_id: 3013,
    username: 'maria',
    full_name: 'Мария Орлова',
    goal: 'fat_loss',
    level: 'advanced',
    height_cm: 172,
    weight_kg: 70,
    workouts_per_week: 4,
    cardio_trainings_per_week: 2,
    timezone: 'Europe/Moscow',
    kbju: null,
    status: 'active',
  },
  {
    id: null,
    invite_id: 91,
    telegram_user_id: null,
    username: null,
    full_name: 'Елена — приглашение ожидает подтверждения',
    status: 'pending',
  },
];

const component = (
  status: 'available' | 'not_applicable',
  percent: number | null,
  achieved: number,
  evaluated: number,
) => ({ status, percent, achieved, evaluated, weight: status === 'available' ? 1 : 0 });

function summary(
  userId: number,
  name: string,
  lastWorkout: string | null,
  personalRecords: number,
  measuredOn: string | null,
) {
  return {
    user_id: userId,
    client_name: name,
    period_days: 30,
    period_start: '2026-07-22',
    period_end: '2026-08-20',
    training: {
      planned_workouts: 8,
      completed_workouts: 6,
      frequency_per_week: 1.5,
      volume_kg: 14200,
      new_personal_records: personalRecords,
      last_completed_workout_on: lastWorkout,
      next_workout:
        userId === 11
          ? {
              id: 501,
              scheduled_date: '2026-08-22',
              scheduled_time: '18:30:00',
              title: 'Ноги и корпус',
              status: 'planned',
            }
          : null,
    },
    nutrition: {
      visible: userId !== 13,
      logged_days: userId === 13 ? 0 : 16,
      adherence_evaluated_days: userId === 13 ? 0 : 14,
      average_calories: userId === 13 ? null : 2050,
      target_calories: userId === 13 ? null : 2150,
      average_protein_g: userId === 13 ? null : 132,
      target_protein_g: userId === 13 ? null : 140,
      target_effective_on: userId === 13 ? null : '2026-07-01',
    },
    body: {
      latest_measurement: measuredOn ? { measured_on: measuredOn, weight_kg: 68.5 } : null,
      trends: [],
      priority: null,
      guidance: {},
    },
    adherence: {
      formula_version: 'adherence-v1',
      overall_percent: 75,
      included_components: ['workouts'],
      workouts: component('available', 75, 6, 8),
      cardio: component('not_applicable', null, 0, 0),
      calories: component('not_applicable', null, 0, 0),
      protein: component('not_applicable', null, 0, 0),
    },
    data_sufficiency: {},
  };
}

async function mockCoachWorkspace(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/public/config'))
      return route.fulfill({
        json: { app_env: 'dev', enable_dev_auth: true, telegram_bot_username: 'fit_bot' },
      });
    if (path.endsWith('/auth/refresh'))
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    if (path.endsWith('/auth/dev-login'))
      return route.fulfill({ json: { access_token: 'coach-token', token_type: 'bearer' } });
    if (path.endsWith('/me'))
      return route.fulfill({
        json: {
          id: 1,
          telegram_user_id: 2001,
          username: 'coach',
          first_name: 'Ирина',
          is_coach: true,
          is_admin: false,
          has_active_program: true,
          has_workout_history: true,
          onboarding: { status: 'complete', required_fields: [], missing_fields: [] },
          profile: {
            full_name: 'Ирина Тренер',
            goal: 'maintenance',
            level: 'advanced',
            workouts_per_week: 3,
            timezone: 'Europe/Moscow',
            kbju: null,
          },
          trainer: null,
        },
      });
    if (path.endsWith('/coach/client-summaries'))
      return route.fulfill({
        json: {
          items: [
            summary(11, 'Анна Петрова', '2026-08-19', 2, '2026-08-18'),
            summary(12, 'Борис Александрович', '2026-08-08', 0, null),
            summary(13, 'Мария Орлова', null, 1, '2026-08-01'),
          ],
          total: 3,
          limit: 100,
          offset: 0,
        },
      });
    if (path.endsWith('/coach/assigned-programs'))
      return route.fulfill({
        json: [
          {
            id: 701,
            client_id: 11,
            client_telegram_user_id: 3011,
            client_username: 'anna_runner',
            client_full_name: 'Анна Петрова',
            template_id: 17,
            title: 'Силовая база · четыре недели',
            goal: 'maintenance',
            level: 'intermediate',
            assigned_at: '2026-08-01T10:00:00',
            is_active: true,
            status: 'active',
            start_date: '2026-08-03',
            duration_weeks: 4,
            schedule_weekdays: [1, 3, 5],
            completed_at: null,
            workouts_total: 12,
            workouts_completed: 5,
            next_workout_date: '2026-08-22',
            current_revision_number: 2,
          },
        ],
      });
    if (path.endsWith('/coach/clients')) return route.fulfill({ json: clients });
    if (path.endsWith('/programs/exercises')) return route.fulfill({ json: [] });
    if (/\/programs\/assigned\/\d+\/(revisions|blocks)$/.test(path))
      return route.fulfill({ json: [] });
    if (path.endsWith('/coach/invite-links') && request.method() === 'POST')
      return route.fulfill({
        json: {
          token: 'test',
          start_param: 'coach_test',
          code: 'YFC-TEST',
          url: 'https://example.test/join/test',
          web_url: 'https://example.test/join/test',
          telegram_url: 'https://t.me/fit_bot?startapp=coach_test',
          expires_at: '2026-08-27T12:00:00',
        },
      });
    return route.fulfill({ json: [] });
  });
}

async function openCoach(page: Page) {
  await mockCoachWorkspace(page);
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();
  await expect(page.getByRole('heading', { name: 'Кабинет тренера' })).toBeVisible();
}

test('dashboard даёт обзор и фильтрует клиентов без загрузки полной истории', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const fullHistoryRequests: string[] = [];
  page.on('request', (request) => {
    const path = new URL(request.url()).pathname;
    if (/\/coach\/clients\/\d+\/(workouts|training-analytics)$/.test(path)) {
      fullHistoryRequests.push(path);
    }
  });
  await openCoach(page);

  await expect(page.getByText('Состояние клиентской базы')).toBeVisible();
  await expect(
    page.getByLabel('Состояние клиентской базы').getByText('Тренировались за 7 дней'),
  ).toBeVisible();
  await expect(page.getByText('Борис Александрович С Очень Длинной Фамилией')).toBeVisible();
  await expect(page.getByText('Сейчас открыт клиент')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Анна Петрова', exact: true })).toBeVisible();
  await expect(page.locator('.coach-client-program .ui-badge--success')).toHaveCSS(
    'border-radius',
    '8px',
  );
  await expect(page.locator('.coach-client-program .ui-badge--success')).toHaveCSS(
    'padding-top',
    '3px',
  );
  expect(
    (await page.locator('.coach-client-program .ui-badge--success').boundingBox())?.height,
  ).toBeLessThanOrEqual(26);
  expect(fullHistoryRequests).toEqual([]);

  if (captureAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-48/coach-desktop-light.png',
      fullPage: true,
    });
  }

  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await expect(page.getByRole('tab', { name: 'Клиенты' })).toHaveCSS(
    'background-color',
    'rgb(22, 25, 22)',
  );
  await expect(page.getByLabel('Найти клиента')).toHaveCSS('background-color', 'rgb(22, 25, 22)');
  await expect(page.getByRole('button', { name: 'Пригласить клиента', exact: true })).toHaveCSS(
    'background-color',
    'rgb(168, 232, 58)',
  );
  if (captureAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-48/coach-desktop-dark.png',
      fullPage: true,
    });
  }
  await page.getByRole('button', { name: 'Включить светлую тему' }).click();

  await page.getByLabel('Показать').selectOption('attention');
  await expect(page.getByText('Анна Петрова', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Борис Александрович С Очень Длинной Фамилией')).toBeVisible();
  await expect(page.getByText('Мария Орлова')).toBeVisible();

  await page.getByLabel('Найти клиента').fill('Борис');
  await expect(page.getByText('Мария Орлова')).toHaveCount(0);
  await expect(page.getByText('Борис Александрович С Очень Длинной Фамилией')).toBeVisible();
  await page.getByLabel('Найти клиента').fill('');
  await page.getByLabel('Показать').selectOption('pending');
  await expect(page.locator('.coach-client-roster .coach-client-row')).toHaveCount(1);
  await expect(page.getByText('Елена — приглашение ожидает подтверждения')).toBeVisible();
  await page.getByRole('button', { name: 'Пригласить клиента', exact: true }).click();
  await expect(page.getByLabel('Универсальная ссылка — для браузера и Telegram')).toHaveValue(
    'https://example.test/join/test',
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(1440);
});

test('mobile использует список и отдельный контекст клиента', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openCoach(page);

  expect((await page.locator('.coach-workspace-header').boundingBox())?.height).toBeLessThan(190);
  await expect(page.getByRole('heading', { name: 'Анна Петрова', exact: true })).toBeHidden();
  await page.getByRole('button', { name: /Борис Александрович/ }).click();
  await expect(
    page.getByRole('heading', {
      name: 'Борис Александрович С Очень Длинной Фамилией',
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText('Сейчас открыт клиент')).toBeVisible();
  await expect(page.getByText('Цель: Набор мышц')).toBeVisible();
  await expect(page.getByRole('button', { name: 'К списку клиентов' })).toBeVisible();
  await expect(page.getByRole('tablist', { name: 'Разделы тренера' })).toBeHidden();
  const headerBox = await page.locator('.coach-workspace-header').boundingBox();
  const dashboardEyebrowBox = await page.locator('.coach-dashboard .eyebrow').boundingBox();
  expect(
    (dashboardEyebrowBox?.y ?? 0) - ((headerBox?.y ?? 0) + (headerBox?.height ?? 0)),
  ).toBeLessThanOrEqual(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByText('Назначить новую программу').click();
  await expect(page.getByRole('heading', { name: 'Тренировочные дни' })).toBeVisible();
  const trainingFields = page.locator('.program-exercise-row__metrics .field');
  await expect(trainingFields).toHaveCount(3);
  const fieldBoxes = await trainingFields.evaluateAll((fields) =>
    fields.map((field) => field.getBoundingClientRect()),
  );
  expect(fieldBoxes.every((box) => box.width >= 70)).toBe(true);
  expect(
    Math.max(...fieldBoxes.map((box) => box.top)) - Math.min(...fieldBoxes.map((box) => box.top)),
  ).toBeLessThan(2);
  const dayHeader = page.locator('.program-day__head');
  const dayInput = dayHeader.getByLabel('Название дня 1');
  const dayControls = dayHeader.locator('.program-order-controls');
  expect((await dayControls.boundingBox())?.y).toBeLessThan(
    ((await dayInput.boundingBox())?.y ?? 0) + ((await dayInput.boundingBox())?.height ?? 0),
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  if (captureAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-48/coach-mobile-program-390.png',
      fullPage: true,
    });
  }

  await page.getByRole('button', { name: 'Ещё', exact: true }).click();
  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await page.keyboard.press('Escape');
  await expect(dayInput).toHaveCSS('background-color', 'rgb(22, 25, 22)');
  await expect(dayControls.getByRole('button', { name: 'Переместить день 1 выше' })).toHaveCSS(
    'background-color',
    'rgba(0, 0, 0, 0)',
  );
  if (captureAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-48/coach-mobile-program-dark-390.png',
      fullPage: true,
    });
  }

  await page.setViewportSize({ width: 360, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);
  expect(
    (
      await trainingFields.evaluateAll((fields) =>
        fields.map((field) => field.getBoundingClientRect().width),
      )
    ).every((width) => width >= 65),
  ).toBe(true);
  await page.getByRole('button', { name: 'Ещё', exact: true }).click();
  await page.getByRole('button', { name: 'Включить светлую тему' }).click();
  await page.keyboard.press('Escape');

  await page.getByRole('button', { name: 'К списку клиентов' }).click();
  await expect(page.getByLabel('Найти клиента')).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);
  if (captureAudit) {
    await page.screenshot({
      path: '../.artifacts/ui-audit/task-48/coach-mobile-360.png',
      fullPage: true,
    });
  }
});
