import { expect, test, type Page, type Route } from '@playwright/test';

const screenshots = '../.artifacts/design-alternatives/49e-pilot/screenshots';
const today = '2026-08-22';

const workout = {
  id: 42,
  scheduled_date: today,
  scheduled_time: '18:30:00',
  title: 'Силовая база',
  status: 'in_progress',
  day_number: 1,
  week_number: 1,
  started_at: `${today}T15:00:00+03:00`,
  completed_at: null,
  exercises: [
    {
      id: 101,
      exercise_id: 11,
      exercise_title: 'Жим штанги лёжа',
      sort_order: 1,
      prescribed_sets: 3,
      prescribed_reps: '8–10',
      rest_seconds: 90,
      notes: 'Сохраняйте опору стоп и контролируйте траекторию.',
      has_guide: false,
      sets: [1, 2, 3].map((setNumber) => ({
        id: 200 + setNumber,
        set_number: setNumber,
        actual_reps: setNumber === 1 ? 10 : null,
        actual_weight: setNumber === 1 ? 50 : null,
        rir: null,
        set_kind: null,
        reached_failure: null,
        is_completed: setNumber === 1,
        version: 1,
      })),
    },
    {
      id: 102,
      exercise_id: 12,
      exercise_title: 'Тяга верхнего блока',
      sort_order: 2,
      prescribed_sets: 3,
      prescribed_reps: '10–12',
      rest_seconds: 90,
      notes: null,
      has_guide: false,
      sets: [1, 2, 3].map((setNumber) => ({
        id: 210 + setNumber,
        set_number: setNumber,
        actual_reps: null,
        actual_weight: null,
        rir: null,
        set_kind: null,
        reached_failure: null,
        is_completed: false,
        version: 1,
      })),
    },
  ],
};

const longWorkout = {
  ...workout,
  title: 'Силовая база — длинное название для проверки реального переноса',
  exercises: workout.exercises.map((exercise, index) => ({
    ...exercise,
    exercise_title:
      index === 0
        ? 'Жим штанги лёжа с контролируемой паузой и длинным названием'
        : 'Тяга верхнего блока с паузой в конечной позиции',
  })),
};

const oatmeal = {
  id: 7,
  name: 'Овсяная каша с очень длинным названием продукта',
  brand: null,
  barcode: null,
  energy_kcal_per_100g: '360.00',
  protein_g_per_100g: '12.000',
  fat_g_per_100g: '6.000',
  carbs_g_per_100g: '62.000',
  fiber_g_per_100g: '8.000',
  standard_serving_amount: '1.000',
  standard_serving_unit: 'serving',
  standard_serving_weight_g: '50.000',
  food_type: 'system',
  is_favorite: true,
  last_used_at: '2026-08-21T07:00:00Z',
  created_at: '2026-07-01T07:00:00Z',
  updated_at: '2026-08-21T07:00:00Z',
};

const user = {
  id: 7,
  telegram_user_id: 2001,
  username: 'pilot_client',
  first_name: 'Анна',
  is_coach: false,
  is_admin: false,
  is_root: false,
  has_active_program: true,
  has_workout_history: true,
  onboarding: { status: 'complete', required_fields: [], missing_fields: [] },
  profile: {
    full_name: 'Анна Петрова — длинное имя для проверки навигации',
    timezone: 'Europe/Moscow',
    goal: 'maintenance',
    level: 'beginner',
    height_cm: 168,
    workouts_per_week: 3,
    kbju: null,
  },
  trainer: null,
};

function diary(entries: Array<Record<string, unknown>> = []) {
  const zero = {
    energy_kcal: '0.00',
    protein_g: '0.000',
    fat_g: '0.000',
    carbs_g: '0.000',
    fiber_g: null,
  };
  return {
    diary_date: today,
    timezone: 'Europe/Moscow',
    meals: [
      { meal_type: 'breakfast', entries, totals: zero },
      { meal_type: 'lunch', entries: [], totals: zero },
      { meal_type: 'dinner', entries: [], totals: zero },
      { meal_type: 'snacks', entries: [], totals: zero },
    ],
    totals: {
      energy_kcal: '2020.00',
      protein_g: '141.000',
      fat_g: '69.000',
      carbs_g: '221.000',
      fiber_g: '18.000',
    },
    targets: {
      energy_kcal: '2100.00',
      protein_g: '140.000',
      fat_g: '70.000',
      carbs_g: '230.000',
    },
    remaining: {
      energy_kcal: '-20.00',
      protein_g: '-1.000',
      fat_g: '1.000',
      carbs_g: '-1.000',
    },
  };
}

