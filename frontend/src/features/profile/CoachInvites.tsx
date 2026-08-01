import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { CoachInvite } from '../../shared/api/types';
import { useAuth } from '../../app/AuthProvider';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

export function CoachInvites() {
  const { user, reloadUser } = useAuth();
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const invites = useQuery({
    queryKey: ['coach-invites'],
    queryFn: () => api<CoachInvite[]>('/api/v1/me/coach-invites'),
  });
  const mutation = useMutation({
    mutationFn: ({ path, method }: { path: string; method: string }) => api(path, { method }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['coach-invites'] }),
        reloadUser(),
      ]);
      toast('Связь с тренером обновлена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  return (
    <Card title="Тренер и код клиента">
      <div className="metric-grid top-gap">
        <div className="metric">
          <span>Код клиента</span>
          <strong>{user?.client_code || '—'}</strong>
        </div>
        <div className="metric">
          <span>Тренер</span>
          <strong>{user?.trainer?.full_name || user?.trainer?.username || 'Не назначен'}</strong>
        </div>
      </div>
      <div className="toolbar wrap top-gap">
        <button
          className="secondary"
          onClick={async () => {
            if (!user?.client_code) return;
            try {
              await navigator.clipboard.writeText(user.client_code);
              toast('Код клиента скопирован');
            } catch {
              toast('Не удалось скопировать код', 'error');
            }
          }}
        >
          Копировать код
        </button>
        <button
          className="secondary"
          onClick={() => mutation.mutate({ path: '/api/v1/me/client-code/rotate', method: 'POST' })}
        >
          Обновить код
        </button>
        {user?.trainer?.chat_url && (
          <a className="button-link" href={user.trainer.chat_url} target="_blank" rel="noreferrer">
            Написать тренеру
          </a>
        )}
        {user?.trainer && (
          <button
            className="btn-danger"
            onClick={async () => {
              if (
                await confirm({
                  title: 'Отвязаться от тренера?',
                  message: 'Тренер потеряет доступ к профилю и назначениям.',
                  confirmText: 'Отвязаться',
                })
              )
                mutation.mutate({ path: '/api/v1/me/trainer', method: 'DELETE' });
            }}
          >
            Отвязаться
          </button>
        )}
      </div>
      <h3 className="top-gap">Приглашения</h3>
      {invites.isLoading ? (
        <LoadingState />
      ) : invites.error ? (
        <ErrorState message={(invites.error as Error).message} />
      ) : !invites.data?.length ? (
        <EmptyState title="Новых приглашений нет" />
      ) : (
        <div className="list-grid">
          {invites.data.map((invite) => (
            <article className="list-row" key={invite.id}>
              <div>
                <strong>
                  {invite.coach_full_name ||
                    invite.coach_username ||
                    `Тренер ${invite.coach_user_id}`}
                </strong>
                <br />
                <Badge>Ожидает ответа</Badge>
              </div>
              <div className="list-row__actions">
                <button
                  onClick={() =>
                    mutation.mutate({
                      path: `/api/v1/me/coach-invites/${invite.id}/accept`,
                      method: 'POST',
                    })
                  }
                >
                  Принять
                </button>
                <button
                  className="secondary"
                  onClick={() =>
                    mutation.mutate({
                      path: `/api/v1/me/coach-invites/${invite.id}/decline`,
                      method: 'POST',
                    })
                  }
                >
                  Отклонить
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
