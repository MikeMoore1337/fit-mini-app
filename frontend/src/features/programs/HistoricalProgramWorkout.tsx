import { useQuery } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { Exercise } from '../../shared/api/types';
import { Badge, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import {
  formatProgramDate,
  revisionWorkoutSnapshot,
  type ProgramRevision,
  workoutStatusLabel,
} from './programHistory';

function historyErrorMessage(error: unknown): string {
  if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
    return 'Снимок версии недоступен. Возможно, доступ тренера к программе был отозван.';
  }
  return error instanceof Error ? error.message : 'Не удалось загрузить снимок версии.';
}

export function HistoricalProgramWorkout({
  programId,
  revisionNumber,
  workoutId,
}: {
  programId: number;
  revisionNumber: number;
  workoutId: number;
}) {
  const revisions = useQuery({
    queryKey: ['assigned-program', programId, 'revisions'],
    queryFn: () => api<ProgramRevision[]>(`/api/v1/programs/assigned/${programId}/revisions`),
  });
  const exercises = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api<Exercise[]>('/api/v1/programs/exercises'),
  });
  const revision = revisions.data?.find((item) => item.revision_number === revisionNumber);
  const workout = revisionWorkoutSnapshot(revision, workoutId);
  const exerciseTitles = new Map(exercises.data?.map((exercise) => [exercise.id, exercise.title]));

  if (revisions.isLoading) return <LoadingState label="Загружаем снимок тренировки…" />;
  if (revisions.error) {
    return (
      <ErrorState
        message={historyErrorMessage(revisions.error)}
        retry={() => void revisions.refetch()}
      />
    );
  }
  if (!revision || !workout) {
    return (
      <EmptyState
        title="Снимок тренировки не найден"
        text="Версия программы могла быть недоступна или не содержать эту тренировку."
      />
    );
  }

  return (
    <section
      className="program-history-workout"
      aria-labelledby={`program-history-workout-${programId}-${revisionNumber}-${workoutId}`}
    >
      <header className="program-history-workout__header">
        <div>
          <span className="eyebrow">Снимок программы · v{revisionNumber}</span>
          <h2 id={`program-history-workout-${programId}-${revisionNumber}-${workoutId}`}>
            {workout.title}
          </h2>
        </div>
        <Badge>{workoutStatusLabel(workout.status)}</Badge>
      </header>
      <p className="program-history-workout__notice">
        Это сохранённый состав тренировки из выбранной версии. Он доступен только для просмотра и не
        заменяется текущим планом.
      </p>
      <dl className="program-history-workout__facts">
        <div>
          <dt>Дата в версии</dt>
          <dd>{formatProgramDate(workout.scheduledDate)}</dd>
        </div>
        {workout.weekNumber != null && (
          <div>
            <dt>Неделя</dt>
            <dd>{workout.weekNumber}</dd>
          </div>
        )}
        {workout.dayNumber != null && (
          <div>
            <dt>День программы</dt>
            <dd>{workout.dayNumber}</dd>
          </div>
        )}
      </dl>
      <div className="program-history-workout__plan">
        <h3>Состав в версии v{revisionNumber}</h3>
        {workout.exercises.length ? (
          <ol>
            {workout.exercises.map((exercise) => (
              <li key={`${exercise.sortOrder}-${exercise.exerciseId}`}>
                <div>
                  <strong>
                    {exerciseTitles.get(exercise.exerciseId) ??
                      `Упражнение #${exercise.exerciseId}`}
                  </strong>
                  <span>
                    {exercise.prescribedSets} подх. · {exercise.prescribedReps} повт.
                    {exercise.restSeconds != null ? ` · отдых ${exercise.restSeconds} сек.` : ''}
                  </span>
                </div>
                {exercise.notes && <p>{exercise.notes}</p>}
              </li>
            ))}
          </ol>
        ) : (
          <p className="muted">В снимке этой тренировки упражнения не сохранены.</p>
        )}
      </div>
    </section>
  );
}
