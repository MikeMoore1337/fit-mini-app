import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ProgramTemplate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

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

function programMeta(item: ProgramTemplate) {
  return `${goalLabels[item.goal] ?? 'Цель не указана'} · ${levelLabels[item.level] ?? 'Уровень не указан'} · ${item.days.length} дн.`;
}

export function TemplatesList() {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [selectedExample, setSelectedExample] = useState<ProgramTemplate | null>(null);
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
      await queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast('Программы обновлены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  useEffect(() => {
    if (!selectedExample) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedExample(null);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [selectedExample]);

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
                      onClick={() =>
                        mutation.mutate({
                          path: `/api/v1/programs/templates/${item.id}/assign-to-me`,
                          method: 'POST',
                          body: {},
                        })
                      }
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
          <div className="modal__panel card program-example-modal__panel">
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
    </>
  );
}
