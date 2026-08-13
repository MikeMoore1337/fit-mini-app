import { expect, test, type Page } from '@playwright/test';

test('логотип и кнопки в шапке имеют одинаковую высоту', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    const logo = await page.locator('.landing-header .landing-brand__mark').boundingBox();
    const themeButton = await page.locator('.landing-theme-toggle').boundingBox();
    const loginButton = await page.locator('.landing-button--compact').boundingBox();

    expect(logo).not.toBeNull();
    expect(themeButton).not.toBeNull();
    expect(loginButton).not.toBeNull();
    expect(logo?.height).toBe(44);
    expect(themeButton?.height).toBe(logo?.height);
    expect(loginButton?.height).toBe(logo?.height);
  }
});

test('первый экран лендинга объясняет продукт и не создаёт горизонтальный скролл', async ({
  page,
}) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(page.getByRole('heading', { name: /знайте, что делать сегодня/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /открыть приложение/i })).toBeVisible();
    await expect(page.getByLabel('Пример интерфейса тренировки на сегодня')).toBeVisible();
    await expect(page.getByText('Жим гантелей лёжа')).toBeVisible();
    await expect(page.getByText('+18%')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

test('блок возможностей показывает пользу спортсмену и инструменты тренеру', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(
      page.getByRole('heading', { name: /тренировки не должны жить в пяти разных местах/i }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /ведите своих клиентов в одном кабинете/i }),
    ).toBeVisible();
    await expect(page.getByText(/приглашайте клиентов, назначайте и корректируйте/i)).toBeVisible();
    if (viewport.width >= 768) {
      const sources = await page.locator('.landing-problem__sources').boundingBox();
      const result = await page.locator('.landing-problem__result').boundingBox();
      expect(sources).not.toBeNull();
      expect(result).not.toBeNull();
      expect(sources!.x + sources!.width).toBeLessThan(result!.x);
    } else {
      const sources = await page.locator('.landing-problem__sources').boundingBox();
      const result = await page.locator('.landing-problem__result').boundingBox();
      expect(sources).not.toBeNull();
      expect(result).not.toBeNull();
      expect(sources!.y + sources!.height).toBeLessThan(result!.y);
    }

    const featureCards = page.locator('.landing-feature');
    for (const card of await featureCards.all()) {
      const cardBox = await card.boundingBox();
      const metaBox = await card.locator('.landing-feature__meta').boundingBox();
      const paragraphBox = await card.locator('p').boundingBox();
      expect(cardBox).not.toBeNull();
      expect(metaBox).not.toBeNull();
      expect(paragraphBox).not.toBeNull();
      const topSpace = metaBox!.y - cardBox!.y;
      const bottomSpace = cardBox!.y + cardBox!.height - (paragraphBox!.y + paragraphBox!.height);
      expect(Math.abs(topSpace - bottomSpace)).toBeLessThanOrEqual(32);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

test('сценарий и платформы остаются понятными на разных экранах', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(page.locator('.landing-workflow li')).toHaveCount(5);
    await expect(page.getByRole('heading', { name: 'Выберите свой путь' })).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /один аккаунт.*два способа открыть/i }),
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: /когда нужен большой экран/i })).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /когда тренировка уже началась/i }),
    ).toBeVisible();

    const browserCard = await page.locator('.landing-platform-card').first().boundingBox();
    const telegramCard = await page.locator('.landing-platform-card').last().boundingBox();
    expect(browserCard).not.toBeNull();
    expect(telegramCard).not.toBeNull();
    if (viewport.width >= 768) {
      expect(browserCard!.x + browserCard!.width).toBeLessThan(telegramCard!.x);
    } else {
      expect(browserCard!.y + browserCard!.height).toBeLessThan(telegramCard!.y);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

async function mockApi(page: Page, { withCoachClient = false } = {}) {
  let role: 'client' | 'coach' | 'admin' = 'client';
  const heartRateZones = [
    { zone: 1, title: 'Восстановление', min_bpm: 130, max_bpm: 140 },
    { zone: 2, title: 'Лёгкая', min_bpm: 140, max_bpm: 151 },
    { zone: 3, title: 'Аэробная', min_bpm: 151, max_bpm: 162 },
    { zone: 4, title: 'Пороговая', min_bpm: 162, max_bpm: 173 },
    { zone: 5, title: 'Максимальная', min_bpm: 173, max_bpm: 184 },
  ];
  const emptyProgress = {
    workouts_total: 0,
    workouts_completed: 0,
    workouts_skipped: 0,
    workouts_missed: 0,
    adherence_percent: 0,
    current_streak: 0,
    weight_change_kg: null,
    weights: [],
    weekly_volume: [],
    personal_records: [],
  };
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (path.endsWith('/public/config'))
      return route.fulfill({
        json: { app_env: 'dev', enable_dev_auth: true, telegram_bot_username: 'fit_bot' },
      });
    if (path.endsWith('/auth/refresh'))
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    if (path.endsWith('/auth/dev-login')) {
      const body = request.postDataJSON() as { is_admin: boolean; is_coach: boolean };
      role = body.is_admin ? 'admin' : body.is_coach ? 'coach' : 'client';
      return route.fulfill({ json: { access_token: 'test-token', token_type: 'bearer' } });
    }
    if (path.endsWith('/me/profile/heart-rates/preview')) {
      const body = request.postDataJSON() as {
        resting_heart_rate: number | null;
        goal: 'fat_loss' | 'recomposition' | 'maintenance' | 'muscle_gain' | null;
      };
      const recommendations = {
        fat_loss: { min_bpm: 130, max_bpm: 140 },
        recomposition: { min_bpm: 124, max_bpm: 140 },
        maintenance: { min_bpm: 119, max_bpm: 140 },
        muscle_gain: { min_bpm: 119, max_bpm: 130 },
      };
      return route.fulfill({
        json: {
          estimated_max_heart_rate: 184,
          heart_rate_reserve: body.resting_heart_rate === null ? null : 109,
          heart_rate_calculation_method:
            body.resting_heart_rate === null ? 'percent_maximum' : 'heart_rate_reserve',
          heart_rate_zones: heartRateZones,
          recommended_cardio_range: body.goal ? recommendations[body.goal] : null,
        },
      });
    }
    if (path.endsWith('/me'))
      return route.fulfill({
        json: {
          id: 1,
          telegram_user_id: 2001,
          username: 'demo',
          first_name: 'Демо',
          is_coach: role !== 'client',
          is_admin: role === 'admin',
          has_active_program: false,
          has_workout_history: false,
          profile: { full_name: 'Демо пользователь', timezone: 'Europe/Moscow', kbju: null },
          trainer: null,
        },
      });
    if (path.endsWith('/workouts/today'))
      return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка не назначена' } });
    if (path.endsWith('/workouts/progress')) return route.fulfill({ json: emptyProgress });
    if (path.endsWith('/workouts/schedule')) return route.fulfill({ json: [] });
    if (path.endsWith('/workouts/history/summary'))
      return route.fulfill({
        json: { workouts_completed: 0, completed_sets: 0, volume_kg: 0 },
      });
    if (path.endsWith('/workouts/history') || path.endsWith('/workouts/week'))
      return route.fulfill({ json: [] });
    if (path.endsWith('/me/coach-invites/link/preview'))
      return route.fulfill({
        json: {
          invite_id: 77,
          coach: {
            id: 9,
            telegram_user_id: 9009,
            username: 'test_coach',
            full_name: 'Тестовый тренер',
            can_open_chat: true,
            chat_url: 'https://t.me/test_coach',
            chat_unavailable_reason: null,
          },
          created_at: '2030-01-01T10:00:00',
          expires_at: '2030-01-15T10:00:00',
          requires_trainer_change: false,
          already_current_trainer: false,
          current_trainer: null,
        },
      });
    if (path.endsWith('/me/coach-invites/link/confirm'))
      return route.fulfill({ status: 204, body: '' });
    if (path.endsWith('/notifications/settings'))
      return route.fulfill({
        json: { workout_reminders_enabled: true, reminder_hour: 9 },
      });
    if (path.endsWith('/notifications')) return route.fulfill({ json: [] });
    if (path.endsWith('/programs/exercises/1/guide'))
      return route.fulfill({
        json: {
          technique_steps: ['Зафиксируйте корпус', 'Выполните движение под контролем'],
          breathing: 'Выдох в фазе усилия, вдох при возврате.',
          common_mistakes: ['Раскачивание корпусом'],
          muscles: [
            { name: 'Спина', role: 'Основная', function: 'Тянет плечевой пояс назад.' },
            { name: 'Бицепс', role: 'Вспомогательная', function: 'Сгибает локоть.' },
          ],
          images: [
            {
              phase: 'Исходное положение',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              alt: 'Исходное положение',
            },
            {
              phase: 'Активная фаза',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              alt: 'Активная фаза',
            },
          ],
          source_name: 'Test source',
          source_url: 'https://example.com',
          source_license: 'Public domain',
        },
      });
    if (path.endsWith('/programs/exercises'))
      return route.fulfill({
        json: [
          {
            id: 1,
            title: 'Тяга блока',
            primary_muscle: 'Спина',
            equipment: 'Блок',
            difficulty_level: 'beginner',
            is_custom: false,
            is_personalized: false,
            has_guide: true,
            guide: null,
          },
        ],
      });
    if (path.endsWith('/programs/templates/mine'))
      return route.fulfill({
        json: [
          {
            id: 10,
            title: 'Программа на всё тело — 3 дня',
            slug: 'full-body-3-days',
            goal: 'recomposition',
            level: 'beginner',
            owner_user_id: null,
            owner_telegram_user_id: null,
            owner_full_name: null,
            created_by_user_id: null,
            is_public: true,
            is_example: true,
            is_assigned_to_current_user: false,
            is_active_for_current_user: false,
            assigned_by_user_id: null,
            assigned_by_full_name: null,
            days: [
              {
                id: 100,
                day_number: 1,
                title: 'Всё тело',
                exercises: [
                  {
                    id: 1000,
                    exercise_id: 1,
                    exercise_title: 'Тяга блока',
                    prescribed_sets: 3,
                    prescribed_reps: '10–12',
                    rest_seconds: 90,
                    notes: null,
                    has_guide: true,
                  },
                ],
              },
            ],
          },
        ],
      });
    if (path.endsWith('/programs/templates/hidden')) return route.fulfill({ json: [] });
    if (path.endsWith('/admin/users')) return route.fulfill({ json: [] });
    if (/\/coach\/clients\/\d+\/analytics$/.test(path))
      return route.fulfill({ json: emptyProgress });
    if (/\/coach\/clients\/\d+\/workouts$/.test(path)) return route.fulfill({ json: [] });
    if (path.endsWith('/coach/clients'))
      return route.fulfill({
        json: withCoachClient
          ? [
              {
                id: 2,
                invite_id: null,
                telegram_user_id: 3002,
                username: 'client',
                full_name: 'Тестовый клиент',
                goal: 'maintenance',
                level: 'beginner',
                height_cm: 175,
                weight_kg: 75,
                workouts_per_week: 3,
                cardio_trainings_per_week: 1,
                kbju: null,
                status: 'active',
              },
            ]
          : [],
      });
    return route.fulfill({ json: [] });
  });
}

