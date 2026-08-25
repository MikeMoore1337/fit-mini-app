import { expect, test, type Page } from '@playwright/test';

const captureEvidence =
  (
    globalThis as typeof globalThis & {
      process?: { env?: Record<string, string | undefined> };
    }
  ).process?.env?.YFC_CAPTURE_TASK_73 === '1';
const screenshotRoot = '../.artifacts/screenshots/task-73/final';

async function setStoredTheme(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((value) => localStorage.setItem('app-theme', value), theme);
}

async function expectNoHorizontalOverflow(page: Page, width: number) {
  expect(
    await page.evaluate(() => ({
      content: document.documentElement.scrollWidth,
      viewport: window.innerWidth,
    })),
  ).toEqual({ content: width, viewport: width });
}

async function expectLandingReady(page: Page) {
  await expect(
    page.getByRole('heading', { level: 1, name: 'Знайте, что делать сегодня.' }),
  ).toBeVisible();
  const heroImage = page.locator('.landing-hero-proof img');
  await expect(heroImage).toHaveJSProperty('complete', true);
  expect(
    await heroImage.evaluate((image) => (image as HTMLImageElement).naturalWidth),
  ).toBeGreaterThan(0);
}

test('landing keeps the approved hierarchy across the responsive and theme matrix', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });

  for (const theme of ['light', 'dark'] as const) {
    await setStoredTheme(page, theme);
    for (const viewport of [
      { width: 1440, height: 900 },
      { width: 1280, height: 900 },
      { width: 1024, height: 900 },
      { width: 768, height: 900 },
      { width: 430, height: 932 },
      { width: 390, height: 844 },
      { width: 360, height: 800 },
    ]) {
      await page.setViewportSize(viewport);
      await page.goto('/');

      await expect(page.locator('html')).toHaveAttribute('data-color-scheme', theme);
      await expect(
        page.getByRole('heading', { level: 1, name: 'Знайте, что делать сегодня.' }),
      ).toBeVisible();
      await expect(page.getByRole('link', { name: 'Открыть приложение' }).first()).toHaveAttribute(
        'href',
        '/app',
      );
      await expect(page.locator('.landing-hero-proof img')).toHaveJSProperty('complete', true);
      await expect(page.locator('.landing-hero-proof img')).toHaveClass(/is-loaded/);
      await expectNoHorizontalOverflow(page, viewport.width);

      const bounds = await page.evaluate(() => {
        const rectangle = (selector: string) => {
          const value = document.querySelector<HTMLElement>(selector)!.getBoundingClientRect();
          return { top: value.top, bottom: value.bottom, left: value.left, right: value.right };
        };
        return {
          header: rectangle('.landing-header'),
          hero: rectangle('.landing-hero'),
          primary: rectangle('.landing-hero__copy .landing-button'),
          proof: rectangle('.landing-hero-proof'),
          secondary: rectangle('.landing-hero__continuation .landing-button'),
          capabilities: rectangle('.landing-capabilities'),
        };
      });
      expect(bounds.header.left).toBeGreaterThanOrEqual(0);
      expect(bounds.header.right).toBeLessThanOrEqual(viewport.width);
      expect(bounds.capabilities.top).toBeGreaterThanOrEqual(bounds.hero.bottom - 1);
      expect(bounds.primary.right - bounds.primary.left).toBeCloseTo(
        bounds.secondary.right - bounds.secondary.left,
        0,
      );

      if (viewport.width <= 680) {
        expect(bounds.primary.bottom).toBeLessThanOrEqual(bounds.proof.top);
        expect(bounds.proof.top).toBeLessThan(viewport.height);
        expect(bounds.secondary.top).toBeGreaterThanOrEqual(bounds.proof.bottom);
      }

      const heroResources = await page.evaluate(() =>
        performance
          .getEntriesByType('resource')
          .map((entry) => entry.name)
          .filter((name) => /landing-(today-desktop|workout-mobile)-/.test(name)),
      );
      await expect(page.locator('.landing-hero-proof img')).toHaveCount(1);
      expect(
        await page
          .locator('.landing-hero-proof img')
          .evaluate((image) => (image as HTMLImageElement).currentSrc),
      ).toContain(viewport.width <= 680 ? `mobile-${theme}` : `desktop-${theme}`);
      expect(
        heroResources.some((resource) =>
          resource.includes(viewport.width <= 680 ? `mobile-${theme}` : `desktop-${theme}`),
        ),
      ).toBe(true);
      expect(
        await page.evaluate(() =>
          performance
            .getEntriesByType('resource')
            .every((entry) => !/telegram.*(sdk|web-app)/i.test(entry.name)),
        ),
      ).toBe(true);

      if (viewport.width === 1440) {
        const refinementStyles = await page.evaluate(() => {
          const root = document.querySelector<HTMLElement>('.landing-page')!;
          const workflow = document.querySelector<HTMLElement>('.landing-workflow ol')!;
          const workflowItems = [...workflow.querySelectorAll<HTMLElement>('li')];
          const audienceButtons = [
            ...document.querySelectorAll<HTMLElement>('.landing-audience .landing-button'),
          ];
          const platformBoundary = document.querySelector<HTMLElement>(
            '.landing-platforms__boundary',
          )!;
          const boundaryStyle = getComputedStyle(platformBoundary);
          const primary = root.querySelector<HTMLElement>(
            '.landing-hero__primary .landing-button',
          )!;
          const heading = root.querySelector<HTMLElement>('.landing-hero h1')!;
          const demoRow = root.querySelector<HTMLElement>('.landing-demo-list > a')!;
          const privacy = root.querySelector<HTMLElement>('.landing-privacy')!;
          const contact = root.querySelector<HTMLElement>('.landing-contact')!;
          const primaryStyle = getComputedStyle(primary);
          const selectionStyle = getComputedStyle(heading, '::selection');
          const headingStyle = getComputedStyle(heading);
          return {
            primaryBackground: primaryStyle.backgroundColor,
            primaryColor: primaryStyle.color,
            audienceBackgrounds: audienceButtons.map(
              (button) => getComputedStyle(button).backgroundColor,
            ),
            workflowBorderLeft: Number.parseFloat(getComputedStyle(workflow).borderLeftWidth),
            workflowBorderRight: Number.parseFloat(getComputedStyle(workflow).borderRightWidth),
            workflowInternalBorder: Number.parseFloat(
              getComputedStyle(workflowItems[0]!).borderRightWidth,
            ),
            workflowPaddings: workflowItems.map((item) =>
              Number.parseFloat(getComputedStyle(item).paddingLeft),
            ),
            platformBottom: Number.parseFloat(boundaryStyle.borderBottomWidth),
            platformRight: Number.parseFloat(boundaryStyle.borderRightWidth),
            selectionBackground: selectionStyle.backgroundColor,
            selectionColor: selectionStyle.color,
            headingLineHeight: Number.parseFloat(headingStyle.lineHeight),
            headingFontSize: Number.parseFloat(headingStyle.fontSize),
            demoPaddingLeft: Number.parseFloat(getComputedStyle(demoRow).paddingLeft),
            demoPaddingRight: Number.parseFloat(getComputedStyle(demoRow).paddingRight),
            privacyBottomBorder: Number.parseFloat(getComputedStyle(privacy).borderBottomWidth),
            contactTopBorder: Number.parseFloat(getComputedStyle(contact).borderTopWidth),
          };
        });
        expect(refinementStyles.audienceBackgrounds).toHaveLength(2);
        expect(
          refinementStyles.audienceBackgrounds.every(
            (background) => background === refinementStyles.primaryBackground,
          ),
        ).toBe(true);
        expect(refinementStyles.workflowBorderLeft).toBe(0);
        expect(refinementStyles.workflowBorderRight).toBe(0);
        expect(refinementStyles.workflowInternalBorder).toBeGreaterThanOrEqual(1);
        expect(Math.min(...refinementStyles.workflowPaddings)).toBeGreaterThanOrEqual(28);
        expect(refinementStyles.platformBottom).toBeGreaterThanOrEqual(1);
        expect(refinementStyles.platformRight).toBeGreaterThanOrEqual(1);
        expect(refinementStyles.selectionBackground).toBe(refinementStyles.primaryBackground);
        expect(refinementStyles.selectionColor).toBe(refinementStyles.primaryColor);
        expect(refinementStyles.headingLineHeight).toBeGreaterThanOrEqual(
          refinementStyles.headingFontSize,
        );
        expect(refinementStyles.demoPaddingLeft).toBe(refinementStyles.demoPaddingRight);
        expect(refinementStyles.demoPaddingLeft).toBeGreaterThanOrEqual(28);
        expect(refinementStyles.privacyBottomBorder).toBe(0);
        expect(refinementStyles.contactTopBorder).toBeGreaterThanOrEqual(1);
      }

      const footer = page.locator('.landing-footer');
      await footer.scrollIntoViewIfNeeded();
      const footerBounds = await footer.boundingBox();
      expect(footerBounds?.x).toBeGreaterThanOrEqual(0);
      expect((footerBounds?.x ?? 0) + (footerBounds?.width ?? 0)).toBeLessThanOrEqual(
        viewport.width,
      );
    }
  }
});

