import { expect, test, type Page } from '@playwright/test';

type OnboardingStatus = 'required' | 'complete';

const captureTask117Proofs =
  (
    globalThis as typeof globalThis & {
      process?: { env?: Record<string, string | undefined> };
    }
  ).process?.env?.YFC_CAPTURE_TASK_117_PROOFS === '1';

async function installTelegramLaunch(page: Page, colorScheme: 'light' | 'dark' = 'dark') {
  await page.addInitScript((theme) => {
    Object.defineProperty(window, 'Telegram', {
      value: {
        WebApp: {
          initData: 'signed-test-data',
          initDataUnsafe: {},
          colorScheme: theme,
          themeParams: {},
          BackButton: { hide() {}, show() {}, onClick() {}, offClick() {} },
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
  }, colorScheme);
}

function onboardingUser(status: OnboardingStatus, profile: 'missing' | 'partial' | 'complete') {
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
    profile:
      profile === 'missing'
        ? null
        : {
            full_name: 'Новый пользователь',
            goal: profile === 'complete' ? 'maintenance' : null,
            level: profile === 'complete' ? 'beginner' : null,
            height_cm: profile === 'complete' ? 178 : null,
            workouts_per_week: profile === 'complete' ? 3 : null,
            timezone: 'Europe/Moscow',
            kbju: null,
          },
    trainer: null,
  };
}

async function mockFirstRunApi(
  page: Page,
  status: OnboardingStatus = 'required',
  profile: 'missing' | 'partial' | 'complete' = 'missing',
) {
  const user = onboardingUser(status, profile);

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
      return route.fulfill({ json: { access_token: 'first-run-token' } });
    }
    if (path.endsWith('/auth/logout')) return route.fulfill({ status: 204, body: '' });
    if (path.endsWith('/me')) return route.fulfill({ json: user });
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
    if (path.endsWith('/workouts/progress')) {
      return route.fulfill({
        json: {
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
        },
      });
    }
    if (path.endsWith('/workouts/history/summary')) {
      return route.fulfill({ json: { workouts_completed: 0, completed_sets: 0, volume_kg: 0 } });
    }
    if (
      path.endsWith('/workouts/schedule') ||
      path.endsWith('/workouts/history') ||
      path.endsWith('/workouts/week')
    ) {
      return route.fulfill({ json: [] });
    }
    return route.fulfill({ json: [] });
  });
}

test('brand-new Web user enters Today without a mandatory profile step', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockFirstRunApi(page, 'required', 'missing');

  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await expect(page).toHaveURL('/app');
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  await expect(page.getByRole('heading', { level: 1, name: /^Сегодня ·/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toHaveCount(0);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Создать свою программу' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Выбрать готовую' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Заполнить профиль' })).toBeVisible();

  await page.getByRole('link', { name: 'Создать свою программу' }).click();
  await expect(page).toHaveURL('/app?section=programs&start=create');
  const builder = page.locator('#program-builder');
  await expect(builder).toHaveAttribute('open', '');
  await expect(builder.locator(':scope > summary')).toBeFocused();
  await expect(page.getByRole('textbox', { name: 'Название', exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Сегодня', exact: true }).click();
  await page.getByRole('link', { name: 'Выбрать готовую' }).click();
  await expect(page).toHaveURL('/app?section=programs&start=templates');
  const library = page.locator('#program-library');
  await expect(library).toHaveAttribute('open', '');
  await expect(library.locator(':scope > summary')).toBeFocused();
  await expect(page.getByText('Программ пока нет')).toBeVisible();
});

test('returning and legacy required users keep requested core routes without redirect loops', async ({
  page,
}) => {
  await page.addInitScript(() => window.sessionStorage.setItem('fit_access_token', 'test-token'));
  await mockFirstRunApi(page, 'complete', 'complete');
  await page.goto('/app?section=nutrition');
  await expect(page).toHaveURL('/app?section=nutrition');
  await expect(page.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();

  await page.unroute('**/api/v1/**');
  await mockFirstRunApi(page, 'required', 'partial');
  await page.goto('/app?section=progress');
  await expect(page).toHaveURL('/app?section=progress');
  await expect(page.getByRole('heading', { name: 'Прогресс', exact: true })).toBeVisible();

  await page.goto('/app?section=nutrition');
  await expect(page).toHaveURL('/app?section=nutrition');
  await expect(page.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
  await expect(page).toHaveURL(/\/login\?next=%2Fapp/);
  await page.getByRole('button', { name: 'Клиент' }).click();
  await expect(page).toHaveURL('/app');
  await expect(page.getByRole('heading', { level: 1, name: /^Сегодня ·/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toHaveCount(0);
});

test('first-run shell stays usable across required responsive surfaces', async ({ browser }) => {
  const cases = [
    { name: 'mobile-web-360x800-light.png', width: 360, height: 800, theme: 'light', tma: false },
    { name: 'mobile-web-390x844-light.png', width: 390, height: 844, theme: 'light', tma: false },
    { name: 'mobile-web-430x932-light.png', width: 430, height: 932, theme: 'light', tma: false },
    { name: 'tablet-web-768x900-light.png', width: 768, height: 900, theme: 'light', tma: false },
    {
      name: 'desktop-web-1440x900-light.png',
      width: 1440,
      height: 900,
      theme: 'light',
      tma: false,
    },
    { name: 'mock-tma-390x844-dark.png', width: 390, height: 844, theme: 'dark', tma: true },
  ] as const;

  for (const current of cases) {
    const context = await browser.newContext({
      viewport: { width: current.width, height: current.height },
      hasTouch: current.width <= 768,
      isMobile: current.width <= 430,
      reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    if (current.tma) await installTelegramLaunch(page, current.theme);
    else {
      await page.addInitScript((theme) => {
        sessionStorage.setItem('fit_access_token', 'first-run-token');
        localStorage.setItem('app-theme', theme);
      }, current.theme);
    }
    await mockFirstRunApi(page, 'required', 'missing');
    await page.goto(current.tma ? '/app?tgWebAppVersion=8.0' : '/app');

    await expect(page.getByRole('heading', { level: 1, name: /^Сегодня ·/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toHaveCount(0);
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(current.width);
    for (const action of ['Создать свою программу', 'Выбрать готовую', 'Заполнить профиль']) {
      const box = await page.getByRole('link', { name: action }).boundingBox();
      expect(box).not.toBeNull();
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }

    if (captureTask117Proofs) {
      await page.screenshot({
        path: `../.artifacts/screenshots/task-117/${current.name}`,
        fullPage: true,
      });
    }
    await context.close();
  }
});

test('Telegram Mini App uses the same first-run shell for a legacy required user', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installTelegramLaunch(page);
  await mockFirstRunApi(page, 'required', 'missing');

  await page.goto('/app?tgWebAppVersion=8.0');
  await expect(page).toHaveURL('/app?tgWebAppVersion=8.0');
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  await expect(page.getByRole('heading', { level: 1, name: /^Сегодня ·/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Включить .* тему/ })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Создать свою программу' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Выбрать готовую' })).toBeVisible();
});
