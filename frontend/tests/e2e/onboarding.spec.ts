import { expect, test, type Page } from '@playwright/test';

type OnboardingStatus = 'required' | 'complete';

function onboardingUser(status: OnboardingStatus) {
  return {
    id: 91,
    telegram_user_id: 9001,
    username: 'new_user',
    first_name: 'Новый',
    is_coach: false,
    is_admin: false,
    has_active_program: false,
    has_workout_history: false,
    auth_providers: ['telegram'],
    onboarding: {
      status,
      required_fields: ['goal'],
      missing_fields: status === 'required' ? ['goal'] : [],
    },
    profile: {
      full_name: 'Новый пользователь',
      goal: status === 'complete' ? 'maintenance' : null,
      timezone: 'Europe/Moscow',
      kbju: null,
    },
    trainer: null,
  };
}

async function mockOnboardingApi(page: Page, initialStatus: OnboardingStatus = 'required') {
  let status = initialStatus;
  let savedProfileBody: unknown = null;

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: {
          app_env: 'dev',
          enable_dev_auth: true,
          enable_web_auth: true,
          enable_email_auth: false,
          telegram_bot_username: 'fit_bot',
          oauth_providers: [],
        },
      });
    }
    if (path.endsWith('/auth/refresh')) {
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    }
    if (path.endsWith('/auth/dev-login') || path.endsWith('/auth/telegram/init')) {
      return route.fulfill({ json: { access_token: 'onboarding-token' } });
    }
    if (path.endsWith('/me/profile') && request.method() === 'PATCH') {
      savedProfileBody = request.postDataJSON();
      status = 'complete';
      return route.fulfill({ json: onboardingUser(status) });
    }
    if (path.endsWith('/me')) return route.fulfill({ json: onboardingUser(status) });
    if (path.endsWith('/workouts/today')) {
      return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка не назначена' } });
    }
    return route.fulfill({ json: [] });
  });

  return { savedProfileBody: () => savedProfileBody };
}

test('новый Web-пользователь проходит короткий flow и продолжает с выбранного действия', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const events: unknown[] = [];
    Object.defineProperty(window, '__onboardingEvents', { value: events, writable: false });
    window.addEventListener('yfc:product-event', (event) => {
      events.push((event as CustomEvent).detail);
    });
  });
  const api = await mockOnboardingApi(page);

  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await expect(page).toHaveURL('/onboarding?next=%2Fapp');
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toBeVisible();
  await expect(page.getByText('Пол', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Возраст', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Рост, см', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Вес, кг', { exact: true })).toHaveCount(0);

  await page.getByLabel(/^Поддерживать форму/).check();
  await page.getByRole('button', { name: 'Продолжить' }).click();
  await expect(page.getByRole('heading', { name: 'С чего хотите начать?' })).toBeFocused();
  expect(api.savedProfileBody()).toEqual({ goal: 'maintenance' });

  await page.reload();
  await expect(page.getByRole('heading', { name: 'С чего хотите начать?' })).toBeVisible();
  await page.getByRole('button', { name: /Настроить питание/ }).click();
  await expect(page).toHaveURL('/app?section=nutrition');
  await expect(page.getByRole('heading', { name: 'КБЖУ' })).toBeVisible();

  const events = await page.evaluate(
    () => (window as typeof window & { __onboardingEvents: unknown[] }).__onboardingEvents ?? [],
  );
  expect(JSON.stringify(events)).not.toContain('maintenance');
  expect(events).toContainEqual({
    name: 'onboarding_next_action_selected',
    surface: 'web',
    next_action: 'nutrition',
  });
});

test('returning user skips onboarding, while the first-run layout stays responsive', async ({
  page,
}) => {
  await page.addInitScript(() => window.sessionStorage.setItem('fit_access_token', 'test-token'));
  await mockOnboardingApi(page, 'complete');
  await page.goto('/app');
  await expect(page).toHaveURL('/app');
  await expect(page.getByRole('heading', { name: 'Новый пользователь' })).toBeVisible();

  await page.unroute('**/api/v1/**');
  await mockOnboardingApi(page, 'required');
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 360, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/onboarding?next=%2Fapp');
    await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
    for (const goal of await page.locator('.onboarding-goal').all()) {
      const box = await goal.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width);
    }
  }
});

test('Telegram Mini App uses the same flow without browser theme or back controls', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const backButtonCalls = { hide: 0, show: 0 };
    Object.defineProperty(window, '__backButtonCalls', { value: backButtonCalls });
    Object.defineProperty(window, 'Telegram', {
      value: {
        WebApp: {
          initData: 'signed-test-data',
          initDataUnsafe: {},
          colorScheme: 'light',
          themeParams: {},
          BackButton: {
            hide: () => (backButtonCalls.hide += 1),
            show: () => (backButtonCalls.show += 1),
            onClick() {},
            offClick() {},
          },
          ready() {},
          expand() {},
          onEvent() {},
          offEvent() {},
          setHeaderColor() {},
          setBackgroundColor() {},
          setBottomBarColor() {},
        },
      },
    });
  });
  await mockOnboardingApi(page);

  await page.goto('/app?tgWebAppVersion=8.0');
  await expect(page).toHaveURL('/onboarding?next=%2Fapp');
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toBeVisible();
  await expect(page.getByRole('button', { name: /Включить .* тему/ })).toHaveCount(0);
  const backButtonCalls = await page.evaluate(
    () =>
      (window as typeof window & { __backButtonCalls: { hide: number; show: number } })
        .__backButtonCalls,
  );
  expect(backButtonCalls.hide).toBeGreaterThan(0);
  expect(backButtonCalls.show).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});
