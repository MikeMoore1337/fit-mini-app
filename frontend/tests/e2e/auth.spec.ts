import { expect, test, type Page } from '@playwright/test';

const configuredProviders = ['telegram', 'google', 'yandex', 'vk'];

function userPayload() {
  return {
    id: 17,
    telegram_user_id: 7017,
    username: 'browser_user',
    first_name: 'Браузер',
    is_coach: false,
    is_admin: false,
    has_active_program: false,
    has_workout_history: false,
    auth_providers: ['telegram', 'google'],
    profile: { full_name: 'Тестовый пользователь', timezone: 'Europe/Moscow', kbju: null },
    trainer: null,
  };
}

async function mockAuthApi(
  page: Page,
  { authenticated = false, providers = configuredProviders } = {},
) {
  let hasSession = authenticated;
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: {
          app_env: 'prod',
          enable_dev_auth: false,
          enable_web_auth: providers.length > 0,
          enable_email_auth: false,
          telegram_bot_username: 'fitness_bot',
          oauth_providers: providers,
        },
      });
    }
    if (path.endsWith('/auth/refresh')) {
      return hasSession
        ? route.fulfill({ json: { access_token: 'refreshed-token' } })
        : route.fulfill({ status: 401, json: { detail: 'Сессия отсутствует' } });
    }
    if (path.endsWith('/auth/telegram/init')) {
      hasSession = true;
      return route.fulfill({ json: { access_token: 'telegram-token' } });
    }
    if (path.endsWith('/me')) {
      return hasSession
        ? route.fulfill({ json: userPayload() })
        : route.fulfill({ status: 401, json: { detail: 'Требуется вход' } });
    }
    if (path.endsWith('/workouts/today')) {
      return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка не назначена' } });
    }
    if (path.endsWith('/workouts/progress/summary')) {
      return route.fulfill({
        json: {
          user_id: 17,
          period_days: 30,
          period_start: '2026-07-22',
          period_end: '2026-08-20',
          training: { last_completed_workout_on: null, next_workout: null },
          nutrition: { visible: false },
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
    if (path.endsWith('/nutrition/diary')) {
      return route.fulfill({
        json: {
          diary_date: '2026-08-20',
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
    if (
      path.endsWith('/workouts/schedule') ||
      path.endsWith('/workouts/history') ||
      path.endsWith('/workouts/week')
    ) {
      return route.fulfill({ json: [] });
    }
    if (path.endsWith('/workouts/history/summary')) {
      return route.fulfill({ json: { workouts_completed: 0, completed_sets: 0, volume_kg: 0 } });
    }
    if (path.endsWith('/me/coach-application')) return route.fulfill({ json: null });
    return route.fulfill({ json: [] });
  });
}

test('Landing ведёт на canonical Login, а protected route сохраняет safe next', async ({
  page,
}) => {
  await mockAuthApi(page);
  await page.goto('/');
  await page.getByRole('link', { name: 'Войти' }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.locator('#login-title .login-title--desktop')).toBeVisible();
  await expect(page.locator('#login-title')).toContainText('Вернитесь к своему плану.');

  await page.goto('/coach');
  await expect(page).toHaveURL(/\/login\?next=%2Fcoach$/);
  await expect(page.getByRole('link', { name: 'Продолжить с Google' })).toHaveAttribute(
    'href',
    '/api/v1/auth/oauth/google/start?next=%2Fcoach',
  );
});

test('Login использует surface-aware logo и не дублирует Войти в mobile header', async ({
  page,
}) => {
  await mockAuthApi(page);
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/login');

  await expect(page.locator('.login-continuation-brand .yfc-lockup__mark')).toHaveAttribute(
    'src',
    '/assets/brand/yfc-mark-dark.svg',
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('link', { name: 'Войти', exact: true })).toHaveCount(0);
  await expect(page.locator('.public-shell__header .yfc-lockup__wordmark')).toBeVisible();
  await expect(page.locator('.public-shell__header .yfc-lockup__wordmark')).toContainText(
    'Your FitnessCoach',
  );
});

test('Login показывает только configured providers и контролируемую OAuth ошибку', async ({
  page,
}) => {
  await mockAuthApi(page, { providers: ['google', 'vk'] });
  await page.goto('/login?next=%2Fadmin&auth_error=denied&code=secret-code');

  await expect(page.getByText('Вход отменён')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Продолжить с Google' })).toHaveAttribute(
    'href',
    '/api/v1/auth/oauth/google/start?next=%2Fadmin',
  );
  await expect(page.getByRole('link', { name: 'Войти с VK ID' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Войти через Telegram' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Войти с Яндекс ID' })).toHaveCount(0);
  await expect(page.getByText('secret-code')).toHaveCount(0);
});

test('Telegram fallback сохраняет контраст, когда browser providers недоступны', async ({
  page,
}) => {
  await mockAuthApi(page, { providers: [] });
  await page.goto('/login');

  const fallback = page.getByRole('link', { name: 'Открыть в Telegram' });
  await expect(fallback).toBeVisible();
  await expect(fallback).toHaveCSS('min-height', '48px');
  await expect(fallback).toHaveCSS('background-color', 'rgb(236, 237, 233)');
  await expect(fallback).toHaveCSS('color', 'rgb(22, 26, 23)');
});

test('Повторить сохраняет контраст и единый hover с provider-кнопками', async ({ page }) => {
  await mockAuthApi(page, { providers: ['google'] });

  for (const scheme of ['light', 'dark'] as const) {
    await page.emulateMedia({ colorScheme: scheme, reducedMotion: 'reduce' });
    await page.goto('/login?auth_error=provider_failure');

    const retry = page.getByRole('button', { name: 'Повторить' });
    const provider = page.getByRole('link', { name: 'Продолжить с Google' });
    await retry.hover();
    const retryStyles = await retry.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        backgroundColor: styles.backgroundColor,
        borderColor: styles.borderColor,
        color: styles.color,
        transform: styles.transform,
      };
    });
    await provider.hover();
    const providerStyles = await provider.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        backgroundColor: styles.backgroundColor,
        borderColor: styles.borderColor,
        color: styles.color,
        transform: styles.transform,
      };
    });

    expect(retryStyles).toEqual(providerStyles);
    expect(retryStyles.backgroundColor).toBe(
      scheme === 'light' ? 'rgb(236, 237, 233)' : 'rgb(30, 34, 30)',
    );
    expect(retryStyles.color).toBe(scheme === 'light' ? 'rgb(22, 26, 23)' : 'rgb(238, 240, 234)');
  }
});

