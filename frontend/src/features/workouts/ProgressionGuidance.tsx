import { useEffect, useRef } from 'react';
import type { Workout } from '../../shared/api/types';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import { Button, DisclosureIcon } from '../../shared/ui/common';

type Guidance = NonNullable<Workout['exercises'][number]['progression_guidance']>;
type Session = Guidance['evidence']['sessions'][number];

const feedbackLabels: Record<NonNullable<Session['completion_feedback']>, string> = {
  easier_than_expected: 'легче ожидаемого',
  as_expected: 'нормально',
  harder_than_expected: 'тяжелее ожидаемого',
};

function formatNumber(value: number): string {
  return value.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
}

function unitLabel(unit: Guidance['load_unit']): string {
  return unit === 'kg' ? 'кг' : 'lb';
}

function targetLabel(guidance: Guidance): string {
  const { target_reps_min: minimum, target_reps_max: maximum } = guidance.evidence;
  if (minimum == null || maximum == null) return 'Диапазон повторений не распознан';
  const reps = minimum === maximum ? String(minimum) : `${minimum}–${maximum}`;
  return `Цель: ${guidance.evidence.prescribed_sets} × ${reps}`;
}

function sessionLabel(session: Session): string {
  const date = new Date(`${session.scheduled_date}T12:00:00`).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  });
  const reps =
    session.reps_min == null || session.reps_max == null
      ? 'повторы не записаны'
      : session.reps_min === session.reps_max
        ? `${session.reps_min} повторов`
        : `${session.reps_min}–${session.reps_max} повторов`;
  const load =
    session.load == null
      ? 'нагрузка неполная'
      : `${formatNumber(session.load)} ${unitLabel(session.load_unit)}`;
  return `${date} · ${load} · ${reps}`;
}

export function ProgressionGuidance({
  guidance,
  exerciseKey,
  applied = false,
  onApply,
  onDismiss,
}: {
  guidance: Guidance;
  exerciseKey: number;
  applied?: boolean;
  onApply?: () => void;
  onDismiss: () => void;
}) {
  const applyStarted = useRef(false);
  const exactSuggestion = guidance.suggested_weight;

  useEffect(() => {
    trackProductEvent(
      { name: 'progression_suggestion_shown', surface: productEventSurface() },
      { dedupe: 'session', dedupeKey: `workout-exercise-${exerciseKey}` },
    );
  }, [exerciseKey]);

  return (
    <section
      aria-label="Рекомендация по следующей нагрузке"
      className={`progression-guidance is-${guidance.outcome}`}
    >
      <div className="progression-guidance__copy">
        <span>Следующая нагрузка</span>
        <strong>{guidance.message}</strong>
        <p>{guidance.detail}</p>
      </div>

      <details className="progression-guidance__details">
        <summary>
          <span>Почему?</span>
          <DisclosureIcon />
        </summary>
        <div className="progression-guidance__evidence">
          <div className="progression-guidance__facts">
            <span>{targetLabel(guidance)}</span>
            <span>
              Сопоставимых тренировок: {guidance.evidence.comparable_session_count} из{' '}
              {guidance.evidence.required_session_count}
            </span>
            <span>
              Запас повторов записан в {guidance.evidence.rir_recorded_set_count} из{' '}
              {guidance.evidence.working_set_count} рабочих подходов
            </span>
          </div>
          {guidance.evidence.sessions.length > 0 ? (
            <ol className="progression-guidance__history" aria-label="Последние тренировки">
              {guidance.evidence.sessions.map((session) => (
                <li key={session.workout_id}>
                  <span>{sessionLabel(session)}</span>
                  <small>
                    {session.working_set_count} раб. подх.
                    {session.rir_recorded_set_count > 0
                      ? ` · запас записан: ${session.rir_values.join(', ')}`
                      : ' · без оценки запаса'}
                    {session.reached_failure ? ' · отмечен отказ' : ''}
                    {session.completion_feedback
                      ? ` · тренировка: ${feedbackLabels[session.completion_feedback]}`
                      : ''}
                  </small>
                </li>
              ))}
            </ol>
          ) : (
            <p className="progression-guidance__empty">
              Пока нет полных сопоставимых тренировок в этом контексте программы.
            </p>
          )}
        </div>
      </details>

      <div className="progression-guidance__actions">
        {exactSuggestion != null && onApply && (
          <Button
            type="button"
            variant="secondary"
            disabled={applied}
            onClick={() => {
              if (applyStarted.current || applied) return;
              applyStarted.current = true;
              onApply();
            }}
          >
            {applied
              ? 'Вес подставлен'
              : `Подставить ${formatNumber(exactSuggestion)} ${unitLabel(guidance.load_unit)}`}
          </Button>
        )}
        <Button
          type="button"
          variant="ghost"
          onClick={() => {
            trackProductEvent({
              name: 'progression_suggestion_dismissed',
              surface: productEventSurface(),
            });
            onDismiss();
          }}
        >
          Скрыть подсказку
        </Button>
      </div>
    </section>
  );
}
