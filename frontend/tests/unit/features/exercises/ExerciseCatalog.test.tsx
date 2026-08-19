import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExerciseCatalog } from '../../../../src/features/exercises/ExerciseCatalog';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const exercises = [
  {
    id: 1,
    title: 'Тяга верхнего блока с очень длинным названием для проверки переноса',
    slug: 'lat-pulldown',
    primary_muscle: 'Спина',
    equipment: 'Тросовый блок',
    primary_muscle_ids: ['back'],
    secondary_muscle_ids: ['biceps'],
    equipment_ids: ['cable'],
    alternatives: [{ id: 2, slug: 'pull-up', title: 'Подтягивания' }],
    difficulty_level: 'beginner',
    is_custom: false,
    is_personalized: false,
    has_guide: true,
  },
  {
    id: 2,
    title: 'Подтягивания',
    slug: 'pull-up',
    primary_muscle: 'Спина',
    equipment: 'Собственный вес',
    primary_muscle_ids: ['back'],
    secondary_muscle_ids: ['biceps'],
    equipment_ids: ['bodyweight'],
    alternatives: [{ id: 1, slug: 'lat-pulldown', title: 'Тяга верхнего блока' }],
    difficulty_level: 'intermediate',
    is_custom: false,
    is_personalized: false,
    has_guide: true,
  },
];

function renderCatalog() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <ExerciseCatalog />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ExerciseCatalog', () => {
  it('filters the visible list by structured equipment and supports an empty search state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(exercises), { status: 200 }),
    );
    renderCatalog();

    expect(await screen.findByText('Подтягивания')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Оборудование'), { target: { value: 'cable' } });

    expect(screen.getByText(/Тяга верхнего блока с очень длинным названием/)).toBeInTheDocument();
    expect(screen.queryByText('Подтягивания')).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('searchbox', { name: 'Поиск' }), {
      target: { value: 'несуществующее движение' },
    });
    expect(screen.getByText('Ничего не найдено')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Сбросить фильтры' })).toBeInTheDocument();
  });

  it('shows a retryable error state when the catalog request fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Каталог временно недоступен' }), { status: 503 }),
    );
    renderCatalog();

    expect(await screen.findByText('Не удалось загрузить данные')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Повторить' })).toBeInTheDocument();
  });
});
