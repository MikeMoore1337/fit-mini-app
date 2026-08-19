import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExerciseGuideDialog } from '../../../../src/features/exercises/ExerciseGuideDialog';
import type { Exercise } from '../../../../src/shared/api/types';

const fullExercise: Exercise = {
  id: 1,
  title: 'Тяга верхнего блока',
  primary_muscle: 'Спина',
  equipment: 'Тросовый блок',
  primary_muscle_ids: ['back'],
  secondary_muscle_ids: ['biceps'],
  equipment_ids: ['cable'],
  alternatives: [{ id: 2, slug: 'band-pulldown', title: 'Тяга резиновой ленты' }],
  difficulty_level: 'beginner',
  is_custom: false,
  is_personalized: false,
  has_guide: true,
  guide: {
    technique_steps: ['Зафиксируйте корпус.', 'Опустите локти под контролем.'],
    breathing: 'Выдохните во время тяги.',
    common_mistakes: ['Раскачивание корпусом'],
    muscles: [
      {
        identifier: 'back',
        name: 'Спина',
        role_id: 'primary',
        role: 'Основная',
        function: 'Тянет плечевой пояс назад и вниз.',
      },
      {
        identifier: 'biceps',
        name: 'Бицепс',
        role_id: 'secondary',
        role: 'Дополнительная',
        function: 'Сгибает локоть.',
      },
    ],
    equipment: [{ identifier: 'cable', name: 'Тросовый блок' }],
    safety_notes: ['Не тяните рукоять рывком.'],
    alternatives: [{ id: 2, slug: 'band-pulldown', title: 'Тяга резиновой ленты' }],
    media: [],
    images: [],
    media_reference: 'exercise-guides:lat-pulldown',
    source_name: 'Проверенный источник',
    source_url: 'https://example.com/source',
    source_license: 'Разрешённая лицензия',
    source_license_url: 'https://example.com/license',
  },
};

const customExercise: Exercise = {
  id: 2,
  title: 'Тяга резиновой ленты',
  primary_muscle: 'Спина',
  equipment: 'Резиновая лента',
  primary_muscle_ids: [],
  secondary_muscle_ids: [],
  equipment_ids: [],
  alternatives: [{ id: 1, slug: 'lat-pulldown', title: 'Тяга верхнего блока' }],
  difficulty_level: 'beginner',
  is_custom: true,
  is_personalized: true,
  has_guide: false,
  guide: null,
};

function renderGuide() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ExerciseGuideDialog
        exerciseId={fullExercise.id}
        exerciseTitle={fullExercise.title}
        onClose={vi.fn()}
      />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ExerciseGuideDialog', () => {
  it('shows reviewed guide metadata and opens an alternative in the same dialog', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      const exercise = path.endsWith('/2') ? customExercise : fullExercise;
      return new Response(JSON.stringify(exercise), { status: 200 });
    });
    renderGuide();

    expect(await screen.findByRole('heading', { name: 'Техника выполнения' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Основные мышцы' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Дополнительные мышцы' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Оборудование' })).toBeVisible();
    expect(screen.getByText('Не тяните рукоять рывком.')).toBeVisible();
    expect(screen.getByRole('link', { name: 'Разрешённая лицензия' })).toHaveAttribute(
      'href',
      'https://example.com/license',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Тяга резиновой ленты' }));

    expect(await screen.findByRole('heading', { name: 'Техника пока не добавлена' })).toBeVisible();
    expect(screen.getByText('Пользовательское упражнение')).toBeVisible();
    expect(screen.getByText('Резиновая лента')).toBeVisible();
    expect(screen.queryByText('Всё тело')).not.toBeInTheDocument();
    expect(screen.queryByText('Без оборудования')).not.toBeInTheDocument();
  });
});
