import { expect, test, type Page } from '@playwright/test';

async function openCard(page: Page, title: string) {
  const card = page
    .getByRole('heading', { name: title, exact: true })
    .locator('xpath=ancestor::details[1]');
  await expect(card).not.toHaveAttribute('open');
  await card.locator(':scope > summary').click();
  await expect(card).toHaveAttribute('open');
}

type AppDestination = 'Сегодня' | 'План' | 'Прогресс' | 'Питание' | 'Упражнения' | 'Профиль';

async function openAppDestination(page: Page, destination: AppDestination) {
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  const desktopLabel = destination;
  const mobileLabel = destination === 'Профиль' ? 'Профиль и настройки' : destination;
  const directLink = page.getByRole('link', { name: desktopLabel, exact: true });
  for (let index = 0; index < (await directLink.count()); index += 1) {
    const candidate = directLink.nth(index);
    if (await candidate.isVisible()) {
      await candidate.click();
      return;
    }
  }
  await page.getByRole('button', { name: 'Ещё', exact: true }).click();
  await page.locator('#appMorePanel').getByRole('link', { name: mobileLabel, exact: true }).click();
}

test('логотип и кнопки в шапке имеют одинаковую высоту', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    const logo = await page.locator('.landing-header .landing-brand__mark').boundingBox();
    const themeButton = await page.locator('.landing-theme-toggle').boundingBox();
    const loginButton = await page.locator('.landing-button--compact').boundingBox();

    expect(logo).not.toBeNull();
    expect(themeButton).not.toBeNull();
    expect(loginButton).not.toBeNull();
    expect(logo?.height).toBe(44);
    expect(themeButton?.height).toBe(logo?.height);
    expect(loginButton?.height).toBe(logo?.height);

    const themeControl = page.getByRole('button', { name: /Включить .* тему/ });
    const loginControl = page.getByRole('link', { name: 'Войти' });
    await themeControl.hover();
    const themeHoverStyles = await themeControl.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        backgroundColor: styles.backgroundColor,
        borderColor: styles.borderColor,
        boxShadow: styles.boxShadow,
        transform: styles.transform,
      };
    });
    await loginControl.hover();
    const loginHoverStyles = await loginControl.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        backgroundColor: styles.backgroundColor,
        borderColor: styles.borderColor,
        boxShadow: styles.boxShadow,
        transform: styles.transform,
      };
    });
    expect(loginHoverStyles).toEqual(themeHoverStyles);

    const menuButton = page.getByRole('button', { name: 'Открыть меню' });
    if (viewport.width < 980) {
      await expect(menuButton).toBeVisible();
      await menuButton.hover();
      await expect
        .poll(() =>
          menuButton.evaluate((element) => {
            const styles = getComputedStyle(element);
            return {
              backgroundColor: styles.backgroundColor,
              borderColor: styles.borderColor,
              boxShadow: styles.boxShadow,
              transform: styles.transform,
            };
          }),
        )
        .toEqual(themeHoverStyles);
      await menuButton.click();
      await expect(page.getByRole('navigation', { name: 'Навигация по странице' })).toHaveClass(
        /is-open/,
      );
      await expect(page.getByRole('link', { name: 'Возможности', exact: true })).toBeVisible();
      await page.getByRole('link', { name: 'Возможности', exact: true }).click();
      await expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    } else {
      await expect(menuButton).toBeHidden();
    }
  }
});

test('мобильное меню не сохраняет активную заливку после касания', async ({ browser }) => {
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:4173',
    hasTouch: true,
    isMobile: true,
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
  await page.goto('/');

  expect(await page.evaluate(() => matchMedia('(hover: none)').matches)).toBe(true);
  const menuButton = page.getByRole('button', { name: 'Открыть меню' });
  const restStyles = await menuButton.evaluate((element) => {
    const styles = getComputedStyle(element);
    return {
      backgroundColor: styles.backgroundColor,
      borderColor: styles.borderColor,
      boxShadow: styles.boxShadow,
      color: styles.color,
    };
  });

  await menuButton.tap();
  const closeMenuButton = page.getByRole('button', { name: 'Закрыть меню' });
  await expect
    .poll(() =>
      closeMenuButton.evaluate((element) => {
        const styles = getComputedStyle(element);
        return {
          backgroundColor: styles.backgroundColor,
          borderColor: styles.borderColor,
          boxShadow: styles.boxShadow,
          color: styles.color,
        };
      }),
    )
    .toEqual(restStyles);

  await context.close();
});

test('первый экран лендинга объясняет продукт и не создаёт горизонтальный скролл', async ({
  page,
}) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(page.getByRole('heading', { name: /знайте, что делать сегодня/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /открыть приложение/i })).toBeVisible();
    await expect(page.getByLabel('Пример интерфейса тренировки на сегодня')).toBeVisible();
    await expect(page.getByText('Жим гантелей лёжа')).toBeVisible();
    await expect(page.getByText('+18%')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

test('вторичные CTA сохраняют контрастный текст при наведении в обеих темах', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');

  for (const scheme of ['light', 'dark'] as const) {
    await page.evaluate(() => window.localStorage.removeItem('app-theme'));
    await page.emulateMedia({ colorScheme: scheme, reducedMotion: 'reduce' });
    await page.reload();

    const expectedBackground = scheme === 'light' ? 'rgb(223, 230, 220)' : 'rgb(32, 42, 35)';
    const expectedText = scheme === 'light' ? 'rgb(23, 32, 24)' : 'rgb(242, 246, 239)';
    for (const link of [
      page.getByRole('link', { name: /Посмотреть, как всё устроено/ }),
      page.getByRole('link', { name: /Задать вопрос в Telegram/ }),
    ]) {
      await link.hover();
      await expect(link).toHaveCSS('background-color', expectedBackground);
      await expect(link).toHaveCSS('color', expectedText);
      await expect(link.locator('.landing-action__arrow')).toHaveCSS('color', expectedText);
    }
  }
});

test('лендинг остаётся адаптивным на контрольных ширинах', async ({ page }) => {
  for (const width of [360, 390, 430, 768, 1024, 1280, 1440]) {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 900 });
    await page.goto('/');

    const pageMetrics = await page.evaluate(() => ({
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
    }));
    expect(pageMetrics.documentWidth).toBeLessThanOrEqual(pageMetrics.viewport);
    expect(pageMetrics.bodyWidth).toBeLessThanOrEqual(pageMetrics.viewport);
    await expect(page.getByRole('link', { name: /открыть приложение/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Включить .* тему/ })).toBeInViewport();
    await expect(page.locator('.landing-platform-card')).toHaveCount(2);
  }
});

test('лендинг доступен с клавиатуры и содержит метаданные', async ({ page }) => {
  await page.goto('/');

  const skipLink = page.getByRole('link', { name: 'К содержимому' });
  await skipLink.focus();
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.locator('#landing-content')).toBeFocused();

  await expect(page).toHaveTitle(/тренировки, питание и прогресс в браузере и telegram/i);
  expect(await page.locator('meta[name="description"]').getAttribute('content')).toMatch(
    /фиксировать результаты.*ориентиры кбжу/i,
  );
  await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
    'content',
    /в браузере и telegram/i,
  );
  await expect(page.locator('meta[property="og:type"]')).toHaveAttribute('content', 'website');
});

