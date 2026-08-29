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

const plannedSession = {
  id: 65,
  activity_type: 'walking',
  duration_minutes: 30,
  distance_km: null,
  average_heart_rate_bpm: null,
  heart_rate_zone: null,
  note: null,
  scheduled_at: '2030-01-10T09:00:00',
  completed_at: null,
  status: 'planned',
  source: 'manual',
  created_at: '2030-01-09T12:00:00',
  updated_at: '2030-01-09T12:00:00',
};

describe('CardioQuickLog', () => {
  beforeEach(() => {
    apiMock.mockReset();
    apiMock.mockResolvedValue([plannedSession]);
    trackProductEventMock.mockReset();
  });

  afterEach(() => cleanup());

  it('does not show a cardio entry prompt on an unplanned empty day', async () => {
    apiMock.mockResolvedValue([]);
    renderCardio();

    await waitFor(() => expect(apiMock).toHaveBeenCalled());
    expect(screen.queryByRole('heading', { name: 'Кардио' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /кардио/i })).not.toBeInTheDocument();
  });

  it('shows the plan before a secondary factual entry and validates required duration', async () => {
    renderCardio();
    await screen.findByRole('heading', { name: 'План кардио' });

    const openForm = screen.getByRole('button', { name: 'Добавить фактическое кардио' });
    expect(screen.queryByLabelText('Длительность, мин')).not.toBeInTheDocument();
    fireEvent.click(openForm);

    expect(screen.queryByLabelText('Статус')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Длительность, мин'), { target: { value: '0' } });
    expect(screen.getByRole('button', { name: 'Сохранить кардио' })).toBeDisabled();
    expect(apiMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(0);
  });

  it('resets an open draft to the newly selected day', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    const ui = (today: string) => (
      <QueryClientProvider client={queryClient}>
        <FeedbackProvider>
          <CardioQuickLog today={today} />
        </FeedbackProvider>
      </QueryClientProvider>
    );
    const view = render(ui('2030-01-10'));
    await screen.findByRole('heading', { name: 'План кардио' });
    fireEvent.click(screen.getByRole('button', { name: 'Добавить фактическое кардио' }));
    expect((screen.getByLabelText('Дата и время') as HTMLInputElement).value).toMatch(
      /^2030-01-10T/,
    );

    view.rerender(ui('2030-01-11'));

    expect(((await screen.findByLabelText('Дата и время')) as HTMLInputElement).value).toMatch(
      /^2030-01-11T/,
    );
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
        if (path.startsWith('/api/v1/workouts/cardio')) return saved ? [saved] : [plannedSession];
        return null;
      },
    );
    renderCardio();
    await screen.findByRole('heading', { name: 'План кардио' });
    fireEvent.click(screen.getByRole('button', { name: 'Добавить фактическое кардио' }));

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
    expect(screen.queryByLabelText('Длительность, мин')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Результат кардио' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Добавить ещё кардио' })).toBeVisible();

    const posts = apiMock.mock.calls.filter((call) => call[1]?.method === 'POST');
    expect(posts[0]![1].body.client_request_id).toBe(posts[1]![1].body.client_request_id);
    expect(trackProductEventMock).toHaveBeenCalledWith({
      name: 'cardio_logged',
      surface: 'mobile_web',
    });

    fireEvent.click(screen.getByRole('button', { name: 'Изменить' }));
    const saveChanges = screen.getByRole('button', { name: 'Сохранить изменения' });
    expect(saveChanges).toBeDisabled();
    const editForm = saveChanges.closest('form');
    expect(editForm).not.toBeNull();
    fireEvent.change(within(editForm!).getByLabelText('Длительность, мин'), {
      target: { value: '40' },
    });
    expect(saveChanges).toBeEnabled();
    fireEvent.click(saveChanges);
    await waitFor(() =>
      expect(apiMock.mock.calls.filter((call) => call[1]?.method === 'PATCH')).toHaveLength(1),
    );
    expect(trackProductEventMock).toHaveBeenCalledTimes(1);
  });
});
