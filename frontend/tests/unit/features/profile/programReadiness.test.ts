import { describe, expect, it } from 'vitest';
import { programProfileReadiness } from '../../../../src/features/profile/programReadiness';

describe('programProfileReadiness', () => {
  it('counts only the canonical program recommendation fields', () => {
    expect(programProfileReadiness(null)).toEqual({ completed: 0, total: 3, isComplete: false });
    expect(
      programProfileReadiness({
        full_name: 'Анна',
        goal: 'maintenance',
        level: null,
        workouts_per_week: 0,
        timezone: 'Europe/Moscow',
      }),
    ).toEqual({ completed: 1, total: 3, isComplete: false });
    expect(
      programProfileReadiness({
        goal: 'maintenance',
        level: 'beginner',
        workouts_per_week: 3,
        timezone: 'Europe/Moscow',
      }),
    ).toEqual({ completed: 3, total: 3, isComplete: true });
  });
});
