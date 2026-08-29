import { expect, test, type Page, type Route } from '@playwright/test';
import type { FoodDiaryEntry } from '../../src/shared/api/types';

const zeroNutrition = {
  energy_kcal: '0.00',
  protein_g: '0.000',
  fat_g: '0.000',
  carbs_g: '0.000',
  fiber_g: null,
};

const yogurtEntry: FoodDiaryEntry = {
  id: 21,
  diary_date: '2026-08-19',
  meal_type: 'breakfast',
  food_id: 3,
  recipe_id: null,
  entry_kind: 'food',
  logged_at: null,
  food_name: 'Греческий йогурт',
  food_brand: 'YFC Foods',
  amount: '180.000',
  amount_unit: 'g',
  weight_g: '180.000',
  serving_amount: null,
  serving_unit: null,
  serving_weight_g: null,
  nutrition: {
    energy_kcal: '153.00',
    protein_g: '17.100',
    fat_g: '3.600',
    carbs_g: '10.800',
    fiber_g: null,
  },
  created_at: '2026-08-19T07:00:00Z',
  updated_at: '2026-08-19T07:00:00Z',
};

const oatmealFood = {
  id: 7,
  name: 'Овсяная каша',
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
  last_used_at: '2026-08-18T07:00:00Z',
  created_at: '2026-07-01T07:00:00Z',
  updated_at: '2026-07-01T07:00:00Z',
};

async function mockNutritionApi(page: Page) {
  let entries: FoodDiaryEntry[] = [yogurtEntry];
  let dayStatus: 'incomplete' | 'complete' = 'incomplete';

  await page.addInitScript(() => {
    sessionStorage.setItem('fit_access_token', 'e2e-token');
  });
  await page.route('**/api/v1/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (path === '/api/v1/public/config') {
      return route.fulfill({
        json: {
          app_env: 'test',
          enable_dev_auth: true,
          enable_web_auth: false,
          enable_email_auth: false,
          telegram_bot_username: '',
          oauth_providers: [],
        },
      });
    }
    if (path === '/api/v1/me') {
      return route.fulfill({
        json: {
          id: 1,
          telegram_user_id: 2001,
          username: 'nutrition_user',
          first_name: 'Анна',
          is_coach: false,
          is_admin: false,
          has_active_program: false,
          has_workout_history: false,
          onboarding: { status: 'complete', required_fields: [], missing_fields: [] },
          profile: {
            full_name: 'Анна Петрова',
            timezone: 'Europe/Moscow',
            goal: 'maintenance',
            kbju: null,
          },
          trainer: null,
        },
      });
    }
    if (path === '/api/v1/nutrition/diary' && request.method() === 'GET') {
      return route.fulfill({
        json: {
          diary_date: url.searchParams.get('diary_date') || '2026-08-19',
          timezone: 'Europe/Moscow',
          meals: [
            {
              meal_type: 'breakfast',
              entries,
              totals: entries.length ? yogurtEntry.nutrition : zeroNutrition,
            },
            { meal_type: 'lunch', entries: [], totals: zeroNutrition },
            { meal_type: 'dinner', entries: [], totals: zeroNutrition },
            { meal_type: 'snacks', entries: [], totals: zeroNutrition },
          ],
          totals: {
            energy_kcal: '2020.00',
            protein_g: '141.000',
            fat_g: '69.000',
            carbs_g: '221.000',
            fiber_g: null,
          },
          targets: {
            energy_kcal: '2000.00',
            protein_g: '140.000',
            fat_g: '70.000',
            carbs_g: '220.000',
          },
          remaining: {
            energy_kcal: '-20.00',
            protein_g: '-1.000',
            fat_g: '1.000',
            carbs_g: '-1.000',
          },
          status: entries.length ? dayStatus : 'unlogged',
          status_is_explicit: dayStatus === 'complete',
        },
      });
    }
    if (path === '/api/v1/nutrition/foods/recent') {
      return route.fulfill({ json: { items: [oatmealFood], total: 1, limit: 12, offset: 0 } });
    }
    if (path === '/api/v1/nutrition/foods/favorites') {
      return route.fulfill({ json: { items: [oatmealFood], total: 1, limit: 12, offset: 0 } });
    }
    if (path === '/api/v1/nutrition/diary/status' && request.method() === 'PUT') {
      dayStatus = 'complete';
      return route.fulfill({
        json: {
          diary_date: '2026-08-19',
          timezone: 'Europe/Moscow',
          meals: [
            { meal_type: 'breakfast', entries, totals: yogurtEntry.nutrition },
            { meal_type: 'lunch', entries: [], totals: zeroNutrition },
            { meal_type: 'dinner', entries: [], totals: zeroNutrition },
            { meal_type: 'snacks', entries: [], totals: zeroNutrition },
          ],
          totals: yogurtEntry.nutrition,
          targets: null,
          remaining: null,
          status: dayStatus,
          status_is_explicit: true,
        },
      });
    }
    if (path === '/api/v1/nutrition/diary/entries' && request.method() === 'POST') {
      const body = request.postDataJSON() as {
        diary_date: string;
        meal_type: FoodDiaryEntry['meal_type'];
        logged_at?: string | null;
        quick_add?: {
          name?: string | null;
          energy_kcal: number;
          protein_g?: number | null;
          fat_g?: number | null;
          carbs_g?: number | null;
        };
      };
      const isQuick = Boolean(body.quick_add);
      const created: FoodDiaryEntry = {
        ...yogurtEntry,
        id: 22,
        diary_date: body.diary_date,
        meal_type: body.meal_type,
        food_id: isQuick ? null : oatmealFood.id,
        entry_kind: isQuick ? 'quick_add' : 'food',
        logged_at: body.logged_at ?? null,
        food_name: body.quick_add?.name || (isQuick ? 'Быстрый ввод' : oatmealFood.name),
        food_brand: null,
        amount: '1.000',
        amount_unit: 'serving',
        weight_g: '50.000',
        serving_amount: '1.000',
        serving_unit: 'serving',
        serving_weight_g: '50.000',
        nutrition: isQuick
          ? {
              energy_kcal: String(body.quick_add?.energy_kcal ?? 0),
              protein_g:
                body.quick_add?.protein_g == null ? null : String(body.quick_add.protein_g),
              fat_g: body.quick_add?.fat_g == null ? null : String(body.quick_add.fat_g),
              carbs_g: body.quick_add?.carbs_g == null ? null : String(body.quick_add.carbs_g),
              fiber_g: null,
            }
          : {
              energy_kcal: '180.00',
              protein_g: '6.000',
              fat_g: '3.000',
              carbs_g: '31.000',
              fiber_g: '4.000',
            },
      };
      entries = [...entries, created];
      return route.fulfill({ status: 201, json: created });
    }
    return route.fulfill({ status: 404, json: { detail: `Unhandled ${path}` } });
  });
}