test('клиент входит и видит экран тренировки', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await expect(page.getByRole('heading', { name: 'Демо пользователь' })).toBeVisible();
  await expect(page.getByText('Сегодня отдых')).toBeVisible();
});

test('deep link показывает тренера до явного подтверждения', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app?startapp=trainer_test-invite-token');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await expect(page.getByRole('heading', { name: 'Тестовый тренер' })).toBeVisible();
  await page.getByRole('button', { name: 'Подтвердить подключение' }).click();
  await expect(page.getByText('Тренер подключён')).toBeVisible();
});

test('мобильный интерфейс не обрезает навигацию и текст плана', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 780 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  const tabs = page.getByRole('tab');
  await expect(tabs).toHaveCount(6);
  for (const tab of await tabs.all()) await expect(tab).toBeInViewport();

  const firstStep = page.getByRole('button', { name: /Заполнить профиль/ });
  const title = firstStep.getByText('Заполнить профиль', { exact: true });
  const description = firstStep.getByText('Дата рождения, цель, уровень и текущий вес', {
    exact: true,
  });
  const [titleBox, descriptionBox] = await Promise.all([
    title.boundingBox(),
    description.boundingBox(),
  ]);
  expect(titleBox).not.toBeNull();
  expect(descriptionBox).not.toBeNull();
  expect(titleBox!.y + titleBox!.height).toBeLessThanOrEqual(descriptionBox!.y);

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeInViewport();
});

