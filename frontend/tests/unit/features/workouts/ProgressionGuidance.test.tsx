import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Workout } from '../../../../src/shared/api/types';
import { ProgressionGuidance } from '../../../../src/features/workouts/ProgressionGuidance';

type Guidance = NonNullable<Workout['exercises'][number]['progression_guidance']>;

afterEach(cleanup);

function guidance(overrides: Partial<Guidance> = {}): Guidance {
  return {
    ruleset_version: 'progression-guidance-v1',
    outcome: 'consider_progressing',
    message: 'Можно рассмотреть небольшое увеличение веса',
    detail:
      'Верхняя граница повторений стабильно достигнута. Доступный шаг оборудования учтён; решение остаётся за вами.',
    suggested_increment: 2.5,
    suggested_weight: 42.5,
    load_unit: 'kg',
    evidence: {
      target_reps_min: 8,
      target_reps_max: 10,
      prescribed_sets: 3,
      comparable_session_count: 2,
      required_session_count: 2,
      working_set_count: 6,
      rir_recorded_set_count: 6,
      reason_keys: ['top_range_repeated', 'full_rir_coverage'],
      sessions: [
        {
          workout_id: 31,
          scheduled_date: '2026-08-17',
          working_set_count: 3,
          load: 40,
          load_unit: 'kg',
          reps_min: 10,
          reps_max: 10,
          rir_recorded_set_count: 3,
          rir_values: ['1', '2', '2'],
          reached_failure: false,
          completion_feedback: 'as_expected',
        },
      ],
    },
    ...overrides,
  };
}

describe('ProgressionGuidance', () => {
  it('shows factual evidence and applies an exact configured step only once', () => {
    const onApply = vi.fn();
    render(
      <ProgressionGuidance
        exerciseKey={101}
        guidance={guidance()}
        onApply={onApply}
        onDismiss={() => undefined}
      />,
    );

    expect(screen.getByText('Можно рассмотреть небольшое увеличение веса')).toBeVisible();
    fireEvent.click(screen.getByText('Почему?'));
    expect(screen.getByText('Цель: 3 × 8–10')).toBeVisible();
    expect(screen.getByText(/40 кг · 10 повторов/)).toBeVisible();
    expect(screen.getByText(/тренировка: нормально/)).toBeVisible();

    const apply = screen.getByRole('button', { name: 'Подставить 42,5 кг' });
    fireEvent.click(apply);
    fireEvent.click(apply);
    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it('keeps insufficient data plain and dismissible without an apply action', () => {
    const onDismiss = vi.fn();
    render(
      <ProgressionGuidance
        exerciseKey={102}
        guidance={guidance({
          outcome: 'review',
          message: 'Данных недостаточно — сначала закрепите текущий диапазон повторений',
          suggested_increment: null,
          suggested_weight: null,
          evidence: {
            ...guidance().evidence,
            comparable_session_count: 0,
            working_set_count: 0,
            rir_recorded_set_count: 0,
            sessions: [],
          },
        })}
        onDismiss={onDismiss}
      />,
    );

    expect(screen.queryByRole('button', { name: /Подставить/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Скрыть подсказку' }));
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});
