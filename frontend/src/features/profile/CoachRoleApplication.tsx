import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { CoachRoleApplication } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, ErrorState, LoadingState } from '../../shared/ui/common';

const statusLabels: Record<CoachRoleApplication['status'], string> = {
  pending: 'На рассмотрении',
  approved: 'Одобрена',
  rejected: 'Отклонена',
  cancelled: 'Отменена',
};

export function CoachRoleApplicationCard() {
  const { user } = useAuth();
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const application = useQuery({
    queryKey: ['me', 'coach-application'],
    queryFn: () => api<CoachRoleApplication | null>('/api/v1/me/coach-application'),
    enabled: Boolean(user && !user.is_coach),
  });
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['me', 'coach-application'] });
  };
  const submit = useMutation({
    mutationFn: () => api<CoachRoleApplication>('/api/v1/me/coach-application', { method: 'POST' }),
    onSuccess: async () => {
      await refresh();
      toast('Заявка на кабинет тренера отправлена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const cancel = useMutation({
    mutationFn: () => api('/api/v1/me/coach-application', { method: 'DELETE' }),
    onSuccess: async () => {
      await refresh();
      toast('Заявка отменена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  if (!user || user.is_coach) return null;

  const requestCoachRole = async () => {
    const accepted = await confirm({
      title: 'Стать тренером?',
      message:
        'Заявка попадёт администратору. После одобрения в приложении откроется кабинет тренера.',
      confirmText: 'Отправить заявку',
      danger: false,
    });
    if (accepted) submit.mutate();
  };

  return (
    <Card
      title="Стать тренером"
      description="Отправьте заявку администратору прямо из приложения. Писать кому-либо отдельно не нужно."
    >
      {application.isLoading ? (
        <LoadingState label="Проверяем статус заявки…" />
      ) : application.error ? (
        <ErrorState
          message={(application.error as Error).message}
          retry={() => void application.refetch()}
        />
      ) : application.data?.status === 'pending' ? (
        <div className="coach-application top-gap">
          <div className="coach-application__status">
            <div>
              <strong>Заявка отправлена</strong>
              <p className="muted">Администратор рассмотрит её вручную.</p>
            </div>
            <Badge>{statusLabels.pending}</Badge>
          </div>
          <button
            type="button"
            className="secondary"
            disabled={cancel.isPending}
            onClick={() => cancel.mutate()}
          >
            Отменить заявку
          </button>
        </div>
      ) : (
        <div className="coach-application top-gap">
          {application.data && (
            <p className="muted">
              Предыдущая заявка: {statusLabels[application.data.status].toLowerCase()}.
            </p>
          )}
          <p>
            После одобрения здесь появятся инструменты для приглашения клиентов и ведения их
            программ.
          </p>
          <button type="button" disabled={submit.isPending} onClick={() => void requestCoachRole()}>
            {submit.isPending ? 'Отправляем…' : 'Стать тренером'}
          </button>
        </div>
      )}
    </Card>
  );
}
