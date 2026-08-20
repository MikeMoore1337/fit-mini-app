import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import { addCalendarDays, dateInputValue } from '../../shared/dateTime';
import { invalidateNutritionSummaries, queryKeys } from '../../shared/queryKeys';
import type {
  FoodDiaryDay,
  FoodDiaryEntry,
  FoodDiaryMeal,
  FoodDiaryNutrition,
} from '../../shared/api/types';
import {
  Badge,
  Button,
  ErrorState,
  Field,
  Input,
  LoadingState,
  Select,
} from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { FoodPickerDialog, type MealType } from './FoodPickerDialog';
import { CopyDiaryDialog, type CopySubject } from './CopyDiaryDialog';

const mealOrder: MealType[] = ['breakfast', 'lunch', 'dinner', 'snacks'];
const mealLabels: Record<MealType, string> = {
  breakfast: 'Завтрак',
  lunch: 'Обед',
  dinner: 'Ужин',
  snacks: 'Перекусы',
};

const emptyNutrition: FoodDiaryNutrition = {
  energy_kcal: '0',
  protein_g: '0',
  fat_g: '0',
  carbs_g: '0',
  fiber_g: null,
};

function formatNumber(value: string | number, maximumFractionDigits = 0): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits }).format(number);
}

function formatDate(value: string, today: string): { title: string; subtitle: string } {
  const date = new Date(`${value}T12:00:00`);
  const formatted = new Intl.DateTimeFormat('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(date);
  const weekday = formatted.charAt(0).toUpperCase() + formatted.slice(1);
  if (value === today) return { title: 'Сегодня', subtitle: weekday };
  if (value === addCalendarDays(today, -1)) return { title: 'Вчера', subtitle: weekday };
  return { title: weekday, subtitle: String(date.getFullYear()) };
}

function amountLabel(entry: FoodDiaryEntry): string {
  if (entry.amount_unit === 'serving') {
    return `${formatNumber(entry.amount, 2)} ${Number(entry.amount) === 1 ? 'порция' : 'порции'} · ${formatNumber(entry.weight_g)} г`;
  }
  return `${formatNumber(entry.weight_g, 1)} г`;
}

function targetStatus(remaining: number, target: number, unit: string): string {
  if (remaining >= 0) return `Осталось ${formatNumber(remaining)} ${unit}`;
  const over = Math.abs(remaining);
  if (target > 0 && over / target <= 0.05)
    return `Немного выше ориентира: ${formatNumber(over)} ${unit}`;
  return `Выше ориентира на ${formatNumber(over)} ${unit}`;
}

function MacroProgress({
  label,
  total,
  target,
  remaining,
  unit,
}: {
  label: string;
  total: string;
  target: string;
  remaining: string;
  unit: 'г' | 'ккал';
}) {
  const totalNumber = Number(total);
  const targetNumber = Number(target);
  const remainingNumber = Number(remaining);
  const ratio = targetNumber > 0 ? totalNumber / targetNumber : 0;
  const meaningfullyOver = ratio > 1.1;
  return (
    <div className={`nutrition-target${meaningfullyOver ? ' is-over' : ''}`}>
      <div className="nutrition-target__heading">
        <span>{label}</span>
        <strong>
          {formatNumber(totalNumber)}{' '}
          <small>
            / {formatNumber(targetNumber)} {unit}
          </small>
        </strong>
      </div>
      <div
        className="nutrition-target__track"
        role="progressbar"
        aria-label={`${label}: ${formatNumber(totalNumber)} из ${formatNumber(targetNumber)} ${unit}`}
        aria-valuemin={0}
        aria-valuemax={Math.max(targetNumber, 1)}
        aria-valuenow={Math.min(Math.max(totalNumber, 0), Math.max(targetNumber, 1))}
      >
        <span style={{ width: `${Math.min(Math.max(ratio * 100, 0), 100)}%` }} />
      </div>
      <small>{targetStatus(remainingNumber, targetNumber, unit)}</small>
    </div>
  );
}

function DaySummary({ day }: { day: FoodDiaryDay }) {
  const { totals, targets, remaining } = day;
  return (
    <aside className="nutrition-day-summary" aria-labelledby="nutrition-summary-title">
      <div className="nutrition-day-summary__head">
        <span className="eyebrow">Баланс дня</span>
        <h2 id="nutrition-summary-title">Итоги и цель</h2>
      </div>
      {targets && remaining ? (
        <div className="nutrition-targets">
          <MacroProgress
            label="Калории"
            total={totals.energy_kcal}
            target={targets.energy_kcal}
            remaining={remaining.energy_kcal}
            unit="ккал"
          />
          <div className="nutrition-targets__macros">
            <MacroProgress
              label="Белки"
              total={totals.protein_g}
              target={targets.protein_g}
              remaining={remaining.protein_g}
              unit="г"
            />
            <MacroProgress
              label="Жиры"
              total={totals.fat_g}
              target={targets.fat_g}
              remaining={remaining.fat_g}
              unit="г"
            />
            <MacroProgress
              label="Углеводы"
              total={totals.carbs_g}
              target={targets.carbs_g}
              remaining={remaining.carbs_g}
              unit="г"
            />
          </div>
        </div>
      ) : (
        <div className="nutrition-targets nutrition-targets--unset">
          <strong>{formatNumber(totals.energy_kcal)} ккал записано</strong>
          <p>Настройте ориентиры КБЖУ, чтобы видеть остаток на день.</p>
          <a href="#nutrition-target-settings">Настроить цель</a>
        </div>
      )}
      <dl className="nutrition-day-summary__totals" aria-label="Сумма макронутриентов">
        <div>
          <dt>Белки</dt>
          <dd>{formatNumber(totals.protein_g, 1)} г</dd>
        </div>
        <div>
          <dt>Жиры</dt>
          <dd>{formatNumber(totals.fat_g, 1)} г</dd>
        </div>
        <div>
          <dt>Углеводы</dt>
          <dd>{formatNumber(totals.carbs_g, 1)} г</dd>
        </div>
      </dl>
    </aside>
  );
}

function EntryRow({ entry, onCopy }: { entry: FoodDiaryEntry; onCopy: () => void }) {
  const queryClient = useQueryClient();
  const { confirm, toast } = useFeedback();
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState(entry.amount);
  const [amountUnit, setAmountUnit] = useState<'g' | 'serving'>(entry.amount_unit);

  const update = useMutation({
    mutationFn: () =>
      api<FoodDiaryEntry>(`/api/v1/nutrition/diary/entries/${entry.id}`, {
        method: 'PATCH',
        body: { amount: Number(amount.replace(',', '.')), amount_unit: amountUnit },
      }),
    onSuccess: async () => {
      await invalidateNutritionSummaries(queryClient);
      setEditing(false);
      toast('Количество обновлено');
    },
  });
  const remove = useMutation({
    mutationFn: () =>
      api<void>(`/api/v1/nutrition/diary/entries/${entry.id}`, { method: 'DELETE' }),
    onSuccess: async () => {
      await invalidateNutritionSummaries(queryClient);
      toast('Запись удалена');
    },
  });

  const requestDelete = async () => {
    const approved = await confirm({
      title: 'Удалить запись?',
      message: `${entry.food_name} исчезнет из этого приёма пищи.`,
      confirmText: 'Удалить',
    });
    if (approved) remove.mutate();
  };

  return (
    <li className="nutrition-entry">
      <div className="nutrition-entry__content">
        <div className="nutrition-entry__title">
          <div>
            <strong>{entry.food_name}</strong>
            <span>{entry.food_brand || amountLabel(entry)}</span>
          </div>
          <strong className="nutrition-entry__calories">
            {formatNumber(entry.nutrition.energy_kcal)} ккал
          </strong>
        </div>
        {entry.food_brand && <span className="nutrition-entry__amount">{amountLabel(entry)}</span>}
        <div className="nutrition-entry__macros" aria-label="Пищевая ценность записи">
          <span>Б {formatNumber(entry.nutrition.protein_g, 1)}</span>
          <span>Ж {formatNumber(entry.nutrition.fat_g, 1)}</span>
          <span>У {formatNumber(entry.nutrition.carbs_g, 1)}</span>
        </div>
      </div>
      {!editing ? (
        <div className="nutrition-entry__actions">
          <button type="button" onClick={onCopy} disabled={remove.isPending}>
            Повторить
          </button>
          <button type="button" onClick={() => setEditing(true)} disabled={remove.isPending}>
            Изменить
          </button>
          <button type="button" onClick={() => void requestDelete()} disabled={remove.isPending}>
            {remove.isPending ? 'Удаляем…' : 'Удалить'}
          </button>
        </div>
      ) : (
        <form
          className="nutrition-entry-editor"
          onSubmit={(event) => {
            event.preventDefault();
            update.mutate();
          }}
        >
          <Field label="Количество" labelFor={`nutrition-entry-amount-${entry.id}`}>
            <Input
              id={`nutrition-entry-amount-${entry.id}`}
              type="number"
              inputMode="decimal"
              min="0.001"
              step="any"
              required
              value={amount}
              onChange={(event) => {
                update.reset();
                setAmount(event.target.value);
              }}
            />
          </Field>
          <Field label="Единица" labelFor={`nutrition-entry-unit-${entry.id}`}>
            <Select
              id={`nutrition-entry-unit-${entry.id}`}
              value={amountUnit}
              onChange={(event) => {
                update.reset();
                setAmountUnit(event.target.value as 'g' | 'serving');
              }}
            >
              <option value="g">граммы</option>
              {entry.serving_weight_g && <option value="serving">порции</option>}
            </Select>
          </Field>
          <div className="nutrition-entry-editor__actions">
            <Button disabled={update.isPending} type="submit">
              {update.isPending ? 'Сохраняем…' : 'Сохранить'}
            </Button>
            <Button
              disabled={update.isPending}
              type="button"
              variant="ghost"
              onClick={() => {
                update.reset();
                setAmount(entry.amount);
                setAmountUnit(entry.amount_unit);
                setEditing(false);
              }}
            >
              Отмена
            </Button>
          </div>
          {update.error && (
            <div className="nutrition-inline-error" role="alert">
              <span>{(update.error as Error).message}</span>
              <button type="button" onClick={() => update.mutate()}>
                Повторить
              </button>
            </div>
          )}
        </form>
      )}
      {remove.error && (
        <div className="nutrition-inline-error nutrition-entry__delete-error" role="alert">
          <span>{(remove.error as Error).message}</span>
          <button type="button" onClick={() => void requestDelete()}>
            Повторить
          </button>
        </div>
      )}
    </li>
  );
}

function MealSection({
  meal,
  onAdd,
  onCopy,
  onCopyEntry,
}: {
  meal: FoodDiaryMeal;
  onAdd: () => void;
  onCopy: () => void;
  onCopyEntry: (entry: FoodDiaryEntry) => void;
}) {
  return (
    <section className="nutrition-meal" aria-labelledby={`nutrition-meal-${meal.meal_type}`}>
      <header className="nutrition-meal__header">
        <div>
          <h2 id={`nutrition-meal-${meal.meal_type}`}>{mealLabels[meal.meal_type as MealType]}</h2>
          <span>
            {meal.entries.length
              ? `${formatNumber(meal.totals.energy_kcal)} ккал`
              : 'Пока без записей'}
          </span>
        </div>
        <div className="nutrition-meal__actions">
          {meal.entries.length > 0 && (
            <button type="button" onClick={onCopy}>
              Копировать
            </button>
          )}
          <Button variant="secondary" type="button" onClick={onAdd}>
            <span aria-hidden="true">＋</span> Добавить
          </Button>
        </div>
      </header>
      {meal.entries.length ? (
        <ul className="nutrition-entry-list">
          {meal.entries.map((entry) => (
            <EntryRow entry={entry} key={entry.id} onCopy={() => onCopyEntry(entry)} />
          ))}
        </ul>
      ) : (
        <p className="nutrition-meal__empty">Добавьте продукт — недавние будут под рукой.</p>
      )}
    </section>
  );
}

function normalizeMeals(meals: FoodDiaryMeal[]): FoodDiaryMeal[] {
  return mealOrder.map(
    (mealType) =>
      meals.find((meal) => meal.meal_type === mealType) ?? {
        meal_type: mealType,
        entries: [],
        totals: emptyNutrition,
      },
  );
}

export function NutritionDiary({
  timeZone,
  initialDate,
}: {
  timeZone?: string | null;
  initialDate?: string;
}) {
  const today = dateInputValue(new Date(), timeZone || undefined);
  const [selectedDate, setSelectedDate] = useState(initialDate || today);
  const [addingTo, setAddingTo] = useState<MealType | null>(null);
  const [copySubject, setCopySubject] = useState<CopySubject | null>(null);
  const diary = useQuery({
    queryKey: queryKeys.nutrition.diaryDate(selectedDate),
    queryFn: () => api<FoodDiaryDay>(`/api/v1/nutrition/diary?diary_date=${selectedDate}`),
  });
  const dateLabel = formatDate(selectedDate, today);
  const meals = useMemo(() => normalizeMeals(diary.data?.meals ?? []), [diary.data?.meals]);

  return (
    <div className="nutrition-diary nutrition-diary--design-v2">
      <header className="nutrition-diary__intro">
        <div>
          <span className="eyebrow">Ежедневный дневник</span>
          <h1>Питание</h1>
          <p>{dateLabel.subtitle}</p>
        </div>
        <Button
          className="nutrition-diary__primary-action"
          type="button"
          aria-label="Добавить продукт в завтрак"
          onClick={() => setAddingTo('breakfast')}
        >
          <span aria-hidden="true">＋</span> Добавить продукт
        </Button>
      </header>

      <nav className="nutrition-date-nav" aria-label="Дата дневника">
        <Button
          variant="ghost"
          type="button"
          aria-label="Предыдущий день"
          onClick={() => setSelectedDate(addCalendarDays(selectedDate, -1))}
        >
          ←
        </Button>
        <label className="nutrition-date-nav__current">
          <span>{dateLabel.title}</span>
          <small>{dateLabel.subtitle}</small>
          <input
            type="date"
            aria-label="Выбрать дату"
            max={today}
            value={selectedDate}
            onChange={(event) => event.target.value && setSelectedDate(event.target.value)}
          />
        </label>
        <Button
          variant="ghost"
          type="button"
          aria-label="Следующий день"
          disabled={selectedDate >= today}
          onClick={() => setSelectedDate(addCalendarDays(selectedDate, 1))}
        >
          →
        </Button>
        {selectedDate !== today && (
          <button
            className="nutrition-date-nav__today"
            type="button"
            onClick={() => setSelectedDate(today)}
          >
            К сегодня
          </button>
        )}
      </nav>

      {diary.data && diary.data.meals.some((meal) => meal.entries.length > 0) && (
        <div className="nutrition-day-actions">
          <button
            type="button"
            onClick={() =>
              setCopySubject({
                scope: 'day',
                sourceDate: selectedDate,
                label: `Все записи за ${dateLabel.title.toLowerCase()}`,
              })
            }
          >
            Скопировать день
          </button>
        </div>
      )}

      <div className="nutrition-diary__status" aria-live="polite">
        {diary.data?.targets ? (
          <Badge tone="success">Цель КБЖУ настроена</Badge>
        ) : diary.data ? (
          <Badge>Без цели</Badge>
        ) : null}
      </div>

      {diary.isLoading && <LoadingState label="Загружаем дневник…" />}
      {diary.error && (
        <ErrorState message={(diary.error as Error).message} retry={() => void diary.refetch()} />
      )}
      {diary.data && (
        <div className="nutrition-diary__layout">
          <div className="nutrition-meals">
            {meals.map((meal) => (
              <MealSection
                key={meal.meal_type}
                meal={meal}
                onAdd={() => setAddingTo(meal.meal_type as MealType)}
                onCopy={() =>
                  setCopySubject({
                    scope: 'meal',
                    sourceDate: selectedDate,
                    sourceMeal: meal.meal_type as MealType,
                    label: `${mealLabels[meal.meal_type as MealType]} — ${meal.entries.length} записей`,
                  })
                }
                onCopyEntry={(entry) =>
                  setCopySubject({
                    scope: 'product',
                    sourceDate: selectedDate,
                    sourceMeal: meal.meal_type as MealType,
                    entryId: entry.id,
                    label: entry.food_name,
                  })
                }
              />
            ))}
          </div>
          <DaySummary day={diary.data} />
        </div>
      )}

      {addingTo && (
        <FoodPickerDialog
          diaryDate={selectedDate}
          mealType={addingTo}
          onClose={() => setAddingTo(null)}
        />
      )}
      {copySubject && (
        <CopyDiaryDialog subject={copySubject} today={today} onClose={() => setCopySubject(null)} />
      )}
    </div>
  );
}
