import { expect, test, type Page } from '@playwright/test';

async function mockApi(page: Page) {
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
    if (path.endsWith('/admin/users')) return route.fulfill({ json: [] });
    if (path.endsWith('/coach/clients')) return route.fulfill({ json: [] });
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

test('администратор открывает React-панель', async ({ page }) => {
  await mockApi(page);
  await page.goto('/admin');
  await page.getByRole('button', { name: 'Админ' }).click();
  await expect(page.getByRole('heading', { name: 'Панель администратора' })).toBeVisible();
  await expect(page.getByText('Пользователи не найдены')).toBeVisible();
});

test('тренер открывает кабинет', async ({ page }) => {
  await mockApi(page);
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();
  await expect(page.getByRole('heading', { name: 'Кабинет тренера' })).toBeVisible();
  await expect(page.getByText('Клиентов пока нет')).toBeVisible();
});