test('nutrition diary is responsive, keyboard-safe and supports local quick add', async ({
  page,
}) => {
  await page.clock.setFixedTime(new Date('2026-08-19T09:00:00+03:00'));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mockNutritionApi(page);
  await page.goto('/app?section=nutrition');

  await expect(page.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();
  await expect(page.getByText('Греческий йогурт')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'КБЖУ' })).toBeVisible();
  await expect(page.getByText('Немного выше ориентира: 20 ккал')).toBeVisible();
  await expect(page.locator('.nutrition-target').first()).not.toHaveClass(/is-over/);
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
    { width: 360, height: 740 },
  ]) {
    await page.setViewportSize(viewport);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    const week = page.getByRole('navigation', { name: 'Неделя дневника' });
    await expect(week.locator('button[aria-current="date"]')).toBeVisible();
    await expect(week.locator('button[aria-pressed="true"]')).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Дата дневника' })).not.toBeAttached();
    const selectedDay = week.locator('button[aria-pressed="true"]');
    expect((await selectedDay.boundingBox())?.height).toBeGreaterThanOrEqual(44);
    const borderTop = await week.evaluate((element) => getComputedStyle(element).borderTopWidth);
    expect(borderTop).toBe(viewport.width <= 640 ? '0px' : '1px');
    const status = page.locator('.nutrition-diary__status');
    const targetBadge = status.getByText('Цель КБЖУ настроена', { exact: true });
    const [weekBox, statusBox, targetBadgeBox] = await Promise.all([
      week.boundingBox(),
      status.boundingBox(),
      targetBadge.boundingBox(),
    ]);
    expect(weekBox).not.toBeNull();
    expect(statusBox).not.toBeNull();
    expect(targetBadgeBox).not.toBeNull();
    expect(statusBox!.y).toBeGreaterThanOrEqual(weekBox!.y + weekBox!.height);
    expect(targetBadgeBox!.y).toBeGreaterThanOrEqual(weekBox!.y + weekBox!.height);
  }

  await page.getByRole('button', { name: 'Предыдущая неделя' }).click();
  await expect(page.getByRole('heading', { name: 'Неделя', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Следующая неделя' }).click();
  await expect(page.getByRole('heading', { name: 'Эта неделя', exact: true })).toBeVisible();

  await page.getByRole('button', { name: /Быстрый ввод/ }).click();
  const calories = page.getByRole('spinbutton', { name: 'Калории' });
  await expect(calories).toHaveAttribute('inputmode', 'decimal');
  await expect(calories).toHaveAttribute('enterkeyhint', 'next');
  await page.getByRole('textbox', { name: 'Название (необязательно)' }).fill('Обед вне дома');
  await calories.fill('640');
  await page.getByLabel('Время (необязательно)').fill('13:10');
  await expect(page.getByRole('button', { name: 'Сохранить Quick Add' })).toBeInViewport();
  await page.getByRole('button', { name: 'Сохранить Quick Add' }).click();
  await expect(page.getByRole('dialog')).not.toBeAttached();
  await expect(page.getByText('Обед вне дома')).toBeVisible();
  await expect(page.getByText('Быстрый ввод · 13:10')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);

  await page.getByRole('button', { name: 'День заполнен' }).click();
  await expect(page.getByText('Подтверждено')).toBeVisible();

  const breakfast = page.getByRole('region', { name: 'Завтрак' });
  const addButton = breakfast.getByRole('button', { name: /Добавить/ });
  await addButton.focus();
  await page.keyboard.press('Enter');
  const barcodeEntry = page.getByRole('button', { name: 'Поиск по штрихкоду' });
  const search = page.getByRole('searchbox', { name: 'Поиск по названию или бренду' });
  await expect(barcodeEntry).toBeFocused();
  await expect(search).toBeVisible();
  await expect(page.getByRole('button', { name: /Свой продукт/ })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Рецепты' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeAttached();
  await expect(addButton).toBeFocused();

  await addButton.click();
  await page.getByRole('button', { name: 'Добавить Овсяная каша' }).click();
  await expect(page.getByRole('spinbutton', { name: 'Количество' })).toHaveValue('1');
  await page.getByRole('button', { name: 'Добавить в дневник' }).click();
  await expect(page.getByRole('dialog')).not.toBeAttached();
  await expect(page.getByText('Овсяная каша')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);

  const oatmeal = page.locator('.nutrition-entry').filter({ hasText: 'Овсяная каша' });
  await oatmeal.getByRole('button', { name: 'Повторить' }).click();
  await expect(page.getByRole('dialog', { name: 'Повторить продукт' })).toBeVisible();
  await expect(page.getByText('Новые записи добавятся к уже существующим.')).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Дата назначения' })).toHaveValue('2026-08-19');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(360);
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeAttached();
});

test('dark nutrition uses the shared lime status and progress accents', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('app-theme', 'dark'));
  await mockNutritionApi(page);
  await page.goto('/app?section=nutrition');

  const status = page.getByText('Цель КБЖУ настроена');
  await expect(status).toHaveCSS('background-color', 'rgb(30, 34, 30)');
  await expect(status).toHaveCSS('border-color', 'rgb(89, 111, 56)');
  await expect(status).toHaveCSS('color', 'rgb(185, 234, 114)');
  await expect(
    page.getByRole('progressbar', { name: /Калории:/ }).locator(':scope > span'),
  ).toHaveCSS('background-color', 'rgb(168, 232, 58)');
  await expect(page.getByRole('link', { name: 'Питание', exact: true })).toHaveCSS(
    'background-color',
    'rgb(30, 34, 30)',
  );
});