async function mockApi(
  page: Page,
  options: { authenticated?: boolean; holdConfig?: boolean; longContent?: boolean } = {},
): Promise<{ releaseConfig(): void }> {
  let entries: Array<Record<string, unknown>> = [];
  let releaseConfig: () => void = () => undefined;
  const configGate = options.holdConfig
    ? new Promise<void>((resolve) => {
        releaseConfig = resolve;
      })
    : Promise.resolve();
  if (options.authenticated) {
    await page.addInitScript(() => sessionStorage.setItem('fit_access_token', '49e-pilot-token'));
  }
  await page.route('**/api/v1/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const apiPath = url.pathname;

    if (apiPath === '/api/v1/public/config') {
      await configGate;
      return route.fulfill({
        json: {
          app_env: 'dev',
          enable_dev_auth: false,
          enable_web_auth: true,
          enable_email_auth: false,
          telegram_bot_username: 'yfc_pilot_bot',
          oauth_providers: ['telegram', 'google', 'yandex', 'vk'],
        },
      });
    }
    if (apiPath === '/api/v1/auth/refresh') {
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    }
    if (apiPath === '/api/v1/me') return route.fulfill({ json: user });
    if (apiPath === '/api/v1/workouts/today') {
      return route.fulfill({ json: options.longContent ? longWorkout : workout });
    }
    if (apiPath === '/api/v1/workouts/progress/summary') {
      return route.fulfill({
        json: {
          user_id: 7,
          period_days: 30,
          period_start: '2026-07-24',
          period_end: today,
          training: {
            planned_workouts: 8,
            completed_workouts: 7,
            frequency_per_week: 1.63,
            volume_kg: 12400,
            new_personal_records: 1,
            last_completed_workout_on: '2026-08-20',
            next_workout: null,
          },
          nutrition: {
            visible: true,
            logged_days: 20,
            adherence_evaluated_days: 20,
            average_calories: 1980,
            target_calories: 2100,
            average_protein_g: 130,
            target_protein_g: 140,
            target_effective_on: '2026-07-01',
          },
          body: {
            latest_measurement: { measured_on: '2026-08-21', weight_kg: 81.2 },
            trends: [
              {
                metric: 'weight_kg',
                first_value: 82,
                latest_value: 81.2,
                change: -0.8,
                first_measured_on: '2026-07-25',
                latest_measured_on: '2026-08-21',
                point_count: 5,
                span_days: 27,
                interpretation_status: 'available',
                points: [
                  { measured_on: '2026-07-25', value: 82 },
                  { measured_on: '2026-08-01', value: 81.8 },
                  { measured_on: '2026-08-08', value: 81.65 },
                  { measured_on: '2026-08-15', value: 81.4 },
                  { measured_on: '2026-08-21', value: 81.2 },
                ],
              },
            ],
            priority: null,
            guidance: {},
          },
          adherence: {
            formula_version: 'adherence-v1',
            overall_percent: 84,
            included_components: ['workouts', 'calories', 'protein'],
            workouts: {},
            cardio: {},
            calories: {},
            protein: {},
          },
          data_sufficiency: {},
        },
      });
    }
    if (apiPath === '/api/v1/nutrition/diary' && request.method() === 'GET') {
      return route.fulfill({ json: diary(entries) });
    }
    if (
      apiPath === '/api/v1/nutrition/foods/recent' ||
      apiPath === '/api/v1/nutrition/foods/favorites'
    ) {
      return route.fulfill({ json: { items: [oatmeal], total: 1, limit: 12, offset: 0 } });
    }
    if (apiPath === '/api/v1/nutrition/diary/entries' && request.method() === 'POST') {
      const created = {
        id: 22,
        diary_date: today,
        meal_type: 'breakfast',
        food_id: oatmeal.id,
        recipe_id: null,
        food_name: oatmeal.name,
        food_brand: null,
        amount: '1.000',
        amount_unit: 'serving',
        weight_g: '50.000',
        serving_amount: '1.000',
        serving_unit: 'serving',
        serving_weight_g: '50.000',
        nutrition: {
          energy_kcal: '180.00',
          protein_g: '6.000',
          fat_g: '3.000',
          carbs_g: '31.000',
          fiber_g: '4.000',
        },
        created_at: '2026-08-22T08:00:00Z',
        updated_at: '2026-08-22T08:00:00Z',
      };
      entries = [created];
      return route.fulfill({ status: 201, json: created });
    }
    if (/\/api\/v1\/workouts\/sets\/\d+$/.test(apiPath)) {
      const setId = Number(apiPath.split('/').at(-1));
      const body = request.postDataJSON() as Record<string, unknown>;
      return route.fulfill({
        json: {
          id: setId,
          set_number: setId - 200,
          actual_reps: body.actual_reps ?? null,
          actual_weight: body.actual_weight ?? null,
          rir: body.rir ?? null,
          set_kind: body.set_kind ?? null,
          reached_failure: body.reached_failure ?? null,
          is_completed: body.is_completed ?? false,
          version: 2,
        },
      });
    }
    return route.fulfill({ json: [] });
  });
  return { releaseConfig };
}

