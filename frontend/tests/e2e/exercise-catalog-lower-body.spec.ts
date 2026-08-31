import { expect, test, type Page } from '@playwright/test';
import {
  expectNoHorizontalOverflow,
  installTelegramHarness,
  MOBILE_CONTEXTS,
  newMobilePage,
  TelegramHarness,
} from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

const definitions = [
  ['pendulum-squat', 'Маятниковый присед в тренажёре', ['pendulum squat']],
  ['plate-loaded-leg-press', 'Жим ногами в тренажёре с дисками', ['жим ногами на блинах']],
  ['unilateral-leg-press', 'Жим одной ногой в тренажёре', ['single leg press']],
  [
    'machine-hip-thrust',
    'Ягодичный мост в рычажном тренажёре',
    ['ягодичный тренажер', 'glute drive'],
  ],
  ['smith-split-squat', 'Сплит-присед в машине Смита', ['smith lunge']],
  ['machine-glute-kickback', 'Разгибание бедра назад в тренажёре', ['machine glute kickback']],
  ['v-squat-machine', 'V-присед в рычажном тренажёре', ['v squat machine']],
  ['reverse-hyperextension', 'Обратная гиперэкстензия', ['reverse hyper']],
] as const;

const exercises = definitions.map(([slug, title, aliases], index) => ({
  id: 12020 + index,
  edit_target_id: 12020 + index,
  title,
  slug,
  metric_type: 'strength',
  primary_muscle: slug.includes('hip') || slug.includes('kickback') ? 'Ягодицы' : 'Квадрицепс',
  equipment: slug === 'smith-split-squat' ? 'Машина Смита' : 'Тренажёр',
  primary_muscle_ids: [slug.includes('hip') || slug.includes('kickback') ? 'glutes' : 'quadriceps'],
  secondary_muscle_ids: ['hamstrings'],
  equipment_ids: ['machine'],
  aliases: [...aliases],
  movement_pattern: slug === 'machine-hip-thrust' ? 'glute' : 'squat',
  machine_variant_tags: slug === 'smith-split-squat' ? ['smith'] : ['plate_loaded', 'lever'],
  execution_variant_tags:
    slug.includes('unilateral') || slug.includes('kickback') || slug.includes('split')
      ? ['unilateral']
      : ['bilateral'],
  alternatives: [],
  difficulty_level: 'beginner',
  is_custom: false,
  is_personalized: false,
  has_guide: true,
  source_exercise_id: null,
}));

