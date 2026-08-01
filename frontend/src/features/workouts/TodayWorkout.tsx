import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { Workout } from '../../shared/api/types';
import { haptic } from '../../shared/telegram/useTelegram';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

type WorkoutSet = Workout['exercises'][number]['sets'][number];

function WorkoutSetRow({
  set,
  disabled,
  restSeconds,
}: {
  set: WorkoutSet;
  disabled: boolean;
  restSeconds: number;
}) {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const draftKey = `fit_workout_set_${set.id}`;
  const stored = (() => {
    try {
      return JSON.parse(localStorage.getItem(draftKey) || '{}') as Partial<WorkoutSet>;
    } catch {
      return {};
    }
  })();
  const [reps, setReps] = useState<string>(String(stored.actual_reps ?? set.actual_reps ?? ''));
  const [weight, setWeight] = useState<string>(
    String(stored.actual_weight ?? set.actual_weight ?? ''),
  );
  const [saving, setSaving] = useState(false);
  const pending = useRef<{
    actual_reps: number | null;
    actual_weight: number | null;
    is_completed: boolean;
  } | null>(null);
  const inFlight = useRef<Promise<void> | null>(null);
  const enqueueSave = (completed: boolean) => {
    pending.current = {
      actual_reps: reps === '' ? null : Number(reps),
      actual_weight: weight === '' ? null : Number(weight),
      is_completed: completed,
    };
    if (inFlight.current) return;
    setSaving(true);
    inFlight.current = (async () => {
      try {
        while (pending.current) {
          const payload = pending.current;
          pending.current = null;
          await api(`/api/v1/workouts/sets/${set.id}`, { method: 'PATCH', body: payload });
          if (payload.is_completed) {
            haptic('success');
            window.dispatchEvent(new CustomEvent('fit:rest', { detail: restSeconds }));
          }
        }
        localStorage.removeItem(draftKey);
        await queryClient.invalidateQueries({ queryKey: ['workout', 'today'] });
      } catch (reason) {
        toast((reason as Error).message, 'error');
      } finally {
        inFlight.current = null;
        setSaving(false);
      }
    })();
  };
  const saveDraft = (nextReps: string, nextWeight: string) =>
    localStorage.setItem(
      draftKey,
      JSON.stringify({
        actual_reps: nextReps === '' ? null : Number(nextReps),
        actual_weight: nextWeight === '' ? null : Number(nextWeight),
      }),
    );
  return (
    <div className="workout-set-row">
      <strong>#{set.set_number}</strong>
      <label className="field">
        <span>Повторы</span>
        <input
          disabled={disabled}
          inputMode="numeric"
          type="number"
          min="0"
          value={reps}
          onChange={(e) => {
            setReps(e.target.value);
            saveDraft(e.target.value, weight);
          }}
          onBlur={() => {
            if (!disabled && (reps || weight)) enqueueSave(set.is_completed);
          }}
        />
      </label>
      <label className="field">
        <span>Вес, кг</span>
        <input
          disabled={disabled}
          inputMode="decimal"
          type="number"
          min="0"
          step="0.5"
          value={weight}
          onChange={(e) => {
            setWeight(e.target.value);
            saveDraft(reps, e.target.value);
          }}
          onBlur={() => {
            if (!disabled && (reps || weight)) enqueueSave(set.is_completed);
          }}
        />
      </label>
      <button
        type="button"
        disabled={disabled || saving}
        className={set.is_completed ? 'secondary' : ''}
        onClick={() => enqueueSave(!set.is_completed)}
      >
        {saving ? 'Сохраняем…' : set.is_completed ? 'Отменить' : 'Готово'}
      </button>
    </div>
  );
}

function RestTimer() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const handler = (event: Event) => setSeconds((event as CustomEvent<number>).detail || 0);
    window.addEventListener('fit:rest', handler);
    return () => window.removeEventListener('fit:rest', handler);
  }, []);
  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [seconds]);
  if (!seconds) return null;
  return (
    <div className="floating-workout-status">
      <strong>
        Отдых: {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, '0')}
      </strong>
      <button className="secondary" onClick={() => setSeconds(0)}>
        Пропустить
      </button>
    </div>
  );
}

