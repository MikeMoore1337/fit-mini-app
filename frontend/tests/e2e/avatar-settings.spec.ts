/// <reference types="node" />

import { expect, test, type Browser, type Page } from '@playwright/test';
import { installTelegramHarness, TelegramHarness } from './fixtures/mobile-tma';
import { installPlatformApi, type PlatformApiController } from './fixtures/platform-api';

const avatarFile = {
  name: 'new-avatar.png',
  mimeType: 'image/png',
  buffer: Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFElEQVR42mNkYPj/n4GBgYGJAQoAHgQCAftFq20AAAAASUVORK5CYII=',
    'base64',
  ),
};

async function openPersonalData(page: Page) {
  await page.goto('/app?section=profile');
  await page.getByRole('link', { name: 'Личные данные', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Изменить аватар' })).toBeVisible();
}

async function openAvatarSettings(page: Page) {
  await openPersonalData(page);
  await page.getByRole('button', { name: 'Изменить аватар' }).click();
  await expect(page.getByRole('dialog', { name: 'Аватар' })).toBeVisible();
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
  const previewSource = await page.locator('.avatar-editor__avatar img').getAttribute('src');
  expect(previewSource).toMatch(/^blob:/);

  api.failNextAvatarUpload();
  await page.getByRole('button', { name: 'Сохранить аватар' }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось обработать изображение');
  await expect(page.getByRole('button', { name: 'Повторить сохранение' })).toBeVisible();
  await expect(page.locator('.avatar-editor__avatar img')).toHaveAttribute('src', previewSource!);

  await page.getByRole('button', { name: 'Повторить сохранение' }).click();
  await expect(page.getByRole('status')).toContainText('Аватар сохранён');
  expect(api.avatarUploads()).toBe(2);
  await expect(page.locator('.app-desktop-account-entry img')).toHaveAttribute('src', /^blob:/);

  await page.reload();
  await openAvatarSettings(page);
  await expect(
    page.getByRole('dialog', { name: 'Аватар' }).getByText('Используется свой аватар'),
  ).toBeVisible();
  await expect(page.locator('.avatar-editor__avatar img')).toHaveAttribute('src', /^blob:/);
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
  await expect(confirmation.getByRole('button', { name: 'Отмена' })).toBeFocused();
  await confirmation.getByRole('button', { name: 'Удалить', exact: true }).click();

  await expect(page.getByRole('status')).toContainText('фото из способа входа');
  await expect(page.locator('.app-desktop-account-entry img')).toHaveAttribute(
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
  { width: 768, height: 900 },
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

    const editor = page.getByRole('dialog', { name: 'Аватар' });
    await expect(editor).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    for (const button of await editor.locator('button').all()) {
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
  const telegram = new TelegramHarness(page);
  const api: PlatformApiController = await installPlatformApi(page, { avatarState: 'default' });
  await openAvatarSettings(page);

  await chooseAvatar(page);
  await page.getByRole('button', { name: 'Сохранить аватар' }).click();
  await expect(page.getByRole('status')).toContainText('Аватар сохранён');
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await expect(page.locator('.profile-avatar-setting img')).toHaveAttribute('src', /^blob:/);

  await page.getByRole('button', { name: 'Изменить аватар' }).click();
  const editor = page.getByRole('dialog', { name: 'Аватар' });
  const deleteAvatar = editor.getByRole('button', { name: 'Удалить свой аватар' });
  await deleteAvatar.click();
  await expect(page.getByRole('alertdialog', { name: 'Удалить свой аватар?' })).toBeVisible();
  await telegram.clickBack();
  await expect(page.getByRole('alertdialog', { name: 'Удалить свой аватар?' })).not.toBeAttached();
  await expect(editor).toBeVisible();
  await expect(deleteAvatar).toBeFocused();
  await editor.getByRole('button', { name: 'Закрыть редактор аватара' }).click();

  await page.getByRole('button', { name: 'Открыть профиль и настройки' }).click();
  await expect(page.getByRole('dialog', { name: 'Профиль и настройки' })).toBeVisible();
  await expect(page.locator('.app-more-panel__identity img')).toHaveAttribute('src', /^blob:/);
  expect(api.authInitCalls()).toBe(1);
  expect(api.avatarUploads()).toBe(1);
  await context.close();
});

test('captures the exact Task 110A owner approval screenshots', async ({ browser }) => {
  const scenarios = [
    {
      name: '01-mobile-390x844-light-personal-data',
      viewport: { width: 390, height: 844 },
      hasTouch: true,
      theme: 'light',
      editorOpen: false,
    },
    {
      name: '02-mobile-390x844-dark-avatar-sheet',
      viewport: { width: 390, height: 844 },
      hasTouch: true,
      theme: 'dark',
      editorOpen: true,
    },
    {
      name: '03-desktop-1280x900-light-personal-data',
      viewport: { width: 1280, height: 900 },
      hasTouch: false,
      theme: 'light',
      editorOpen: false,
    },
    {
      name: '04-desktop-1280x900-dark-avatar-modal',
      viewport: { width: 1280, height: 900 },
      hasTouch: false,
      theme: 'dark',
      editorOpen: true,
    },
  ] as const;

  for (const scenario of scenarios) {
    const context = await browser.newContext({
      viewport: scenario.viewport,
      hasTouch: scenario.hasTouch,
      colorScheme: scenario.theme,
      reducedMotion: 'reduce',
    });
    await context.addInitScript((selectedTheme) => {
      localStorage.setItem('app-theme', selectedTheme);
    }, scenario.theme);
    const page = await context.newPage();
    await installPlatformApi(page, { browserSession: true, avatarState: 'custom' });

    if (scenario.editorOpen) {
      await openAvatarSettings(page);
      await expect(
        page.getByRole('dialog', { name: 'Аватар' }).getByText('Используется свой аватар'),
      ).toBeVisible();
    } else {
      await openPersonalData(page);
      await expect(page.locator('.profile-avatar-card')).not.toBeAttached();
      await expect(page.locator('.profile-avatar-setting')).toBeVisible();
    }

    await expect(page.locator('html')).toHaveAttribute('data-color-scheme', scenario.theme);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    await page.screenshot({
      path: `../.artifacts/screenshots/task-110A/approval/${scenario.name}.png`,
      fullPage: false,
    });
    await context.close();
  }
});
