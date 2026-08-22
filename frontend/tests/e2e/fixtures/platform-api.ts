import type { Page, Route } from '@playwright/test';

type WorkoutStatus = 'planned' | 'in_progress' | 'completed' | 'none';

export interface PlatformApiOptions {
  browserSession?: boolean;
  workoutStatus?: WorkoutStatus;
  activeProgram?: boolean;
  weeklyReviewAvailable?: boolean;
}

export interface PlatformApiController {
  setOffline(offline: boolean): void;
  authInitCalls(): number;
  setPatchCalls(): number;
  workoutValues(): { actualReps: number | null; actualWeight: number | null; completed: boolean };
}

const zeroNutrition = {
  energy_kcal: '0.00',
  protein_g: '0.000',
  fat_g: '0.000',
  carbs_g: '0.000',
  fiber_g: null,
};

const oatmeal = {
  id: 7,
  name: 'Овсяная каша',
  brand: null,
  barcode: null,
  energy_kcal_per_100g: '360.00',
  protein_g_per_100g: '12.000',
  fat_g_per_100g: '6.000',
  carbs_g_per_100g: '62.000',
  fiber_g_per_100g: '8.000',
  standard_serving_amount: '1.000',
  standard_serving_unit: 'serving',
  standard_serving_weight_g: '50.000',
  food_type: 'system',
  is_favorite: true,
  last_used_at: '2030-01-09T07:00:00Z',
  created_at: '2030-01-01T07:00:00Z',
  updated_at: '2030-01-09T07:00:00Z',
};