test('already authenticated Login возвращает в safe destination', async ({ page }) => {
  await mockAuthApi(page, { authenticated: true });
  await page.goto('/login?next=%2Fapp');

  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
});

test('valid Telegram launch authenticates automatically without browser Login', async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.Telegram = {
      WebApp: {
        initData: 'signed-init-data',
        initDataUnsafe: {},
        colorScheme: 'dark',
        ready() {},
        expand() {},
        BackButton: {
          show() {},
          hide() {},
          onClick() {},
          offClick() {},
        },
      },
    };
  });
  await mockAuthApi(page);
  await page.goto('/app?tgWebAppPlatform=android');

  await expect(page).toHaveURL(/\/app\?tgWebAppPlatform=android$/);
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Продолжить в Your Fitness Coach' })).toHaveCount(
    0,
  );
});

test('linking callback показывает success и conflict без raw данных', async ({ page }) => {
  await mockAuthApi(page, { authenticated: true });
  await page.goto('/app?auth_linked=google');
  await expect(page.getByRole('status')).toContainText('Google привязан к аккаунту');

  await page.goto('/app?auth_error=conflict&identity=provider-secret');
  await expect(page.getByRole('alert')).toContainText(
    'Этот способ входа уже привязан к другому аккаунту',
  );
  await expect(page.getByText('provider-secret')).toHaveCount(0);
});

test('Login адаптивен, доступен с клавиатуры и уважает reduced motion', async ({ browser }) => {
  for (const width of [1440, 1280, 768, 390, 360]) {
    const context = await browser.newContext({
      viewport: { width, height: width < 768 ? 844 : 900 },
      reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    try {
      await mockAuthApi(page);
      await page.goto('/login?next=%2Fapp');
      const title = page.locator('#login-title');
      await expect(title).toBeVisible();
      await expect(
        title.locator(width >= 1024 ? '.login-title--desktop' : '.login-title--mobile'),
      ).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);

      const themeControl = page.getByRole('button', { name: /Включить .* тему/ });
      await expect(themeControl).toBeHidden();
      await expect(page.getByRole('combobox')).toHaveCount(0);

      const google = page.getByRole('link', { name: 'Продолжить с Google' });
      await expect(google).toHaveCSS('border-radius', '12px');
      const googleBox = await google.boundingBox();
      expect(googleBox).not.toBeNull();

      if (width >= 1024) {
        const [layoutBox, introBox, cardBox, titleStyles] = await Promise.all([
          page.locator('.login-layout').boundingBox(),
          page.locator('.login-intro').boundingBox(),
          page.locator('.login-card').boundingBox(),
          title.evaluate((element) => {
            const styles = getComputedStyle(element);
            return { fontSize: styles.fontSize, whiteSpace: styles.whiteSpace };
          }),
        ]);
        expect(layoutBox).not.toBeNull();
        expect(introBox).not.toBeNull();
        expect(cardBox).not.toBeNull();
        expect(introBox!.width / cardBox!.width).toBeCloseTo(1.04 / 0.96, 2);
        expect(introBox!.width + cardBox!.width).toBeCloseTo(layoutBox!.width, 0);
        expect(titleStyles).toEqual({ fontSize: '35px', whiteSpace: 'nowrap' });
        expect(googleBox!.width).toBeCloseTo(240, 0);
      } else {
        await expect(page.locator('.login-title--desktop')).toBeHidden();
        await expect(page.locator('.login-title--mobile')).toBeVisible();
        expect(googleBox!.height).toBeGreaterThanOrEqual(48);
      }

      await google.focus();
      await expect(google).toBeFocused();
      const transitionDuration = await google.evaluate((element) =>
        Number.parseFloat(getComputedStyle(element).transitionDuration),
      );
      expect(transitionDuration).toBeLessThanOrEqual(0.001);
    } finally {
      await context.close();
    }
  }
});
