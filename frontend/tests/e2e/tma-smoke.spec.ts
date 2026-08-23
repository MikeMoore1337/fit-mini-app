import {
  expect,
  expectNoHorizontalOverflow,
  expectNoOverlap,
  expectTouchTargets,
  installTelegramHarness,
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

test('nutrition report keeps period analytics and diary return aligned in Mobile Web and TMA', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const tmaApi = await installPlatformApi(tmaPage);
  const mobileApi = await installPlatformApi(mobilePage, { browserSession: true });
  await Promise.all([
    tmaPage.goto('/app?section=progress&nutrition_period=days_7'),
    mobilePage.goto('/app?section=progress&nutrition_period=days_7'),
  ]);

  for (const currentPage of [tmaPage, mobilePage]) {
    const report = currentPage.locator('#nutrition-period-report');
    await expect(report.getByRole('heading', { name: 'Отчёт по питанию' })).toBeVisible();
    await expect(report.getByText('Заполнено 3 из 7 дней')).toBeVisible();
    await expect(report.getByText('Изменения цели в периоде')).toBeVisible();
    await expect(report.getByRole('table')).toBeVisible();
  }
  expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));

  const tmaReport = tmaPage.locator('#nutrition-period-report');
  const tmaSelector = tmaReport.getByRole('tablist', { name: 'Период отчёта по питанию' });
  const mobileSelector = mobilePage
    .locator('#nutrition-period-report')
    .getByRole('tablist', { name: 'Период отчёта по питанию' });
  for (const period of ['30 дней', '90 дней', '7 дней']) {
    await Promise.all([
      tmaSelector.getByRole('tab', { name: period }).click(),
      mobileSelector.getByRole('tab', { name: period }).click(),
    ]);
  }
  await expect
    .poll(() => tmaApi.nutritionReportPeriods())
    .toEqual(expect.arrayContaining(['days_7', 'days_30', 'days_90']));
  await expect
    .poll(() => mobileApi.nutritionReportPeriods())
    .toEqual(expect.arrayContaining(['days_7', 'days_30', 'days_90']));

  for (const viewport of Object.values(MOBILE_CONTEXTS)) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(viewport.height, viewport.height);
    await expectNoHorizontalOverflow(tmaPage);
    await expectTouchTargets(tmaSelector.getByRole('tab'));
  }
  const diaryLink = tmaReport.locator('.nutrition-report-days tbody a').first();
  await diaryLink.scrollIntoViewIfNeeded();
  await expectNoOverlap(diaryLink, tmaPage.locator('#appBottomNav'));

  await tmaPage.setViewportSize({ width: 390, height: 844 });
  await tma.setViewport(844, 844);
  await tma.setTheme('dark');
  await expect(tmaPage.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await expect
    .poll(() =>
      tmaReport
        .locator('.nutrition-report-chart__point')
        .first()
        .evaluate((point) => {
          const style = getComputedStyle(point);
          return {
            fill: style.fill,
            stroke: style.stroke,
            theme: document.documentElement.dataset.colorScheme,
          };
        }),
    )
    .toEqual({
      fill: 'rgb(255, 255, 255)',
      stroke: 'rgb(255, 255, 255)',
      theme: 'dark',
    });
  await tmaReport.evaluate((element) => element.scrollIntoView({ block: 'start' }));
  await tmaPage.screenshot({
    path: '../.artifacts/screenshots/task-57/tma-390x844-dark-compact.png',
  });
  await tmaReport.screenshot({
    path: '../.artifacts/screenshots/task-57/tma-390x844-dark-partial.png',
  });
  await tmaReport.locator('.nutrition-report-chart').screenshot({
    path: '../.artifacts/screenshots/task-57/tma-390x844-dark-chart.png',
  });

  await diaryLink.click();
  await expect(tmaPage).toHaveURL(/section=nutrition&date=.*return_to=/);
  await expect(tmaPage.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();
  await tmaPage.getByRole('link', { name: 'К отчёту по питанию' }).click();
  await expect(tmaPage).toHaveURL(/section=progress&nutrition_period=days_7/);
  await expect(tmaSelector.getByRole('tab', { name: '7 дней' })).toHaveAttribute(
    'aria-selected',
    'true',
  );
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

test('unified weekly review keeps Mobile Web/TMA parity and distinct adaptive decisions', async ({
  browser,
  mobilePage,
  tma,
  tmaPage,
}) => {
  const tmaApi = await installPlatformApi(tmaPage, {
    workoutStatus: 'none',
    weeklyReviewAvailable: true,
    weeklyCalibration: 'pending',
  });
  const mobileApi = await installPlatformApi(mobilePage, {
    browserSession: true,
    workoutStatus: 'none',
    weeklyReviewAvailable: true,
    weeklyCalibration: 'pending',
  });
  await Promise.all([
    tmaPage.goto('/app?section=progress&weekly_review=1'),
    mobilePage.goto('/app?section=progress&weekly_review=1'),
  ]);

  for (const page of [tmaPage, mobilePage]) {
    await expect(page.getByRole('heading', { name: 'Что известно приложению' })).toBeVisible();
    await expect(page.locator('#weekly-review')).toBeFocused();
    await page.getByRole('button', { name: 'Всё верно, продолжить' }).click();
    await expect(page.getByRole('heading', { name: 'Короткие уточнения' })).toBeVisible();
    await page.getByRole('button', { name: 'Пропустить вопросы' }).click();
    await expect(page.getByText('Есть предложение')).toBeVisible();
    await expect(page.getByText('2100 ккал', { exact: true })).toBeVisible();
    await expect(page.getByText('2300 ккал', { exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  }
  expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));
  for (const viewport of Object.values(MOBILE_CONTEXTS)) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(viewport.height, viewport.height);
    await expectNoHorizontalOverflow(tmaPage);
    await expectTouchTargets(tmaPage.locator('.weekly-review__decision button'));
  }
  const deferDecision = tmaPage.getByRole('button', { name: 'Отложить решение' });
  await deferDecision.scrollIntoViewIfNeeded();
  await expectNoOverlap(deferDecision, tmaPage.locator('#appBottomNav'));
  await tma.setActive(false);
  await tma.setActive(true);
  await expect(tmaPage.getByText('Есть предложение')).toBeVisible();

  await tmaPage.getByRole('button', { name: 'Принять новую цель' }).click();
  await mobilePage.getByRole('button', { name: 'Оставить текущую цель' }).click();
  await expect.poll(() => tmaApi.weeklyDecisionCalls()).toEqual(['accept']);
  await expect.poll(() => mobileApi.weeklyDecisionCalls()).toEqual(['reject']);
  await expect.poll(() => tmaApi.weeklyReviewSubmits()).toBe(1);
  await expect.poll(() => mobileApi.weeklyReviewSubmits()).toBe(1);

  const deferPage = await browser.newPage({ viewport: MOBILE_CONTEXTS.compact, hasTouch: true });
  const deferApi = await installPlatformApi(deferPage, {
    browserSession: true,
    weeklyReviewAvailable: true,
    weeklyCalibration: 'pending',
  });
  await deferPage.goto('/app?section=progress&weekly_review=1');
  await deferPage.getByRole('button', { name: 'Всё верно, продолжить' }).click();
  await deferPage.getByRole('button', { name: 'Пропустить вопросы' }).click();
  await deferPage.getByRole('button', { name: 'Отложить решение' }).click();
  await expect.poll(() => deferApi.weeklyDecisionCalls()).toEqual([]);
  await expect.poll(() => deferApi.weeklyReviewSubmits()).toBe(1);
  await deferPage.close();

  const insufficientPage = await browser.newPage({
    viewport: MOBILE_CONTEXTS.baseline,
    hasTouch: true,
  });
  const insufficientApi = await installPlatformApi(insufficientPage, {
    browserSession: true,
    weeklyReviewAvailable: true,
    weeklyCalibration: 'insufficient',
  });
  await insufficientPage.goto('/app?section=progress&weekly_review=1');
  await insufficientPage.getByRole('button', { name: 'Всё верно, продолжить' }).click();
  const note = insufficientPage.getByLabel('Заметка о неделе');
  await insufficientPage.setViewportSize({ width: 390, height: 560 });
  await note.focus();
  const skipQuestions = insufficientPage.getByRole('button', { name: 'Пропустить вопросы' });
  await skipQuestions.scrollIntoViewIfNeeded();
  await expectNoOverlap(skipQuestions, insufficientPage.locator('#appBottomNav'));
  await note.fill('Черновик переживает background и reload');
  await insufficientPage.reload();
  await expect(insufficientPage.getByLabel('Заметка о неделе')).toHaveValue(
    'Черновик переживает background и reload',
  );
  await skipQuestions.click();
  await expect(insufficientPage.getByText('Данных пока недостаточно')).toBeVisible();
  await insufficientPage.getByRole('button', { name: 'Завершить обзор' }).click();
  await expect.poll(() => insufficientApi.weeklyDecisionCalls()).toEqual([]);
  await expect.poll(() => insufficientApi.weeklyReviewSubmits()).toBe(1);
  await insufficientPage.close();
});

test('weekly review visual evidence covers compact Mobile Web, dark TMA and desktop', async ({
  browser,
}) => {
  const cases = [
    {
      surface: 'mobile-web',
      viewport: MOBILE_CONTEXTS.compact,
      theme: 'light' as const,
      step: 'facts' as const,
      telegram: false,
    },
    {
      surface: 'tma',
      viewport: MOBILE_CONTEXTS.baseline,
      theme: 'dark' as const,
      step: 'decision' as const,
      telegram: true,
    },
    {
      surface: 'desktop',
      viewport: { width: 1440, height: 960 },
      theme: 'light' as const,
      step: 'decision' as const,
      telegram: false,
    },
  ];

  for (const current of cases) {
    const page = await browser.newPage({ viewport: current.viewport, hasTouch: current.telegram });
    if (current.telegram) {
      await installTelegramHarness(page, { colorScheme: current.theme });
    } else {
      await page.addInitScript((theme) => localStorage.setItem('app-theme', theme), current.theme);
    }
    await installPlatformApi(page, {
      browserSession: !current.telegram,
      weeklyReviewAvailable: true,
      weeklyCalibration: 'pending',
    });
    await page.goto('/app?section=progress&weekly_review=1');
    await expect(page.getByRole('heading', { name: 'Что известно приложению' })).toBeVisible();
    if (current.step === 'decision') {
      await page.getByRole('button', { name: 'Всё верно, продолжить' }).click();
      await page.getByRole('button', { name: 'Пропустить вопросы' }).click();
      await expect(page.getByText('Есть предложение')).toBeVisible();
    }
    await expectNoHorizontalOverflow(page);

    const brandContract = await page.evaluate((step) => {
      const tokenValue = (property: 'color' | 'borderRadius', token: string) => {
        const sample = document.createElement('span');
        sample.style[property] = `var(${token})`;
        document.body.append(sample);
        const value = getComputedStyle(sample)[property];
        sample.remove();
        return value;
      };
      const primary = document.querySelector<HTMLElement>('.weekly-review__primary');
      const activeStep = document.querySelector<HTMLElement>(
        '.weekly-review__steps li[aria-current="step"]',
      );
      const boundary = document.querySelector<HTMLElement>(
        step === 'facts' ? '.weekly-review__target' : '.weekly-review__diff > div:last-child',
      );
      const decisionNote = document.querySelector<HTMLElement>('.weekly-review__decision-note');
      const disclosure = document.querySelector<HTMLElement>(
        '.weekly-review__history .disclosure-icon',
      );
      const disclosureRect = disclosure?.getBoundingClientRect();
      return {
        lime: tokenValue('color', '--v2-lime'),
        onLime: tokenValue('color', '--v2-on-lime'),
        actionRadius: tokenValue('borderRadius', '--radius-action'),
        primaryBackground: primary ? getComputedStyle(primary).backgroundColor : null,
        primaryColor: primary ? getComputedStyle(primary).color : null,
        primaryRadius: primary ? getComputedStyle(primary).borderRadius : null,
        activeStepBoundary: activeStep ? getComputedStyle(activeStep).borderBottomColor : null,
        boundaryBorder: boundary ? getComputedStyle(boundary).borderLeftColor : null,
        boundaryShadow: boundary ? getComputedStyle(boundary).boxShadow : null,
        noteBorder: decisionNote ? getComputedStyle(decisionNote).borderLeftColor : null,
        disclosure: disclosureRect
          ? {
              width: disclosureRect.width,
              height: disclosureRect.height,
              radius: getComputedStyle(disclosure!).borderRadius,
            }
          : null,
      };
    }, current.step);
    expect(brandContract.primaryBackground).toBe(brandContract.lime);
    expect(brandContract.primaryColor).toBe(brandContract.onLime);
    expect(brandContract.primaryRadius).toBe(brandContract.actionRadius);
    expect(brandContract.activeStepBoundary).toBe(brandContract.lime);
    if (current.step === 'facts') {
      expect(brandContract.boundaryBorder).toBe(brandContract.lime);
    } else {
      expect(brandContract.boundaryShadow).toContain(brandContract.lime);
      expect(brandContract.noteBorder).toBe(brandContract.lime);
    }
    expect(brandContract.disclosure).toEqual({ width: 28, height: 28, radius: '50%' });

    if (current.viewport.width >= 900) {
      const desktopPadding = await page.locator('.weekly-review-card').evaluate((card) => {
        const styles = getComputedStyle(card);
        return {
          left: styles.paddingLeft,
          right: styles.paddingRight,
          token: getComputedStyle(document.documentElement).getPropertyValue('--v2-space-4').trim(),
        };
      });
      expect(desktopPadding.left).toBe(desktopPadding.token);
      expect(desktopPadding.right).toBe(desktopPadding.token);
    }

    await page
      .locator('#weekly-review')
      .locator('..')
      .screenshot({
        path: `../.artifacts/screenshots/task-56/${current.surface}-${current.viewport.width}x${current.viewport.height}-${current.theme}-${current.step}.png`,
      });
    if (current.step === 'facts') {
      const primaryAction = page.getByRole('button', { name: 'Всё верно, продолжить' });
      await primaryAction.scrollIntoViewIfNeeded();
      await expectNoOverlap(primaryAction, page.locator('#appBottomNav'));
      const scheduleCard = page.locator('details.card').filter({
        has: page.getByRole('heading', { name: 'Расписание', exact: true }),
      });
      const weekCard = page.locator('details.card').filter({
        has: page.getByRole('heading', { name: 'Неделя', exact: true }),
      });
      const [scheduleBox, weekBox] = await Promise.all([
        scheduleCard.boundingBox(),
        weekCard.boundingBox(),
      ]);
      expect(scheduleBox).not.toBeNull();
      expect(weekBox).not.toBeNull();
      const adjacentGap = weekBox!.y - (scheduleBox!.y + scheduleBox!.height);
      expect(adjacentGap).toBeGreaterThanOrEqual(8);
      expect(adjacentGap).toBeLessThanOrEqual(16);
      await page.screenshot({
        path: `../.artifacts/screenshots/task-56/${current.surface}-${current.viewport.width}x${current.viewport.height}-${current.theme}-facts-actions.png`,
      });
    }
    if (current.telegram && current.step === 'decision') {
      const deferDecision = page.getByRole('button', { name: 'Отложить решение' });
      await deferDecision.scrollIntoViewIfNeeded();
      await expectNoOverlap(deferDecision, page.locator('#appBottomNav'));
      await page.screenshot({
        path: `../.artifacts/screenshots/task-56/${current.surface}-${current.viewport.width}x${current.viewport.height}-${current.theme}-decision-actions.png`,
      });
    }
    await page.close();
  }
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

test('manual nutrition targets validate, preserve keyboard flow and expose effective history in Mobile Web and TMA', async ({
  mobilePage,
  tma,
  tmaPage,
}) => {
  const api = await installPlatformApi(tmaPage);
  await installPlatformApi(mobilePage, {
    browserSession: true,
    nutritionTargetSource: 'trainer',
  });
  await Promise.all([
    tmaPage.goto('/app?section=nutrition'),
    mobilePage.goto('/app?section=nutrition'),
  ]);

  for (const currentPage of [tmaPage, mobilePage]) {
    await currentPage.getByRole('heading', { name: 'КБЖУ', exact: true }).click();
    if (currentPage === mobilePage) {
      await expect(currentPage.getByText('Назначено тренером', { exact: true })).toBeVisible();
      await expect(
        currentPage.getByLabel('Текущие ориентиры КБЖУ').getByText('Изменил: Ирина Тренерова'),
      ).toBeVisible();
      await currentPage.getByRole('button', { name: 'Указать вручную' }).click();
    }
    await expect(currentPage.getByRole('button', { name: 'Указать вручную' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await expect(
      currentPage.getByText(currentPage === mobilePage ? 'Назначено тренером' : 'Указано вручную', {
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      currentPage.getByLabel('Текущие ориентиры КБЖУ').getByText('Ориентир для текущего этапа'),
    ).toBeVisible();
    await expectNoHorizontalOverflow(currentPage);
  }
  expect(await sharedSurfaceSignature(tmaPage)).toEqual(await sharedSurfaceSignature(mobilePage));

  const calories = tmaPage.getByRole('spinbutton', { name: 'Калории, ккал' });
  const protein = tmaPage.getByRole('spinbutton', { name: 'Белки, г' });
  const fat = tmaPage.getByRole('spinbutton', { name: 'Жиры, г' });
  const carbs = tmaPage.getByRole('spinbutton', { name: 'Углеводы, г' });
  await calories.fill('1200');
  await protein.fill('200');
  await fat.fill('100');
  await carbs.fill('200');
  const save = tmaPage.getByRole('button', { name: 'Сохранить ручные ориентиры' });
  await expect(tmaPage.getByRole('alert')).toContainText('Проверьте разницу: 1300 ккал');
  await expect(save).toBeDisabled();
  await tmaPage.getByRole('checkbox', { name: /Сохранить значения/ }).check();

  await tma.setSafeArea({ top: 24, right: 2, bottom: 22, left: 2 });
  await tma.setContentSafeArea({ top: 36, right: 0, bottom: 18, left: 0 });
  await carbs.focus();
  await tma.setViewport(560, MOBILE_CONTEXTS.baseline.height, false);
  await expect(tmaPage.locator('#appBottomNav')).toBeHidden();
  await save.scrollIntoViewIfNeeded();
  await expect(save).toBeInViewport();
  await expectNoHorizontalOverflow(tmaPage);
  await tma.setTheme('dark');
  await tma.setActive(false);
  await tma.setActive(true);
  await expect(calories).toHaveValue('1200');
  await expect(tmaPage.getByRole('checkbox', { name: /Сохранить значения/ })).toBeChecked();

  await save.click();
  await expect(tmaPage.getByText('Ручные ориентиры КБЖУ сохранены')).toBeVisible();
  await expect(tmaPage.getByText('Калории 2100 → 1200 ккал')).toBeAttached();
  expect(api.manualTargetSaves()).toBe(1);
  expect(api.targetHistoryLength()).toBe(3);

  const retry = await tmaPage.evaluate(async () => {
    const response = await fetch('/api/v1/nutrition/targets/manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        calories: 1200,
        protein_g: 200,
        fat_g: 100,
        carbs_g: 200,
        effective_from: new Date().toLocaleDateString('sv-SE', {
          timeZone: 'Europe/Moscow',
        }),
        note: null,
        confirm_energy_mismatch: true,
      }),
    });
    return { status: response.status, id: (await response.json()).id };
  });
  expect(retry.status).toBe(200);
  expect(api.manualTargetSaves()).toBe(2);
  expect(api.targetHistoryLength()).toBe(3);

  const targetCard = tmaPage.locator('#nutrition-target-settings > details');
  if ((await targetCard.getAttribute('open')) === null) {
    await tmaPage.getByRole('heading', { name: 'КБЖУ', exact: true }).click();
  }
  for (const viewport of Object.values(MOBILE_CONTEXTS)) {
    await tmaPage.setViewportSize(viewport);
    await tma.setViewport(viewport.height, viewport.height);
    await expectNoHorizontalOverflow(tmaPage);
    await expectTouchTargets(tmaPage.locator('.nutrition-target-mode > button'));
  }
});

test('manual nutrition target history screenshots cover all responsive surfaces and themes', async ({
  browser,
}) => {
  const cases = [
    { surface: 'mobile-web', width: 360, height: 800, theme: 'light' },
    { surface: 'mobile-web', width: 390, height: 844, theme: 'dark' },
    { surface: 'mobile-web', width: 430, height: 932, theme: 'light' },
    { surface: 'mobile-web', width: 768, height: 900, theme: 'dark' },
    { surface: 'desktop-web', width: 1440, height: 900, theme: 'light' },
    { surface: 'tma-mock', width: 360, height: 800, theme: 'dark' },
    { surface: 'tma-mock', width: 390, height: 844, theme: 'light' },
    { surface: 'tma-mock', width: 430, height: 932, theme: 'dark' },
  ] as const;

  for (const current of cases) {
    const page = await browser.newPage({
      viewport: { width: current.width, height: current.height },
      hasTouch: current.width <= 768,
      isMobile: current.width <= 430,
      reducedMotion: 'reduce',
    });
    if (current.surface === 'tma-mock') {
      await installTelegramHarness(page, {
        colorScheme: current.theme,
        viewportHeight: current.height,
        viewportStableHeight: current.height,
      });
      await installPlatformApi(page, { nutritionTargetSource: 'trainer' });
    } else {
      await page.addInitScript((theme) => localStorage.setItem('app-theme', theme), current.theme);
      await installPlatformApi(page, { browserSession: true });
    }

    await page.goto('/app?section=nutrition');
    await page.getByRole('heading', { name: 'КБЖУ', exact: true }).click();
    if (current.surface === 'tma-mock') {
      await expect(page.getByText('Назначено тренером', { exact: true })).toBeVisible();
      await page.getByRole('button', { name: 'Указать вручную' }).click();
    }
    await expect(page.locator('html')).toHaveAttribute('data-color-scheme', current.theme);
    await expect(page.getByLabel('Текущие ориентиры КБЖУ')).toBeVisible();
    await expectNoHorizontalOverflow(page);

    const brandContract = await page.evaluate(() => {
      const tokenColor = (token: string) => {
        const sample = document.createElement('span');
        sample.style.color = `var(${token})`;
        document.body.append(sample);
        const color = getComputedStyle(sample).color;
        sample.remove();
        return color;
      };
      const save = document.querySelector<HTMLElement>('.nutrition-target-save');
      const activeMode = document.querySelector<HTMLElement>(
        '.nutrition-target-mode > button.is-active',
      );
      const note = document.querySelector<HTMLElement>('.nutrition-target-note');
      const disclosureIcons = Array.from(
        document.querySelectorAll<HTMLElement>('.nutrition-target-history__list .disclosure-icon'),
      );
      return {
        lime: tokenColor('--v2-lime'),
        onLime: tokenColor('--v2-on-lime'),
        saveBackground: save ? getComputedStyle(save).backgroundColor : null,
        saveColor: save ? getComputedStyle(save).color : null,
        activeModeShadow: activeMode ? getComputedStyle(activeMode).boxShadow : null,
        noteBorder: note ? getComputedStyle(note).borderLeftColor : null,
        disclosureIcons: disclosureIcons.map((icon) => {
          const rect = icon.getBoundingClientRect();
          return {
            width: rect.width,
            height: rect.height,
            radius: getComputedStyle(icon).borderRadius,
          };
        }),
      };
    });
    expect(brandContract.saveBackground).toBe(brandContract.lime);
    expect(brandContract.saveColor).toBe(brandContract.onLime);
    expect(brandContract.activeModeShadow).toContain(brandContract.lime);
    expect(brandContract.noteBorder).toBe(brandContract.lime);
    expect(brandContract.disclosureIcons.length).toBeGreaterThan(0);
    expect(
      brandContract.disclosureIcons.every(
        ({ width, height, radius }) => width === 28 && height === 28 && radius === '50%',
      ),
    ).toBe(true);

    const targetCard = page.locator('#nutrition-target-settings > details');
    await targetCard.scrollIntoViewIfNeeded();
    await targetCard.screenshot({
      path: `../.artifacts/screenshots/task-55/${current.surface}-${current.width}x${current.height}-${current.theme}.png`,
    });
    await page.close();
  }
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
  await tmaPage.getByRole('button', { name: 'Рассчитать ориентиры' }).click();
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
