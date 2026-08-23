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

const todayStates = [
  { name: 'planned', options: { workoutStatus: 'planned' as const }, action: 'Начать тренировку' },
  {
    name: 'in-progress',
    options: { workoutStatus: 'in_progress' as const },
    action: 'Продолжить тренировку',
  },
  {
    name: 'completed',
    options: { workoutStatus: 'completed' as const },
    action: 'Вернуться в Сегодня',
  },
  { name: 'rest', options: { workoutStatus: 'none' as const }, action: 'Добавить питание' },
  {
    name: 'no-program',
    options: { workoutStatus: 'none' as const, activeProgram: false },
    action: 'Подобрать программу',
  },
] as const;

test('TMA auth, shared UI, theme, viewport, safe areas and BackButton stay on one platform contract', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const tmaApi = await installPlatformApi(tmaPage);
  await installPlatformApi(mobilePage, { browserSession: true });

  await Promise.all([tmaPage.goto('/app'), mobilePage.goto('/app')]);
  await expect(tmaPage.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
  await expect(mobilePage.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
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
  await expectTouchTargets(tmaPage.locator('.week-strip__day--interactive'));
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

  const weekLink = tmaPage.getByRole('link', { name: /Открыть тренировку Контекст недели/ });
  await weekLink.focus();
  await expect(weekLink).toBeFocused();
  await weekLink.press('Enter');
  await expect(tmaPage).toHaveURL(/section=progress&workout_id=43/);
  await expect(
    tmaPage.locator('#workout-schedule-43').or(tmaPage.locator('#workout-history-43')),
  ).toBeVisible();
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(true);
  await tma.clickBack();
  await expect(tmaPage).toHaveURL('/app?section=progress');
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(false);
});

test('weekly review focus exposes a predictable TMA BackButton return path', async ({
  tma,
  tmaPage,
}) => {
  await installPlatformApi(tmaPage, {
    workoutStatus: 'none',
    weeklyReviewAvailable: true,
  });
  await tmaPage.goto('/app');

  await tmaPage.getByRole('link', { name: 'Пройти короткую проверку' }).click();
  await expect(tmaPage).toHaveURL('/app?section=progress&weekly_review=1');
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(true);

  await tma.clickBack();
  await expect(tmaPage).toHaveURL('/app');
  await expect(tmaPage.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(false);
});

for (const scenario of todayStates) {
  test(`Today ${scenario.name} keeps one primary action in Mobile Web and mocked TMA`, async ({
    mobilePage,
    tma,
    tmaPage,
  }) => {
    await installPlatformApi(tmaPage, scenario.options);
    await installPlatformApi(mobilePage, { ...scenario.options, browserSession: true });

    await Promise.all([tmaPage.goto('/app'), mobilePage.goto('/app')]);
    const tmaAction = tmaPage
      .getByRole('button', { name: scenario.action })
      .or(tmaPage.getByRole('link', { name: scenario.action }));
    const mobileAction = mobilePage
      .getByRole('button', { name: scenario.action })
      .or(mobilePage.getByRole('link', { name: scenario.action }));
    await expect(tmaAction).toBeVisible();
    await expect(mobileAction).toBeVisible();
    if (scenario.name === 'completed') {
      await expect(tmaPage.getByRole('region', { name: 'Эта неделя' })).not.toBeAttached();
      await expect(mobilePage.getByRole('region', { name: 'Эта неделя' })).not.toBeAttached();
    } else {
      await expect(tmaPage.getByRole('region', { name: 'Эта неделя' })).toBeVisible();
      await expect(mobilePage.getByRole('region', { name: 'Эта неделя' })).toBeVisible();
    }
    expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));
    await expectNoHorizontalOverflow(tmaPage);
    await expectNoHorizontalOverflow(mobilePage);
    await expectNoOverlap(tmaAction, tmaPage.locator('#appBottomNav'));

    const routeBeforeRuntimeEvents = tmaPage.url();
    await tma.setViewport(760, 844);
    await tma.setTheme('dark');
    await tma.setActive(false);
    await tma.setActive(true);
    await expect(tmaAction).toBeVisible();
    expect(tmaPage.url()).toBe(routeBeforeRuntimeEvents);
  });
}

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

