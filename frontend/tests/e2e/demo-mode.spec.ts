import type { Browser, Page } from '@playwright/test';
import type { DemoScenario, DemoSessionSnapshot } from '../../src/features/demo/demoApi';
import {
  expect,
  expectNoHorizontalOverflow,
  expectNoOverlap,
  expectTouchTargets,
  installTelegramHarness,
  MOBILE_CONTEXTS,
  TelegramHarness,
  setNetworkOffline,
  test,
} from './fixtures/mobile-tma';

const CAPTURE =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.YFC_CAPTURE_TASK_69 === '1';
const LIVE_DEMO =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.YFC_DEMO_LIVE === '1';
const SCREENSHOT_DIR = '../.artifacts/screenshots/task-69';

function demoFixture(scenario: DemoScenario): DemoSessionSnapshot {
  const base = {
    capability: 'demo' as const,
    scenario,
    fixture_version: 'demo-curated-v1' as const,
    revision: 1,
    expires_at: '2026-08-24T12:30:00Z',
  };
  if (scenario === 'nutrition') {
    return {
      ...base,
      state: {
        kind: 'nutrition',
        screen: 'diary',
        date_label: 'Сегодня · подготовленный дневник',
        item_added: false,
        recent_item: {
          name: 'Овсяная каша с бананом и греческим йогуртом',
          serving: '320 г · недавний продукт',
          calories: 428,
          protein_g: 24,
        },
        calories: 1160,
        calorie_target: 2150,
        protein_g: 82,
        protein_target_g: 145,
        meals_logged: 2,
      },
    };
  }
  if (scenario === 'trainer') {
    return {
      ...base,
      state: {
        kind: 'trainer',
        screen: 'client',
        client_name: 'Алексей Воронов — подготовленный демо-клиент',
        context_label: 'Последняя тренировка · сегодня, 18:40',
        workout_title: 'Ноги и корпус · неделя 4',
        facts: [
          { label: 'Выполнено', value: '6 из 6 упражнений' },
          { label: 'Объём', value: '6 840 кг' },
          { label: 'Самочувствие', value: '8 из 10' },
          { label: 'Следующий ориентир', value: '+2,5 кг в приседе' },
        ],
        comment: null,
      },
    };
  }
  return {
    ...base,
    state: {
      kind: 'self_training',
      screen: 'today',
      workout_title: 'Верх тела · уверенный старт',
      workout_subtitle: 'Подготовленная тренировка на сегодня',
      completed_sets: 2,
      total_sets: 3,
      exercises: [
        {
          name: 'Жим гантелей лёжа с контролируемой паузой',
          prescription: '3 × 10 · 18 кг · отдых 90 сек.',
          status: 'current',
        },
        {
          name: 'Тяга верхнего блока нейтральным хватом',
          prescription: '3 × 12 · 40 кг · отдых 75 сек.',
          status: 'next',
        },
      ],
      duration_minutes: 0,
      total_volume_kg: 0,
      progress_change_percent: 0,
    },
  };
}

function applyMockAction(snapshot: DemoSessionSnapshot, action: string, comment?: string) {
  const next = structuredClone(snapshot);
  next.revision += 1;
  if (next.state.kind === 'self_training') {
    if (action === 'start_workout') next.state.screen = 'active_workout';
    if (action === 'complete_set') next.state.completed_sets = next.state.total_sets;
    if (action === 'finish_workout') {
      next.state.screen = 'summary';
      next.state.duration_minutes = 46;
      next.state.total_volume_kg = 6840;
    }
    if (action === 'open_progress') {
      next.state.screen = 'progress';
      next.state.progress_change_percent = 6.5;
    }
  } else if (next.state.kind === 'nutrition') {
    if (action === 'add_recent' && !next.state.item_added) {
      next.state.item_added = true;
      next.state.calories += next.state.recent_item.calories;
      next.state.protein_g += next.state.recent_item.protein_g;
      next.state.meals_logged += 1;
    }
    if (action === 'open_nutrition_report') next.state.screen = 'report';
  } else if (action === 'save_comment') {
    next.state.comment = comment ?? 'Техника стабильна.';
  }
  return next;
}

