import { useState, type ReactNode } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ApiSchemas, ProgressSummary, TrainingAnalytics } from '../../shared/api/types';
import { queryKeys } from '../../shared/queryKeys';
import { AppLink } from '../../shared/navigation/router';
import { ContextualHelp } from '../../shared/ui/ContextualHelp';
import { DataConfidence } from '../../shared/ui/DataConfidence';
import { formatCalendarDate } from '../../shared/dateTime';
import {
  Badge,
  EmptyState,
  ErrorState,
  LoadingState,
  SegmentedControl,
} from '../../shared/ui/common';
import { NutritionPeriodReport } from './NutritionReport';
import { CardioHistory } from '../cardio/CardioLogging';

type PeriodDays = 7 | 30 | 90;
type BodyTrend = ProgressSummary['body']['trends'][number];
type AdherenceComponent = ProgressSummary['adherence']['workouts'];

const periodOptions = [
  { value: '7', label: '7 дней' },
  { value: '30', label: '30 дней' },
  { value: '90', label: '90 дней' },
] as const;

const bodyMetricLabels: Record<BodyTrend['metric'], string> = {
  weight_kg: 'Вес',
  chest_cm: 'Грудь',
  waist_cm: 'Талия',
  hips_cm: 'Бёдра',
  biceps_cm: 'Окружность плеча',
  thigh_cm: 'Окружность бедра',
};

const bodyMetricUnits: Record<BodyTrend['metric'], string> = {
  weight_kg: 'кг',
  chest_cm: 'см',
  waist_cm: 'см',
  hips_cm: 'см',
  biceps_cm: 'см',
  thigh_cm: 'см',
};

function formatNumber(value: number, maximumFractionDigits = 1): string {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits }).format(value);
}

function formatDate(value: string, withYear = false): string {
  return formatCalendarDate(value, {
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  });
}

function formatChange(change: number | null | undefined, unit: string): string {
  if (change == null) return 'Пока без динамики';
  const sign = change > 0 ? '+' : '';
  return `${sign}${formatNumber(change)} ${unit}`;
}

function trendInterpretationText(
  trend: BodyTrend,
  guidance: ProgressSummary['body']['guidance'],
): string | null {
  if (trend.interpretation_status === 'available') return null;
  if (trend.interpretation_status === 'single_point') {
    return 'Одна точка сохраняет факт, но ещё не показывает направление изменений.';
  }
  if (trend.interpretation_status === 'insufficient_points') {
    return `Нужно минимум ${guidance.minimum_points_for_interpretation} замера: разовое изменение не считаем трендом.`;
  }
  return `Точек достаточно, но период короче ${guidance.minimum_span_days_for_interpretation} дней — вывод пока преждевременный.`;
}

function plural(value: number, one: string, few: string, many: string): string {
  const absolute = Math.abs(value) % 100;
  const last = absolute % 10;
  if (absolute > 10 && absolute < 20) return many;
  if (last === 1) return one;
  if (last >= 2 && last <= 4) return few;
  return many;
}

function SectionHeading({
  description,
  eyebrow,
  title,
  titleId,
  trailing,
}: {
  description: string;
  eyebrow: string;
  title: string;
  titleId: string;
  trailing?: ReactNode;
}) {
  return (
    <header className="progress-section__head">
      <div>
        <span className="progress-section__eyebrow">{eyebrow}</span>
        <h2 id={titleId}>{title}</h2>
        <p>{description}</p>
      </div>
      {trailing}
    </header>
  );
}