test('блок возможностей показывает пользу спортсмену и инструменты тренеру', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(
      page.getByRole('heading', { name: /тренировки не должны жить в пяти разных местах/i }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /ведите своих клиентов в одном кабинете/i }),
    ).toBeVisible();
    await expect(page.getByText(/приглашайте клиентов, назначайте и корректируйте/i)).toBeVisible();
    if (viewport.width >= 768) {
      const sources = await page.locator('.landing-problem__sources').boundingBox();
      const result = await page.locator('.landing-problem__result').boundingBox();
      expect(sources).not.toBeNull();
      expect(result).not.toBeNull();
      expect(sources!.x + sources!.width).toBeLessThan(result!.x);
    } else {
      const sources = await page.locator('.landing-problem__sources').boundingBox();
      const result = await page.locator('.landing-problem__result').boundingBox();
      expect(sources).not.toBeNull();
      expect(result).not.toBeNull();
      expect(sources!.y + sources!.height).toBeLessThan(result!.y);
    }

    const featureCards = page.locator('.landing-feature');
    for (const card of await featureCards.all()) {
      await expect(card).toHaveCSS('justify-content', 'flex-start');
    }
    if (viewport.width === 1440) {
      const metaBoxes = await featureCards.locator('.landing-feature__meta').evaluateAll((items) =>
        items.map((item) => {
          const box = item.getBoundingClientRect();
          return { x: box.x, y: box.y };
        }),
      );
      expect(metaBoxes).toHaveLength(6);
      const firstRow = metaBoxes.slice(0, 2).map(({ y }) => y);
      expect(Math.max(...firstRow)).toBeLessThanOrEqual(Math.min(...firstRow) + 1);
      expect(Math.max(...metaBoxes.slice(2, 5).map(({ y }) => y))).toBeLessThanOrEqual(
        Math.min(...metaBoxes.slice(2, 5).map(({ y }) => y)) + 1,
      );
    }
    if (viewport.width === 390) {
      const problemVisual = await page.locator('.landing-problem__visual').boundingBox();
      const problemIcon = await page
        .locator('.landing-problem__result .landing-flow-icon')
        .boundingBox();
      expect(problemVisual).not.toBeNull();
      expect(problemIcon).not.toBeNull();
      expect(
        Math.abs(
          problemIcon!.x + problemIcon!.width / 2 - (problemVisual!.x + problemVisual!.width / 2),
        ),
      ).toBeLessThanOrEqual(1);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

test('сценарий и платформы остаются понятными на разных экранах', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    await expect(page.locator('.landing-workflow li')).toHaveCount(5);
    await expect(page.getByRole('heading', { name: 'Откройте веб-приложение' })).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Выберите свой путь', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', {
        name: /открывайте на компьютере или смартфоне.*telegram.*когда удобнее/i,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Открывайте на компьютере или смартфоне', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: /продолжайте в telegram mini app/i }),
    ).toBeVisible();
    await expect(page.getByText(/для самостоятельных тренировок telegram не нужен/i)).toBeVisible();
    await expect(page.getByText(/общение с тренером происходит в telegram/i)).toBeVisible();

    const flowIcons = page.locator('.landing-flow-icon');
    await expect(flowIcons).toHaveCount(2);
    const problemIcon = page.locator('.landing-problem__result .landing-flow-icon');
    const syncIcon = page.locator('.landing-platforms__sync .landing-flow-icon');
    await expect(syncIcon.locator('svg')).toBeVisible();
    await expect(problemIcon.locator('svg')).toBeVisible();
    await expect(problemIcon).toHaveCSS('width', '44px');
    await expect(problemIcon).toHaveCSS('height', '44px');
    await expect(syncIcon).toHaveCSS('width', '44px');
    await expect(syncIcon).toHaveCSS('height', '44px');
    await expect(problemIcon.locator('svg')).toHaveCSS('stroke', 'rgb(0, 0, 0)');
    await expect(syncIcon.locator('svg')).toHaveCSS('stroke', 'rgb(0, 0, 0)');
    const syncIconBox = await syncIcon.boundingBox();
    const syncSvgBox = await syncIcon.locator('svg').boundingBox();
    expect(syncIconBox).not.toBeNull();
    expect(syncSvgBox).not.toBeNull();
    expect(
      Math.abs(syncSvgBox!.x + syncSvgBox!.width / 2 - (syncIconBox!.x + syncIconBox!.width / 2)),
    ).toBeLessThanOrEqual(1);
    expect(
      Math.abs(syncSvgBox!.y + syncSvgBox!.height / 2 - (syncIconBox!.y + syncIconBox!.height / 2)),
    ).toBeLessThanOrEqual(1);

    const platformCards = page.locator('.landing-platform-card');
    await expect(platformCards).toHaveCount(2);
    const platformIcons = page.locator('.landing-platform-card__icon');
    await expect(platformIcons).toHaveCount(2);
    for (const icon of await platformIcons.all()) {
      await expect(icon).toHaveCSS('width', '44px');
      await expect(icon).toHaveCSS('height', '44px');
      await expect(icon.locator('svg')).toHaveCSS('width', '22px');
      await expect(icon.locator('svg')).toHaveCSS('height', '22px');
    }
    const browserCard = await platformCards.first().boundingBox();
    const telegramCard = await platformCards.last().boundingBox();
    expect(browserCard).not.toBeNull();
    expect(telegramCard).not.toBeNull();
    if (viewport.width >= 768) {
      expect(browserCard!.x + browserCard!.width).toBeLessThan(telegramCard!.x);
      const platformHeadings = await platformCards
        .locator('h3')
        .evaluateAll((items) => items.map((item) => item.getBoundingClientRect().y));
      const platformDescriptions = await platformCards
        .locator('p')
        .evaluateAll((items) => items.map((item) => item.getBoundingClientRect().y));
      expect(Math.max(...platformHeadings) - Math.min(...platformHeadings)).toBeLessThanOrEqual(1);
      expect(
        Math.max(...platformDescriptions) - Math.min(...platformDescriptions),
      ).toBeLessThanOrEqual(1);
    } else {
      expect(browserCard!.y + browserCard!.height).toBeLessThan(telegramCard!.y);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
  }
});

test('сценарии спортсмена и тренера ведут в веб-приложение', async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 768, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/');

    const audienceCards = page.locator('.landing-audience article');
    await expect(audienceCards).toHaveCount(2);
    await expect(page.getByText(/занимаетесь самостоятельно/i)).toBeVisible();
    await expect(page.getByText(/вы тренер/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /начать самостоятельно/i })).toHaveAttribute(
      'href',
      '/app',
    );
    await expect(page.getByRole('link', { name: /войти и подать заявку/i })).toHaveAttribute(
      'href',
      '/app',
    );
    await expect(page.getByText(/нажмите «стать тренером» в профиле/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /перейти в веб-приложение/i })).toHaveAttribute(
      'href',
      '/app',
    );
    await expect(page.getByRole('link', { name: /задать вопрос в telegram/i })).toHaveAttribute(
      'href',
      'https://t.me/your_fitness_support_bot',
    );
    const actionArrows = page.locator('.landing-action__arrow');
    await expect(actionArrows).toHaveCount(6);
    for (const arrow of await actionArrows.all()) {
      await expect(arrow).toHaveCSS('font-size', '13.6px');
      await expect(arrow).toHaveCSS('font-weight', '800');
    }
    const heroButtons = page.locator('.landing-hero__actions .landing-button');
    const contactButtons = page.locator('.landing-contact__actions .landing-button');
    const audienceButtons = page.locator('.landing-audience .landing-button');
    for (const buttons of [heroButtons, contactButtons, audienceButtons]) {
      await expect(buttons).toHaveCount(2);
      const first = await buttons.first().boundingBox();
      const second = await buttons.last().boundingBox();
      expect(first).not.toBeNull();
      expect(second).not.toBeNull();
      expect(first!.width).toBeCloseTo(second!.width, 0);
      expect(first!.height).toBe(second!.height);
    }
    if (viewport.width === 390) {
      const brand = page.locator('.landing-header .landing-brand');
      await expect(brand.locator('span')).toHaveCSS('white-space', 'nowrap');
      const brandBox = await brand.boundingBox();
      const brandTextBox = await brand.locator('span').boundingBox();
      expect(brandBox).not.toBeNull();
      expect(brandTextBox).not.toBeNull();
      expect(brandTextBox!.height).toBeLessThan(20);
    }

    const clientCard = await audienceCards.first().boundingBox();
    const coachCard = await audienceCards.last().boundingBox();
    expect(clientCard).not.toBeNull();
    expect(coachCard).not.toBeNull();
    if (viewport.width >= 768) {
      expect(clientCard!.x + clientCard!.width).toBeLessThan(coachCard!.x);
      const audienceHeadings = await audienceCards
        .locator('h2')
        .evaluateAll((items) => items.map((item) => item.getBoundingClientRect().y));
      const audienceDescriptions = await audienceCards
        .locator(':scope > p:last-of-type')
        .evaluateAll((items) => items.map((item) => item.getBoundingClientRect().y));
      expect(Math.max(...audienceHeadings) - Math.min(...audienceHeadings)).toBeLessThanOrEqual(1);
      expect(
        Math.max(...audienceDescriptions) - Math.min(...audienceDescriptions),
      ).toBeLessThanOrEqual(1);
    } else {
      expect(clientCard!.y + clientCard!.height).toBeLessThan(coachCard!.y);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
    if (viewport.width === 390) {
      await expect(page.locator('.landing-footer p')).toBeVisible();
    }
  }
});

