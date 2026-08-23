import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EnergyCalibrationCard } from '../../../../src/features/nutrition/EnergyCalibrationCard';
import type { EnergyCalibration, NutritionTarget } from '../../../../src/shared/api/types';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));

const target: NutritionTarget = {
  id: 1,
  user_id: 10,
  telegram_user_id: 1001,
  effective_from: '2026-08-19',
  source: 'calculated',
  created_at: '2026-08-19T10:00:00',
  sex: 'male',
  weight_kg: 80,
  height_cm: 180,
  age: 32,
  daily_routine: 'mixed',
  steps_range: 'from_7000_to_10000',
  strength_trainings_per_week: 3,
  strength_training_duration_minutes: 60,
  strength_training_type: 'regular',
  strength_rest: 'one_to_two',
  cardio_trainings: [],
  goal: 'maintenance',
  bmr: 1750,
  tdee: 2000,
  calories: 2000,
  protein_g: 144,
  fat_g: 72,
  carbs_g: 194,
  saved_at: '2026-08-19T10:00:00',
  assigned_by: null,
  daily_activity_level: 'moderate',
  cardio_trainings_per_week: 0,
  cardio_training_duration_minutes: 30,
  cardio_intensity: 'moderate',
};

const pending: EnergyCalibration = {
  id: 17,
  status: 'pending',
  ruleset_version: 'adaptive-energy-v1',
  period_start: '2026-07-22',
  period_end: '2026-08-18',
  sufficiency: {
    status: 'sufficient',
    counters: { logged_day_count: 28 },
    reason_keys: ['thresholds_met'],
  },
  average_intake_kcal: 2600,
  smoothed_start_weight_kg: 80,
  smoothed_end_weight_kg: 80,
  estimated_expenditure_kcal: 2600,
  estimate_low_kcal: 2350,
  estimate_high_kcal: 2850,
  goal: 'maintenance',
  current_target_calories: 2000,
  proposed_target_calories: 2200,
  rationale: ['Среднее потребление по заполненным дням: 2600 ккал.'],
  created_at: '2026-08-19T10:00:00',
  decided_at: null,
};

function renderCard(onAccepted = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <EnergyCalibrationCard target={target} onAccepted={onAccepted} />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
  return onAccepted;
}

describe('EnergyCalibrationCard', () => {
  beforeEach(() => {
    apiMock.mockReset();
    apiMock.mockImplementation((path: string) => {
      if (path.endsWith('/history')) return Promise.resolve({ items: [] });
      if (path.endsWith('/preview')) return Promise.resolve(pending);
      if (path.endsWith('/decision')) return Promise.resolve({ ...pending, status: 'accepted' });
      throw new Error(`Unexpected API path: ${path}`);
    });
  });

  afterEach(cleanup);

  it('shows a preview and applies it only after explicit confirmation', async () => {
    const onAccepted = renderCard();
    await waitFor(() => expect(apiMock).toHaveBeenCalledWith(expect.stringMatching(/history$/)));

    fireEvent.click(screen.getByRole('button', { name: 'Проверить по истории' }));

    expect(await screen.findByText('Ожидает решения')).toBeInTheDocument();
    expect(screen.getByText(/Предлагаемая цель:/)).toHaveTextContent('2200 ккал');
    fireEvent.click(screen.getByRole('button', { name: 'Подтвердить новую цель' }));

    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith(
        '/api/v1/nutrition/energy-calibration/17/decision',
        expect.objectContaining({ method: 'POST', body: { decision: 'accept' } }),
      ),
    );
    await waitFor(() => expect(onAccepted).toHaveBeenCalledOnce());
  });

  it('explains insufficient data without offering a target change', async () => {
    apiMock.mockImplementation((path: string) => {
      if (path.endsWith('/history')) return Promise.resolve({ items: [] });
      return Promise.resolve({
        ...pending,
        id: null,
        status: 'insufficient',
        estimated_expenditure_kcal: null,
        estimate_low_kcal: null,
        estimate_high_kcal: null,
        proposed_target_calories: null,
        rationale: ['Пока недостаточно заполненных дней питания и регулярных замеров массы.'],
      });
    });
    renderCard();

    fireEvent.click(screen.getByRole('button', { name: 'Проверить по истории' }));

    expect(await screen.findByText('Недостаточно данных')).toBeInTheDocument();
    expect(screen.getByText(/Пока недостаточно заполненных дней/)).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Подтвердить новую цель' }),
    ).not.toBeInTheDocument();
  });
});
