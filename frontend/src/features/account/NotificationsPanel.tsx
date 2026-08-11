import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { NotificationItem, NotificationSetting } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useAuth } from '../../app/AuthProvider';
import { addCalendarDays, dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { usePersistentState } from '../../shared/storage';
import { notificationStatusLabel } from '../../shared/statusLabels';
import { DateInput, TimeInput } from '../../shared/ui/PickerInput';

type NotificationDestination = 'today' | 'nutrition';

function notificationDestination(item: NotificationItem): NotificationDestination | null {
  if (item.title === 'Тренировка сегодня') return 'today';
  if (item.title === 'КБЖУ пересчитаны') return 'nutrition';
  return null;
}

export function NotificationsPanel({
  onNavigate,
}: {
  onNavigate?: (destination: NotificationDestination) => void;
}) {
  const queryClient = useQueryClient();
  const { toast, confirm } = useFeedback();
  const { user } = useAuth();
  const timeZone = user?.profile?.timezone || detectedTimeZone();
  const settings = useQuery({
    queryKey: ['notifications', 'settings'],
    queryFn: () => api<NotificationSetting>('/api/v1/notifications/settings'),
  });
  const notifications = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => api<NotificationItem[]>('/api/v1/notifications'),
  });
  const defaultNotification = () => ({
    title: 'Тренировка',
    body: 'Пора выполнить тренировку по плану',
    scheduledDate: addCalendarDays(dateInputValue(new Date(), timeZone), 1),
  });
  const [notificationDraft, setNotificationDraft, clearNotificationDraft] = usePersistentState(
    `fit_notification_draft_${user?.id ?? 'anonymous'}`,
    defaultNotification,
  );
  const [settingsDraft, setSettingsDraft] = useState<NotificationSetting | null>(null);
  const visibleSettings = settingsDraft ?? settings.data ?? null;
  const settingsDirty = Boolean(
    settings.data &&
    settingsDraft &&
    (settings.data.reminder_hour !== settingsDraft.reminder_hour ||
      settings.data.workout_reminders_enabled !== settingsDraft.workout_reminders_enabled),
  );
  const settingsMutation = useMutation({
    mutationFn: (payload: NotificationSetting) =>
      api<NotificationSetting>('/api/v1/notifications/settings', {
        method: 'PATCH',
        body: payload,
      }),
    onSuccess: (saved) => {
      queryClient.setQueryData(['notifications', 'settings'], saved);
      setSettingsDraft(null);
      toast('Настройки напоминаний сохранены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
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
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['notifications'] });
      if (variables.method === 'POST') {
        clearNotificationDraft(defaultNotification());
        toast('Уведомление создано');
      } else {
        toast('Уведомление удалено');
      }
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
          visibleSettings && (
            <form
              className="stack top-gap"
              onSubmit={(event) => {
                event.preventDefault();
                settingsMutation.mutate(visibleSettings);
              }}
            >
              <div className="form-grid">
                <label className="switch-row">
                  <input
                    type="checkbox"
                    checked={visibleSettings.workout_reminders_enabled}
                    onChange={(e) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        workout_reminders_enabled: e.target.checked,
                      })
                    }
                  />
                  <span>Включить напоминания</span>
                </label>
                <label className="field">
                  <span>Час отправки</span>
                  <TimeInput
                    controlClassName="reminder-time-control"
                    step="3600"
                    value={`${String(visibleSettings.reminder_hour).padStart(2, '0')}:00`}
                    onChange={(e) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        reminder_hour: Number(e.target.value.split(':')[0]),
                      })
                    }
                  />
                </label>
              </div>
              <button type="submit" disabled={!settingsDirty || settingsMutation.isPending}>
                {settingsMutation.isPending ? 'Сохраняем…' : 'Сохранить настройки'}
              </button>
            </form>
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
                  title: notificationDraft.title,
                  body: notificationDraft.body,
                  scheduled_for: `${notificationDraft.scheduledDate}T${String(
                    settings.data?.reminder_hour ?? 9,
                  ).padStart(2, '0')}:00:00`,
                },
              });
            }}
          >
            <div className="form-grid">
              <label className="field">
                <span>Заголовок</span>
                <input
                  value={notificationDraft.title}
                  maxLength={128}
                  onChange={(e) =>
                    setNotificationDraft({ ...notificationDraft, title: e.target.value })
                  }
                  required
                />
              </label>
              <label className="field">
                <span>Дата</span>
                <DateInput
                  controlClassName="notification-date-control"
                  min={dateInputValue(new Date(), timeZone)}
                  value={notificationDraft.scheduledDate}
                  onChange={(e) =>
                    setNotificationDraft({ ...notificationDraft, scheduledDate: e.target.value })
                  }
                  required
                />
                <small className="field-hint">
                  Отправка в {String(settings.data?.reminder_hour ?? 9).padStart(2, '0')}:00
                </small>
              </label>
            </div>
            <label className="field">
              <span>Текст</span>
              <textarea
                value={notificationDraft.body}
                maxLength={2000}
                onChange={(e) =>
                  setNotificationDraft({ ...notificationDraft, body: e.target.value })
                }
                required
              />
            </label>
            <button disabled={mutation.isPending}>
              {mutation.isPending ? 'Создаём…' : 'Создать уведомление'}
            </button>
          </form>
          {notifications.isLoading ? (
            <LoadingState />
          ) : notifications.error ? (
            <ErrorState message={(notifications.error as Error).message} />
          ) : !notifications.data?.length ? (
            <EmptyState title="Уведомлений пока нет" />
          ) : (
            <div className="list-grid">
              {notifications.data.map((item) => {
                const destination = notificationDestination(item);
                const notificationCopy = (
                  <>
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                    <span className="muted">
                      {new Date(item.scheduled_for).toLocaleString('ru-RU')}
                    </span>
                  </>
                );
                return (
                  <article className="list-row" key={item.id}>
                    {destination && onNavigate ? (
                      <button
                        type="button"
                        className="list-row__main text-button notification-action"
                        aria-label={
                          destination === 'today'
                            ? `Открыть тренировку: ${item.title}`
                            : `Открыть раздел питания: ${item.title}`
                        }
                        onClick={() => onNavigate(destination)}
                      >
                        {notificationCopy}
                      </button>
                    ) : (
                      <div className="list-row__main">{notificationCopy}</div>
                    )}
                    <div className="list-row__actions">
                      <Badge>{notificationStatusLabel(item.status)}</Badge>
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
                );
              })}
            </div>
          )}
        </div>
      </details>
    </div>
  );
}