async function mockApi(
  page: Page,
  { withCoachClient = false, withCoachApplication = false, withCoachProgram = false } = {},
) {
  let role: 'client' | 'coach' | 'admin' = 'client';
  let coachApplication = withCoachApplication
    ? {
        id: 42,
        user_id: 7,
        username: 'future_coach',
        full_name: 'Будущий тренер',
        status: 'pending',
        source: 'web',
        created_at: '2030-01-09T09:00:00',
        reviewed_at: null,
      }
    : null;
  const heartRateZones = [
    { zone: 1, title: 'Восстановление', min_bpm: 130, max_bpm: 140 },
    { zone: 2, title: 'Лёгкая', min_bpm: 140, max_bpm: 151 },
    { zone: 3, title: 'Аэробная', min_bpm: 151, max_bpm: 162 },
    { zone: 4, title: 'Пороговая', min_bpm: 162, max_bpm: 173 },
    { zone: 5, title: 'Максимальная', min_bpm: 173, max_bpm: 184 },
  ];
  const emptyProgress = {
    workouts_total: 0,
    workouts_completed: 0,
    workouts_skipped: 0,
    workouts_missed: 0,
    adherence_percent: 0,
    current_streak: 0,
    weight_change_kg: null,
    weights: [],
    weekly_volume: [],
    personal_records: [],
  };
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (path.endsWith('/public/config'))
      return route.fulfill({
        json: { app_env: 'dev', enable_dev_auth: true, telegram_bot_username: 'fit_bot' },
      });
    if (path.endsWith('/auth/refresh'))
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    if (path.endsWith('/auth/telegram/init'))
      return route.fulfill({ json: { access_token: 'telegram-test-token', token_type: 'bearer' } });
    if (path.endsWith('/auth/dev-login')) {
      const body = request.postDataJSON() as { is_admin: boolean; is_coach: boolean };
      role = body.is_admin ? 'admin' : body.is_coach ? 'coach' : 'client';
      return route.fulfill({ json: { access_token: 'test-token', token_type: 'bearer' } });
    }
    if (path.endsWith('/me/profile/heart-rates/preview')) {
      const body = request.postDataJSON() as {
        resting_heart_rate: number | null;
        goal: 'fat_loss' | 'recomposition' | 'maintenance' | 'muscle_gain' | null;
      };
      const recommendations = {
        fat_loss: { min_bpm: 130, max_bpm: 140 },
        recomposition: { min_bpm: 124, max_bpm: 140 },
        maintenance: { min_bpm: 119, max_bpm: 140 },
        muscle_gain: { min_bpm: 119, max_bpm: 130 },
      };
      return route.fulfill({
        json: {
          estimated_max_heart_rate: 184,
          heart_rate_reserve: body.resting_heart_rate === null ? null : 109,
          heart_rate_calculation_method:
            body.resting_heart_rate === null ? 'percent_maximum' : 'heart_rate_reserve',
          heart_rate_zones: heartRateZones,
          recommended_cardio_range: body.goal ? recommendations[body.goal] : null,
        },
      });
    }
    if (path.endsWith('/me'))
      return route.fulfill({
        json: {
          id: 1,
          telegram_user_id: 2001,
          username: 'demo',
          first_name: 'Демо',
          is_coach: role !== 'client',
          is_admin: role === 'admin',
          has_active_program: false,
          has_workout_history: false,
          onboarding: { status: 'complete', required_fields: ['goal'], missing_fields: [] },
          profile: {
            full_name: 'Демо пользователь',
            goal: 'maintenance',
            timezone: 'Europe/Moscow',
            kbju: null,
          },
          trainer: null,
        },
      });
    if (path.endsWith('/me/coach-application')) {
      if (request.method() === 'POST') {
        coachApplication = {
          id: 42,
          user_id: 1,
          username: 'demo',
          full_name: 'Демо пользователь',
          status: 'pending',
          source: 'web',
          created_at: '2030-01-09T09:00:00',
          reviewed_at: null,
        };
        return route.fulfill({ status: 201, json: coachApplication });
      }
      if (request.method() === 'DELETE') {
        coachApplication = coachApplication ? { ...coachApplication, status: 'cancelled' } : null;
        return route.fulfill({ status: 204, body: '' });
      }
      return route.fulfill({ json: coachApplication });
    }
    if (path.endsWith('/workouts/today'))
      return route.fulfill({ status: 404, json: { detail: 'На сегодня тренировка не назначена' } });
    if (path.endsWith('/workouts/progress/summary'))
      return route.fulfill({
        json: {
          user_id: 1,
          period_days: 30,
          period_start: '2030-01-01',
          period_end: '2030-01-10',
          training: {
            planned_workouts: 0,
            completed_workouts: 0,
            frequency_per_week: 0,
            volume_kg: 0,
            new_personal_records: 0,
            last_completed_workout_on: null,
            next_workout: null,
          },
          nutrition: {
            visible: true,
            logged_days: 0,
            adherence_evaluated_days: 0,
            average_calories: null,
            target_calories: null,
            average_protein_g: null,
            target_protein_g: null,
            target_effective_on: null,
          },
          body: { latest_measurement: null, trends: [], priority: null, guidance: {} },
          adherence: {
            formula_version: 'adherence-v1',
            overall_percent: null,
            included_components: [],
            workouts: {},
            cardio: {},
            calories: {},
            protein: {},
          },
          data_sufficiency: {
            ruleset_version: 'data-sufficiency-v1',
            workout_logging: { status: 'insufficient', counters: {}, reason_keys: [] },
            working_sets: { status: 'insufficient', counters: {}, reason_keys: [] },
            rir_coverage: { status: 'insufficient', counters: {}, reason_keys: [] },
            nutrition_coverage: { status: 'insufficient', counters: {}, reason_keys: [] },
            weight_trend: { status: 'insufficient', counters: {}, reason_keys: [] },
            anthropometry: { status: 'insufficient', counters: {}, reason_keys: [] },
            schedule_adherence: { status: 'insufficient', counters: {}, reason_keys: [] },
          },
        },
      });
    if (path.endsWith('/workouts/progress/training-analytics'))
      return route.fulfill({
        json: {
          period_days: 30,
          period_start: '2030-01-01',
          period_end: '2030-01-10',
          exercise_history_limit: 20,
          completed_set_count: 0,
          reps_total: 0,
          reps_recorded_sets: 0,
          external_load_volume_kg: 0,
          volume_recorded_sets: 0,
          exercises: [],
          rir: {
            completed_set_count: 0,
            recorded_set_count: 0,
            missing_set_count: 0,
            distribution: [],
          },
          primary_muscle_exposure: [],
          secondary_muscle_exposure: [],
          completed_sets_without_muscle_metadata: 0,
          data_sufficiency: {
            ruleset_version: 'data-sufficiency-v1',
            workout_logging: { status: 'insufficient', counters: {}, reason_keys: [] },
            working_sets: { status: 'insufficient', counters: {}, reason_keys: [] },
            rir_coverage: { status: 'insufficient', counters: {}, reason_keys: [] },
          },
        },
      });
    if (path.endsWith('/nutrition/diary'))
      return route.fulfill({
        json: {
          diary_date: '2030-01-10',
          timezone: 'Europe/Moscow',
          meals: [],
          totals: {
            energy_kcal: '0',
            protein_g: '0',
            fat_g: '0',
            carbs_g: '0',
            fiber_g: null,
          },
          targets: null,
          remaining: null,
        },
      });
    if (path.endsWith('/workouts/progress')) return route.fulfill({ json: emptyProgress });
    if (path.endsWith('/check-ins/weekly/current'))
      return route.fulfill({
        json: {
          week_start: '2030-01-07',
          week_end: '2030-01-13',
          submitted_on: '2030-01-10',
          timezone: 'Europe/Moscow',
          existing: null,
          summary: {
            ruleset_version: 'weekly-check-in-summary-v1',
            period_start: '2030-01-07',
            period_end: '2030-01-10',
            goal: null,
            training: {
              planned_workouts: 0,
              completed_workouts: 0,
              adherence: {
                status: 'not_applicable',
                percent: null,
                achieved: 0,
                evaluated: 0,
                weight: 0.4,
              },
            },
            nutrition: {
              logged_days: 0,
              average_calories: null,
              target_calories: null,
              average_protein_g: null,
              target_protein_g: null,
              calories_adherence: {
                status: 'not_applicable',
                percent: null,
                achieved: 0,
                evaluated: 0,
                weight: 0.2,
              },
              protein_adherence: {
                status: 'not_applicable',
                percent: null,
                achieved: 0,
                evaluated: 0,
                weight: 0.2,
              },
            },
            weight_trend: null,
            anthropometry_trends: [],
            body_priority: null,
            progression: { training_volume_kg: 0, new_personal_records: 0 },
            data_sufficiency: {},
          },
        },
      });
    if (path.endsWith('/check-ins/weekly'))
      return route.fulfill({ json: { items: [], total: 0, limit: 4, offset: 0 } });
    if (path.endsWith('/workouts/schedule')) return route.fulfill({ json: [] });
    if (path.endsWith('/workouts/history/summary'))
      return route.fulfill({
        json: { workouts_completed: 0, completed_sets: 0, volume_kg: 0 },
      });
    if (path.endsWith('/workouts/history') || path.endsWith('/workouts/week'))
      return route.fulfill({ json: [] });
    if (path.endsWith('/me/coach-invites/link/preview'))
      return route.fulfill({
        json: {
          invite_id: 77,
          coach: {
            id: 9,
            telegram_user_id: 9009,
            username: 'test_coach',
            full_name: 'Тестовый тренер',
            can_open_chat: true,
            chat_url: 'https://t.me/test_coach',
            chat_unavailable_reason: null,
          },
          created_at: '2030-01-01T10:00:00',
          expires_at: '2030-01-15T10:00:00',
          requires_trainer_change: false,
          already_current_trainer: false,
          current_trainer: null,
        },
      });
    if (path.endsWith('/me/coach-invites/link/confirm'))
      return route.fulfill({ status: 204, body: '' });
    if (path.endsWith('/notifications/settings'))
      return route.fulfill({
        json: {
          workout_reminders_enabled: true,
          weekly_check_in_reminders_enabled: true,
          reminder_hour: 9,
        },
      });
    if (path.endsWith('/notifications')) return route.fulfill({ json: [] });
    if (path.endsWith('/programs/exercises/1/guide'))
      return route.fulfill({
        json: {
          technique_steps: ['Зафиксируйте корпус', 'Выполните движение под контролем'],
          breathing: 'Выдох в фазе усилия, вдох при возврате.',
          common_mistakes: ['Раскачивание корпусом'],
          muscles: [
            { name: 'Спина', role: 'Основная', function: 'Тянет плечевой пояс назад.' },
            { name: 'Бицепс', role: 'Вспомогательная', function: 'Сгибает локоть.' },
          ],
          images: [
            {
              phase: 'Исходное положение',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              alt: 'Исходное положение',
            },
            {
              phase: 'Активная фаза',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              alt: 'Активная фаза',
            },
          ],
          media: [
            {
              type: 'image',
              phase: 'Исходное положение',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              poster:
                'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
              alt: 'Исходное положение',
              source_name: 'Test source',
              source_url: 'https://example.com',
              source_license: 'Public domain',
              source_license_url: null,
              width: 400,
              height: 300,
              byte_size: 100,
              sort_order: 0,
            },
            {
              type: 'image',
              phase: 'Активная фаза',
              url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>%20',
              poster:
                'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>%20',
              alt: 'Активная фаза',
              source_name: 'Test source',
              source_url: 'https://example.com',
              source_license: 'Public domain',
              source_license_url: null,
              width: 400,
              height: 300,
              byte_size: 100,
              sort_order: 1,
            },
          ],
          source_name: 'Test source',
          source_url: 'https://example.com',
          source_license: 'Public domain',
        },
      });
    if (path.endsWith('/programs/exercises'))
      return route.fulfill({
        json: [
          {
            id: 1,
            title: 'Тяга блока',
            primary_muscle: 'Спина',
            equipment: 'Блок',
            primary_muscle_ids: ['back'],
            secondary_muscle_ids: ['biceps'],
            equipment_ids: ['cable'],
            alternatives: [],
            difficulty_level: 'beginner',
            is_custom: false,
            is_personalized: false,
            has_guide: true,
            guide: null,
          },
        ],
      });
    if (path.endsWith('/programs/templates/mine'))
      return route.fulfill({
        json: [
          {
            id: 10,
            title: 'Программа на всё тело — 3 дня',
            slug: 'full-body-3-days',
            goal: 'recomposition',
            level: 'beginner',
            owner_user_id: null,
            owner_telegram_user_id: null,
            owner_full_name: null,
            created_by_user_id: null,
            is_public: true,
            is_example: true,
            is_assigned_to_current_user: false,
            is_active_for_current_user: false,
            assigned_by_user_id: null,
            assigned_by_full_name: null,
            days: [
              {
                id: 100,
                day_number: 1,
                title: 'Всё тело',
                exercises: [
                  {
                    id: 1000,
                    exercise_id: 1,
                    exercise_title: 'Тяга блока',
                    prescribed_sets: 3,
                    prescribed_reps: '10–12',
                    rest_seconds: 90,
                    notes: null,
                    has_guide: true,
                  },
                ],
              },
            ],
          },
          {
            id: 11,
            title: 'Текущий план от тренера',
            slug: 'coach-active-plan',
            goal: 'maintenance',
            level: 'beginner',
            owner_user_id: null,
            owner_telegram_user_id: null,
            owner_full_name: null,
            created_by_user_id: 99,
            is_public: false,
            is_example: false,
            is_assigned_to_current_user: true,
            is_active_for_current_user: true,
            can_edit: false,
            assigned_by_user_id: 99,
            assigned_by_full_name: 'Тренер Анна',
            assigned_program_id: 501,
            assigned_program_status: 'active',
            assigned_program_start_date: '2030-01-01',
            assigned_program_duration_weeks: 4,
            current_revision_number: 1,
            days: [
              {
                id: 110,
                day_number: 1,
                title: 'База',
                exercises: [
                  {
                    id: 1100,
                    exercise_id: 1,
                    exercise_title: 'Тяга блока',
                    prescribed_sets: 3,
                    prescribed_reps: '10–12',
                    rest_seconds: 90,
                    notes: null,
                    superset_group: null,
                    superset_order: null,
                    has_guide: true,
                  },
                ],
              },
            ],
          },
        ],
      });
    if (path.endsWith('/programs/templates/recommendation')) {
      const criteria = request.postDataJSON() as {
        goal: string;
        experience: string;
        workouts_per_week: number;
        training_location: string | null;
        available_equipment_ids: string[] | null;
      };
      return route.fulfill({
        json: {
          status: 'recommended',
          criteria: { ...criteria, profile_fields_used: [] },
          missing_fields: [],
          message: 'Сначала посмотрите состав программы.',
          recommendation: {
            template: {
              id: 10,
              title: 'Программа на всё тело — 3 дня',
              slug: 'full-body-3-days',
              goal: 'recomposition',
              level: 'beginner',
              split_type: 'full_body',
              owner_user_id: null,
              owner_telegram_user_id: null,
              owner_full_name: null,
              created_by_user_id: null,
              is_public: true,
              is_example: true,
              is_assigned_to_current_user: false,
              is_active_for_current_user: false,
              can_edit: false,
              assigned_by_user_id: null,
              assigned_by_full_name: null,
              days: [
                {
                  id: 100,
                  day_number: 1,
                  title: 'Всё тело',
                  exercises: [
                    {
                      id: 1000,
                      exercise_id: 1,
                      exercise_title: 'Тяга блока',
                      prescribed_sets: 3,
                      prescribed_reps: '10–12',
                      rest_seconds: 90,
                      notes: null,
                      has_guide: true,
                    },
                  ],
                },
                {
                  id: 101,
                  day_number: 2,
                  title: 'Всё тело B',
                  exercises: [],
                },
                {
                  id: 102,
                  day_number: 3,
                  title: 'Всё тело C',
                  exercises: [],
                },
              ],
            },
            reason: 'Совпадает с выбранной целью, уровнем и ритмом.',
            fit_facts: [
              'Цель подбора: улучшение композиции тела.',
              'В шаблоне 3 тренировки за цикл.',
              'Для шаблона не требуется отдельное оборудование.',
            ],
            limitations: [],
          },
          alternatives: [],
          requires_explicit_start: true,
        },
      });
    }
    if (path.endsWith('/programs/assigned/501/revisions'))
      return route.fulfill({
        json: [
          {
            id: 1,
            user_program_id: 501,
            revision_number: 1,
            changed_by_user_id: 99,
            actor_role: 'trainer',
            change_kind: 'assigned',
            reason: null,
            changed_fields: {},
            snapshot: {},
            created_at: '2030-01-01T10:00:00',
          },
        ],
      });
    if (path.endsWith('/programs/assigned/501/blocks')) return route.fulfill({ json: [] });
    if (path.endsWith('/programs/templates/hidden')) return route.fulfill({ json: [] });
    if (path.endsWith('/admin/coach-applications')) {
      return route.fulfill({
        json: coachApplication?.status === 'pending' ? [coachApplication] : [],
      });
    }
    if (/\/admin\/coach-applications\/\d+$/.test(path) && request.method() === 'PATCH') {
      const body = request.postDataJSON() as { status: 'approved' | 'rejected' };
      coachApplication = coachApplication ? { ...coachApplication, status: body.status } : null;
      return route.fulfill({ json: coachApplication });
    }
    if (path.endsWith('/admin/users')) return route.fulfill({ json: [] });
    if (/\/coach\/clients\/\d+\/analytics$/.test(path))
      return route.fulfill({ json: emptyProgress });
    if (/\/coach\/clients\/\d+\/workouts$/.test(path)) return route.fulfill({ json: [] });
    if (path.endsWith('/coach/assigned-programs'))
      return route.fulfill({
        json: withCoachProgram
          ? [
              {
                id: 701,
                client_id: 2,
                client_telegram_user_id: 3002,
                client_username: 'client',
                client_full_name: 'Тестовый клиент',
                template_id: 10,
                title: 'План клиента на четыре недели',
                goal: 'maintenance',
                level: 'beginner',
                assigned_at: '2030-01-01T10:00:00',
                is_active: true,
                status: 'active',
                start_date: '2030-01-01',
                duration_weeks: 4,
                schedule_weekdays: [0, 2, 4],
                completed_at: null,
                workouts_total: 12,
                workouts_completed: 4,
                workouts_planned: 8,
                next_workout_date: '2030-01-08',
                current_revision_number: 2,
              },
            ]
          : [],
      });
    if (path.endsWith('/programs/assigned/701/revisions')) return route.fulfill({ json: [] });
    if (path.endsWith('/programs/assigned/701/blocks')) return route.fulfill({ json: [] });
    if (path.endsWith('/coach/clients'))
      return route.fulfill({
        json: withCoachClient
          ? [
              {
                id: 2,
                invite_id: null,
                telegram_user_id: 3002,
                username: 'client',
                full_name: 'Тестовый клиент',
                goal: 'maintenance',
                level: 'beginner',
                height_cm: 175,
                weight_kg: 75,
                workouts_per_week: 3,
                cardio_trainings_per_week: 1,
                kbju: null,
                status: 'active',
              },
            ]
          : [],
      });
    return route.fulfill({ json: [] });
  });
}