test('real product proof reserves space, loads lazily and degrades without blocking conversion', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  let releaseNutrition: (() => void) | undefined;
  const nutritionGate = new Promise<void>((resolve) => {
    releaseNutrition = resolve;
  });
  await page.route('**/assets/product/landing-nutrition-desktop-light.png', async (route) => {
    await nutritionGate;
    await route.continue();
  });
  await page.route('**/assets/product/landing-trainer-desktop-light.png', (route) => route.abort());
  await page.goto('/');

  expect(
    await page.evaluate(() =>
      performance
        .getEntriesByType('resource')
        .some((entry) => entry.name.includes('landing-nutrition-desktop-light.png')),
    ),
  ).toBe(false);

  const nutritionFrame = page.locator('.landing-showcase-compact').first().locator('figure');
  const reserved = await nutritionFrame.boundingBox();
  await nutritionFrame.scrollIntoViewIfNeeded();
  const nutritionImage = nutritionFrame.locator('img');
  await expect(nutritionImage).not.toHaveClass(/is-loaded/);
  await expect(nutritionFrame.getByText('Экран питания временно недоступен.')).toBeVisible();
  releaseNutrition?.();
  await expect(nutritionImage).toHaveJSProperty('complete', true);
  await expect(nutritionImage).toHaveClass(/is-loaded/);
  expect(
    await nutritionImage.evaluate((image) => (image as HTMLImageElement).naturalWidth),
  ).toBeGreaterThan(0);
  const loaded = await nutritionFrame.boundingBox();
  expect(loaded?.width).toBeCloseTo(reserved?.width ?? 0, 0);
  expect(loaded?.height).toBeCloseTo(reserved?.height ?? 0, 0);

  const trainerFrame = page.locator('.landing-proof-frame--trainer');
  await trainerFrame.scrollIntoViewIfNeeded();
  await expect(trainerFrame.getByText('Экран кабинета тренера временно недоступен.')).toBeVisible();

  const finalAction = page.getByRole('link', { name: 'Открыть приложение' }).last();
  await finalAction.scrollIntoViewIfNeeded();
  await expect(finalAction).toHaveAttribute('href', '/app');
  await expectNoHorizontalOverflow(page, 1280);
});

