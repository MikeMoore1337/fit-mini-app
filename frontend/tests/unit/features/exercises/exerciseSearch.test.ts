import { describe, expect, it } from 'vitest';
import { matchesExerciseSearch } from '../../../../src/features/exercises/exerciseSearch';
import type { Exercise } from '../../../../src/shared/api/types';

const lowerBodyExercises = [
  ['pendulum-squat', 'Маятниковый присед в тренажёре', ['pendulum squat', 'маятник в тренажере']],
  [
    'plate-loaded-leg-press',
    'Жим ногами в тренажёре с дисками',
    ['жим ногами на блинах', 'plate loaded leg press'],
  ],
  ['unilateral-leg-press', 'Жим одной ногой в тренажёре', ['single leg press']],
  [
    'machine-hip-thrust',
    'Ягодичный мост в рычажном тренажёре',
    ['ягодичный тренажер', 'glute drive'],
  ],
  ['smith-split-squat', 'Сплит-присед в машине Смита', ['смит сплит', 'smith lunge']],
  ['machine-glute-kickback', 'Разгибание бедра назад в тренажёре', ['machine glute kickback']],
  ['v-squat-machine', 'V-присед в рычажном тренажёре', ['v squat machine']],
  ['reverse-hyperextension', 'Обратная гиперэкстензия', ['reverse hyper']],
] as const;

const exercises = lowerBodyExercises.map(
  ([slug, title, aliases], index) =>
    ({
      id: 12020 + index,
      edit_target_id: 12020 + index,
      title,
      slug,
      metric_type: 'strength',
      primary_muscle: 'Ноги',
      equipment: 'Тренажёр',
      primary_muscle_ids: ['legs'],
      secondary_muscle_ids: [],
      equipment_ids: ['machine'],
      aliases: [...aliases],
      movement_pattern: 'squat',
      machine_variant_tags: ['lever'],
      execution_variant_tags: ['bilateral'],
      alternatives: [],
      difficulty_level: 'beginner',
      is_custom: false,
      is_personalized: false,
      has_guide: true,
      source_exercise_id: null,
    }) satisfies Exercise,
);

describe('lower-body exercise aliases', () => {
  it.each([
    ['pendulum squat', 'pendulum-squat'],
    ['жим ногами на блинах', 'plate-loaded-leg-press'],
    ['single leg press', 'unilateral-leg-press'],
    ['ягодичный тренажер', 'machine-hip-thrust'],
    ['smith lunge', 'smith-split-squat'],
    ['machine glute kickback', 'machine-glute-kickback'],
    ['v squat machine', 'v-squat-machine'],
    ['reverse hyper', 'reverse-hyperextension'],
  ])('finds %s as one canonical record', (query, expectedSlug) => {
    expect(exercises.filter((exercise) => matchesExerciseSearch(exercise, query))).toMatchObject([
      { slug: expectedSlug },
    ]);
  });
});
