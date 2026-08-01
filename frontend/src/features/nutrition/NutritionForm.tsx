import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { NutritionTarget, NutritionTargetSave } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card } from '../../shared/ui/common';

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

export function NutritionForm({
  targetTelegramId,
  initial,
  onSaved,
}: {
  targetTelegramId?: number | null;
  initial?: NutritionTarget | null;
  onSaved?: () => void;
}) {
  const { toast } = useFeedback();
  const [form, setForm] = useState<NutritionTargetSave>(() =>
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

  const estimate = useMemo(() => {
    const base =
      10 * form.weight_kg + 6.25 * form.height_cm - 5 * form.age + (form.sex === 'male' ? 5 : -161);
    const factor = { sedentary: 1.2, low: 1.35, moderate: 1.5, high: 1.7 }[
      form.daily_activity_level
    ];
    const training =
      form.strength_trainings_per_week * form.strength_training_duration_minutes * 4 +
      form.cardio_trainings_per_week * form.cardio_training_duration_minutes * 5;
    const maintenance = Math.round(base * factor + training / 7);
    const calories = Math.round(
      maintenance *
        { fat_loss: 0.85, muscle_gain: 1.1, maintenance: 1, recomposition: 0.95 }[form.goal],
    );
    const protein = Math.round(form.weight_kg * (form.goal === 'muscle_gain' ? 2 : 1.8));
    const fat = Math.round(form.weight_kg * 0.9);
    const carbs = Math.max(0, Math.round((calories - protein * 4 - fat * 9) / 4));
    return { calories, protein, fat, carbs };
  }, [form]);

  const mutation = useMutation({
    mutationFn: () =>
      api<NutritionTarget>('/api/v1/nutrition/targets', {
        method: 'POST',
        body: { ...form, target_telegram_user_id: targetTelegramId || null },
      }),
    onSuccess: () => {
      toast('Ориентиры КБЖУ сохранены');
      onSaved?.();
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const setNumber = (key: keyof NutritionTargetSave, value: string) =>
    setForm({ ...form, [key]: Number(value) });

  return (
    <Card title="КБЖУ" description="Расчёт является ориентиром и может корректироваться тренером.">
      <form
        className="stack top-gap"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="form-grid">
          <label className="field">
            <span>Пол</span>
            <select
              value={form.sex}
              onChange={(e) => setForm({ ...form, sex: e.target.value as 'male' | 'female' })}
            >
              <option value="male">Мужской</option>
              <option value="female">Женский</option>
            </select>
          </label>
          <label className="field">
            <span>Возраст</span>
            <input
              type="number"
              min="14"
              max="100"
              value={form.age}
              onChange={(e) => setNumber('age', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Вес, кг</span>
            <input
              type="number"
              min="25"
              max="500"
              step="0.1"
              value={form.weight_kg}
              onChange={(e) => setNumber('weight_kg', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Рост, см</span>
            <input
              type="number"
              min="80"
              max="250"
              value={form.height_cm}
              onChange={(e) => setNumber('height_cm', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Активность</span>
            <select
              value={form.daily_activity_level}
              onChange={(e) =>
                setForm({
                  ...form,
                  daily_activity_level: e.target
                    .value as NutritionTargetSave['daily_activity_level'],
                })
              }
            >
              <option value="sedentary">Сидячая</option>
              <option value="low">Низкая</option>
              <option value="moderate">Средняя</option>
              <option value="high">Высокая</option>
            </select>
          </label>
          <label className="field">
            <span>Цель</span>
            <select
              value={form.goal}
              onChange={(e) =>
                setForm({ ...form, goal: e.target.value as NutritionTargetSave['goal'] })
              }
            >
              <option value="fat_loss">Похудение</option>
              <option value="muscle_gain">Набор</option>
              <option value="maintenance">Поддержание</option>
              <option value="recomposition">Рекомпозиция</option>
            </select>
          </label>
          <label className="field">
            <span>Силовых</span>
            <input
              type="number"
              min="0"
              max="14"
              value={form.strength_trainings_per_week}
              onChange={(e) => setNumber('strength_trainings_per_week', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Минут силовой</span>
            <input
              type="number"
              min="10"
              max="300"
              value={form.strength_training_duration_minutes}
              onChange={(e) => setNumber('strength_training_duration_minutes', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Кардио</span>
            <input
              type="number"
              min="0"
              max="14"
              value={form.cardio_trainings_per_week}
              onChange={(e) => setNumber('cardio_trainings_per_week', e.target.value)}
            />
          </label>
          <label className="field">
            <span>Минут кардио</span>
            <input
              type="number"
              min="5"
              max="300"
              value={form.cardio_training_duration_minutes}
              onChange={(e) => setNumber('cardio_training_duration_minutes', e.target.value)}
            />
          </label>
        </div>
        <div className="metric-grid">
          <div className="metric">
            <span>Калории</span>
            <strong>{estimate.calories}</strong>
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
        <button disabled={mutation.isPending}>
          {mutation.isPending ? 'Сохраняем…' : 'Сохранить КБЖУ'}
        </button>
      </form>
    </Card>
  );
}