async function installDemoApi(page: Page, forcedCurrentStatus?: 403 | 410) {
  const sessions = new Map<string, DemoSessionSnapshot>();
  let sequence = 0;
  let unavailable = false;
  await page.route('**/api/v1/demo/**', async (route) => {
    if (unavailable) {
      await route.abort('internetdisconnected');
      return;
    }
    const request = route.request();
    const url = new URL(request.url());
    const token = request.headers()['x-demo-session'];
    if (url.pathname.endsWith('/sessions') && request.method() === 'POST') {
      const body = request.postDataJSON() as { scenario: DemoScenario };
      const nextToken = `demo-token-${String(++sequence).padStart(32, '0')}`;
      const snapshot = demoFixture(body.scenario);
      sessions.set(nextToken, snapshot);
      await route.fulfill({ status: 201, json: { ...snapshot, session_token: nextToken } });
      return;
    }
    if (forcedCurrentStatus && request.method() === 'GET') {
      await route.fulfill({
        status: forcedCurrentStatus,
        json: {
          detail:
            forcedCurrentStatus === 410
              ? 'Демо-сессия истекла. Начните новый сценарий.'
              : 'Это действие недоступно в демо-режиме.',
        },
      });
      return;
    }
    const snapshot = token ? sessions.get(token) : undefined;
    if (!token || !snapshot) {
      await route.fulfill({ status: 410, json: { detail: 'Демо-сессия истекла.' } });
      return;
    }
    if (url.pathname.endsWith('/actions')) {
      const body = request.postDataJSON() as { action: string; comment?: string };
      const next = applyMockAction(snapshot, body.action, body.comment);
      sessions.set(token, next);
      await route.fulfill({ status: 200, json: next });
      return;
    }
    if (url.pathname.endsWith('/reset')) {
      const next = demoFixture(snapshot.scenario);
      sessions.set(token, next);
      await route.fulfill({ status: 200, json: next });
      return;
    }
    await route.fulfill({ status: 200, json: snapshot });
  });
  return {
    setUnavailable(value: boolean) {
      unavailable = value;
    },
  };
}

async function installAuthApi(page: Page) {
  let authenticated = false;
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.includes('/demo/')) return route.fallback();
    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: {
          app_env: 'prod',
          enable_dev_auth: false,
          enable_web_auth: true,
          enable_email_auth: false,
          telegram_bot_username: 'fitness_bot',
          oauth_providers: ['telegram', 'google', 'yandex', 'vk'],
        },
      });
    }
    if (path.endsWith('/auth/refresh')) {
      return route.fulfill({ status: 401, json: { detail: 'Сессия отсутствует' } });
    }
    if (path.endsWith('/auth/telegram/init')) {
      authenticated = true;
      return route.fulfill({ json: { access_token: 'telegram-demo-handoff-token' } });
    }
    if (path.endsWith('/me')) {
      return authenticated
        ? route.fulfill({
            json: {
              id: 69,
              is_coach: false,
              is_admin: false,
              is_root: false,
              has_active_program: false,
              has_workout_history: false,
              onboarding: {
                status: 'required',
                required_fields: ['goal'],
                missing_fields: ['goal'],
              },
              profile: null,
              trainer: null,
            },
          })
        : route.fulfill({ status: 401, json: { detail: 'Требуется вход' } });
    }
    return route.fallback();
  });
}

async function completeScenario(page: Page, scenario: DemoScenario) {
  if (scenario === 'self_training') {
    await page.getByRole('button', { name: 'Начать тренировку' }).click();
    await page.getByRole('button', { name: 'Завершить текущий подход' }).click();
    await page.getByRole('button', { name: 'Завершить тренировку' }).click();
    await expectMetricSpacing(page);
    if (CAPTURE && page.viewportSize()?.width === 360) {
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/mobile-web-360-training-summary-spacing.png`,
        fullPage: true,
      });
    }
    await page.getByRole('button', { name: 'Перейти к прогрессу' }).click();
  } else if (scenario === 'nutrition') {
    await expectMetricSpacing(page);
    await page.getByRole('button', { name: 'Добавить недавний продукт' }).click();
    await page.getByRole('button', { name: 'Открыть отчёт по питанию' }).click();
  } else {
    await page.getByRole('button', { name: 'Сохранить комментарий' }).click();
  }
  const authHandoff = page.getByRole('link', { name: 'Войти и начать настройку' });
  await expect(authHandoff).toBeVisible();
  await expect(authHandoff).toBeInViewport();

  const isTma = await page.evaluate(() => Boolean(window.Telegram?.WebApp?.initData?.trim()));
  if (CAPTURE && !isTma) {
    const width = page.viewportSize()?.width;
    const shouldCapture =
      (scenario === 'self_training' && width === 360) ||
      (scenario === 'nutrition' && width === 390) ||
      (scenario === 'trainer' && width === 390);
    if (shouldCapture) {
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/mobile-web-${width}-${scenario}-conversion-light.png`,
        fullPage: true,
      });
    }
  }
}

