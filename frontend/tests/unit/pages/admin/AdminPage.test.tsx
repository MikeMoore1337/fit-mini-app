import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
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

  it('не показывает очередь заявок и не запрашивает application endpoints', async () => {
    renderPage();
    expect(await screen.findByText('Пользователи не найдены')).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: 'Заявки тренеров' })).not.toBeInTheDocument();
    expect(
      vi.mocked(fetch).mock.calls.some(([input]) => String(input).includes('coach-applications')),
    ).toBe(false);
  });
});
