import type { NutritionTargetSave } from '../../shared/api/types';

export const activityCoefficients = {
  sedentary: 1.2,
  low: 1.3,
  moderate: 1.4,
  high: 1.5,
} as const;

export const cardioMetValues = { low: 4, moderate: 6, high: 8 } as const;
export const goalMultipliers = {
  fat_loss: 0.85,
  recomposition: 0.95,
  maintenance: 1,
  muscle_gain: 1.05,
} as const;

export type NutritionEstimate = {
  bmr: number;
  activityCoefficient: number;
  baseTdee: number;
  strengthDailyCalories: number;
  cardioDailyCalories: number;
  maintenanceCalories: number;
  goalMultiplier: number;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  macroWarning: boolean;
};

export type NutritionCalculationResult =
  | { valid: true; estimate: NutritionEstimate; errors: [] }
  | { valid: false; estimate: null; errors: string[] };

const roundNumber = (value: number) => Math.max(0, Math.floor(value + 0.5));
const roundToTen = (value: number) => Math.max(0, Math.floor(value / 10 + 0.5) * 10);
const roundUpToTen = (value: number) => Math.max(0, Math.ceil(value / 10) * 10);

export function calculateNutritionEstimate(form: NutritionTargetSave): NutritionCalculationResult {
  const errors: string[] = [];
  const inRange = (value: number, min: number, max: number, label: string) => {
    if (!Number.isFinite(value) || value < min || value > max) {
      errors.push(`${label}: допустимо от ${min} до ${max}`);
    }
  };

  inRange(form.weight_kg, 20, 350, 'Вес');
  inRange(form.height_cm, 100, 250, 'Рост');
  inRange(form.age, 18, 100, 'Возраст');
  inRange(form.strength_trainings_per_week, 0, 14, 'Силовые тренировки');
  inRange(form.cardio_trainings_per_week, 0, 14, 'Кардиотренировки');
  inRange(form.strength_training_duration_minutes, 10, 300, 'Длительность силовой');
  inRange(form.cardio_training_duration_minutes, 10, 300, 'Длительность кардио');

  if (!Number.isInteger(form.strength_trainings_per_week)) {
    errors.push('Количество силовых тренировок должно быть целым');
  }
  if (!Number.isInteger(form.cardio_trainings_per_week)) {
    errors.push('Количество кардиотренировок должно быть целым');
  }
  if (errors.length) return { valid: false, estimate: null, errors };

  const bmrExact =
    10 * form.weight_kg + 6.25 * form.height_cm - 5 * form.age + (form.sex === 'male' ? 5 : -161);
  const activityCoefficient = activityCoefficients[form.daily_activity_level];
  const baseTdeeExact = bmrExact * activityCoefficient;
  const strengthDailyExact =
    (5 *
      form.weight_kg *
      (form.strength_training_duration_minutes / 60) *
      form.strength_trainings_per_week) /
    7;
  const cardioDailyExact =
    (cardioMetValues[form.cardio_intensity] *
      form.weight_kg *
      (form.cardio_training_duration_minutes / 60) *
      form.cardio_trainings_per_week) /
    7;
  const maintenanceExact = baseTdeeExact + strengthDailyExact + cardioDailyExact;
  const goalMultiplier = goalMultipliers[form.goal];
  let calories = roundToTen(maintenanceExact * goalMultiplier);

  const proteinPerKg = {
    fat_loss: 2,
    muscle_gain: 1.8,
    maintenance: 1.6,
    recomposition: 2,
  }[form.goal];
  const fatPerKg = form.goal === 'muscle_gain' ? 0.9 : 0.8;
  const protein = roundNumber(form.weight_kg * proteinPerKg);
  const fat = roundNumber(form.weight_kg * fatPerKg);
  let remainingCalories = calories - protein * 4 - fat * 9;
  const macroWarning = remainingCalories < 0;
  if (macroWarning) {
    calories = roundUpToTen(protein * 4 + fat * 9);
    remainingCalories = calories - protein * 4 - fat * 9;
  }

  return {
    valid: true,
    errors: [],
    estimate: {
      bmr: roundNumber(bmrExact),
      activityCoefficient,
      baseTdee: roundNumber(baseTdeeExact),
      strengthDailyCalories: roundNumber(strengthDailyExact),
      cardioDailyCalories: roundNumber(cardioDailyExact),
      maintenanceCalories: roundNumber(maintenanceExact),
      goalMultiplier,
      calories,
      protein,
      fat,
      carbs: roundNumber(remainingCalories / 4),
      macroWarning,
    },
  };
}