test('клиент входит и видит экран тренировки', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await expect(page.getByRole('heading', { name: /^Сегодня,/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Выберите тренировочный план' })).toBeVisible();
});

test('цветовая система сохраняет иерархию в светлой и тёмной темах', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app');

  const authPanel = page.locator('.login-card');
  await expect(page.getByRole('heading', { name: 'Войти в Your Fitness Coach' })).toBeVisible();
  await expect(authPanel).toHaveCSS('background-color', 'rgb(251, 252, 247)');
  await expect(authPanel).toHaveCSS('border-color', 'rgb(213, 219, 209)');

  const clientButton = page.getByRole('button', { name: 'Клиент' });
  await expect(clientButton).toHaveCSS('background-color', 'rgb(232, 237, 228)');
  await expect(clientButton).toHaveCSS('color', 'rgb(23, 32, 24)');

  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await expect(authPanel).toHaveCSS('background-color', 'rgb(21, 28, 23)');
  await expect(authPanel).toHaveCSS('border-color', 'rgb(43, 55, 47)');
  await expect(clientButton).toHaveCSS('background-color', 'rgb(32, 42, 35)');
  await expect(clientButton).toHaveCSS('color', 'rgb(242, 246, 239)');

  await clientButton.click();
  const selectedDestination = page.getByRole('link', { name: 'Сегодня', exact: true });
  const selectedDestinationIcon = selectedDestination.locator('.app-bottom-nav__icon');
  await expect(selectedDestination).toHaveAttribute('aria-current', 'page');
  await expect(selectedDestinationIcon).toHaveCSS('background-color', 'rgb(182, 242, 56)');
  await expect(selectedDestinationIcon).toHaveCSS('color', 'rgb(23, 32, 24)');
  await page.getByRole('button', { name: 'Включить светлую тему' }).click();
  await expect(selectedDestinationIcon).toHaveCSS('background-color', 'rgb(24, 37, 29)');
  await expect(selectedDestinationIcon).toHaveCSS('color', 'rgb(255, 255, 255)');
});

test('Web theme preference следует системе и сохраняет ручной выбор', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  let toggle = page.getByRole('button', { name: 'Включить тёмную тему' });
  await toggle.focus();
  await expect(toggle).toBeFocused();
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'light');

  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');

  toggle = page.getByRole('button', { name: 'Включить светлую тему' });
  await toggle.click();
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'light');
  await page.reload();
  await expect(page.getByRole('button', { name: 'Включить тёмную тему' })).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'light');

  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
});

