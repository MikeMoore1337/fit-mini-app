import { expect, test, type Page } from '@playwright/test';

const captureEvidence =
  (
    globalThis as typeof globalThis & {
      process?: { env?: Record<string, string | undefined> };
    }
  ).process?.env?.YFC_CAPTURE_TASK_73A === '1';
const screenshotRoot = '../.artifacts/screenshots/task-73a/final';

async function openLanding(page: Page, theme: 'light' | 'dark') {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.evaluate((value) => localStorage.setItem('app-theme', value), theme);
  await page.reload({ waitUntil: 'domcontentloaded' });
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
  for (const image of await page.locator('.landing-hero-scene img').all()) {
    await expect(image).toHaveJSProperty('complete', true);
    expect(
      await image.evaluate((element) => (element as HTMLImageElement).naturalWidth),
    ).toBeGreaterThan(0);
    await image.evaluate((element) => (element as HTMLImageElement).decode());
  }
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
}

async function loadAllProductProofs(page: Page) {
  for (const image of await page.locator('.landing-product-image img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect(image).toHaveJSProperty('complete', true);
    expect(
      await image.evaluate((element) => (element as HTMLImageElement).naturalWidth),
    ).toBeGreaterThan(0);
    await image.evaluate((element) => (element as HTMLImageElement).decode());
  }
  await page.evaluate(() => window.scrollTo(0, 0));
}

async function settleForScreenshot(page: Page) {
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    window.getSelection()?.removeAllRanges();
    window.scrollTo(0, 0);
  });
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
}