async function expectMetricSpacing(page: Page) {
  const metrics = page.locator('.demo-metrics');
  await expect(metrics.locator('.ui-metric')).toHaveCount(3);
  const gaps = await metrics.evaluate((element) => {
    const styles = getComputedStyle(element);
    return { column: Number.parseFloat(styles.columnGap), row: Number.parseFloat(styles.rowGap) };
  });
  expect(gaps.column).toBeGreaterThanOrEqual(8);
  expect(gaps.row).toBeGreaterThanOrEqual(8);
}

async function expectPrimaryContract(page: Page) {
  const primary = page.locator('.demo-stage .ui-button:not(.ui-button--secondary)').first();
  await expect(primary).toBeVisible();
  const contract = await primary.evaluate(() => {
    const sample = document.createElement('span');
    sample.style.backgroundColor = 'var(--v2-lime)';
    sample.style.borderRadius = 'var(--radius-action)';
    document.body.append(sample);
    const expected = getComputedStyle(sample);
    const result = {
      expectedBackground: expected.backgroundColor,
      expectedRadius: expected.borderRadius,
    };
    sample.remove();
    return result;
  });
  await expect(primary).toHaveCSS('background-color', contract.expectedBackground);
  await expect(primary).toHaveCSS('border-radius', contract.expectedRadius);
}

async function expectSelectionContract(page: Page) {
  const active = page.locator('.demo-scenario-nav button.is-active');
  const contract = await active.evaluate(() => {
    const sample = document.createElement('span');
    sample.style.backgroundColor = 'var(--v2-surface-secondary)';
    sample.style.borderLeftColor = 'var(--v2-lime)';
    sample.style.borderRadius = 'var(--v2-compact-radius)';
    document.body.append(sample);
    const expected = getComputedStyle(sample);
    const result = {
      background: expected.backgroundColor,
      boundary: expected.borderLeftColor,
      radius: expected.borderRadius,
    };
    sample.remove();
    return result;
  });
  await expect(active).toHaveCSS('background-color', contract.background);
  await expect(active).toHaveCSS('border-left-color', contract.boundary);
  await expect(active).toHaveCSS('border-radius', contract.radius);
}

