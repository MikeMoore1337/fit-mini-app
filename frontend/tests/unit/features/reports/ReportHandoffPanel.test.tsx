import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ReportHandoffPanel } from '../../../../src/features/reports/ReportHandoffPanel';
import type { ReportHandoff } from '../../../../src/shared/api/types';
import { makeProgressReportFixture } from '../../../fixtures/progress-report';

function makeHandoff(
  deliveryStatus: ReportHandoff['delivery_status'],
  deliveryAttempt = 1,
): ReportHandoff {
  return {
    id: 91,
    trainer: { id: 44, full_name: 'Ирина Тренерова', username: 'trainer' },
    period: 'days_30',
    period_start: '2026-07-26',
    period_end: '2026-08-24',
    timezone: 'Europe/Moscow',
    report_contract_version: 'progress-report-v1',
    included_section_ids: ['overview', 'training', 'data_sufficiency'],
    created_at: '2026-08-24T09:30:00+03:00',
    delivery_status: deliveryStatus,
    delivery_attempt: deliveryAttempt,
    live: true,
  };
}

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ReportHandoffPanel
        dateFrom=""
        dateTo=""
        period="days_30"
        report={makeProgressReportFixture()}
        trainer={{
          id: 44,
          full_name: 'Ирина Тренерова',
          username: 'trainer',
          can_open_chat: false,
        }}
      />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ReportHandoffPanel', () => {
  it('показывает получателя и отправляет только описатель живого отчёта', async () => {
    const handoff = makeHandoff('delivered');
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === '/api/v1/report-handoffs') {
        if (init?.method === 'POST') return new Response(JSON.stringify(handoff), { status: 201 });
        return new Response(JSON.stringify([]), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });

    renderPanel();

    expect(await screen.findByText('Отправить отчёт текущему тренеру')).toBeVisible();
    expect(screen.getByText('Ирина Тренерова')).toBeVisible();
    expect(screen.getByText(/Живые данные/)).toBeVisible();
    expect(screen.getByText(/Дневник питания: 80% покрытия/)).toBeVisible();
    expect(screen.queryByText(/Неделя прошла ровно/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Отправить отчёт тренеру' }));

    await waitFor(() => expect(screen.getByText(/Доставлено в центр уведомлений/)).toBeVisible());
    const postCall = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST');
    expect(postCall?.[0]).toBe('/api/v1/report-handoffs');
    expect(postCall?.[1]).toEqual(
      expect.objectContaining({
        body: JSON.stringify({ period: 'days_30' }),
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
    expect(postCall?.[1]?.body).not.toContain('Ирина');
  });

  it('повторяет только неудачную доставку с новым ключом попытки', async () => {
    const failed = makeHandoff('failed');
    const delivered = makeHandoff('delivered', 2);
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === '/api/v1/report-handoffs') {
        if (init?.method === 'POST') return new Response(JSON.stringify(failed), { status: 201 });
        return new Response(JSON.stringify([]), { status: 200 });
      }
      if (path === '/api/v1/report-handoffs/91/retry') {
        return new Response(JSON.stringify(delivered), { status: 201 });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });

    renderPanel();
    fireEvent.click(await screen.findByRole('button', { name: 'Отправить отчёт тренеру' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить отправку' }));

    await waitFor(() => expect(screen.getByText(/Доставлено в центр уведомлений/)).toBeVisible());
    const retryCall = fetchMock.mock.calls.find(
      ([path, options]) =>
        path === '/api/v1/report-handoffs/91/retry' && options?.method === 'POST',
    );
    expect(retryCall?.[1]).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });

  it('позволяет повторить неудачную отправку из истории', async () => {
    const failed = makeHandoff('failed');
    const delivered = makeHandoff('delivered', 2);
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === '/api/v1/report-handoffs') {
        if (init?.method === 'POST')
          return new Response(JSON.stringify(delivered), { status: 201 });
        return new Response(JSON.stringify([failed]), { status: 200 });
      }
      if (path === '/api/v1/report-handoffs/91/retry') {
        return new Response(JSON.stringify(delivered), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });

    renderPanel();
    fireEvent.click(
      await screen.findByRole('button', { name: /Повторить отправку отчёта за период/ }),
    );

    await waitFor(() => expect(screen.getByText(/Доставлено в центр уведомлений/)).toBeVisible());
    const retryCall = fetchMock.mock.calls.find(
      ([path, options]) =>
        path === '/api/v1/report-handoffs/91/retry' && options?.method === 'POST',
    );
    expect(retryCall?.[1]).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });
});
