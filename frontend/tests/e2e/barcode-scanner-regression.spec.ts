import { expect, test, type Page } from '@playwright/test';
import { expectNoHorizontalOverflow, installTelegramHarness } from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

declare global {
  interface Window {
    __task114CameraRequests?: number;
  }
}

async function installIosClassCamera(page: Page, { touch }: { touch: boolean }) {
  await page.addInitScript(
    ({ touch }) => {
      const originalMatchMedia = window.matchMedia.bind(window);
      window.matchMedia = (query: string) => {
        if (query !== '(hover: none) and (pointer: coarse)') return originalMatchMedia(query);
        return {
          matches: touch,
          media: query,
          onchange: null,
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          addListener: () => undefined,
          removeListener: () => undefined,
          dispatchEvent: () => false,
        } as MediaQueryList;
      };
      Object.defineProperty(globalThis, 'BarcodeDetector', {
        configurable: true,
        value: undefined,
      });
      window.__task114CameraRequests = 0;
      Object.defineProperty(navigator, 'mediaDevices', {
        configurable: true,
        value: {
          getUserMedia: async () => {
            window.__task114CameraRequests = (window.__task114CameraRequests ?? 0) + 1;
            throw new DOMException(
              'Physical camera is not opened by the harness.',
              'NotAllowedError',
            );
          },
        },
      });
    },
    { touch },
  );
}

async function installCanvasBarcodeCamera(page: Page) {
  await page.addInitScript(() => {
    const originalMatchMedia = window.matchMedia.bind(window);
    window.matchMedia = (query: string) => {
      if (query !== '(hover: none) and (pointer: coarse)') return originalMatchMedia(query);
      return {
        matches: true,
        media: query,
        onchange: null,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        addListener: () => undefined,
        removeListener: () => undefined,
        dispatchEvent: () => false,
      } as MediaQueryList;
    };
    Object.defineProperty(globalThis, 'BarcodeDetector', {
      configurable: true,
      value: undefined,
    });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => {
          const barcode = '3017620422003';
          const left = [
            '0001101',
            '0011001',
            '0010011',
            '0111101',
            '0100011',
            '0110001',
            '0101111',
            '0111011',
            '0110111',
            '0001011',
          ];
          const alternate = [
            '0100111',
            '0110011',
            '0011011',
            '0100001',
            '0011101',
            '0111001',
            '0000101',
            '0010001',
            '0001001',
            '0010111',
          ];
          const right = [
            '1110010',
            '1100110',
            '1101100',
            '1000010',
            '1011100',
            '1001110',
            '1010000',
            '1000100',
            '1001000',
            '1110100',
          ];
          const parity = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG'];
          const encoding = parity[Number(barcode[0])]!;
          let modules = '101';
          for (let index = 0; index < 6; index += 1) {
            const digit = Number(barcode[index + 1]);
            modules += encoding[index] === 'L' ? left[digit] : alternate[digit];
          }
          modules += '01010';
          for (const digit of barcode.slice(7)) modules += right[Number(digit)];
          modules += '101';

          const quietModules = 12;
          const moduleWidth = 4;
          const canvas = document.createElement('canvas');
          canvas.width = (modules.length + quietModules * 2) * moduleWidth;
          canvas.height = 180;
          canvas.style.position = 'fixed';
          canvas.style.left = '-10000px';
          document.body.append(canvas);
          const context = canvas.getContext('2d', { alpha: false });
          if (!context) throw new Error('Canvas is unavailable');
          const draw = () => {
            context.fillStyle = '#fff';
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.fillStyle = '#000';
            for (let index = 0; index < modules.length; index += 1) {
              if (modules[index] === '1') {
                context.fillRect((index + quietModules) * moduleWidth, 20, moduleWidth, 140);
              }
            }
          };
          draw();
          const stream = canvas.captureStream(10);
          const repaint = window.setInterval(draw, 100);
          for (const track of stream.getTracks()) {
            const originalStop = track.stop.bind(track);
            track.stop = () => {
              window.clearInterval(repaint);
              canvas.remove();
              originalStop();
            };
          }
          return stream;
        },
      },
    });
  });
}

