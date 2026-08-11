import { useId, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { Exercise, ProgramTemplate, ProgramTemplateCreate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card, LoadingState } from '../../shared/ui/common';
import { difficultyLabels, orderExercisesForLevel } from './exerciseOrdering';
import { buildStrengthPreset, resolveStrengthRule, type StrengthSplit } from './strengthPresets';
import { usePersistentState } from '../../shared/storage';
import { useAuth } from '../../app/AuthProvider';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { applyRestSeconds } from './programRest';
import { ExerciseGuideDialog } from '../exercises/ExerciseGuideDialog';
import { scheduleWeekdaysForSave, templateDraftTitle } from './templateEditing';
import { DateInput } from '../../shared/ui/PickerInput';

type Day = ProgramTemplateCreate['days'][number];
type ProgramTemplateAssignmentCreate = ProgramTemplateCreate & {
  start_date: string;
  duration_weeks: number;
  schedule_weekdays: number[] | null;
  replace_active: boolean;
};
const blankExercise = (restSeconds = 90): Day['exercises'][number] => ({
  exercise_id: 0,
  prescribed_sets: 3,
  prescribed_reps: '8-12',
  rest_seconds: restSeconds,
  notes: '',
});
const blankDay = (index: number): Day => ({ title: `День ${index}`, exercises: [blankExercise()] });
const weekdayLabels = [
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
  'Воскресенье',
];

function weekdayFromDate(value: string): number {
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(date.valueOf()) ? 0 : (date.getUTCDay() + 6) % 7;
}

function scheduleForDays(dayCount: number, startDate: string): number[] {
  const firstWeekday = weekdayFromDate(startDate);
  return Array.from({ length: dayCount }, (_, index) => (firstWeekday + index) % 7);
}

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
  const [activeIndex, setActiveIndex] = useState(0);
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

  const currentActiveIndex = Math.min(activeIndex, Math.max(0, results.length - 1));
  const chooseExercise = (exercise: Exercise) => {
    onChange(exercise.id);
    setQuery(exercise.title);
    setOpen(false);
  };

  return (
    <div className="exercise-picker">
      <input
        type="search"
        role="combobox"
        aria-label="Поиск упражнения"
        aria-expanded={open}
        aria-controls={resultsId}
        aria-activedescendant={
          open && results[currentActiveIndex]
            ? `${resultsId}-${results[currentActiveIndex].id}`
            : undefined
        }
        autoComplete="off"
        value={query}
        placeholder="Начните вводить название"
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onChange={(event) => {
          setQuery(event.target.value);
          setActiveIndex(0);
          setOpen(true);
          if (value) onChange(0);
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            setOpen(true);
            setActiveIndex((index) => Math.min(results.length - 1, index + 1));
          } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            setOpen(true);
            setActiveIndex((index) => Math.max(0, index - 1));
          } else if (event.key === 'Enter' && open && results[currentActiveIndex]) {
            event.preventDefault();
            chooseExercise(results[currentActiveIndex]);
          } else if (event.key === 'Escape') {
            setOpen(false);
          }
        }}
      />
      {open && (
        <div className="exercise-picker__results" id={resultsId} role="listbox">
          {results.length ? (
            results.map((exercise) => (
              <button
                type="button"
                role="option"
                id={`${resultsId}-${exercise.id}`}
                tabIndex={-1}
                aria-selected={exercise.id === value}
                className="exercise-picker__option"
                key={exercise.id}
                onMouseDown={(event) => event.preventDefault()}
                onPointerDown={(event) => event.preventDefault()}
                onClick={() => chooseExercise(exercise)}
              >
                <strong>{exercise.title}</strong>
                <span className="exercise-picker__meta">
                  <small>
                    {exercise.primary_muscle || 'Все мышцы'} ·{' '}
                    {exercise.equipment || 'Без оборудования'}
                  </small>
                  <span className="badge">{difficultyLabels[exercise.difficulty_level]}</span>
                  {exercise.is_custom && <span className="badge">Своё</span>}
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
  editingTemplate,
  saveAsCopy = false,
  onSaved,
}: {
  targetTelegramId?: number | null;
  targetName?: string | null;
  editingTemplate?: ProgramTemplate | null;
  saveAsCopy?: boolean;
  onSaved?: () => void;
}) {
  const { toast, confirm } = useFeedback();
  const { user, reloadUser } = useAuth();
  const queryClient = useQueryClient();
  const draftScope = editingTemplate
    ? `template_${saveAsCopy ? 'copy_' : ''}${editingTemplate.id}`
    : targetTelegramId
      ? `client_${targetTelegramId}`
      : `user_${user?.id ?? 'me'}`;
  const [title, setTitle, clearTitleDraft] = usePersistentState(
    `fit_program_title_${draftScope}`,
    editingTemplate ? templateDraftTitle(editingTemplate, saveAsCopy) : 'Персональная программа',
  );
  const [goal, setGoal, clearGoalDraft] = usePersistentState<ProgramTemplateCreate['goal']>(
    `fit_program_goal_${draftScope}`,
    (editingTemplate?.goal as ProgramTemplateCreate['goal'] | undefined) ?? 'maintenance',
  );
  const [level, setLevel, clearLevelDraft] = usePersistentState<ProgramTemplateCreate['level']>(
    `fit_program_level_${draftScope}`,
    (editingTemplate?.level as ProgramTemplateCreate['level'] | undefined) ?? 'beginner',
  );
  const [days, setDays, clearDaysDraft] = usePersistentState<Day[]>(
    `fit_program_days_${draftScope}`,
    editingTemplate?.days.map((day) => ({
      title: day.title,
      exercises: day.exercises.map((exercise) => ({
        exercise_id: exercise.exercise_id,
        prescribed_sets: exercise.prescribed_sets,
        prescribed_reps: exercise.prescribed_reps,
        rest_seconds: exercise.rest_seconds,
        notes: exercise.notes,
      })),
    })) ?? [blankDay(1)],
  );
  const [defaultRestSeconds, setDefaultRestSeconds, clearDefaultRestDraft] = usePersistentState(
    `fit_program_rest_${draftScope}`,
    90,
  );
  const defaultStartDate = dateInputValue(
    new Date(),
    user?.profile?.timezone || detectedTimeZone(),
  );
  const [startDate, setStartDate, clearStartDateDraft] = usePersistentState(
    `fit_program_start_${draftScope}`,
    defaultStartDate,
  );
  const [durationWeeks, setDurationWeeks, clearDurationDraft] = usePersistentState(
    `fit_program_duration_${draftScope}`,
    4,
  );
  const [scheduleWeekdays, setScheduleWeekdays, clearScheduleDraft] = usePersistentState<number[]>(
    `fit_program_weekdays_${draftScope}`,
    [],
  );
  const [split, setSplit] = useState<StrengthSplit>('upper_lower');
  const [guide, setGuide] = useState<{ id: number; title: string } | null>(null);
  const exercises = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api<Exercise[]>('/api/v1/programs/exercises'),
  });

  const effectiveScheduleWeekdays =
    scheduleWeekdays.length === days.length
      ? scheduleWeekdays
      : scheduleForDays(days.length, startDate);
  const scheduleOffsets = effectiveScheduleWeekdays.map(
    (weekday) => (weekday - (effectiveScheduleWeekdays[0] ?? weekday) + 7) % 7,
  );
  const usesSequentialCycle = days.length > 7;
  const scheduleIsValid =
    usesSequentialCycle ||
    (effectiveScheduleWeekdays.length === days.length &&
      new Set(effectiveScheduleWeekdays).size === effectiveScheduleWeekdays.length &&
      scheduleOffsets.every(
        (offset, index) => index === 0 || offset > scheduleOffsets[index - 1]!,
      ));
  const updateTemplatePath =
    editingTemplate && !saveAsCopy ? `/api/v1/programs/templates/${editingTemplate.id}` : null;

  const mutation = useMutation({
    mutationFn: ({ replaceActive }: { replaceActive: boolean }) =>
      api(updateTemplatePath ?? '/api/v1/programs/templates', {
        method: updateTemplatePath ? 'PATCH' : 'POST',
        body: {
          title,
          goal,
          level,
          mode: targetTelegramId ? 'coach' : 'self',
          target_telegram_user_id: targetTelegramId || null,
          target_full_name: targetName || null,
          assign_after_create: !editingTemplate,
          start_date: startDate,
          duration_weeks: durationWeeks,
          schedule_weekdays: scheduleWeekdaysForSave(days.length, effectiveScheduleWeekdays),
          replace_active: replaceActive,
          days: days.map((day) => ({
            ...day,
            exercises: day.exercises.filter((item) => item.exercise_id > 0),
          })),
        } satisfies ProgramTemplateAssignmentCreate,
      }),
    onSuccess: async () => {
      toast(
        saveAsCopy
          ? 'Личная копия программы создана'
          : editingTemplate
            ? 'Изменения программы сохранены'
            : targetTelegramId
              ? 'Программа создана и назначена'
              : 'Программа создана',
      );
      clearTitleDraft(
        editingTemplate
          ? templateDraftTitle(editingTemplate, saveAsCopy)
          : 'Персональная программа',
      );
      clearGoalDraft(
        (editingTemplate?.goal as ProgramTemplateCreate['goal'] | undefined) ?? 'maintenance',
      );
      clearLevelDraft(
        (editingTemplate?.level as ProgramTemplateCreate['level'] | undefined) ?? 'beginner',
      );
      clearDaysDraft([blankDay(1)]);
      clearDefaultRestDraft(90);
      clearStartDateDraft(defaultStartDate);
      clearDurationDraft(4);
      clearScheduleDraft([]);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['templates'] }),
        queryClient.invalidateQueries({ queryKey: ['workout'] }),
        queryClient.invalidateQueries({ queryKey: ['coach', 'programs'] }),
        reloadUser(),
      ]);
      onSaved?.();
    },
    onError: async (reason, variables) => {
      if (
        reason instanceof ApiError &&
        reason.status === 409 &&
        !variables.replaceActive &&
        reason.message.toLowerCase().includes('confirmation')
      ) {
        if (
          await confirm({
            title: 'Заменить активную программу?',
            message: targetTelegramId
              ? 'Текущая программа клиента будет отправлена в архив. Тренировку, которая уже идёт, заменить нельзя.'
              : 'Текущая программа будет отправлена в архив. Тренировку, которая уже идёт, заменить нельзя.',
            confirmText: 'Заменить программу',
          })
        )
          mutation.mutate({ replaceActive: true });
        return;
      }
      toast(
        reason instanceof ApiError && reason.message.toLowerCase().includes('in progress')
          ? 'Сначала завершите текущую тренировку — во время неё программу заменить нельзя.'
          : (reason as Error).message,
        'error',
      );
    },
  });

  const updateDay = (index: number, next: Day) =>
    setDays(days.map((day, dayIndex) => (dayIndex === index ? next : day)));
  const rule = resolveStrengthRule(level, split);
  const [presetDays, setPresetDays] = useState<number>(rule.recommended);
  const loadPreset = async () => {
    const hasManualWork = days.some(
      (day) =>
        day.exercises.some((exercise) => exercise.exercise_id > 0) ||
        day.title.trim() !== `День ${days.indexOf(day) + 1}`,
    );
    if (
      hasManualWork &&
      !(await confirm({
        title: 'Заменить текущий черновик?',
        message: 'Дни и упражнения из текущего черновика будут заменены силовым шаблоном.',
        confirmText: 'Заменить',
      }))
    )
      return;
    const nextRule = resolveStrengthRule(level, split);
    const normalizedDays = Math.min(nextRule.max, Math.max(nextRule.min, presetDays));
    setPresetDays(normalizedDays);
    setDays(
      applyRestSeconds(
        buildStrengthPreset(exercises.data ?? [], level, split, normalizedDays),
        defaultRestSeconds,
      ),
    );
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
        editingTemplate
          ? saveAsCopy
            ? `Настройте личную копию «${editingTemplate.title}»`
            : `Редактирование «${editingTemplate.title}»`
          : targetTelegramId
            ? `Назначение для ${targetName || targetTelegramId}`
            : 'Создайте программу для себя.'
      }
    >
      {exercises.isLoading ? (
        <LoadingState />
      ) : (
        <form
          className="stack top-gap"
          onSubmit={async (e) => {
            e.preventDefault();
            let replaceActive = false;
            if (
              !editingTemplate &&
              user?.has_active_program &&
              !(await confirm({
                title: 'Заменить активную программу?',
                message:
                  'Новая программа станет активной, а текущая будет отправлена в архив. Тренировку, которая уже идёт, заменить нельзя.',
                confirmText: 'Создать и заменить',
              }))
            )
              return;
            replaceActive = Boolean(user?.has_active_program);
            mutation.mutate({ replaceActive });
          }}
        >
          {saveAsCopy && (
            <p className="auth-notice">
              Исходный готовый шаблон останется без изменений. После сохранения появится личная
              копия, в которой можно использовать свои упражнения.
            </p>
          )}
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
          <fieldset className="auth-notice stack">
            <legend>Расписание</legend>
            <div className="form-grid">
              <label className="field">
                <span>Начать не раньше</span>
                <DateInput
                  min={defaultStartDate}
                  value={startDate}
                  onChange={(event) => {
                    setStartDate(event.target.value);
                    setScheduleWeekdays(scheduleForDays(days.length, event.target.value));
                  }}
                  required
                />
              </label>
              <label className="field">
                <span>Длительность, недель</span>
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={durationWeeks}
                  onChange={(event) => setDurationWeeks(Number(event.target.value))}
                  required
                />
              </label>
            </div>
            {usesSequentialCycle ? (
              <p className="muted">
                Восьмидневный цикл планируется последовательно и автоматически повторяется после
                восьмого дня.
              </p>
            ) : (
              <div className="form-grid">
                {days.map((day, dayIndex) => (
                  <label className="field" key={`schedule-${dayIndex}`}>
                    <span>{day.title || `День ${dayIndex + 1}`}</span>
                    <select
                      value={effectiveScheduleWeekdays[dayIndex] ?? ''}
                      onChange={(event) =>
                        setScheduleWeekdays(
                          effectiveScheduleWeekdays.map((value, index) =>
                            index === dayIndex ? Number(event.target.value) : value,
                          ),
                        )
                      }
                    >
                      {weekdayLabels.map((label, weekday) => (
                        <option value={weekday} key={label}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            )}
            {!scheduleIsValid && (
              <p className="field-error" role="alert">
                Выберите разные дни недели в порядке тренировок. После воскресенья можно продолжить
                с понедельника.
              </p>
            )}
          </fieldset>
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
            <button type="button" className="secondary" onClick={() => void loadPreset()}>
              Заполнить по шаблону
            </button>
          </div>
          <fieldset className="auth-notice stack">
            <legend>Отдых между подходами</legend>
            <p className="muted">
              Укажите общее время и примените его ко всей программе. При необходимости измените
              отдых отдельно у любого упражнения ниже.
            </p>
            <div className="toolbar wrap">
              <label className="field">
                <span>Общий отдых, сек</span>
                <input
                  type="number"
                  min="15"
                  max="600"
                  value={defaultRestSeconds}
                  onChange={(event) => setDefaultRestSeconds(Number(event.target.value))}
                  required
                />
              </label>
              <button
                type="button"
                className="secondary"
                disabled={defaultRestSeconds < 15 || defaultRestSeconds > 600}
                onClick={() => {
                  setDays(applyRestSeconds(days, defaultRestSeconds));
                  toast('Общее время отдыха применено ко всем упражнениям');
                }}
              >
                Применить ко всем упражнениям
              </button>
            </div>
          </fieldset>
          {days.map((day, dayIndex) => (
            <div className="program-day stack" key={dayIndex}>
              <div className="section-head">
                <input
                  aria-label={`Название дня ${dayIndex + 1}`}
                  value={day.title}
                  maxLength={128}
                  required
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
                    {exercises.data?.find((exercise) => exercise.id === item.exercise_id)
                      ?.has_guide && (
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          const selected = exercises.data?.find(
                            (exercise) => exercise.id === item.exercise_id,
                          );
                          if (selected) setGuide({ id: selected.id, title: selected.title });
                        }}
                      >
                        Есть техника — посмотреть
                      </button>
                    )}
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
                        min={
                          key === 'prescribed_sets' ? 1 : key === 'rest_seconds' ? 15 : undefined
                        }
                        max={
                          key === 'prescribed_sets' ? 10 : key === 'rest_seconds' ? 600 : undefined
                        }
                        maxLength={key === 'prescribed_reps' ? 32 : undefined}
                        required
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
                  <label className="field exercise-notes">
                    <span>Заметка к упражнению</span>
                    <input
                      maxLength={2000}
                      value={item.notes ?? ''}
                      placeholder="Например: контролировать темп"
                      onChange={(event) =>
                        updateDay(dayIndex, {
                          ...day,
                          exercises: day.exercises.map((row, index) =>
                            index === exerciseIndex ? { ...row, notes: event.target.value } : row,
                          ),
                        })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary"
                    aria-label={`Удалить упражнение ${exerciseIndex + 1} из дня ${dayIndex + 1}`}
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
              {day.exercises.length < 20 ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={() =>
                    updateDay(dayIndex, {
                      ...day,
                      exercises: [...day.exercises, blankExercise(defaultRestSeconds)],
                    })
                  }
                >
                  Добавить упражнение
                </button>
              ) : (
                <span className="muted">В одной тренировке максимум 20 упражнений.</span>
              )}
            </div>
          ))}
          <div className="toolbar wrap">
            {days.length < 8 ? (
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  setDays([
                    ...days,
                    {
                      title: `День ${days.length + 1}`,
                      exercises: [blankExercise(defaultRestSeconds)],
                    },
                  ])
                }
              >
                Добавить день
              </button>
            ) : (
              <span className="muted">В одном цикле максимум 8 тренировочных дней.</span>
            )}
            <button
              disabled={
                mutation.isPending ||
                !scheduleIsValid ||
                durationWeeks < 1 ||
                durationWeeks > 24 ||
                days.some((day) => day.exercises.every((item) => !item.exercise_id))
              }
            >
              {mutation.isPending
                ? 'Сохраняем…'
                : saveAsCopy
                  ? 'Сохранить личную копию'
                  : editingTemplate
                    ? 'Сохранить изменения'
                    : targetTelegramId
                      ? 'Создать и назначить'
                      : 'Создать программу'}
            </button>
          </div>
        </form>
      )}
      {guide && (
        <ExerciseGuideDialog
          exerciseId={guide.id}
          exerciseTitle={guide.title}
          onClose={() => setGuide(null)}
        />
      )}
    </Card>
  );
}
