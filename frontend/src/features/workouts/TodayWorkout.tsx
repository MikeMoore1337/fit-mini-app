import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { Workout } from '../../shared/api/types';
import { haptic } from '../../shared/telegram/useTelegram';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { readStorage, removeStorage, writeStorage } from '../../shared/storage';
import { ExerciseGuideDialog } from '../exercises/ExerciseGuideDialog';

type WorkoutSet = Workout['exercises'][number]['sets'][number];

export function formatWorkoutDuration(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    : `${minutes}:${String(seconds).padStart(2, '0')}`;
}

function WorkoutDuration({ startedAt, completedAt }: { startedAt: string; completedAt?: string }) {
  const [now, setNow] = useState(() => Date.now());
  const startTime = new Date(startedAt).getTime();
  const endTime = completedAt ? new Date(completedAt).getTime() : now;
  const elapsedSeconds = Number.isFinite(startTime)
    ? Math.max(0, Math.floor((endTime - startTime) / 1000))
    : 0;

  useEffect(() => {
    if (completedAt) return;
    const update = () => setNow(Date.now());
    const timer = window.setInterval(update, 1000);
    document.addEventListener('visibilitychange', update);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', update);
    };
  }, [completedAt]);

  return (
    <div className="metric" role="timer" aria-label="Длительность тренировки">
      <span>Длительность</span>
      <strong>{formatWorkoutDuration(elapsedSeconds)}</strong>
    </div>
  );
}

function WorkoutSetRow({
  set,
  disabled,
  restSeconds,
  workoutId,
  exerciseTitle,
}: {
  set: WorkoutSet;
  disabled: boolean;
  restSeconds: number;
  workoutId: number;
  exerciseTitle: string;
}) {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const draftKey = `fit_workout_set_${set.id}`;
  const pendingKey = `fit_workout_pending_${set.id}`;
  const stored = readStorage<Partial<WorkoutSet>>(draftKey, {});
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
  const dirty = useRef(false);
  const processQueue = useCallback(() => {
    if (inFlight.current || !pending.current) return;
    setSaving(true);
    inFlight.current = (async () => {
      try {
        while (pending.current) {
          const payload = pending.current;
          pending.current = null;
          await api(`/api/v1/workouts/sets/${set.id}`, { method: 'PATCH', body: payload });
        }
        removeStorage(pendingKey);
        removeStorage(draftKey);
        await queryClient.invalidateQueries({ queryKey: ['workout', 'today'] });
      } catch (reason) {
        const retryable =
          !(reason instanceof ApiError) ||
          reason.status === 0 ||
          reason.status === 429 ||
          reason.status >= 500;
        if (!retryable) removeStorage(pendingKey);
        toast(
          navigator.onLine
            ? (reason as Error).message
            : 'Нет сети. Подход сохранён на устройстве и будет отправлен позже.',
          'error',
        );
      } finally {
        inFlight.current = null;
        setSaving(false);
      }
    })();
  }, [draftKey, pendingKey, queryClient, set.id, toast]);

  const enqueueSave = (completed: boolean, startRest = false) => {
    const payload = {
      actual_reps: reps === '' ? null : Number(reps),
      actual_weight: weight === '' ? null : Number(weight),
      is_completed: completed,
    };
    pending.current = payload;
    writeStorage(pendingKey, payload);
    if (startRest && completed) {
      haptic('success');
      window.dispatchEvent(
        new CustomEvent('fit:rest', { detail: { workoutId, seconds: restSeconds } }),
      );
    }
    processQueue();
  };
  const saveDraft = (nextReps: string, nextWeight: string) =>
    writeStorage(draftKey, {
      actual_reps: nextReps === '' ? null : Number(nextReps),
      actual_weight: nextWeight === '' ? null : Number(nextWeight),
    });

  useEffect(() => {
    const flush = () => {
      const saved = readStorage<NonNullable<typeof pending.current> | null>(pendingKey, null);
      if (!saved) return;
      pending.current = saved;
      processQueue();
    };
    flush();
    window.addEventListener('online', flush);
    return () => window.removeEventListener('online', flush);
  }, [pendingKey, processQueue]);
  return (
    <div className="workout-set-row">
      <strong>#{set.set_number}</strong>
      <label className="field">
        <span>Повторы</span>
        <input
          disabled={disabled}
          aria-label={`Повторы, ${exerciseTitle}, подход ${set.set_number}`}
          inputMode="numeric"
          type="number"
          min="0"
          value={reps}
          onChange={(e) => {
            setReps(e.target.value);
            dirty.current = true;
            saveDraft(e.target.value, weight);
          }}
          onBlur={() => {
            if (!disabled && dirty.current) {
              dirty.current = false;
              enqueueSave(set.is_completed);
            }
          }}
        />
      </label>
      <label className="field">
        <span>Вес, кг</span>
        <input
          disabled={disabled}
          aria-label={`Вес, ${exerciseTitle}, подход ${set.set_number}`}
          inputMode="decimal"
          type="number"
          min="0"
          step="0.5"
          value={weight}
          onChange={(e) => {
            setWeight(e.target.value);
            dirty.current = true;
            saveDraft(reps, e.target.value);
          }}
          onBlur={() => {
            if (!disabled && dirty.current) {
              dirty.current = false;
              enqueueSave(set.is_completed);
            }
          }}
        />
      </label>
      <button
        type="button"
        disabled={disabled || saving}
        aria-label={`${set.is_completed ? 'Отметить невыполненным' : 'Завершить'}: ${exerciseTitle}, подход ${set.set_number}`}
        className={set.is_completed ? 'secondary' : ''}
        onClick={() => {
          dirty.current = false;
          enqueueSave(!set.is_completed, true);
        }}
      >
        {saving ? 'Сохраняем…' : set.is_completed ? 'Отменить' : 'Готово'}
      </button>
    </div>
  );
}

