import type { ProgressSummary, Workout } from '../shared/api/types';

type WorkoutProps = {
  kind: 'workout';
  workout: Workout;
};

type ProgressProps = {
  kind: 'progress';
  trend: ProgressSummary['body']['trends'][number];
};

type SelectedTodayPilot49eProps = WorkoutProps | ProgressProps;

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(
    new Date(`${value}T12:00:00`),
  );
}

function WorkoutSummary({ workout }: WorkoutProps) {
  const sets = workout.exercises.flatMap((exercise) => exercise.sets);
  const completedSets = sets.filter((set) => set.is_completed);
  const completedSet = completedSets.at(-1);
  const completionPercent = sets.length
    ? Math.round((completedSets.length / sets.length) * 100)
    : 0;
  const nextExercise = workout.exercises.at(1);

  return (
    <div className="pilot49e-workout-summary" aria-label="Краткая сводка тренировки">
      <div className="pilot49e-workout-summary__track" aria-hidden="true">
        <span style={{ width: `${completionPercent}%` }} />
      </div>
      <dl>
        <div>
          <dt>кг · прошлый подход</dt>
          <dd>{completedSet?.actual_weight ?? '—'}</dd>
        </div>
        <div>
          <dt>повторов</dt>
          <dd>{completedSet?.actual_reps ?? '—'}</dd>
        </div>
        <div>
          <dt>выполнено</dt>
          <dd>{completionPercent}%</dd>
        </div>
      </dl>
      <div className="pilot49e-workout-summary__current">
        <span>
          Подход {Math.min(completedSets.length + 1, sets.length)} · сейчас
          <small>Вес → повторы → готово</small>
        </span>
      </div>
      {nextExercise && (
        <div className="pilot49e-workout-summary__next">
          <strong>{nextExercise.exercise_title}</strong>
          <span>{nextExercise.prescribed_sets} подхода · дальше</span>
        </div>
      )}
    </div>
  );
}

function ProgressOverview({ trend }: ProgressProps) {
  const pointValues = trend.points.map((point) => point.value);
  const pointMinimum = Math.min(...pointValues);
  const pointMaximum = Math.max(...pointValues);
  const pointRange = pointMaximum - pointMinimum;
  const chartDescription = `Вес по замерам: ${trend.points
    .map((point) => `${formatDate(point.measured_on)} — ${point.value.toLocaleString('ru-RU')} кг`)
    .join('; ')}.`;

  return (
    <article className="pilot49e-progress-overview">
      <span className="today-panel__kicker">Прогресс · 4 недели</span>
      <h2>Вес меняется в рамках цели</h2>
      <p>
        {trend.change == null
          ? 'Изменение за период пока не рассчитано'
          : `${trend.change > 0 ? '+' : ''}${trend.change.toLocaleString('ru-RU')} кг за период`}
      </p>
      <div className="pilot49e-progress-overview__chart" role="img" aria-label={chartDescription}>
        {trend.points.map((point) => {
          const height =
            pointRange === 0 ? 68 : 42 + ((point.value - pointMinimum) / pointRange) * 46;
          return (
            <span
              aria-hidden="true"
              key={point.measured_on}
              style={{ height: `${height}%` }}
              title={`${point.measured_on}: ${point.value.toLocaleString('ru-RU')} кг`}
            />
          );
        })}
      </div>
      <div className="pilot49e-progress-overview__dates" aria-hidden="true">
        <span>{formatDate(trend.first_measured_on)}</span>
        <span>{formatDate(trend.latest_measured_on)}</span>
      </div>
    </article>
  );
}

export default function SelectedTodayPilot49e(props: SelectedTodayPilot49eProps) {
  return props.kind === 'workout' ? <WorkoutSummary {...props} /> : <ProgressOverview {...props} />;
}
