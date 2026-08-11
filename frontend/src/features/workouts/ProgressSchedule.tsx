import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  ProgressVolumePoint,
  WorkoutProgress,
  WorkoutScheduleItem,
} from '../../shared/api/types';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { workoutStatusLabel } from '../../shared/statusLabels';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { DateInput, TimeInput } from '../../shared/ui/PickerInput';

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    weekday: 'short',
  });
}

function VolumeChart({ points }: { points: ProgressVolumePoint[] }) {
  const rows = points.slice(-6);
  const maximum = Math.max(...rows.map((item) => item.volume_kg), 1);
  if (!rows.length) return <EmptyState title="Данных об объёме пока нет" />;
  return (
    <div
      className="trend-bars"
      role="img"
      aria-label={`Объём по неделям: ${rows
        .map((item) => `${formatDate(item.week_start)} — ${Math.round(item.volume_kg)} кг`)
        .join(', ')}`}
    >
      {rows.map((item) => (
        <div className="trend-bar" key={item.week_start} aria-hidden="true">
          <span className="trend-bar__value">{Math.round(item.volume_kg)}</span>
          <span
            className="trend-bar__fill"
            style={{ height: `${Math.max(8, (item.volume_kg / maximum) * 100)}%` }}
          />
          <span className="trend-bar__label">
            {new Date(`${item.week_start}T12:00:00`).toLocaleDateString('ru-RU', {
              day: '2-digit',
              month: '2-digit',
            })}
          </span>
        </div>
      ))}
    </div>
  );
}

