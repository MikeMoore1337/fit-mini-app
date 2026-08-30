import type { ProgramTemplateCreate } from '../../shared/api/types';

export const SIMPLE_PROGRAM_DEFAULTS = {
  title: 'Моя программа',
  goal: 'maintenance' as ProgramTemplateCreate['goal'],
  level: 'beginner' as ProgramTemplateCreate['level'],
  durationWeeks: 1,
  restSeconds: 90,
} as const;

export function simpleTrainingTitle(index: number): string {
  return `Тренировка ${index}`;
}

export function trainingCountLabel(count: number): string {
  const modulo100 = count % 100;
  const modulo10 = count % 10;
  const noun =
    modulo100 >= 11 && modulo100 <= 14
      ? 'тренировок'
      : modulo10 === 1
        ? 'тренировка'
        : modulo10 >= 2 && modulo10 <= 4
          ? 'тренировки'
          : 'тренировок';
  return `${count} ${noun}`;
}