export async function installPlatformApi(
  page: Page,
  options: PlatformApiOptions = {},
): Promise<PlatformApiController> {
  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Europe/Moscow' });
  const todayDate = new Date(`${today}T12:00:00Z`);
  const contextDate = new Date(todayDate);
  const contextIsCompleted = todayDate.getUTCDay() === 0;
  contextDate.setUTCDate(todayDate.getUTCDate() + (contextIsCompleted ? -1 : 1));
  const contextDay = contextDate.toISOString().slice(0, 10);
  let offline = false;
  let workoutStatus = options.workoutStatus ?? 'planned';
  const activeProgram = options.activeProgram ?? true;
  let authInitCalls = 0;
  let patchCalls = 0;
  let setVersion = 1;
  let setValues = {
    actualReps: null as number | null,
    actualWeight: null as number | null,
    completed: false,
  };
  let nutritionEntries: Array<Record<string, unknown>> = [];

  if (options.browserSession) {
    await page.addInitScript(() => sessionStorage.setItem('fit_access_token', 'e2e-browser-token'));
  }

  const workout = () => ({
    id: 42,
    scheduled_date: today,
    scheduled_time: '18:30:00',
    title: 'Силовая база',
    status: workoutStatus,
    day_number: 1,
    week_number: 1,
    started_at: workoutStatus === 'in_progress' ? `${today}T10:00:00` : null,
    completed_at: workoutStatus === 'completed' ? `${today}T11:00:00` : null,
    exercises: [
      {
        id: 101,
        exercise_id: 11,
        exercise_title: 'Приседания',
        sort_order: 1,
        prescribed_sets: 1,
        prescribed_reps: '8–10',
        rest_seconds: 90,
        notes: null,
        has_guide: false,
        sets: [
          {
            id: 201,
            set_number: 1,
            actual_reps: setValues.actualReps,
            actual_weight: setValues.actualWeight,
            rir: null,
            set_kind: 'working',
            reached_failure: false,
            is_completed: setValues.completed,
            version: setVersion,
          },
        ],
      },
    ],
  });

  const contextWorkout = {
    id: 43,
    scheduled_date: contextDay,
    scheduled_time: '09:00:00',
    title: 'Контекст недели',
    status: contextIsCompleted ? 'completed' : 'planned',
    day_number: 2,
    week_number: 1,
  };

  const progressSummary = {
    user_id: 7,
    period_days: 30,
    period_start: today,
    period_end: today,
    training: {
      planned_workouts: 1,
      completed_workouts: workoutStatus === 'completed' ? 1 : 0,
      frequency_per_week: 0,
      volume_kg: 0,
      new_personal_records: 0,
      last_completed_workout_on: workoutStatus === 'completed' ? today : null,
      next_workout: null,
    },
    nutrition: {
      visible: true,
      logged_days: nutritionEntries.length ? 1 : 0,
      adherence_evaluated_days: 0,
      average_calories: null,
      target_calories: 2100,
      average_protein_g: null,
      target_protein_g: 140,
      target_effective_on: today,
    },
    body: { latest_measurement: null, trends: [], priority: null, guidance: {} },
    adherence: {
      formula_version: 'adherence-v1',
      overall_percent: null,
      included_components: [],
      workouts: {},
      cardio: {},
      calories: {},
      protein: {},
    },
    data_sufficiency: {},
  };

  await page.route('**/api/v1/**', async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (offline && !path.endsWith('/public/config')) return route.abort('internetdisconnected');
    if (path.endsWith('/public/config')) {
      return route.fulfill({
        json: {
          app_env: 'test',
          enable_dev_auth: true,
          enable_web_auth: false,
          enable_email_auth: false,
          telegram_bot_username: 'fit_test_bot',
          oauth_providers: [],
        },
      });
    }
    if (path.endsWith('/auth/refresh')) {
      return route.fulfill({ status: 401, json: { detail: 'No refresh cookie' } });
    }
    if (path.endsWith('/auth/telegram/init')) {
      authInitCalls += 1;
      return route.fulfill({
        json: { access_token: 'telegram-test-token', token_type: 'bearer' },
      });
    }
    if (path.endsWith('/auth/dev-login')) {
      return route.fulfill({ json: { access_token: 'dev-test-token', token_type: 'bearer' } });
    }
    if (path.endsWith('/me')) {
      return route.fulfill({
        json: {
          id: 7,
          telegram_user_id: 7007,
          username: 'mobile_user',
          first_name: 'Анна',
          is_coach: false,
          is_admin: false,
          has_active_program: activeProgram,
          has_workout_history: false,
          onboarding: { status: 'complete', required_fields: [], missing_fields: [] },
          profile: {
            full_name: 'Анна Петрова',
            timezone: 'Europe/Moscow',
            goal: 'maintenance',
            level: 'beginner',
            height_cm: 168,
            weight_kg: 67,
            workouts_per_week: 3,
            cardio_trainings_per_week: 1,
            kbju: null,
          },
          trainer: null,
        },
      });
    }
    if (path.endsWith('/workouts/today')) {
      if (workoutStatus === 'completed' || workoutStatus === 'none') {
        return route.fulfill({
          status: 404,
          json: { detail: 'На сегодня тренировка не назначена' },
        });
      }
      return route.fulfill({ json: workout() });
    }
    if (path.endsWith('/workouts/week')) {
      if (!activeProgram) return route.fulfill({ json: [] });
      return route.fulfill({
        json: [...(workoutStatus === 'none' ? [] : [workout()]), contextWorkout],
      });
    }
    if (path.endsWith('/workouts/schedule')) {
      return route.fulfill({ json: contextIsCompleted ? [] : [contextWorkout] });
    }
    if (path.endsWith('/workouts/history')) {
      return route.fulfill({
        json: contextIsCompleted
          ? [
              {
                ...contextWorkout,
                started_at: `${contextDay}T08:00:00`,
                completed_at: `${contextDay}T09:00:00`,
                completed_sets: 1,
                volume_kg: 40,
                exercises: [],
                adaptations: [],
              },
            ]
          : [],
      });
    }
    if (path.endsWith('/workouts/history/summary')) {
      return route.fulfill({
        json: {
          workouts_completed: contextIsCompleted ? 1 : 0,
          completed_sets: contextIsCompleted ? 1 : 0,
          volume_kg: contextIsCompleted ? 40 : 0,
        },
      });
    }
    if (path.endsWith('/workouts/42/start')) {
      workoutStatus = 'in_progress';
      return route.fulfill({ json: workout() });
    }
    if (path.endsWith('/workouts/sets/201')) {
      patchCalls += 1;
      const body = request.postDataJSON() as {
        actual_reps: number | null;
        actual_weight: number | null;
        is_completed: boolean;
      };
      setValues = {
        actualReps: body.actual_reps,
        actualWeight: body.actual_weight,
        completed: body.is_completed,
      };
      setVersion += 1;
      return route.fulfill({
        json: {
          id: 201,
          set_number: 1,
          actual_reps: setValues.actualReps,
          actual_weight: setValues.actualWeight,
          rir: null,
          set_kind: 'working',
          reached_failure: false,
          is_completed: setValues.completed,
          version: setVersion,
        },
      });
    }
    if (path.endsWith('/workouts/progress/summary')) {
      return route.fulfill({ json: progressSummary });
    }
    if (path.endsWith('/check-ins/weekly/current')) {
      return route.fulfill({
        json: {
          week_start: today,
          week_end: today,
          submitted_on: today,
          timezone: 'Europe/Moscow',
          existing: options.weeklyReviewAvailable ? null : { id: 1 },
          summary: {
            training: { completed_workouts: 0, planned_workouts: 1 },
            nutrition: { logged_days: nutritionEntries.length ? 1 : 0 },
            progression: { new_personal_records: 0 },
            weight_trend: null,
          },
        },
      });
    }
    if (/\/workouts\/\d+\/comments$/.test(path)) return route.fulfill({ json: [] });
    if (path.endsWith('/nutrition/diary') && request.method() === 'GET') {
      return route.fulfill({
        json: {
          diary_date: url.searchParams.get('diary_date') || today,
          timezone: 'Europe/Moscow',
          meals: [
            { meal_type: 'breakfast', entries: nutritionEntries, totals: zeroNutrition },
            { meal_type: 'lunch', entries: [], totals: zeroNutrition },
            { meal_type: 'dinner', entries: [], totals: zeroNutrition },
            { meal_type: 'snacks', entries: [], totals: zeroNutrition },
          ],
          totals: zeroNutrition,
          targets: {
            energy_kcal: '2100.00',
            protein_g: '140.000',
            fat_g: '70.000',
            carbs_g: '230.000',
          },
          remaining: {
            energy_kcal: '2100.00',
            protein_g: '140.000',
            fat_g: '70.000',
            carbs_g: '230.000',
          },
        },
      });
    }
    if (path.endsWith('/nutrition/foods/recent') || path.endsWith('/nutrition/foods/favorites')) {
      return route.fulfill({ json: { items: [oatmeal], total: 1, limit: 12, offset: 0 } });
    }
    if (path.endsWith('/nutrition/diary/entries') && request.method() === 'POST') {
      const body = request.postDataJSON() as { diary_date: string; meal_type: string };
      const entry = {
        id: 21,
        diary_date: body.diary_date,
        meal_type: body.meal_type,
        food_id: oatmeal.id,
        recipe_id: null,
        food_name: oatmeal.name,
        food_brand: null,
        amount: '1.000',
        amount_unit: 'serving',
        weight_g: '50.000',
        serving_amount: '1.000',
        serving_unit: 'serving',
        serving_weight_g: '50.000',
        nutrition: {
          energy_kcal: '180.00',
          protein_g: '6.000',
          fat_g: '3.000',
          carbs_g: '31.000',
          fiber_g: '4.000',
        },
        created_at: `${today}T07:00:00Z`,
        updated_at: `${today}T07:00:00Z`,
      };
      nutritionEntries = [...nutritionEntries, entry];
      return route.fulfill({ status: 201, json: entry });
    }
    return route.fulfill({
      status: 404,
      json: { detail: `Not available in platform smoke: ${path}` },
    });
  });

  return {
    setOffline(value) {
      offline = value;
    },
    authInitCalls() {
      return authInitCalls;
    },
    setPatchCalls() {
      return patchCalls;
    },
    workoutValues() {
      return { ...setValues };
    },
  };
}