test('Mobile Web и Telegram используют одну YFC palette и геометрию', async ({ browser }) => {
  const viewport = { width: 390, height: 844 };
  const webPage = await browser.newPage({ viewport });
  const telegramPage = await browser.newPage({ viewport });
  await telegramPage.addInitScript(() => {
    const themeHandlers = new Set<() => void>();
    const shellColors = {
      background: [] as string[],
      bottomBar: [] as string[],
      header: [] as string[],
    };
    const telegram = {
      initData: 'signed-test-data',
      colorScheme: 'light' as 'light' | 'dark',
      themeParams: { bg_color: '#ffffff', button_color: '#ff00ff', text_color: '#00ffff' },
      ready() {},
      expand() {},
      onEvent(event: string, callback: () => void) {
        if (event === 'themeChanged') themeHandlers.add(callback);
      },
      offEvent(event: string, callback: () => void) {
        if (event === 'themeChanged') themeHandlers.delete(callback);
      },
      setHeaderColor(color: string) {
        shellColors.header.push(color);
      },
      setBackgroundColor(color: string) {
        shellColors.background.push(color);
      },
      setBottomBarColor(color: string) {
        shellColors.bottomBar.push(color);
      },
    };
    Object.assign(window, {
      Telegram: { WebApp: telegram },
      __telegramShellColors: shellColors,
      __setTelegramTheme(colorScheme: 'light' | 'dark') {
        telegram.colorScheme = colorScheme;
        themeHandlers.forEach((callback) => callback());
      },
    });
  });

  await mockApi(webPage);
  await mockApi(telegramPage);
  await webPage.goto('/app');
  await webPage.getByRole('button', { name: 'Клиент' }).click();
  await telegramPage.goto('/app');
  await expect(webPage.getByRole('heading', { name: /^Сегодня,/ })).toBeVisible();
  await expect(telegramPage.getByRole('heading', { name: /^Сегодня,/ })).toBeVisible();
  await expect(telegramPage.getByRole('button', { name: /Включить .* тему/ })).not.toBeAttached();

  const snapshot = (page: Page) =>
    page.evaluate(() => {
      const rootStyle = getComputedStyle(document.documentElement);
      const surfaceElement = document.querySelector<HTMLElement>('.today-workout-spotlight')!;
      const card = surfaceElement.getBoundingClientRect();
      const container = document.querySelector<HTMLElement>('.container')!.getBoundingClientRect();
      const navigation = document
        .querySelector<HTMLElement>('#appBottomNav')!
        .getBoundingClientRect();
      const destinations = Array.from(
        document.querySelectorAll<HTMLElement>(
          '.app-bottom-nav__primary > a, .app-bottom-nav__primary > button',
        ),
      ).map((destination) => {
        const rect = destination.getBoundingClientRect();
        return { height: rect.height, width: rect.width, x: rect.x, y: rect.y };
      });
      return {
        tokens: ['--bg', '--card', '--text', '--accent', '--border'].map((token) =>
          rootStyle.getPropertyValue(token).trim(),
        ),
        card: {
          width: card.width,
          borderRadius: getComputedStyle(surfaceElement).borderRadius,
        },
        container: { width: container.width, x: container.x },
        navigation: {
          height: navigation.height,
          width: navigation.width,
          x: navigation.x,
          y: navigation.y,
        },
        destinations,
      };
    });

  expect(await snapshot(telegramPage)).toEqual(await snapshot(webPage));
  expect(await telegramPage.evaluate(() => document.documentElement.dataset.themeSource)).toBe(
    'telegram',
  );
  expect(
    await telegramPage.evaluate(() =>
      (
        window as unknown as Window & { __telegramShellColors: { background: string[] } }
      ).__telegramShellColors.background.at(-1),
    ),
  ).toBe('#f1f3ec');

  await webPage.getByRole('button', { name: 'Ещё', exact: true }).click();
  await webPage.getByRole('dialog').getByRole('button', { name: 'Включить тёмную тему' }).click();
  await webPage.getByRole('button', { name: 'Закрыть меню' }).click();
  await telegramPage.evaluate(() =>
    (
      window as unknown as Window & { __setTelegramTheme(theme: 'light' | 'dark'): void }
    ).__setTelegramTheme('dark'),
  );
  await expect(telegramPage.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  expect(await snapshot(telegramPage)).toEqual(await snapshot(webPage));
  await expect(telegramPage.getByRole('heading', { name: /^Сегодня,/ })).toBeVisible();

  await webPage.close();
  await telegramPage.close();
});

test('primary CTA лендинга меняется вместе с темой', async ({ page }) => {
  await page.goto('/');
  const primary = page.getByRole('link', { name: /открыть приложение/i });

  await expect(primary).toHaveCSS('background-color', 'rgb(24, 37, 29)');
  await expect(primary).toHaveCSS('color', 'rgb(255, 255, 255)');
  await page.getByRole('button', { name: 'Включить тёмную тему' }).click();
  await expect(primary).toHaveCSS('background-color', 'rgb(182, 242, 56)');
  await expect(primary).toHaveCSS('color', 'rgb(23, 32, 24)');
});

test('deep link показывает тренера до явного подтверждения', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app?startapp=trainer_test-invite-token');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await openCard(page, 'Мой тренер');
  await expect(page.getByRole('heading', { name: 'Тестовый тренер' })).toBeVisible();
  await page.getByRole('button', { name: 'Подтвердить подключение' }).click();
  await expect(page.getByText('Тренер подключён')).toBeVisible();
});

