import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProgressExperience } from '../../../../src/features/workouts/ProgressExperience';
import type { ProgressSummary, TrainingAnalytics } from '../../../../src/shared/api/types';

const signal = (
  status: 'sufficient' | 'limited' | 'insufficient',
): ProgressSummary['data_sufficiency']['weight_trend'] => ({
  status,
  counters: {},
  reason_keys: status === 'sufficient' ? ['thresholds_met'] : ['too_few_points'],
});

function makeSummary(): ProgressSummary {
  return {
    user_id: 7,
    period_days: 30,
    period_start: '2030-01-01',
    period_end: '2030-01-30',
    training: {
      planned_workouts: 8,
      completed_workouts: 7,
      frequency_per_week: 1.63,
      volume_kg: 12400,
      new_personal_records: 3,
      last_completed_workout_on: '2030-01-28',
      next_workout: null,
    },
    nutrition: {
      visible: true,
      logged_days: 20,
      adherence_evaluated_days: 18,
      average_calories: 1980,
      target_calories: 2100,
      average_protein_g: 132,
      target_protein_g: 140,
      target_effective_on: '2029-12-01',
    },
    body: {
      latest_measurement: { measured_on: '2030-01-29', weight_kg: 68.4, waist_cm: 72 },
      trends: [
        {
          metric: 'weight_kg',
          first_value: 69.4,
          latest_value: 68.4,
          change: -1,
          first_measured_on: '2030-01-02',
          latest_measured_on: '2030-01-29',
          point_count: 4,
          span_days: 27,
          interpretation_status: 'available',
          points: [
            { measured_on: '2030-01-02', value: 69.4 },
            { measured_on: '2030-01-05', value: 69.1 },
            { measured_on: '2030-01-22', value: 68.8 },
            { measured_on: '2030-01-29', value: 68.4 },
          ],
        },
        {
          metric: 'waist_cm',
          first_value: 73,
          latest_value: 72,
          change: -1,
          first_measured_on: '2030-01-02',
          latest_measured_on: '2030-01-29',
          point_count: 2,
          span_days: 27,
          interpretation_status: 'insufficient_points',
          points: [
            { measured_on: '2030-01-02', value: 73 },
            { measured_on: '2030-01-29', value: 72 },
          ],
        },
      ],
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
      overall_percent: 84,
      included_components: ['workouts', 'calories', 'protein'],
      workouts: { status: 'available', percent: 87.5, achieved: 7, evaluated: 8, weight: 0.4 },
      cardio: { status: 'unsupported', percent: null, achieved: 0, evaluated: 0, weight: 0.2 },
      calories: { status: 'available', percent: 83.3, achieved: 15, evaluated: 18, weight: 0.2 },
      protein: { status: 'available', percent: 72.2, achieved: 13, evaluated: 18, weight: 0.2 },
    },
    data_sufficiency: {
      ruleset_version: 'data-sufficiency-v1',
      workout_logging: signal('sufficient'),
      working_sets: signal('sufficient'),
      rir_coverage: signal('limited'),
      nutrition_coverage: signal('sufficient'),
      weight_trend: signal('sufficient'),
      anthropometry: signal('limited'),
      schedule_adherence: signal('sufficient'),
    },
  };
}

function makeAnalytics(): TrainingAnalytics {
  return {
    period_days: 30,
    period_start: '2030-01-01',
    period_end: '2030-01-30',
    exercise_history_limit: 20,
    completed_set_count: 28,
    reps_total: 226,
    reps_recorded_sets: 28,
    external_load_volume_kg: 12400,
    volume_recorded_sets: 24,
    exercises: [
      {
        exercise_id: 11,
        exercise_title: 'Жим штанги лёжа',
        uses_bodyweight_equipment: false,
        performed_session_count: 6,
        completed_set_count: 18,
        first_performed_on: '2030-01-03',
        last_performed_on: '2030-01-28',
        reps_total: 144,
        reps_recorded_sets: 18,
        max_external_load_kg: 62.5,
        best_set_volume_kg: 500,
        external_load_volume_kg: 7200,
        volume_recorded_sets: 18,
        history_truncated: true,
        sessions: [
          {
            workout_id: 42,
            workout_exercise_id: 101,
            performed_on: '2030-01-28',
            completed_set_count: 2,
            reps_total: 16,
            reps_recorded_sets: 2,
            max_external_load_kg: 62.5,
            external_load_volume_kg: 980,
            volume_recorded_sets: 2,
            sets: [
              {
                set_number: 1,
                reps: 8,
                external_load_kg: 60,
                external_load_volume_kg: 480,
                rir: '2',
                set_kind: 'working',
                reached_failure: false,
              },
              {
                set_number: 2,
                reps: 8,
                external_load_kg: 62.5,
                external_load_volume_kg: 500,
                rir: null,
                set_kind: 'working',
                reached_failure: false,
              },
            ],
          },
        ],
      },
    ],
    rir: {
      completed_set_count: 28,
      recorded_set_count: 16,
      missing_set_count: 12,
      distribution: [],
    },
    primary_muscle_exposure: [
      { muscle_id: 'chest', muscle_name: 'Грудные', completed_set_count: 18 },
    ],
    secondary_muscle_exposure: [
      { muscle_id: 'triceps', muscle_name: 'Трицепс', completed_set_count: 18 },
    ],
    completed_sets_without_muscle_metadata: 0,
    data_sufficiency: {
      ruleset_version: 'data-sufficiency-v1',
      workout_logging: signal('sufficient'),
      working_sets: signal('sufficient'),
      rir_coverage: signal('limited'),
    },
  };
}

