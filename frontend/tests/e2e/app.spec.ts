import { expect, test, type Page } from '@playwright/test';

async function mockApi(page: Page, { withCoachClient = false } = {}) {
  let role: 'client' | 'coach' | 'admin' = 'client';
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
    if (path.endsWith('/me'))
      return route.fulfill({
        json: {
          id: 1,
          telegram_user_id: 2001,
          username: 'demo',
          first_name: 'Демо',
          client_code: 'ABC123',
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
                  },
                ],
              },
            ],
          },
        ],
      });
    if (path.endsWith('/programs/templates/hidden')) return route.fulfill({ json: [] });
    if (path.endsWith('/admin/users')) return route.fulfill({ json: [] });
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
  const description = firstStep.getByText('Цель, уровень и текущий вес', { exact: true });
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

  await page.getByRole('tab', { name: 'Питание' }).click();
  await expect(page.getByRole('heading', { name: 'Напоминания о тренировках' })).toHaveCount(0);

  await page.getByRole('tab', { name: 'Упражнения' }).click();
  await page.getByRole('button', { name: 'Техника' }).click();
  await expect(page.getByRole('heading', { name: 'Для чего это упражнение' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какие мышцы работают' })).toBeVisible();
  await expect(page.getByText('Тянет плечевой пояс назад.')).toBeVisible();
  await page.getByRole('button', { name: 'Увеличить: Исходное положение' }).click();
  await expect(page.locator('.exercise-lightbox')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.exercise-lightbox')).toHaveCount(0);
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
});

test('администратор открывает React-панель', async ({ page }) => {
  await mockApi(page);
  await page.goto('/admin');
  await page.getByRole('button', { name: 'Админ' }).click();
  await expect(page.getByRole('heading', { name: 'Панель администратора' })).toBeVisible();
  await expect(page.getByText('Пользователи не найдены')).toBeVisible();
});

test('дата остаётся внутри анкеты клиента в кабинете тренера', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page, { withCoachClient: true });
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();
  await page.getByText('Прогресс и замеры', { exact: true }).click();

  const dateBox = await page.getByLabel('Дата').boundingBox();
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
