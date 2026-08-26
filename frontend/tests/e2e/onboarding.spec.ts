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
          status: 'unlogged',
          status_is_explicit: false,
        },
      });
    }
    if (path.endsWith('/workouts/progress/summary')) {
      return route.fulfill({
        json: {
          user_id: 91,
          period_days: 30,
          period_start: '2030-01-01',
          period_end: '2030-01-30',
          training: {
            planned_workouts: 0,
            completed_workouts: 0,
            frequency_per_week: 0,
            volume_kg: 0,
            new_personal_records: 0,
            last_completed_workout_on: null,
            next_workout: null,
          },
          nutrition: { visible: true },
          body: { latest_measurement: null, trends: [], priority: null, guidance: {} },
          adherence: {
            formula_version: 'adherence-v1',
            overall_percent: null,
            included_components: [],
            workouts: {},
            cardio: {},
            calories: {},
            protein: {},
          },
          data_sufficiency: {},
        },
      });
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
  const beforeReloadEvents = await page.evaluate(
    () => (window as typeof window & { __onboardingEvents: unknown[] }).__onboardingEvents ?? [],
  );

  await page.reload();
  await expect(page.getByRole('heading', { name: 'С чего хотите начать?' })).toBeVisible();
  await page.getByRole('button', { name: /Настроить питание/ }).click();
  await expect(page).toHaveURL('/app?section=nutrition');
  await expect(page.getByRole('heading', { name: 'КБЖУ' })).toBeVisible();

  const afterReloadEvents = await page.evaluate(
    () => (window as typeof window & { __onboardingEvents: unknown[] }).__onboardingEvents ?? [],
  );
  const events = [...beforeReloadEvents, ...afterReloadEvents];
  expect(JSON.stringify(events)).not.toContain('maintenance');
  expect(events).toContainEqual(
    expect.objectContaining({
      name: 'onboarding_next_action_selected',
      surface: 'mobile_web',
      next_action: 'nutrition',
    }),
  );
  const eventNames = events.map((event) => (event as { name?: string }).name);
  expect(eventNames).toEqual(
    expect.arrayContaining([
      'login_started',
      'login_completed',
      'onboarding_started',
      'onboarding_completed',
      'onboarding_next_action_selected',
    ]),
  );
  expect(eventNames.filter((name) => name === 'onboarding_started')).toHaveLength(1);
});

test('returning user skips onboarding, while the first-run layout stays responsive', async ({
  page,
}) => {
  await page.addInitScript(() => window.sessionStorage.setItem('fit_access_token', 'test-token'));
  await mockOnboardingApi(page, 'complete');
  await page.goto('/app');
  await expect(page).toHaveURL('/app');
  await expect(page.getByRole('heading', { level: 1, name: /^Сегодня ·/ })).toBeVisible();

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
