import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ProgramTemplate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

export function TemplatesList() {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
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
  return (
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
            <article className="list-row" key={item.id}>
              <div className="list-row__main">
                <strong>{item.title}</strong>
                <span className="muted">
                  {item.goal} · {item.level} · {item.days.length} дн.
                </span>
                <div>
                  {item.is_active_for_current_user && <Badge>Активна</Badge>}{' '}
                  {item.is_example && <Badge>Пример</Badge>}
                </div>
              </div>
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
                  Удалить
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      {!!hidden.data?.length && (
        <details className="top-gap">
          <summary>Скрытые примеры ({hidden.data.length})</summary>
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
  );
}