test('landing keeps a minimal premium product story across themes and viewports', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });

  for (const theme of ['light', 'dark'] as const) {
    for (const viewport of [
      { width: 1440, height: 1000 },
      { width: 1280, height: 900 },
      { width: 1024, height: 900 },
      { width: 768, height: 900 },
      // Layout viewport equivalent for the 1440px composition at 200% zoom.
      { width: 720, height: 900 },
      { width: 430, height: 932 },
      { width: 390, height: 844 },
      { width: 360, height: 800 },
    ]) {
      await page.setViewportSize(viewport);
      await openLanding(page, theme);
      await expectLandingReady(page);

      await expect(page.locator('html')).toHaveAttribute('data-color-scheme', theme);
      await expect(page.locator('h1')).toHaveCount(1);
      await expect(page.locator('.landing-core__features article')).toHaveCount(3);
      await expect(page.locator('.landing-trainer')).toBeVisible();
      await expect(page.locator('.landing-bento-card, .landing-system__card')).toHaveCount(0);
      await expect(page.getByRole('link', { name: 'Открыть приложение' }).first()).toHaveAttribute(
        'href',
        '/app',
      );
      await expect(page.getByRole('link', { name: 'Попробовать демо' })).toHaveAttribute(
        'href',
        '/demo?cabinet=1&scenario=self_training&section=today',
      );
      await expect(page.locator('.landing-hero-scene img')).toHaveCount(2);
      await expectNoHorizontalOverflow(page, viewport.width);

      const bounds = await page.evaluate(() => {
        const rectangle = (selector: string) => {
          const value = document.querySelector<HTMLElement>(selector)!.getBoundingClientRect();
          return { top: value.top, bottom: value.bottom, left: value.left, right: value.right };
        };
        return {
          header: rectangle('.landing-header'),
          hero: rectangle('.landing-hero'),
          primary: rectangle('.landing-hero__actions .landing-button'),
          secondary: rectangle('.landing-hero__actions .landing-button--secondary'),
          scene: rectangle('.landing-hero-scene'),
          device: rectangle('.landing-hero-device'),
          core: rectangle('.landing-core'),
          brand: rectangle('.public-shell__brand'),
          actions: rectangle('.public-shell__header-actions'),
          documentHeight: document.documentElement.scrollHeight,
        };
      });
      expect(bounds.header.left).toBeGreaterThanOrEqual(0);
      expect(bounds.header.right).toBeLessThanOrEqual(viewport.width);
      expect(bounds.core.top).toBeGreaterThanOrEqual(bounds.hero.bottom - 1);
      expect(bounds.core.top).toBeLessThanOrEqual(bounds.hero.bottom + 1);
      expect(bounds.primary.right).toBeLessThanOrEqual(viewport.width);
      expect(bounds.secondary.right).toBeLessThanOrEqual(viewport.width);
      expect(bounds.brand.right).toBeLessThanOrEqual(bounds.actions.left);
      await expect(page.locator('.landing-header .yfc-lockup__wordmark')).toBeVisible();

      if (viewport.width <= 680) {
        expect(bounds.primary.bottom).toBeLessThanOrEqual(bounds.scene.top);
        expect(bounds.secondary.bottom).toBeLessThanOrEqual(bounds.scene.top);
        expect(bounds.scene.top).toBeLessThan(viewport.height * 0.8);
        expect(bounds.documentHeight).toBeLessThanOrEqual(6800);
      } else if (viewport.width >= 1280) {
        expect(bounds.documentHeight).toBeLessThanOrEqual(5200);
      }

      const athlete = page.locator('.landing-athlete-image img');
      await expect(athlete).toHaveAttribute('width', '1280');
      await expect(athlete).toHaveAttribute('height', '1171');
      expect(await athlete.evaluate((image) => (image as HTMLImageElement).currentSrc)).toMatch(
        /landing-athlete-deadlift-cutout-(640|960|1280)\.webp$/,
      );

      expect(
        await page.evaluate(() =>
          performance
            .getEntriesByType('resource')
            .every(
              (entry) =>
                !/telegram.*(sdk|web-app)/i.test(entry.name) &&
                !/candidate-a-deadlift.*\.png/i.test(entry.name),
            ),
        ),
      ).toBe(true);

      if (viewport.width === 1440) {
        const directionStyles = await page.evaluate(() => {
          const hero = document.querySelector<HTMLElement>('.landing-hero')!;
          const heading = document.querySelector<HTMLElement>('.landing-hero h1')!;
          const primary = document.querySelector<HTMLElement>(
            '.landing-hero__actions .landing-button',
          )!;
          const secondary = document.querySelector<HTMLElement>(
            '.landing-hero__actions .landing-button--secondary',
          )!;
          const header = document.querySelector<HTMLElement>('.public-shell__header')!;
          const device = document.querySelector<HTMLElement>('.landing-hero-device')!;
          const signals = document.querySelector<HTMLElement>('.landing-hero-signals')!;
          const signalIcon = signals.querySelector<SVGElement>('svg')!;
          const energy = document.querySelector<HTMLElement>('.landing-energy-path')!;
          const desktopFlow = energy.querySelector<SVGGElement>('.energy-flow__scene--desktop')!;
          const filament = desktopFlow.querySelector<SVGPathElement>(
            '.energy-flow__filament--primary-a',
          )!;
          const secondaryFilament = desktopFlow.querySelector<SVGPathElement>(
            '.energy-flow__filament--support-d',
          )!;
          const filaments = Array.from(
            desktopFlow.querySelectorAll<SVGPathElement>('.energy-flow__filament'),
          );
          const volume = energy.querySelector<SVGGElement>('.energy-flow__volume')!;
          const athleteFrame = document.querySelector<HTMLElement>('.landing-athlete-frame')!;
          const coreMobile = document.querySelector<HTMLElement>('.landing-core__mobile')!;
          const trainerProof = document.querySelector<HTMLElement>('.landing-trainer__proof')!;
          const core = document.querySelector<HTMLElement>('.landing-core')!;
          const pathLength = filament.getTotalLength();
          const pathMatrix = filament.getScreenCTM()!;
          const secondaryBounds = secondary.getBoundingClientRect();
          const pathSamples = Array.from({ length: 161 }, (_, index) => {
            const point = filament.getPointAtLength((pathLength * index) / 160);
            return new DOMPoint(point.x, point.y).matrixTransform(pathMatrix);
          });
          const endpoint = pathSamples.at(-1)!;
          return {
            heroHeight: hero.getBoundingClientRect().height,
            headingLineHeight: Number.parseFloat(getComputedStyle(heading).lineHeight),
            headingFontSize: Number.parseFloat(getComputedStyle(heading).fontSize),
            headingFontFamily: getComputedStyle(heading).fontFamily,
            primaryBackground: getComputedStyle(primary).backgroundColor,
            secondaryBackground: getComputedStyle(secondary).backgroundColor,
            secondaryBorderWidth: Number.parseFloat(getComputedStyle(secondary).borderLeftWidth),
            headerBackground: getComputedStyle(header).backgroundColor,
            deviceWidth: device.getBoundingClientRect().width,
            devicePadding: Number.parseFloat(getComputedStyle(device).paddingLeft),
            signalsBackground: getComputedStyle(signals).backgroundColor,
            signalsBackdrop: getComputedStyle(signals).backdropFilter,
            signalIconColor: getComputedStyle(signalIcon).color,
            energyLayer: Number.parseFloat(getComputedStyle(energy).zIndex),
            athleteLayer: Number.parseFloat(getComputedStyle(athleteFrame).zIndex),
            deviceLayer: Number.parseFloat(getComputedStyle(device).zIndex),
            energyPointerEvents: getComputedStyle(energy).pointerEvents,
            energyAriaHidden: energy.getAttribute('aria-hidden'),
            filamentCount: filaments.length,
            uniqueTrajectoryCount: new Set(filaments.map((path) => path.getAttribute('d'))).size,
            filamentsHaveNoFill: filaments.every((path) => path.getAttribute('fill') === 'none'),
            fadeMask: volume.getAttribute('mask'),
            filterCount: energy.querySelectorAll('filter').length,
            primaryFilamentWidth: Number.parseFloat(getComputedStyle(filament).strokeWidth),
            secondaryFilamentWidth: Number.parseFloat(
              getComputedStyle(secondaryFilament).strokeWidth,
            ),
            trajectoryCrossesDemo: pathSamples.some(
              (point) =>
                point.x >= secondaryBounds.left &&
                point.x <= secondaryBounds.right &&
                point.y >= secondaryBounds.top &&
                point.y <= secondaryBounds.bottom,
            ),
            trajectoryEndX: endpoint.x,
            deviceRight: device.getBoundingClientRect().right,
            athleteLift: new DOMMatrix(getComputedStyle(athleteFrame).transform).m42,
            coreMobilePadding: Number.parseFloat(getComputedStyle(coreMobile).paddingLeft),
            trainerBorder: Number.parseFloat(getComputedStyle(trainerProof).borderLeftWidth),
            coreHeight: core.getBoundingClientRect().height,
          };
        });
        expect(directionStyles.heroHeight).toBeLessThanOrEqual(740);
        expect(directionStyles.headingLineHeight).toBeGreaterThanOrEqual(
          directionStyles.headingFontSize * 0.92,
        );
        expect(directionStyles.headingFontFamily).toMatch(/^Inter,/i);
        expect(directionStyles.headingFontFamily).not.toMatch(/Georgia|Times New Roman/i);
        expect(directionStyles.primaryBackground).not.toBe(directionStyles.secondaryBackground);
        expect(directionStyles.secondaryBorderWidth).toBeGreaterThanOrEqual(1);
        expect(directionStyles.headerBackground).toBe('rgba(0, 0, 0, 0)');
        expect(directionStyles.deviceWidth).toBeGreaterThanOrEqual(200);
        expect(directionStyles.devicePadding).toBeLessThanOrEqual(3);
        expect(directionStyles.signalsBackground).toBe('rgba(0, 0, 0, 0)');
        expect(directionStyles.signalsBackdrop).toBe('none');
        expect(directionStyles.signalIconColor).toBe(
          theme === 'light' ? 'rgb(86, 122, 13)' : 'rgb(182, 242, 56)',
        );
        expect(directionStyles.energyLayer).toBeLessThan(directionStyles.athleteLayer);
        expect(directionStyles.energyLayer).toBeLessThan(directionStyles.deviceLayer);
        expect(directionStyles.energyPointerEvents).toBe('none');
        expect(directionStyles.energyAriaHidden).toBe('true');
        expect(directionStyles.filamentCount).toBeGreaterThanOrEqual(7);
        expect(directionStyles.filamentCount).toBeLessThanOrEqual(14);
        expect(directionStyles.uniqueTrajectoryCount).toBe(directionStyles.filamentCount);
        expect(directionStyles.filamentsHaveNoFill).toBe(true);
        expect(directionStyles.fadeMask).toMatch(/^url\(#energy-flow-fade-/);
        expect(directionStyles.filterCount).toBeLessThanOrEqual(2);
        expect(directionStyles.primaryFilamentWidth).toBeGreaterThanOrEqual(1.5);
        expect(directionStyles.primaryFilamentWidth).toBeLessThanOrEqual(2.5);
        expect(directionStyles.secondaryFilamentWidth).toBeGreaterThanOrEqual(0.5);
        expect(directionStyles.secondaryFilamentWidth).toBeLessThanOrEqual(1.5);
        expect(directionStyles.trajectoryCrossesDemo).toBe(true);
        expect(directionStyles.trajectoryEndX).toBeGreaterThan(directionStyles.deviceRight);
        expect(directionStyles.athleteLift).toBeLessThanOrEqual(-40);
        expect(directionStyles.coreMobilePadding).toBeLessThanOrEqual(3);
        expect(directionStyles.trainerBorder).toBeLessThanOrEqual(2);
        expect(directionStyles.coreHeight).toBeGreaterThanOrEqual(800);
      }

      if (viewport.width <= 430) {
        const mobileFlow = await page.evaluate(() => {
          const energy = document.querySelector<HTMLElement>('.landing-energy-path')!;
          const mobileScene = energy.querySelector<SVGGElement>('.energy-flow__scene--mobile')!;
          const filaments = Array.from(
            mobileScene.querySelectorAll<SVGPathElement>('.energy-flow__filament'),
          );
          const widths = filaments.map((filament) =>
            Number.parseFloat(getComputedStyle(filament).strokeWidth),
          );
          return {
            visibleCount: filaments.length,
            maxWidth: Math.max(...widths),
            ambientOpacity: Number.parseFloat(
              getComputedStyle(mobileScene.querySelector<SVGPathElement>('.energy-flow__ambient')!)
                .opacity,
            ),
            glowCount: Array.from(
              mobileScene.querySelectorAll<SVGPathElement>('.energy-flow__glow'),
            ).filter((path) => getComputedStyle(path).display !== 'none').length,
          };
        });
        expect(mobileFlow.visibleCount).toBeGreaterThanOrEqual(7);
        expect(mobileFlow.visibleCount).toBeLessThanOrEqual(10);
        expect(mobileFlow.maxWidth).toBeLessThanOrEqual(1.5);
        expect(mobileFlow.ambientOpacity).toBeLessThanOrEqual(0.04);
        expect(mobileFlow.glowCount).toBeLessThanOrEqual(1);
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

test('media failures preserve the story and product proofs reserve their layout', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  let releaseDesktop: (() => void) | undefined;
  const desktopGate = new Promise<void>((resolve) => {
    releaseDesktop = resolve;
  });
  await page.route('**/assets/marketing/landing-athlete-deadlift-*', (route) => route.abort());
  await page.route('**/assets/product/landing-today-desktop-light.png', async (route) => {
    await desktopGate;
    await route.continue();
  });
  await page.route('**/assets/product/landing-trainer-desktop-light.png', (route) => route.abort());
  await openLanding(page, 'light');

  await expect(page.getByText(/силовая тренировка остаётся контекстом страницы/i)).toBeVisible();
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Открыть приложение' }).first()).toHaveAttribute(
    'href',
    '/app',
  );

  const desktopFrame = page.locator('.landing-core__desktop');
  const reserved = await desktopFrame.boundingBox();
  await desktopFrame.scrollIntoViewIfNeeded();
  const desktopImage = desktopFrame.locator('img');
  await expect(desktopImage).not.toHaveClass(/is-loaded/);
  await expect(desktopFrame.getByText('Desktop proof временно недоступен.')).toBeVisible();
  releaseDesktop?.();
  await expect(desktopImage).toHaveJSProperty('complete', true);
  await expect(desktopImage).toHaveClass(/is-loaded/);
  await expect(desktopFrame.getByText('Desktop proof временно недоступен.')).toBeHidden();
  const loaded = await desktopFrame.boundingBox();
  expect(loaded?.width).toBeCloseTo(reserved?.width ?? 0, 0);
  expect(loaded?.height).toBeCloseTo(reserved?.height ?? 0, 0);

  const trainerFrame = page.locator('.landing-trainer__proof');
  await trainerFrame.scrollIntoViewIfNeeded();
  await expect(trainerFrame.getByText('Экран кабинета тренера временно недоступен.')).toBeVisible();
  await expectNoHorizontalOverflow(page, 1280);
});

test('keyboard, menu, FAQ and canonical public actions stay operable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openLanding(page, 'light');

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

  const knowledgeDetails = page.locator('.landing-assurance__details > details').first();
  await knowledgeDetails.locator('summary').click();
  await expect(
    knowledgeDetails.getByRole('link', { name: 'Тренировки и программы' }),
  ).toBeVisible();

  const mobileReadability = await page.evaluate(() => {
    const linkSelectors = [
      '.landing-core__features a',
      '.landing-core__self-link',
      '.landing-assurance__details nav a',
      '.landing-footer nav a',
    ];
    const textSelectors = [
      '.landing-core__features p',
      '.landing-trainer__copy > p:not(.landing-kicker)',
      '.landing-start__steps p',
      '.landing-faq-list details > p',
      '.landing-assurance__details details > div > p',
      '.landing-contact > div > p:not(.landing-kicker)',
      '.landing-footer__brand p',
      '.landing-footer__privacy p',
    ];
    const numberSelectors = [
      '.landing-core__feature-label > span',
      '.landing-start__steps small',
      '.landing-start__demo nav > a > span',
    ];
    return {
      linkHeights: linkSelectors.flatMap((selector) =>
        [...document.querySelectorAll<HTMLElement>(selector)].map(
          (element) => element.getBoundingClientRect().height,
        ),
      ),
      textSizes: textSelectors.flatMap((selector) =>
        [...document.querySelectorAll<HTMLElement>(selector)].map((element) =>
          Number.parseFloat(getComputedStyle(element).fontSize),
        ),
      ),
      numberSizes: numberSelectors.flatMap((selector) =>
        [...document.querySelectorAll<HTMLElement>(selector)].map((element) =>
          Number.parseFloat(getComputedStyle(element).fontSize),
        ),
      ),
    };
  });
  expect(mobileReadability.linkHeights.length).toBeGreaterThan(0);
  expect(Math.min(...mobileReadability.linkHeights)).toBeGreaterThanOrEqual(44);
  expect(Math.min(...mobileReadability.textSizes)).toBeGreaterThanOrEqual(13);
  expect(Math.min(...mobileReadability.numberSizes)).toBeGreaterThanOrEqual(15);

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
  await page.getByRole('link', { name: 'Приватность и данные' }).click();
  await expect(page).toHaveURL(/#privacy$/);
  await expect(page.locator('#privacy')).toBeInViewport();
});

test('motion has an immediate reduced-motion final state', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await openLanding(page, 'dark');
  await expectLandingReady(page);

  const motionState = await page.evaluate(() => {
    const path = document.querySelector<SVGPathElement>('.landing-energy-path path')!;
    const proof = document.querySelector<HTMLElement>('.landing-core__desktop')!;
    const athlete = document.querySelector<HTMLElement>('.landing-athlete-frame')!;
    const product = document.querySelector<HTMLElement>('.landing-hero-device')!;
    return {
      pathOffset: getComputedStyle(path).strokeDashoffset,
      pathAnimation: getComputedStyle(path).animationName,
      proofOpacity: getComputedStyle(proof).opacity,
      proofTransform: getComputedStyle(proof).transform,
      athleteAnimation: getComputedStyle(athlete).animationName,
      productAnimation: getComputedStyle(product).animationName,
    };
  });
  expect(motionState.pathOffset).toMatch(/^0(px)?$/);
  expect(motionState.pathAnimation).toBe('none');
  expect(motionState.proofOpacity).toBe('1');
  expect(motionState.proofTransform).toMatch(/^(none|matrix\(1, 0, 0, 1, 0, 0\))$/);
  expect(motionState.athleteAnimation).toBe('none');
  expect(motionState.productAnimation).toBe('none');
});

test('captures the task 73A owner-review packet when requested', async ({ page, browser }) => {
  if (!captureEvidence) return;

  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const theme of ['light', 'dark'] as const) {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await openLanding(page, theme);
    await expectLandingReady(page);
    await settleForScreenshot(page);
    await page.screenshot({ path: `${screenshotRoot}/desktop-1440-${theme}-hero.png` });
    await loadAllProductProofs(page);
    await page.locator('#product').screenshot({
      path: `${screenshotRoot}/desktop-1440-${theme}-product.png`,
    });
    await page.locator('.landing-trainer').screenshot({
      path: `${screenshotRoot}/desktop-1440-${theme}-trainer.png`,
    });
    await settleForScreenshot(page);
    await page.screenshot({
      path: `${screenshotRoot}/desktop-1440-${theme}-full.png`,
      fullPage: true,
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await openLanding(page, theme);
    await expectLandingReady(page);
    await settleForScreenshot(page);
    await page.screenshot({ path: `${screenshotRoot}/mobile-390-${theme}-hero.png` });
    await loadAllProductProofs(page);
    await page.addStyleTag({ content: '.public-shell__skip-link { display: none !important; }' });
    await page.locator('#product').screenshot({
      path: `${screenshotRoot}/mobile-390-${theme}-product.png`,
    });
    await settleForScreenshot(page);
    await page.screenshot({
      path: `${screenshotRoot}/mobile-390-${theme}-full.png`,
      fullPage: true,
    });
  }

  const mobile360Context = await browser.newContext({
    viewport: { width: 360, height: 800 },
    deviceScaleFactor: 2,
  });
  const mobile360Page = await mobile360Context.newPage();
  await mobile360Page.emulateMedia({ reducedMotion: 'reduce' });
  await openLanding(mobile360Page, 'light');
  await expectLandingReady(mobile360Page);
  await expectNoHorizontalOverflow(mobile360Page, 360);
  await settleForScreenshot(mobile360Page);
  await mobile360Page.screenshot({
    path: `${screenshotRoot}/mobile-360-light-overflow-crop.png`,
  });
  await mobile360Context.close();
});