test('профиль содержит уведомления, а карточка упражнения открывает полное описание', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 780 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await page.getByRole('tab', { name: 'Профиль' }).click();
  await expect(page.getByRole('heading', { name: 'Напоминания о тренировках' })).toBeVisible();
  await expect(page.getByText('Личные уведомления')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Подписка' })).toHaveCount(0);

  const birthDate = page.getByLabel('Дата рождения');
  const birthDateControl = page.locator('.profile-birth-date-control');
  const [birthDateBox, birthDateControlBox] = await Promise.all([
    birthDate.boundingBox(),
    birthDateControl.boundingBox(),
  ]);
  expect(birthDateBox).not.toBeNull();
  expect(birthDateControlBox).not.toBeNull();
  expect(birthDateBox!.x).toBeGreaterThanOrEqual(birthDateControlBox!.x);
  expect(birthDateBox!.x + birthDateBox!.width).toBeLessThanOrEqual(
    birthDateControlBox!.x + birthDateControlBox!.width,
  );

  const reminderTime = page.getByLabel('Час отправки');
  const reminderTimeControl = page.locator('.reminder-time-control');
  const [reminderTimeBox, reminderTimeControlBox] = await Promise.all([
    reminderTime.boundingBox(),
    reminderTimeControl.boundingBox(),
  ]);
  expect(reminderTimeBox).not.toBeNull();
  expect(reminderTimeControlBox).not.toBeNull();
  expect(reminderTimeBox!.x).toBeGreaterThanOrEqual(reminderTimeControlBox!.x);
  expect(reminderTimeBox!.x + reminderTimeBox!.width).toBeLessThanOrEqual(
    reminderTimeControlBox!.x + reminderTimeControlBox!.width,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByText('Личные уведомления').click();
  const notificationDate = page.locator('.notification-date-control input');
  await expect(notificationDate).toHaveAttribute('type', 'date');
  await expect(notificationDate).toHaveCSS('text-align', 'center');
  await expect(page.locator('input[type="datetime-local"]')).toHaveCount(0);
  const [notificationDateBox, notificationDateControlBox] = await Promise.all([
    notificationDate.boundingBox(),
    page.locator('.notification-date-control').boundingBox(),
  ]);
  expect(notificationDateBox).not.toBeNull();
  expect(notificationDateControlBox).not.toBeNull();
  expect(notificationDateBox!.x).toBeGreaterThanOrEqual(notificationDateControlBox!.x);
  expect(notificationDateBox!.x + notificationDateBox!.width).toBeLessThanOrEqual(
    notificationDateControlBox!.x + notificationDateControlBox!.width,
  );

  const notificationRequest = page.waitForRequest(
    (request) =>
      new URL(request.url()).pathname.endsWith('/notifications') && request.method() === 'POST',
  );
  await page.getByRole('button', { name: 'Создать уведомление' }).click();
  const notificationPayload = (await notificationRequest).postDataJSON() as {
    scheduled_for: string;
  };
  expect(notificationPayload.scheduled_for).toMatch(/^\d{4}-\d{2}-\d{2}T09:00:00$/);

  await page.getByRole('tab', { name: 'Питание' }).click();
  await expect(page.getByRole('heading', { name: 'Напоминания о тренировках' })).toHaveCount(0);

  await page.getByRole('tab', { name: 'Упражнения' }).click();
  await page.getByRole('button', { name: 'Техника' }).click();
  await expect(page.getByRole('heading', { name: 'Для чего это упражнение' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какие мышцы работают' })).toBeVisible();
  await expect(page.getByText('Тянет плечевой пояс назад.')).toBeVisible();
  const [guidePanelBox, guideHeadBox] = await Promise.all([
    page.locator('.exercise-guide-modal__panel').boundingBox(),
    page.locator('.exercise-guide-modal__head').boundingBox(),
  ]);
  expect(guidePanelBox).not.toBeNull();
  expect(guideHeadBox).not.toBeNull();
  expect(Math.abs(guideHeadBox!.x - guidePanelBox!.x)).toBeLessThanOrEqual(2);
  expect(
    Math.abs(guideHeadBox!.x + guideHeadBox!.width - (guidePanelBox!.x + guidePanelBox!.width)),
  ).toBeLessThanOrEqual(2);
  await page.getByRole('button', { name: 'Увеличить: Исходное положение' }).click();
  await expect(page.locator('.exercise-lightbox')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.exercise-lightbox')).toHaveCount(0);
});

test('рекомендация кардио меняется с целью, а физиологические зоны остаются прежними', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await page.getByRole('tab', { name: 'Профиль' }).click();

  await page.getByLabel('Дата рождения').fill('1992-08-12');
  await page.getByText('Средний пульс в покое, уд/мин').locator('..').locator('input').fill('75');
  await page.getByLabel('Цель').selectOption('fat_loss');
  await expect(page.getByText('130–140 уд/мин')).toHaveCount(2);

  const zones = page.getByText('Пульсовые зоны').locator('..').locator('+ .list-grid');
  const initialZones = await zones.textContent();

  await page.getByLabel('Цель').selectOption('recomposition');
  await expect(page.getByText('124–140 уд/мин')).toBeVisible();
  await page.getByLabel('Цель').selectOption('maintenance');
  await expect(page.getByText('119–140 уд/мин')).toBeVisible();
  await page.getByLabel('Цель').selectOption('muscle_gain');
  await expect(page.getByText('119–130 уд/мин')).toBeVisible();

  await expect(zones).toHaveText(initialZones ?? '');
  await expect(page.getByText('184 уд/мин', { exact: true })).toBeVisible();
  await expect(page.locator('body')).not.toContainText('HRR');
  await expect(page.locator('body')).not.toContainText('MET');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('поля профиля и питания выровнены на десктопе и остаются адаптивными', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await page.getByRole('tab', { name: 'Профиль' }).click();
  const profileControlTops = await page.locator('.profile-form-grid').evaluate((grid) =>
    Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field'))
      .slice(6)
      .map((field) => {
        const control = field.querySelector<HTMLElement>('input, select, .date-control');
        return control?.getBoundingClientRect().top ?? 0;
      }),
  );
  expect(new Set(profileControlTops.map(Math.round)).size).toBe(1);

  await page.getByRole('tab', { name: 'Питание' }).click();
  const nutritionControlTops = await page
    .locator('.nutrition-form-grid')
    .first()
    .evaluate((grid) =>
      Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field'))
        .slice(5, 8)
        .map((field) => {
          const control = field.querySelector<HTMLElement>('input, select');
          return control?.getBoundingClientRect().top ?? 0;
        }),
    );
  expect(new Set(nutritionControlTops.map(Math.round)).size).toBe(1);

  await page.setViewportSize({ width: 390, height: 844 });
  const mobileFields = await page
    .locator('.nutrition-form-grid')
    .first()
    .evaluate((grid) =>
      Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field')).map((field) => {
        const box = field.getBoundingClientRect();
        return { left: box.left, right: box.right, top: box.top };
      }),
    );
  expect(mobileFields.every((field) => field.left >= 0 && field.right <= 390)).toBe(true);
  expect(
    mobileFields.every((field, index) => index === 0 || field.top > mobileFields[index - 1]!.top),
  ).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('поля адаптируются к разным iPhone, а пример программы открывает состав', async ({ page }) => {
  await page.setViewportSize({ width: 440, height: 956 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await page.getByRole('tab', { name: 'Прогресс' }).click();
  const dateField = page.getByLabel('Дата');
  const weightField = page.getByLabel('Вес, кг');
  const diaryGrid = page.locator('.diary-form-grid');
  const dateControl = page.locator('.diary-date-control');
  const [dateBox, dateControlBox, weightBox, diaryGridBox] = await Promise.all([
    dateField.boundingBox(),
    dateControl.boundingBox(),
    weightField.boundingBox(),
    diaryGrid.boundingBox(),
  ]);
  expect(dateBox).not.toBeNull();
  expect(dateControlBox).not.toBeNull();
  expect(weightBox).not.toBeNull();
  expect(diaryGridBox).not.toBeNull();
  expect(dateBox!.y + dateBox!.height).toBeLessThanOrEqual(weightBox!.y);
  expect(dateControlBox!.x).toBeGreaterThanOrEqual(diaryGridBox!.x);
  expect(dateControlBox!.x + dateControlBox!.width).toBeLessThanOrEqual(
    diaryGridBox!.x + diaryGridBox!.width,
  );
  expect(dateBox!.x).toBeGreaterThanOrEqual(dateControlBox!.x);
  expect(dateBox!.x + dateBox!.width).toBeLessThanOrEqual(
    dateControlBox!.x + dateControlBox!.width,
  );

  await page.getByRole('tab', { name: 'Питание' }).click();
  expect(
    await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    })),
  ).toEqual({ viewport: 440, content: 440 });
  await page.evaluate(() => window.scrollTo({ left: 1000 }));
  expect(await page.evaluate(() => window.scrollX)).toBe(0);

  await page.getByRole('tab', { name: 'Упражнения' }).click();
  const search = page.getByRole('combobox', { name: 'Поиск в каталоге упражнений' });
  await search.focus();
  await expect(page.getByRole('option', { name: /Тяга блока/ })).toBeVisible();
  const searchBox = await search.boundingBox();
  expect(searchBox).not.toBeNull();
  expect(searchBox!.x + searchBox!.width).toBeLessThanOrEqual(440);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );

  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );

  await page.getByRole('tab', { name: 'Программы' }).click();
  const example = page.getByRole('button', {
    name: 'Посмотреть пример программы «Программа на всё тело — 3 дня»',
  });
  await expect(example).toContainText('Рекомпозиция · Начальный уровень · 1 дн.');
  await expect(example).toContainText('Пример программы');
  await expect(example).not.toContainText('recomposition');
  await expect(example).not.toContainText('beginner');
  await example.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'День 1. Всё тело' })).toBeVisible();
  await expect(page.getByRole('dialog').getByText('Тяга блока')).toBeVisible();
  await expect(page.getByRole('dialog').getByText('3 подх. × 10–12 · отдых 90 сек.')).toBeVisible();
  const [programPanelBox, programHeadBox] = await Promise.all([
    page.locator('.program-example-modal__panel').boundingBox(),
    page.locator('.program-example-modal__head').boundingBox(),
  ]);
  expect(programPanelBox).not.toBeNull();
  expect(programHeadBox).not.toBeNull();
  expect(programPanelBox!.x).toBeLessThanOrEqual(1);
  expect(Math.abs(programPanelBox!.width - 390)).toBeLessThanOrEqual(1);
  expect(Math.abs(programHeadBox!.x - programPanelBox!.x)).toBeLessThanOrEqual(2);
  expect(
    Math.abs(
      programHeadBox!.x + programHeadBox!.width - (programPanelBox!.x + programPanelBox!.width),
    ),
  ).toBeLessThanOrEqual(2);
  await page.getByRole('button', { name: 'Есть техника — посмотреть' }).click();
  const exerciseGuide = page.locator('.exercise-guide-modal__panel');
  await expect(exerciseGuide.getByRole('img', { name: 'Исходное положение' })).toBeVisible();
  await expect(exerciseGuide.getByRole('img', { name: 'Активная фаза' })).toBeVisible();
  await expect(exerciseGuide.getByText('Исходное положение', { exact: true })).toBeVisible();
  await expect(exerciseGuide.getByText('Активная фаза', { exact: true })).toBeVisible();
});