async function setTheme(page: Page, theme: 'light' | 'dark'): Promise<void> {
  await page.addInitScript(
    (selectedTheme) => localStorage.setItem('app-theme', selectedTheme),
    theme,
  );
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    )
    .toBe(true);
}

test('Landing pilot keeps Quiet Pace across the required responsive matrix', async ({ page }) => {
  const matrix = [
    { width: 1440, height: 1000, theme: 'light' as const },
    { width: 1280, height: 900, theme: 'dark' as const },
    { width: 768, height: 900, theme: 'light' as const },
    { width: 430, height: 932, theme: 'dark' as const },
    { width: 390, height: 844, theme: 'light' as const },
    { width: 360, height: 800, theme: 'dark' as const },
  ];

  for (const viewport of matrix) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/?design_pilot=49e');
    await page.evaluate((theme) => {
      localStorage.setItem('app-theme', theme);
      window.dispatchEvent(new StorageEvent('storage', { key: 'app-theme' }));
    }, viewport.theme);
    await expect(page.locator('html')).toHaveAttribute('data-design-pilot', '49e');
    await expect(
      page.getByRole('heading', { level: 1, name: 'Знайте, что делать сегодня.' }),
    ).toBeVisible();
    await expect(page.locator('.pilot49e-landing-proof')).toBeVisible();
    await expect(page.getByText('Следите, как растёт прогресс.')).toHaveCount(0);
    await expect(page.locator('#how-it-works')).toBeAttached();
    await expectNoHorizontalOverflow(page);
    const copyBox = await page.locator('.pilot49e-landing-hero__copy').boundingBox();
    const proofBox = await page.locator('.pilot49e-landing-proof').boundingBox();
    if (viewport.width >= 1024) {
      expect(proofBox?.x).toBeGreaterThan((copyBox?.x ?? 0) + (copyBox?.width ?? 0));
    } else {
      expect(proofBox?.y).toBeGreaterThan((copyBox?.y ?? 0) + (copyBox?.height ?? 0));
    }
    await page.screenshot({
      path: `${screenshots}/landing-${viewport.width}-${viewport.theme}.png`,
      fullPage: true,
    });
  }
});