async function openBarcode(page: Page) {
  await page.goto('/app?section=nutrition');
  await page
    .getByRole('region', { name: 'Завтрак' })
    .getByRole('button', { name: /Добавить/ })
    .click();
  await page.getByRole('button', { name: 'Поиск по штрихкоду', exact: true }).click();
}

for (const current of [
  { label: 'mobile-web-360', viewport: { width: 360, height: 800 }, telegram: false },
  { label: 'mock-tma-390', viewport: { width: 390, height: 844 }, telegram: true },
  { label: 'mobile-web-430', viewport: { width: 430, height: 932 }, telegram: false },
] as const) {
  test(`camera fallback stays available without BarcodeDetector (${current.label})`, async ({
    browserName,
    page,
  }) => {
    await page.setViewportSize(current.viewport);
    await installIosClassCamera(page, { touch: true });
    if (current.telegram) {
      await installTelegramHarness(page, {
        colorScheme: 'dark',
        viewportHeight: current.viewport.height,
        viewportStableHeight: current.viewport.height,
      });
    }
    await installPlatformApi(page, { browserSession: !current.telegram });
    await openBarcode(page);

    const scan = page.getByRole('button', { name: 'Сканировать камерой' });
    const manual = page.getByRole('textbox', { name: 'Штрихкод' });
    await expect(scan).toHaveClass(/ui-button--primary/);
    await expect(manual).toBeVisible();
    await expect.poll(() => page.evaluate(() => window.__task114CameraRequests)).toBe(0);
    await scan.click();
    await expect(
      page.getByText(
        'Доступ к камере запрещён. Разрешите его в настройках браузера или введите код вручную.',
      ),
    ).toBeVisible();
    await expect.poll(() => page.evaluate(() => window.__task114CameraRequests)).toBe(1);
    await expect(manual).toBeEnabled();
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: `../.artifacts/screenshots/task-114/${browserName}-${current.label}-camera-denied.png`,
    });
  });
}

test('desktop keeps manual barcode behavior primary', async ({ browserName, page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await installIosClassCamera(page, { touch: false });
  await installPlatformApi(page, { browserSession: true });
  await openBarcode(page);

  await expect(page.getByRole('button', { name: 'Сканировать камерой' })).not.toBeAttached();
  await expect(page.getByRole('button', { name: 'Найти', exact: true })).toHaveClass(
    /ui-button--primary/,
  );
  await expect(page.getByRole('textbox', { name: 'Штрихкод' })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: `../.artifacts/screenshots/task-114/${browserName}-desktop-1280-manual.png`,
  });
});

test('barcode flow completes through the local decoder or manual recovery', async ({
  browserName,
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installCanvasBarcodeCamera(page);
  await installPlatformApi(page, { browserSession: true });
  await openBarcode(page);

  await page.getByRole('button', { name: 'Сканировать камерой' }).click();
  if (browserName !== 'chromium') {
    await expect(
      page.getByText('Не удалось открыть камеру. Введите штрихкод вручную.'),
    ).toBeVisible();
    await page.getByRole('textbox', { name: 'Штрихкод' }).fill('3017620422003');
    await page.getByRole('button', { name: 'Найти', exact: true }).click();
  }
  await expect(page.getByRole('button', { name: 'Выбрать продукт' })).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByRole('textbox', { name: 'Штрихкод' })).toHaveValue('3017620422003');
  await page.getByRole('button', { name: 'Выбрать продукт' }).click();
  await expect(page.getByRole('heading', { name: 'Овсяная каша' })).toBeVisible();
  await page.getByRole('button', { name: 'Добавить в дневник' }).click();
  await expect(
    page.getByRole('region', { name: 'Завтрак' }).getByText('Овсяная каша'),
  ).toBeVisible();
});