test('app shell сохраняет композицию и доступность на целевых viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 780 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 1280, height: 800 },
    { width: 768, height: 900 },
    { width: 390, height: 780 },
    { width: 360, height: 740 },
  ]) {
    await page.setViewportSize(viewport);
    const primaryNavigation = page.locator('.app-bottom-nav__primary');
    const visibleDestinations = primaryNavigation.locator('a:visible, button:visible');
    await expect(visibleDestinations).toHaveCount(viewport.width >= 900 ? 4 : 5);
    for (const destination of await visibleDestinations.all()) {
      await expect(destination).toBeInViewport();
    }
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
  }

  await page.setViewportSize({ width: 390, height: 780 });
  await openAppDestination(page, 'Прогресс');
  await expect(page).toHaveURL('/app?section=progress');
  await openAppDestination(page, 'Питание');
  await expect(page).toHaveURL('/app?section=nutrition');
  await page.goBack();
  await expect(page).toHaveURL('/app?section=progress');
  await expect(page.getByRole('link', { name: 'Прогресс', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await page.goForward();
  await expect(page).toHaveURL('/app?section=nutrition');

  await openAppDestination(page, 'Сегодня');
  await expect(page.getByRole('heading', { name: /^Сегодня,/ })).toBeVisible();

  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeInViewport();
  const moreButton = page.getByRole('button', { name: 'Ещё', exact: true });
  await moreButton.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeAttached();
  await expect(moreButton).toBeFocused();

  await moreButton.click();
  await page.getByRole('dialog').getByRole('button', { name: 'Выйти из аккаунта' }).click();
  await expect(page.getByRole('heading', { name: 'Войти в Your Fitness Coach' })).toBeVisible();
});

test('профиль содержит уведомления, а карточка упражнения открывает полное описание', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 780 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  let guideRequests = 0;
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.endsWith('/programs/exercises/1/guide')) {
      guideRequests += 1;
    }
  });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await openAppDestination(page, 'Профиль');
  await openCard(page, 'Профиль');
  await openCard(page, 'Напоминания о тренировках');
  await expect(page.getByRole('heading', { name: 'Напоминания о тренировках' })).toBeVisible();
  await expect(page.getByText('Личные уведомления')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Подписка' })).toHaveCount(0);

  const birthDate = page.getByLabel('Дата рождения');
  const birthDateControl = page.locator('.profile-birth-date-control');
  const [birthDateBox, birthDateControlBox] = await Promise.all([
    birthDate.boundingBox(),
    birthDateControl.boundingBox(),
  ]);
  expect(birthDateBox).not.toBeNull();
  expect(birthDateControlBox).not.toBeNull();
  expect(birthDateBox!.x).toBeGreaterThanOrEqual(birthDateControlBox!.x);
  expect(birthDateBox!.x + birthDateBox!.width).toBeLessThanOrEqual(
    birthDateControlBox!.x + birthDateControlBox!.width,
  );

  const reminderTime = page.getByLabel('Час отправки');
  const reminderTimeControl = page.locator('.reminder-time-control');
  const [reminderTimeBox, reminderTimeControlBox] = await Promise.all([
    reminderTime.boundingBox(),
    reminderTimeControl.boundingBox(),
  ]);
  expect(reminderTimeBox).not.toBeNull();
  expect(reminderTimeControlBox).not.toBeNull();
  expect(reminderTimeBox!.x).toBeGreaterThanOrEqual(reminderTimeControlBox!.x);
  expect(reminderTimeBox!.x + reminderTimeBox!.width).toBeLessThanOrEqual(
    reminderTimeControlBox!.x + reminderTimeControlBox!.width,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByText('Личные уведомления').click();
  const notificationDate = page.locator('.notification-date-control input');
  await expect(notificationDate).toHaveAttribute('type', 'date');
  await expect(notificationDate).toHaveCSS('text-align', 'center');
  await expect(page.locator('input[type="datetime-local"]')).toHaveCount(0);
  const [notificationDateBox, notificationDateControlBox] = await Promise.all([
    notificationDate.boundingBox(),
    page.locator('.notification-date-control').boundingBox(),
  ]);
  expect(notificationDateBox).not.toBeNull();
  expect(notificationDateControlBox).not.toBeNull();
  expect(notificationDateBox!.x).toBeGreaterThanOrEqual(notificationDateControlBox!.x);
  expect(notificationDateBox!.x + notificationDateBox!.width).toBeLessThanOrEqual(
    notificationDateControlBox!.x + notificationDateControlBox!.width,
  );

  const notificationRequest = page.waitForRequest(
    (request) =>
      new URL(request.url()).pathname.endsWith('/notifications') && request.method() === 'POST',
  );
  await page.getByRole('button', { name: 'Создать уведомление' }).click();
  const notificationPayload = (await notificationRequest).postDataJSON() as {
    scheduled_for: string;
  };
  expect(notificationPayload.scheduled_for).toMatch(/^\d{4}-\d{2}-\d{2}T09:00:00$/);

  await openAppDestination(page, 'Питание');
  await expect(page.getByRole('heading', { name: 'Напоминания о тренировках' })).toHaveCount(0);

  await openAppDestination(page, 'Упражнения');
  await expect(page.getByRole('heading', { name: 'Упражнения', exact: true })).toBeVisible();
  expect(guideRequests).toBe(0);
  await page.getByRole('button', { name: 'Техника' }).click();
  expect(guideRequests).toBe(1);
  await expect(page.getByRole('heading', { name: 'Для чего это упражнение' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Какие мышцы работают' })).toBeVisible();
  await expect(page.getByText('Тянет плечевой пояс назад.')).toBeVisible();
  const [guidePanelBox, guideHeadBox] = await Promise.all([
    page.locator('.exercise-guide-modal__panel').boundingBox(),
    page.locator('.exercise-guide-modal__head').boundingBox(),
  ]);
  expect(guidePanelBox).not.toBeNull();
  expect(guideHeadBox).not.toBeNull();
  expect(Math.abs(guideHeadBox!.x - guidePanelBox!.x)).toBeLessThanOrEqual(2);
  expect(
    Math.abs(guideHeadBox!.x + guideHeadBox!.width - (guidePanelBox!.x + guidePanelBox!.width)),
  ).toBeLessThanOrEqual(2);
  const phaseImage = page.getByAltText('Исходное положение');
  await expect(phaseImage).toHaveAttribute('loading', 'lazy');
  await expect(phaseImage).toHaveAttribute('width', '400');
  expect(
    await phaseImage.evaluate((image) =>
      Number.parseFloat(getComputedStyle(image).transitionDuration),
    ),
  ).toBeLessThanOrEqual(0.001);
  await page.getByRole('button', { name: 'Увеличить: Исходное положение' }).click();
  await expect(page.locator('.exercise-lightbox')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.exercise-lightbox')).toHaveCount(0);
});

test('описание упражнения использует широкую панель в веб-версии', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await openAppDestination(page, 'Упражнения');
  await expect(page.getByRole('heading', { name: 'Упражнения', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Техника' }).click();

  const guidePanel = page.locator('.exercise-guide-modal__panel');
  const guidePanelBox = await guidePanel.boundingBox();
  expect(guidePanelBox).not.toBeNull();
  expect(guidePanelBox!.width).toBeGreaterThan(800);
  await expect(guidePanel).toHaveCSS('overflow-x', 'hidden');
  const noteColumns = await guidePanel
    .locator('.exercise-guide-notes')
    .evaluate((notes) => getComputedStyle(notes).gridTemplateColumns.split(' '));
  expect(noteColumns).toHaveLength(2);
});

test('клиент подаёт заявку на роль тренера из профиля', async ({ page }) => {
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await openAppDestination(page, 'Профиль');
  await openCard(page, 'Стать тренером');

  await page.getByRole('button', { name: 'Стать тренером' }).click();
  await page.getByRole('button', { name: 'Отправить заявку' }).click();

  await expect(page.getByText('Заявка отправлена')).toBeVisible();
  await expect(page.getByText('На рассмотрении')).toBeVisible();
});

test('рекомендация кардио меняется с целью, а физиологические зоны остаются прежними', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await openAppDestination(page, 'Профиль');
  await openCard(page, 'Профиль');

  await page.getByLabel('Дата рождения').fill('1992-08-12');
  await page.getByText('Средний пульс в покое, уд/мин').locator('..').locator('input').fill('75');
  await page.getByLabel('Цель').selectOption('fat_loss');
  await expect(page.getByText('130–140 уд/мин')).toHaveCount(2);

  const zones = page.getByText('Пульсовые зоны').locator('..').locator('+ .list-grid');
  const initialZones = await zones.textContent();

  await page.getByLabel('Цель').selectOption('recomposition');
  await expect(page.getByText('124–140 уд/мин')).toBeVisible();
  await page.getByLabel('Цель').selectOption('maintenance');
  await expect(page.getByText('119–140 уд/мин')).toBeVisible();
  await page.getByLabel('Цель').selectOption('muscle_gain');
  await expect(page.getByText('119–130 уд/мин')).toBeVisible();

  await expect(zones).toHaveText(initialZones ?? '');
  await expect(page.getByText('184 уд/мин', { exact: true })).toBeVisible();
  await expect(page.locator('body')).not.toContainText('HRR');
  await expect(page.locator('body')).not.toContainText('MET');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('поля профиля и питания выровнены на десктопе и остаются адаптивными', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await openAppDestination(page, 'Профиль');
  await openCard(page, 'Профиль');
  const profileControlTops = await page.locator('.profile-form-grid').evaluate((grid) =>
    Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field'))
      .slice(6)
      .map((field) => {
        const control = field.querySelector<HTMLElement>('input, select, .date-control');
        return control?.getBoundingClientRect().top ?? 0;
      }),
  );
  expect(new Set(profileControlTops.map(Math.round)).size).toBe(1);

  await openAppDestination(page, 'Питание');
  await openCard(page, 'КБЖУ');
  const nutritionControlTops = await page
    .locator('.nutrition-form-grid')
    .first()
    .evaluate((grid) =>
      Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field'))
        .slice(5, 8)
        .map((field) => {
          const control = field.querySelector<HTMLElement>('input, select');
          return control?.getBoundingClientRect().top ?? 0;
        }),
    );
  expect(new Set(nutritionControlTops.map(Math.round)).size).toBe(1);

  await page.setViewportSize({ width: 390, height: 844 });
  const mobileFields = await page
    .locator('.nutrition-form-grid')
    .first()
    .evaluate((grid) =>
      Array.from(grid.querySelectorAll<HTMLElement>(':scope > .field')).map((field) => {
        const box = field.getBoundingClientRect();
        return { left: box.left, right: box.right, top: box.top };
      }),
    );
  expect(mobileFields.every((field) => field.left >= 0 && field.right <= 390)).toBe(true);
  expect(
    mobileFields.every((field, index) => index === 0 || field.top > mobileFields[index - 1]!.top),
  ).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('поля адаптируются к разным iPhone, а пример программы открывает состав', async ({ page }) => {
  await page.setViewportSize({ width: 440, height: 956 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();

  await openAppDestination(page, 'Прогресс');
  await openCard(page, 'Дневник замеров');
  const dateField = page.getByLabel('Дата');
  const weightField = page.getByLabel('Вес, кг');
  const diaryGrid = page.locator('.diary-form-grid');
  const dateControl = page.locator('.diary-date-control');
  const [dateBox, dateControlBox, weightBox, diaryGridBox] = await Promise.all([
    dateField.boundingBox(),
    dateControl.boundingBox(),
    weightField.boundingBox(),
    diaryGrid.boundingBox(),
  ]);
  expect(dateBox).not.toBeNull();
  expect(dateControlBox).not.toBeNull();
  expect(weightBox).not.toBeNull();
  expect(diaryGridBox).not.toBeNull();
  expect(dateBox!.y + dateBox!.height).toBeLessThanOrEqual(weightBox!.y);
  expect(dateControlBox!.x).toBeGreaterThanOrEqual(diaryGridBox!.x);
  expect(dateControlBox!.x + dateControlBox!.width).toBeLessThanOrEqual(
    diaryGridBox!.x + diaryGridBox!.width,
  );
  expect(dateBox!.x).toBeGreaterThanOrEqual(dateControlBox!.x);
  expect(dateBox!.x + dateBox!.width).toBeLessThanOrEqual(
    dateControlBox!.x + dateControlBox!.width,
  );

  await openAppDestination(page, 'Питание');
  await openCard(page, 'КБЖУ');
  expect(
    await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    })),
  ).toEqual({ viewport: 440, content: 440 });
  await page.evaluate(() => window.scrollTo({ left: 1000 }));
  expect(await page.evaluate(() => window.scrollX)).toBe(0);

  await openAppDestination(page, 'Упражнения');
  await expect(page.getByRole('heading', { name: 'Упражнения', exact: true })).toBeVisible();
  const search = page.getByRole('searchbox', { name: 'Поиск' });
  await search.fill('Тяга');
  await expect(page.getByText('Тяга блока', { exact: true })).toBeVisible();
  const searchBox = await search.boundingBox();
  expect(searchBox).not.toBeNull();
  expect(searchBox!.x + searchBox!.width).toBeLessThanOrEqual(440);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );

  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );

  await openAppDestination(page, 'План');
  await expect(page.getByRole('heading', { name: 'Текущий план от тренера' })).toBeVisible();
  await expect(page.getByText('Назначил тренер Тренер Анна')).toBeVisible();
  await page.getByText('Этапы и история программы', { exact: true }).click();
  await expect(page.getByText('Блоков пока нет')).toBeVisible();
  await expect(page.getByText('Программа назначена')).toBeVisible();
  await page.getByText('Этапы и история программы', { exact: true }).click();
  await openCard(page, 'Программы и шаблоны');
  const example = page.getByRole('button', {
    name: 'Посмотреть шаблон «Программа на всё тело — 3 дня»',
  });
  await expect(example).toContainText('Рекомпозиция · Начальный уровень · 1 тренировка в цикле');
  await expect(example).toContainText('Готовый шаблон');
  await expect(example).not.toContainText('recomposition');
  await expect(example).not.toContainText('beginner');
  await example.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'День 1. Всё тело' })).toBeVisible();
  await expect(page.getByRole('dialog').getByText('Тяга блока')).toBeVisible();
  await expect(page.getByRole('dialog').getByText('3 подх. × 10–12 · отдых 90 сек.')).toBeVisible();
  const [programPanelBox, programHeadBox] = await Promise.all([
    page.locator('.program-example-modal__panel').boundingBox(),
    page.locator('.program-example-modal__head').boundingBox(),
  ]);
  expect(programPanelBox).not.toBeNull();
  expect(programHeadBox).not.toBeNull();
  expect(programPanelBox!.x).toBeLessThanOrEqual(1);
  expect(Math.abs(programPanelBox!.width - 390)).toBeLessThanOrEqual(1);
  expect(Math.abs(programHeadBox!.x - programPanelBox!.x)).toBeLessThanOrEqual(2);
  expect(
    Math.abs(
      programHeadBox!.x + programHeadBox!.width - (programPanelBox!.x + programPanelBox!.width),
    ),
  ).toBeLessThanOrEqual(2);
  await page.getByRole('button', { name: 'Есть техника — посмотреть' }).click();
  const exerciseGuide = page.locator('.exercise-guide-modal__panel');
  await expect(exerciseGuide.getByRole('img', { name: 'Исходное положение' })).toBeVisible();
  await expect(exerciseGuide.getByRole('img', { name: 'Активная фаза' })).toBeVisible();
  await expect(exerciseGuide.getByText('Исходное положение', { exact: true })).toBeVisible();
  await expect(exerciseGuide.getByText('Активная фаза', { exact: true })).toBeVisible();
  await exerciseGuide.getByRole('button', { name: 'Увеличить: Исходное положение' }).click();
  await expect(page.locator('.exercise-lightbox')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.exercise-lightbox')).toHaveCount(0);
});

test('мастер подбора сохраняет ответы и ведёт к явному запуску на mobile и desktop', async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await openAppDestination(page, 'План');

  const launcher = page.getByRole('button', { name: 'Начать подбор' });
  await launcher.click();
  const wizard = page.getByRole('dialog', { name: 'Цель' });
  await expect(wizard).toBeVisible();
  await expect(wizard.getByText(/профиль от этого не обновится/i)).toBeVisible();
  expect(
    await wizard.locator('.program-wizard__panel').evaluate((element) => ({
      client: element.clientWidth,
      scroll: element.scrollWidth,
    })),
  ).toEqual({ client: 360, scroll: 360 });

  await wizard.getByRole('radio', { name: /Рекомпозиция/ }).check();
  await wizard.getByRole('button', { name: 'Далее' }).click();
  await page.getByRole('radio', { name: /Начинаю или возвращаюсь/ }).check();
  await page.getByRole('button', { name: 'Далее' }).click();
  const threeWorkouts = page.locator('input[name="recommendation-frequency"][value="3"]');
  await threeWorkouts.check();
  await page.getByRole('button', { name: 'Назад' }).click();
  await expect(page.getByRole('radio', { name: /Начинаю или возвращаюсь/ })).toBeChecked();
  await page.getByRole('button', { name: 'Далее' }).click();
  await expect(threeWorkouts).toBeChecked();
  await page.getByRole('button', { name: 'Далее' }).click();
  await page.getByRole('radio', { name: /Тренажёрный зал/ }).check();
  await page.getByRole('button', { name: 'Далее' }).click();
  await page.getByRole('radio', { name: /Учесть только доступное/ }).check();
  await page.getByRole('checkbox', { name: 'Только собственный вес' }).check();
  await page.getByRole('button', { name: 'Показать рекомендацию' }).click();

  const result = page.getByRole('dialog', { name: 'Ваш результат' });
  await expect(
    result.getByRole('heading', { name: 'Программа на всё тело — 3 дня' }),
  ).toBeVisible();
  await expect(result.getByText(/Всё тело — основные мышечные группы/)).toBeVisible();
  await expect(result.getByText(/не является медицинской рекомендацией/i)).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await result
      .locator('.program-wizard__panel')
      .evaluate((element) => element.scrollWidth <= element.clientWidth),
  ).toBe(true);
  await expect(result.getByText('Рекомпозиция', { exact: true })).toBeVisible();
  const frequencySummary = result
    .getByText('Частота', { exact: true })
    .locator('xpath=following-sibling::dd');
  await expect(frequencySummary).toContainText('3 тренировки в неделю');
  await expect(frequencySummary).toContainText('В программе: 3 тренировки в цикле');
  const mobileSummary = await result.locator('.program-wizard-result__summary').boundingBox();
  expect(mobileSummary).not.toBeNull();
  expect(mobileSummary!.height).toBeGreaterThan(150);

  await result.getByRole('button', { name: 'Посмотреть план' }).click();
  const preview = page.getByRole('dialog', { name: /Программа на всё тело — 3 дня/ });
  await expect(
    preview.getByRole('button', { name: 'Настроить расписание и запустить' }),
  ).toBeVisible();
  await preview.locator('.program-example-modal__close').click();

  await page.setViewportSize({ width: 1440, height: 900 });
  await launcher.click();
  const desktopPanel = page
    .getByRole('dialog', { name: 'Ваш результат' })
    .locator('.program-wizard__panel');
  const desktopBox = await desktopPanel.boundingBox();
  expect(desktopBox).not.toBeNull();
  expect(desktopBox!.width).toBeLessThanOrEqual(760);
  expect(Math.abs(desktopBox!.x + desktopBox!.width / 2 - 720)).toBeLessThanOrEqual(1);
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog', { name: 'Ваш результат' })).toHaveCount(0);
  await expect(launcher).toBeFocused();
});

test('клиент собирает и переупорядочивает личную программу', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto('/app');
  await page.getByRole('button', { name: 'Клиент' }).click();
  await openAppDestination(page, 'План');
  await openCard(page, 'Создать свою программу');

  const exercisePicker = page.getByRole('combobox', { name: 'Поиск упражнения' }).first();
  await exercisePicker.fill('Тяга');
  await page.getByRole('option', { name: /Тяга блока/ }).click();

  await page.getByRole('button', { name: 'Добавить упражнение' }).first().click();
  await page.getByRole('button', { name: 'Переместить упражнение 2 выше' }).click();
  await page.getByRole('button', { name: 'Удалить упражнение 1 из дня 1' }).click();

  await page.getByRole('button', { name: 'Добавить день' }).click();
  await page.getByRole('button', { name: 'Переместить день 2 выше' }).click();
  await page.getByRole('button', { name: 'Удалить день 1' }).click();

  const createRequest = page.waitForRequest(
    (request) =>
      new URL(request.url()).pathname.endsWith('/programs/templates') &&
      request.method() === 'POST',
  );
  await page.getByRole('button', { name: 'Создать программу' }).click();
  const payload = (await createRequest).postDataJSON() as {
    days: Array<{ exercises: Array<{ exercise_id: number }> }>;
  };
  expect(payload.days).toHaveLength(1);
  expect(payload.days[0]?.exercises).toEqual([expect.objectContaining({ exercise_id: 1 })]);
});

