import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NutritionTargetHistory } from '../../../../src/features/nutrition/NutritionTargetHistory';
import type { NutritionTarget } from '../../../../src/shared/api/types';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));

function target(overrides: Partial<NutritionTarget> = {}): NutritionTarget {
  return {
    id: 2,
    user_id: 10,
    effective_from: '2026-08-20',
    effective_to: null,
    source: 'trainer',
    created_at: '2026-08-20T09:00:00',
    calories: 2200,
    protein_g: 150,
    fat_g: 70,
    carbs_g: 242,
    strength_rest: null,
    saved_at: '2026-08-20T09:00:00',
    created_by: { id: 4, telegram_user_id: 4004, full_name: 'Мария Тренер' },
    ...overrides,
  };
}

function renderHistory(targetTelegramId?: number) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <NutritionTargetHistory targetTelegramId={targetTelegramId} />
    </QueryClientProvider>,
  );
}

describe('NutritionTargetHistory', () => {
  beforeEach(() => apiMock.mockReset());
  afterEach(cleanup);

  it('shows current trainer source and an accessible previous-to-new diff list', async () => {
    apiMock.mockResolvedValue({
      items: [
        target(),
        target({
          id: 1,
          source: 'manual',
          effective_from: '2026-08-01',
          effective_to: '2026-08-20',
          calories: 2000,
          protein_g: 140,
          fat_g: 65,
          carbs_g: 214,
          created_by: { id: 10, telegram_user_id: 1010, full_name: 'Анна Пользователь' },
        }),
      ],
    });
    renderHistory(55005);

    expect(await screen.findByText('Назначено тренером')).toBeInTheDocument();
    expect(screen.getAllByText('Изменил: Мария Тренер')).toHaveLength(2);
    const currentVersion = screen.getByText('Назначено тренером · 2200 ккал');
    fireEvent.click(currentVersion.closest('summary')!);
    expect(screen.getByText('Калории 2000 → 2200 ккал')).toBeInTheDocument();
    expect(screen.getByText('Белки 140 → 150 г')).toBeInTheDocument();
    expect(apiMock).toHaveBeenCalledWith(
      '/api/v1/nutrition/targets/history?target_telegram_user_id=55005',
    );
  });

  it('labels a single history row as the first saved target', async () => {
    apiMock.mockResolvedValue({ items: [target({ source: 'manual', created_by: null })] });
    renderHistory();

    const version = await screen.findByText('Указано вручную · 2200 ккал');
    fireEvent.click(version.closest('summary')!);
    expect(screen.getByText('Первая сохранённая цель.')).toBeInTheDocument();
  });
});
