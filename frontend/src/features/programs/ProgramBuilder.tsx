import { useId, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { Exercise, ProgramTemplateCreate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card, LoadingState } from '../../shared/ui/common';
import { difficultyLabels, orderExercisesForLevel } from './exerciseOrdering';
import { buildStrengthPreset, resolveStrengthRule, type StrengthSplit } from './strengthPresets';

type Day = ProgramTemplateCreate['days'][number];
const blankExercise = (): Day['exercises'][number] => ({
  exercise_id: 0,
  prescribed_sets: 3,
  prescribed_reps: '8-12',
  rest_seconds: 90,
  notes: '',
});
const blankDay = (index: number): Day => ({ title: `День ${index}`, exercises: [blankExercise()] });

function ExercisePicker({
  exercises,
  level,
  value,
  onChange,
}: {
  exercises: Exercise[];
  level: ProgramTemplateCreate['level'];
  value: number;
  onChange: (id: number) => void;
}) {
  const selected = exercises.find((exercise) => exercise.id === value);
  const resultsId = useId();
  const [query, setQuery] = useState(selected?.title ?? '');
  const [open, setOpen] = useState(false);
  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return orderExercisesForLevel(
      exercises.filter(
        (exercise) =>
          !normalized ||
          `${exercise.title} ${exercise.primary_muscle || ''} ${exercise.equipment || ''}`
            .toLowerCase()
            .includes(normalized),
      ),
      level,
    );
  }, [exercises, level, query]);

  return (
    <div className="exercise-picker">
      <input
        type="search"
        role="combobox"
        aria-label="Поиск упражнения"
        aria-expanded={open}
        aria-controls={resultsId}
        autoComplete="off"
        value={query}
        placeholder="Начните вводить название"
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          if (value) onChange(0);
        }}
      />
      {open && (
        <div className="exercise-picker__results" id={resultsId} role="listbox">
          {results.length ? (
            results.map((exercise) => (
              <button
                type="button"
                role="option"
                aria-selected={exercise.id === value}
                className="exercise-picker__option"
                key={exercise.id}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onChange(exercise.id);
                  setQuery(exercise.title);
                  setOpen(false);
                }}
              >
                <strong>{exercise.title}</strong>
                <span className="exercise-picker__meta">
                  <small>
                    {exercise.primary_muscle || 'Все мышцы'} ·{' '}
                    {exercise.equipment || 'Без оборудования'}
                  </small>
                  <span className="badge">{difficultyLabels[exercise.difficulty_level]}</span>
                </span>
              </button>
            ))
          ) : (
            <span className="exercise-picker__empty">Ничего не найдено</span>
          )}
        </div>
      )}
    </div>
  );
}

