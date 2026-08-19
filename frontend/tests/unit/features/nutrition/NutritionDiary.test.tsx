import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NutritionDiary } from '../../../../src/features/nutrition/NutritionDiary';
import type { Food, FoodDiaryDay, FoodDiaryEntry } from '../../../../src/shared/api/types';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());
const useAuthMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({ useAuth: useAuthMock }));

const nutrition = {
  energy_kcal: '420.00',
  protein_g: '18.500',
  fat_g: '12.000',
  carbs_g: '54.000',
  fiber_g: '7.000',
};

const entry: FoodDiaryEntry = {
  id: 41,
  diary_date: '2026-08-19',
  meal_type: 'breakfast',
  food_id: 7,
  recipe_id: null,
  food_name: 'Овсяная каша',
  food_brand: null,
  amount: '100.000',
  amount_unit: 'g',
  weight_g: '100.000',
  serving_amount: '1.000',
  serving_unit: 'serving',
  serving_weight_g: '50.000',
  nutrition,
  created_at: '2026-08-19T07:00:00Z',
  updated_at: '2026-08-19T07:00:00Z',
};

const food: Food = {
  id: 7,
  name: 'Овсяная каша',
  brand: null,
  barcode: null,
  energy_kcal_per_100g: '420.00',
  protein_g_per_100g: '18.500',
  fat_g_per_100g: '12.000',
  carbs_g_per_100g: '54.000',
  fiber_g_per_100g: '7.000',
  standard_serving_amount: '1.000',
  standard_serving_unit: 'serving',
  standard_serving_weight_g: '50.000',
  food_type: 'system',
  is_favorite: true,
  last_used_at: '2026-08-18T07:00:00Z',
  created_at: '2026-08-01T07:00:00Z',
  updated_at: '2026-08-01T07:00:00Z',
};

function makeDay(entries: FoodDiaryEntry[] = [entry]): FoodDiaryDay {
  return {
    diary_date: '2026-08-19',
    timezone: 'Europe/Moscow',
    meals: [
      { meal_type: 'breakfast', entries, totals: entries.length ? nutrition : zeroNutrition },
      { meal_type: 'lunch', entries: [], totals: zeroNutrition },
      { meal_type: 'dinner', entries: [], totals: zeroNutrition },
      { meal_type: 'snacks', entries: [], totals: zeroNutrition },
    ],
    totals: entries.length ? nutrition : zeroNutrition,
    targets: {
      energy_kcal: '2000.00',
      protein_g: '140.000',
      fat_g: '70.000',
      carbs_g: '220.000',
    },
    remaining: {
      energy_kcal: entries.length ? '1580.00' : '2000.00',
      protein_g: entries.length ? '121.500' : '140.000',
      fat_g: entries.length ? '58.000' : '70.000',
      carbs_g: entries.length ? '166.000' : '220.000',
    },
  };
}

const zeroNutrition = {
  energy_kcal: '0.00',
  protein_g: '0.000',
  fat_g: '0.000',
  carbs_g: '0.000',
  fiber_g: null,
};

function renderDiary() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <NutritionDiary initialDate="2026-08-19" timeZone="Europe/Moscow" />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
}

function breakfastSection(): HTMLElement {
  return screen.getByRole('heading', { name: 'Завтрак' }).closest('section') as HTMLElement;
}