test('сенсорное поле даты сохраняет нативный пикер и показывает иконку календаря', async ({
  browser,
}) => {
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:4173',
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const page = await context.newPage();

  try {
    await mockApi(page);
    await page.goto('/app');
    await page.getByRole('button', { name: 'Клиент' }).click();
    await openAppDestination(page, 'Прогресс');
    await openCard(page, 'Дневник замеров');

    const dateField = page.getByLabel('Дата');
    const dateControl = page.locator('.diary-date-control');
    await expect(dateField).toHaveAttribute('type', 'date');
    const fallbackIcon = await dateControl.evaluate((element) => {
      const style = getComputedStyle(element, '::after');
      return {
        content: style.content,
        height: style.height,
        mask: style.maskImage || style.getPropertyValue('-webkit-mask-image'),
        pointerEvents: style.pointerEvents,
        width: style.width,
      };
    });
    expect(fallbackIcon).toMatchObject({
      content: '""',
      height: '18px',
      pointerEvents: 'none',
      width: '18px',
    });
    expect(fallbackIcon.mask).toContain('svg');

    await dateControl.scrollIntoViewIfNeeded();
    const dateControlBox = await dateControl.boundingBox();
    expect(dateControlBox).not.toBeNull();
    await dateField.evaluate((element) => {
      element.addEventListener('click', () => element.setAttribute('data-picker-clicked', 'true'), {
        once: true,
      });
    });
    await dateField.click({
      position: { x: dateControlBox!.width - 14, y: dateControlBox!.height / 2 },
    });
    await expect(dateField).toHaveAttribute('data-picker-clicked', 'true');
  } finally {
    await context.close();
  }
});

