import type { UserProfileUpdate } from '../../shared/api/types';

export type ProfileGoal = NonNullable<UserProfileUpdate['goal']>;

export const profileGoals: ReadonlyArray<{
  value: ProfileGoal;
  label: string;
  description: string;
}> = [
  {
    value: 'fat_loss',
    label: 'Снизить вес',
    description: 'Постепенно снижать вес, сохраняя силы для тренировок.',
  },
  {
    value: 'muscle_gain',
    label: 'Набрать мышечную массу',
    description: 'Сделать акцент на силовых тренировках и восстановлении.',
  },
  {
    value: 'maintenance',
    label: 'Поддерживать форму',
    description: 'Сохранить текущую форму и регулярно двигаться.',
  },
  {
    value: 'recomposition',
    label: 'Улучшить форму без фокуса на вес',
    description: 'Постепенно менять соотношение мышц и жировой ткани.',
  },
];
