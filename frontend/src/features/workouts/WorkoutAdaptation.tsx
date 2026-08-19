import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  Workout,
  WorkoutAdaptationApply,
  WorkoutAdaptationPreview,
  WorkoutAdaptationRequest,
  WorkoutAlternative,
} from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

type AdaptationReason = WorkoutAdaptationRequest['reason'];
type EquipmentId = NonNullable<WorkoutAdaptationRequest['available_equipment_ids']>[number];

const reasons: ReadonlyArray<{ value: AdaptationReason; label: string }> = [
  { value: 'limited_time', label: 'Мало времени' },
  { value: 'unavailable_equipment', label: 'Оборудование недоступно' },
  { value: 'replace_exercise', label: 'Хочу заменить упражнение' },
  { value: 'different_environment', label: 'Тренируюсь в другом месте' },
  { value: 'pain_or_injury', label: 'Есть боль или травма' },
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
  { value: 'other', label: 'Другое' },
];

function alternativesPath(
  workoutId: number,
  workoutExerciseId: number,
  equipmentIds: EquipmentId[],
): string {
  const params = new URLSearchParams();
  equipmentIds.forEach((item) => params.append('available_equipment_ids', item));
  return `/api/v1/workouts/${workoutId}/exercises/${workoutExerciseId}/alternatives?${params}`;
}

