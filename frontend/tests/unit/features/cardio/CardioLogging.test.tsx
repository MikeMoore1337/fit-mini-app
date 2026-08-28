import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CardioQuickLog } from '../../../../src/features/cardio/CardioLogging';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());
const trackProductEventMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/shared/analytics/productEvents', () => ({
  productEventSurface: () => 'mobile_web',
  trackProductEvent: trackProductEventMock,
}));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { profile: { timezone: 'Europe/Moscow' } } }),
}));

function renderCardio() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <CardioQuickLog today="2030-01-10" />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('CardioQuickLog', () => {
  beforeEach(() => {
    apiMock.mockReset();
    apiMock.mockResolvedValue([]);
    trackProductEventMock.mockReset();
  });

  afterEach(() => cleanup());

  it('validates required duration next to the field before calling the API', async () => {
    renderCardio();
    await screen.findByText('Кардио пока не записано');

    fireEvent.change(screen.getByLabelText('Длительность, мин'), { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить кардио' }));

    expect(screen.getByText('Укажите длительность от 1 до 600 минут.')).toBeVisible();
    expect(apiMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(0);
  });

  it('keeps the draft and idempotency key after a failed save, then refreshes the list', async () => {
    let saved: Record<string, unknown> | null = null;
    let postAttempts = 0;
    apiMock.mockImplementation(
      async (path: string, options?: { method?: string; body?: unknown }) => {
        if (options?.method === 'POST') {
          postAttempts += 1;
          if (postAttempts === 1) throw new Error('Временная ошибка сохранения');
          const body = options.body as Record<string, unknown>;
          saved = {
            ...body,
            id: 66,
            source: 'manual',
            completed_at: body.scheduled_at,
            created_at: '2030-01-10T12:00:00',
            updated_at: '2030-01-10T12:00:00',
          };
          return saved;
        }
        if (options?.method === 'PATCH') {
          saved = { ...saved, ...(options.body as Record<string, unknown>) };
          return saved;
        }
        if (path.startsWith('/api/v1/workouts/cardio')) return saved ? [saved] : [];
        return null;
      },
    );
    renderCardio();
    await screen.findByText('Кардио пока не записано');

    fireEvent.change(screen.getByLabelText('Длительность, мин'), { target: { value: '35' } });
    fireEvent.click(screen.getByText('Дистанция, пульс и заметка'));
    fireEvent.change(screen.getByLabelText('Заметка'), { target: { value: 'Ровный темп' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить кардио' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Временная ошибка сохранения');
    expect(screen.getByLabelText('Длительность, мин')).toHaveValue(35);
    expect(screen.getByLabelText('Заметка')).toHaveValue('Ровный темп');
    expect(trackProductEventMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить кардио' }));
    await waitFor(() => expect(postAttempts).toBe(2));
    await screen.findByText('35 мин');

    const posts = apiMock.mock.calls.filter((call) => call[1]?.method === 'POST');
    expect(posts[0]![1].body.client_request_id).toBe(posts[1]![1].body.client_request_id);
    expect(trackProductEventMock).toHaveBeenCalledWith({
      name: 'cardio_logged',
      surface: 'mobile_web',
    });

    fireEvent.click(screen.getByRole('button', { name: 'Изменить' }));
    const saveChanges = screen.getByRole('button', { name: 'Сохранить изменения' });
    const editForm = saveChanges.closest('form');
    expect(editForm).not.toBeNull();
    fireEvent.change(within(editForm!).getByLabelText('Длительность, мин'), {
      target: { value: '40' },
    });
    fireEvent.click(saveChanges);
    await waitFor(() =>
      expect(apiMock.mock.calls.filter((call) => call[1]?.method === 'PATCH')).toHaveLength(1),
    );
    expect(trackProductEventMock).toHaveBeenCalledTimes(1);
  });
});