test('completion summary survives finish retry, feedback error, reload and TMA lifecycle', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const api = await installPlatformApi(tmaPage, { workoutStatus: 'planned' });
  await tmaPage.goto('/app');
  await tmaPage.getByRole('button', { name: 'Начать тренировку' }).click();
  await tmaPage.getByRole('spinbutton', { name: 'Повторы, Приседания, подход 1' }).fill('8');
  await tmaPage.getByRole('spinbutton', { name: 'Вес, Приседания, подход 1' }).fill('40');
  await tmaPage.getByRole('button', { name: 'Завершить: Приседания, подход 1' }).click();
  await expect(tmaPage.getByText('Синхронизировано')).toBeVisible();
  await tmaPage.getByRole('button', { name: 'Завершить тренировку' }).click();

  await expect(tmaPage.getByRole('heading', { name: 'Тренировка завершена' })).toBeVisible();
  await expect(tmaPage.getByText('1 ч')).toBeVisible();
  await expect(tmaPage.getByText(/максимальный вес 40 кг/)).toBeVisible();
  await expect(tmaPage.getByText(/Следующая тренировка/)).toBeVisible();
  expect(api.finishCalls()).toBe(1);
  await expectNoHorizontalOverflow(tmaPage);
  const focusHeader = tmaPage.locator('.today-workout-focus__header');
  const backAction = focusHeader.getByRole('button', { name: 'К сводке' });
  const focusTitle = focusHeader.getByText('Итог тренировки');
  const [backBox, titleBox] = await Promise.all([
    backAction.boundingBox(),
    focusTitle.boundingBox(),
  ]);
  expect(backBox?.x ?? 0).toBeGreaterThanOrEqual(24);
  expect((titleBox?.x ?? 0) + (titleBox?.width ?? 0)).toBeLessThanOrEqual(
    (await tmaPage.evaluate(() => window.innerWidth)) - 24,
  );
  await expect(focusHeader).toHaveCSS('position', 'static');

  const resultsDisclosure = tmaPage.locator('.workout-completion__results');
  const resultsSummary = resultsDisclosure.locator('summary');
  const [resultsBox, resultsTextBox] = await Promise.all([
    resultsDisclosure.boundingBox(),
    resultsSummary.boundingBox(),
  ]);
  expect(resultsBox?.height ?? Infinity).toBeLessThanOrEqual(54);
  expect(
    Math.abs(
      (resultsTextBox?.x ?? 0) +
        (resultsTextBox?.width ?? 0) / 2 -
        ((resultsBox?.x ?? 0) + (resultsBox?.width ?? 0) / 2),
    ),
  ).toBeLessThanOrEqual(2);

  const feedbackLegend = tmaPage.locator('.workout-completion__feedback legend');
  const firstFeedback = tmaPage.getByRole('button', { name: 'Легче ожидаемого' });
  const [legendBox, firstFeedbackBox] = await Promise.all([
    feedbackLegend.boundingBox(),
    firstFeedback.boundingBox(),
  ]);
  expect(
    (firstFeedbackBox?.y ?? 0) - ((legendBox?.y ?? 0) + (legendBox?.height ?? 0)),
  ).toBeGreaterThanOrEqual(12);
  await expect(firstFeedback).toHaveCSS('border-radius', '12px');
  await expect(tmaPage.getByRole('button', { name: 'Вернуться в Сегодня' })).toHaveCSS(
    'border-radius',
    '12px',
  );

  const duplicateStatus = await tmaPage.evaluate(async () => {
    const response = await fetch('/api/v1/workouts/42/finish', { method: 'POST' });
    return response.status;
  });
  expect(duplicateStatus).toBe(200);
  expect(api.finishCalls()).toBe(2);
  await expect(tmaPage.getByRole('heading', { name: 'Тренировка завершена' })).toHaveCount(1);

  await tma.setSafeArea({ top: 28, right: 2, bottom: 22, left: 2 });
  await tma.setContentSafeArea({ top: 40, right: 0, bottom: 18, left: 0 });
  const note = tmaPage.getByRole('textbox', { name: 'Заметка' });
  await note.fill('Сохранить ровный темп');
  await tmaPage.getByRole('button', { name: 'Нормально' }).click();
  await note.focus();
  await tma.setViewport(560, MOBILE_CONTEXTS.baseline.height, false);
  await expect(tmaPage.locator('#appBottomNav')).toBeHidden();
  await tmaPage.getByRole('button', { name: 'Сохранить' }).scrollIntoViewIfNeeded();
  await expectNoHorizontalOverflow(tmaPage);

  api.setOffline(true);
  await tmaPage.getByRole('button', { name: 'Сохранить' }).click();
  await expect(tmaPage.getByRole('alert')).toContainText('Введённый текст сохранён в форме');
  await expect(note).toHaveValue('Сохранить ровный темп');
  api.setOffline(false);
  await tmaPage.getByRole('button', { name: 'Сохранить' }).click();
  await expect(tmaPage.getByText('Обратная связь сохранена')).toBeVisible();
  expect(api.completionFeedback()).toEqual({
    feedback: 'as_expected',
    note: 'Сохранить ровный темп',
  });

  await tma.setTheme('dark');
  await tma.setActive(false);
  await tma.setActive(true);
  await tma.setViewport(MOBILE_CONTEXTS.baseline.height, MOBILE_CONTEXTS.baseline.height);
  await tmaPage.reload();
  await expect(tmaPage.getByRole('heading', { name: 'Тренировка завершена' })).toBeVisible();
  await expect(tmaPage.getByRole('textbox', { name: 'Заметка' })).toHaveValue(
    'Сохранить ровный темп',
  );
  await expect(
    tmaPage.getByRole('spinbutton', { name: 'Повторы, Приседания, подход 1' }),
  ).not.toBeAttached();
  await expect.poll(async () => (await tma.state()).backButton.visible).toBe(false);
  for (const viewport of Object.values(MOBILE_CONTEXTS)) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(viewport.height, viewport.height);
    await expectNoHorizontalOverflow(tmaPage);
  }

  await mobilePage.goto('/');
  await expect(mobilePage.locator('.landing-button').first()).toHaveCSS('border-radius', '12px');
});

