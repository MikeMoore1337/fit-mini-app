import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { ApiError, api } from '../../shared/api/client';
import type { FoodDiaryDay, ProgressSummary, Workout } from '../../shared/api/types';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { AppLink } from '../../shared/navigation/router';
import { queryKeys } from '../../shared/queryKeys';
import {
  loadActiveWorkoutQueue,
  loadCurrentActiveWorkoutSnapshot,
} from '../workouts/activeWorkoutQueue';
import { TodayWorkout } from '../workouts/TodayWorkout';
import { Badge, Button, Skeleton } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

function formatCalendarDate(value: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat('ru-RU', options).format(new Date(`${value}T12:00:00`));
}

export function formatTodayHeading(value: string): { eyebrow: string; title: string } {
  const weekday = formatCalendarDate(value, { weekday: 'long' });
  const date = formatCalendarDate(value, { day: 'numeric', month: 'long' });
  return {
    eyebrow: `${weekday.charAt(0).toUpperCase() + weekday.slice(1)} · ${date}`,
    title: 'Сегодня',
  };
}

function formatWorkoutDate(value: string, today: string): string {
  if (value === today) return 'сегодня';
  return formatCalendarDate(value, { weekday: 'long', day: 'numeric', month: 'short' });
}

function formatAmount(value: string | number): string {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? String(Math.round(numeric)) : '—';
}

function workoutStatusLabel(status: string): string {
  if (status === 'in_progress') return 'В процессе';
  if (status === 'completed') return 'Завершена';
  return 'Запланирована';
}

function formatIncludedComponents(components: string[]): string {
  const labels = components
    .map(
      (component) =>
        ({
          workouts: 'тренировки',
          cardio: 'кардио',
          calories: 'калории',
          protein: 'белок',
        })[component],
    )
    .filter((label): label is string => Boolean(label));
  if (labels.length < 2) return labels[0] ?? '';
  return `${labels.slice(0, -1).join(', ')} и ${labels.at(-1)}`;
}

function Macro({ label, total, target }: { label: string; total: string; target?: string }) {
  return (
    <div className="today-macro">
      <span>{label}</span>
      <strong>
        {formatAmount(total)}
        {target ? <small> / {formatAmount(target)} г</small> : <small> г</small>}
      </strong>
    </div>
  );
}

function NutritionSummary({ today }: { today: string }) {
  const diary = useQuery({
    queryKey: ['nutrition', 'diary', today],
    queryFn: () => api<FoodDiaryDay>(`/api/v1/nutrition/diary?diary_date=${today}`),
  });

  return (
    <section className="today-panel today-nutrition" aria-labelledby="today-nutrition-title">
      <div className="today-panel__head">
        <div>
          <span className="today-panel__kicker">За день</span>
          <h2 id="today-nutrition-title">Питание</h2>
        </div>
        <AppLink className="today-text-link" to="/app?section=nutrition">
          Открыть
        </AppLink>
      </div>
      {diary.isLoading ? (
        <div className="today-summary-skeleton" aria-label="Загружаем питание" role="status">
          <Skeleton height="42px" width="58%" />
          <Skeleton height="58px" width="100%" />
        </div>
      ) : diary.error || !diary.data ? (
        <div className="today-inline-state" role="alert">
          <strong>Сводка питания временно недоступна</strong>
          <button className="today-text-link" type="button" onClick={() => void diary.refetch()}>
            Повторить
          </button>
        </div>
      ) : (
        <>
          <div className="today-calories">
            <strong>{formatAmount(diary.data.totals.energy_kcal)}</strong>
            <span>
              {diary.data.targets
                ? `из ${formatAmount(diary.data.targets.energy_kcal)} ккал`
                : 'ккал записано'}
            </span>
          </div>
          <div className="today-macros" aria-label="Белки, жиры и углеводы">
            <Macro
              label="Белки"
              total={diary.data.totals.protein_g}
              target={diary.data.targets?.protein_g}
            />
            <Macro
              label="Жиры"
              total={diary.data.totals.fat_g}
              target={diary.data.targets?.fat_g}
            />
            <Macro
              label="Углеводы"
              total={diary.data.totals.carbs_g}
              target={diary.data.targets?.carbs_g}
            />
          </div>
          <p className="today-panel__note">
            {diary.data.targets
              ? 'Добавляйте продукты и приёмы пищи в разделе «Питание».'
              : 'Настройте ориентиры, чтобы видеть дневную цель.'}
          </p>
        </>
      )}
    </section>
  );
}