function SummaryOverview({ summary }: { summary: ProgressSummary }) {
  const weight = summary.body.trends.find((trend) => trend.metric === 'weight_kg');
  return (
    <section className="progress-summary" aria-labelledby="progress-overview-title">
      <div className="progress-summary__lead">
        <span>Соблюдение плана</span>
        <strong
          id="progress-overview-title"
          className={
            summary.adherence.overall_percent == null ? undefined : 'progress-summary__score'
          }
        >
          {summary.adherence.overall_percent == null
            ? 'Пока не оценить'
            : `${formatNumber(summary.adherence.overall_percent)}%`}
        </strong>
        <p>
          {summary.adherence.overall_percent == null
            ? 'Добавляйте тренировки и питание — оценка появится, когда будет что сравнивать с планом.'
            : 'Расчёт учитывает только доступные компоненты плана за выбранный период.'}
        </p>
      </div>
      <dl className="progress-summary__facts">
        <div>
          <dt>Тренировки</dt>
          <dd>
            {summary.training.completed_workouts} из {summary.training.planned_workouts}
          </dd>
          <small>завершено по плану</small>
        </div>
        <div>
          <dt>Новые рекорды</dt>
          <dd>{summary.training.new_personal_records}</dd>
          <small>по данным завершённых подходов</small>
        </div>
        <div>
          <dt>{weight ? 'Изменение веса' : 'Дней с питанием'}</dt>
          <dd>
            {weight
              ? formatChange(weight.change, bodyMetricUnits[weight.metric])
              : summary.nutrition.complete_days + summary.nutrition.fasted_days}
          </dd>
          <small>{weight ? 'сравнение с собой' : 'подтверждено за период'}</small>
        </div>
      </dl>
    </section>
  );
}

function TrainingFacts({
  summary,
  analytics,
}: {
  summary?: ProgressSummary;
  analytics: TrainingAnalytics;
}) {
  return (
    <dl className="progress-fact-strip" aria-label="Итоги тренировок">
      <div>
        <dt>Рабочих подходов</dt>
        <dd>{analytics.completed_set_count}</dd>
      </div>
      <div>
        <dt>Частота</dt>
        <dd>
          {summary ? `${formatNumber(summary.training.frequency_per_week, 2)} в неделю` : '—'}
        </dd>
      </div>
      <div>
        <dt>Внешняя нагрузка</dt>
        <dd>
          {analytics.external_load_volume_kg == null
            ? 'Нет данных'
            : `${formatNumber(analytics.external_load_volume_kg, 0)} кг`}
        </dd>
      </div>
      <div>
        <dt>Повторов записано</dt>
        <dd>
          {analytics.reps_total == null ? 'Нет данных' : formatNumber(analytics.reps_total, 0)}
        </dd>
      </div>
    </dl>
  );
}

function SetValue({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <span>
      <small>{label}</small>
      <strong>{value ?? '—'}</strong>
    </span>
  );
}

function ExerciseHistory({ analytics }: { analytics: TrainingAnalytics }) {
  if (!analytics.exercises.length) {
    return (
      <EmptyState
        title="История упражнений пока пуста"
        text="Завершите тренировку и отметьте рабочие подходы — здесь появится фактическая динамика."
      />
    );
  }
  return (
    <div className="progress-exercises">
      {analytics.exercises.map((exercise) => (
        <details className="progress-exercise" key={exercise.exercise_id}>
          <summary>
            <span>
              <strong>{exercise.exercise_title}</strong>
              <small>
                {exercise.performed_session_count}{' '}
                {plural(exercise.performed_session_count, 'тренировка', 'тренировки', 'тренировок')}{' '}
                · {exercise.completed_set_count}{' '}
                {plural(
                  exercise.completed_set_count,
                  'рабочий подход',
                  'рабочих подхода',
                  'рабочих подходов',
                )}
              </small>
            </span>
            <span className="progress-exercise__best">
              {exercise.max_external_load_kg == null
                ? exercise.uses_bodyweight_equipment
                  ? 'Собственный вес'
                  : 'Вес не записан'
                : `до ${formatNumber(exercise.max_external_load_kg)} кг`}
            </span>
          </summary>
          <div className="progress-exercise__sessions">
            {exercise.sessions.map((session) => (
              <article className="progress-session" key={session.workout_exercise_id}>
                <header>
                  <div>
                    <strong>{formatDate(session.performed_on, true)}</strong>
                    <small>
                      {session.completed_set_count}{' '}
                      {plural(
                        session.completed_set_count,
                        'рабочий подход',
                        'рабочих подхода',
                        'рабочих подходов',
                      )}
                      {session.external_load_volume_kg == null
                        ? ''
                        : ` · ${formatNumber(session.external_load_volume_kg, 0)} кг внешней нагрузки`}
                    </small>
                  </div>
                  <Badge>Детали тренировки</Badge>
                </header>
                <div
                  className="progress-session__sets"
                  aria-label={`Подходы ${exercise.exercise_title}`}
                >
                  {session.sets.map((set) => (
                    <div className="progress-set" key={set.set_number}>
                      <b>{set.set_number}</b>
                      <SetValue
                        label="Вес"
                        value={
                          set.external_load_kg == null
                            ? '—'
                            : `${formatNumber(set.external_load_kg)} кг`
                        }
                      />
                      <SetValue label="Повторы" value={set.reps} />
                      <SetValue label="Повторы в запасе" value={set.rir} />
                    </div>
                  ))}
                </div>
              </article>
            ))}
            {exercise.history_truncated && (
              <p className="progress-note">
                Показаны последние {analytics.exercise_history_limit} тренировок упражнения.
              </p>
            )}
          </div>
        </details>
      ))}
    </div>
  );
}