function ProgressPanel() {
  const progress = useQuery({
    queryKey: ['workout', 'progress'],
    queryFn: () => api<WorkoutProgress>('/api/v1/workouts/progress'),
  });
  if (progress.isLoading) return <LoadingState label="Считаем прогресс…" />;
  if (progress.error) {
    return (
      <ErrorState
        message={(progress.error as Error).message}
        retry={() => void progress.refetch()}
      />
    );
  }
  const data = progress.data;
  if (!data) return null;
  return (
    <Card title="Динамика" description="По всем тренировкам и замерам">
      <div className="metric-grid top-gap">
        <div className="metric">
          <span>Соблюдение плана</span>
          <strong>{data.adherence_percent}%</strong>
        </div>
        <div className="metric">
          <span>Завершено</span>
          <strong>{data.workouts_completed}</strong>
        </div>
        <div className="metric">
          <span>Серия</span>
          <strong>{data.current_streak}</strong>
        </div>
        <div className="metric">
          <span>Изменение веса</span>
          <strong>
            {data.weight_change_kg == null
              ? '—'
              : `${data.weight_change_kg > 0 ? '+' : ''}${data.weight_change_kg} кг`}
          </strong>
        </div>
      </div>
      <div className="progress-trends top-gap">
        <section className="trend-card">
          <div>
            <strong>Объём по неделям</strong>
            <p className="muted">Килограммы × повторения</p>
          </div>
          <VolumeChart points={data.weekly_volume} />
        </section>
        <section className="trend-card">
          <div>
            <strong>Лучшие результаты</strong>
            <p className="muted">Личные рекорды в подходах</p>
          </div>
          {!data.personal_records.length ? (
            <EmptyState title="Рекорды появятся после тренировок" />
          ) : (
            <div className="list-grid">
              {data.personal_records.slice(0, 4).map((record) => (
                <div className="list-row" key={record.exercise_id}>
                  <div>
                    <strong>{record.exercise_title}</strong>
                    <p className="muted">{formatDate(record.last_performed_on)}</p>
                  </div>
                  <strong>
                    {record.max_weight_kg == null ? '—' : `${record.max_weight_kg} кг`}
                  </strong>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
      {(data.workouts_skipped > 0 || data.workouts_missed > 0) && (
        <p className="muted">
          Пропущено по плану: {data.workouts_skipped}; просрочено: {data.workouts_missed}.
        </p>
      )}
    </Card>
  );
}

function ScheduleRow({
  item,
  minDate,
  pending,
  onReschedule,
  onSkip,
}: {
  item: WorkoutScheduleItem;
  minDate: string;
  pending: boolean;
  onReschedule(date: string, time: string): void;
  onSkip(): void;
}) {
  const [scheduledDate, setScheduledDate] = useState(item.scheduled_date);
  const [scheduledTime, setScheduledTime] = useState(item.scheduled_time?.slice(0, 5) ?? '');
  return (
    <article
      className="list-row"
      id={`workout-schedule-${item.id}`}
      tabIndex={-1}
      aria-label={`Тренировка ${item.title} в расписании`}
    >
      <div className="list-row__main">
        <strong>{item.title}</strong>
        <span className="muted">
          {formatDate(item.scheduled_date)}
          {item.scheduled_time ? ` в ${item.scheduled_time.slice(0, 5)}` : ''} · неделя{' '}
          {item.week_number}
        </span>
        <Badge>{workoutStatusLabel(item.status)}</Badge>
      </div>
      {item.status === 'planned' && (
        <form
          className="list-row__actions"
          onSubmit={(event) => {
            event.preventDefault();
            onReschedule(scheduledDate, scheduledTime);
          }}
        >
          <label className="field compact-field">
            <span className="sr-only">Новая дата для {item.title}</span>
            <DateInput
              min={minDate}
              value={scheduledDate}
              onChange={(event) => setScheduledDate(event.target.value)}
              required
            />
          </label>
          <label className="field compact-field">
            <span className="sr-only">Новое время для {item.title}</span>
            <TimeInput
              value={scheduledTime}
              onChange={(event) => setScheduledTime(event.target.value)}
            />
          </label>
          <button
            type="submit"
            className="secondary"
            disabled={
              pending ||
              (scheduledDate === item.scheduled_date &&
                scheduledTime === (item.scheduled_time?.slice(0, 5) ?? ''))
            }
          >
            Перенести
          </button>
          <button type="button" className="btn-danger" disabled={pending} onClick={onSkip}>
            Пропустить
          </button>
        </form>
      )}
    </article>
  );
}

function SchedulePanel({
  timeZone,
  focusedWorkoutId,
}: {
  timeZone?: string | null;
  focusedWorkoutId?: number | null;
}) {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const schedule = useQuery({
    queryKey: ['workout', 'schedule'],
    queryFn: () => api<WorkoutScheduleItem[]>('/api/v1/workouts/schedule'),
  });
  const mutation = useMutation({
    mutationFn: ({
      action,
      workoutId,
      scheduledDate,
      scheduledTime,
    }: {
      action: 'reschedule' | 'skip';
      workoutId: number;
      scheduledDate?: string;
      scheduledTime?: string;
    }) =>
      api<WorkoutScheduleItem>(
        action === 'reschedule'
          ? `/api/v1/workouts/${workoutId}/schedule`
          : `/api/v1/workouts/${workoutId}/skip`,
        action === 'reschedule'
          ? {
              method: 'PATCH',
              body: { scheduled_date: scheduledDate, scheduled_time: scheduledTime || null },
            }
          : { method: 'POST' },
      ),
    onSuccess: async (_item, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['workout'] });
      toast(variables.action === 'reschedule' ? 'Тренировка перенесена' : 'Тренировка пропущена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const today = dateInputValue(new Date(), timeZone || detectedTimeZone());

  useEffect(() => {
    if (!focusedWorkoutId || !schedule.data?.some((item) => item.id === focusedWorkoutId)) return;
    const row = document.getElementById(`workout-schedule-${focusedWorkoutId}`);
    row?.focus({ preventScroll: true });
    row?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
  }, [focusedWorkoutId, schedule.data]);

  return (
    <Card title="Расписание" description="Ближайшие восемь недель">
      {schedule.isLoading ? (
        <LoadingState />
      ) : schedule.error ? (
        <ErrorState
          message={(schedule.error as Error).message}
          retry={() => void schedule.refetch()}
        />
      ) : !schedule.data?.length ? (
        <EmptyState title="Активного расписания пока нет" />
      ) : (
        <div className="list-grid top-gap">
          {schedule.data.map((item) => (
            <ScheduleRow
              key={`${item.id}-${item.scheduled_date}-${item.scheduled_time}-${item.status}`}
              item={item}
              minDate={today}
              pending={mutation.isPending && mutation.variables?.workoutId === item.id}
              onReschedule={(scheduledDate, scheduledTime) =>
                mutation.mutate({
                  action: 'reschedule',
                  workoutId: item.id,
                  scheduledDate,
                  scheduledTime,
                })
              }
              onSkip={async () => {
                if (
                  await confirm({
                    title: 'Пропустить тренировку?',
                    message: `${item.title}, ${formatDate(item.scheduled_date)}. Её можно перенести, если вы планируете выполнить её позже.`,
                    confirmText: 'Пропустить',
                  })
                )
                  mutation.mutate({ action: 'skip', workoutId: item.id });
              }}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

export function ProgressSchedule({
  timeZone,
  focusedWorkoutId,
}: {
  timeZone?: string | null;
  focusedWorkoutId?: number | null;
}) {
  return (
    <div className="stack">
      <ProgressPanel />
      <SchedulePanel timeZone={timeZone} focusedWorkoutId={focusedWorkoutId} />
    </div>
  );
}