function ProgressSummaryPanel({ summary }: { summary: ReturnType<typeof useProgressSummary> }) {
  if (summary.isLoading) {
    return (
      <section className="today-progress-grid" aria-label="Загружаем прогресс">
        <Skeleton className="today-progress-skeleton" height="150px" width="100%" />
        <Skeleton className="today-progress-skeleton" height="150px" width="100%" />
      </section>
    );
  }
  if (summary.error || !summary.data) {
    return (
      <section className="today-panel today-inline-state today-progress-unavailable" role="alert">
        <span>Прогресс временно недоступен. Остальные данные на экране актуальны.</span>
        <button className="today-text-link" type="button" onClick={() => void summary.refetch()}>
          Повторить
        </button>
      </section>
    );
  }

  const weight = summary.data.body.latest_measurement?.weight_kg;
  const weightTrend = summary.data.body.trends.find((item) => item.metric === 'weight_kg');
  const weightChange =
    weightTrend?.point_count && weightTrend.point_count > 1 ? weightTrend.change : null;
  const adherence = summary.data.adherence;
  const adherenceAvailable =
    adherence.formula_version === 'adherence-v1' &&
    adherence.overall_percent != null &&
    adherence.included_components.length > 0;

  return (
    <section className="today-progress-grid" aria-label="Главное о прогрессе">
      <article className="today-panel today-signal today-signal--weight">
        <div className="today-panel__head">
          <div>
            <span className="today-panel__kicker">Последний замер</span>
            <h2>Вес</h2>
          </div>
          <AppLink className="today-text-link" to="/app?section=progress">
            Все замеры
          </AppLink>
        </div>
        {weight == null ? (
          <p className="today-signal__empty">Добавьте первый замер, чтобы видеть изменения.</p>
        ) : (
          <div className="today-signal__value">
            <strong>{weight.toLocaleString('ru-RU')} кг</strong>
            {weightChange != null && (
              <span>
                {weightChange > 0 ? '+' : ''}
                {weightChange.toLocaleString('ru-RU')} кг за период наблюдений
              </span>
            )}
          </div>
        )}
      </article>
      <article className="today-panel today-signal">
        <div className="today-panel__head">
          <div>
            <span className="today-panel__kicker">Последние 30 дней</span>
            <h2>Выполнение плана</h2>
          </div>
          <AppLink className="today-text-link" to="/app?section=progress">
            Подробнее
          </AppLink>
        </div>
        {adherenceAvailable ? (
          <div className="today-signal__value">
            <strong>{Math.round(adherence.overall_percent!)}%</strong>
            <span>Учтены: {formatIncludedComponents(adherence.included_components)}</span>
          </div>
        ) : (
          <p className="today-signal__empty">Пока мало данных для общей сводки.</p>
        )}
      </article>
    </section>
  );
}

function useProgressSummary() {
  return useQuery({
    queryKey: queryKeys.progress.summary(30),
    queryFn: () => api<ProgressSummary>('/api/v1/workouts/progress/summary?period_days=30'),
  });
}

