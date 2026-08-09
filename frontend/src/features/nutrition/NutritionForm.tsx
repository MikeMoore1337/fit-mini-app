import { useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { NutritionTarget, NutritionTargetSave } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card } from '../../shared/ui/common';
import { calculateNutritionEstimate } from './nutritionCalculator';
import { usePersistentState } from '../../shared/storage';
import { useAuth } from '../../app/AuthProvider';

const defaults: NutritionTargetSave = {
  sex: 'male',
  weight_kg: 75,
  height_cm: 175,
  age: 30,
  daily_activity_level: 'moderate',
  strength_trainings_per_week: 3,
  strength_training_duration_minutes: 60,
  cardio_trainings_per_week: 1,
  cardio_training_duration_minutes: 30,
  cardio_intensity: 'moderate',
  goal: 'maintenance',
};

const goalLabels = {
  fat_loss: 'Снижение веса',
  muscle_gain: 'Набор мышечной массы',
  maintenance: 'Поддержание',
  recomposition: 'Рекомпозиция',
};

const goalAdjustmentLabels = {
  fat_loss: 'дефицит 15%',
  muscle_gain: 'профицит 5%',
  maintenance: 'без поправки',
  recomposition: 'дефицит 5%',
};

export function NutritionForm({
  targetTelegramId,
  initial,
  onSaved,
}: {
  targetTelegramId?: number | null;
  initial?: NutritionTarget | null;
  onSaved?: () => void | Promise<void>;
}) {
  const { toast } = useFeedback();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [form, setForm, clearDraft] = usePersistentState<NutritionTargetSave>(
    `fit_nutrition_draft_${targetTelegramId ? `client_${targetTelegramId}` : `user_${user?.id ?? 'me'}`}`,
    () =>
      initial
        ? {
            target_telegram_user_id: targetTelegramId,
            sex: initial.sex as 'male' | 'female',
            weight_kg: initial.weight_kg,
            height_cm: initial.height_cm,
            age: initial.age,
            daily_activity_level:
              initial.daily_activity_level as NutritionTargetSave['daily_activity_level'],
            strength_trainings_per_week: initial.strength_trainings_per_week,
            strength_training_duration_minutes: initial.strength_training_duration_minutes,
            cardio_trainings_per_week: initial.cardio_trainings_per_week,
            cardio_training_duration_minutes: initial.cardio_training_duration_minutes,
            cardio_intensity: initial.cardio_intensity as NutritionTargetSave['cardio_intensity'],
            goal: initial.goal as NutritionTargetSave['goal'],
          }
        : { ...defaults, target_telegram_user_id: targetTelegramId },
  );

  const calculation = useMemo(() => calculateNutritionEstimate(form), [form]);
  const estimate = calculation.estimate;

  const mutation = useMutation({
    mutationFn: () =>
      api<NutritionTarget>('/api/v1/nutrition/targets', {
        method: 'POST',
        body: { ...form, target_telegram_user_id: targetTelegramId || null },
      }),
    onSuccess: async () => {
      clearDraft();
      await queryClient.invalidateQueries({ queryKey: ['notifications'] });
      await onSaved?.();
      toast('Ориентиры КБЖУ сохранены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const setNumber = (key: keyof NutritionTargetSave, value: string) =>
    setForm({ ...form, [key]: value === '' ? 0 : Number(value) });

  return (
    <Card title="КБЖУ" description="Расчёт является ориентиром и может корректироваться тренером.">
      <form
        className="stack top-gap"
        onSubmit={(event) => {
          event.preventDefault();
          if (calculation.valid) mutation.mutate();
        }}
      >
        <div className="form-grid nutrition-form-grid">
          <label className="field">
            <span>Пол</span>
            <select
              value={form.sex}
              onChange={(event) =>
                setForm({ ...form, sex: event.target.value as 'male' | 'female' })
              }
            >
              <option value="male">Мужской</option>
              <option value="female">Женский</option>
            </select>
          </label>
          <label className="field">
            <span>Возраст</span>
            <input
              type="number"
              min="18"
              max="100"
              required
              value={form.age || ''}
              onChange={(event) => setNumber('age', event.target.value)}
            />
          </label>
          <label className="field">
            <span>Вес, кг</span>
            <input
              type="number"
              min="20"
              max="350"
              step="0.1"
              required
              value={form.weight_kg || ''}
              onChange={(event) => setNumber('weight_kg', event.target.value)}
            />
          </label>
          <label className="field">
            <span>Рост, см</span>
            <input
              type="number"
              min="100"
              max="250"
              step="0.1"
              required
              value={form.height_cm || ''}
              onChange={(event) => setNumber('height_cm', event.target.value)}
            />
          </label>
          <label className="field nutrition-form-grid__wide">
            <span>Повседневная активность без учёта тренировок</span>
            <select
              value={form.daily_activity_level}
              onChange={(event) =>
                setForm({
                  ...form,
                  daily_activity_level: event.target
                    .value as NutritionTargetSave['daily_activity_level'],
                })
              }
            >
              <option value="sedentary">
                Малоподвижная: сидячая работа, менее 5000 шагов (×1.2)
              </option>
              <option value="low">Низкая: примерно 5000–8000 шагов (×1.3)</option>
              <option value="moderate">Средняя: примерно 8000–12000 шагов (×1.4)</option>
              <option value="high">Высокая: более 12000 шагов или физическая работа (×1.5)</option>
            </select>
          </label>
          <label className="field">
            <span>Цель</span>
            <select
              value={form.goal}
              onChange={(event) =>
                setForm({ ...form, goal: event.target.value as NutritionTargetSave['goal'] })
              }
            >
              <option value="fat_loss">Снижение веса</option>
              <option value="recomposition">Рекомпозиция</option>
              <option value="maintenance">Поддержание</option>
              <option value="muscle_gain">Набор мышечной массы</option>
            </select>
          </label>
          <label className="field">
            <span>Силовых тренировок в неделю</span>
            <input
              type="number"
              min="0"
              max="14"
              step="1"
              required
              value={form.strength_trainings_per_week}
              onChange={(event) => setNumber('strength_trainings_per_week', event.target.value)}
            />
          </label>
          <label className="field">
            <span>Средняя продолжительность силовой, минут</span>
            <input
              type="number"
              min="10"
              max="300"
              step="1"
              required
              value={form.strength_training_duration_minutes || ''}
              onChange={(event) =>
                setNumber('strength_training_duration_minutes', event.target.value)
              }
            />
          </label>
          <label className="field">
            <span>Кардиотренировок в неделю</span>
            <input
              type="number"
              min="0"
              max="14"
              step="1"
              required
              value={form.cardio_trainings_per_week}
              onChange={(event) => setNumber('cardio_trainings_per_week', event.target.value)}
            />
          </label>
          <label className="field">
            <span>Средняя продолжительность кардио, минут</span>
            <input
              type="number"
              min="10"
              max="300"
              step="1"
              required
              value={form.cardio_training_duration_minutes || ''}
              onChange={(event) =>
                setNumber('cardio_training_duration_minutes', event.target.value)
              }
            />
          </label>
          <label className="field">
            <span>Интенсивность кардио</span>
            <select
              value={form.cardio_intensity}
              onChange={(event) =>
                setForm({
                  ...form,
                  cardio_intensity: event.target.value as NutritionTargetSave['cardio_intensity'],
                })
              }
            >
              <option value="low">Низкая (4 MET)</option>
              <option value="moderate">Средняя (6 MET)</option>
              <option value="high">Высокая (8 MET)</option>
            </select>
          </label>
        </div>

        {!calculation.valid && (
          <div className="nutrition-warning" role="alert">
            <strong>Проверьте данные</strong>
            <ul>
              {calculation.errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {estimate && (
          <>
            <div className="metric-grid nutrition-metrics" aria-live="polite">
              <div className="metric">
                <span>Калории</span>
                <strong>{estimate.calories} ккал</strong>
              </div>
              <div className="metric">
                <span>Белки</span>
                <strong>{estimate.protein} г</strong>
              </div>
              <div className="metric">
                <span>Жиры</span>
                <strong>{estimate.fat} г</strong>
              </div>
              <div className="metric">
                <span>Углеводы</span>
                <strong>{estimate.carbs} г</strong>
              </div>
            </div>

            {estimate.macroWarning && (
              <div className="nutrition-warning" role="alert">
                Исходная калорийность была ниже норм белка и жиров, поэтому ориентир автоматически
                повышен до минимально согласованного значения, а углеводы показаны как 0 г.
              </div>
            )}

            <details className="nutrition-details">
              <summary>Подробнее о расчёте</summary>
              <p>Основной обмен: {estimate.bmr} ккал.</p>
              <p>Повседневная активность: ×{estimate.activityCoefficient}.</p>
              <p>Расход без тренировок: {estimate.baseTdee} ккал.</p>
              <p>Силовые тренировки: в среднем {estimate.strengthDailyCalories} ккал в день.</p>
              <p>Кардио: в среднем {estimate.cardioDailyCalories} ккал в день.</p>
              <p>Поддерживающая калорийность: {estimate.maintenanceCalories} ккал.</p>
              <p>
                Цель «{goalLabels[form.goal]}»: {goalAdjustmentLabels[form.goal]}.
              </p>
              <p>Целевая калорийность: {estimate.calories} ккал.</p>
            </details>
          </>
        )}

        <aside className="nutrition-reality-check">
          <strong>Важна проверка по реальной динамике</strong>
          <p>Наблюдайте 14–21 день:</p>
          <ul>
            <li>ежедневно взвешивайтесь утром в одинаковых условиях;</li>
            <li>считайте среднюю массу за каждую неделю;</li>
            <li>поддерживайте примерно одинаковую активность;</li>
            <li>считайте среднее фактическое потребление калорий.</li>
          </ul>
          <p>
            Если средняя масса стабильна — это ваша реальная поддерживающая калорийность. Если
            снижается слишком быстро — добавьте 100–200 ккал. Если стоит — уберите 100–150 ккал.
          </p>
        </aside>

        <button disabled={mutation.isPending || !calculation.valid}>
          {mutation.isPending ? 'Сохраняем…' : 'Сохранить КБЖУ'}
        </button>
      </form>
    </Card>
  );
}