describe('NutritionDiary', () => {
  beforeEach(() => {
    localStorage.clear();
    apiMock.mockReset();
    useAuthMock.mockReturnValue({ user: { id: 10 } });
  });

  afterEach(cleanup);

  it('shows all meals, entry macros, targets and navigates by date', async () => {
    apiMock.mockResolvedValue(makeDay());
    renderDiary();

    expect(await screen.findByText('Овсяная каша')).toBeInTheDocument();
    expect(
      screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent),
    ).toEqual(expect.arrayContaining(['Завтрак', 'Обед', 'Ужин', 'Перекусы', 'Итоги и цель']));
    expect(screen.getByRole('progressbar', { name: /Калории: 420 из 2.+000 ккал/ })).toBeVisible();
    expect(screen.getByText('Б 18,5')).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: 'Предыдущий день' }));
    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith('/api/v1/nutrition/diary?diary_date=2026-08-18'),
    );
  });

  it('adds a recent product and reloads the persisted diary', async () => {
    let logged = false;
    apiMock.mockImplementation((path: string, options?: { method?: string; body?: unknown }) => {
      if (path.startsWith('/api/v1/nutrition/diary?')) {
        return Promise.resolve(makeDay(logged ? [entry] : []));
      }
      if (path.startsWith('/api/v1/nutrition/foods/recent')) {
        return Promise.resolve({ items: [food], total: 1, limit: 12, offset: 0 });
      }
      if (path.startsWith('/api/v1/nutrition/foods/favorites')) {
        return Promise.resolve({ items: [], total: 0, limit: 12, offset: 0 });
      }
      if (path === '/api/v1/nutrition/diary/entries' && options?.method === 'POST') {
        logged = true;
        return Promise.resolve(entry);
      }
      throw new Error(`Unexpected API call: ${path}`);
    });
    renderDiary();
    await screen.findAllByText('Пока без записей');

    fireEvent.click(within(breakfastSection()).getByRole('button', { name: /Добавить/ }));
    fireEvent.click(await screen.findByRole('button', { name: 'Добавить Овсяная каша' }));
    const amount = screen.getByRole('spinbutton', { name: 'Количество' });
    fireEvent.change(amount, { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Добавить в дневник' }));

    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith(
        '/api/v1/nutrition/diary/entries',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({
            food_id: 7,
            amount: 2,
            amount_unit: 'serving',
            meal_type: 'breakfast',
          }),
        }),
      ),
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Овсяная каша')).toBeVisible();
    expect(localStorage.getItem('fit_food_draft_10_2026-08-19_breakfast')).toBeNull();
  });

  it('keeps the quantity draft through a recoverable failure and remount', async () => {
    apiMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path.startsWith('/api/v1/nutrition/diary?')) return Promise.resolve(makeDay([]));
      if (path.startsWith('/api/v1/nutrition/foods/recent')) {
        return Promise.resolve({ items: [food], total: 1, limit: 12, offset: 0 });
      }
      if (path.startsWith('/api/v1/nutrition/foods/favorites')) {
        return Promise.resolve({ items: [], total: 0, limit: 12, offset: 0 });
      }
      if (path === '/api/v1/nutrition/diary/entries' && options?.method === 'POST') {
        return Promise.reject(new Error('Соединение прервано'));
      }
      throw new Error(`Unexpected API call: ${path}`);
    });
    const first = renderDiary();
    await screen.findAllByText('Пока без записей');
    fireEvent.click(within(breakfastSection()).getByRole('button', { name: /Добавить/ }));
    fireEvent.click(await screen.findByRole('button', { name: 'Добавить Овсяная каша' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Количество' }), {
      target: { value: '2.5' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Добавить в дневник' }));

    expect(await screen.findByText('Соединение прервано')).toBeVisible();
    expect(screen.getByRole('spinbutton', { name: 'Количество' })).toHaveValue(2.5);
    first.unmount();

    renderDiary();
    await screen.findAllByText('Пока без записей');
    fireEvent.click(within(breakfastSection()).getByRole('button', { name: /Добавить/ }));
    expect(await screen.findByRole('spinbutton', { name: 'Количество' })).toHaveValue(2.5);
    expect(screen.getByRole('heading', { name: 'Овсяная каша' })).toBeVisible();
  });

  it('edits and deletes an entry with explicit confirmation', async () => {
    let currentEntries = [entry];
    apiMock.mockImplementation((path: string, options?: { method?: string; body?: unknown }) => {
      if (path.startsWith('/api/v1/nutrition/diary?')) {
        return Promise.resolve(makeDay(currentEntries));
      }
      if (path.endsWith('/entries/41') && options?.method === 'PATCH') {
        currentEntries = [{ ...entry, amount: '150.000', weight_g: '150.000' }];
        return Promise.resolve(currentEntries[0]);
      }
      if (path.endsWith('/entries/41') && options?.method === 'DELETE') {
        currentEntries = [];
        return Promise.resolve(undefined);
      }
      throw new Error(`Unexpected API call: ${path}`);
    });
    renderDiary();
    await screen.findByText('Овсяная каша');

    fireEvent.click(screen.getByRole('button', { name: 'Изменить' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Количество' }), {
      target: { value: '150' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith(
        '/api/v1/nutrition/diary/entries/41',
        expect.objectContaining({ method: 'PATCH', body: { amount: 150, amount_unit: 'g' } }),
      ),
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Удалить' }));
    const confirmDialog = await screen.findByRole('dialog', { name: 'Удалить запись?' });
    fireEvent.click(within(confirmDialog).getByRole('button', { name: 'Удалить' }));
    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith('/api/v1/nutrition/diary/entries/41', {
        method: 'DELETE',
      }),
    );
    await waitFor(() => expect(screen.queryByText('Овсяная каша')).not.toBeInTheDocument());
  });

  it('retries the day and keeps favorites usable when recent products fail', async () => {
    let diaryAttempts = 0;
    apiMock.mockImplementation((path: string) => {
      if (path.startsWith('/api/v1/nutrition/diary?')) {
        diaryAttempts += 1;
        return diaryAttempts === 1
          ? Promise.reject(new Error('Дневник недоступен'))
          : Promise.resolve(makeDay([]));
      }
      if (path.startsWith('/api/v1/nutrition/foods/recent')) {
        return Promise.reject(new Error('Недавние недоступны'));
      }
      if (path.startsWith('/api/v1/nutrition/foods/favorites')) {
        return Promise.resolve({ items: [food], total: 1, limit: 12, offset: 0 });
      }
      throw new Error(`Unexpected API call: ${path}`);
    });
    renderDiary();

    expect(await screen.findByText('Дневник недоступен')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    await screen.findAllByText('Пока без записей');
    fireEvent.click(within(breakfastSection()).getByRole('button', { name: /Добавить/ }));
    expect(await screen.findByText('Недавние недоступны')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Избранное' }));
    expect(await screen.findByRole('button', { name: 'Добавить Овсяная каша' })).toBeVisible();
  });
});