function WorkoutOverview({
  today,
  workout,
  progress,
  detailsOpen,
  startPending,
  onOpenDetails,
  onStart,
}: {
  today: string;
  workout?: Workout;
  progress: ReturnType<typeof useProgressSummary>;
  detailsOpen: boolean;
  startPending: boolean;
  onOpenDetails(): void;
  onStart(): void;
}) {
  const { user } = useAuth();
  const totalSets =
    workout?.exercises.reduce((sum, exercise) => sum + exercise.sets.length, 0) ?? 0;
  const completedSets =
    workout?.exercises.reduce(
      (sum, exercise) => sum + exercise.sets.filter((set) => set.is_completed).length,
      0,
    ) ?? 0;
  const completedToday = !workout && progress.data?.training.last_completed_workout_on === today;
  const nextWorkout = progress.data?.training.next_workout;

  if (workout) {
    if (workout.status === 'completed') {
      return (
        <>
          <div className="today-workout-copy">
            <Badge tone="success">Готово</Badge>
            <h2 id="today-workout-title">Тренировка завершена</h2>
            <p>Результат сохранён. Следующее действие — восстановиться и продолжить план.</p>
          </div>
          <AppLink className="button-link secondary-link" to="/app?section=progress">
            Посмотреть результат
          </AppLink>
        </>
      );
    }
    const started = workout.status === 'in_progress';
    return (
      <>
        <div className="today-workout-copy">
          <div className="today-workout-copy__status">
            <Badge tone={started ? 'warning' : 'neutral'}>
              {workoutStatusLabel(workout.status)}
            </Badge>
            <span>
              {workout.scheduled_time ? `${workout.scheduled_time.slice(0, 5)} · ` : ''}
              День {workout.day_number}
            </span>
          </div>
          <h2 id="today-workout-title">{workout.title}</h2>
          <p>
            {started
              ? `${completedSets} из ${totalSets} подходов отмечено`
              : `${workout.exercises.length} упражнений · ${totalSets} подходов`}
          </p>
        </div>
        <div className="today-workout-actions">
          <Button
            fullWidth
            disabled={startPending}
            type="button"
            onClick={started ? onOpenDetails : onStart}
          >
            {startPending ? 'Начинаем…' : started ? 'Продолжить тренировку' : 'Начать тренировку'}
          </Button>
          {!detailsOpen && (
            <Button fullWidth variant="secondary" type="button" onClick={onOpenDetails}>
              Посмотреть упражнения
            </Button>
          )}
        </div>
      </>
    );
  }

  if (completedToday) {
    return (
      <>
        <div className="today-workout-copy">
          <Badge tone="success">Готово</Badge>
          <h2 id="today-workout-title">Тренировка завершена</h2>
          <p>
            {nextWorkout
              ? `Следующая — ${formatWorkoutDate(nextWorkout.scheduled_date, today)}${nextWorkout.scheduled_time ? ` в ${nextWorkout.scheduled_time.slice(0, 5)}` : ''}.`
              : 'На сегодня главное действие выполнено.'}
          </p>
        </div>
        <AppLink className="button-link secondary-link" to="/app?section=progress">
          Посмотреть результат
        </AppLink>
      </>
    );
  }

  if (!user?.has_active_program) {
    return (
      <>
        <div className="today-workout-copy">
          <span className="today-workout-copy__marker" aria-hidden="true">
            01
          </span>
          <h2 id="today-workout-title">Выберите тренировочный план</h2>
          <p>План создаст понятное расписание и покажет, с чего начать сегодня.</p>
        </div>
        <AppLink className="button-link" to="/app?section=programs">
          Выбрать программу
        </AppLink>
      </>
    );
  }

  return (
    <>
      <div className="today-workout-copy">
        <Badge>Восстановление</Badge>
        <h2 id="today-workout-title">Сегодня без тренировки</h2>
        <p>
          {nextWorkout
            ? `Ближайшая — ${formatWorkoutDate(nextWorkout.scheduled_date, today)}${nextWorkout.scheduled_time ? ` в ${nextWorkout.scheduled_time.slice(0, 5)}` : ''}: ${nextWorkout.title}.`
            : 'В активном плане пока нет ближайшей тренировки.'}
        </p>
      </div>
      <AppLink className="button-link secondary-link" to="/app?section=programs">
        Открыть план
      </AppLink>
    </>
  );
}

