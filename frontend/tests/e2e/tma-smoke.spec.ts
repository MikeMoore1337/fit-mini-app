import {
  expect,
  expectNoHorizontalOverflow,
  expectNoOverlap,
  expectTouchTargets,
  MOBILE_CONTEXTS,
  setNetworkOffline,
  sharedSurfaceSignature,
  test,
} from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

test('TMA auth, shared UI, theme, viewport, safe areas and BackButton stay on one platform contract', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const tmaApi = await installPlatformApi(tmaPage);
  await installPlatformApi(mobilePage, { browserSession: true });

  await Promise.all([tmaPage.goto('/app'), mobilePage.goto('/app')]);
  await expect(tmaPage.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  await expect(mobilePage.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  expect(tmaApi.authInitCalls()).toBe(1);
  await expect(tmaPage.getByRole('heading', { name: 'Вход' })).not.toBeAttached();
  await expect(tmaPage.locator('body')).not.toContainText('query_id=test');
  await expect(tmaPage.locator('html')).toHaveAttribute('data-yfc-layout-surface', 'telegram');
  await expect(mobilePage.locator('html')).toHaveAttribute('data-yfc-layout-surface', 'browser');
  expect(await tmaPage.evaluate(() => matchMedia('(hover: none)').matches)).toBe(true);
  expect(await tmaPage.evaluate(() => navigator.maxTouchPoints)).toBeGreaterThan(0);
  expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));

  for (const viewport of Object.values(MOBILE_CONTEXTS)) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(viewport.height, viewport.height);
    await expectNoHorizontalOverflow(tmaPage);
  }
  await expectTouchTargets(
    tmaPage.locator('.app-bottom-nav__primary > a, .app-bottom-nav__primary > button'),
  );
  await expectNoOverlap(
    tmaPage.getByRole('button', { name: 'Начать тренировку' }),
    tmaPage.locator('#appBottomNav'),
  );

  await tma.setSafeArea({ top: 28, right: 2, bottom: 20, left: 2 });
  await tma.setContentSafeArea({ top: 44, right: 0, bottom: 16, left: 0 });
  await expect(tmaPage.locator('html')).toHaveCSS('--yfc-tg-safe-bottom', '20px');
  await expect(tmaPage.locator('html')).toHaveCSS('--yfc-tg-content-safe-top', '44px');

  const routeBeforeTheme = tmaPage.url();
  await tma.setTheme('dark');
  await expect(tmaPage.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  expect(tmaPage.url()).toBe(routeBeforeTheme);
  await tma.setTheme('light');
  await expect(tmaPage.locator('html')).toHaveAttribute('data-color-scheme', 'light');

  await tma.setActive(false);
  await expect(tmaPage.locator('html')).toHaveAttribute('data-yfc-viewport-active', 'false');
  await tma.setActive(true);
  await expect(tmaPage.locator('html')).toHaveAttribute('data-yfc-viewport-active', 'true');
  const lifecycleState = await tma.state();
  expect(lifecycleState.version).toBe('8.0');
  expect(lifecycleState.platform).toBe('android');
  expect(lifecycleState.ready).toBeGreaterThan(0);
  expect(lifecycleState.expand).toBeGreaterThan(0);
  expect(await tmaPage.evaluate(() => window.Telegram?.WebApp?.MainButton)).toBeUndefined();

  await tmaPage.goto('/app?workout_id=42&comment_id=7');
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(true);
  await tma.clickBack();
  await expect(tmaPage).toHaveURL('/app?section=progress');
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(false);
});

test('active workout starts, logs offline and resumes once after reconnect and reload', async ({
  tma,
  tmaPage,
}) => {
  const api = await installPlatformApi(tmaPage, { workoutStatus: 'planned' });
  await tmaPage.goto('/app');
  await tmaPage.getByRole('button', { name: 'Начать тренировку' }).click();
  await expect(
    tmaPage.getByRole('spinbutton', { name: 'Повторы, Приседания, подход 1' }),
  ).toBeVisible();

  api.setOffline(true);
  await setNetworkOffline(tmaPage, true);
  const reps = tmaPage.getByRole('spinbutton', { name: 'Повторы, Приседания, подход 1' });
  const weight = tmaPage.getByRole('spinbutton', { name: 'Вес, Приседания, подход 1' });
  await reps.fill('8');
  await weight.fill('40');
  await tma.setTheme('dark');
  await expect(reps).toHaveValue('8');
  await expect(weight).toHaveValue('40');
  await tmaPage.getByRole('button', { name: 'Завершить: Приседания, подход 1' }).click();
  await expect(tmaPage.getByText('Сохранено на устройстве')).toBeVisible();

  api.setOffline(false);
  await setNetworkOffline(tmaPage, false);
  await expect(tmaPage.getByText('Синхронизировано')).toBeVisible();
  expect(api.setPatchCalls()).toBe(1);
  expect(api.workoutValues()).toEqual({ actualReps: 8, actualWeight: 40, completed: true });

  await tmaPage.reload();
  await tmaPage.getByRole('button', { name: 'Продолжить тренировку' }).click();
  await expect(
    tmaPage.getByRole('spinbutton', { name: 'Повторы, Приседания, подход 1' }),
  ).toHaveValue('8');
  await expect(tmaPage.getByRole('spinbutton', { name: 'Вес, Приседания, подход 1' })).toHaveValue(
    '40',
  );
  await expectNoHorizontalOverflow(tmaPage);
});

