import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProgressSchedule } from '../../../../src/features/workouts/ProgressSchedule';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const progress = {
  workouts_total: 5,
  workouts_completed: 4,
  workouts_skipped: 1,
  workouts_missed: 0,
  adherence_percent: 80,
  current_streak: 3,
  weight_change_kg: -1.5,
  weights: [],
  weekly_volume: [{ week_start: '2030-01-07', completed_workouts: 2, volume_kg: 1200 }],
  personal_records: [
    {
      exercise_id: 7,
      exercise_title: 'Приседания',
      max_weight_kg: 80,
      best_set_volume_kg: 800,
      last_performed_on: '2030-01-09',
    },
  ],
};

const schedule = [
  {
    id: 42,
    scheduled_date: '2030-01-10',
    title: 'Тренировка A',
    status: 'planned',
    day_number: 1,
    week_number: 1,
  },
];

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <ProgressSchedule />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('ProgressSchedule', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === '/api/v1/workouts/progress') {
        return new Response(JSON.stringify(progress), { status: 200 });
      }
      if (path === '/api/v1/workouts/schedule' && (!init?.method || init.method === 'GET')) {
        return new Response(JSON.stringify(schedule), { status: 200 });
      }
      if (path === '/api/v1/workouts/42/schedule' && init?.method === 'PATCH') {
        return new Response(JSON.stringify({ ...schedule[0], scheduled_date: '2030-01-12' }), {
          status: 200,
        });
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => vi.restoreAllMocks());

  it('shows progress and sends a reschedule request', async () => {
    renderPanel();

    expect(await screen.findByText('80%')).toBeInTheDocument();
    expect(screen.getByText('Тренировка A')).toBeInTheDocument();
    expect(screen.getByText('Запланирована')).toBeInTheDocument();
    expect(screen.queryByText('planned')).not.toBeInTheDocument();

    const input = screen.getByLabelText('Новая дата для Тренировка A');
    fireEvent.change(input, { target: { value: '2030-01-12' } });
    fireEvent.click(screen.getByRole('button', { name: 'Перенести' }));

    await waitFor(() =>
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/workouts/42/schedule',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ scheduled_date: '2030-01-12' }),
        }),
      ),
    );
  });
});