const machineHipThrust = exercises.find((exercise) => exercise.slug === 'machine-hip-thrust')!;
const guide = {
  technique_steps: [
    'Настрой опору и ремень или подушку по инструкции тренажёра, зафиксируй таз и поставь стопы устойчиво.',
    'Разогни тазобедренные суставы без прогиба поясницы.',
    'Плавно опусти таз, сохраняя контакт с опорами.',
  ],
  breathing: 'Вдох при опускании таза, выдох во время разгибания бёдер.',
  common_mistakes: ['Прогиб поясницы', 'Стопы теряют опору', 'Рычаг резко опускается'],
  muscles: [
    {
      identifier: 'glutes',
      name: 'Ягодицы',
      role_id: 'primary',
      role: 'Основная',
      function: 'Разгибают бедро.',
    },
  ],
  equipment: [{ identifier: 'machine', name: 'Тренажёр' }],
  safety_notes: ['Используй нагрузку и амплитуду, при которых сохраняется описанная техника.'],
  alternatives: [],
  media: [
    {
      type: 'image',
      url: '/static/exercise-guides/machine-hip-thrust-active.svg',
      poster: '/static/exercise-guides/machine-hip-thrust-active.svg',
      phase: 'Фаза усилия',
      alt: 'Ягодичный мост в рычажном тренажёре: бёдра разогнуты',
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
      url: '/static/exercise-guides/machine-hip-thrust-start.svg',
      poster: '/static/exercise-guides/machine-hip-thrust-start.svg',
      phase: 'Фаза возврата',
      alt: 'Ягодичный мост в рычажном тренажёре: таз опущен',
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
  media_reference: 'exercise-guides:machine-hip-thrust',
  source_name: 'Your Fitness Coach',
  source_url: '/',
  source_license: 'Иллюстрация создана для приложения',
  source_license_url: null,
};

async function installExerciseMocks(page: Page) {
  await installPlatformApi(page, { browserSession: true });
  await page.route('**/api/v1/programs/exercises', (route) => route.fulfill({ json: exercises }));
  await page.route(`**/api/v1/programs/exercises/${machineHipThrust.id}`, (route) =>
    route.fulfill({ json: { ...machineHipThrust, guide } }),
  );
  await page.route('**/static/exercise-guides/machine-hip-thrust-*.svg', (route) => {
    const filename = route.request().url().split('/').at(-1);
    if (!filename) throw new Error('SVG filename is missing');
    return route.fulfill({
      path: `../backend/assets/exercise-guides/${filename}`,
      contentType: 'image/svg+xml',
    });
  });
}

test('lower-body aliases, compact guide and program selection work on small viewports', async ({
  browser,
}) => {
  const { context, page } = await newMobilePage(browser, 'compact');
  await installTelegramHarness(page, { platform: 'android' });
  await installExerciseMocks(page);

  for (const [name, viewport] of Object.entries(MOBILE_CONTEXTS)) {
    await page.setViewportSize(viewport);
    await page.goto('/app?section=catalog');
    const search = page.getByRole('searchbox', { name: 'Поиск' });

    for (const [query, expectedTitle] of [
      ['pendulum squat', 'Маятниковый присед в тренажёре'],
      ['жим ногами на блинах', 'Жим ногами в тренажёре с дисками'],
      ['ягодичный тренажер', 'Ягодичный мост в рычажном тренажёре'],
      ['smith lunge', 'Сплит-присед в машине Смита'],
      ['reverse hyper', 'Обратная гиперэкстензия'],
    ] as const) {
      await search.fill(query);
      const row = page.locator('.exercise-catalog-item');
      await expect(row).toHaveCount(1);
      await expect(row).toContainText(expectedTitle);
      expect((await row.boundingBox())?.height).toBeLessThanOrEqual(128);
    }

    await search.fill('ягодичный тренажер');
    await page
      .locator('.exercise-catalog-item')
      .getByRole('button', { name: /Техника и детали/ })
      .tap();
    const dialog = page.getByRole('dialog', { name: machineHipThrust.title });
    await expect(dialog).toBeVisible();
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
      path: `../.artifacts/screenshots/task-120c/guide-${name}-${viewport.width}.png`,
    });
    await dialog.getByRole('button', { name: 'Закрыть карточку упражнения' }).click();
  }

  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/app?section=programs');
  const builder = page.locator('#program-builder');
  const picker = builder.getByRole('combobox', { name: 'Поиск упражнения' }).first();
  await picker.fill('жим ногами на блинах');
  const option = builder.getByRole('option', { name: /Жим ногами в тренажёре с дисками/ });
  await expect(option).toBeVisible();
  await option.tap();
  await expect(picker).toHaveValue('Жим ногами в тренажёре с дисками');
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: '../.artifacts/screenshots/task-120c/program-picker-mocked-tma-360.png',
    fullPage: true,
  });

  const tmaState = await new TelegramHarness(page).state();
  expect(tmaState.ready).toBeGreaterThan(0);
  expect(tmaState.platform).toBe('android');
  await context.close();
});

test('lower-body catalog and picker keep Mobile Web and desktop parity', async ({ browser }) => {
  const { context, page } = await newMobilePage(browser, 'baseline');
  await installExerciseMocks(page);

  for (const [name, viewport] of Object.entries(MOBILE_CONTEXTS)) {
    await page.setViewportSize(viewport);
    await page.goto('/app?section=catalog');
    await page.getByRole('searchbox', { name: 'Поиск' }).fill('machine glute kickback');
    const row = page.locator('.exercise-catalog-item');
    await expect(row).toHaveCount(1);
    await expect(row).toContainText('Разгибание бедра назад в тренажёре');
    expect((await row.boundingBox())?.height).toBeLessThanOrEqual(128);
    await expectNoHorizontalOverflow(page);
    if (viewport.width === 390) {
      await page.screenshot({
        path: `../.artifacts/screenshots/task-120c/catalog-mobile-web-${name}-390.png`,
        fullPage: true,
      });
    }
  }

  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/app?section=programs');
  const picker = page
    .locator('#program-builder')
    .getByRole('combobox', { name: 'Поиск упражнения' })
    .first();
  await picker.fill('glute drive');
  const option = page.getByRole('option', {
    name: /Ягодичный мост в рычажном тренажёре/,
  });
  await expect(option).toBeVisible();
  await option.tap();
  await expect(picker).toHaveValue('Ягодичный мост в рычажном тренажёре');
  await expectNoHorizontalOverflow(page);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto('/app?section=catalog');
  await page.getByRole('searchbox', { name: 'Поиск' }).fill('v squat machine');
  await expect(page.locator('.exercise-catalog-item')).toContainText(
    'V-присед в рычажном тренажёре',
  );
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: '../.artifacts/screenshots/task-120c/catalog-desktop-1280.png',
    fullPage: true,
  });

  await context.close();
});
