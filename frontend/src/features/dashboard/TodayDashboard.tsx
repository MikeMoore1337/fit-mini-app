import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { ApiError, api } from '../../shared/api/client';
import type {
  FoodDiaryDay,
  ProgressSummary,
  WeeklyCheckInCurrent,
  Workout,
  WorkoutComment,
  WorkoutScheduleItem,
} from '../../shared/api/types';
import { dateInputValue, detectedTimeZone, formatCalendarDate } from '../../shared/dateTime';
import { AppLink } from '../../shared/navigation/router';
import { queryKeys } from '../../shared/queryKeys';
import {
  loadActiveWorkoutQueue,
  loadCurrentActiveWorkoutSnapshot,
} from '../workouts/activeWorkoutQueue';
import { WorkoutAdaptation } from '../workouts/WorkoutAdaptation';
import { TodayWorkout } from '../workouts/TodayWorkout';
import { Badge, Button, Skeleton } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { WeekStrip, type WeekStripDayMeta, type WeekStripStatus } from '../../shared/ui/WeekStrip';

export function formatTodayHeading(value: string): { title: string } {
  const weekday = formatCalendarDate(value, { weekday: 'long' });
  const date = formatCalendarDate(value, { day: 'numeric', month: 'long' });
  return {
    title: `Сегодня · ${weekday}, ${date}`,
  };
}

const weekStatusPriority = ['in_progress', 'completed', 'planned', 'skipped'] as const;

function weekWorkoutForDate(
  workouts: WorkoutScheduleItem[] | undefined,
  value: string,
): WorkoutScheduleItem | undefined {
  const matches = workouts?.filter((item) => item.scheduled_date === value) ?? [];
  const priority = (status: string) => {
    const index = weekStatusPriority.indexOf(status as (typeof weekStatusPriority)[number]);
    return index === -1 ? weekStatusPriority.length : index;
  };
  return matches.sort((left, right) => priority(left.status) - priority(right.status))[0];
}

function weekStatus(
  item: WorkoutScheduleItem | undefined,
  date: string,
  today: string,
): (WeekStripStatus & { icon: string }) | null {
  if (!item) return null;
  if (item.status === 'completed') return { key: 'completed', label: 'Выполнено', icon: '✓' };
  if (item.status === 'in_progress') return { key: 'in-progress', label: 'В процессе', icon: '›' };
  if (item.status === 'skipped') return { key: 'skipped', label: 'Пропущено', icon: '—' };
  if (item.status === 'planned' && date > today) {
    return { key: 'upcoming', label: 'Предстоит тренировка', icon: '•' };
  }
  if (item.status === 'planned') return { key: 'planned', label: 'Запланировано', icon: '•' };
  return null;
}

function WeekContext({
  today,
  workouts,
  loading,
  error,
  onRetry,
}: {
  today: string;
  workouts?: WorkoutScheduleItem[];
  loading: boolean;
  error: boolean;
  onRetry(): void;
}) {
  return (
    <WeekStrip
      anchorDate={today}
      ariaLabel="Эта неделя"
      getDayMeta={(date): WeekStripDayMeta => {
        const item = weekWorkoutForDate(workouts, date);
        const status = weekStatus(item, date, today);
        const isToday = date === today;
        const canOpenWorkout =
          item &&
          !isToday &&
          (item.status === 'completed' ||
            (date >= today && ['planned', 'in_progress', 'skipped'].includes(item.status)));
        return {
          status: status ? { ...status, marker: status.icon } : null,
          link: canOpenWorkout
            ? {
                label: `Открыть тренировку ${item.title}`,
                to: `/app?section=progress&workout_id=${item.id}`,
              }
            : undefined,
        };
      }}
      headerAction={
        error ? (
          <button className="today-text-link" type="button" onClick={onRetry}>
            Обновить план
          </button>
        ) : undefined
      }
      loading={loading}
      loadingLabel="Загружаем план недели"
      mode="overview"
      title="Эта неделя"
      today={today}
    />
  );
}

function formatWorkoutDate(value: string, today: string): string {
  if (value === today) return 'сегодня';
  return formatCalendarDate(value, { weekday: 'long', day: 'numeric', month: 'short' });
}

function formatAmount(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const numeric = Number(value);
  return Number.isFinite(numeric) ? String(Math.round(numeric)) : '—';
}

