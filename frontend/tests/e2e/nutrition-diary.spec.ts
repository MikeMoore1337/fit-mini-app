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
        },
      });
    }
    if (path === '/api/v1/nutrition/foods/recent') {
      return route.fulfill({ json: { items: [oatmealFood], total: 1, limit: 12, offset: 0 } });
    }
    if (path === '/api/v1/nutrition/foods/favorites') {
      return route.fulfill({ json: { items: [oatmealFood], total: 1, limit: 12, offset: 0 } });
    }
    if (path === '/api/v1/nutrition/diary/entries' && request.method() === 'POST') {
      const body = request.postDataJSON() as {
        diary_date: string;
        meal_type: FoodDiaryEntry['meal_type'];
      };
      const created: FoodDiaryEntry = {
        ...yogurtEntry,
        id: 22,
        diary_date: body.diary_date,
        meal_type: body.meal_type,
        food_id: oatmealFood.id,
        food_name: oatmealFood.name,
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
    await expect(page.getByRole('button', { name: 'Предыдущий день' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Следующий день' })).toBeDisabled();
  }

  const breakfast = page.getByRole('region', { name: 'Завтрак' });
  const addButton = breakfast.getByRole('button', { name: /Добавить/ });
  await addButton.focus();
  await page.keyboard.press('Enter');
  const search = page.getByRole('searchbox', { name: 'Поиск по названию или бренду' });
  await expect(search).toBeFocused();
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
});
