import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type {
  ExternalFood,
  Food,
  FoodDiaryEntry,
  FoodList,
  FoodSearch,
  Recipe,
} from '../../shared/api/types';
import { usePersistentState } from '../../shared/storage';
import { foodDraftStorageKey } from '../../shared/userScopedStorage';
import { invalidateNutritionSummaries } from '../../shared/queryKeys';
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
import { BarcodeLookup } from './BarcodeLookup';
import { FoodEditor } from './FoodEditor';
import { RecipeBrowser } from './RecipeBrowser';

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';

const mealLabels: Record<MealType, string> = {
  breakfast: 'завтрак',
  lunch: 'обед',
  dinner: 'ужин',
  snacks: 'перекусы',
};
type PickerSource = 'recent' | 'favorites';
type PickerView = 'browse' | 'food-editor' | 'recipes' | 'barcode';

type FoodDraftSelection = Pick<
  Food,
  | 'id'
  | 'name'
  | 'brand'
  | 'food_type'
  | 'energy_kcal_per_100g'
  | 'protein_g_per_100g'
  | 'fat_g_per_100g'
  | 'carbs_g_per_100g'
  | 'standard_serving_weight_g'
>;

interface AddDraft {
  food: FoodDraftSelection | null;
  amount: string;
  amountUnit: 'g' | 'serving';
}

function foodSourceLabel(food: Pick<Food, 'food_type'>): string {
  if (food.food_type === 'user') return 'Мой продукт';
  if (food.food_type === 'branded') return 'Брендовый';
  return 'Каталог';
}

function foodDraftSelection(food: Food): FoodDraftSelection {
  return {
    id: food.id,
    name: food.name,
    brand: food.brand,
    food_type: food.food_type,
    energy_kcal_per_100g: food.energy_kcal_per_100g,
    protein_g_per_100g: food.protein_g_per_100g,
    fat_g_per_100g: food.fat_g_per_100g,
    carbs_g_per_100g: food.carbs_g_per_100g,
    standard_serving_weight_g: food.standard_serving_weight_g,
  };
}

function formatNumber(value: string): string {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(Number(value));
}

function providerMessage(status: FoodSearch['provider_status']): string | null {
  if (status === 'not_needed')
    return 'В локальном каталоге появился подходящий продукт. Обновите поиск, чтобы выбрать его.';
  if (status === 'disabled')
    return 'Внешний каталог не подключён. Можно выбрать локальный продукт или добавить свой.';
  if (status === 'rate_limited')
    return 'Внешний каталог временно занят. Локальные продукты продолжают работать.';
  if (status === 'unavailable')
    return 'Внешний каталог временно недоступен. Локальные продукты продолжают работать.';
  return null;
}