test('/login pilot renders the approved split and truthful provider error state', async ({
  page,
}) => {
  const api = await mockApi(page, { holdConfig: true });
  await setTheme(page, 'light');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/login?design_pilot=49e');
  await expect(page.getByText('Проверяем авторизацию…')).toBeVisible();
  await page.screenshot({
    path: `${screenshots}/login-390-light-loading.png`,
    fullPage: true,
  });
  api.releaseConfig();

  await expect(page.getByRole('heading', { name: 'Войти и продолжить' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Google/ })).toBeVisible();
  await expect(page.locator('.public-shell__skip-link')).toBeHidden();
  await page.keyboard.press('Tab');
  await expect(page.locator('.public-shell__brand')).toBeFocused();
  await page.locator('#login-content').focus();
  await page.screenshot({ path: `${screenshots}/login-390-light.png`, fullPage: true });

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.getByRole('heading', { name: 'Вернитесь к своему плану.' })).toBeVisible();
  await expect(page.locator('.auth-public-shell .public-shell__header')).toBeHidden();
  const layoutBox = await page.locator('.login-layout').boundingBox();
  const authPlaneBox = await page.locator('.login-card').boundingBox();
  expect(layoutBox?.width).toBe(1440);
  expect((authPlaneBox?.x ?? 0) / (layoutBox?.width ?? 1)).toBeCloseTo(0.52, 2);
  expect((await page.locator('.oauth-auth').boundingBox())?.width).toBe(240);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${screenshots}/login-1440-light.png`, fullPage: true });
  await page.goto('/login?design_pilot=49e&auth_error=provider_failure');
  await expect(page.getByRole('alert')).toContainText('Не удалось завершить вход');
  await page.screenshot({
    path: `${screenshots}/login-1440-light-error.png`,
    fullPage: true,
  });
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toBeVisible();
  await page.locator('#login-content').focus();

  await page.setViewportSize({ width: 1024, height: 900 });
  await expect(page.locator('.login-intro h1')).toHaveCSS('font-size', '35px');
  await expect(page.locator('.login-intro h1')).toHaveCSS('white-space', 'nowrap');
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `${screenshots}/login-1024-light-error.png`,
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => {
    localStorage.setItem('app-theme', 'dark');
    window.dispatchEvent(new StorageEvent('storage', { key: 'app-theme' }));
  });
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await expect(page.getByRole('heading', { name: 'Войти и продолжить' })).toBeVisible();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.locator('.oauth-button').first()).toHaveCSS(
    'background-color',
    'rgb(22, 25, 22)',
  );
  await expect(page.locator('.oauth-button').first()).toHaveCSS('color', 'rgb(238, 240, 234)');
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `${screenshots}/login-390-dark-error.png`,
    fullPage: true,
  });
});

test('Today and active workout use real app components and mobile bottom navigation', async ({
  page,
}) => {
  await mockApi(page, { authenticated: true });
  await setTheme(page, 'light');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/app?design_pilot=49e');

  await expect(page.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  expect((await page.locator('.app-bottom-nav').boundingBox())?.width).toBe(164);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${screenshots}/today-1440-light.png`, fullPage: true });

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.evaluate(() => {
    localStorage.setItem('app-theme', 'dark');
    window.dispatchEvent(new StorageEvent('storage', { key: 'app-theme' }));
  });
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  expect((await page.locator('.app-bottom-nav').boundingBox())?.width).toBe(164);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${screenshots}/today-1280-dark.png`, fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => {
    localStorage.setItem('app-theme', 'light');
    window.dispatchEvent(new StorageEvent('storage', { key: 'app-theme' }));
  });
  await page.reload();

  await expect(page.getByRole('heading', { name: 'Сегодня', exact: true })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  expect(await page.evaluate(() => matchMedia('(hover: none)').matches)).toBe(true);
  expect(await page.evaluate(() => navigator.maxTouchPoints)).toBeGreaterThan(0);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${screenshots}/today-390-light.png`, fullPage: true });

  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();
  const currentSet = page.locator('[data-workout-set-id="202"]');
  await expect(currentSet).toHaveAttribute('aria-current', 'step');
  const weight = currentSet.getByRole('spinbutton', { name: /Вес/ });
  await weight.fill('47.5');
  await expect(weight).toHaveValue('47.5');
  const primaryActionBox = await currentSet.locator('.active-workout-set__done').boundingBox();
  expect(primaryActionBox?.height).toBeGreaterThanOrEqual(44);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `${screenshots}/workout-390-light-current-set.png`,
    fullPage: true,
  });
});