function RestTimer({ workoutId }: { workoutId: number }) {
  const storageKey = `fit_workout_rest_deadline_${workoutId}`;
  const [deadline, setDeadline] = useState(() => readStorage<number>(storageKey, 0));
  const [now, setNow] = useState(() => Date.now());
  const seconds = Math.max(0, Math.ceil((deadline - now) / 1000));
  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ workoutId: number; seconds: number }>).detail;
      if (!detail || detail.workoutId !== workoutId) return;
      const nextDeadline = Date.now() + detail.seconds * 1000;
      setNow(Date.now());
      setDeadline(nextDeadline);
      writeStorage(storageKey, nextDeadline);
    };
    window.addEventListener('fit:rest', handler);
    return () => window.removeEventListener('fit:rest', handler);
  }, [storageKey, workoutId]);
  useEffect(() => {
    if (!deadline) return;
    const update = () => {
      const currentTime = Date.now();
      setNow(currentTime);
      if (deadline <= currentTime) {
        removeStorage(storageKey);
        setDeadline(0);
        haptic('success');
      }
    };
    const timer = window.setInterval(update, 1000);
    document.addEventListener('visibilitychange', update);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', update);
    };
  }, [deadline, storageKey]);
  if (!seconds) return null;
  return (
    <div className="floating-workout-status" role="timer" aria-live="polite">
      <strong>
        Отдых: {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, '0')}
      </strong>
      <button
        className="secondary"
        onClick={() => {
          removeStorage(storageKey);
          setDeadline(0);
        }}
      >
        Пропустить
      </button>
    </div>
  );
}

export function TodayWorkout() {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [guide, setGuide] = useState<{ id: number; title: string } | null>(null);
  const workout = useQuery({
    queryKey: ['workout', 'today'],
    queryFn: () => api<Workout>('/api/v1/workouts/today'),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api<Workout | void>(path, { method, body }),
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
            {data.started_at && (
              <WorkoutDuration
                startedAt={data.started_at}
                completedAt={data.completed_at ?? undefined}
              />
            )}
          </div>
          {data.status === 'planned' && (
            <button
              disabled={mutation.isPending}
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
                  {exercise.notes && <p className="exercise-note">{exercise.notes}</p>}
                </div>
                {exercise.has_guide && (
                  <button
                    type="button"
                    className="secondary compact"
                    onClick={() =>
                      setGuide({ id: exercise.exercise_id, title: exercise.exercise_title })
                    }
                  >
                    Техника
                  </button>
                )}
              </div>
              {exercise.sets.map((set) => (
                <WorkoutSetRow
                  key={set.id}
                  set={set}
                  restSeconds={exercise.rest_seconds}
                  disabled={!started}
                  workoutId={data.id}
                  exerciseTitle={exercise.exercise_title}
                />
              ))}
            </article>
          ))}
          {started && (
            <button
              disabled={mutation.isPending}
              onClick={async () => {
                const incomplete = total - completed;
                if (
                  incomplete > 0 &&
                  !(await confirm({
                    title: 'Завершить неполную тренировку?',
                    message: `Не отмечено подходов: ${incomplete}. Их можно оставить незаполненными и завершить тренировку.`,
                    confirmText: 'Завершить',
                    danger: false,
                  }))
                )
                  return;
                mutation.mutate({
                  path: `/api/v1/workouts/${data.id}/finish`,
                  method: 'POST',
                  body: incomplete > 0 ? { confirm_incomplete: true } : undefined,
                });
              }}
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
                    title: 'Пропустить тренировку?',
                    message:
                      'Она останется в истории как пропущенная. Если хотите выполнить её позже, перенесите дату в разделе «Прогресс».',
                    confirmText: 'Пропустить',
                  })
                )
                  mutation.mutate({
                    path: `/api/v1/workouts/${data.id}/skip`,
                    method: 'POST',
                  });
              }}
            >
              Пропустить тренировку
            </button>
          )}
        </div>
      </Card>
      <RestTimer workoutId={data.id} />
      {guide && (
        <ExerciseGuideDialog
          exerciseId={guide.id}
          exerciseTitle={guide.title}
          onClose={() => setGuide(null)}
        />
      )}
    </>
  );
}
