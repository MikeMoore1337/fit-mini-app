import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiError, api } from '../../shared/api/client';
import type { Food, UserFoodCreate } from '../../shared/api/types';
import { Button, Field, Input } from '../../shared/ui/common';

interface FoodEditorProps {
  barcode?: string;
  food?: Food;
  onCancel: () => void;
  onSaved: (food: Food) => void;
}

interface FoodDraft {
  name: string;
  brand: string;
  barcode: string;
  energy: string;
  protein: string;
  fat: string;
  carbs: string;
  fiber: string;
  servingWeight: string;
}

type FoodErrors = Partial<Record<keyof FoodDraft, string>>;

function initialDraft(food?: Food, barcode = ''): FoodDraft {
  return {
    name: food?.name ?? '',
    brand: food?.brand ?? '',
    barcode: food?.barcode ?? barcode,
    energy: food?.energy_kcal_per_100g ?? '',
    protein: food?.protein_g_per_100g ?? '',
    fat: food?.fat_g_per_100g ?? '',
    carbs: food?.carbs_g_per_100g ?? '',
    fiber: food?.fiber_g_per_100g ?? '',
    servingWeight: food?.standard_serving_weight_g ?? '',
  };
}

export function isValidGtin(value: string): boolean {
  if (![8, 12, 13, 14].includes(value.length) || !/^\d+$/.test(value)) return false;
  const digits = [...value].map(Number);
  const payload = digits.slice(0, -1);
  const sum = payload.reduce(
    (total, digit, index) => total + digit * ((payload.length - index) % 2 === 1 ? 3 : 1),
    0,
  );
  return (10 - (sum % 10)) % 10 === digits.at(-1);
}

function parseRequiredNumber(
  value: string,
  label: string,
  maximum: number,
): { value?: number; error?: string } {
  const parsed = Number(value.replace(',', '.'));
  if (!value.trim() || !Number.isFinite(parsed)) return { error: `Укажите ${label.toLowerCase()}` };
  if (parsed < 0 || parsed > maximum) return { error: `Допустимо от 0 до ${maximum}` };
  return { value: parsed };
}

function validateFood(draft: FoodDraft): { errors: FoodErrors; payload?: UserFoodCreate } {
  const errors: FoodErrors = {};
  const name = draft.name.trim().replace(/\s+/g, ' ');
  if (!name) errors.name = 'Введите название продукта';
  else if (name.length > 256) errors.name = 'Не больше 256 символов';
  if (draft.brand.trim().length > 128) errors.brand = 'Не больше 128 символов';
  const barcode = draft.barcode.replace(/\s+/g, '');
  if (barcode && !isValidGtin(barcode))
    errors.barcode = 'Проверьте цифры штрихкода GTIN-8, UPC-A, EAN-13 или GTIN-14';

  const energy = parseRequiredNumber(draft.energy, 'калорийность', 1000);
  const protein = parseRequiredNumber(draft.protein, 'белки', 100);
  const fat = parseRequiredNumber(draft.fat, 'жиры', 100);
  const carbs = parseRequiredNumber(draft.carbs, 'углеводы', 100);
  if (energy.error) errors.energy = energy.error;
  if (protein.error) errors.protein = protein.error;
  if (fat.error) errors.fat = fat.error;
  if (carbs.error) errors.carbs = carbs.error;

  let fiber: number | null = null;
  if (draft.fiber.trim()) {
    const parsedFiber = parseRequiredNumber(draft.fiber, 'клетчатку', 100);
    if (parsedFiber.error) errors.fiber = parsedFiber.error;
    else fiber = parsedFiber.value ?? null;
  }
  let servingWeight: number | null = null;
  if (draft.servingWeight.trim()) {
    servingWeight = Number(draft.servingWeight.replace(',', '.'));
    if (!Number.isFinite(servingWeight) || servingWeight <= 0)
      errors.servingWeight = 'Вес порции должен быть больше нуля';
  }
  if (Object.keys(errors).length) return { errors };
  return {
    errors,
    payload: {
      name,
      brand: draft.brand.trim().replace(/\s+/g, ' ') || null,
      barcode: barcode || null,
      energy_kcal_per_100g: energy.value!,
      protein_g_per_100g: protein.value!,
      fat_g_per_100g: fat.value!,
      carbs_g_per_100g: carbs.value!,
      fiber_g_per_100g: fiber,
      standard_serving_amount: servingWeight ? 1 : null,
      standard_serving_unit: servingWeight ? 'serving' : null,
      standard_serving_weight_g: servingWeight,
    },
  };
}