export function ProgramBuilder({
  targetTelegramId,
  targetName,
}: {
  targetTelegramId?: number | null;
  targetName?: string | null;
}) {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('Персональная программа');
  const [goal, setGoal] = useState<ProgramTemplateCreate['goal']>('maintenance');
  const [level, setLevel] = useState<ProgramTemplateCreate['level']>('beginner');
  const [days, setDays] = useState<Day[]>([blankDay(1)]);
  const [split, setSplit] = useState<StrengthSplit>('upper_lower');
  const exercises = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api<Exercise[]>('/api/v1/programs/exercises'),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api('/api/v1/programs/templates', {
        method: 'POST',
        body: {
          title,
          goal,
          level,
          mode: targetTelegramId ? 'coach' : 'self',
          target_telegram_user_id: targetTelegramId || null,
          target_full_name: targetName || null,
          assign_after_create: true,
          days: days.map((day) => ({
            ...day,
            exercises: day.exercises.filter((item) => item.exercise_id > 0),
          })),
        } satisfies ProgramTemplateCreate,
      }),
    onSuccess: async () => {
      toast(targetTelegramId ? 'Программа создана и назначена' : 'Программа создана');
      await queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  const updateDay = (index: number, next: Day) =>
    setDays(days.map((day, dayIndex) => (dayIndex === index ? next : day)));
  const rule = resolveStrengthRule(level, split);
  const [presetDays, setPresetDays] = useState<number>(rule.recommended);
  const loadPreset = () => {
    const nextRule = resolveStrengthRule(level, split);
    const normalizedDays = Math.min(nextRule.max, Math.max(nextRule.min, presetDays));
    setPresetDays(normalizedDays);
    setDays(buildStrengthPreset(exercises.data ?? [], level, split, normalizedDays));
    setTitle(
      `${{ fullbody: 'Фуллбади', upper_lower: 'Верх/Низ', push_pull_legs: 'Тяни/Толкай/Ноги', split: 'Сплит' }[split]} · ${normalizedDays} дн.`,
    );
    if (nextRule.warning) toast(nextRule.warning, 'error');
    else toast('Силовой шаблон загружен');
  };
  return (
    <Card
      title="Конструктор программы"
      description={
        targetTelegramId
          ? `Назначение для ${targetName || targetTelegramId}`
          : 'Создайте программу для себя.'
      }
    >
      {exercises.isLoading ? (
        <LoadingState />
      ) : (
        <form
          className="stack top-gap"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <div className="form-grid">
            <label className="field">
              <span>Название</span>
              <input
                value={title}
                maxLength={128}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Цель</span>
              <select
                value={goal}
                onChange={(e) => setGoal(e.target.value as ProgramTemplateCreate['goal'])}
              >
                <option value="fat_loss">Похудение</option>
                <option value="muscle_gain">Набор</option>
                <option value="maintenance">Поддержание</option>
                <option value="recomposition">Рекомпозиция</option>
              </select>
            </label>
            <label className="field">
              <span>Уровень</span>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value as ProgramTemplateCreate['level'])}
              >
                <option value="beginner">Начальный</option>
                <option value="intermediate">Средний</option>
                <option value="advanced">Продвинутый</option>
              </select>
            </label>
          </div>
          <div className="auth-notice stack">
            <strong>Быстрый силовой шаблон</strong>
            <div className="form-grid">
              <label className="field">
                <span>Схема</span>
                <select
                  value={split}
                  onChange={(e) => {
                    const next = e.target.value as StrengthSplit;
                    setSplit(next);
                    setPresetDays(resolveStrengthRule(level, next).recommended);
                  }}
                >
                  <option value="fullbody">Фуллбади</option>
                  <option value="upper_lower">Верх/Низ</option>
                  <option value="push_pull_legs">Тяни/Толкай/Ноги</option>
                  <option value="split">Сплит</option>
                </select>
              </label>
              <label className="field">
                <span>
                  Дней ({rule.min}–{rule.max})
                </span>
                <input
                  type="number"
                  min={rule.min}
                  max={rule.max}
                  value={presetDays}
                  onChange={(e) => setPresetDays(Number(e.target.value))}
                />
              </label>
            </div>
            {rule.warning && <p className="muted">{rule.warning}</p>}
            <button type="button" className="secondary" onClick={loadPreset}>
              Заполнить по шаблону
            </button>
          </div>
          {days.map((day, dayIndex) => (
            <div className="program-day stack" key={dayIndex}>
              <div className="section-head">
                <input
                  aria-label={`Название дня ${dayIndex + 1}`}
                  value={day.title}
                  onChange={(e) => updateDay(dayIndex, { ...day, title: e.target.value })}
                />
                {days.length > 1 && (
                  <button
                    type="button"
                    className="btn-danger"
                    onClick={() => setDays(days.filter((_, index) => index !== dayIndex))}
                  >
                    Удалить день
                  </button>
                )}
              </div>
              {day.exercises.map((item, exerciseIndex) => (
                <div className="program-exercise-row" key={exerciseIndex}>
                  <label className="field exercise-select">
                    <span>Упражнение</span>
                    <ExercisePicker
                      key={`${exerciseIndex}-${item.exercise_id}`}
                      exercises={exercises.data ?? []}
                      level={level}
                      value={item.exercise_id}
                      onChange={(exerciseId) =>
                        updateDay(dayIndex, {
                          ...day,
                          exercises: day.exercises.map((row, index) =>
                            index === exerciseIndex ? { ...row, exercise_id: exerciseId } : row,
                          ),
                        })
                      }
                    />
                  </label>
                  {(
                    [
                      ['prescribed_sets', 'Подходы'],
                      ['prescribed_reps', 'Повторы'],
                      ['rest_seconds', 'Отдых, сек'],
                    ] as const
                  ).map(([key, label]) => (
                    <label className="field" key={key}>
                      <span>{label}</span>
                      <input
                        type={key === 'prescribed_reps' ? 'text' : 'number'}
                        value={item[key] ?? ''}
                        onChange={(e) =>
                          updateDay(dayIndex, {
                            ...day,
                            exercises: day.exercises.map((row, index) =>
                              index === exerciseIndex
                                ? {
                                    ...row,
                                    [key]:
                                      key === 'prescribed_reps'
                                        ? e.target.value
                                        : Number(e.target.value),
                                  }
                                : row,
                            ),
                          })
                        }
                      />
                    </label>
                  ))}
                  <button
                    type="button"
                    className="secondary"
                    onClick={() =>
                      updateDay(dayIndex, {
                        ...day,
                        exercises: day.exercises.filter((_, index) => index !== exerciseIndex),
                      })
                    }
                  >
                    ×
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  updateDay(dayIndex, { ...day, exercises: [...day.exercises, blankExercise()] })
                }
              >
                Добавить упражнение
              </button>
            </div>
          ))}
          <div className="toolbar wrap">
            <button
              type="button"
              className="secondary"
              onClick={() => setDays([...days, blankDay(days.length + 1)])}
            >
              Добавить день
            </button>
            <button
              disabled={
                mutation.isPending ||
                days.some((day) => day.exercises.every((item) => !item.exercise_id))
              }
            >
              {mutation.isPending
                ? 'Сохраняем…'
                : targetTelegramId
                  ? 'Создать и назначить'
                  : 'Создать программу'}
            </button>
          </div>
        </form>
      )}
    </Card>
  );
}