test('keyboard, menu, FAQ and canonical demo actions stay operable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const skipLink = page.getByRole('link', { name: 'К содержимому' });
  await skipLink.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#landing-content')).toBeFocused();

  const menu = page.getByRole('button', { name: 'Открыть меню' });
  await menu.click();
  await expect(page.getByRole('navigation', { name: 'Навигация по странице' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(menu).toBeFocused();
  await expect(menu).toHaveAttribute('aria-expanded', 'false');

  await page.locator('#faq').scrollIntoViewIfNeeded();
  const question = page.getByText('Telegram обязателен?', { exact: true });
  await question.click();
  await expect(page.getByText(/доступны в браузере/i)).toBeVisible();

  await expect(page.getByRole('link', { name: /пройдите тренировку/i })).toHaveAttribute(
    'href',
    '/demo?cabinet=1&scenario=self_training&section=today',
  );
  await expect(page.getByRole('link', { name: /добавьте питание/i })).toHaveAttribute(
    'href',
    '/demo?cabinet=1&scenario=nutrition&section=nutrition',
  );
  await expect(page.getByRole('link', { name: /посмотрите кабинет тренера/i })).toHaveAttribute(
    'href',
    '/demo?cabinet=1&scenario=trainer&section=trainer',
  );
  await expect(page.getByRole('link', { name: 'Приватность и данные' })).toHaveAttribute(
    'href',
    '#privacy',
  );
  await page.getByRole('link', { name: 'Приватность и данные' }).click();
  await expect(page).toHaveURL(/#privacy$/);
  await expect(page.locator('#privacy')).toBeInViewport();
});

test('captures the owner-review evidence packet when requested', async ({ page }) => {
  if (!captureEvidence) return;

  await page.emulateMedia({ reducedMotion: 'reduce' });
  await setStoredTheme(page, 'light');
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await expectLandingReady(page);
  await page.screenshot({ path: `${screenshotRoot}/desktop-1440-light-hero.png` });

  await page.locator('.landing-hero h1').evaluate((heading) => {
    const selection = window.getSelection();
    selection?.removeAllRanges();
    const range = document.createRange();
    range.selectNodeContents(heading);
    selection?.addRange(range);
  });
  await page.screenshot({ path: `${screenshotRoot}/desktop-selection-light.png` });
  await page.evaluate(() => window.getSelection()?.removeAllRanges());

  const primaryAction = page.getByRole('link', { name: 'Открыть приложение' }).first();
  await primaryAction.hover();
  await page.screenshot({ path: `${screenshotRoot}/desktop-1440-light-hover.png` });

  await page.locator('.landing-workflow').screenshot({
    path: `${screenshotRoot}/desktop-workflow-refined.png`,
  });
  await page.locator('.landing-audience').screenshot({
    path: `${screenshotRoot}/desktop-audience-lime-actions.png`,
  });
  await page.locator('.landing-platforms').screenshot({
    path: `${screenshotRoot}/desktop-platform-boundary.png`,
  });
  await page.locator('.landing-demo').screenshot({
    path: `${screenshotRoot}/desktop-demo-symmetric-insets.png`,
  });
  await page.locator('.landing-privacy').screenshot({
    path: `${screenshotRoot}/desktop-privacy-public.png`,
  });
  const contact = page.locator('.landing-contact');
  await contact.evaluate((element) =>
    window.scrollTo({ top: element.getBoundingClientRect().top + window.scrollY - 120 }),
  );
  await page.screenshot({ path: `${screenshotRoot}/desktop-contact-without-extra-rule.png` });

  const showcase = page.locator('#product');
  for (const image of await showcase.locator('img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect(image).toHaveJSProperty('complete', true);
  }
  await showcase.screenshot({ path: `${screenshotRoot}/desktop-product-proof-light.png` });

  const faq = page.locator('#faq');
  await faq.scrollIntoViewIfNeeded();
  const firstSummary = faq.locator('summary').first();
  await firstSummary.click();
  await firstSummary.focus();
  await page.keyboard.press('Tab');
  await expect(faq.locator('summary').nth(1)).toBeFocused();
  await faq.screenshot({ path: `${screenshotRoot}/desktop-faq-focus-long-copy.png` });

  for (const path of ['/training', '/nutrition', '/knowledge']) {
    await page.goto(path);
    await expect(page.locator('.public-hero h1')).toBeVisible();
    await page.screenshot({
      path: `${screenshotRoot}/desktop-public-${path.slice(1)}-compact-hero.png`,
    });
  }

  await setStoredTheme(page, 'dark');
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await expectLandingReady(page);
  await page.locator('.landing-hero h1').evaluate((heading) => {
    const selection = window.getSelection();
    selection?.removeAllRanges();
    const range = document.createRange();
    range.selectNodeContents(heading);
    selection?.addRange(range);
  });
  await page.screenshot({ path: `${screenshotRoot}/desktop-selection-dark.png` });
  await page.evaluate(() => window.getSelection()?.removeAllRanges());

  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${screenshotRoot}/mobile-390-dark-tma-equivalent-hero.png` });

  await setStoredTheme(page, 'light');
  await page.goto('/');
  await expectLandingReady(page);
  await page.screenshot({ path: `${screenshotRoot}/mobile-390-light-hero.png` });
  const mobileFaq = page.locator('#faq');
  await mobileFaq.scrollIntoViewIfNeeded();
  for (const summary of await mobileFaq.locator('summary').all()) await summary.click();
  await mobileFaq.evaluate((element) =>
    window.scrollTo({ top: element.getBoundingClientRect().top + window.scrollY }),
  );
  await page.locator('body').evaluate((body) => {
    body.tabIndex = -1;
    body.focus();
  });
  await expect(page.getByRole('link', { name: 'К содержимому' })).not.toBeFocused();
  await page.screenshot({ path: `${screenshotRoot}/mobile-390-light-faq-long-copy.png` });
});