test('сенсорное поле даты сохраняет нативный пикер и показывает иконку календаря', async ({
  browser,
}) => {
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:4173',
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const page = await context.newPage();

  try {
    await mockApi(page);
    await page.goto('/app');
    await page.getByRole('button', { name: 'Клиент' }).click();
    await page.getByRole('tab', { name: 'Прогресс' }).click();

    const dateField = page.getByLabel('Дата');
    const dateControl = page.locator('.diary-date-control');
    await expect(dateField).toHaveAttribute('type', 'date');
    const fallbackIcon = await dateControl.evaluate((element) => {
      const style = getComputedStyle(element, '::after');
      return {
        content: style.content,
        height: style.height,
        mask: style.maskImage || style.getPropertyValue('-webkit-mask-image'),
        pointerEvents: style.pointerEvents,
        width: style.width,
      };
    });
    expect(fallbackIcon).toMatchObject({
      content: '""',
      height: '18px',
      pointerEvents: 'none',
      width: '18px',
    });
    expect(fallbackIcon.mask).toContain('svg');

    await dateControl.scrollIntoViewIfNeeded();
    const dateControlBox = await dateControl.boundingBox();
    expect(dateControlBox).not.toBeNull();
    await dateField.evaluate((element) => {
      element.addEventListener('click', () => element.setAttribute('data-picker-clicked', 'true'), {
        once: true,
      });
    });
    await page.mouse.click(
      dateControlBox!.x + dateControlBox!.width - 14,
      dateControlBox!.y + dateControlBox!.height / 2,
    );
    await expect(dateField).toHaveAttribute('data-picker-clicked', 'true');
  } finally {
    await context.close();
  }
});

