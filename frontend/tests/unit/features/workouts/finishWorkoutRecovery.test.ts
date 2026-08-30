import { QueryClient } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  activeWorkoutQueueKey,
  activeWorkoutRestKey,
  clearActiveWorkoutData,
  saveActiveWorkoutSnapshot,
} from '../../../../src/features/workouts/activeWorkoutQueue';
import { reconcileFinishedWorkout } from '../../../../src/features/workouts/finishWorkoutRecovery';
import type { Workout } from '../../../../src/shared/api/types';

const activeWorkout: Workout = {
  id: 42,
  scheduled_date: '2030-01-10',
  title: 'Тренировка A',
  status: 'in_progress',
  day_number: 1,
  week_number: 1,
  started_at: '2030-01-10T10:00:00',
  exercises: [
    {
      id: 101,
      exercise_id: 11,
      exercise_title: 'Жим штанги лежа',
      metric_type: 'strength',
      sort_order: 1,
      prescribed_sets: 1,
      prescribed_reps: '8-10',
      rest_seconds: 90,
      has_guide: false,
      sets: [
        {
          id: 201,
          set_number: 1,
          actual_reps: 8,
          actual_weight: 40,
          is_completed: true,
          version: 2,
        },
      ],
    },
  ],
};

const completedWorkout: Workout = {
  ...activeWorkout,
  status: 'completed',
  completed_at: '2030-01-10T10:45:00',
};

describe('finish workout recovery', () => {
  beforeEach(() => localStorage.clear());

  it('reconciles an idempotent retry response and clears all local active state', async () => {
    saveActiveWorkoutSnapshot(7, activeWorkout);
    localStorage.setItem(activeWorkoutRestKey(7, 42), '1894300200000');
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['workout', 'today'], activeWorkout);
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    await reconcileFinishedWorkout(queryClient, completedWorkout, async () => {
      clearActiveWorkoutData(7, 42);
    });

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['workout'] });
    expect(queryClient.getQueryData(['workout', 'today'])).toEqual(completedWorkout);
    expect(localStorage.getItem(activeWorkoutQueueKey(7, 42))).toBeNull();
    expect(localStorage.getItem(activeWorkoutRestKey(7, 42))).toBeNull();
  });
});