test('fast nutrition entry survives touch, focus and offline state', async ({ page, context }) => {
  await mockApi(page, { authenticated: true });
  await setTheme(page, 'dark');
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto('/app?section=nutrition&design_pilot=49e');

  await expect(page.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();
  const breakfast = page.getByRole('region', { name: 'Завтрак' });
  await breakfast.getByRole('button', { name: /Добавить/ }).click();
  const search = page.getByRole('searchbox', { name: 'Поиск по названию или бренду' });
  await expect(search).toBeFocused();
  await page.getByRole('button', { name: /Добавить Овсяная каша/ }).click();
  await page.getByRole('button', { name: 'Добавить в дневник' }).click();
  await expect(page.locator('.nutrition-entry').filter({ hasText: oatmeal.name })).toBeVisible();

  await context.setOffline(true);
  await expect(
    page.getByText('Нет сети · изменения подходов сохранятся как черновик'),
  ).toBeVisible();
  await page.screenshot({
    path: `${screenshots}/nutrition-430-dark-offline.png`,
    fullPage: true,
  });
  await context.setOffline(false);
  await expectNoHorizontalOverflow(page);
});

test('long workout content preserves the mobile action hierarchy', async ({ page }) => {
  await mockApi(page, { authenticated: true, longContent: true });
  await setTheme(page, 'light');
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/app?design_pilot=49e');

  await expect(page.getByText('длинное название для проверки реального переноса')).toBeVisible();
  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();
  await expect(
    page.getByRole('heading', {
      name: 'Жим штанги лёжа с контролируемой паузой и длинным названием',
    }),
  ).toBeVisible();
  await expect(
    page.locator('.active-workout-set[aria-current="step"] .active-workout-set__done'),
  ).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `${screenshots}/workout-360-light-long-content.png`,
    fullPage: true,
  });
});

test('TMA mock applies safe areas, stable viewport, theme, BackButton object and keyboard resize', async ({
  page,
}) => {
  await mockApi(page, { authenticated: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(
    '/app?design_pilot=49e&pilot_surface=tma&pilot_theme=dark&pilot_safe_top=28&pilot_safe_bottom=20&pilot_content_safe_top=44&pilot_content_safe_bottom=16&tgWebAppPlatform=android&tgWebAppVersion=8.0',
  );

  const root = page.locator('html');
  await expect(root).toHaveAttribute('data-pilot-surface', 'tma-mock');
  await expect(root).toHaveAttribute('data-app-surface', 'telegram');
  await expect(root).toHaveAttribute('data-color-scheme', 'dark');
  await expect(root).toHaveAttribute('data-pilot-telegram-ready', 'true');
  await expect(root).toHaveAttribute('data-pilot-telegram-expanded', 'true');
  await expect(root).toHaveAttribute('data-pilot-back-button', 'hidden');
  await expect(page.locator('.app-bottom-nav')).toHaveCSS('padding-bottom', '20px');
  await page.screenshot({ path: `${screenshots}/tma-390-dark-today.png`, fullPage: true });

  await page.getByRole('button', { name: 'Продолжить тренировку' }).click();
  const currentSet = page.locator('[data-workout-set-id="202"]');
  const weight = currentSet.getByRole('spinbutton', { name: /Вес/ });
  await page.screenshot({ path: `${screenshots}/tma-390-dark-workout.png`, fullPage: true });
  await weight.focus();
  await page.setViewportSize({ width: 390, height: 560 });
  await page.evaluate(() => window.__YFC_DESIGN_PILOT_49E__?.setViewport(560, 844));
  await weight.scrollIntoViewIfNeeded();
  await expect(weight).toBeFocused();
  await expect(root).toHaveAttribute('data-pilot-keyboard', 'visible');
  await expect(page.locator('.app-bottom-nav')).toHaveCSS('visibility', 'hidden');
  await expect(currentSet.locator('.active-workout-set__done')).toBeVisible();
  const fieldBox = await weight.boundingBox();
  expect(fieldBox?.y).toBeGreaterThanOrEqual(0);
  expect((fieldBox?.y ?? 0) + (fieldBox?.height ?? 0)).toBeLessThanOrEqual(560);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `${screenshots}/tma-390-dark-keyboard.png`,
    fullPage: false,
  });
});