export function TodayWorkout() {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const workout = useQuery({
    queryKey: ['workout', 'today'],
    queryFn: () => api<Workout>('/api/v1/workouts/today'),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
  const mutation = useMutation({
    mutationFn: ({ path, method }: { path: string; method: string }) =>
      api<Workout | void>(path, { method }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workout'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const completed = useMemo(
    () =>
      workout.data?.exercises.flatMap((item) => item.sets).filter((item) => item.is_completed)
        .length ?? 0,
    [workout.data],
  );
  const total = useMemo(
    () => workout.data?.exercises.flatMap((item) => item.sets).length ?? 0,
    [workout.data],
  );
  if (workout.isLoading)
    return (
      <Card title="Тренировка сегодня">
        <LoadingState />
      </Card>
    );
  if (workout.error instanceof ApiError && workout.error.status === 404)
    return (
      <Card title="Тренировка сегодня">
        <EmptyState title="Сегодня отдых" text="На сегодня тренировка не назначена." />
      </Card>
    );
  if (workout.error || !workout.data)
    return (
      <Card title="Тренировка сегодня">
        <ErrorState
          message={(workout.error as Error)?.message || 'Нет данных'}
          retry={() => void workout.refetch()}
        />
      </Card>
    );
  const data = workout.data;
  const started = data.status === 'in_progress';
  return (
    <>
      <Card
        title={data.title}
        description={`${data.scheduled_date} · День ${data.day_number}`}
        actions={
          <Badge>
            {data.status === 'completed' ? 'Завершена' : started ? 'В процессе' : 'Запланирована'}
          </Badge>
        }
      >
        <div className="stack top-gap">
          <div className="metric-grid">
            <div className="metric">
              <span>Прогресс</span>
              <strong>
                {completed}/{total}
              </strong>
            </div>
            <div className="metric">
              <span>Упражнений</span>
              <strong>{data.exercises.length}</strong>
            </div>
          </div>
          {data.status === 'planned' && (
            <button
              onClick={() =>
                mutation.mutate({ path: `/api/v1/workouts/${data.id}/start`, method: 'POST' })
              }
            >
              Начать тренировку
            </button>
          )}
          {data.exercises.map((exercise) => (
            <article className="program-day stack" key={exercise.id}>
              <div className="section-head">
                <div>
                  <h3>{exercise.exercise_title}</h3>
                  <p className="muted">
                    {exercise.prescribed_sets} × {exercise.prescribed_reps} · отдых{' '}
                    {exercise.rest_seconds} сек
                  </p>
                </div>
                {exercise.has_guide && <Badge>Есть техника</Badge>}
              </div>
              {exercise.sets.map((set) => (
                <WorkoutSetRow
                  key={set.id}
                  set={set}
                  restSeconds={exercise.rest_seconds}
                  disabled={!started}
                />
              ))}
            </article>
          ))}
          {started && (
            <button
              disabled={!completed || mutation.isPending}
              onClick={() =>
                mutation.mutate({ path: `/api/v1/workouts/${data.id}/finish`, method: 'POST' })
              }
            >
              Завершить тренировку
            </button>
          )}
          {data.status !== 'in_progress' && data.status !== 'completed' && (
            <button
              className="btn-danger"
              onClick={async () => {
                if (
                  await confirm({
                    title: 'Удалить тренировку на сегодня?',
                    message: 'Вернуть её можно будет только повторным назначением программы.',
                    confirmText: 'Удалить',
                  })
                )
                  mutation.mutate({ path: '/api/v1/workouts/today', method: 'DELETE' });
              }}
            >
              Удалить тренировку
            </button>
          )}
        </div>
      </Card>
      <RestTimer />
    </>
  );
}