function saveError(error: unknown): string {
  if (error instanceof ApiError && error.status === 409)
    return 'Свой продукт с таким штрихкодом уже существует.';
  return 'Не удалось сохранить продукт. Проверьте данные и попробуйте снова.';
}

export function FoodEditor({ barcode = '', food, onCancel, onSaved }: FoodEditorProps) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState(() => initialDraft(food, barcode));
  const [errors, setErrors] = useState<FoodErrors>({});
  const title = food ? 'Изменить свой продукт' : 'Новый продукт';
  const mutation = useMutation({
    mutationFn: (payload: UserFoodCreate) =>
      api<Food>(food ? `/api/v1/nutrition/foods/${food.id}` : '/api/v1/nutrition/foods', {
        method: food ? 'PATCH' : 'POST',
        body: payload,
      }),
    onSuccess: async (saved) => {
      await queryClient.invalidateQueries({ queryKey: ['nutrition', 'foods'] });
      onSaved(saved);
    },
  });
  const field = (key: keyof FoodDraft, value: string) => {
    mutation.reset();
    setErrors((current) => ({ ...current, [key]: undefined }));
    setDraft((current) => ({ ...current, [key]: value }));
  };
  const macroFields = useMemo(
    () =>
      [
        ['energy', 'Калории', '0–1000 ккал'],
        ['protein', 'Белки', '0–100 г'],
        ['fat', 'Жиры', '0–100 г'],
        ['carbs', 'Углеводы', '0–100 г'],
      ] as const,
    [],
  );

  return (
    <form
      className="nutrition-editor"
      aria-label={title}
      onSubmit={(event) => {
        event.preventDefault();
        const result = validateFood(draft);
        setErrors(result.errors);
        if (result.payload) mutation.mutate(result.payload);
      }}
    >
      <div className="nutrition-editor__intro">
        <h3>{title}</h3>
        <p>Значения указываются на 100 г. Обязательные поля отмечены звёздочкой.</p>
      </div>
      <div className="nutrition-editor__grid">
        <Field label="Название *" labelFor="own-food-name" error={errors.name}>
          <Input
            id="own-food-name"
            autoFocus
            maxLength={256}
            value={draft.name}
            onChange={(event) => field('name', event.target.value)}
          />
        </Field>
        <Field label="Бренд" labelFor="own-food-brand" error={errors.brand}>
          <Input
            id="own-food-brand"
            maxLength={128}
            value={draft.brand}
            onChange={(event) => field('brand', event.target.value)}
          />
        </Field>
        {macroFields.map(([key, label, hint]) => (
          <Field
            key={key}
            label={`${label} *`}
            labelFor={`own-food-${key}`}
            hint={hint}
            error={errors[key]}
          >
            <Input
              id={`own-food-${key}`}
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              value={draft[key]}
              onChange={(event) => field(key, event.target.value)}
            />
          </Field>
        ))}
        <Field
          label="Клетчатка"
          labelFor="own-food-fiber"
          hint="необязательно, г"
          error={errors.fiber}
        >
          <Input
            id="own-food-fiber"
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            value={draft.fiber}
            onChange={(event) => field('fiber', event.target.value)}
          />
        </Field>
        <Field
          label="Вес одной порции"
          labelFor="own-food-serving"
          hint="необязательно, г"
          error={errors.servingWeight}
        >
          <Input
            id="own-food-serving"
            type="number"
            inputMode="decimal"
            min="0.001"
            step="any"
            value={draft.servingWeight}
            onChange={(event) => field('servingWeight', event.target.value)}
          />
        </Field>
        <Field
          label="Штрихкод"
          labelFor="own-food-barcode"
          hint="необязательно"
          error={errors.barcode}
        >
          <Input
            id="own-food-barcode"
            inputMode="numeric"
            maxLength={14}
            value={draft.barcode}
            onChange={(event) => field('barcode', event.target.value.replace(/\D/g, ''))}
          />
        </Field>
      </div>
      {mutation.error && (
        <p className="nutrition-form-error" role="alert">
          {saveError(mutation.error)}
        </p>
      )}
      <div className="nutrition-editor__actions">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Сохраняем…' : food ? 'Сохранить изменения' : 'Создать продукт'}
        </Button>
        <Button type="button" variant="ghost" disabled={mutation.isPending} onClick={onCancel}>
          Отмена
        </Button>
      </div>
    </form>
  );
}
