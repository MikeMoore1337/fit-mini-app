import { fireEvent, render, screen } from '@testing-library/react';
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
    title: 'Тренировка сегодня',
    body: 'По плану: Тренировка A',
    scheduled_for: '2030-01-10T09:00:00',
    status: 'queued',
    sent_at: null,
  },
  {
    id: 2,
    title: 'КБЖУ пересчитаны',
    body: 'Проверьте новые ориентиры.',
    scheduled_for: '2030-01-09T09:00:00',
    status: 'sent',
    sent_at: '2030-01-09T09:00:01',
  },
  {
    id: 3,
    title: 'Личная заметка',
    body: 'Не забыть воду.',
    scheduled_for: '2030-01-08T09:00:00',
    status: 'processing',
    sent_at: null,
  },
  {
    id: 4,
    title: 'Комментарий тренера к тренировке',
    body: 'К тренировке «Тренировка B»: Следите за темпом.',
    scheduled_for: '2030-01-08T10:00:00',
    status: 'sent',
    sent_at: '2030-01-08T10:00:01',
    action_url: '/app?workout_id=43&comment_id=7&workout_exercise_id=55',
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
            reminder_hour: 9,
          }),
          {
            status: 200,
          },
        );
      }
      if (path === '/api/v1/notifications') {
        return new Response(JSON.stringify(notifications), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => vi.restoreAllMocks());

  it('локализует статусы и навигирует только из системных уведомлений', async () => {
    const onNavigate = renderPanel();
    fireEvent.click(screen.getByText('Личные уведомления'));

    expect(await screen.findByText('Ожидает отправки')).toBeInTheDocument();
    expect(screen.getAllByText('Отправлено')).toHaveLength(2);
    expect(screen.getByText('Отправляется')).toBeInTheDocument();
    expect(screen.queryByText('queued')).not.toBeInTheDocument();
    expect(screen.queryByText('sent')).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Открыть тренировку: Тренировка сегодня',
      }),
    );
    expect(onNavigate).toHaveBeenLastCalledWith('/app?section=today');

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Открыть раздел питания: КБЖУ пересчитаны',
      }),
    );
    expect(onNavigate).toHaveBeenLastCalledWith('/app?section=nutrition');

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Открыть комментарий тренера: Комментарий тренера к тренировке',
      }),
    );
    expect(onNavigate).toHaveBeenLastCalledWith(
      '/app?workout_id=43&comment_id=7&workout_exercise_id=55',
    );

    expect(screen.getByText('Личная заметка').closest('button')).toBeNull();
  });
});
