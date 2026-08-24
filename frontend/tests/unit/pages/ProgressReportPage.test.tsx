import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ProgressReportPage from '../../../src/pages/reports/ProgressReportPage';
import { NavigationProvider } from '../../../src/shared/navigation/router';
import { makeProgressReportFixture } from '../../fixtures/progress-report';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NavigationProvider>
      <QueryClientProvider client={queryClient}>
        <ProgressReportPage />
      </QueryClientProvider>
    </NavigationProvider>,
  );
}

function installApi() {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify(makeProgressReportFixture()), { status: 200 }),
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState(null, '', '/app/report?period=days_30');
  Object.defineProperty(window, 'Telegram', { configurable: true, value: undefined });
});

describe('ProgressReportPage', () => {
  it('shows factual report sections and invokes browser print outside TMA', async () => {
    installApi();
    const print = vi.spyOn(window, 'print').mockImplementation(() => undefined);
    renderPage();

    expect(await screen.findByRole('heading', { name: /Александр Константинович/ })).toBeVisible();
    expect(screen.getByText('84')).toBeVisible();
    expect(screen.getByRole('table', { name: 'Таблица замеров массы' })).toBeVisible();
    expect(screen.getByText(/Пропущенный или неполный день/)).toBeVisible();
    expect(screen.getByText(/не медицинская оценка/)).toBeVisible();
    expect(screen.getByText('Тренер', { exact: true })).toBeVisible();
    expect(screen.getByText(/статус: активна/)).toBeVisible();
    expect(screen.getByText('Рекомендация:', { exact: true })).toBeVisible();
    expect(document.querySelector('.progress-report-document')?.textContent).not.toContain(
      'adherence-v1',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Печать / Сохранить как PDF' }));
    expect(print).toHaveBeenCalledTimes(1);
  });

  it('validates and persists a custom period and managed client subject', async () => {
    window.history.replaceState(null, '', '/app/report?period=days_30&client_id=73');
    installApi();
    renderPage();
    await screen.findByRole('heading', { name: /Александр Константинович/ });

    fireEvent.click(screen.getByRole('tab', { name: 'Свой период' }));
    fireEvent.change(screen.getByLabelText('Начало'), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText('Окончание'), { target: { value: '2026-08-20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Показать период' }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/coach/clients/73/progress-report?period=custom&date_from=2026-08-01&date_to=2026-08-20',
        expect.anything(),
      );
      expect(window.location.search).toContain('client_id=73');
      expect(window.location.search).toContain('date_from=2026-08-01');
    });
  });

  it('gives an explicit print fallback in Telegram instead of promising a native PDF', async () => {
    Object.defineProperty(window, 'Telegram', {
      configurable: true,
      value: { WebApp: { initData: 'signed-test-data' } },
    });
    installApi();
    const print = vi.spyOn(window, 'print').mockImplementation(() => undefined);
    renderPage();
    await screen.findByRole('heading', { name: /Александр Константинович/ });

    fireEvent.click(screen.getByRole('button', { name: 'Печать / Сохранить как PDF' }));

    expect(screen.getByText(/В Telegram системная печать может быть недоступна/)).toBeVisible();
    expect(screen.getByText(/Открыть в браузере/)).toBeVisible();
    expect(print).not.toHaveBeenCalled();
  });
});
