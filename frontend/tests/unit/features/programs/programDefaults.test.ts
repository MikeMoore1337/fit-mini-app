import { describe, expect, it } from 'vitest';
import {
  SIMPLE_PROGRAM_DEFAULTS,
  simpleTrainingTitle,
  trainingCountLabel,
} from '../../../../src/features/programs/programDefaults';

describe('simple program defaults', () => {
  it('keeps required API fields deterministic without asking the beginner first', () => {
    expect(SIMPLE_PROGRAM_DEFAULTS).toEqual({
      title: 'Моя программа',
      goal: 'maintenance',
      level: 'beginner',
      durationWeeks: 1,
      restSeconds: 90,
    });
    expect(simpleTrainingTitle(1)).toBe('Тренировка 1');
  });

  it('uses Russian plural forms for the available training count range', () => {
    expect(trainingCountLabel(1)).toBe('1 тренировка');
    expect(trainingCountLabel(2)).toBe('2 тренировки');
    expect(trainingCountLabel(5)).toBe('5 тренировок');
    expect(trainingCountLabel(8)).toBe('8 тренировок');
  });
});
