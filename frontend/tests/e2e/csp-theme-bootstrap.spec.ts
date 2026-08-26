import { expect, test, type Page } from '@playwright/test';

const FASTAPI_ORIGIN =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.YFC_FASTAPI_ORIGIN === '1';
const CAPTURE =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
    ?.YFC_CAPTURE_TASK_74 === '1';
const SCREENSHOT_DIR = '../.artifacts/screenshots/task-74';

async function mockLoggedOutAuth(page: Page): Promise<void> {
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/public/config')) {
      await route.fulfill({
        json: {
          app_env: 'prod',
          enable_dev_auth: false,
          enable_web_auth: true,
          enable_email_auth: false,
          telegram_bot_username: 'fitness_bot',
          oauth_providers: ['telegram', 'google', 'yandex', 'vk'],
        },
      });
      return;
    }
    if (path.endsWith('/auth/refresh') || path.endsWith('/me')) {
      await route.fulfill({ status: 401, json: { detail: 'Требуется вход' } });
      return;
    }
    await route.fulfill({ json: [] });
  });
}

test('FastAPI CSP permits the external early theme bootstrap in Light and Dark', async ({
  page,
}) => {
  test.skip(!FASTAPI_ORIGIN, 'Requires the built frontend served by the local FastAPI origin.');

  const consoleProblems: string[] = [];
  const bootstrapResponses: number[] = [];
  page.on('console', (message) => {
    const text = message.text();
    const expectedLoggedOutResponse =
      text === 'Failed to load resource: the server responded with a status of 401 (Unauthorized)';
    if (
      /content security policy/i.test(text) ||
      (message.type() === 'error' && !expectedLoggedOutResponse)
    ) {
      consoleProblems.push(text);
    }
  });
  page.on('response', (response) => {
    if (response.url().endsWith('/assets/theme-bootstrap-20260826.js')) {
      bootstrapResponses.push(response.status());
    }
  });
  await mockLoggedOutAuth(page);

  await page.goto('/robots.txt');
  await page.evaluate(() => localStorage.setItem('app-theme', 'dark'));
  await page.setViewportSize({ width: 390, height: 844 });
  const darkResponse = await page.goto('/login');
  expect(darkResponse).not.toBeNull();
  const policy = darkResponse!.headers()['content-security-policy'] ?? '';
  const scriptPolicy = policy.split('script-src', 2)[1]?.split(';', 1)[0] ?? '';
  expect(scriptPolicy).toContain("'self'");
  expect(scriptPolicy).not.toContain("'unsafe-inline'");
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await expect(page.locator('html')).toHaveAttribute('data-theme-source', 'web');
  await expect(page.getByRole('region', { name: 'Способы входа' })).toBeVisible();
  if (CAPTURE) {
    await page.screenshot({ path: `${SCREENSHOT_DIR}/auth-390x844-dark-fastapi-csp.png` });
  }

  await page.evaluate(() => localStorage.setItem('app-theme', 'light'));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'light');
  await expect(page.getByRole('region', { name: 'Способы входа' })).toBeVisible();
  if (CAPTURE) {
    await page.screenshot({ path: `${SCREENSHOT_DIR}/auth-1440x900-light-fastapi-csp.png` });
  }

  expect(bootstrapResponses).toEqual([200, 200]);
  expect(consoleProblems).toEqual([]);
});
