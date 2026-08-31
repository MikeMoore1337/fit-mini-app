import { expect, test, type Page } from '@playwright/test';
import {
  expectNoHorizontalOverflow,
  installTelegramHarness,
  MOBILE_CONTEXTS,
  newMobilePage,
  TelegramHarness,
} from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

const exercise = {
  id: 12001,
  edit_target_id: 12001,
  title: 'Верхняя рычажная тяга с упором грудью',
  slug: 'lever-high-row',
  metric_type: 'strength',
  primary_muscle: 'Спина',
  equipment: 'Тренажёр',
  primary_muscle_ids: ['back'],
  secondary_muscle_ids: ['biceps', 'posterior_deltoid', 'forearms'],
  equipment_ids: ['machine'],
  aliases: ['верхняя тяга хаммер', 'high row'],
  movement_pattern: 'row',
  machine_variant_tags: ['plate_loaded', 'lever', 'independent'],
  execution_variant_tags: ['bilateral', 'unilateral'],
  alternatives: [],
  difficulty_level: 'beginner',
  is_custom: false,
  is_personalized: false,
  has_guide: true,
  source_exercise_id: null,
};

const guide = {
  technique_steps: [
    'Настрой сиденье и грудной упор так, чтобы дотянуться до верхних рукоятей без отрыва груди.',
    'Потяни локти вниз и назад, сохраняя грудь на опоре и запястья нейтральными.',
    'Плавно выпрями руки вверх-вперёд, не позволяя плечам резко тянуться к ушам.',
  ],
  breathing: 'Выдох во время тяги, вдох при контролируемом возврате рычагов.',
  common_mistakes: [
    'Отрыв груди от опоры',
    'Рывок корпусом вместо тяги локтями',
    'Неравная траектория независимых рычагов',
  ],
  muscles: [
    {
      identifier: 'back',
      name: 'Спина',
      role_id: 'primary',
      role: 'Основная',
      function: 'Тянет плечо к корпусу.',
    },
    {
      identifier: 'biceps',
      name: 'Бицепс',
      role_id: 'secondary',
      role: 'Вспомогательная / стабилизатор',
      function: 'Сгибает локоть.',
    },
  ],
  equipment: [{ identifier: 'machine', name: 'Тренажёр' }],
  safety_notes: ['Настрой тренажёр до начала подхода.'],
  alternatives: [],
  media: [
    {
      type: 'image',
      url: '/static/exercise-guides/lever-high-row-active.svg',
      poster: '/static/exercise-guides/lever-high-row-active.svg',
      phase: 'Фаза усилия',
      alt: 'Верхняя рычажная тяга: конечное положение, локти отведены вниз и назад',
      source_name: 'Your Fitness Coach',
      source_url: '/',
      source_license: 'Иллюстрация создана для приложения',
      source_license_url: null,
      width: 720,
      height: 520,
      byte_size: 3200,
      sort_order: 0,
    },
    {
      type: 'image',
      url: '/static/exercise-guides/lever-high-row-start.svg',
      poster: '/static/exercise-guides/lever-high-row-start.svg',
      phase: 'Фаза возврата',
      alt: 'Верхняя рычажная тяга: исходное положение, грудь на опоре и руки направлены вверх-вперёд',
      source_name: 'Your Fitness Coach',
      source_url: '/',
      source_license: 'Иллюстрация создана для приложения',
      source_license_url: null,
      width: 720,
      height: 520,
      byte_size: 3200,
      sort_order: 1,
    },
  ],
  images: [],
  media_reference: 'exercise-guides:lever-high-row',
  source_name: 'Your Fitness Coach',
  source_url: '/',
  source_license: 'Иллюстрация создана для приложения',
  source_license_url: null,
};

async function installExerciseMocks(page: Page) {
  await installPlatformApi(page, { browserSession: true });
  await page.route('**/api/v1/programs/exercises', (route) => route.fulfill({ json: [exercise] }));
  await page.route('**/api/v1/programs/exercises/12001', (route) =>
    route.fulfill({ json: { ...exercise, guide } }),
  );
  await page.route('**/static/exercise-guides/lever-high-row-*.svg', (route) => {
    const filename = route.request().url().split('/').at(-1);
    if (!filename) throw new Error('SVG filename is missing');
    return route.fulfill({
      path: `../backend/assets/exercise-guides/${filename}`,
      contentType: 'image/svg+xml',
    });
  });
}

test('upper-body alias, compact row and guide work in mocked TMA mobile viewports', async ({
  browser,
}) => {
  const { context, page } = await newMobilePage(browser, 'compact');
  await installTelegramHarness(page, { platform: 'android' });
  await installExerciseMocks(page);

  for (const [name, viewport] of Object.entries(MOBILE_CONTEXTS)) {
    await page.setViewportSize(viewport);
    await page.goto('/app?section=catalog');
    await page.getByRole('searchbox', { name: 'Поиск' }).fill('верхняя тяга хаммер');

    const row = page.locator('.exercise-catalog-item');
    await expect(row).toHaveCount(1);
    await expect(row).toContainText(exercise.title);
    expect((await row.boundingBox())?.height).toBeLessThanOrEqual(128);
    const guideButton = row.getByRole('button', { name: /Техника и детали/ });
    await guideButton.tap();

    const dialog = page.getByRole('dialog', { name: exercise.title });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('heading', { name: 'Техника выполнения' })).toBeVisible();
    const media = dialog.locator('.exercise-guide-image img');
    await expect(media).toHaveCount(2);
    await expect(media.first()).toHaveAttribute('loading', 'lazy');
    await expect
      .poll(() =>
        media.evaluateAll((items) =>
          items.every((item) => (item as HTMLImageElement).naturalWidth > 0),
        ),
      )
      .toBe(true);
    await expectNoHorizontalOverflow(page);
    await dialog.screenshot({
      path: `../.artifacts/screenshots/task-120b/guide-${name}-${viewport.width}.png`,
    });
    await dialog.getByRole('button', { name: 'Закрыть карточку упражнения' }).click();
  }

  const tmaState = await new TelegramHarness(page).state();
  expect(tmaState.ready).toBeGreaterThan(0);
  expect(tmaState.platform).toBe('android');
  await context.close();
});

test('upper-body alias and guide keep tablet and desktop regression paths', async ({ page }) => {
  await installExerciseMocks(page);

  for (const viewport of [
    { width: 768, height: 900 },
    { width: 1280, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/app?section=catalog');
    const search = page.getByRole('searchbox', { name: 'Поиск' });
    await search.click();
    await search.fill('high row');

    const row = page.locator('.exercise-catalog-item');
    await expect(row).toHaveCount(1);
    await row.getByRole('button', { name: /Техника и детали/ }).click();
    const dialog = page.getByRole('dialog', { name: exercise.title });
    await expect(dialog).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await dialog.getByRole('button', { name: 'Закрыть карточку упражнения' }).click();
  }
});
