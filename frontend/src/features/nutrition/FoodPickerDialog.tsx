import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { Food, FoodDiaryEntry, FoodList, FoodSearch } from '../../shared/api/types';
import { usePersistentState } from '../../shared/storage';
import { trackProductEvent, productEventSurface } from '../../shared/analytics/productEvents';
import {
  Badge,
  Button,
  CloseIcon,
  ErrorState,
  Field,
  Input,
  LoadingState,
  Select,
} from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { useModalA11y } from '../../shared/ui/useModalA11y';

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';

const mealLabels: Record<MealType, string> = {
  breakfast: 'завтрак',
  lunch: 'обед',
  dinner: 'ужин',
  snacks: 'перекусы',
};

type PickerSource = 'recent' | 'favorites';

interface AddDraft {
  food: Food | null;
  amount: string;
  amountUnit: 'g' | 'serving';
}

function foodSourceLabel(food: Food): string {
  if (food.food_type === 'user') return 'Мой продукт';
  if (food.food_type === 'branded') return 'Брендовый';
  return 'Каталог';
}

function formatPer100(value: string): string {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(Number(value));
}

function FoodResults({ foods, onSelect }: { foods: Food[]; onSelect: (food: Food) => void }) {
  if (!foods.length) {
    return (
      <p className="nutrition-picker__empty">
        Здесь пока пусто. Найдите продукт по названию или добавьте его в каталог позже.
      </p>
    );
  }
  return (
    <ul className="nutrition-food-results" aria-label="Продукты">
      {foods.map((food) => (
        <li key={food.id}>
          <button
            className="nutrition-food-result"
            type="button"
            onClick={() => onSelect(food)}
            aria-label={`Добавить ${food.name}`}
          >
            <span className="nutrition-food-result__main">
              <strong>{food.name}</strong>
              <span>
                {food.brand ? `${food.brand} · ` : ''}
                {formatPer100(food.energy_kcal_per_100g)} ккал на 100 г
              </span>
            </span>
            <span className="nutrition-food-result__meta">
              {food.is_favorite && <span aria-label="В избранном">★</span>}
              <Badge>{foodSourceLabel(food)}</Badge>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function FoodPickerDialog({
  diaryDate,
  mealType,
  onClose,
}: {
  diaryDate: string;
  mealType: MealType;
  onClose: () => void;
}) {
  const { user } = useAuth();
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const panelRef = useModalA11y<HTMLDivElement>(true, onClose, '#nutrition-food-search');
  const [source, setSource] = useState<PickerSource>('recent');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [draft, setDraft, clearDraft] = usePersistentState<AddDraft>(
    `fit_food_draft_${user?.id ?? 'anonymous'}_${diaryDate}_${mealType}`,
    { food: null, amount: '100', amountUnit: 'g' },
  );

  useEffect(() => {
    const normalized = searchInput.trim().replace(/\s+/g, ' ');
    const timer = window.setTimeout(() => setSearchQuery(normalized), 250);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const recent = useQuery({
    queryKey: ['nutrition', 'foods', 'recent'],
    queryFn: () => api<FoodList>('/api/v1/nutrition/foods/recent?limit=12'),
  });
  const favorites = useQuery({
    queryKey: ['nutrition', 'foods', 'favorites'],
    queryFn: () => api<FoodList>('/api/v1/nutrition/foods/favorites?limit=12'),
  });
  const search = useQuery({
    queryKey: ['nutrition', 'foods', 'search', searchQuery],
    queryFn: () =>
      api<FoodSearch>(
        `/api/v1/nutrition/foods/search?q=${encodeURIComponent(searchQuery)}&limit=20`,
      ),
    enabled: searchQuery.length >= 2,
  });

  const activeCollection = source === 'recent' ? recent : favorites;
  const shownFoods = useMemo(() => {
    const items = searchQuery.length >= 2 ? search.data?.items : activeCollection.data?.items;
    return items ?? [];
  }, [activeCollection.data?.items, search.data?.items, searchQuery.length]);
  const activeError = searchQuery.length >= 2 ? search.error : activeCollection.error;
  const activeLoading = searchQuery.length >= 2 ? search.isLoading : activeCollection.isLoading;

  const addEntry = useMutation({
    mutationFn: () => {
      if (!draft.food) throw new Error('Сначала выберите продукт');
      const amount = Number(draft.amount.replace(',', '.'));
      if (!Number.isFinite(amount) || amount <= 0)
        throw new Error('Введите количество больше нуля');
      return api<FoodDiaryEntry>('/api/v1/nutrition/diary/entries', {
        method: 'POST',
        body: {
          food_id: draft.food.id,
          diary_date: diaryDate,
          meal_type: mealType,
          amount,
          amount_unit: draft.amountUnit,
        },
      });
    },
    onSuccess: async () => {
      clearDraft({ food: null, amount: '100', amountUnit: 'g' });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['nutrition', 'diary', diaryDate] }),
        queryClient.invalidateQueries({ queryKey: ['nutrition', 'foods', 'recent'] }),
      ]);
      trackProductEvent({ name: 'food_logged', surface: productEventSurface() });
      toast(`Добавлено в ${mealLabels[mealType]}`);
      onClose();
    },
  });

  const selectFood = (food: Food) => {
    const canUseServing = Boolean(food.standard_serving_weight_g);
    setDraft({
      food,
      amount: canUseServing ? '1' : '100',
      amountUnit: canUseServing ? 'serving' : 'g',
    });
  };

  return (
    <div
      className="modal nutrition-picker"
      role="dialog"
      aria-modal="true"
      aria-labelledby="nutrition-picker-title"
    >
      <div className="modal__backdrop" aria-hidden="true" onClick={onClose} />
      <div className="modal__panel nutrition-picker__panel" ref={panelRef} tabIndex={-1}>
        <header className="nutrition-picker__header">
          <div>
            <span className="eyebrow">Добавить в {mealLabels[mealType]}</span>
            <h2 id="nutrition-picker-title">{draft.food ? draft.food.name : 'Выберите продукт'}</h2>
          </div>
          <Button variant="ghost" type="button" aria-label="Закрыть добавление" onClick={onClose}>
            <CloseIcon />
          </Button>
        </header>

        {draft.food ? (
          <form
            className="nutrition-picker__quantity"
            onSubmit={(event) => {
              event.preventDefault();
              addEntry.mutate();
            }}
          >
            <button
              className="nutrition-picker__back"
              type="button"
              onClick={() => setDraft({ ...draft, food: null })}
            >
              ← Выбрать другой продукт
            </button>
            <div className="nutrition-picker__selected">
              <span>{draft.food.brand || foodSourceLabel(draft.food)}</span>
              <strong>{formatPer100(draft.food.energy_kcal_per_100g)} ккал / 100 г</strong>
              <small>
                Б {formatPer100(draft.food.protein_g_per_100g)} · Ж{' '}
                {formatPer100(draft.food.fat_g_per_100g)} · У{' '}
                {formatPer100(draft.food.carbs_g_per_100g)}
              </small>
            </div>
            <div className="nutrition-picker__amount-grid">
              <Field label="Количество" labelFor="nutrition-food-amount">
                <Input
                  id="nutrition-food-amount"
                  type="number"
                  inputMode="decimal"
                  min="0.001"
                  step="any"
                  required
                  value={draft.amount}
                  onChange={(event) => setDraft({ ...draft, amount: event.target.value })}
                />
              </Field>
              <Field label="Единица" labelFor="nutrition-food-unit">
                <Select
                  id="nutrition-food-unit"
                  value={draft.amountUnit}
                  onChange={(event) =>
                    setDraft({ ...draft, amountUnit: event.target.value as 'g' | 'serving' })
                  }
                >
                  <option value="g">граммы</option>
                  {draft.food.standard_serving_weight_g && <option value="serving">порции</option>}
                </Select>
              </Field>
            </div>
            {draft.amountUnit === 'serving' && draft.food.standard_serving_weight_g && (
              <p className="nutrition-picker__serving-hint">
                1 порция ≈ {formatPer100(draft.food.standard_serving_weight_g)} г
              </p>
            )}
            {addEntry.error && (
              <div className="nutrition-inline-error" role="alert">
                <span>{(addEntry.error as Error).message}</span>
                <button type="button" onClick={() => addEntry.mutate()}>
                  Повторить
                </button>
              </div>
            )}
            <Button fullWidth disabled={addEntry.isPending} type="submit">
              {addEntry.isPending ? 'Добавляем…' : 'Добавить в дневник'}
            </Button>
          </form>
        ) : (
          <div className="nutrition-picker__browse">
            <Field
              label="Поиск по названию или бренду"
              labelFor="nutrition-food-search"
              hint="Локальный поиск начинается после двух символов"
            >
              <Input
                id="nutrition-food-search"
                type="search"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="Например, овсянка"
              />
            </Field>

            {searchQuery.length < 2 && (
              <div className="nutrition-picker__tabs" aria-label="Быстрое добавление">
                <button
                  type="button"
                  className={source === 'recent' ? 'is-active' : ''}
                  aria-pressed={source === 'recent'}
                  onClick={() => setSource('recent')}
                >
                  Недавние
                </button>
                <button
                  type="button"
                  className={source === 'favorites' ? 'is-active' : ''}
                  aria-pressed={source === 'favorites'}
                  onClick={() => setSource('favorites')}
                >
                  Избранное
                </button>
              </div>
            )}

            {activeLoading && <LoadingState label="Ищем продукты…" />}
            {activeError && (
              <ErrorState
                message={
                  activeError instanceof Error
                    ? activeError.message
                    : 'Не удалось загрузить продукты'
                }
                retry={() =>
                  void (searchQuery.length >= 2 ? search.refetch() : activeCollection.refetch())
                }
              />
            )}
            {!activeLoading && !activeError && (
              <FoodResults foods={shownFoods} onSelect={selectFood} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
