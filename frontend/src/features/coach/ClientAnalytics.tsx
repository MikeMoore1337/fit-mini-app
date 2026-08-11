import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { WorkoutProgress, WorkoutTimelineItem } from '../../shared/api/types';
import { workoutStatusLabel } from '../../shared/statusLabels';
import { Badge, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function ClientAnalytics({ clientId }: { clientId: number }) {
  const progress = useQuery({
    queryKey: ['coach', 'client', clientId, 'analytics'],
    queryFn: () => api<WorkoutProgress>(`/api/v1/coach/clients/${clientId}/analytics`),
  });
  const timeline = useQuery({
    queryKey: ['coach', 'client', clientId, 'workouts'],
    queryFn: () =>
      api<WorkoutTimelineItem[]>(`/api/v1/coach/clients/${clientId}/workouts?limit=30`),
  });

  return (
    <div className="stack">
      {progress.isLoading ? (
        <LoadingState label="Считаем показатели…" />
      ) : progress.error ? (
        <ErrorState
          message={(progress.error as Error).message}
          retry={() => void progress.refetch()}
        />
      ) : progress.data ? (
        <>
          <div className="metric-grid">
            <div className="metric">
              <span>Соблюдение плана</span>
              <strong>{progress.data.adherence_percent}%</strong>
            </div>
            <div className="metric">
              <span>Завершено</span>
              <strong>{progress.data.workouts_completed}</strong>
            </div>
            <div className="metric">
              <span>Серия</span>
              <strong>{progress.data.current_streak}</strong>
            </div>
            <div className="metric">
              <span>Вес</span>
              <strong>
                {progress.data.weight_change_kg == null
                  ? '—'
                  : `${progress.data.weight_change_kg > 0 ? '+' : ''}${progress.data.weight_change_kg} кг`}
              </strong>
            </div>
          </div>
          {(progress.data.workouts_skipped > 0 || progress.data.workouts_missed > 0) && (
            <p className="muted">
              Пропущено: {progress.data.workouts_skipped}; просрочено:{' '}
              {progress.data.workouts_missed}.
            </p>
          )}
          {!!progress.data.personal_records.length && (
            <div>
              <h3>Лучшие результаты</h3>
              <div className="list-grid top-gap">
                {progress.data.personal_records.slice(0, 5).map((record) => (
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
            </div>
          )}
        </>
      ) : null}

      <div>
        <h3>Лента тренировок</h3>
        {timeline.isLoading ? (
          <LoadingState />
        ) : timeline.error ? (
          <ErrorState
            message={(timeline.error as Error).message}
            retry={() => void timeline.refetch()}
          />
        ) : !timeline.data?.length ? (
          <EmptyState title="Тренировок пока нет" />
        ) : (
          <div className="list-grid top-gap">
            {timeline.data.map((workout) => (
              <details className="card compact-disclosure" key={workout.id}>
                <summary>
                  <span>
                    <strong>{workout.title}</strong>
                    <small>
                      {formatDate(workout.scheduled_date)} · {workout.completed_sets} подх. ·{' '}
                      {Math.round(workout.volume_kg)} кг
                    </small>
                  </span>
                  <Badge>{workoutStatusLabel(workout.status)}</Badge>
                </summary>
                <div className="stack top-gap">
                  {!workout.exercises.length ? (
                    <p className="muted">Упражнения не добавлены.</p>
                  ) : (
                    workout.exercises.map((exercise) => (
                      <div className="list-row" key={exercise.exercise_id}>
                        <div className="list-row__main">
                          <strong>{exercise.exercise_title}</strong>
                          {exercise.notes && <span className="muted">{exercise.notes}</span>}
                          <span className="muted">
                            {exercise.sets
                              .filter((set) => set.is_completed)
                              .map(
                                (set) => `${set.actual_weight ?? 0} кг × ${set.actual_reps ?? 0}`,
                              )
                              .join(' · ') || 'Нет выполненных подходов'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
