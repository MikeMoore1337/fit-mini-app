import { describe, expect, it } from 'vitest';
import { applyRestSeconds } from '../../../../src/features/programs/programRest';

describe('applyRestSeconds', () => {
  it('applies common rest to every exercise without mutating the draft', () => {
    const days = [
      {
        title: 'День 1',
        exercises: [
          {
            exercise_id: 1,
            prescribed_sets: 3,
            prescribed_reps: '10',
            rest_seconds: 60,
          },
          {
            exercise_id: 2,
            prescribed_sets: 4,
            prescribed_reps: '8',
            rest_seconds: 120,
          },
        ],
      },
    ];

    const result = applyRestSeconds(days, 90);

    expect(result[0]?.exercises.map((exercise) => exercise.rest_seconds)).toEqual([90, 90]);
    expect(days[0]?.exercises.map((exercise) => exercise.rest_seconds)).toEqual([60, 120]);
  });
});
