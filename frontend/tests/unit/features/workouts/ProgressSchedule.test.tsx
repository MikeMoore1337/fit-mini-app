import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProgressSchedule } from '../../../../src/features/workouts/ProgressSchedule';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const progress = {
  user_id: 7,
  period_days: 30,
  period_start: '2029-12-12',
  period_end: '2030-01-10',
  training: {
    planned_workouts: 5,
    completed_workouts: 4,
    frequency_per_week: 1.2,
    volume_kg: 1200,
    new_personal_records: 1,
    last_completed_workout_on: '2030-01-09',
    next_workout: null,
  },
  nutrition: {
    visible: true,
    logged_days: 4,
    adherence_evaluated_days: 4,
    average_calories: 2000,
    target_calories: 2100,
    average_protein_g: 140,
    target_protein_g: 150,
    target_effective_on: '2029-12-01',
  },
  body: {
    latest_measurement: null,
    trends: [],
    priority: null,
    guidance: {
      comparison_basis: 'self',
      minimum_points_for_interpretation: 3,
      minimum_span_days_for_interpretation: 14,
      consistency_tips: [],
      circumference_limitations: [],
    },
  },
  adherence: {
    formula_version: 'adherence-v1',
    overall_percent: 80,
    included_components: ['workouts', 'calories', 'protein'],
    workouts: { status: 'available', percent: 80, achieved: 4, evaluated: 5, weight: 0.4 },
    cardio: { status: 'unsupported', percent: null, achieved: 0, evaluated: 0, weight: 0.2 },
    calories: { status: 'available', percent: 75, achieved: 3, evaluated: 4, weight: 0.2 },
    protein: { status: 'available', percent: 75, achieved: 3, evaluated: 4, weight: 0.2 },
  },
  data_sufficiency: {
    ruleset_version: 'data-sufficiency-v1',
    workout_logging: { status: 'sufficient', counters: {}, reason_keys: ['thresholds_met'] },
    working_sets: { status: 'limited', counters: {}, reason_keys: ['too_few_working_sets'] },
    rir_coverage: { status: 'insufficient', counters: {}, reason_keys: ['no_rir_observations'] },
    nutrition_coverage: {
      status: 'limited',
      counters: {},
      reason_keys: ['below_required_coverage'],
    },
    weight_trend: { status: 'insufficient', counters: {}, reason_keys: ['no_measurements'] },
    anthropometry: {
      status: 'insufficient',
      counters: {},
      reason_keys: ['no_anthropometry_measurements'],
    },
    schedule_adherence: { status: 'sufficient', counters: {}, reason_keys: ['thresholds_met'] },
  },
};

const trainingAnalytics = {
  period_days: 30,
  period_start: '2029-12-12',
  period_end: '2030-01-10',
  exercise_history_limit: 20,
  completed_set_count: 12,
  reps_total: 96,
  reps_recorded_sets: 12,
  external_load_volume_kg: 1200,
  volume_recorded_sets: 12,
  exercises: [],
  rir: { completed_set_count: 12, recorded_set_count: 0, missing_set_count: 12, distribution: [] },
  primary_muscle_exposure: [],
  secondary_muscle_exposure: [],
  completed_sets_without_muscle_metadata: 12,
  data_sufficiency: {
    ruleset_version: 'data-sufficiency-v1',
    workout_logging: { status: 'sufficient', counters: {}, reason_keys: ['thresholds_met'] },
    working_sets: { status: 'limited', counters: {}, reason_keys: ['too_few_working_sets'] },
    rir_coverage: { status: 'insufficient', counters: {}, reason_keys: ['no_rir_observations'] },
  },
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
      if (path === '/api/v1/workouts/progress/summary?period_days=30') {
        return new Response(JSON.stringify(progress), { status: 200 });
      }
      if (path === '/api/v1/workouts/progress/training-analytics?period_days=30') {
        return new Response(JSON.stringify(trainingAnalytics), { status: 200 });
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

    expect((await screen.findAllByText('80%')).length).toBeGreaterThan(1);
    expect(screen.getByRole('heading', { name: 'Прогресс' })).toBeInTheDocument();
    expect(screen.getByText('Замеров за этот период нет')).toBeInTheDocument();
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
