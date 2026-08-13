import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import AdminPage from '../../../../src/pages/admin/AdminPage';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 1, is_admin: true } }),
}));

vi.mock('../../../../src/app/AppShell', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <AdminPage />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('AdminPage', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const path = String(input);
      if (path.startsWith('/api/v1/admin/users?')) {
        return new Response(JSON.stringify([]), { status: 200 });
      }
      if (path.startsWith('/api/v1/admin/notifications?')) {
        return new Response(
          JSON.stringify([
            {
              id: 10,
              user_id: 2,
              title: 'КБЖУ пересчитаны',
              body: 'Проверьте новые ориентиры.',
              scheduled_for: '2030-01-09T09:00:00',
              status: 'sent',
              timezone: 'Europe/Moscow',
              sent_at: '2030-01-09T09:00:01',
              created_at: '2030-01-09T08:00:00',
            },
          ]),
          { status: 200 },
        );
      }
      if (path.startsWith('/api/v1/admin/coach-applications?')) {
        return new Response(
          JSON.stringify([
            {
              id: 42,
              user_id: 7,
              username: 'future_coach',
              full_name: 'Будущий тренер',
              status: 'pending',
              source: 'web',
              created_at: '2030-01-09T09:00:00',
              reviewed_at: null,
            },
          ]),
          { status: 200 },
        );
      }
      if (path === '/api/v1/admin/coach-applications/42' && init?.method === 'PATCH') {
        return new Response(JSON.stringify({ id: 42, status: 'approved' }), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('показывает статус уведомления на русском языке', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: 'Уведомления' }));

    expect(await screen.findByText('Отправлено')).toBeInTheDocument();
    expect(screen.queryByText('sent')).not.toBeInTheDocument();
  });

  it('показывает заявки тренеров и одобряет выбранную', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: 'Заявки тренеров' }));

    expect(await screen.findByText('Будущий тренер')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Одобрить' }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Одобрить' }));

    await waitFor(() => {
      const call = vi
        .mocked(fetch)
        .mock.calls.find(
          ([input, options]) =>
            String(input) === '/api/v1/admin/coach-applications/42' && options?.method === 'PATCH',
        );
      expect(call?.[1]?.body).toBe(JSON.stringify({ status: 'approved' }));
    });
  });
});
