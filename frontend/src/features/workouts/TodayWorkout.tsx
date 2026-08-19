import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api, ApiError } from '../../shared/api/client';
import type { Workout } from '../../shared/api/types';
import { haptic } from '../../shared/telegram/useTelegram';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { readStorage, removeStorage, writeStorage } from '../../shared/storage';
import { ExerciseGuideDialog } from '../exercises/ExerciseGuideDialog';
import {
  activeWorkoutRestKey,
  clearActiveWorkoutData,
  loadCurrentActiveWorkoutSnapshot,
  type ActiveWorkoutMutation,
  type ActiveWorkoutSetValues,
} from './activeWorkoutQueue';
import { WorkoutAdaptation } from './WorkoutAdaptation';
import { useActiveWorkoutQueue } from './useActiveWorkoutQueue';

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
  pending,
  syncing,
  enqueue,
}: {
  set: WorkoutSet;
  disabled: boolean;
  restSeconds: number;
  workoutId: number;
  exerciseTitle: string;
  pending?: ActiveWorkoutMutation;
  syncing: boolean;
  enqueue: (
    setId: number,
    serverVersion: number,
    values: ActiveWorkoutSetValues,
    immediate?: boolean,
  ) => void;
}) {
  const [reps, setReps] = useState<string>(
    String(pending?.values.actual_reps ?? set.actual_reps ?? ''),
  );
  const [weight, setWeight] = useState<string>(
    String(pending?.values.actual_weight ?? set.actual_weight ?? ''),
  );
  const [completed, setCompleted] = useState(pending?.values.is_completed ?? set.is_completed);
  const editing = useRef(false);
  const serverVersion = set.version ?? 1;
  const enqueueSave = (
    nextReps: string,
    nextWeight: string,
    nextCompleted: boolean,
    immediate = false,
  ) => {
    enqueue(
      set.id,
      serverVersion,
      {
        actual_reps: nextReps === '' ? null : Number(nextReps),
        actual_weight: nextWeight === '' ? null : Number(nextWeight),
        is_completed: nextCompleted,
      },
      immediate,
    );
    if (immediate && nextCompleted) {
      haptic('success');
      window.dispatchEvent(
        new CustomEvent('fit:rest', { detail: { workoutId, seconds: restSeconds } }),
      );
    }
  };

  useEffect(() => {
    if (pending) {
      if (editing.current) return;
      setReps(String(pending.values.actual_reps ?? ''));
      setWeight(String(pending.values.actual_weight ?? ''));
      setCompleted(pending.values.is_completed);
    } else {
      if (editing.current) {
        editing.current = false;
        return;
      }
      setReps(String(set.actual_reps ?? ''));
      setWeight(String(set.actual_weight ?? ''));
      setCompleted(set.is_completed);
    }
  }, [pending, set.actual_reps, set.actual_weight, set.is_completed]);

  return (
    <div className="workout-set-row" aria-busy={syncing || undefined}>
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
            const next = e.target.value;
            editing.current = true;
            setReps(next);
            enqueueSave(next, weight, completed);
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
            const next = e.target.value;
            editing.current = true;
            setWeight(next);
            enqueueSave(reps, next, completed);
          }}
        />
      </label>
      <button
        type="button"
        disabled={disabled}
        aria-label={`${completed ? 'Отметить невыполненным' : 'Завершить'}: ${exerciseTitle}, подход ${set.set_number}`}
        className={completed ? 'secondary' : ''}
        onClick={() => {
          const next = !completed;
          editing.current = true;
          setCompleted(next);
          enqueueSave(reps, weight, next, true);
        }}
      >
        {completed ? 'Отменить' : 'Готово'}
      </button>
    </div>
  );
}