test('nutrition quick paths recover in TMA and match Mobile Web before core navigation', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const api = await installPlatformApi(tmaPage, { workoutStatus: 'in_progress' });
  await installPlatformApi(mobilePage, { workoutStatus: 'in_progress', browserSession: true });
  await Promise.all([
    tmaPage.goto('/app?section=nutrition'),
    mobilePage.goto('/app?section=nutrition'),
  ]);
  await expect(tmaPage.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();
  await expect(mobilePage.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();
  expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));
  for (const currentPage of [tmaPage, mobilePage]) {
    const week = currentPage.getByRole('navigation', { name: 'Неделя дневника' });
    await expect(week.locator('button[aria-current="date"]')).toBeVisible();
    await expect(week.locator('button[aria-pressed="true"]')).toBeVisible();
    await expect(currentPage.getByRole('navigation', { name: 'Дата дневника' })).not.toBeAttached();
    expect(
      await week.evaluate((element) => {
        const style = getComputedStyle(element);
        return [Number.parseFloat(style.paddingTop), Number.parseFloat(style.paddingBottom)];
      }),
    ).toEqual([0, 8]);
  }

  const breakfast = tmaPage.getByRole('region', { name: 'Завтрак' });
  await breakfast.getByRole('button', { name: /Добавить/ }).click();
  await expect(tmaPage.getByRole('button', { name: 'Добавить Овсяная каша' })).toBeVisible();
  await tmaPage.getByRole('button', { name: 'Избранное' }).click();
  await expect(tmaPage.getByRole('button', { name: 'Добавить Овсяная каша' })).toBeVisible();
  await tmaPage.getByRole('button', { name: '＋ Быстрый ввод' }).click();
  await tma.setSafeArea({ top: 20, right: 2, bottom: 24, left: 2 });
  await tma.setContentSafeArea({ top: 32, right: 0, bottom: 18, left: 0 });
  const calories = tmaPage.getByRole('spinbutton', { name: 'Калории' });
  await calories.fill('510');
  await tmaPage.getByRole('textbox', { name: 'Название (необязательно)' }).fill('TMA перекус');
  for (const viewport of [MOBILE_CONTEXTS.compact, MOBILE_CONTEXTS.baseline]) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(560, viewport.height, false);
    const lastAction = tmaPage.locator('.nutrition-picker__submit .ui-button').last();
    await lastAction.scrollIntoViewIfNeeded();
    const geometry = await tmaPage.locator('.nutrition-picker__submit').evaluate((submit) => {
      const action = submit.querySelector('.ui-button:last-child');
      if (!(action instanceof HTMLElement)) throw new Error('Quick Add action is missing');
      return {
        actionBottom: action.getBoundingClientRect().bottom,
        paddingBottom: Number.parseFloat(getComputedStyle(submit).paddingBottom),
        viewportHeight: window.innerHeight,
      };
    });
    expect(geometry.paddingBottom).toBeGreaterThanOrEqual(24);
    expect(geometry.actionBottom).toBeLessThanOrEqual(geometry.viewportHeight - 23);
    await expectNoHorizontalOverflow(tmaPage);
  }
  await expect(tmaPage.locator('html')).toHaveAttribute('data-yfc-keyboard', 'visible');
  await expect(tmaPage.locator('#appBottomNav')).toBeHidden();
  await tma.setTheme('dark');
  await tma.setActive(false);
  await tma.setActive(true);
  await expect(calories).toHaveValue('510');
  await expect(tmaPage.getByRole('dialog')).toBeVisible();

  api.setOffline(true);
  await tmaPage.getByRole('button', { name: 'Сохранить Quick Add' }).click();
  await expect(tmaPage.getByRole('alert')).toBeVisible();
  await expect(calories).toHaveValue('510');
  api.setOffline(false);
  await tmaPage.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(tmaPage.getByRole('dialog')).not.toBeAttached();
  await expect(tmaPage.getByText('TMA перекус')).toBeVisible();

  const entry = tmaPage.locator('.nutrition-entry').filter({ hasText: 'TMA перекус' });
  await entry.getByRole('button', { name: 'Повторить' }).click();
  await tmaPage.getByRole('dialog').getByRole('button', { name: 'Повторить продукт' }).click();
  await expect(tmaPage.getByText('Скопировано записей: 1')).toBeVisible();
  await expectNoHorizontalOverflow(tmaPage);

  await tmaPage.getByRole('link', { name: 'Прогресс', exact: true }).click();
  await expect(tmaPage).toHaveURL('/app?section=progress');
  await tmaPage.getByRole('button', { name: 'Ещё', exact: true }).click();
  await tmaPage
    .getByRole('dialog')
    .getByRole('link', { name: 'Профиль и настройки', exact: true })
    .click();
  await expect(tmaPage.getByRole('heading', { name: 'Профиль и настройки' })).toBeVisible();
  await tmaPage.getByRole('link', { name: 'Сегодня', exact: true }).click();
  await expect(tmaPage.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
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
  await expect(tmaPage.getByRole('heading', { name: /^Сегодня ·/ })).toBeVisible();
  await expect(tmaPage.getByRole('heading', { name: /База знаний/i })).not.toBeAttached();
});
