import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NotificationsPanel } from '../../../../src/features/account/NotificationsPanel';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 10, profile: { timezone: 'Europe/Moscow' } },
  }),
}));

const notifications = [
  {
    id: 1,
    category: 'workout_reminder',
    event_kind: 'reminder',
    title: 'Скоро тренировка',
    body: 'По плану: Тренировка A',
    created_at: '2030-01-10T08:00:00',
    scheduled_for: '2030-01-10T09:00:00',
    delivery_status: 'queued',
    sent_at: null,
    read_at: null,
    action_url: '/app?section=today',
  },
  {
    id: 2,
    category: 'nutrition_update',
    event_kind: 'transactional',
    title: 'КБЖУ пересчитаны',
    body: 'Проверьте новые ориентиры.',
    created_at: '2030-01-09T09:00:00',
    scheduled_for: '2030-01-09T09:00:00',
    delivery_status: 'sent',
    sent_at: '2030-01-09T09:00:01',
    read_at: '2030-01-09T10:00:00',
    action_url: '/app?section=nutrition',
  },
  {
    id: 3,
    category: 'custom_reminder',
    event_kind: 'reminder',
    title: 'Личная заметка',
    body: 'Не забыть воду.',
    created_at: '2030-01-08T08:00:00',
    scheduled_for: '2030-01-08T09:00:00',
    delivery_status: 'processing',
    sent_at: null,
    read_at: null,
    action_url: null,
  },
];

function renderPanel(onNavigate = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <NotificationsPanel onNavigate={onNavigate} />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
  return onNavigate;
}

describe('NotificationsPanel', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path === '/api/v1/notifications/settings') {
        return new Response(
          JSON.stringify({
            workout_reminders_enabled: true,
            weekly_check_in_reminders_enabled: true,
            measurement_reminders_enabled: false,
            telegram_enabled: true,
            telegram_linked: true,
            reminder_hour: 9,
            quiet_hours_start: null,
            quiet_hours_end: null,
          }),
          { status: 200 },
        );
      }
      if (path === '/api/v1/notifications') {
        return new Response(JSON.stringify(notifications), { status: 200 });
      }
      if (path === '/api/v1/notifications/1/open') {
        return new Response(
          JSON.stringify({ destination: '/app?section=today', stale: false, message: null }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => vi.restoreAllMocks());

  it('разделяет каналы и открывает canonical destination через server resolver', async () => {
    const onNavigate = renderPanel();

    expect((await screen.findAllByText('Непрочитанные · 2')).length).toBeGreaterThan(0);
    const notificationCenter = screen.getByText('Центр уведомлений').closest('details');
    expect(notificationCenter).not.toHaveAttribute('open');
    fireEvent.click(screen.getByText('Центр уведомлений'));
    expect(notificationCenter).toHaveAttribute('open');
    expect(screen.getByText('В приложении')).toBeInTheDocument();
    expect(screen.getByText('Предстоящая тренировка')).toBeInTheDocument();
    expect(screen.queryByText('Комментарий тренера')).not.toBeInTheDocument();
    expect(screen.getByText('Личное напоминание', { selector: 'strong' })).toBeInTheDocument();
    expect(screen.queryByText('queued')).not.toBeInTheDocument();
    expect(screen.queryByText('sent')).not.toBeInTheDocument();
    expect(screen.getByText(/Создано: 9 января в 09:00/)).toBeInTheDocument();

    fireEvent.click(await screen.findByRole('button', { name: 'Открыть: Скоро тренировка' }));

    await waitFor(() =>
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/notifications/1/open',
        expect.objectContaining({ method: 'POST' }),
      ),
    );
    await waitFor(() => expect(onNavigate).toHaveBeenCalledWith('/app?section=today'));
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/v1/notifications/1/open',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(screen.getByText('Личная заметка').closest('button')).toBeNull();
  });
});
