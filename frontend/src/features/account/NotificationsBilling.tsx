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

function toDateInputValue(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

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
  const [scheduledDate, setScheduledDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return toDateInputValue(tomorrow);
  });
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
                />
                <span>Включить напоминания</span>
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
      <details className="card profile-disclosure">
        <summary>
          <span>
            <strong>Личные уведомления</strong>
            <small>Создание и история уведомлений</small>
          </span>
        </summary>
        <div className="profile-disclosure__body">
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate({
                path: '/api/v1/notifications',
                method: 'POST',
                body: {
                  title,
                  body,
                  scheduled_for: `${scheduledDate}T${String(
                    settings.data?.reminder_hour ?? 9,
                  ).padStart(2, '0')}:00:00`,
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
                <span>Дата</span>
                <div className="date-control notification-date-control">
                  <input
                    type="date"
                    min={toDateInputValue(new Date())}
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    required
                  />
                </div>
                <small className="field-hint">
                  Отправка в {String(settings.data?.reminder_hour ?? 9).padStart(2, '0')}:00
                </small>
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
            <div className="list-grid">
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
        </div>
      </details>
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
