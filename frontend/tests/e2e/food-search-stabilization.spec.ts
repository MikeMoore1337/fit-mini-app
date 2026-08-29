import { expect, test } from '@playwright/test';
import { expectNoHorizontalOverflow } from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

test('empty local food search automatically shows the configured external result', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installPlatformApi(page, { browserSession: true });
  await page.route('**/api/v1/nutrition/foods/search*', async (route) => {
    const url = new URL(route.request().url());
    const includeExternal = url.searchParams.get('include_external') === 'true';
    await route.fulfill({
      json: {
        items: [],
        external_items: includeExternal
          ? [
              {
                name: 'Nutella hazelnut spread',
                brand: 'Ferrero',
                barcode: '3017620422003',
                energy_kcal_per_100g: '539.00',
                protein_g_per_100g: '6.300',
                fat_g_per_100g: '30.900',
                carbs_g_per_100g: '57.500',
                fiber_g_per_100g: null,
                standard_serving_amount: null,
                standard_serving_unit: null,
                standard_serving_weight_g: null,
                external_id: '3017620422003',
                source: {
                  provider: 'open_food_facts',
                  attribution: 'Open Food Facts contributors',
                  source_url: 'https://world.openfoodfacts.org/product/3017620422003',
                  license: 'ODbL-1.0',
                  license_url: 'https://opendatacommons.org/licenses/odbl/1-0/',
                },
              },
            ]
          : [],
        total: 0,
        limit: 20,
        offset: 0,
        provider_status: includeExternal ? 'available' : 'not_requested',
      },
    });
  });

  await page.goto('/app?section=nutrition');
  const breakfast = page.getByRole('region', { name: /Завтрак/ });
  await breakfast.getByRole('button', { name: /Добавить/ }).click();
  await page.getByRole('searchbox', { name: 'Поиск по названию или бренду' }).fill('нутелла');

  await expect(page.getByText('Nutella hazelnut spread')).toBeVisible();
  await expect(page.getByText(/Ferrero/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Источник' })).toHaveAttribute(
    'href',
    'https://world.openfoodfacts.org/product/3017620422003',
  );
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: '../.artifacts/screenshots/task-113A-round-2/mobile-food-search-external-result-390.png',
  });
});
