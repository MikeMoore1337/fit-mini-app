import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WorkoutAdaptation } from '../../../../src/features/workouts/WorkoutAdaptation';
import type { Workout } from '../../../../src/shared/api/types';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const workout: Workout = {
  id: 42,
  scheduled_date: '2030-01-10',
  title: 'Тренировка A',
  status: 'planned',
  day_number: 1,
  week_number: 1,
  exercises: [
    {
      id: 101,
      exercise_id: 11,
      exercise_title: 'Жим штанги лежа',
      sort_order: 1,
      prescribed_sets: 3,
      prescribed_reps: '8-10',
      rest_seconds: 90,
      has_guide: true,
      sets: [{ id: 201, set_number: 1, is_completed: false, version: 1 }],
    },
    {
      id: 102,
      exercise_id: 12,
      exercise_title: 'Разведение гантелей',
      sort_order: 3,
      prescribed_sets: 3,
      prescribed_reps: '10-12',
      rest_seconds: 60,
      has_guide: true,
      sets: [{ id: 202, set_number: 1, is_completed: false, version: 1 }],
    },
  ],
};

const preview = {
  status: 'preview',
  workout_id: 42,
  reason: 'limited_time',
  ruleset_version: 'workout-adaptation-v1',
  original_estimated_minutes: 32,
  adapted_estimated_minutes: 18,
  time_budget_minutes: 20,
  changes: [
    {
      kind: 'removed',
      workout_exercise_id: 102,
      from_exercise_id: 12,
      from_title: 'Разведение гантелей',
    },
  ],
  original_exercises: [],
  adapted_exercises: [],
  warnings: [],
  message: 'Проверьте изменения перед применением.',
  preview_token: 'a'.repeat(64),
};

function renderAdaptation(safetyOnly = false) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <WorkoutAdaptation workout={workout} safetyOnly={safetyOnly} />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('WorkoutAdaptation', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('показывает diff до применения и позволяет отменить без записи', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify(preview), { status: 200 }));
    const user = userEvent.setup();
    renderAdaptation();

    await user.click(screen.getByRole('button', { name: 'Адаптировать тренировку' }));
    await user.clear(screen.getByRole('spinbutton', { name: 'Сколько минут есть на тренировку?' }));
    await user.type(
      screen.getByRole('spinbutton', { name: 'Сколько минут есть на тренировку?' }),
      '20',
    );
    await user.click(screen.getByRole('button', { name: 'Показать изменения' }));

    expect(await screen.findByText('Убрать «Разведение гантелей»')).toBeInTheDocument();
    expect(screen.getByText('Расчётное время: 32 → 18 мин.')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole('button', { name: 'Отмена' }));
    expect(screen.getByRole('button', { name: 'Адаптировать тренировку' })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('применяет только после отдельного подтверждения', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith('/adaptations/preview')) {
        return new Response(JSON.stringify(preview), { status: 200 });
      }
      if (path.endsWith('/adaptations/apply')) {
        return new Response(
          JSON.stringify({ adaptation_id: 9, applied_at: '2030-01-10T10:00:00', workout }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
    const user = userEvent.setup();
    renderAdaptation();

    await user.click(screen.getByRole('button', { name: 'Адаптировать тренировку' }));
    await user.clear(screen.getByRole('spinbutton', { name: 'Сколько минут есть на тренировку?' }));
    await user.type(
      screen.getByRole('spinbutton', { name: 'Сколько минут есть на тренировку?' }),
      '20',
    );
    await user.click(screen.getByRole('button', { name: 'Показать изменения' }));
    await screen.findByText('Убрать «Разведение гантелей»');
    await user.click(screen.getByRole('button', { name: 'Подтвердить и применить' }));

    expect(screen.getByRole('dialog', { name: 'Применить изменения?' })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole('button', { name: 'Применить' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const applyCall = fetchMock.mock.calls[1]!;
    expect(String(applyCall[0])).toContain('/adaptations/apply');
    expect(String((applyCall[1] as RequestInit).body)).toContain('"preview_token"');
  });

  it('во время тренировки оставляет только безопасный сценарий боли', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          ...preview,
          status: 'safety_stop',
          reason: 'pain_or_injury',
          changes: [],
          message: 'Приложение не подбирает медицинскую замену.',
          preview_token: null,
        }),
        { status: 200 },
      ),
    );
    const user = userEvent.setup();
    renderAdaptation(true);

    await user.click(screen.getByRole('button', { name: 'Боль или травма во время тренировки' }));
    expect(screen.getByRole('combobox', { name: 'Почему нужно изменить тренировку?' })).toHaveValue(
      'pain_or_injury',
    );
    expect(screen.getAllByRole('option')).toHaveLength(1);
    await user.click(screen.getByRole('button', { name: 'Показать изменения' }));
    expect(await screen.findByText('Безопасность прежде всего')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Подтвердить и применить' }),
    ).not.toBeInTheDocument();
  });
});