function FoodResults({
  foods,
  onEdit,
  onFavorite,
  onSelect,
  pendingFavorite,
}: {
  foods: Food[];
  onEdit: (food: Food) => void;
  onFavorite: (food: Food) => void;
  onSelect: (food: Food) => void;
  pendingFavorite: number | null;
}) {
  if (!foods.length)
    return (
      <p className="nutrition-picker__empty">
        Здесь пока пусто. Найдите продукт по названию или создайте свой.
      </p>
    );
  return (
    <ul className="nutrition-food-results" aria-label="Продукты">
      {foods.map((food) => (
        <li className="nutrition-food-result" key={food.id}>
          <button
            className="nutrition-food-result__select"
            type="button"
            onClick={() => onSelect(food)}
            aria-label={`Добавить ${food.name}`}
          >
            <span className="nutrition-food-result__main">
              <strong>{food.name}</strong>
              <span>
                {food.brand ? `${food.brand} · ` : ''}
                {formatNumber(food.energy_kcal_per_100g)} ккал на 100 г
              </span>
            </span>
            <Badge>{foodSourceLabel(food)}</Badge>
          </button>
          <div className="nutrition-food-result__actions">
            <button
              type="button"
              aria-label={
                food.is_favorite
                  ? `Убрать ${food.name} из избранного`
                  : `Добавить ${food.name} в избранное`
              }
              aria-pressed={food.is_favorite}
              disabled={pendingFavorite === food.id}
              onClick={() => onFavorite(food)}
            >
              {food.is_favorite ? '★' : '☆'}
            </button>
            {food.food_type === 'user' && (
              <button
                type="button"
                onClick={() => onEdit(food)}
                aria-label={`Изменить ${food.name}`}
              >
                Изменить
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

function ExternalResults({ response }: { response: FoodSearch }) {
  const fallback = providerMessage(response.provider_status);
  if (fallback)
    return (
      <div className="nutrition-provider-fallback" role="status">
        <strong>Продолжайте с локальным каталогом</strong>
        <span>{fallback}</span>
      </div>
    );
  if (!response.external_items?.length)
    return (
      <div className="nutrition-provider-fallback">
        <strong>Во внешнем каталоге ничего не найдено</strong>
        <span>Попробуйте другое название или создайте свой продукт по данным с упаковки.</span>
      </div>
    );
  return (
    <div className="nutrition-external-results">
      <p>Внешние карточки доступны для сверки и не сохраняются автоматически.</p>
      {response.external_items.map((food: ExternalFood) => (
        <article
          className="nutrition-external-result"
          key={`${food.source.provider}-${food.external_id}`}
        >
          <div>
            <strong>{food.name}</strong>
            <span>
              {food.brand || 'Без бренда'} · {formatNumber(food.energy_kcal_per_100g)} ккал / 100 г
            </span>
          </div>
          <div className="nutrition-external-result__links">
            <a href={food.source.source_url} target="_blank" rel="noreferrer">
              Источник
            </a>
            <a href={food.source.license_url} target="_blank" rel="noreferrer">
              {food.source.attribution} · {food.source.license}
            </a>
          </div>
        </article>
      ))}
    </div>
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
  const [view, setView] = useState<PickerView>('browse');
  const [source, setSource] = useState<PickerSource>('recent');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [externalQuery, setExternalQuery] = useState('');
  const [editingFood, setEditingFood] = useState<Food | undefined>();
  const [editorBarcode, setEditorBarcode] = useState('');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [recipeAmount, setRecipeAmount] = useState('100');
  const [draft, setDraft, clearDraft] = usePersistentState<AddDraft>(
    foodDraftStorageKey(user?.id ?? 'anonymous', diaryDate, mealType),
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
    queryFn: ({ signal }) =>
      api<FoodSearch>(
        `/api/v1/nutrition/foods/search?q=${encodeURIComponent(searchQuery)}&limit=20`,
        { signal },
      ),
    enabled: searchQuery.length >= 2,
  });
  const external = useQuery({
    queryKey: ['nutrition', 'foods', 'external-search', externalQuery],
    queryFn: ({ signal }) =>
      api<FoodSearch>(
        `/api/v1/nutrition/foods/search?q=${encodeURIComponent(externalQuery)}&limit=20&include_external=true`,
        { signal },
      ),
    enabled: externalQuery.length >= 2 && externalQuery === searchQuery,
  });
  const favorite = useMutation({
    mutationFn: (food: Food) =>
      api<Food | void>(`/api/v1/nutrition/foods/${food.id}/favorite`, {
        method: food.is_favorite ? 'DELETE' : 'PUT',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['nutrition', 'foods'] }),
  });
  const activeCollection = source === 'recent' ? recent : favorites;
  const shownFoods = useMemo(
    () => (searchQuery.length >= 2 ? search.data?.items : activeCollection.data?.items) ?? [],
    [activeCollection.data?.items, search.data?.items, searchQuery.length],
  );
  const activeError = searchQuery.length >= 2 ? search.error : activeCollection.error;
  const activeLoading = searchQuery.length >= 2 ? search.isFetching : activeCollection.isLoading;

  const addEntry = useMutation({
    mutationFn: () => {
      const selected = draft.food
        ? {
            food_id: draft.food.id,
            amount: Number(draft.amount.replace(',', '.')),
            amount_unit: draft.amountUnit,
          }
        : selectedRecipe
          ? {
              recipe_id: selectedRecipe.id,
              amount: Number(recipeAmount.replace(',', '.')),
              amount_unit: 'g' as const,
            }
          : null;
      if (!selected) throw new Error('Сначала выберите продукт или рецепт');
      if (!Number.isFinite(selected.amount) || selected.amount <= 0)
        throw new Error('Введите количество больше нуля');
      return api<FoodDiaryEntry>('/api/v1/nutrition/diary/entries', {
        method: 'POST',
        body: { ...selected, diary_date: diaryDate, meal_type: mealType },
      });
    },
    onSuccess: async () => {
      clearDraft({ food: null, amount: '100', amountUnit: 'g' });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['nutrition', 'foods', 'recent'] }),
        invalidateNutritionSummaries(queryClient),
      ]);
      trackProductEvent({ name: 'food_logged', surface: productEventSurface() });
      toast(`Добавлено в ${mealLabels[mealType]}`);
      onClose();
    },
  });
  const selectFood = (food: Food) => {
    setSelectedRecipe(null);
    setDraft({
      food: foodDraftSelection(food),
      amount: food.standard_serving_weight_g ? '1' : '100',
      amountUnit: food.standard_serving_weight_g ? 'serving' : 'g',
    });
  };
  const selectRecipe = (recipe: Recipe) => {
    setDraft({ ...draft, food: null });
    setSelectedRecipe(recipe);
    setRecipeAmount('100');
  };
  const title =
    draft.food?.name ||
    selectedRecipe?.name ||
    (
      {
        browse: 'Выберите продукт',
        'food-editor': editingFood ? 'Изменить продукт' : 'Новый продукт',
        recipes: 'Рецепты',
        barcode: 'Штрихкод',
      } as const
    )[view];
  const quantityMode = Boolean(draft.food || selectedRecipe);

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
            <h2 id="nutrition-picker-title">{title}</h2>
          </div>
          <Button variant="ghost" type="button" aria-label="Закрыть добавление" onClick={onClose}>
            <CloseIcon />
          </Button>
        </header>
        {quantityMode ? (
          <form
            className="nutrition-picker__quantity"
            onSubmit={(event) => {
              event.preventDefault();
              if (!addEntry.isPending) addEntry.mutate();
            }}
          >
            <button
              className="nutrition-picker__back"
              type="button"
              onClick={() => {
                addEntry.reset();
                setSelectedRecipe(null);
                setDraft({ ...draft, food: null });
              }}
            >
              ← Выбрать другое
            </button>
            {draft.food ? (
              <>
                <div className="nutrition-picker__selected">
                  <span>{draft.food.brand || foodSourceLabel(draft.food)}</span>
                  <strong>{formatNumber(draft.food.energy_kcal_per_100g)} ккал / 100 г</strong>
                  <small>
                    Б {formatNumber(draft.food.protein_g_per_100g)} · Ж{' '}
                    {formatNumber(draft.food.fat_g_per_100g)} · У{' '}
                    {formatNumber(draft.food.carbs_g_per_100g)}
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
                      {draft.food.standard_serving_weight_g && (
                        <option value="serving">порции</option>
                      )}
                    </Select>
                  </Field>
                </div>
                {draft.amountUnit === 'serving' && draft.food.standard_serving_weight_g && (
                  <p className="nutrition-picker__serving-hint">
                    1 порция ≈ {formatNumber(draft.food.standard_serving_weight_g)} г
                  </p>
                )}
              </>
            ) : (
              selectedRecipe && (
                <>
                  <div className="nutrition-picker__selected">
                    <span>Рецепт · {selectedRecipe.ingredients.length} продуктов</span>
                    <strong>
                      {formatNumber(selectedRecipe.nutrients_per_100g.energy_kcal_per_100g)} ккал /
                      100 г
                    </strong>
                    <small>Итоговый вес: {formatNumber(selectedRecipe.effective_weight_g)} г</small>
                  </div>
                  <Field
                    label="Порция готового блюда, г"
                    labelFor="nutrition-recipe-amount"
                    hint="Можно указать любую фактическую массу"
                  >
                    <Input
                      id="nutrition-recipe-amount"
                      type="number"
                      inputMode="decimal"
                      min="0.001"
                      step="any"
                      required
                      value={recipeAmount}
                      onChange={(event) => setRecipeAmount(event.target.value)}
                    />
                  </Field>
                </>
              )
            )}
            {addEntry.error && (
              <div className="nutrition-inline-error" role="alert">
                <span>{(addEntry.error as Error).message}</span>
                <button
                  type="button"
                  disabled={addEntry.isPending}
                  onClick={() => addEntry.mutate()}
                >
                  Повторить
                </button>
              </div>
            )}
            <Button fullWidth disabled={addEntry.isPending} type="submit">
              {addEntry.isPending ? 'Добавляем…' : 'Добавить в дневник'}
            </Button>
          </form>
        ) : view === 'food-editor' ? (
          <div className="nutrition-picker__browse">
            <FoodEditor
              barcode={editorBarcode}
              food={editingFood}
              onCancel={() => setView('browse')}
              onSaved={(food) => {
                toast(editingFood ? 'Продукт обновлён' : 'Продукт создан');
                setEditingFood(undefined);
                setEditorBarcode('');
                selectFood(food);
              }}
            />
          </div>
        ) : view === 'recipes' ? (
          <div className="nutrition-picker__browse">
            <button
              className="nutrition-picker__back"
              type="button"
              onClick={() => setView('browse')}
            >
              ← К продуктам
            </button>
            <RecipeBrowser onSelect={selectRecipe} />
          </div>
        ) : view === 'barcode' ? (
          <div className="nutrition-picker__browse">
            <button
              className="nutrition-picker__back"
              type="button"
              onClick={() => setView('browse')}
            >
              ← К продуктам
            </button>
            <BarcodeLookup
              onSelect={selectFood}
              onCreate={(barcode) => {
                setEditorBarcode(barcode);
                setEditingFood(undefined);
                setView('food-editor');
              }}
            />
          </div>
        ) : (
          <div className="nutrition-picker__browse">
            <div className="nutrition-picker__tools" aria-label="Способы добавления">
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setEditingFood(undefined);
                  setEditorBarcode('');
                  setView('food-editor');
                }}
              >
                ＋ Свой продукт
              </Button>
              <Button type="button" variant="secondary" onClick={() => setView('recipes')}>
                Рецепты
              </Button>
              <Button type="button" variant="secondary" onClick={() => setView('barcode')}>
                Штрихкод
              </Button>
            </div>
            <Field
              label="Поиск по названию или бренду"
              labelFor="nutrition-food-search"
              hint="Локальный поиск начинается после двух символов"
            >
              <Input
                id="nutrition-food-search"
                type="search"
                value={searchInput}
                onChange={(event) => {
                  setSearchInput(event.target.value);
                  setExternalQuery('');
                }}
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
                message="Локальный каталог сейчас не ответил. Попробуйте снова."
                retry={() =>
                  void (searchQuery.length >= 2 ? search.refetch() : activeCollection.refetch())
                }
              />
            )}
            {!activeLoading && !activeError && (
              <FoodResults
                foods={shownFoods}
                onSelect={selectFood}
                onFavorite={(food) => favorite.mutate(food)}
                pendingFavorite={favorite.isPending ? (favorite.variables?.id ?? null) : null}
                onEdit={(food) => {
                  setEditingFood(food);
                  setEditorBarcode('');
                  setView('food-editor');
                }}
              />
            )}
            {favorite.error && (
              <p className="nutrition-form-error" role="alert">
                Не удалось обновить избранное.
              </p>
            )}
            {searchQuery.length >= 2 &&
              !activeLoading &&
              !activeError &&
              shownFoods.length === 0 &&
              externalQuery !== searchQuery && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setExternalQuery(searchQuery)}
                >
                  Искать во внешнем каталоге
                </Button>
              )}
            {external.isFetching && <LoadingState label="Проверяем внешний каталог…" />}
            {external.error && (
              <div className="nutrition-provider-fallback" role="status">
                <strong>Внешний каталог временно недоступен</strong>
                <span>Можно использовать локальный поиск или создать свой продукт.</span>
              </div>
            )}
            {external.data && externalQuery === searchQuery && (
              <ExternalResults response={external.data} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