function installApi({
  analytics = makeAnalytics(),
  failSummary = false,
  pending = false,
  summary = makeSummary(),
}: {
  analytics?: ReturnType<typeof makeAnalytics>;
  failSummary?: boolean;
  pending?: boolean;
  summary?: ReturnType<typeof makeSummary>;
} = {}) {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    if (pending) return new Promise<Response>(() => undefined);
    const path = String(input);
    const period = Number(new URL(path, 'http://test.local').searchParams.get('period_days')) || 30;
    if (path.startsWith('/api/v1/workouts/progress/summary')) {
      if (failSummary) {
        return new Response(JSON.stringify({ detail: 'Сводка временно недоступна' }), {
          status: 503,
        });
      }
      return new Response(JSON.stringify({ ...summary, period_days: period }), { status: 200 });
    }
    if (path.startsWith('/api/v1/workouts/progress/training-analytics')) {
      return new Response(JSON.stringify({ ...analytics, period_days: period }), { status: 200 });
    }
    return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
  });
}

function renderExperience() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ProgressExperience />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ProgressExperience', () => {
  it('shows backend summaries, factual body points and workout detail', async () => {
    installApi();
    renderExperience();

    expect(await screen.findAllByText('84%')).toHaveLength(2);
    expect(screen.getByRole('heading', { name: 'Прогресс' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Тренировки' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Тело' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Питание' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Соблюдение плана' })).toBeVisible();
    expect(screen.getByRole('img', { name: /Вес: 2 янв. — 69,4 кг/ })).toBeVisible();

    fireEvent.click(screen.getByText('Жим штанги лёжа'));
    expect(screen.getByText('Детали тренировки')).toBeVisible();
    expect(screen.getByText('Показаны последние 20 тренировок упражнения.')).toBeVisible();
    expect(screen.queryByText('too_few_points')).not.toBeInTheDocument();
  });

  it('requests both backend aggregates when the period changes', async () => {
    installApi();
    renderExperience();
    await screen.findAllByText('84%');

    fireEvent.click(screen.getByRole('tab', { name: '7 дней' }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/workouts/progress/summary?period_days=7',
        expect.anything(),
      );
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/v1/workouts/progress/training-analytics?period_days=7',
        expect.anything(),
      );
    });
  });

  it('keeps empty, one-point and partial adherence states factual', async () => {
    const summary = makeSummary();
    summary.training.planned_workouts = 0;
    summary.training.completed_workouts = 0;
    summary.training.new_personal_records = 0;
    summary.nutrition.logged_days = 0;
    const weightTrend = summary.body.trends[0];
    if (!weightTrend) throw new Error('Weight trend fixture is missing');
    summary.body.trends = [
      {
        ...weightTrend,
        first_value: 68.4,
        latest_value: 68.4,
        change: null,
        first_measured_on: '2030-01-29',
        latest_measured_on: '2030-01-29',
        point_count: 1,
        span_days: 0,
        interpretation_status: 'single_point',
        points: [{ measured_on: '2030-01-29', value: 68.4 }],
      },
    ];
    summary.adherence.overall_percent = null;
    summary.adherence.included_components = [];
    summary.adherence.workouts = {
      status: 'not_applicable',
      percent: null,
      achieved: 0,
      evaluated: 0,
      weight: 0.4,
    };
    summary.adherence.calories = {
      status: 'insufficient_data',
      percent: null,
      achieved: 0,
      evaluated: 0,
      weight: 0.2,
    };
    const analytics = makeAnalytics();
    analytics.exercises = [];
    analytics.completed_set_count = 0;
    analytics.external_load_volume_kg = null;
    installApi({ summary, analytics });
    renderExperience();

    expect(await screen.findByText('Пока не оценить')).toBeVisible();
    expect(screen.getByText('0 новых рекордов')).toBeVisible();
    expect(screen.getByText('История упражнений пока пуста')).toBeVisible();
    expect(screen.getByText('Питание за период не записано')).toBeVisible();
    expect(screen.getByText('Один замер')).toBeVisible();
    expect(screen.getByText('Нет цели или плана')).toBeVisible();
    expect(screen.getAllByText('Мало данных').length).toBeGreaterThan(0);
  });

  it('shows a loading state without inventing zero values', () => {
    installApi({ pending: true });
    renderExperience();

    expect(screen.getByText('Собираем динамику за период…')).toBeVisible();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('keeps training analytics available when the main summary fails', async () => {
    installApi({ failSummary: true });
    renderExperience();

    expect(await screen.findByRole('alert')).toHaveTextContent('Сводка временно недоступна');
    expect(await screen.findByText('Жим штанги лёжа')).toBeVisible();
    expect(screen.getByText('28')).toBeVisible();
  });
});
