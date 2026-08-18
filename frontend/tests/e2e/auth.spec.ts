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
  await expect(page.getByRole('heading', { name: 'Войти в Your Fitness Coach' })).toBeVisible();

  await page.goto('/coach');
  await expect(page).toHaveURL(/\/login\?next=%2Fcoach$/);
  await expect(page.getByRole('link', { name: 'Продолжить с Google' })).toHaveAttribute(
    'href',
    '/api/v1/auth/oauth/google/start?next=%2Fcoach',
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
          setText() {},
          enable() {},
          disable() {},
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
  await expect(page.getByRole('heading', { name: 'Войти в Your Fitness Coach' })).toHaveCount(0);
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
      await expect(page.getByRole('heading', { name: 'Войти в Your Fitness Coach' })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);

      const themeControl = page.getByRole('button', { name: /Включить .* тему/ });
      const themeIcon = themeControl.locator('.app-theme-toggle__icon');
      const [controlBox, iconBox] = await Promise.all([
        themeControl.boundingBox(),
        themeIcon.boundingBox(),
      ]);
      expect(controlBox?.height).toBe(44);
      expect(controlBox?.width).toBe(44);
      expect(iconBox).not.toBeNull();
      expect(
        Math.abs(iconBox!.x + iconBox!.width / 2 - (controlBox!.x + controlBox!.width / 2)),
      ).toBeLessThan(1);
      expect(
        Math.abs(iconBox!.y + iconBox!.height / 2 - (controlBox!.y + controlBox!.height / 2)),
      ).toBeLessThan(1);
      const themeStyles = await themeControl.evaluate((element) => {
        const styles = getComputedStyle(element);
        return {
          backgroundColor: styles.backgroundColor,
          borderTopWidth: styles.borderTopWidth,
          cursor: styles.cursor,
        };
      });
      expect(themeStyles.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
      expect(themeStyles.borderTopWidth).toBe('1px');
      expect(themeStyles.cursor).toBe('pointer');

      await themeControl.hover();
      const themeHoverStyles = await themeControl.evaluate((element) => {
        const styles = getComputedStyle(element);
        return {
          backgroundColor: styles.backgroundColor,
          borderColor: styles.borderColor,
          boxShadow: styles.boxShadow,
          transform: styles.transform,
        };
      });
      const homeLink = page.getByRole('link', { name: 'На главную', exact: true });
      await homeLink.hover();
      const homeHoverStyles = await homeLink.evaluate((element) => {
        const styles = getComputedStyle(element);
        return {
          backgroundColor: styles.backgroundColor,
          borderColor: styles.borderColor,
          boxShadow: styles.boxShadow,
          transform: styles.transform,
        };
      });
      expect(homeHoverStyles).toEqual(themeHoverStyles);

      await themeControl.click();
      expect(await themeControl.evaluate((element) => element.matches(':focus-visible'))).toBe(
        false,
      );
      await expect(page.getByRole('combobox')).toHaveCount(0);

      const google = page.getByRole('link', { name: 'Продолжить с Google' });
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