test('nutrition keyboard draft and core Progress/Profile navigation survive platform events', async ({
  tma,
  tmaPage,
}) => {
  await installPlatformApi(tmaPage, { workoutStatus: 'in_progress' });
  await tmaPage.goto('/app');
  await tmaPage.getByRole('link', { name: 'Питание', exact: true }).click();
  await expect(tmaPage.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();

  const breakfast = tmaPage.getByRole('region', { name: 'Завтрак' });
  await breakfast.getByRole('button', { name: /Добавить/ }).click();
  const search = tmaPage.getByRole('searchbox', { name: 'Поиск по названию или бренду' });
  await search.fill('О');
  await tma.setViewport(560, 844, false);
  await expect(tmaPage.locator('html')).toHaveAttribute('data-yfc-keyboard', 'visible');
  await expect(tmaPage.locator('#appBottomNav')).toBeHidden();
  await tma.setTheme('dark');
  await tma.setActive(false);
  await tma.setActive(true);
  await expect(search).toHaveValue('О');
  await expect(tmaPage.getByRole('dialog')).toBeVisible();

  await tmaPage.getByRole('button', { name: 'Добавить Овсяная каша' }).click();
  await tmaPage.getByRole('button', { name: 'Добавить в дневник' }).click();
  await expect(tmaPage.getByText('Овсяная каша')).toBeVisible();

  await tmaPage.getByRole('link', { name: 'Прогресс', exact: true }).click();
  await expect(tmaPage).toHaveURL('/app?section=progress');
  await tmaPage.getByRole('button', { name: 'Ещё', exact: true }).click();
  await tmaPage
    .getByRole('dialog')
    .getByRole('link', { name: 'Профиль и настройки', exact: true })
    .click();
  await expect(tmaPage.getByRole('heading', { name: 'Профиль и настройки' })).toBeVisible();
  await tmaPage.getByRole('link', { name: 'Сегодня', exact: true }).click();
  await expect(tmaPage.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(tmaPage);
});

test('contextual help covers workout, nutrition and Progress without a TMA library', async ({
  tma,
  tmaPage,
}) => {
  await installPlatformApi(tmaPage, { workoutStatus: 'planned' });
  await tmaPage.goto('/app');

  await expect(tmaPage.getByRole('link', { name: 'База знаний' })).not.toBeAttached();
  await tmaPage.getByRole('button', { name: 'Начать тренировку' }).click();
  await tmaPage.getByText('Дополнительно', { exact: true }).first().click();
  const rirDetails = tmaPage.locator('.active-workout-rir .contextual-help');
  const rirHelp = rirDetails.getByText('Что это?', { exact: true });
  await rirHelp.click();
  await expect(
    tmaPage.locator('.active-workout-rir').getByRole('link', { name: /Подробнее на сайте/ }),
  ).toHaveAttribute('href', '/knowledge/training/repetitions-in-reserve');
  await tma.setTheme('dark');
  await expect(rirDetails).toHaveAttribute('open', '');
  await rirHelp.click();
  await expect(rirHelp).toBeFocused();
  await expect(rirDetails).not.toHaveAttribute('open', '');

  await tmaPage.getByRole('link', { name: 'Питание', exact: true }).click();
  await tmaPage.getByRole('heading', { name: 'КБЖУ', exact: true }).click();
  const nutritionHelp = tmaPage.locator('.contextual-help').getByText('Что это?', { exact: true });
  await nutritionHelp.click();
  await expect(
    tmaPage.locator('.contextual-help').getByRole('link', { name: /Подробнее на сайте/ }),
  ).toHaveAttribute('href', '/knowledge/nutrition/kbju-as-a-reference');

  await tmaPage.getByRole('link', { name: 'Прогресс', exact: true }).click();
  await tmaPage.locator('.progress-hero').getByText('Что это?', { exact: true }).click();
  await expect(
    tmaPage.locator('.progress-hero').getByRole('link', { name: /Подробнее на сайте/ }),
  ).toHaveAttribute('href', '/knowledge/progress/how-to-read-progress');
  await tma.setTheme('light');
  await expectNoHorizontalOverflow(tmaPage);

  await tmaPage.goto('/knowledge');
  await expect(tmaPage).toHaveURL('/app');
  await expect(tmaPage.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  await expect(tmaPage.getByRole('heading', { name: /База знаний/i })).not.toBeAttached();
});
