/// <reference types="node" />

import { expect, test, type Browser, type Page } from '@playwright/test';
import { installTelegramHarness } from './fixtures/mobile-tma';
import { installPlatformApi, type PlatformApiController } from './fixtures/platform-api';

const avatarFile = {
  name: 'new-avatar.png',
  mimeType: 'image/png',
  buffer: Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFElEQVR42mNkYPj/n4GBgYGJAQoAHgQCAftFq20AAAAASUVORK5CYII=',
    'base64',
  ),
};

async function openAvatarSettings(page: Page) {
  await page.goto('/app?section=profile');
  await expect(page.getByRole('heading', { name: 'Аватар', exact: true })).toBeVisible();
}

async function chooseAvatar(page: Page) {
  await page.getByLabel('Выбрать изображение для аватара').setInputFiles(avatarFile);
  await expect(page.getByText('Предпросмотр нового изображения')).toBeVisible();
}

async function createBrowserProfile(
  browser: Browser,
  options: Parameters<typeof installPlatformApi>[1],
) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const api = await installPlatformApi(page, { ...options, browserSession: true });
  return { context, page, api };
}

test('failed upload keeps the local preview and retry updates every account avatar', async ({
  browser,
}) => {
  const { context, page, api } = await createBrowserProfile(browser, {
    avatarState: 'provider',
  });
  await openAvatarSettings(page);

  await chooseAvatar(page);
  const previewSource = await page.locator('.profile-avatar-card__avatar img').getAttribute('src');
  expect(previewSource).toMatch(/^blob:/);

  api.failNextAvatarUpload();
  await page.getByRole('button', { name: 'Сохранить аватар' }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось обработать изображение');
  await expect(page.getByRole('button', { name: 'Повторить сохранение' })).toBeVisible();
  await expect(page.locator('.profile-avatar-card__avatar img')).toHaveAttribute(
    'src',
    previewSource!,
  );

  await page.getByRole('button', { name: 'Повторить сохранение' }).click();
  await expect(page.getByRole('status')).toContainText('Аватар сохранён');
  expect(api.avatarUploads()).toBe(2);
  await expect(page.getByText('Используется свой аватар')).toBeVisible();
  await expect(page.locator('.app-desktop-account-entry img')).toHaveAttribute('src', /^blob:/);

  await page.reload();
  await expect(page.getByText('Используется свой аватар')).toBeVisible();
  await expect(page.locator('.profile-avatar-card__avatar img')).toHaveAttribute('src', /^blob:/);
  await context.close();
});

test('deletion requires confirmation and restores the provider avatar', async ({ browser }) => {
  const { context, page, api } = await createBrowserProfile(browser, {
    avatarState: 'custom',
  });
  await openAvatarSettings(page);

  await page.getByRole('button', { name: 'Удалить свой аватар' }).click();
  const confirmation = page.getByRole('alertdialog', { name: 'Удалить свой аватар?' });
  await expect(confirmation).toBeVisible();
  await expect(confirmation.getByRole('button', { name: 'Удалить', exact: true })).toBeFocused();
  await confirmation.getByRole('button', { name: 'Удалить', exact: true }).click();

  await expect(page.getByRole('status')).toContainText('фото из способа входа');
  await expect(page.getByText('Используется фото из способа входа')).toBeVisible();
  await expect(page.locator('.profile-avatar-card__avatar img')).toHaveAttribute(
    'src',
    /^data:image\/svg\+xml/,
  );
  expect(api.avatarDeletes()).toBe(1);
  await context.close();
});

for (const viewport of [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
]) {
  test(`mobile ${viewport.width}px keeps avatar actions inside the viewport`, async ({
    browser,
  }) => {
    const context = await browser.newContext({
      viewport,
      hasTouch: true,
      reducedMotion: viewport.width === 360 ? 'reduce' : 'no-preference',
    });
    const page = await context.newPage();
    await installPlatformApi(page, { browserSession: true, avatarState: 'custom' });
    await openAvatarSettings(page);

    await expect(page.locator('.profile-avatar-card')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    for (const button of await page.locator('.profile-avatar-card__actions button').all()) {
      const box = await button.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44);
    }
    await context.close();
  });
}

test('mocked Telegram Mini App uses the same custom avatar flow', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
  });
  const page = await context.newPage();
  await installTelegramHarness(page, {
    colorScheme: 'dark',
    safeAreaInset: { top: 16, right: 0, bottom: 20, left: 0 },
    contentSafeAreaInset: { top: 8, right: 0, bottom: 24, left: 0 },
  });
  const api: PlatformApiController = await installPlatformApi(page, { avatarState: 'default' });
  await openAvatarSettings(page);

  await chooseAvatar(page);
  await page.getByRole('button', { name: 'Сохранить аватар' }).click();
  await expect(page.getByRole('status')).toContainText('Аватар сохранён');
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await page.getByRole('button', { name: 'Открыть профиль и настройки' }).click();
  await expect(page.getByRole('dialog', { name: 'Профиль и настройки' })).toBeVisible();
  await expect(page.locator('.app-more-panel__identity img')).toHaveAttribute('src', /^blob:/);
  expect(api.authInitCalls()).toBe(1);
  expect(api.avatarUploads()).toBe(1);
  await context.close();
});

