import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { WorkoutScheduleItem } from '../../shared/api/types';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { workoutStatusLabel } from '../../shared/statusLabels';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { DateInput, TimeInput } from '../../shared/ui/PickerInput';
import { ProgressExperience } from './ProgressExperience';
import { WeeklyCheckInCard } from './WeeklyCheckInCard';

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    weekday: 'short',
  });
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
    <div className="stack progress-schedule">
      <ProgressExperience />
      <WeeklyCheckInCard />
      <SchedulePanel timeZone={timeZone} focusedWorkoutId={focusedWorkoutId} />
    </div>
  );
}
