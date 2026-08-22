import { expect, test } from '@playwright/test';

const representativePages = [
  {
    path: '/training',
    heading: /план тренировки, который остаётся перед глазами/i,
  },
  {
    path: '/knowledge',
    heading: /материалы, которые помогают понять следующий шаг/i,
  },
  {
    path: '/knowledge/nutrition/kbju-as-a-reference',
    heading: /кбжу как ориентир, а не обещание результата/i,
  },
  {
    path: '/knowledge/training/repetitions-in-reserve',
    heading: /повторы в запасе: полезная оценка/i,
  },
];

test('публичные страницы сохраняют hierarchy и не создают overflow', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
    { width: 360, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    for (const publicPage of representativePages) {
      await page.goto(publicPage.path);

      await expect(page.getByRole('heading', { level: 1, name: publicPage.heading })).toBeVisible();
      await expect(page.getByRole('navigation', { name: 'Хлебные крошки' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Войти' })).toBeVisible();
      await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'index, follow');
      await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
        'href',
        `http://127.0.0.1:4173${publicPage.path}`,
      );
      await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
        'content',
        'http://127.0.0.1:4173/assets/brand/yfc-social-preview.png',
      );
      await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
        'content',
        'summary_large_image',
      );
      expect(
        await page.evaluate(() => ({
          content: document.documentElement.scrollWidth,
          viewport: window.innerWidth,
        })),
      ).toEqual({ content: viewport.width, viewport: viewport.width });

      if (viewport.width === 1440) {
        const heroGutters = await page.evaluate(() => {
          const hero = document.querySelector('.public-hero')!.getBoundingClientRect();
          const copy = document.querySelector('.public-hero__copy')!.getBoundingClientRect();
          const summary = document.querySelector('.public-hero__summary')!.getBoundingClientRect();
          return {
            left: copy.left - hero.left,
            right: hero.right - summary.right,
          };
        });
        expect(heroGutters.left).toBeGreaterThanOrEqual(40);
        expect(heroGutters.right).toBeGreaterThanOrEqual(40);
      }
    }
  }
});

test('mobile menu, skip link and contextual navigation work without an auth wall', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/progress');

  const skipLink = page.getByRole('link', { name: 'К содержимому' });
  await skipLink.focus();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.locator('#public-content')).toBeFocused();

  const menu = page.getByRole('button', { name: 'Открыть меню' });
  await menu.click();
  await expect(page.getByRole('button', { name: 'Закрыть меню' })).toHaveAttribute(
    'aria-expanded',
    'true',
  );
  const publicNavigation = page.getByRole('navigation', { name: 'Публичные разделы' });
  await expect(publicNavigation.getByRole('link', { name: 'Питание' })).toBeVisible();
  await publicNavigation.getByRole('link', { name: 'Питание' }).click();
  await expect(page).toHaveURL('/nutrition');
  await expect(page.getByRole('heading', { level: 1, name: /ориентиры кбжу/i })).toBeVisible();
});

test('guide exposes visible editorial metadata, sources and matching Article schema', async ({
  page,
}) => {
  await page.goto('/knowledge/training/how-to-start-strength-training');

  await expect(page.getByText('Редакция Your Fitness Coach')).toBeVisible();
  await expect(page.getByText(/22 августа 2026/i).first()).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Оглавление' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Источники' })).toBeVisible();
  await expect(page.getByRole('link', { name: /WHO Guidelines/i })).toHaveAttribute(
    'href',
    'https://www.who.int/publications/i/item/9789240015128',
  );
  const structuredData = await page
    .locator('script[type="application/ld+json"][data-public-seo]')
    .textContent();
  expect(structuredData).not.toBeNull();
  const payload = JSON.parse(structuredData ?? '{}') as {
    '@graph': Array<{ '@type': string }>;
  };
  expect(payload['@graph'].map((item) => item['@type'])).toEqual(['Article', 'BreadcrumbList']);
});

test('a public exercise stays readable on mobile and gets facts from the public API', async ({
  page,
}) => {
  let releaseResponse: (() => void) | undefined;
  const responseGate = new Promise<void>((resolve) => {
    releaseResponse = resolve;
  });
  await page.route('**/api/v1/public/exercises/bench-press', async (route) => {
    await responseGate;
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        slug: 'bench-press',
        title: 'Жим лежа',
        primary_muscle: 'Грудь',
        secondary_muscles: ['Трицепс'],
        equipment: 'Штанга',
        difficulty_level: 'intermediate',
        technique_steps: [
          'Сведите лопатки и устойчиво поставьте стопы.',
          'Опустите гриф под контролем и выжмите его вверх.',
        ],
        breathing: 'Вдохните перед опусканием, выдохните после трудной части подъёма.',
        common_mistakes: ['Потеря опоры стоп.', 'Резкий отскок грифа.'],
        safety_notes: ['Используйте страховку при тяжёлых подходах.'],
        source_name: 'Your Fitness Coach exercise domain',
        source_url: 'https://your-fitness-coach.ru/',
        source_license: 'Собственные данные проекта',
        source_license_url: null,
      }),
    });
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/exercises/bench-press');

  await expect(page.getByRole('status')).toContainText('Загружаем технику');
  releaseResponse?.();
  await expect(page.getByRole('heading', { name: 'Техника выполнения' })).toBeVisible();
  await expect(page.getByText('Трицепс')).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Your Fitness Coach exercise domain' }),
  ).toHaveAttribute('href', 'https://your-fitness-coach.ru/');
  expect(
    await page.evaluate(() => ({
      content: document.documentElement.scrollWidth,
      viewport: window.innerWidth,
    })),
  ).toEqual({ content: 360, viewport: 360 });
});

test('campaign parameters keep one canonical URL and a fetchable social preview', async ({
  page,
  request,
}) => {
  await page.goto(
    '/training?utm_source=telegram&utm_medium=organic_social&utm_campaign=strength_start_guide&utm_content=channel_post',
  );

  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    'href',
    'http://127.0.0.1:4173/training',
  );
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute(
    'content',
    'http://127.0.0.1:4173/training',
  );
  const socialImage = page.locator('meta[property="og:image"]');
  await expect(socialImage).toHaveAttribute(
    'content',
    'http://127.0.0.1:4173/assets/brand/yfc-social-preview.png',
  );
  await expect(page.locator('meta[property="og:image:alt"]')).toHaveAttribute(
    'content',
    /тренировки, питание и прогресс/i,
  );

  const imageUrl = await socialImage.getAttribute('content');
  if (!imageUrl) throw new Error('Social preview URL is missing');
  const response = await request.get(imageUrl);
  expect(response.ok()).toBe(true);
  expect(response.headers()['content-type']).toContain('image/png');
  expect(
    await page.evaluate(
      (url) =>
        new Promise<{ width: number; height: number }>((resolve, reject) => {
          const image = new Image();
          image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
          image.onerror = () => reject(new Error('Social preview failed to load'));
          image.src = url;
        }),
      imageUrl,
    ),
  ).toEqual({ width: 1200, height: 630 });
});
