import { describe, expect, it } from 'vitest';
import type { Exercise } from '../../shared/api/types';
import { buildStrengthPreset, resolveStrengthRule } from './strengthPresets';

const exercises = Array.from(
  { length: 12 },
  (_, index) =>
    ({
      id: index + 1,
      title: `Упражнение ${index + 1}`,
      slug: index === 0 ? 'squat' : `exercise-${index}`,
      difficulty_level: 'beginner',
      is_custom: false,
      is_personalized: false,
      has_guide: false,
    }) satisfies Exercise,
);

describe('strength presets', () => {
  it('uses level-specific day limits', () => {
    expect(resolveStrengthRule('beginner', 'fullbody')).toMatchObject({
      min: 2,
      max: 3,
      recommended: 3,
    });
    expect(resolveStrengthRule('advanced', 'push_pull_legs')).toMatchObject({
      min: 5,
      max: 6,
      recommended: 6,
    });
  });

  it('builds the requested number of non-empty days', () => {
    const days = buildStrengthPreset(exercises, 'beginner', 'fullbody', 3);
    expect(days).toHaveLength(3);
    expect(days.every((day) => day.exercises.length > 0)).toBe(true);
  });
});