function ExposureList({
  items,
  title,
}: {
  items: TrainingAnalytics['primary_muscle_exposure'];
  title: string;
}) {
  const visible = items.slice(0, 8);
  const maximum = Math.max(...visible.map((item) => item.completed_set_count), 1);
  return (
    <div className="progress-exposure">
      <h3>{title}</h3>
      {!visible.length ? (
        <p className="progress-note">Нет структурированных данных по мышечным группам.</p>
      ) : (
        <ul>
          {visible.map((item) => (
            <li key={item.muscle_id}>
              <span>{item.muscle_name}</span>
              <span className="progress-exposure__track" aria-hidden="true">
                <i style={{ width: `${(item.completed_set_count / maximum) * 100}%` }} />
              </span>
              <strong>{item.completed_set_count}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TrainingSection({
  analytics,
  summary,
}: {
  analytics: ReturnType<typeof useTrainingAnalytics>;
  summary?: ProgressSummary;
}) {
  return (
    <section
      className="progress-section"
      id="progress-training"
      aria-labelledby="progress-training-title"
    >
      <SectionHeading
        eyebrow="Нагрузка"
        title="Тренировки"
        titleId="progress-training-title"
        description="Фактические подходы, нагрузка и история упражнений — без расчётных коэффициентов."
        trailing={
          summary && (
            <Badge>
              {summary.training.new_personal_records}{' '}
              {plural(
                summary.training.new_personal_records,
                'новый рекорд',
                'новых рекорда',
                'новых рекордов',
              )}
            </Badge>
          )
        }
      />
      {analytics.isLoading ? (
        <LoadingState label="Собираем историю тренировок…" />
      ) : analytics.error ? (
        <ErrorState
          message={(analytics.error as Error).message}
          retry={() => void analytics.refetch()}
        />
      ) : analytics.data ? (
        <>
          <TrainingFacts analytics={analytics.data} summary={summary} />
          <DataConfidence
            isStale={analytics.isPlaceholderData}
            kind="training"
            signal={analytics.data.data_sufficiency.working_sets}
            action={<AppLink to="/app?section=today">Открыть тренировку</AppLink>}
          />
          <div className="progress-subsection">
            <div className="progress-subsection__head">
              <div>
                <h3>История упражнений</h3>
                <p>Раскройте упражнение, чтобы увидеть тренировки и записанные подходы.</p>
              </div>
              <a href="#progress-methodology">Как читать данные</a>
            </div>
            <ExerciseHistory analytics={analytics.data} />
          </div>
          <div className="progress-training-details">
            <ExposureList
              title="Основные мышечные группы"
              items={analytics.data.primary_muscle_exposure}
            />
            <ExposureList
              title="Дополнительные мышечные группы"
              items={analytics.data.secondary_muscle_exposure}
            />
          </div>
          <details className="progress-methodology" id="progress-methodology">
            <summary>Как читать тренировочные показатели</summary>
            <div>
              <p>
                Внешняя нагрузка учитывается только там, где записаны и вес, и повторы. Для
                упражнений с собственным весом она не описывает всю выполненную работу.
              </p>
              <p>
                Подход отдельно учитывается для каждой явно связанной основной и дополнительной
                мышечной группы. Эти значения не складываются в «эффективные подходы».
              </p>
              <p>
                Повторы в запасе необязательны и не используются для вывода об усталости или
                восстановлении.
              </p>
            </div>
          </details>
        </>
      ) : null}
    </section>
  );
}

function BodyChart({ trend }: { trend: BodyTrend }) {
  const width = 360;
  const height = 132;
  const inset = 14;
  const times = trend.points.map((point) => new Date(`${point.measured_on}T12:00:00`).getTime());
  const values = trend.points.map((point) => point.value);
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const x = (time: number) =>
    times.length === 1 || minTime === maxTime
      ? width / 2
      : inset + ((time - minTime) / (maxTime - minTime)) * (width - inset * 2);
  const y = (value: number) =>
    minValue === maxValue
      ? height / 2
      : inset + ((maxValue - value) / (maxValue - minValue)) * (height - inset * 2);
  const coordinates = trend.points.map((point, index) => ({
    x: x(times[index] ?? minTime),
    y: y(point.value),
    point,
  }));
  const unit = bodyMetricUnits[trend.metric];
  const label = `${bodyMetricLabels[trend.metric]}: ${trend.points.map((point) => `${formatDate(point.measured_on)} — ${formatNumber(point.value)} ${unit}`).join(', ')}`;
  return (
    <div className="progress-body-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={label}
        preserveAspectRatio="none"
      >
        <line x1={inset} x2={width - inset} y1={height - inset} y2={height - inset} />
        {coordinates.length > 1 && (
          <polyline points={coordinates.map((point) => `${point.x},${point.y}`).join(' ')} />
        )}
        {coordinates.map(({ point, x: pointX, y: pointY }) => (
          <circle key={`${point.measured_on}-${point.value}`} cx={pointX} cy={pointY} r="4" />
        ))}
      </svg>
      <div className="progress-body-chart__range" aria-hidden="true">
        <span>
          {formatNumber(minValue)} {unit}
        </span>
        <span>диапазон серии</span>
        <span>
          {formatNumber(maxValue)} {unit}
        </span>
      </div>
      <div className="progress-body-chart__scale" aria-hidden="true">
        <span>{formatDate(trend.first_measured_on)}</span>
        <span>{formatDate(trend.latest_measured_on)}</span>
      </div>
      <details>
        <summary>Все точки: {trend.point_count}</summary>
        <ul>
          {trend.points.map((point) => (
            <li key={`${point.measured_on}-${point.value}`}>
              <time dateTime={point.measured_on}>{formatDate(point.measured_on, true)}</time>
              <strong>
                {formatNumber(point.value)} {unit}
              </strong>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function BodySection({
  isStale,
  measurementDiary,
  summary,
}: {
  isStale?: boolean;
  measurementDiary?: ReactNode;
  summary: ProgressSummary;
}) {
  const { body } = summary;
  const priorityOptions = useQuery({
    queryKey: ['body-priority-options'],
    queryFn: () =>
      api<ApiSchemas['BodyPriorityOptionsResponse']>('/api/v1/me/profile/body-priority-options'),
    enabled: body.priority?.mode === 'muscle_groups',
    staleTime: Number.POSITIVE_INFINITY,
  });
  const priorityNames =
    body.priority?.mode === 'muscle_groups'
      ? (body.priority.muscle_group_ids ?? [])
          .map((id) => priorityOptions.data?.items.find((option) => option.id === id)?.name)
          .filter((name): name is string => Boolean(name))
      : [];
  const hasGuidance =
    body.guidance.consistency_tips.length > 0 || body.guidance.circumference_limitations.length > 0;
  return (
    <section className="progress-section" id="progress-body" aria-labelledby="progress-body-title">
      <SectionHeading
        eyebrow="Замеры"
        title="Замеры и приоритеты"
        titleId="progress-body-title"
        description="Фактические значения по датам и выбранный контекст развития — без идеальных пропорций и оценки тела."
        trailing={
          body.latest_measurement && (
            <Badge>Последний замер {formatDate(body.latest_measurement.measured_on)}</Badge>
          )
        }
      />
      <div
        className={`progress-priority${body.priority ? ' is-selected' : ' is-empty'}`}
        aria-label="Выбранный приоритет развития"
      >
        <div>
          <span>Приоритет развития</span>
          <strong>
            {!body.priority
              ? 'Не выбран'
              : body.priority.mode === 'balanced'
                ? 'Сбалансированное развитие'
                : 'Выбранные мышечные группы'}
          </strong>
        </div>
        {body.priority?.mode === 'muscle_groups' &&
          (priorityOptions.isLoading ? (
            <p role="status">Загружаем названия выбранных групп…</p>
          ) : priorityOptions.error ? (
            <p role="alert">
              Не удалось загрузить названия групп. Выбрано:{' '}
              {body.priority.muscle_group_ids?.length ?? 0}.
            </p>
          ) : (
            <ul>
              {priorityNames.map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
          ))}
        <p>
          {body.priority
            ? 'Это предпочтение для планирования. Оно не оценивает тело и не объясняет изменение окружностей.'
            : 'Можно оставить развитие без отдельного акцента или выбрать предпочтения в профиле.'}
        </p>
        <AppLink to="/app?section=profile#profile-fitness">
          {body.priority ? 'Изменить в профиле' : 'Выбрать в профиле'}
        </AppLink>
      </div>
      <div className="progress-body-flow">
        {measurementDiary && <div className="progress-body-diary">{measurementDiary}</div>}
        <div className="progress-body-trends" aria-label="Динамика замеров">
          <div className="progress-confidence-grid">
            <DataConfidence
              isStale={isStale}
              kind="weight"
              signal={summary.data_sufficiency.weight_trend}
              action={
                measurementDiary ? <a href="#measurement-diary">Добавить замер</a> : undefined
              }
            />
            <DataConfidence
              isStale={isStale}
              kind="anthropometry"
              signal={summary.data_sufficiency.anthropometry}
              action={
                measurementDiary &&
                summary.data_sufficiency.weight_trend.status === 'sufficient' ? (
                  <a href="#measurement-diary">Добавить замер</a>
                ) : undefined
              }
            />
          </div>
          {!body.trends.length ? (
            <EmptyState
              title="Замеров за этот период нет"
              text="Добавьте вес или окружности — первая точка начнёт историю, но ещё не станет трендом."
            />
          ) : (
            <>
              <div className="progress-body-grid">
                {body.trends.map((trend) => {
                  const unit = bodyMetricUnits[trend.metric];
                  const interpretation = trendInterpretationText(trend, body.guidance);
                  return (
                    <article className="progress-body-metric" key={trend.metric}>
                      <header>
                        <div>
                          <span className="progress-body-metric__kind">
                            {trend.metric === 'weight_kg' ? 'Масса тела' : 'Окружность'}
                          </span>
                          <h3>{bodyMetricLabels[trend.metric]}</h3>
                          <p>
                            {trend.point_count === 1
                              ? `1 точка · ${formatDate(trend.latest_measured_on, true)}`
                              : `${trend.point_count} ${plural(trend.point_count, 'точка', 'точки', 'точек')} · ${trend.span_days} ${plural(trend.span_days, 'день', 'дня', 'дней')}`}
                          </p>
                        </div>
                        <div className="progress-body-metric__value">
                          <strong>
                            {formatNumber(trend.latest_value)} {unit}
                          </strong>
                          <span>{formatChange(trend.change, unit)}</span>
                        </div>
                      </header>
                      <BodyChart trend={trend} />
                      {interpretation && <p className="progress-note">{interpretation}</p>}
                    </article>
                  );
                })}
              </div>
            </>
          )}
          {hasGuidance && (
            <details className="progress-body-guidance">
              <summary>Как сравнивать замеры</summary>
              <div>
                {body.guidance.consistency_tips.length > 0 && (
                  <ul>
                    {body.guidance.consistency_tips.map((tip) => (
                      <li key={tip}>{tip}</li>
                    ))}
                  </ul>
                )}
                {body.guidance.circumference_limitations.map((limitation) => (
                  <p key={limitation}>{limitation}</p>
                ))}
              </div>
            </details>
          )}
          <ContextualHelp articlePath="/knowledge/progress/how-to-read-progress">
            <p>
              Сравнивайте значения только с собственной историей. Окружность участка тела не
              показывает рост отдельной мышцы.
            </p>
          </ContextualHelp>
        </div>
      </div>
    </section>
  );
}

function NutritionSection({ isStale, summary }: { isStale?: boolean; summary: ProgressSummary }) {
  const { nutrition, adherence } = summary;
  return (
    <section
      className="progress-section"
      id="progress-nutrition"
      aria-labelledby="progress-nutrition-title"
    >
      <SectionHeading
        eyebrow="Средние значения"
        title="Питание"
        titleId="progress-nutrition-title"
        description="Средние значения по заполненным прошлым дням и сравнение с действующей целью."
      />
      {!nutrition.visible ? (
        <>
          <DataConfidence
            isStale={isStale}
            kind="nutrition"
            signal={summary.data_sufficiency.nutrition_coverage}
          />
          <EmptyState title="Данные питания недоступны" />
        </>
      ) : nutrition.complete_days + nutrition.fasted_days === 0 ? (
        <>
          <DataConfidence
            isStale={isStale}
            kind="nutrition"
            signal={summary.data_sufficiency.nutrition_coverage}
            action={<AppLink to="/app?section=nutrition">Заполнить дневник</AppLink>}
          />
          <EmptyState
            title="Нет подтверждённых дней питания"
            text={`${nutrition.incomplete_days} частичных и ${nutrition.unlogged_days} отсутствующих дней не входят в средние значения.`}
          />
        </>
      ) : (
        <>
          <div className="progress-nutrition-summary">
            <div>
              <span>В среднем за день</span>
              <strong>
                {nutrition.average_calories == null
                  ? '—'
                  : `${formatNumber(nutrition.average_calories, 0)} ккал`}
              </strong>
              <small>
                {nutrition.target_calories == null
                  ? 'Цель не задана'
                  : `цель ${formatNumber(nutrition.target_calories, 0)} ккал`}
              </small>
            </div>
            <div>
              <span>Белок в среднем</span>
              <strong>
                {nutrition.average_protein_g == null
                  ? '—'
                  : `${formatNumber(nutrition.average_protein_g, 0)} г`}
              </strong>
              <small>
                {nutrition.target_protein_g == null
                  ? 'Цель не задана'
                  : `цель ${formatNumber(nutrition.target_protein_g, 0)} г`}
              </small>
            </div>
            <div>
              <span>Подтверждено</span>
              <strong>{nutrition.complete_days + nutrition.fasted_days} дней</strong>
              <small>
                {nutrition.incomplete_days} частичных · {nutrition.unlogged_days} без записей
              </small>
            </div>
          </div>
          <div className="progress-nutrition-compliance">
            <ComplianceRow label="Калории в диапазоне цели" component={adherence.calories} />
            <ComplianceRow label="Цель по белку достигнута" component={adherence.protein} />
          </div>
          <DataConfidence
            isStale={isStale}
            kind="nutrition"
            signal={summary.data_sufficiency.nutrition_coverage}
            action={<AppLink to="/app?section=nutrition">Дополнить дневник</AppLink>}
          />
        </>
      )}
    </section>
  );
}

function componentStatus(component: AdherenceComponent): string {
  if (component.status === 'unsupported') return 'Пока нельзя оценить';
  if (component.status === 'not_applicable') return 'Нет цели или плана';
  if (component.status === 'insufficient_data') return 'Мало данных';
  return component.percent == null ? 'Мало данных' : `${formatNumber(component.percent)}%`;
}

function ComplianceRow({ label, component }: { label: string; component: AdherenceComponent }) {
  const percent = component.percent;
  return (
    <div className="progress-compliance">
      <div>
        <span>{label}</span>
        <strong>{componentStatus(component)}</strong>
      </div>
      {percent != null && (
        <div
          className="progress-compliance__track"
          role="progressbar"
          aria-label={`${label}: ${formatNumber(percent)}%`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
        >
          <span style={{ width: `${Math.max(0, Math.min(percent, 100))}%` }} />
        </div>
      )}
      {component.status === 'available' && (
        <small>
          {component.achieved} из {component.evaluated} учтённых дней или тренировок
        </small>
      )}
    </div>
  );
}

function AdherenceSection({ summary }: { summary: ProgressSummary }) {
  const rows: Array<{ label: string; component: AdherenceComponent }> = [
    { label: 'Запланированные тренировки', component: summary.adherence.workouts },
    { label: 'Калории', component: summary.adherence.calories },
    { label: 'Белок', component: summary.adherence.protein },
    { label: 'Кардио', component: summary.adherence.cardio },
  ];
  return (
    <section
      className="progress-section progress-adherence"
      id="progress-adherence"
      aria-labelledby="progress-adherence-title"
    >
      <SectionHeading
        eyebrow="Ритм"
        title="Соблюдение плана"
        titleId="progress-adherence-title"
        description="Готовая серверная оценка: отсутствующие компоненты не превращаются в ноль."
        trailing={
          <strong className="progress-adherence__score">
            {summary.adherence.overall_percent == null
              ? '—'
              : `${formatNumber(summary.adherence.overall_percent)}%`}
          </strong>
        }
      />
      <div className="progress-adherence__rows">
        {rows.map((row) => (
          <ComplianceRow key={row.label} {...row} />
        ))}
      </div>
      <p className="progress-note">
        Текущий день питания не учитывается: его ещё можно дополнить. Кардио сравнивается с
        действовавшей недельной целью только по завершённым ручным записям.
      </p>
    </section>
  );
}

function useTrainingAnalytics(period: PeriodDays) {
  return useQuery({
    queryKey: ['workout', 'training-analytics', period],
    queryFn: () =>
      api<TrainingAnalytics>(`/api/v1/workouts/progress/training-analytics?period_days=${period}`),
    placeholderData: keepPreviousData,
  });
}

export function ProgressExperience({
  measurementDiary,
  timeZone,
}: { measurementDiary?: ReactNode; timeZone?: string | null } = {}) {
  const [period, setPeriod] = useState<PeriodDays>(30);
  const summary = useQuery({
    queryKey: queryKeys.progress.summary(period),
    queryFn: () => api<ProgressSummary>(`/api/v1/workouts/progress/summary?period_days=${period}`),
    placeholderData: keepPreviousData,
  });
  const analytics = useTrainingAnalytics(period);

  return (
    <div className="progress-experience">
      <header className="progress-hero">
        <div className="progress-hero__copy">
          <span className="eyebrow">Ваша динамика</span>
          <h1>Прогресс</h1>
          <p>Что изменилось в тренировках, теле и питании — только по фактическим данным.</p>
          <ContextualHelp articlePath="/knowledge/progress/how-to-read-progress">
            <p>
              Сначала смотрите на период и полноту данных. Одна точка не образует тренд, а
              пропущенная запись не равна нулевому результату.
            </p>
          </ContextualHelp>
        </div>
        <SegmentedControl
          ariaLabel="Период прогресса"
          value={String(period)}
          options={periodOptions}
          onChange={(value) => setPeriod(Number(value) as PeriodDays)}
        />
      </header>

      {summary.isLoading ? (
        <LoadingState label="Собираем динамику за период…" />
      ) : summary.error ? (
        <ErrorState
          message={(summary.error as Error).message}
          retry={() => void summary.refetch()}
        />
      ) : summary.data ? (
        <>
          <SummaryOverview summary={summary.data} />
          <TrainingSection analytics={analytics} summary={summary.data} />
          <CardioHistory
            periodDays={period}
            summary={summary.data.cardio}
            timeZone={timeZone ?? undefined}
          />
          <BodySection
            isStale={summary.isPlaceholderData}
            measurementDiary={measurementDiary}
            summary={summary.data}
          />
          <NutritionSection isStale={summary.isPlaceholderData} summary={summary.data} />
          <NutritionPeriodReport />
          <AdherenceSection summary={summary.data} />
        </>
      ) : null}

      {summary.error && <TrainingSection analytics={analytics} />}
    </div>
  );
}
