import { describe, expect, it } from 'vitest';
import {
  formatSetResult,
  formatWorkoutDuration,
} from '../../../../src/features/workouts/TodayWorkout';

describe('formatWorkoutDuration', () => {
  it('formats a workout shorter than one hour', () => {
    expect(formatWorkoutDuration(754)).toBe('12:34');
  });

  it('includes hours for a long workout', () => {
    expect(formatWorkoutDuration(3_661)).toBe('1:01:01');
  });

  it('does not display a negative duration', () => {
    expect(formatWorkoutDuration(-10)).toBe('0:00');
  });
});

describe('formatSetResult', () => {
  it('formats a previous set without inventing missing values', () => {
    expect(formatSetResult(8, 40)).toBe('40 кг × 8');
    expect(formatSetResult(8, null)).toBe('8 повт.');
    expect(formatSetResult(null, 40)).toBe('40 кг');
    expect(formatSetResult(null, null)).toBeNull();
  });
});