function compactSignal(value: string, maxLength = 140): string {
  const normalized = value.replace(/\s+/g, ' ').trim();
  return normalized.length > maxLength
    ? `${normalized.slice(0, maxLength - 1).trimEnd()}…`
    : normalized;
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

function Macro({
  label,
  total,
  target,
}: {
  label: string;
  total: string | null;
  target?: string | null;
}) {
  return (
    <div className="today-macro">
      <span>{label}</span>
      <strong>
        {formatAmount(total)}
        {total === null ? (
          <small> не указано</small>
        ) : target ? (
          <small> / {formatAmount(target)} г</small>
        ) : (
          <small> г</small>
        )}
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
  todayScheduleItem,
  weeklyReview,
  trainerComment,
  progress,
  detailsOpen,
  startPending,
  onOpenDetails,
  onStart,
}: {
  today: string;
  workout?: Workout;
  todayScheduleItem?: WorkoutScheduleItem;
  weeklyReview?: WeeklyCheckInCurrent;
  trainerComment?: WorkoutComment;
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
  const weeklyReviewAvailable = Boolean(weeklyReview && !weeklyReview.existing);
  const feedbackWorkoutId = workout?.id ?? todayScheduleItem?.id;
  const trainerCommentLink =
    trainerComment && feedbackWorkoutId
      ? `/app?section=progress&workout_id=${feedbackWorkoutId}&comment_id=${trainerComment.id}`
      : null;

  const completedAction = () => {
    if (trainerCommentLink) {
      return (
        <AppLink className="button-link" to={trainerCommentLink}>
          Открыть комментарий
        </AppLink>
      );
    }
    if (weeklyReviewAvailable) {
      return (
        <AppLink className="button-link" to="/app?section=progress&weekly_review=1">
          Пройти короткую проверку
        </AppLink>
      );
    }
    return (
      <AppLink
        className="button-link"
        to={
          feedbackWorkoutId
            ? `/app?section=progress&workout_id=${feedbackWorkoutId}`
            : '/app?section=progress'
        }
      >
        Посмотреть итог
      </AppLink>
    );
  };

  if (workout) {
    if (workout.status === 'completed') {
      return (
        <>
          <div className="today-workout-copy">
            <Badge tone="success">Готово</Badge>
            <h2 id="today-workout-title">Тренировка завершена</h2>
            <p>Результат сохранён. Следующее действие — восстановиться и продолжить план.</p>
          </div>
          {completedAction()}
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
          {trainerCommentLink ? (
            <AppLink className="button-link secondary-link" to={trainerCommentLink}>
              Открыть комментарий тренера
            </AppLink>
          ) : !detailsOpen ? (
            <Button fullWidth variant="secondary" type="button" onClick={onOpenDetails}>
              Посмотреть упражнения
            </Button>
          ) : null}
          {!started && <WorkoutAdaptation workout={workout} entryContext="today" />}
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
        {completedAction()}
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
          Подобрать программу
        </AppLink>
      </>
    );
  }

  if (trainerCommentLink) {
    return (
      <>
        <div className="today-workout-copy">
          <Badge tone="warning">Комментарий тренера</Badge>
          <h2 id="today-workout-title">Тренер оставил комментарий</h2>
          <p>{trainerComment ? compactSignal(trainerComment.body) : ''}</p>
        </div>
        <AppLink className="button-link" to={trainerCommentLink}>
          Открыть комментарий
        </AppLink>
      </>
    );
  }

  if (weeklyReviewAvailable) {
    return (
      <>
        <div className="today-workout-copy">
          <Badge>Итоги недели</Badge>
          <h2 id="today-workout-title">Неделя готова к проверке</h2>
          <p>Коротко отметьте нагрузку, восстановление и то, насколько легко было держать план.</p>
        </div>
        <AppLink className="button-link" to="/app?section=progress&weekly_review=1">
          Пройти короткую проверку
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
      <div className="today-workout-actions">
        <AppLink className="button-link" to="/app?section=nutrition">
          Добавить питание
        </AppLink>
        <AppLink className="button-link secondary-link" to="/app?section=progress">
          Записать замер
        </AppLink>
      </div>
    </>
  );
}

function millisecondsUntilNextCalendarDay(timeZone: string): number {
  const now = Date.now();
  const currentDay = dateInputValue(new Date(now), timeZone);
  let lowerBound = now;
  let upperBound = now + 30 * 60 * 60 * 1000;

  while (dateInputValue(new Date(upperBound), timeZone) === currentDay) {
    upperBound += 12 * 60 * 60 * 1000;
  }
  while (upperBound - lowerBound > 1_000) {
    const candidate = Math.floor((lowerBound + upperBound) / 2);
    if (dateInputValue(new Date(candidate), timeZone) === currentDay) lowerBound = candidate;
    else upperBound = candidate;
  }
  return Math.max(1_000, upperBound - now + 100);
}

function useCalendarDay(timeZone: string): string {
  const [day, setDay] = useState(() => dateInputValue(new Date(), timeZone));

  useEffect(() => {
    let timer: number | undefined;
    const scheduleNextDay = () => {
      if (timer !== undefined) window.clearTimeout(timer);
      timer = window.setTimeout(refresh, millisecondsUntilNextCalendarDay(timeZone));
    };
    const refresh = () => {
      setDay((current) => {
        const next = dateInputValue(new Date(), timeZone);
        return next === current ? current : next;
      });
      scheduleNextDay();
    };
    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') refresh();
    };

    refresh();
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => {
      if (timer !== undefined) window.clearTimeout(timer);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  }, [timeZone]);

  return day;
}

export function TodayDashboard() {
  const { user } = useAuth();
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const detailsRef = useRef<HTMLDivElement>(null);
  const autoOpenedCompletionRef = useRef<number | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const timeZone = user?.profile?.timezone || detectedTimeZone();
  const today = useCalendarDay(timeZone);
  const calendarContextRef = useRef(`${timeZone}:${today}`);
  const heading = formatTodayHeading(today);
  const progress = useProgressSummary();
  const week = useQuery({
    queryKey: ['workout', 'week'],
    queryFn: () => api<WorkoutScheduleItem[]>('/api/v1/workouts/week'),
  });
  const weeklyReview = useQuery({
    queryKey: ['weekly-check-ins', 'current'],
    queryFn: () => api<WeeklyCheckInCurrent>('/api/v1/check-ins/weekly/current'),
  });
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
  const todayScheduleItem =
    weekWorkoutForDate(week.data, today) ??
    (visibleWorkout
      ? {
          id: visibleWorkout.id,
          scheduled_date: visibleWorkout.scheduled_date,
          scheduled_time: visibleWorkout.scheduled_time,
          title: visibleWorkout.title,
          status: visibleWorkout.status,
          day_number: visibleWorkout.day_number,
          week_number: visibleWorkout.week_number,
        }
      : undefined);
  const comments = useQuery({
    queryKey: todayScheduleItem
      ? queryKeys.workoutComments.client(todayScheduleItem.id)
      : ['workout', 'comments', 'today', 'disabled'],
    queryFn: () => api<WorkoutComment[]>(`/api/v1/workouts/${todayScheduleItem!.id}/comments`),
    enabled: Boolean(todayScheduleItem),
  });
  const trainerComment = comments.data
    ?.slice()
    .sort(
      (left, right) =>
        new Date(right.created_at).getTime() - new Date(left.created_at).getTime() ||
        right.id - left.id,
    )[0];

  useEffect(() => {
    if (
      visibleWorkout?.status !== 'completed' ||
      autoOpenedCompletionRef.current === visibleWorkout.id
    )
      return;
    autoOpenedCompletionRef.current = visibleWorkout.id;
    setDetailsOpen(true);
  }, [visibleWorkout?.id, visibleWorkout?.status]);
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
      queryClient.setQueryData<WorkoutScheduleItem[]>(['workout', 'week'], (items) =>
        items?.map((item) =>
          item.id === startedWorkout.id ? { ...item, status: startedWorkout.status } : item,
        ),
      );
      setDetailsOpen(true);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workout', 'week'], exact: true }),
        queryClient.invalidateQueries({ queryKey: queryKeys.progress.summaries }),
      ]);
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  useEffect(() => {
    if (!detailsOpen) return;
    detailsRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }, [detailsOpen]);

  useEffect(() => {
    const calendarContext = `${timeZone}:${today}`;
    if (calendarContextRef.current === calendarContext) return;
    calendarContextRef.current = calendarContext;
    setDetailsOpen(false);
    void Promise.all([
      queryClient.invalidateQueries({ queryKey: ['workout', 'today'], exact: true }),
      queryClient.invalidateQueries({ queryKey: ['workout', 'week'], exact: true }),
      queryClient.invalidateQueries({ queryKey: ['weekly-check-ins', 'current'], exact: true }),
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.summaries }),
    ]);
  }, [queryClient, timeZone, today]);

  const workoutFailed = Boolean(workout.error && !noTodayWorkout && !visibleWorkout);
  const priorityContextLoading = Boolean(
    !visibleWorkout &&
    user?.has_active_program &&
    (week.isLoading || weeklyReview.isLoading || (todayScheduleItem && comments.isLoading)),
  );

  if (detailsOpen && visibleWorkout) {
    return (
      <div className="today-workout-focus" ref={detailsRef}>
        <header className="today-workout-focus__header">
          <button className="today-text-link" type="button" onClick={() => setDetailsOpen(false)}>
            <span aria-hidden="true">←</span> К сводке
          </button>
          <div>
            <span>{visibleWorkout.title}</span>
            <strong>
              {visibleWorkout.status === 'completed' ? 'Итог тренировки' : 'Текущая тренировка'}
            </strong>
          </div>
          <span>
            День {visibleWorkout.day_number} ·{' '}
            {visibleWorkout.status === 'completed'
              ? 'Завершена'
              : visibleWorkout.status === 'in_progress'
                ? 'В процессе'
                : 'План'}
          </span>
        </header>
        <TodayWorkout embedded onCompletionClose={() => setDetailsOpen(false)} />
      </div>
    );
  }

  return (
    <div className="today-dashboard today-dashboard--design-v2">
      <header className="today-dashboard__header">
        <h1>{heading.title}</h1>
      </header>

      <WeekContext
        today={today}
        workouts={week.data}
        loading={week.isLoading}
        error={Boolean(week.error)}
        onRetry={() => void week.refetch()}
      />

      <div className="today-dashboard__overview">
        <section className="today-workout-spotlight" aria-labelledby="today-workout-title">
          <span className="today-workout-spotlight__label">Тренировка</span>
          {workout.isLoading ||
          priorityContextLoading ||
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
              todayScheduleItem={todayScheduleItem}
              weeklyReview={weeklyReview.data}
              trainerComment={trainerComment}
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
        <AppLink to="/app?section=progress">Прогресс</AppLink>
        <AppLink to="/app?section=nutrition">Настроить питание</AppLink>
      </nav>
    </div>
  );
}
