import { expect, test, type Page } from '@playwright/test';
import { makeProgressReportFixture } from '../fixtures/progress-report';
import { expectNoHorizontalOverflow, installTelegramHarness } from './fixtures/mobile-tma';
import { installPlatformApi } from './fixtures/platform-api';

type ReportState = Parameters<typeof makeProgressReportFixture>[0];

async function installReportApi(page: Page, state: ReportState = 'full') {
  await page.route(
    /\/api\/v1\/(?:workouts\/progress\/report|coach\/clients\/\d+\/progress-report)/,
    async (route) => {
      const report = makeProgressReportFixture(state);
      const url = new URL(route.request().url());
      report.period = (url.searchParams.get('period') ?? report.period) as typeof report.period;
      if (report.period === 'custom') {
        report.period_start = url.searchParams.get('date_from') ?? report.period_start;
        report.period_end = url.searchParams.get('date_to') ?? report.period_end;
      }
      if (url.pathname.includes('/coach/clients/')) report.subject.role = 'client';
      await route.fulfill({ json: report });
    },
  );
}

test('full report keeps a mobile-first preview and creates a valid light print document', async ({
  page,
}) => {
  await page.addInitScript(() => localStorage.setItem('app-theme', 'dark'));
  await installPlatformApi(page, { browserSession: true });
  await installReportApi(page);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto('/app/report?period=days_30');
  await expect(page.getByRole('heading', { name: /Александр Константинович/ })).toBeVisible();
  await expect(page.getByRole('table', { name: 'Таблица замеров массы' })).toBeVisible();
  await expect(page.getByText('Тренер', { exact: true })).toBeVisible();
  await expect(page.getByText('Рекомендация:', { exact: true })).toBeVisible();
  const reportText = await page.locator('.progress-report-document').innerText();
  expect(reportText).not.toContain('active');
  expect(reportText).not.toContain('adherence-v1');
  expect(reportText).not.toContain('trainer');
  await expect(page.locator('.progress-report-confidence .data-confidence')).toHaveCount(3);
  await expect(
    page.locator(
      '.progress-report-document > .progress-report-overview + .progress-report-confidence + .progress-report-controls',
    ),
  ).toHaveCount(1);
  await expect(
    page.locator(
      '.progress-report-document > .progress-report-controls ~ .progress-report-section #report-training-title',
    ),
  ).toHaveCount(1);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/desktop-1280-dark-preview.png',
  });
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/desktop-1280-dark-full.png',
    fullPage: true,
  });

  await page.setViewportSize({ width: 360, height: 800 });
  await expectNoHorizontalOverflow(page);
  const printButton = page.getByRole('button', { name: 'Печать / Сохранить как PDF' });
  await expect(printButton).toBeVisible();
  expect((await printButton.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  await expect(page.locator('.progress-report-macros-heading')).toHaveCSS('white-space', 'nowrap');
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/mobile-web-360-dark-preview.png',
  });
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/mobile-web-360-dark-full.png',
    fullPage: true,
  });
  await page.locator('.progress-report-macros-heading').scrollIntoViewIfNeeded();
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/mobile-web-360-nutrition-targets.png',
  });

  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.report-screen-only').first()).toBeHidden();
  await expect(page.locator('.progress-report-print-header')).toHaveCount(4);
  await expect(page.locator('.progress-report-print-header').first()).toBeVisible();
  await expect(page.locator('.progress-report-print-header').first()).toHaveCSS(
    'position',
    'static',
  );
  await expect(page.locator('.progress-report-print-header').first()).toHaveCSS(
    'align-items',
    'center',
  );
  await expect(page.locator('.progress-report-print-footer')).toHaveCSS(
    'border-top-style',
    'solid',
  );
  await expect(page.locator('html')).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await page.locator('.data-viz-chart').first().screenshot({
    path: '../.artifacts/screenshots/task-69b/print-grayscale-chart-and-table.png',
  });
  const pdf = await page.pdf({
    path: '../.artifacts/pdf/task-67/progress-report-2026-07-26_2026-08-24.pdf',
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
  });
  expect(pdf.subarray(0, 4).toString()).toBe('%PDF');
  expect(pdf.length).toBeGreaterThan(10_000);
});

for (const state of ['partial', 'empty'] as const) {
  test(`${state} data stays factual and printable`, async ({ page }) => {
    await installPlatformApi(page, { browserSession: true });
    await installReportApi(page, state);
    await page.goto('/app/report?period=days_90');

    await expect(page.getByRole('heading', { name: 'Александр Петров' })).toBeVisible();
    await expect(page.getByText(/не медицинская оценка/)).toBeVisible();
    await expect(page.getByText(/не заполняет пропуски/)).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: `../.artifacts/screenshots/task-67/desktop-${state}-preview.png`,
    });
    if (state === 'empty') {
      await expect(page.getByText('Нет замеров массы за период', { exact: true })).toBeVisible();
      await expect(page.getByText('Отсутствующие дни не интерполируются.')).toBeVisible();
      await expect(page.getByText('Активной программы на дату формирования нет.')).toBeVisible();
    }
  });
}

test('dark TMA explains the print handoff and preserves report context', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installTelegramHarness(page, { colorScheme: 'dark' });
  await installPlatformApi(page);
  await installReportApi(page);

  await page.goto('/app/report?period=custom&date_from=2026-08-01&date_to=2026-08-20&client_id=73');
  await expect(page.locator('html')).toHaveAttribute('data-color-scheme', 'dark');
  await expect(page.getByRole('heading', { name: /Александр Константинович/ })).toBeVisible();
  await page.getByRole('button', { name: 'Печать / Сохранить как PDF' }).click();
  await expect(page.getByText(/В Telegram системная печать может быть недоступна/)).toBeVisible();
  await expect(page.getByText(/Открыть в браузере/)).toBeVisible();
  await expect(page).toHaveURL(/period=custom/);
  await expect(page).toHaveURL(/date_from=2026-08-01/);
  await expect(page).toHaveURL(/client_id=73/);
  await expectNoHorizontalOverflow(page);
  await page.locator('.data-viz-chart').first().scrollIntoViewIfNeeded();
  await page.screenshot({
    path: '../.artifacts/screenshots/task-69b/tma-390x844-dark-chart.png',
  });
  await page
    .getByText(/В Telegram системная печать может быть недоступна/)
    .scrollIntoViewIfNeeded();
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/tma-390-dark-print-fallback-preview.png',
  });
  await page.screenshot({
    path: '../.artifacts/screenshots/task-67/tma-390-dark-print-fallback.png',
    fullPage: true,
  });
});
