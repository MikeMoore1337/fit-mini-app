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
      expect(
        await page.evaluate(() => ({
          content: document.documentElement.scrollWidth,
          viewport: window.innerWidth,
        })),
      ).toEqual({ content: viewport.width, viewport: viewport.width });
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
  await expect(page.getByText(/15 августа 2026/i)).toBeVisible();
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
