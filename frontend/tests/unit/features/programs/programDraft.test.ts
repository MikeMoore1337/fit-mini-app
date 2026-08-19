import { describe, expect, it } from 'vitest';
import {
  isPairedWithPrevious,
  moveItem,
  removeExercise,
  toggleSuperset,
} from '../../../../src/features/programs/programDraft';

const exercise = (id: number) => ({
  exercise_id: id,
  prescribed_sets: 3,
  prescribed_reps: '8-12',
  rest_seconds: 90,
  notes: null,
  superset_group: null,
  superset_order: null,
});

describe('program draft ordering and supersets', () => {
  it('moves items without changing their contents', () => {
    expect(moveItem(['A', 'B', 'C'], 2, 0)).toEqual(['C', 'A', 'B']);
  });

  it('creates an explicit two-exercise superset with the previous exercise', () => {
    const day = { title: 'День 1', exercises: [exercise(1), exercise(2), exercise(3)] };
    const paired = toggleSuperset(day, 2, true);

    expect(paired.exercises[1]).toMatchObject({ superset_group: 1, superset_order: 1 });
    expect(paired.exercises[2]).toMatchObject({ superset_group: 1, superset_order: 2 });
    expect(isPairedWithPrevious(paired, 2)).toBe(true);
  });

  it('clears the remaining half when an exercise in a superset is removed', () => {
    const paired = toggleSuperset(
      { title: 'День 1', exercises: [exercise(1), exercise(2)] },
      1,
      true,
    );

    expect(removeExercise(paired, 1).exercises[0]).toMatchObject({
      superset_group: null,
      superset_order: null,
    });
  });
});
