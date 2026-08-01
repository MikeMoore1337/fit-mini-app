import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  BillingPlan,
  NotificationItem,
  NotificationSetting,
  Subscription,
} from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

export function NotificationsPanel() {
  const queryClient = useQueryClient();
  const { toast, confirm } = useFeedback();
  const settings = useQuery({
    queryKey: ['notifications', 'settings'],
    queryFn: () => api<NotificationSetting>('/api/v1/notifications/settings'),
  });
  const notifications = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => api<NotificationItem[]>('/api/v1/notifications'),
  });
  const [title, setTitle] = useState('Тренировка');
  const [body, setBody] = useState('Пора выполнить тренировку по плану');
  const [scheduled, setScheduled] = useState(() =>
    new Date(Date.now() + 3600_000).toISOString().slice(0, 16),
  );
  const mutation = useMutation({
    mutationFn: ({
      path,
      method,
      body: payload,
    }: {
      path: string;
      method: string;
      body?: unknown;
    }) => api(path, { method, body: payload }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast('Уведомления обновлены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  return (
    <div className="stack">
      <Card title="Напоминания о тренировках">
        {settings.isLoading ? (
          <LoadingState />
        ) : settings.error ? (
          <ErrorState message={(settings.error as Error).message} />
        ) : (
          settings.data && (
            <div className="form-grid top-gap">
              <label className="switch-row">
                <input
                  type="checkbox"
                  checked={settings.data.workout_reminders_enabled}
                  onChange={(e) =>
                    mutation.mutate({
                      path: '/api/v1/notifications/settings',
                      method: 'PATCH',
                      body: { ...settings.data, workout_reminders_enabled: e.target.checked },
                    })
                  }
                />{' '}
                Включить напоминания
              </label>
              <label className="field">
                <span>Час отправки</span>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={settings.data.reminder_hour}
                  onChange={(e) =>
                    mutation.mutate({
                      path: '/api/v1/notifications/settings',
                      method: 'PATCH',
                      body: { ...settings.data, reminder_hour: Number(e.target.value) },
                    })
                  }
                />
              </label>
            </div>
          )
        )}
      </Card>
      <Card title="Личное уведомление">
        <form
          className="stack top-gap"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate({
              path: '/api/v1/notifications',
              method: 'POST',
              body: {
                title,
                body,
                scheduled_for: scheduled.length === 16 ? `${scheduled}:00` : scheduled,
              },
            });
          }}
        >
          <div className="form-grid">
            <label className="field">
              <span>Заголовок</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label className="field">
              <span>Когда</span>
              <input
                type="datetime-local"
                value={scheduled}
                onChange={(e) => setScheduled(e.target.value)}
                required
              />
            </label>
          </div>
          <label className="field">
            <span>Текст</span>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} required />
          </label>
          <button>Создать уведомление</button>
        </form>
        {notifications.isLoading ? (
          <LoadingState />
        ) : notifications.error ? (
          <ErrorState message={(notifications.error as Error).message} />
        ) : !notifications.data?.length ? (
          <EmptyState title="Уведомлений пока нет" />
        ) : (
          <div className="list-grid top-gap">
            {notifications.data.map((item) => (
              <article className="list-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                  <span className="muted">
                    {new Date(item.scheduled_for).toLocaleString('ru-RU')}
                  </span>
                </div>
                <div className="list-row__actions">
                  <Badge>{item.status}</Badge>
                  <button
                    className="btn-danger"
                    onClick={async () => {
                      if (
                        await confirm({
                          title: 'Удалить уведомление?',
                          message: item.title,
                          confirmText: 'Удалить',
                        })
                      )
                        mutation.mutate({
                          path: `/api/v1/notifications/${item.id}`,
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
      </Card>
    </div>
  );
}

export function BillingPanel() {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const plans = useQuery({
    queryKey: ['billing', 'plans'],
    queryFn: () => api<BillingPlan[]>('/api/v1/billing/plans'),
  });
  const subscription = useQuery({
    queryKey: ['billing', 'subscription'],
    queryFn: () => api<Subscription | null>('/api/v1/billing/subscription'),
  });
  const mutation = useMutation({
    mutationFn: (code: string) =>
      api<{ checkout_id: string; checkout_url: string; status: string }>(
        '/api/v1/billing/checkout',
        { method: 'POST', body: { plan_code: code } },
      ),
    onSuccess: async (checkout) => {
      if (checkout.checkout_url) window.location.href = checkout.checkout_url;
      await queryClient.invalidateQueries({ queryKey: ['billing'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  return (
    <Card title="Подписка">
      {subscription.data && (
        <div className="auth-notice top-gap">
          <strong>{subscription.data.plan_title}</strong> ·{' '}
          <Badge>{subscription.data.status}</Badge>
          {subscription.data.ends_at && (
            <p className="muted">
              До {new Date(subscription.data.ends_at).toLocaleDateString('ru-RU')}
            </p>
          )}
        </div>
      )}
      {plans.isLoading ? (
        <LoadingState />
      ) : plans.error ? (
        <ErrorState message={(plans.error as Error).message} />
      ) : (
        <div className="list-grid top-gap">
          {plans.data?.map((plan) => (
            <article className="list-row" key={plan.code}>
              <div>
                <strong>{plan.title}</strong>
                <p className="muted">{plan.period_days} дней</p>
              </div>
              <button disabled={mutation.isPending} onClick={() => mutation.mutate(plan.code)}>
                {plan.price} {plan.currency}
              </button>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
