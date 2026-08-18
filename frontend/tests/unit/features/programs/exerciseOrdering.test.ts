import { describe, expect, it } from 'vitest';
import type { Exercise } from '../../../../src/shared/api/types';
import { orderExercisesForLevel } from '../../../../src/features/programs/exerciseOrdering';

const exercise = (
  id: number,
  title: string,
  difficulty_level: Exercise['difficulty_level'],
): Exercise => ({
  id,
  title,
  slug: `exercise-${id}`,
  primary_muscle_ids: [],
  secondary_muscle_ids: [],
  equipment_ids: [],
  alternatives: [],
  difficulty_level,
  is_custom: false,
  is_personalized: false,
  has_guide: false,
});

const exercises = [
  exercise(1, 'Среднее Б', 'intermediate'),
  exercise(2, 'Продвинутое', 'advanced'),
  exercise(3, 'Начальное', 'beginner'),
  exercise(4, 'Среднее А', 'intermediate'),
];

describe('exercise ordering by program level', () => {
  it('puts the selected level first and the rest in beginner-to-advanced order', () => {
    expect(orderExercisesForLevel(exercises, 'intermediate').map((item) => item.id)).toEqual([
      4, 1, 3, 2,
    ]);
    expect(orderExercisesForLevel(exercises, 'advanced').map((item) => item.id)).toEqual([
      2, 3, 4, 1,
    ]);
  });
});
