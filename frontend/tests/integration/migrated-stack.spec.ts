import { expect, test } from '@playwright/test';

test('migrated PostgreSQL serves a real browser nutrition transaction and idempotent retry', async ({
  page,
}) => {
  const apiRequests: string[] = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith('/api/v1/'))
      apiRequests.push(`${request.method()} ${url.pathname}`);
  });

  await page.goto('/login');
  const devLogin = page.getByRole('region', { name: 'Локальный режим разработки' });
  await expect(devLogin).toBeVisible();
  await devLogin.getByRole('button', { name: 'Клиент', exact: true }).click();
  await page.getByRole('heading', { name: /Какая у вас главная цель\?|Сегодня/ }).waitFor();
  if (await page.getByRole('heading', { name: 'Какая у вас главная цель?' }).isVisible()) {
    await page.getByLabel(/^Поддерживать форму/).check();
    await page.getByRole('button', { name: 'Продолжить' }).click();
    await expect(page.getByRole('heading', { name: 'С чего хотите начать?' })).toBeVisible();
    await page.getByRole('button', { name: /Настроить питание/ }).click();
  } else {
    await page.goto('/app?section=nutrition');
  }
  await expect(page).toHaveURL(/\/app\?section=nutrition$/);
  await expect(page.getByRole('heading', { name: 'Питание', exact: true })).toBeVisible();

  await page.getByRole('button', { name: /Быстрый ввод/ }).click();
  const itemName = `Migrated PostgreSQL browser item ${Date.now()}`;
  await page.getByRole('textbox', { name: 'Название (необязательно)' }).fill(itemName);
  await page.getByRole('spinbutton', { name: 'Калории' }).fill('321');

  const firstRequestPromise = page.waitForRequest(
    (request) =>
      request.method() === 'POST' &&
      new URL(request.url()).pathname === '/api/v1/nutrition/diary/entries',
  );
  const firstResponsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === 'POST' &&
      new URL(response.url()).pathname === '/api/v1/nutrition/diary/entries',
  );
  await page.getByRole('button', { name: 'Сохранить Quick Add' }).click();
  const firstRequest = await firstRequestPromise;
  const firstResponse = await firstResponsePromise;
  expect(firstResponse.status()).toBe(201);
  const firstEntry = (await firstResponse.json()) as { id: number };
  await expect(page.getByText(itemName, { exact: true })).toBeVisible();

  const idempotencyKey = await firstRequest.headerValue('idempotency-key');
  const requestBody = firstRequest.postData();
  expect(idempotencyKey).toBeTruthy();
  expect(requestBody).toBeTruthy();
  const retry = await page.evaluate(
    async ({ body, key }) => {
      const token = sessionStorage.getItem('fit_access_token');
      if (!token) throw new Error('browser access token is missing');
      const response = await fetch('/api/v1/nutrition/diary/entries', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Idempotency-Key': key,
        },
        body,
      });
      return { status: response.status, payload: (await response.json()) as { id: number } };
    },
    { body: requestBody!, key: idempotencyKey! },
  );
  expect(retry.status).toBe(201);
  expect(retry.payload.id).toBe(firstEntry.id);

  await page.reload();
  await expect(page.getByText(itemName, { exact: true })).toHaveCount(1);
  expect(apiRequests).toContain('POST /api/v1/auth/dev-login');
  expect(apiRequests).toContain('GET /api/v1/me');
  expect(apiRequests).toContain('POST /api/v1/nutrition/diary/entries');
});
