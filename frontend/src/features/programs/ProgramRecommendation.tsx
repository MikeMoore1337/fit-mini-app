import { FormEvent, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type {
  ProgramRecommendationRequest,
  ProgramRecommendationResponse,
  ProgramTemplate,
} from '../../shared/api/types';
import { Card, ErrorState } from '../../shared/ui/common';

type RecommendationGoal = NonNullable<ProgramRecommendationRequest['goal']>;
type RecommendationExperience = NonNullable<ProgramRecommendationRequest['experience']>;
type TrainingLocation = NonNullable<ProgramRecommendationRequest['training_location']>;
type EquipmentId = NonNullable<ProgramRecommendationRequest['available_equipment_ids']>[number];

const goals: ReadonlyArray<{ value: RecommendationGoal; label: string }> = [
  { value: 'fat_loss', label: 'Снизить вес' },
  { value: 'recomposition', label: 'Улучшить форму без фокуса на вес' },
  { value: 'maintenance', label: 'Поддерживать форму' },
  { value: 'muscle_gain', label: 'Набрать мышечную массу' },
  { value: 'strength', label: 'Стать сильнее' },
];

const experiences: ReadonlyArray<{ value: RecommendationExperience; label: string }> = [
  { value: 'beginner', label: 'Начинаю или возвращаюсь после перерыва' },
  { value: 'intermediate', label: 'Тренируюсь регулярно' },
  { value: 'advanced', label: 'Тренируюсь давно и системно' },
];

const locations: ReadonlyArray<{ value: TrainingLocation; label: string }> = [
  { value: 'gym', label: 'Тренажёрный зал' },
  { value: 'home', label: 'Дом' },
  { value: 'other', label: 'Другое место' },
];

const equipment: ReadonlyArray<{ value: EquipmentId; label: string }> = [
  { value: 'bodyweight', label: 'Собственный вес' },
  { value: 'dumbbell', label: 'Гантели' },
  { value: 'barbell', label: 'Штанга' },
  { value: 'bench', label: 'Скамья' },
  { value: 'cable', label: 'Тросовый блок' },
  { value: 'machine', label: 'Тренажёры' },
  { value: 'kettlebell', label: 'Гиря' },
  { value: 'cardio', label: 'Кардиооборудование' },
  { value: 'other', label: 'Другое оборудование' },
];

interface ProgramRecommendationProps {
  onPreview: (template: ProgramTemplate) => void;
  onEditCopy: (template: ProgramTemplate) => void;
  onStart: (template: ProgramTemplate) => void;
}

function RecommendationActions({
  template,
  onPreview,
  onEditCopy,
  onStart,
}: ProgramRecommendationProps & { template: ProgramTemplate }) {
  return (
    <div className="list-row__actions program-recommendation__actions">
      <button type="button" className="secondary" onClick={() => onPreview(template)}>
        Посмотреть состав
      </button>
      <button type="button" className="secondary" onClick={() => onEditCopy(template)}>
        Изменить копию
      </button>
      {template.is_active_for_current_user ? (
        <button type="button" className="secondary" disabled>
          Уже запущена
        </button>
      ) : (
        <button type="button" onClick={() => onStart(template)}>
          Перейти к запуску
        </button>
      )}
    </div>
  );
}

export function ProgramRecommendation({
  onPreview,
  onEditCopy,
  onStart,
}: ProgramRecommendationProps) {
  const { user } = useAuth();
  const profileGoal = user?.profile?.goal;
  const profileExperience = user?.profile?.level;
  const profileWorkouts = user?.profile?.workouts_per_week;
  const [goal, setGoal] = useState<RecommendationGoal | ''>(
    goals.some((item) => item.value === profileGoal) ? (profileGoal as RecommendationGoal) : '',
  );
  const [experience, setExperience] = useState<RecommendationExperience | ''>(
    experiences.some((item) => item.value === profileExperience)
      ? (profileExperience as RecommendationExperience)
      : '',
  );
  const [workoutsPerWeek, setWorkoutsPerWeek] = useState<number | ''>(
    profileWorkouts && profileWorkouts >= 1 && profileWorkouts <= 8 ? profileWorkouts : '',
  );
  const [location, setLocation] = useState<TrainingLocation | ''>('');
  const [checkEquipment, setCheckEquipment] = useState(false);
  const [equipmentIds, setEquipmentIds] = useState<EquipmentId[]>([]);

  const recommendation = useMutation({
    mutationFn: (payload: ProgramRecommendationRequest) =>
      api<ProgramRecommendationResponse>('/api/v1/programs/templates/recommendation', {
        method: 'POST',
        body: payload,
      }),
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    recommendation.mutate({
      goal: goal || null,
      experience: experience || null,
      workouts_per_week: workoutsPerWeek || null,
      training_location: location || null,
      available_equipment_ids: checkEquipment ? equipmentIds : null,
    });
  };

  const result = recommendation.data;

  return (
    <Card title="Подобрать программу">
      <p className="muted">
        Ответьте на несколько вопросов. Подбор работает по фиксированным правилам и ничего не
        запускает автоматически.
      </p>
      <form className="stack program-recommendation__form top-gap" onSubmit={submit}>
        <div className="form-grid program-recommendation__primary-fields">
          <label className="field">
            <span>Главная цель</span>
            <select
              value={goal}
              onChange={(event) => setGoal(event.target.value as RecommendationGoal | '')}
              required
            >
              <option value="">Выберите цель</option>
              {goals.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Опыт силовых тренировок</span>
            <select
              value={experience}
              onChange={(event) =>
                setExperience(event.target.value as RecommendationExperience | '')
              }
              required
            >
              <option value="">Выберите уровень</option>
              {experiences.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Сколько тренировок удобно выполнять</span>
            <input
              type="number"
              min="1"
              max="8"
              value={workoutsPerWeek}
              onChange={(event) =>
                setWorkoutsPerWeek(event.target.value ? Number(event.target.value) : '')
              }
              required
            />
            <small className="field-hint">От 1 до 8 тренировок за цикл.</small>
          </label>
          <label className="field">
            <span>Где планируете тренироваться</span>
            <select
              value={location}
              onChange={(event) => setLocation(event.target.value as TrainingLocation | '')}
            >
              <option value="">Не указывать</option>
              {locations.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="checkbox-row program-recommendation__equipment-toggle">
          <input
            type="checkbox"
            checked={checkEquipment}
            onChange={(event) => setCheckEquipment(event.target.checked)}
          />
          <span>Проверить совместимость с доступным оборудованием</span>
        </label>
        {checkEquipment && (
          <fieldset className="program-recommendation__equipment">
            <legend>Что точно доступно</legend>
            <div className="program-recommendation__equipment-grid">
              {equipment.map((item) => (
                <label className="checkbox-row" key={item.value}>
                  <input
                    type="checkbox"
                    checked={equipmentIds.includes(item.value)}
                    onChange={(event) =>
                      setEquipmentIds((current) =>
                        event.target.checked
                          ? [...current, item.value]
                          : current.filter((value) => value !== item.value),
                      )
                    }
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
            <small className="field-hint">
              Неотмеченное оборудование считается недоступным. Собственный вес не требует отдельного
              инвентаря.
            </small>
          </fieldset>
        )}

        <button disabled={recommendation.isPending}>
          {recommendation.isPending ? 'Подбираем…' : 'Подобрать программу'}
        </button>
      </form>

      <div className="program-recommendation__result" aria-live="polite">
        {recommendation.error && <ErrorState message={(recommendation.error as Error).message} />}
        {result && result.status !== 'recommended' && (
          <div className="auth-notice top-gap">
            <strong>
              {result.status === 'needs_input' ? 'Нужны дополнительные данные' : 'Совпадений нет'}
            </strong>
            <p>{result.message}</p>
          </div>
        )}
        {result?.recommendation && (
          <article className="program-recommendation__match top-gap">
            <div>
              <span className="eyebrow">Рекомендованный шаблон</span>
              <h3>{result.recommendation.template.title}</h3>
              <p>{result.recommendation.reason}</p>
            </div>
            <div className="program-recommendation__facts">
              <div>
                <strong>Почему подходит</strong>
                <ul>
                  {result.recommendation.fit_facts.map((fact) => (
                    <li key={fact}>{fact}</li>
                  ))}
                </ul>
              </div>
              {result.recommendation.limitations.length > 0 && (
                <div>
                  <strong>Что учесть</strong>
                  <ul>
                    {result.recommendation.limitations.map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <p className="muted">{result.message}</p>
            <RecommendationActions
              template={result.recommendation.template}
              onPreview={onPreview}
              onEditCopy={onEditCopy}
              onStart={onStart}
            />
          </article>
        )}
        {!!result?.alternatives?.length && (
          <details className="compact-disclosure top-gap">
            <summary>Другие подходящие варианты ({result.alternatives.length})</summary>
            <div className="list-grid top-gap">
              {result.alternatives.map((alternative) => (
                <article className="list-row" key={alternative.template.id}>
                  <div>
                    <strong>{alternative.template.title}</strong>
                    <p className="muted">{alternative.reason}</p>
                  </div>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => onPreview(alternative.template)}
                  >
                    Посмотреть
                  </button>
                </article>
              ))}
            </div>
          </details>
        )}
      </div>
    </Card>
  );
}