test('captures the owner approval matrix in matching light and dark states', async ({
  browser,
}) => {
  const surfaces = [
    { name: 'desktop-1280x900', viewport: { width: 1280, height: 900 }, hasTouch: false },
    { name: 'mobile-390x844', viewport: { width: 390, height: 844 }, hasTouch: true },
  ] as const;
  const states = ['default', 'provider', 'custom', 'error', 'delete-confirmation'] as const;

  for (const surface of surfaces) {
    for (const theme of ['light', 'dark'] as const) {
      for (const state of states) {
        const context = await browser.newContext({
          viewport: surface.viewport,
          hasTouch: surface.hasTouch,
          colorScheme: theme,
        });
        await context.addInitScript((selectedTheme) => {
          localStorage.setItem('app-theme', selectedTheme);
        }, theme);
        const page = await context.newPage();
        const api = await installPlatformApi(page, {
          browserSession: true,
          avatarState:
            state === 'provider' || state === 'error'
              ? 'provider'
              : state === 'custom' || state === 'delete-confirmation'
                ? 'custom'
                : 'default',
        });
        await openAvatarSettings(page);
        await expect(page.locator('html')).toHaveAttribute('data-color-scheme', theme);

        if (state === 'error') {
          await chooseAvatar(page);
          api.failNextAvatarUpload();
          await page.getByRole('button', { name: 'Сохранить аватар' }).click();
          await expect(page.getByRole('alert')).toBeVisible();
        } else if (state === 'delete-confirmation') {
          await page.getByRole('button', { name: 'Удалить свой аватар' }).click();
          await expect(page.getByRole('alertdialog')).toBeVisible();
        } else {
          const label = {
            default: 'Используется нейтральный emoji',
            provider: 'Используется фото из способа входа',
            custom: 'Используется свой аватар',
          }[state];
          await expect(page.getByText(label)).toBeVisible();
        }

        if (surface.hasTouch) {
          const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
          );
          expect(overflow).toBeLessThanOrEqual(1);
        }
        await page.screenshot({
          path: `../.artifacts/screenshots/task-110/approval/${surface.name}-${theme}-${state}.png`,
          fullPage: false,
        });
        const bottomNavigation = page.locator('.app-bottom-nav');
        if (surface.hasTouch) {
          await bottomNavigation.evaluate((element) => {
            element.style.visibility = 'hidden';
          });
        }
        await page.locator('.profile-avatar-card').screenshot({
          path: `../.artifacts/screenshots/task-110/approval/card-${surface.name}-${theme}-${state}.png`,
        });
        await context.close();
      }
    }
  }
});
