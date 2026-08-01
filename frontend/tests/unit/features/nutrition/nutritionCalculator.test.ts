import { describe, expect, it } from 'vitest';
import type { NutritionTargetSave } from '../../../../src/shared/api/types';
import { calculateNutritionEstimate } from '../../../../src/features/nutrition/nutritionCalculator';

const payload = (overrides: Partial<NutritionTargetSave> = {}): NutritionTargetSave => ({
  sex: 'male',
  weight_kg: 78,
  height_cm: 165,
  age: 34,
  daily_activity_level: 'low',
  strength_trainings_per_week: 4,
  strength_training_duration_minutes: 60,
  cardio_trainings_per_week: 3,
  cardio_training_duration_minutes: 30,
  cardio_intensity: 'moderate',
  goal: 'recomposition',
  ...overrides,
});

describe('nutrition calculator', () => {
  it('matches the requested verification example', () => {
    const result = calculateNutritionEstimate(payload());

    expect(result.valid).toBe(true);
    if (!result.valid) return;
    expect(result.estimate).toEqual({
      bmr: 1646,
      activityCoefficient: 1.3,
      baseTdee: 2140,
      strengthDailyCalories: 223,
      cardioDailyCalories: 100,
      maintenanceCalories: 2463,
      goalMultiplier: 0.95,
      calories: 2340,
      protein: 156,
      fat: 62,
      carbs: 290,
      macroWarning: false,
    });
  });

  it.each([
    ['sedentary', 1.2],
    ['low', 1.3],
    ['moderate', 1.4],
    ['high', 1.5],
  ] as const)('uses the %s daily activity coefficient', (level, coefficient) => {
    const result = calculateNutritionEstimate(
      payload({
        daily_activity_level: level,
        strength_trainings_per_week: 0,
        cardio_trainings_per_week: 0,
      }),
    );

    expect(result.valid && result.estimate.activityCoefficient).toBe(coefficient);
  });

  it('rejects empty-equivalent and unrealistic values without producing NaN', () => {
    const result = calculateNutritionEstimate(
      payload({ weight_kg: 0, cardio_training_duration_minutes: 301 }),
    );

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(2);
    expect(result.estimate).toBeNull();
  });

  it('clamps negative carbohydrates and reports the macro warning', () => {
    const result = calculateNutritionEstimate(
      payload({
        weight_kg: 500,
        height_cm: 50,
        age: 120,
        daily_activity_level: 'sedentary',
        strength_trainings_per_week: 0,
        cardio_trainings_per_week: 0,
        goal: 'fat_loss',
      }),
    );

    expect(result.valid && result.estimate.carbs).toBe(0);
    expect(result.valid && result.estimate.macroWarning).toBe(true);
  });
});