async function openMobilePage(browser: Browser, scenario: DemoScenario, width: 360 | 390 | 430) {
  const viewport =
    width === 360
      ? MOBILE_CONTEXTS.compact
      : width === 390
        ? MOBILE_CONTEXTS.baseline
        : MOBILE_CONTEXTS.large;
  const context = await browser.newContext({
    viewport,
    hasTouch: true,
    isMobile: true,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  const api = LIVE_DEMO ? null : await installDemoApi(page);
  await page.goto(`/demo?scenario=${scenario}`);
  return { api, context, page };
}

test('three curated scenarios work at compact Mobile Web widths without visual forks', async ({
  browser,
}) => {
  for (const scenario of ['self_training', 'nutrition', 'trainer'] as const) {
    for (const width of [360, 390] as const) {
      const { context, page } = await openMobilePage(browser, scenario, width);
      await expect(page.getByText('Демо', { exact: true })).toBeVisible();
      const themeToggle = page.getByRole('button', { name: /Включить (тёмную|светлую) тему/ });
      await expect(themeToggle).toBeVisible();
      await expectTouchTargets(themeToggle);
      await expectNoHorizontalOverflow(page);
      await expectTouchTargets(page.locator('.demo-scenario-nav button'));
      await expectSelectionContract(page);
      if (width === 360 && scenario === 'self_training') {
        await themeToggle.click();
        await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
        await page.getByRole('button', { name: 'Включить светлую тему' }).click();
        await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'light');
        const activeButton = page.locator('.demo-scenario-nav button.is-active');
        const [buttonBox, labelBox] = await Promise.all([
          activeButton.boundingBox(),
          activeButton.locator('strong').boundingBox(),
        ]);
        expect(buttonBox).not.toBeNull();
        expect(labelBox).not.toBeNull();
        expect(labelBox!.x - buttonBox!.x).toBeGreaterThanOrEqual(8);
        expect(
          buttonBox!.x + buttonBox!.width - labelBox!.x - labelBox!.width,
        ).toBeGreaterThanOrEqual(8);
        await expect(page.getByRole('button', { name: 'Начать тренировку' })).toBeInViewport();
        if (CAPTURE) {
          await page.screenshot({
            path: `${SCREENSHOT_DIR}/mobile-web-360-training-entry-light.png`,
            fullPage: true,
          });
        }
      }
      await expectPrimaryContract(page);
      await completeScenario(page, scenario);
      await expectNoHorizontalOverflow(page);
      if (CAPTURE && scenario === 'self_training' && width === 360) {
        await page.screenshot({
          path: `${SCREENSHOT_DIR}/mobile-web-360-training-light.png`,
          fullPage: true,
        });
      }
      await context.close();
    }
  }

  const { context, page } = await openMobilePage(browser, 'nutrition', 430);
  await expectNoHorizontalOverflow(page);
  await expect(page.getByRole('button', { name: 'Добавить недавний продукт' })).toBeVisible();
  await context.close();
});

test('mocked Dark TMA keeps the same demo composition and never calls auth or linking', async ({
  browser,
}) => {
  for (const scenario of ['self_training', 'nutrition', 'trainer'] as const) {
    const context = await browser.newContext({
      viewport: MOBILE_CONTEXTS.baseline,
      hasTouch: true,
      isMobile: true,
      reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    const requestedPaths: string[] = [];
    page.on('request', (request) => requestedPaths.push(new URL(request.url()).pathname));
    await installTelegramHarness(page, { colorScheme: 'dark' });
    if (!LIVE_DEMO) await installDemoApi(page);
    await page.goto(`/demo?scenario=${scenario}&tgWebAppPlatform=android`);
    const tma = new TelegramHarness(page);

    await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
    await expect(page.getByText('Демо', { exact: true })).toBeVisible();
    await tma.setActive(false);
    await tma.setActive(true);
    await expect(page.getByText('Демо', { exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await expectSelectionContract(page);
    await completeScenario(page, scenario);
    expect(requestedPaths.some((path) => path.includes('/auth/'))).toBe(false);
    expect(requestedPaths.some((path) => path.includes('/notifications'))).toBe(false);
    expect(requestedPaths.some((path) => path.includes('/coach/invit'))).toBe(false);
    if (CAPTURE && scenario === 'trainer') {
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/tma-390-trainer-conversion-dark.png`,
        fullPage: true,
      });
    }
    await context.close();
  }
});

test('reset, reload, expired and forbidden states are predictable', async ({ browser }) => {
  const { api, context, page } = await openMobilePage(browser, 'nutrition', 390);
  await page.getByRole('button', { name: 'Добавить недавний продукт' }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Открыть отчёт по питанию' })).toBeVisible();
  await page.getByRole('button', { name: 'Сбросить' }).click();
  await expect(page.getByRole('button', { name: 'Добавить недавний продукт' })).toBeVisible();
  if (api) api.setUnavailable(true);
  else await setNetworkOffline(page, true);
  await page.getByRole('button', { name: 'Добавить недавний продукт' }).click();
  await expect(page.getByText(/Нет соединения с сервером/)).toBeVisible();
  if (api) api.setUnavailable(false);
  else await setNetworkOffline(page, false);
  await page.getByRole('button', { name: 'Повторить' }).click();
  await expect(page.getByRole('button', { name: 'Добавить недавний продукт' })).toBeVisible();
  await context.close();

  if (LIVE_DEMO) return;

  for (const status of [410, 403] as const) {
    const stateContext = await browser.newContext({ viewport: MOBILE_CONTEXTS.baseline });
    const statePage = await stateContext.newPage();
    await statePage.addInitScript(() => {
      sessionStorage.setItem(
        'fit_demo_sessions_v1',
        JSON.stringify({ self_training: 'forced-demo-token-000000000000000000000000' }),
      );
    });
    await installDemoApi(statePage, status);
    await statePage.goto('/demo');
    await expect(
      statePage.getByText(status === 410 ? /Демо-сессия истекла/ : /действие недоступно/),
    ).toBeVisible();
    if (CAPTURE) {
      await statePage.screenshot({
        path: `${SCREENSHOT_DIR}/${status === 410 ? 'expired' : 'forbidden'}-390.png`,
        fullPage: true,
      });
    }
    await stateContext.close();
  }
});

test('desktop keeps the canonical content width and separated adjacent regions', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  if (!LIVE_DEMO) await installDemoApi(page);
  await page.goto('/demo?scenario=self_training');
  await expect(page.getByText('Демо', { exact: true })).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'К демо-сценарию' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#demoContent')).toBeFocused();

  const geometry = await page.evaluate(() => {
    const main = document.querySelector<HTMLElement>('.demo-main')!.getBoundingClientRect();
    const boundary = document.querySelector<HTMLElement>('.demo-boundary')!.getBoundingClientRect();
    const stage = document.querySelector<HTMLElement>('.demo-stage')!.getBoundingClientRect();
    return {
      mainWidth: main.width,
      boundaryRight: boundary.right,
      stageLeft: stage.left,
      stageRight: stage.right,
      viewportWidth: document.documentElement.clientWidth,
    };
  });
  expect(geometry.mainWidth).toBeLessThanOrEqual(980);
  expect(geometry.boundaryRight).toBeLessThan(geometry.stageLeft);
  expect(geometry.stageRight).toBeLessThanOrEqual(geometry.viewportWidth);
  if (CAPTURE) {
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/desktop-1280-training-light.png`,
      fullPage: true,
    });
  }

  await page.getByRole('button', { name: 'Начать тренировку' }).click();
  await page.getByRole('button', { name: 'Завершить текущий подход' }).click();
  await page.getByRole('button', { name: 'Завершить тренировку' }).click();
  await expectMetricSpacing(page);
  await page.getByRole('button', { name: 'Перейти к прогрессу' }).click();
  if (CAPTURE) {
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/desktop-1280-training-conversion-light.png`,
      fullPage: true,
    });
  }

  await page.setViewportSize({ width: 768, height: 900 });
  await expectNoHorizontalOverflow(page);
  await expectNoOverlap(page.locator('.demo-stage'), page.locator('.demo-boundary'));
});

test('Landing entry, deep-link scenario history and browser auth return stay explicit', async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: MOBILE_CONTEXTS.baseline,
    hasTouch: true,
    isMobile: true,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  await installAuthApi(page);
  await installDemoApi(page);

  await page.goto('/');
  await page.getByRole('link', { name: /Попробовать демо/ }).click();
  await expect(page).toHaveURL(/\/demo$/);
  await page.getByRole('button', { name: 'Начать тренировку' }).click();
  await page.getByRole('button', { name: 'Завершить текущий подход' }).click();
  await page.getByRole('button', { name: 'Завершить тренировку' }).click();
  await page.getByRole('button', { name: 'Перейти к прогрессу' }).click();
  const demoTokenBeforeHandoff = await page.evaluate(() =>
    sessionStorage.getItem('fit_demo_sessions_v1'),
  );
  expect(demoTokenBeforeHandoff).not.toBeNull();

  await page.getByRole('link', { name: 'Войти и начать настройку' }).click();
  await expect(page).toHaveURL(/\/login\?next=%2Fapp&from=demo&scenario=self_training$/);
  await expect(page.getByText('После демо — чистый профиль')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Продолжить с Google' })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem('fit_demo_sessions_v1'))).toBeNull();
  if (CAPTURE) {
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/mobile-web-390-auth-handoff-light.png`,
      fullPage: true,
    });
  }

  await page.getByRole('link', { name: 'Вернуться в демо' }).click();
  await expect(page).toHaveURL(/\/demo\?scenario=self_training$/);
  await expect(page.getByRole('button', { name: 'Начать тренировку' })).toBeVisible();
  const demoTokenAfterReturn = await page.evaluate(() =>
    sessionStorage.getItem('fit_demo_sessions_v1'),
  );
  expect(demoTokenAfterReturn).not.toBe(demoTokenBeforeHandoff);

  await page.getByRole('button', { name: /Питание/ }).click();
  await expect(page).toHaveURL(/scenario=nutrition$/);
  await page.getByRole('button', { name: /Тренеру/ }).click();
  await expect(page).toHaveURL(/scenario=trainer$/);
  await page.goBack();
  await expect(page).toHaveURL(/scenario=nutrition$/);
  await context.close();
});

test('mocked TMA auth handoff clears demo state and starts clean onboarding', async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: MOBILE_CONTEXTS.baseline,
    hasTouch: true,
    isMobile: true,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  await installTelegramHarness(page, { colorScheme: 'dark' });
  await installAuthApi(page);
  await installDemoApi(page);
  await page.goto('/demo?scenario=nutrition&tgWebAppPlatform=android');
  await completeScenario(page, 'nutrition');

  await page.getByRole('link', { name: 'Войти и начать настройку' }).click();
  await expect(page).toHaveURL(/\/onboarding\?next=%2Fapp$/);
  await expect(page.getByRole('heading', { name: 'Какая у вас главная цель?' })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem('fit_demo_sessions_v1'))).toBeNull();
  await context.close();
});