test('администратор открывает React-панель', async ({ page }) => {
  await mockApi(page, { withCoachApplication: true });
  await page.goto('/admin');
  await page.getByRole('button', { name: 'Админ' }).click();
  await expect(page.getByRole('heading', { name: 'Панель администратора' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Администрирование' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await expect(page.getByRole('link', { name: 'Тренер', exact: true })).toBeVisible();
  await openCard(page, 'Пользователи');
  await expect(page.getByText('Пользователи не найдены')).toBeVisible();
  await page.getByRole('tab', { name: 'Заявки тренеров' }).click();
  await openCard(page, 'Заявки на роль тренера');
  await expect(page.getByText('Будущий тренер')).toBeVisible();
  await page.getByRole('button', { name: 'Одобрить' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Одобрить' }).click();
  await expect(page.getByText('Новых заявок нет')).toBeVisible();
});

test('поля даты остаются внутри анкеты клиента в кабинете тренера', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page, { withCoachClient: true });
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();

  const birthDateField = page.getByLabel('Дата рождения');
  const birthDateBox = await birthDateField.boundingBox();
  const birthDateControlBox = await page.locator('.coach-client-birth-date-control').boundingBox();
  expect(birthDateBox).not.toBeNull();
  expect(birthDateControlBox).not.toBeNull();
  expect(birthDateBox!.x).toBeGreaterThanOrEqual(birthDateControlBox!.x);
  expect(birthDateBox!.x + birthDateBox!.width).toBeLessThanOrEqual(
    birthDateControlBox!.x + birthDateControlBox!.width,
  );

  await page.getByText('Прогресс и замеры', { exact: true }).click();

  const dateField = page.getByLabel('Дата', { exact: true });
  const dateBox = await dateField.boundingBox();
  await expect(dateField).toHaveCSS('text-align', 'center');
  const dateControlBox = await page.locator('.diary-date-control').boundingBox();
  const diaryGridBox = await page.locator('.diary-form-grid').boundingBox();
  expect(dateBox).not.toBeNull();
  expect(dateControlBox).not.toBeNull();
  expect(diaryGridBox).not.toBeNull();
  expect(dateControlBox!.x).toBeGreaterThanOrEqual(diaryGridBox!.x);
  expect(dateControlBox!.x + dateControlBox!.width).toBeLessThanOrEqual(
    diaryGridBox!.x + diaryGridBox!.width,
  );
  expect(dateBox!.x).toBeGreaterThanOrEqual(dateControlBox!.x);
  expect(dateBox!.x + dateBox!.width).toBeLessThanOrEqual(
    dateControlBox!.x + dateControlBox!.width,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test('тренер открывает кабинет', async ({ page }) => {
  await mockApi(page);
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();
  await expect(page.getByRole('heading', { name: 'Кабинет тренера' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Тренер', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await expect(page.getByRole('link', { name: 'Администрирование' })).toHaveCount(0);
  await openCard(page, 'Клиенты');
  await expect(page.getByText('Клиентов пока нет')).toBeVisible();
});

test('тренер быстро переходит между программой клиента и каталогом', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page, { withCoachClient: true, withCoachProgram: true });
  await page.goto('/coach');
  await page.getByRole('button', { name: 'Тренер' }).click();

  await page.getByRole('tab', { name: 'Назначенные программы' }).click();
  await openCard(page, 'Программы клиентов');
  await expect(page.getByText('План клиента на четыре недели')).toBeVisible();
  await page.getByRole('button', { name: 'Открыть клиента' }).click();

  await expect(page.getByText('Текущая программа клиента')).toBeVisible();
  await expect(page.getByText('План клиента на четыре недели')).toBeVisible();
  await page.getByRole('button', { name: 'Добавить упражнение' }).first().click();

  await expect(page.getByRole('heading', { name: 'Упражнения', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'В программу' }).click();
  const assignment = page.getByRole('dialog', { name: /Тяга блока/ });
  const assignmentContext = assignment.locator('.assignment-context select');
  await expect(assignmentContext.nth(0)).toHaveValue('2');
  await expect(assignmentContext.nth(1)).toHaveValue('701');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});