test('администратор открывает React-панель', async ({ page }) => {
  await mockApi(page);
  await page.goto('/admin');
  await page.getByRole('button', { name: 'Админ' }).click();
  await expect(page.getByRole('heading', { name: 'Панель администратора' })).toBeVisible();
  await expect(page.getByText('Пользователи не найдены')).toBeVisible();
});

test('поля даты остаются внутри анкеты клиента в кабинете тренера', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page, { withCoachClient: true });
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();

  const birthDateField = page.getByLabel('Дата рождения');
  const birthDateBox = await birthDateField.boundingBox();
  const birthDateControlBox = await page.locator('.coach-client-birth-date-control').boundingBox();
  expect(birthDateBox).not.toBeNull();
  expect(birthDateControlBox).not.toBeNull();
  expect(birthDateBox!.x).toBeGreaterThanOrEqual(birthDateControlBox!.x);
  expect(birthDateBox!.x + birthDateBox!.width).toBeLessThanOrEqual(
    birthDateControlBox!.x + birthDateControlBox!.width,
  );

  await page.getByText('Прогресс и замеры', { exact: true }).click();

  const dateField = page.getByLabel('Дата', { exact: true });
  const dateBox = await dateField.boundingBox();
  await expect(dateField).toHaveCSS('text-align', 'center');
  const dateControlBox = await page.locator('.diary-date-control').boundingBox();
  const diaryGridBox = await page.locator('.diary-form-grid').boundingBox();
  expect(dateBox).not.toBeNull();
  expect(dateControlBox).not.toBeNull();
  expect(diaryGridBox).not.toBeNull();
  expect(dateControlBox!.x).toBeGreaterThanOrEqual(diaryGridBox!.x);
  expect(dateControlBox!.x + dateControlBox!.width).toBeLessThanOrEqual(
    diaryGridBox!.x + diaryGridBox!.width,
  );
  expect(dateBox!.x).toBeGreaterThanOrEqual(dateControlBox!.x);
  expect(dateBox!.x + dateBox!.width).toBeLessThanOrEqual(
    dateControlBox!.x + dateControlBox!.width,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('тренер открывает кабинет', async ({ page }) => {
  await mockApi(page);
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();
  await expect(page.getByRole('heading', { name: 'Кабинет тренера' })).toBeVisible();
  await expect(page.getByText('Клиентов пока нет')).toBeVisible();
});
