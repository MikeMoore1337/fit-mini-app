import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Workout } from '../../../../src/shared/api/types';
import {
  activeWorkoutQueueKey,
  clearActiveWorkoutDataForUser,
  emptyActiveWorkoutQueue,
  enqueueWorkoutMutation,
  loadActiveWorkoutQueue,
  loadCurrentActiveWorkoutSnapshot,
  resolveWorkoutVersionConflict,
  saveActiveWorkoutQueue,
  saveActiveWorkoutSnapshot,
} from '../../../../src/features/workouts/activeWorkoutQueue';
import { useActiveWorkoutQueue } from '../../../../src/features/workouts/useActiveWorkoutQueue';

const workout: Workout = {
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
      sort_order: 1,
      prescribed_sets: 1,
      prescribed_reps: '8-10',
      rest_seconds: 90,
      has_guide: false,
      sets: [
        {
          id: 201,
          set_number: 1,
          actual_reps: null,
          actual_weight: null,
          is_completed: false,
          version: 1,
        },
      ],
    },
  ],
};

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, value });
}

function Harness() {
  const sync = useActiveWorkoutQueue(7, workout);
  const pending = sync.pendingBySet.get(201);
  return (
    <div>
      <span data-testid="pending">{sync.pendingCount}</span>
      <span data-testid="reps">{pending?.values.actual_reps ?? ''}</span>
      <span data-testid="sync-state">{sync.syncState}</span>
      <button
        onClick={() =>
          sync.enqueue(201, 1, { actual_reps: 8, actual_weight: 40, is_completed: true }, true)
        }
      >
        Изменить
      </button>
    </div>
  );
}

function renderHarness() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <Harness />
    </QueryClientProvider>,
  );
}

describe('active workout durable queue', () => {
  beforeEach(() => {
    localStorage.clear();
    setOnline(false);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    setOnline(true);
  });

  it('восстанавливает offline-изменение после remount и очищает очередь после reconnect', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 201,
          set_number: 1,
          actual_reps: 8,
          actual_weight: 40,
          is_completed: true,
          version: 2,
        }),
        { status: 200 },
      ),
    );
    const first = renderHarness();

    act(() => screen.getByRole('button', { name: 'Изменить' }).click());
    expect(screen.getByTestId('pending')).toHaveTextContent('1');
    expect(screen.getByTestId('reps')).toHaveTextContent('8');
    expect(fetchMock).not.toHaveBeenCalled();
    first.unmount();

    renderHarness();
    expect(screen.getByTestId('pending')).toHaveTextContent('1');
    expect(screen.getByTestId('reps')).toHaveTextContent('8');

    setOnline(true);
    act(() => window.dispatchEvent(new Event('online')));
    await waitFor(() => expect(screen.getByTestId('pending')).toHaveTextContent('0'));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(loadActiveWorkoutQueue(7, 42).queue).toEqual([]);
    expect(loadCurrentActiveWorkoutSnapshot(7)?.id).toBe(42);
  });

  it('сохраняет локальные данные при stale server вместо бесконечного retry', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            code: 'workout_not_active',
            message: 'Подходы можно изменять только во время тренировки',
            current: {
              id: 201,
              set_number: 1,
              actual_reps: null,
              actual_weight: null,
              is_completed: false,
              version: 1,
            },
          },
        }),
        { status: 409 },
      ),
    );
    renderHarness();
    act(() => screen.getByRole('button', { name: 'Изменить' }).click());

    setOnline(true);
    act(() => window.dispatchEvent(new Event('online')));
    await waitFor(() => expect(screen.getByTestId('sync-state')).toHaveTextContent('conflict'));
    expect(screen.getByTestId('pending')).toHaveTextContent('1');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('не даёт старой операции из второй вкладки перезаписать более новую', () => {
    let state = emptyActiveWorkoutQueue(7, 42);
    state = enqueueWorkoutMutation(state, {
      setId: 201,
      serverVersion: 1,
      values: { actual_reps: 8, actual_weight: 40, is_completed: true },
      inFlightMutationId: null,
      now: 1,
    });
    const olderId = state.queue[0]!.mutation_id;
    state = enqueueWorkoutMutation(state, {
      setId: 201,
      serverVersion: 1,
      values: { actual_reps: 10, actual_weight: 42.5, is_completed: true },
      inFlightMutationId: olderId,
      now: 2,
    });

    const resolved = resolveWorkoutVersionConflict(state, olderId, 3);

    expect(resolved.queue).toHaveLength(1);
    expect(resolved.queue[0]).toMatchObject({
      expected_version: 3,
      values: { actual_reps: 10, actual_weight: 42.5, is_completed: true },
    });
  });

  it('сохраняет расширенные поля подхода в offline-очереди', () => {
    const state = enqueueWorkoutMutation(emptyActiveWorkoutQueue(7, 42), {
      setId: 201,
      serverVersion: 1,
      values: {
        actual_reps: 8,
        actual_weight: 40,
        rir: '2',
        set_kind: 'drop',
        reached_failure: false,
        is_completed: true,
      },
      now: 1,
    });

    saveActiveWorkoutQueue(state);

    expect(loadActiveWorkoutQueue(7, 42).queue[0]?.values).toEqual({
      actual_reps: 8,
      actual_weight: 40,
      rir: '2',
      set_kind: 'drop',
      reached_failure: false,
      is_completed: true,
    });
  });

  it('изолирует аккаунты и удаляет повреждённое хранилище', () => {
    saveActiveWorkoutSnapshot(7, workout);
    saveActiveWorkoutQueue({
      ...emptyActiveWorkoutQueue(8, 43),
      queue: [
        {
          mutation_id: 'valid-mutation-00000001',
          set_id: 301,
          expected_version: 1,
          values: { actual_reps: 6, actual_weight: 30, is_completed: false },
          created_at: 1,
        },
      ],
    });
    localStorage.setItem(activeWorkoutQueueKey(9, 44), '{broken');

    clearActiveWorkoutDataForUser(7);

    expect(loadCurrentActiveWorkoutSnapshot(7)).toBeUndefined();
    expect(loadActiveWorkoutQueue(8, 43).queue).toHaveLength(1);
    expect(loadActiveWorkoutQueue(9, 44).queue).toEqual([]);
    expect(localStorage.getItem(activeWorkoutQueueKey(9, 44))).toBeNull();
  });

  it('переносит прежний unscoped draft только в текущую авторизованную тренировку', () => {
    localStorage.setItem(
      'fit_workout_set_201',
      JSON.stringify({ actual_reps: 9, actual_weight: 42.5 }),
    );
    localStorage.setItem(
      'fit_workout_pending_201',
      JSON.stringify({ actual_reps: 9, actual_weight: 42.5, is_completed: true }),
    );

    saveActiveWorkoutSnapshot(7, workout);

    expect(loadActiveWorkoutQueue(7, 42).queue[0]).toMatchObject({
      set_id: 201,
      expected_version: 1,
      values: { actual_reps: 9, actual_weight: 42.5, is_completed: true },
    });
    expect(localStorage.getItem('fit_workout_set_201')).toBeNull();
    expect(localStorage.getItem('fit_workout_pending_201')).toBeNull();
  });
});
