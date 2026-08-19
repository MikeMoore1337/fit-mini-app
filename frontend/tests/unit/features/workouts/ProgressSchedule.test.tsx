import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    scheduled_time: '18:30:00',
    title: 'Тренировка A',
    status: 'planned',
    day_number: 1,
    week_number: 1,
  },
];

const weeklyCheckIn = {
  week_start: '2030-01-07',
  week_end: '2030-01-13',
  submitted_on: '2030-01-10',
  timezone: 'Europe/Moscow',
  existing: null,
  summary: {
    ruleset_version: 'weekly-check-in-summary-v1',
    period_start: '2030-01-07',
    period_end: '2030-01-10',
    goal: 'maintenance',
    training: {
      planned_workouts: 2,
      completed_workouts: 1,
      adherence: { status: 'available', percent: 50, achieved: 1, evaluated: 2, weight: 0.4 },
    },
    nutrition: {
      logged_days: 3,
      average_calories: 2000,
      target_calories: 2000,
      average_protein_g: 140,
      target_protein_g: 150,
      calories_adherence: {
        status: 'available',
        percent: 100,
        achieved: 3,
        evaluated: 3,
        weight: 0.2,
      },
      protein_adherence: {
        status: 'available',
        percent: 66.7,
        achieved: 2,
        evaluated: 3,
        weight: 0.2,
      },
    },
    weight_trend: null,
    anthropometry_trends: [],
    body_priority: null,
    progression: { training_volume_kg: 1200, new_personal_records: 1 },
    data_sufficiency: {},
  },
};

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
      if (path === '/api/v1/check-ins/weekly/current') {
        return new Response(JSON.stringify(weeklyCheckIn), { status: 200 });
      }
      if (path === '/api/v1/check-ins/weekly?limit=4&offset=0') {
        return new Response(JSON.stringify({ items: [], total: 0, limit: 4, offset: 0 }), {
          status: 200,
        });
      }
      if (path === '/api/v1/check-ins/weekly' && init?.method === 'POST') {
        return new Response(JSON.stringify({ id: 1 }), { status: 201 });
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

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('shows progress and sends a reschedule request', async () => {
    renderPanel();

    expect(await screen.findByText('80%')).toBeInTheDocument();
    expect(screen.getByText('Тренировка A')).toBeInTheDocument();
    expect(screen.getByText('Запланирована')).toBeInTheDocument();
    expect(screen.queryByText('planned')).not.toBeInTheDocument();

    const input = screen.getByLabelText('Новая дата для Тренировка A');
    fireEvent.change(input, { target: { value: '2030-01-12' } });
    fireEvent.change(screen.getByLabelText('Новое время для Тренировка A'), {
      target: { value: '19:15' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Перенести' }));

    await waitFor(() =>
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/workouts/42/schedule',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ scheduled_date: '2030-01-12', scheduled_time: '19:15' }),
        }),
      ),
    );
  });

  it('submits optional weekly self-assessment', async () => {
    renderPanel();

    expect(await screen.findByText('Еженедельные итоги')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('combobox', { name: /Как вы восстановились/ }), {
      target: { value: '4' },
    });
    fireEvent.change(screen.getByLabelText('Заметка о неделе'), {
      target: { value: 'Больше сна' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить итоги' }));

    await waitFor(() =>
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/check-ins/weekly',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            status: 'completed',
            training_load: null,
            recovery: 4,
            hunger: null,
            adherence_difficulty: null,
            note: 'Больше сна',
          }),
        }),
      ),
    );
  });
});
