import { expect, test, type Page } from '@playwright/test';

const canonicalSvgPaths = [
  '/assets/brand/favicon.svg',
  '/assets/brand/favicon-light.svg',
  '/assets/brand/favicon-dark.svg',
  '/assets/brand/yfc-logo-light.svg',
  '/assets/brand/yfc-logo-dark.svg',
  '/assets/brand/yfc-mark-light.svg',
  '/assets/brand/yfc-mark-dark.svg',
];

async function assertHeaderMark(page: Page, surface: 'light' | 'dark') {
  const mark = page.locator('.landing-header .landing-brand__mark');
  await expect(mark).toHaveAttribute('src', `/assets/brand/yfc-mark-${surface}.svg`);
  await expect(mark).toHaveAttribute('width', '36');
  await expect(mark).toHaveAttribute('height', '36');
  await expect(mark).toHaveAttribute('alt', '');
}

test('canonical brand assets render on light and dark public surfaces', async ({ page }) => {
  for (const viewport of [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'mobile', width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await page.evaluate(() => window.localStorage.removeItem('landing-theme'));
    await page.reload();
    await assertHeaderMark(page, 'light');
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);

    if (viewport.name === 'desktop') {
      await page.screenshot({ path: '../.artifacts/brand/landing-light-desktop.png' });
    }

    await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
    await assertHeaderMark(page, 'dark');
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);

    if (viewport.name === 'mobile') {
      await page.screenshot({ path: '../.artifacts/brand/landing-dark-mobile.png' });
    }
  }
});

test('favicon is canonical SVG and remains distinct at 16 and 32 pixels', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('link[rel="icon"]:not([media])')).toHaveAttribute(
    'href',
    '/assets/brand/favicon.svg',
  );
  await expect(
    page.locator('link[rel="icon"][media="(prefers-color-scheme: light)"]'),
  ).toHaveAttribute('href', '/assets/brand/favicon-light.svg');
  await expect(
    page.locator('link[rel="icon"][media="(prefers-color-scheme: dark)"]'),
  ).toHaveAttribute('href', '/assets/brand/favicon-dark.svg');
  await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveAttribute(
    'href',
    '/assets/brand/apple-touch-icon.png',
  );

  for (const assetPath of canonicalSvgPaths) {
    const source = await page.evaluate(async (path) => {
      const response = await fetch(path);
      return { body: await response.text(), ok: response.ok };
    }, assetPath);
    expect(source.ok).toBe(true);
    expect(source.body).not.toMatch(/(?:data:|<image\b|(?:href|src)="https?:\/\/|@font-face)/i);
  }

  await page.setViewportSize({ width: 720, height: 420 });
  await page.setContent(`
    <style>
      body { display: grid; gap: 20px; margin: 0; padding: 20px; background: #f1f3ec; }
      .dark { padding: 20px; background: #0d120f; }
      img { display: block; width: 180px; height: auto; }
    </style>
    <img src="/assets/brand/yfc-logo-light.svg" width="180" height="150" alt="Your Fitness Coach" />
    <div class="dark"><img src="/assets/brand/yfc-logo-dark.svg" width="180" height="150" alt="Your Fitness Coach" /></div>
  `);
  await expect(page.getByRole('img', { name: 'Your Fitness Coach' })).toHaveCount(2);
  await page.screenshot({ path: '../.artifacts/brand/logo-variants.png' });

  await page.setViewportSize({ width: 96, height: 64 });
  await page.setContent(`
    <style>
      body { display: flex; gap: 24px; align-items: center; margin: 8px; background: #0d120f; }
      img { display: block; }
    </style>
    <img src="/assets/brand/favicon-dark.svg" width="16" height="16" alt="" />
    <img src="/assets/brand/favicon-dark.svg" width="32" height="32" alt="" />
  `);
  await expect(page.locator('img')).toHaveCount(2);
  await page.screenshot({ path: '../.artifacts/brand/favicon-16-32-dark.png' });
});