export function TodayDashboard() {
  const { user } = useAuth();
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const detailsRef = useRef<HTMLDivElement>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const timeZone = user?.profile?.timezone || detectedTimeZone();
  const today = dateInputValue(new Date(), timeZone);
  const heading = formatTodayHeading(today);
  const firstName = user?.profile?.full_name?.trim().split(/\s+/)[0] || user?.first_name;
  const progress = useProgressSummary();
  const workout = useQuery({
    queryKey: ['workout', 'today'],
    queryFn: () => api<Workout>('/api/v1/workouts/today'),
    initialData: () => (user ? loadCurrentActiveWorkoutSnapshot(user.id) : undefined),
    initialDataUpdatedAt: 0,
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
  const noTodayWorkout = workout.error instanceof ApiError && workout.error.status === 404;
  const hasPendingLocalChanges = Boolean(
    user && workout.data && loadActiveWorkoutQueue(user.id, workout.data.id).queue.length > 0,
  );
  const visibleWorkout = noTodayWorkout && !hasPendingLocalChanges ? undefined : workout.data;
  const profileMissing = useMemo(
    () =>
      Boolean(
        user?.profile &&
        (!user.profile.level || !user.profile.workouts_per_week || !user.profile.height_cm),
      ),
    [user?.profile],
  );
  const start = useMutation({
    mutationFn: (workoutId: number) =>
      api<Workout>(`/api/v1/workouts/${workoutId}/start`, { method: 'POST' }),
    onSuccess: async (startedWorkout) => {
      queryClient.setQueryData(['workout', 'today'], startedWorkout);
      setDetailsOpen(true);
      await queryClient.invalidateQueries({ queryKey: queryKeys.progress.summaries });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  useEffect(() => {
    if (!detailsOpen) return;
    detailsRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }, [detailsOpen]);

  const workoutFailed = Boolean(workout.error && !noTodayWorkout && !visibleWorkout);

  if (detailsOpen && visibleWorkout && visibleWorkout.status !== 'completed') {
    return (
      <div className="today-workout-focus" ref={detailsRef}>
        <header className="today-workout-focus__header">
          <button className="today-text-link" type="button" onClick={() => setDetailsOpen(false)}>
            <span aria-hidden="true">←</span> К сводке
          </button>
          <div>
            <span>{visibleWorkout.title}</span>
            <strong>Текущая тренировка</strong>
          </div>
          <span>
            День {visibleWorkout.day_number} ·{' '}
            {visibleWorkout.status === 'in_progress' ? 'В процессе' : 'План'}
          </span>
        </header>
        <TodayWorkout embedded />
      </div>
    );
  }

  return (
    <div className="today-dashboard today-dashboard--design-v2">
      <header className="today-dashboard__header">
        <span className="eyebrow">{heading.eyebrow}</span>
        <h1>{heading.title}</h1>
        <p>{firstName ? `${firstName}, ` : ''}вот главное на день.</p>
      </header>

      <div className="today-dashboard__overview">
        <section className="today-workout-spotlight" aria-labelledby="today-workout-title">
          <span className="today-workout-spotlight__label">Тренировка</span>
          {workout.isLoading ||
          (noTodayWorkout && progress.isLoading && user?.has_active_program) ? (
            <div
              className="today-summary-skeleton"
              aria-label="Проверяем план на сегодня"
              role="status"
            >
              <Skeleton height="34px" width="62%" />
              <Skeleton height="20px" width="44%" />
              <Skeleton height="48px" width="100%" />
            </div>
          ) : workoutFailed ? (
            <div className="today-inline-state" role="alert">
              <strong id="today-workout-title">Не удалось проверить тренировку</strong>
              <span>Остальные данные на экране доступны.</span>
              <button
                className="today-text-link"
                type="button"
                onClick={() => void workout.refetch()}
              >
                Повторить
              </button>
            </div>
          ) : (
            <WorkoutOverview
              today={today}
              workout={visibleWorkout}
              progress={progress}
              detailsOpen={detailsOpen}
              startPending={start.isPending}
              onOpenDetails={() => setDetailsOpen(true)}
              onStart={() => visibleWorkout && start.mutate(visibleWorkout.id)}
            />
          )}
        </section>

        <div className="today-dashboard__facts">
          <NutritionSummary today={today} />
          <ProgressSummaryPanel summary={progress} />
        </div>
      </div>

      {profileMissing && (
        <aside className="today-profile-nudge">
          <div>
            <strong>Сделайте рекомендации точнее</strong>
            <span>Дополните уровень, рост и желаемую частоту тренировок в профиле.</span>
          </div>
          <AppLink className="today-text-link" to="/app?section=profile">
            Дополнить профиль
          </AppLink>
        </aside>
      )}

      <nav className="today-secondary-actions" aria-label="Быстрые действия">
        <AppLink to="/app?section=programs">План тренировок</AppLink>
        <AppLink to="/app?section=progress">Записать замер</AppLink>
        <AppLink to="/app?section=nutrition">Настроить питание</AppLink>
      </nav>
    </div>
  );
}