export function WorkoutAdaptation({
  workout,
  safetyOnly = false,
}: {
  workout: Workout;
  safetyOnly?: boolean;
}) {
  const queryClient = useQueryClient();
  const { confirm, toast } = useFeedback();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<AdaptationReason>('limited_time');
  const [timeBudget, setTimeBudget] = useState('30');
  const [targetId, setTargetId] = useState('');
  const [replacementId, setReplacementId] = useState('');
  const [equipmentIds, setEquipmentIds] = useState<EquipmentId[]>([]);
  const [preview, setPreview] = useState<WorkoutAdaptationPreview | null>(null);
  const [validationError, setValidationError] = useState('');
  const activeReason: AdaptationReason = safetyOnly ? 'pain_or_injury' : reason;
  const availableReasons = safetyOnly
    ? reasons.filter((item) => item.value === 'pain_or_injury')
    : reasons;

  const needsEquipment = [
    'unavailable_equipment',
    'replace_exercise',
    'different_environment',
  ].includes(activeReason);
  const alternatives = useQuery({
    queryKey: ['workout', 'adaptation-alternatives', workout.id, targetId, equipmentIds],
    queryFn: () =>
      api<WorkoutAlternative[]>(alternativesPath(workout.id, Number(targetId), equipmentIds)),
    enabled: activeReason === 'replace_exercise' && Boolean(targetId) && equipmentIds.length > 0,
    retry: false,
  });

  const selectedTarget = useMemo(
    () => workout.exercises.find((item) => item.id === Number(targetId)),
    [targetId, workout.exercises],
  );

  const resetPreview = () => {
    setPreview(null);
    setValidationError('');
  };

  const buildRequest = (): WorkoutAdaptationRequest | null => {
    if (activeReason === 'limited_time') {
      const minutes = Number(timeBudget);
      if (!Number.isInteger(minutes) || minutes < 10 || minutes > 240) {
        setValidationError('Укажите от 10 до 240 минут.');
        return null;
      }
      return { reason: activeReason, time_budget_minutes: minutes };
    }
    if (activeReason === 'pain_or_injury') return { reason: activeReason };
    if (needsEquipment && equipmentIds.length === 0) {
      setValidationError('Отметьте всё оборудование, которое сейчас доступно.');
      return null;
    }
    if (activeReason === 'different_environment') {
      return { reason: activeReason, available_equipment_ids: equipmentIds };
    }
    if (!targetId) {
      setValidationError('Выберите упражнение.');
      return null;
    }
    if (activeReason === 'replace_exercise' && !replacementId) {
      setValidationError('Выберите проверенную замену.');
      return null;
    }
    return {
      reason: activeReason,
      target_workout_exercise_id: Number(targetId),
      replacement_exercise_id:
        activeReason === 'replace_exercise' ? Number(replacementId) : undefined,
      available_equipment_ids: equipmentIds,
    };
  };

  const previewMutation = useMutation({
    mutationFn: (request: WorkoutAdaptationRequest) =>
      api<WorkoutAdaptationPreview>(`/api/v1/workouts/${workout.id}/adaptations/preview`, {
        method: 'POST',
        body: request,
      }),
    onSuccess: (result) => setPreview(result),
    onError: (reason) => setValidationError((reason as Error).message),
  });
  const applyMutation = useMutation({
    mutationFn: ({ request, token }: { request: WorkoutAdaptationRequest; token: string }) =>
      api<WorkoutAdaptationApply>(`/api/v1/workouts/${workout.id}/adaptations/apply`, {
        method: 'POST',
        body: { ...request, preview_token: token },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workout'] });
      toast('Изменения применены только к сегодняшней тренировке');
      setOpen(false);
      setPreview(null);
    },
    onError: (reason) => setValidationError((reason as Error).message),
  });

  if (!open) {
    return (
      <button type="button" className="secondary" onClick={() => setOpen(true)}>
        {safetyOnly ? 'Боль или травма во время тренировки' : 'Адаптировать тренировку'}
      </button>
    );
  }

  return (
    <section className="workout-adaptation stack" aria-labelledby="adaptation-title">
      <div>
        <h3 id="adaptation-title">Адаптировать только эту тренировку</h3>
        <p className="muted">
          Сначала покажем изменения. Будущие тренировки и программа не изменятся.
        </p>
      </div>
      <label className="field">
        <span>Почему нужно изменить тренировку?</span>
        <select
          value={activeReason}
          onChange={(event) => {
            setReason(event.target.value as AdaptationReason);
            setTargetId('');
            setReplacementId('');
            resetPreview();
          }}
        >
          {availableReasons.map((item) => (
            <option value={item.value} key={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>

      {activeReason === 'limited_time' && (
        <label className="field">
          <span>Сколько минут есть на тренировку?</span>
          <input
            type="number"
            min={10}
            max={240}
            value={timeBudget}
            onChange={(event) => {
              setTimeBudget(event.target.value);
              resetPreview();
            }}
          />
        </label>
      )}

      {(activeReason === 'unavailable_equipment' || activeReason === 'replace_exercise') && (
        <label className="field">
          <span>Какое упражнение изменить?</span>
          <select
            value={targetId}
            onChange={(event) => {
              setTargetId(event.target.value);
              setReplacementId('');
              resetPreview();
            }}
          >
            <option value="">Выберите упражнение</option>
            {workout.exercises.map((item) => (
              <option value={item.id} key={item.id}>
                {item.exercise_title}
              </option>
            ))}
          </select>
        </label>
      )}

      {needsEquipment && (
        <fieldset className="adaptation-equipment">
          <legend>Что доступно сейчас?</legend>
          <p className="muted">Отметьте всё подходящее оборудование.</p>
          <div className="adaptation-equipment__grid">
            {equipment.map((item) => (
              <label key={item.value}>
                <input
                  type="checkbox"
                  checked={equipmentIds.includes(item.value)}
                  onChange={(event) => {
                    setEquipmentIds((current) =>
                      event.target.checked
                        ? [...current, item.value]
                        : current.filter((value) => value !== item.value),
                    );
                    setReplacementId('');
                    resetPreview();
                  }}
                />
                <span>{item.label}</span>
              </label>
            ))}
          </div>
        </fieldset>
      )}

      {activeReason === 'replace_exercise' && targetId && equipmentIds.length > 0 && (
        <label className="field">
          <span>Проверенная замена для «{selectedTarget?.exercise_title}»</span>
          <select
            value={replacementId}
            disabled={alternatives.isLoading || alternatives.isError}
            onChange={(event) => {
              setReplacementId(event.target.value);
              resetPreview();
            }}
          >
            <option value="">{alternatives.isLoading ? 'Ищем…' : 'Выберите замену'}</option>
            {(alternatives.data ?? []).map((item) => (
              <option value={item.exercise_id} key={item.exercise_id}>
                {item.title}
              </option>
            ))}
          </select>
          {!alternatives.isLoading && alternatives.data?.length === 0 && (
            <small className="field-error">
              Для выбранного оборудования нет проверенной замены.
            </small>
          )}
          {alternatives.isError && (
            <small className="field-error">{(alternatives.error as Error).message}</small>
          )}
        </label>
      )}

      {activeReason === 'pain_or_injury' && (
        <p className="adaptation-safety-note">
          Приложение не будет подбирать медицинскую замену. Покажем безопасную границу сценария.
        </p>
      )}

      {validationError && (
        <p className="field-error" role="alert">
          {validationError}
        </p>
      )}

      {preview && (
        <div className="adaptation-preview stack" aria-live="polite">
          <strong>
            {preview.status === 'safety_stop' ? 'Безопасность прежде всего' : 'Предпросмотр'}
          </strong>
          <p>{preview.message}</p>
          {preview.status !== 'safety_stop' && (
            <p className="muted">
              Расчётное время: {preview.original_estimated_minutes} →{' '}
              {preview.adapted_estimated_minutes} мин.
            </p>
          )}
          {preview.changes.length > 0 && (
            <ul>
              {preview.changes.map((change) => (
                <li key={`${change.kind}-${change.workout_exercise_id}`}>
                  {change.kind === 'removed'
                    ? `Убрать «${change.from_title}»`
                    : `«${change.from_title}» → «${change.to_title}»`}
                </li>
              ))}
            </ul>
          )}
          {preview.warnings.map((warning) => (
            <p className="adaptation-warning" key={warning}>
              {warning}
            </p>
          ))}
        </div>
      )}

      <div className="toolbar wrap">
        <button
          type="button"
          className="secondary"
          disabled={previewMutation.isPending || applyMutation.isPending}
          onClick={() => {
            const request = buildRequest();
            if (!request) return;
            setValidationError('');
            previewMutation.mutate(request);
          }}
        >
          {previewMutation.isPending ? 'Считаем…' : 'Показать изменения'}
        </button>
        {preview?.status === 'preview' && preview.preview_token && (
          <button
            type="button"
            disabled={applyMutation.isPending}
            onClick={async () => {
              const request = buildRequest();
              if (!request) return;
              const accepted = await confirm({
                title: 'Применить изменения?',
                message: 'Изменится только сегодняшняя тренировка. Это действие попадёт в историю.',
                confirmText: 'Применить',
                danger: false,
              });
              if (accepted) applyMutation.mutate({ request, token: preview.preview_token! });
            }}
          >
            {applyMutation.isPending ? 'Применяем…' : 'Подтвердить и применить'}
          </button>
        )}
        <button
          type="button"
          className="secondary"
          disabled={applyMutation.isPending}
          onClick={() => {
            setOpen(false);
            setPreview(null);
            setValidationError('');
          }}
        >
          Отмена
        </button>
      </div>
    </section>
  );
}