function RestTimer({ userId, workoutId }: { userId: number; workoutId: number }) {
  const storageKey = activeWorkoutRestKey(userId, workoutId);
  const legacyStorageKey = `fit_workout_rest_deadline_${workoutId}`;
  const [deadline, setDeadline] = useState(() => {
    const scoped = readStorage<number>(storageKey, 0);
    if (scoped) return scoped;
    const legacy = readStorage<number>(legacyStorageKey, 0);
    if (legacy) writeStorage(storageKey, legacy);
    removeStorage(legacyStorageKey);
    return legacy;
  });
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

export function TodayWorkout({ embedded = false }: { embedded?: boolean }) {
  const { toast, confirm } = useFeedback();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [guide, setGuide] = useState<{ id: number; title: string } | null>(null);
  const workout = useQuery({
    queryKey: ['workout', 'today'],
    queryFn: () => api<Workout>('/api/v1/workouts/today'),
    initialData: () => (user ? loadCurrentActiveWorkoutSnapshot(user.id) : undefined),
    initialDataUpdatedAt: 0,
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
  const activeSync = useActiveWorkoutQueue(user?.id, workout.data);
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api<Workout | void>(path, { method, body }),
    onSuccess: async (_result, variables) => {
      if (variables.path.endsWith('/finish')) activeSync.clear();
      await queryClient.invalidateQueries({ queryKey: ['workout'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const completed = useMemo(
    () =>
      workout.data?.exercises
        .flatMap((item) => item.sets)
        .filter(
          (item) => activeSync.pendingBySet.get(item.id)?.values.is_completed ?? item.is_completed,
        ).length ?? 0,
    [activeSync.pendingBySet, workout.data],
  );
  const total = useMemo(
    () => workout.data?.exercises.flatMap((item) => item.sets).length ?? 0,
    [workout.data],
  );
  useEffect(() => {
    if (
      user &&
      activeSync.pendingCount === 0 &&
      workout.error instanceof ApiError &&
      workout.error.status === 404
    ) {
      const stale = loadCurrentActiveWorkoutSnapshot(user.id);
      if (stale) clearActiveWorkoutData(user.id, stale.id);
    }
  }, [activeSync.pendingCount, user, workout.error]);
  if (workout.isLoading)
    return (
      <Card title="Тренировка сегодня">
        <LoadingState />
      </Card>
    );
  if (
    workout.error instanceof ApiError &&
    workout.error.status === 404 &&
    activeSync.pendingCount === 0
  )
    return (
      <Card title="Тренировка сегодня">
        <EmptyState title="Сегодня отдых" text="На сегодня тренировка не назначена." />
      </Card>
    );
  if (
    !workout.data ||
    (workout.error &&
      !(
        workout.error instanceof ApiError &&
        (workout.error.status === 0 ||
          (workout.error.status === 404 && activeSync.pendingCount > 0))
      ))
  )
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
        collapsible={!embedded}
        title={data.title}
        description={`${data.scheduled_date}${data.scheduled_time ? ` в ${data.scheduled_time.slice(0, 5)}` : ''} · День ${data.day_number}`}
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
          {activeSync.pendingCount > 0 && (
            <div className="auth-notice stack" role="status" aria-live="polite">
              <strong>
                {activeSync.syncState === 'syncing'
                  ? 'Синхронизируем тренировку…'
                  : 'Изменения сохранены на устройстве'}
              </strong>
              <span>
                {activeSync.message ||
                  `Ожидает отправки: ${activeSync.pendingCount}. Можно закрыть или обновить приложение.`}
              </span>
              {activeSync.syncState !== 'syncing' && navigator.onLine && (
                <button className="secondary" type="button" onClick={() => void activeSync.retry()}>
                  Повторить синхронизацию
                </button>
              )}
            </div>
          )}
          {(data.status === 'planned' || started) && (
            <WorkoutAdaptation workout={data} safetyOnly={started} />
          )}
          {data.status === 'planned' && (
            <>
              <button
                disabled={mutation.isPending}
                onClick={() =>
                  mutation.mutate({ path: `/api/v1/workouts/${data.id}/start`, method: 'POST' })
                }
              >
                Начать тренировку
              </button>
            </>
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
                    className="exercise-guide-trigger compact"
                    onClick={() =>
                      setGuide({ id: exercise.exercise_id, title: exercise.exercise_title })
                    }
                  >
                    <span>Техника</span>
                    <span aria-hidden="true">⌕</span>
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
                  pending={activeSync.pendingBySet.get(set.id)}
                  syncing={activeSync.syncState === 'syncing'}
                  enqueue={activeSync.enqueue}
                />
              ))}
            </article>
          ))}
          {started && (
            <button
              disabled={mutation.isPending}
              onClick={async () => {
                if (!(await activeSync.flushNow())) {
                  toast('Сначала синхронизируйте сохранённые на устройстве подходы.', 'error');
                  return;
                }
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
      {user && <RestTimer userId={user.id} workoutId={data.id} />}
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
