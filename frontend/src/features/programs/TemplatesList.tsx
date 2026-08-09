import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { ProgramTemplate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useAuth } from '../../app/AuthProvider';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { useModalA11y } from '../../shared/ui/useModalA11y';

const goalLabels: Record<string, string> = {
  muscle_gain: 'Набор мышечной массы',
  fat_loss: 'Снижение веса',
  maintenance: 'Поддержание формы',
  recomposition: 'Рекомпозиция',
};

const levelLabels: Record<string, string> = {
  beginner: 'Начальный уровень',
  intermediate: 'Средний уровень',
  advanced: 'Продвинутый уровень',
};
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

function defaultWeekdays(template: ProgramTemplate, startDate: string): number[] {
  const firstWeekday = weekdayFromDate(startDate);
  return template.days.map((_, index) => (firstWeekday + index) % 7);
}

function programMeta(item: ProgramTemplate) {
  return `${goalLabels[item.goal] ?? 'Цель не указана'} · ${levelLabels[item.level] ?? 'Уровень не указан'} · ${item.days.length} дн.`;
}

export function TemplatesList() {
  const { toast, confirm } = useFeedback();
  const { user, reloadUser } = useAuth();
  const queryClient = useQueryClient();
  const [selectedExample, setSelectedExample] = useState<ProgramTemplate | null>(null);
  const [assignmentTemplate, setAssignmentTemplate] = useState<ProgramTemplate | null>(null);
  const defaultStartDate = dateInputValue(
    new Date(),
    user?.profile?.timezone || detectedTimeZone(),
  );
  const [assignmentStartDate, setAssignmentStartDate] = useState(defaultStartDate);
  const [assignmentDuration, setAssignmentDuration] = useState(4);
  const [assignmentWeekdays, setAssignmentWeekdays] = useState<number[]>([]);
  const examplePanelRef = useModalA11y<HTMLDivElement>(Boolean(selectedExample), () =>
    setSelectedExample(null),
  );
  const assignmentPanelRef = useModalA11y<HTMLDivElement>(Boolean(assignmentTemplate), () =>
    setAssignmentTemplate(null),
  );
  const templates = useQuery({
    queryKey: ['templates', 'mine'],
    queryFn: () => api<ProgramTemplate[]>('/api/v1/programs/templates/mine'),
  });
  const hidden = useQuery({
    queryKey: ['templates', 'hidden'],
    queryFn: () => api<ProgramTemplate[]>('/api/v1/programs/templates/hidden'),
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['templates'] }),
        queryClient.invalidateQueries({ queryKey: ['workout'] }),
        reloadUser(),
      ]);
      toast('Программы обновлены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  const assignmentMutation = useMutation({
    mutationFn: ({ templateId, replaceActive }: { templateId: number; replaceActive: boolean }) =>
      api(`/api/v1/programs/templates/${templateId}/assign-to-me`, {
        method: 'POST',
        body: {
          start_date: assignmentStartDate,
          duration_weeks: assignmentDuration,
          schedule_weekdays: assignmentWeekdays,
          replace_active: replaceActive,
        },
      }),
    onSuccess: async () => {
      setAssignmentTemplate(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['templates'] }),
        queryClient.invalidateQueries({ queryKey: ['workout'] }),
        reloadUser(),
      ]);
      toast('Программа назначена');
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
            message:
              'Текущая программа будет отправлена в архив. Тренировку, которая уже идёт, заменить нельзя.',
            confirmText: 'Заменить программу',
          })
        )
          assignmentMutation.mutate({ ...variables, replaceActive: true });
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

  const assignmentOffsets = assignmentWeekdays.map(
    (weekday) => (weekday - (assignmentWeekdays[0] ?? weekday) + 7) % 7,
  );
  const assignmentScheduleIsValid =
    Boolean(assignmentTemplate) &&
    (assignmentTemplate?.days.length ?? 0) <= 7 &&
    assignmentWeekdays.length === assignmentTemplate?.days.length &&
    new Set(assignmentWeekdays).size === assignmentWeekdays.length &&
    assignmentOffsets.every(
      (offset, index) => index === 0 || offset > assignmentOffsets[index - 1]!,
    );

  return (
    <>
      <Card title="Мои программы">
        {templates.isLoading ? (
          <LoadingState />
        ) : templates.error ? (
          <ErrorState message={(templates.error as Error).message} />
        ) : !templates.data?.length ? (
          <EmptyState title="Программ пока нет" text="Создайте первую программу в конструкторе." />
        ) : (
          <div className="list-grid top-gap">
            {templates.data.map((item) => (
              <article
                className={`list-row${item.is_example ? ' program-example-row' : ''}`}
                key={item.id}
              >
                {item.is_example ? (
                  <button
                    type="button"
                    className="text-button program-example-trigger"
                    aria-label={`Посмотреть пример программы «${item.title}»`}
                    onClick={() => setSelectedExample(item)}
                  >
                    <strong>{item.title}</strong>
                    <span className="muted">{programMeta(item)}</span>
                    <span className="program-template-badges">
                      {item.is_active_for_current_user && <Badge>Активна</Badge>}
                      <Badge>Пример программы</Badge>
                    </span>
                    <span className="program-example-trigger__hint">Посмотреть упражнения</span>
                  </button>
                ) : (
                  <div className="list-row__main">
                    <strong>{item.title}</strong>
                    <span className="muted">{programMeta(item)}</span>
                    {item.is_active_for_current_user && (
                      <span className="program-template-badges">
                        <Badge>Активна</Badge>
                      </span>
                    )}
                  </div>
                )}
                <div className="list-row__actions">
                  {!item.is_active_for_current_user && (
                    <button
                      onClick={() => {
                        setAssignmentStartDate(defaultStartDate);
                        setAssignmentDuration(4);
                        setAssignmentWeekdays(defaultWeekdays(item, defaultStartDate));
                        setAssignmentTemplate(item);
                      }}
                    >
                      Назначить себе
                    </button>
                  )}
                  <button
                    className="btn-danger"
                    onClick={async () => {
                      if (
                        await confirm({
                          title: 'Скрыть или удалить программу?',
                          message: item.title,
                          confirmText: 'Продолжить',
                        })
                      )
                        mutation.mutate({
                          path: `/api/v1/programs/templates/${item.id}`,
                          method: 'DELETE',
                        });
                    }}
                  >
                    {item.is_example ? 'Скрыть' : 'Удалить'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
        {!!hidden.data?.length && (
          <details className="top-gap">
            <summary>Скрытые примеры программ ({hidden.data.length})</summary>
            <div className="list-grid top-gap">
              {hidden.data.map((item) => (
                <article className="list-row" key={item.id}>
                  <strong>{item.title}</strong>
                  <button
                    className="secondary"
                    onClick={() =>
                      mutation.mutate({
                        path: `/api/v1/programs/templates/${item.id}/restore`,
                        method: 'POST',
                      })
                    }
                  >
                    Восстановить
                  </button>
                </article>
              ))}
            </div>
          </details>
        )}
      </Card>
      {selectedExample && (
        <div
          className="modal program-example-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="program-example-title"
        >
          <button
            type="button"
            className="modal__backdrop"
            aria-label="Закрыть состав программы"
            onClick={() => setSelectedExample(null)}
          />
          <div
            className="modal__panel card program-example-modal__panel"
            ref={examplePanelRef}
            tabIndex={-1}
          >
            <div className="program-example-modal__head">
              <div>
                <span className="eyebrow">Пример программы</span>
                <h2 id="program-example-title">{selectedExample.title}</h2>
                <p className="muted">{programMeta(selectedExample)}</p>
              </div>
              <button
                type="button"
                className="secondary program-example-modal__close"
                aria-label="Закрыть состав программы"
                onClick={() => setSelectedExample(null)}
              >
                ×
              </button>
            </div>
            <div className="program-example-days">
              {selectedExample.days.map((day) => (
                <section className="program-example-day" key={day.id}>
                  <h3>
                    День {day.day_number}. {day.title}
                  </h3>
                  <ol>
                    {day.exercises.map((exercise) => (
                      <li key={exercise.id}>
                        <strong>{exercise.exercise_title}</strong>
                        <span>
                          {exercise.prescribed_sets} подх. × {exercise.prescribed_reps} · отдых{' '}
                          {exercise.rest_seconds} сек.
                        </span>
                        {exercise.notes && <small>{exercise.notes}</small>}
                      </li>
                    ))}
                  </ol>
                </section>
              ))}
            </div>
          </div>
        </div>
      )}
      {assignmentTemplate && (
        <div
          className="modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="assign-program-title"
        >
          <button
            type="button"
            className="modal__backdrop"
            aria-label="Закрыть настройку расписания"
            onClick={() => setAssignmentTemplate(null)}
          />
          <div
            className="modal__panel card assignment-modal"
            ref={assignmentPanelRef}
            tabIndex={-1}
          >
            <div className="section-head">
              <div>
                <span className="eyebrow">Расписание программы</span>
                <h2 id="assign-program-title">{assignmentTemplate.title}</h2>
              </div>
              <button
                type="button"
                className="secondary"
                aria-label="Закрыть настройку расписания"
                onClick={() => setAssignmentTemplate(null)}
              >
                ×
              </button>
            </div>
            <form
              className="stack"
              onSubmit={async (event) => {
                event.preventDefault();
                const active = templates.data?.find(
                  (template) => template.is_active_for_current_user,
                );
                let replaceActive = false;
                if (
                  active &&
                  !(await confirm({
                    title: 'Заменить активную программу?',
                    message: `«${active.title}» будет отправлена в архив, а «${assignmentTemplate.title}» станет активной.`,
                    confirmText: 'Заменить программу',
                  }))
                )
                  return;
                replaceActive = Boolean(active);
                assignmentMutation.mutate({ templateId: assignmentTemplate.id, replaceActive });
              }}
            >
              <div className="form-grid">
                <label className="field">
                  <span>Начать не раньше</span>
                  <input
                    type="date"
                    min={defaultStartDate}
                    value={assignmentStartDate}
                    onChange={(event) => {
                      const nextStartDate = event.target.value;
                      setAssignmentStartDate(nextStartDate);
                      setAssignmentWeekdays(defaultWeekdays(assignmentTemplate, nextStartDate));
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
                    value={assignmentDuration}
                    onChange={(event) => setAssignmentDuration(Number(event.target.value))}
                    required
                  />
                </label>
              </div>
              <div className="form-grid">
                {assignmentTemplate.days.map((day, dayIndex) => (
                  <label className="field" key={day.id}>
                    <span>{day.title || `День ${dayIndex + 1}`}</span>
                    <select
                      value={assignmentWeekdays[dayIndex] ?? ''}
                      onChange={(event) =>
                        setAssignmentWeekdays(
                          assignmentWeekdays.map((value, index) =>
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
              {!assignmentScheduleIsValid && (
                <p className="field-error" role="alert">
                  Выберите разные дни недели в порядке тренировок. В одной неделе доступно до семи
                  дней.
                </p>
              )}
              <button
                disabled={
                  assignmentMutation.isPending ||
                  !assignmentScheduleIsValid ||
                  assignmentDuration < 1 ||
                  assignmentDuration > 24
                }
              >
                {assignmentMutation.isPending ? 'Назначаем…' : 'Назначить по расписанию'}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
