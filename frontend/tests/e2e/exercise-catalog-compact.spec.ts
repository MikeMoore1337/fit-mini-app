import { expect, test } from '@playwright/test';
import { expectNoHorizontalOverflow, MOBILE_CONTEXTS } from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

test('client exercise rows stay compact-first across supported mobile widths', async ({ page }) => {
  await installPlatformApi(page, { browserSession: true, longExerciseName: true });
  await page.route('**/api/v1/programs/exercises', async (route) => {
    await route.fulfill({
      json: [
        {
          id: 1,
          title: 'Тяга верхнего блока с длинным названием для проверки переноса',
          slug: 'lat-pulldown',
          primary_muscle: 'Спина',
          equipment: 'Тросовый блок',
          primary_muscle_ids: ['back'],
          secondary_muscle_ids: ['biceps'],
          equipment_ids: ['cable'],
          alternatives: [],
          difficulty_level: 'beginner',
          is_custom: false,
          is_personalized: false,
          has_guide: true,
        },
        {
          id: 2,
          title: 'Приседания со штангой',
          slug: 'barbell-squat',
          primary_muscle: 'Ноги',
          equipment: 'Штанга',
          primary_muscle_ids: ['legs'],
          secondary_muscle_ids: ['core'],
          equipment_ids: ['barbell'],
          alternatives: [],
          difficulty_level: 'intermediate',
          is_custom: false,
          is_personalized: false,
          has_guide: true,
        },
      ],
    });
  });

  for (const [name, viewport] of Object.entries(MOBILE_CONTEXTS)) {
    await page.setViewportSize(viewport);
    await page.goto('/app?section=catalog');
    await expect(page.getByRole('heading', { name: 'Упражнения', exact: true })).toBeVisible();

    const rows = page.locator('.exercise-catalog-item');
    await expect(rows.first()).toBeVisible();
    const rowHeights = await rows.evaluateAll((items) =>
      items.slice(0, 3).map((item) => item.getBoundingClientRect().height),
    );
    expect(rowHeights.length).toBeGreaterThan(0);
    expect(Math.max(...rowHeights)).toBeLessThanOrEqual(128);

    const primaryAction = rows.first().getByRole('button', { name: /Техника и детали|Подробнее/ });
    expect((await primaryAction.boundingBox())?.height).toBeGreaterThanOrEqual(44);
    await expectNoHorizontalOverflow(page);
    await page.locator('.exercise-catalog-list').screenshot({
      path: `../.artifacts/screenshots/task-113A-round-2/exercise-catalog-${name}-${viewport.width}.png`,
    });
  }
});
