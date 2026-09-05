import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { NotificationItem, NotificationSetting } from '../../shared/api/types';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import { addCalendarDays, dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { usePersistentState } from '../../shared/storage';
import { notificationDraftStorageKey } from '../../shared/userScopedStorage';
import { DisclosureIcon, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { DateInput, TimeInput } from '../../shared/ui/PickerInput';

interface NotificationOpenResponse {
  destination: string;
  stale: boolean;
  message?: string | null;
}

const categoryLabels: Record<string, string> = {
  workout_reminder: 'Тренировка',
  trainer_comment: 'Комментарий тренера',
  trainer_program_update: 'Программа',
  weekly_check_in_reminder: 'Итоги недели',
  measurement_reminder: 'Замеры',
  relationship_event: 'Связь с тренером',
  nutrition_update: 'Питание',
  workout_change: 'Расписание',
  report_handoff: 'Отчёт тренеру',
  custom_reminder: 'Личное напоминание',
};

const navigableCategories = new Set([
  'workout_reminder',
  'trainer_comment',
  'trainer_program_update',
  'weekly_check_in_reminder',
  'measurement_reminder',
  'relationship_event',
  'nutrition_update',
  'workout_change',
  'report_handoff',
]);

function timeValue(value: string | null | undefined, fallback: string): string {
  return value ? value.slice(0, 5) : fallback;
}

function formatWallTime(value: string): string {
  const normalized = value.length === 16 ? `${value}:00` : value;
  const parsed = new Date(`${normalized}Z`);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    timeZone: 'UTC',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

export function NotificationsPanel({ onNavigate }: { onNavigate?: (path: string) => void }) {
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
    title: 'Личное напоминание',
    body: 'Откройте приложение и проверьте запланированное действие',
    scheduledDate: addCalendarDays(dateInputValue(new Date(), timeZone), 1),
  });
  const [notificationDraft, setNotificationDraft, clearNotificationDraft] = usePersistentState(
    notificationDraftStorageKey(user?.id ?? 'anonymous'),
    defaultNotification,
  );
  const [settingsDraft, setSettingsDraft] = useState<NotificationSetting | null>(null);
  const visibleSettings = settingsDraft ?? settings.data ?? null;
  const settingsDirty = Boolean(
    settings.data &&
    settingsDraft &&
    JSON.stringify(settings.data) !== JSON.stringify(settingsDraft),
  );
  const unreadCount = useMemo(
    () => notifications.data?.filter((item) => !item.read_at).length ?? 0,
    [notifications.data],
  );

  const settingsMutation = useMutation({
    mutationFn: (payload: NotificationSetting) =>
      api<NotificationSetting>('/api/v1/notifications/settings', {
        method: 'PATCH',
        body: {
          workout_reminders_enabled: payload.workout_reminders_enabled,
          weekly_check_in_reminders_enabled: payload.weekly_check_in_reminders_enabled,
          measurement_reminders_enabled: payload.measurement_reminders_enabled,
          telegram_enabled: payload.telegram_enabled,
          reminder_hour: payload.reminder_hour,
          quiet_hours_start: payload.quiet_hours_start,
          quiet_hours_end: payload.quiet_hours_end,
        },
      }),
    onSuccess: (saved) => {
      trackProductEvent({
        name: 'notification_preferences_changed',
        surface: productEventSurface(),
      });
      queryClient.setQueryData(['notifications', 'settings'], saved);
      setSettingsDraft(null);
      toast('Настройки уведомлений сохранены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const listMutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['notifications'] });
      if (variables.method === 'POST') {
        clearNotificationDraft(defaultNotification());
        toast('Личное напоминание создано');
      } else {
        toast('Уведомление удалено');
      }
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const openMutation = useMutation({
    mutationFn: (notificationId: number) =>
      api<NotificationOpenResponse>(`/api/v1/notifications/${notificationId}/open`, {
        method: 'POST',
      }),
    onSuccess: (result) => {
      if (result.message) toast(result.message, result.stale ? 'error' : 'success');
      onNavigate?.(result.destination);
      void queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const readAllMutation = useMutation({
    mutationFn: () => api('/api/v1/notifications/read-all', { method: 'PATCH' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] });
      toast('Все уведомления отмечены прочитанными');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  return (
    <div className="notification-preferences stack">
      <section className="notification-settings" aria-labelledby="notification-channels-title">
        {settings.isLoading ? (
          <LoadingState />
        ) : settings.error ? (
          <ErrorState message={(settings.error as Error).message} />
        ) : (
          visibleSettings && (
            <form
              className="stack"
              onSubmit={(event) => {
                event.preventDefault();
                settingsMutation.mutate(visibleSettings);
              }}
            >
              <div className="notification-settings__group">
                <div className="notification-settings__heading">
                  <h3 id="notification-channels-title">Каналы</h3>
                  <p>
                    Подробности всегда остаются в приложении; Telegram показывает нейтральный текст.
                  </p>
                </div>
                <div className="notification-channel-row">
                  <span>
                    <strong>В приложении</strong>
                    <small>Всегда доступно в центре уведомлений</small>
                  </span>
                  <span className="notification-channel-state">Включено</span>
                </div>
                <label
                  className={`switch-row ${!visibleSettings.telegram_linked ? 'is-disabled' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={visibleSettings.telegram_enabled && visibleSettings.telegram_linked}
                    disabled={!visibleSettings.telegram_linked}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        telegram_enabled: event.target.checked,
                      })
                    }
                  />
                  <span>
                    <strong>Telegram</strong>
                    <small>
                      {visibleSettings.telegram_linked
                        ? 'Получать внешние уведомления в связанном аккаунте'
                        : 'Недоступно: сначала свяжите Telegram в разделе доступа'}
                    </small>
                  </span>
                </label>
              </div>

              <div className="notification-settings__group">
                <div className="notification-settings__heading">
                  <h3>Полезные напоминания</h3>
                  <p>
                    Системные сообщения тренера и изменения программы остаются отдельными событиями.
                  </p>
                </div>
                <label className="switch-row">
                  <input
                    type="checkbox"
                    checked={visibleSettings.workout_reminders_enabled}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        workout_reminders_enabled: event.target.checked,
                      })
                    }
                  />
                  <span>
                    <strong>Предстоящая тренировка</strong>
                    <small>За 2 часа до точного времени или в выбранный час дня</small>
                  </span>
                </label>
                <label className="switch-row">
                  <input
                    type="checkbox"
                    checked={visibleSettings.weekly_check_in_reminders_enabled}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        weekly_check_in_reminders_enabled: event.target.checked,
                      })
                    }
                  />
                  <span>
                    <strong>Итоги недели</strong>
                    <small>Одно напоминание в воскресенье, если итоги ещё не заполнены</small>
                  </span>
                </label>
                <label className="switch-row">
                  <input
                    type="checkbox"
                    checked={visibleSettings.measurement_reminders_enabled}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        measurement_reminders_enabled: event.target.checked,
                      })
                    }
                  />
                  <span>
                    <strong>Замеры</strong>
                    <small>Не чаще раза в неделю и только если замеров не было 14 дней</small>
                  </span>
                </label>
              </div>

              <div className="notification-settings__group notification-schedule-grid">
                <label className="field">
                  <span>Час для напоминаний без точного времени</span>
                  <TimeInput
                    controlClassName="reminder-time-control"
                    step="3600"
                    value={`${String(visibleSettings.reminder_hour).padStart(2, '0')}:00`}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        reminder_hour: Number(event.target.value.split(':')[0]),
                      })
                    }
                  />
                </label>
                <label className="switch-row notification-quiet-toggle">
                  <input
                    type="checkbox"
                    checked={Boolean(visibleSettings.quiet_hours_start)}
                    onChange={(event) =>
                      setSettingsDraft({
                        ...visibleSettings,
                        quiet_hours_start: event.target.checked ? '22:00:00' : null,
                        quiet_hours_end: event.target.checked ? '08:00:00' : null,
                      })
                    }
                  />
                  <span>
                    <strong>Тихие часы</strong>
                    <small>Доставка подождёт до окончания выбранного периода</small>
                  </span>
                </label>
                {visibleSettings.quiet_hours_start && visibleSettings.quiet_hours_end && (
                  <div className="notification-quiet-hours">
                    <label className="field">
                      <span>С</span>
                      <TimeInput
                        value={timeValue(visibleSettings.quiet_hours_start, '22:00')}
                        onChange={(event) =>
                          setSettingsDraft({
                            ...visibleSettings,
                            quiet_hours_start: `${event.target.value}:00`,
                          })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>До</span>
                      <TimeInput
                        value={timeValue(visibleSettings.quiet_hours_end, '08:00')}
                        onChange={(event) =>
                          setSettingsDraft({
                            ...visibleSettings,
                            quiet_hours_end: `${event.target.value}:00`,
                          })
                        }
                      />
                    </label>
                  </div>
                )}
              </div>
              <div className="notification-settings__save">
                <button type="submit" disabled={!settingsDirty || settingsMutation.isPending}>
                  {settingsMutation.isPending ? 'Сохраняем…' : 'Сохранить настройки'}
                </button>
              </div>
            </form>
          )
        )}
      </section>

      <details className="notification-center profile-disclosure">
        <summary>
          <span>
            <strong>Центр уведомлений</strong>
            <small>
              {notifications.isLoading
                ? 'Загружаем события…'
                : notifications.error
                  ? 'Не удалось загрузить · можно повторить после раскрытия'
                  : unreadCount
                    ? `Непрочитанные · ${unreadCount}`
                    : notifications.data?.length
                      ? 'Всё прочитано'
                      : 'Уведомлений пока нет'}
            </small>
          </span>
          <DisclosureIcon />
        </summary>
        <div className="profile-disclosure__body">
          <header className="notification-center__head">
            <h3 id="notification-center-title">
              {unreadCount ? `Непрочитанные · ${unreadCount}` : 'Последние события'}
            </h3>
            {unreadCount > 0 && (
              <button
                type="button"
                className="secondary"
                disabled={readAllMutation.isPending}
                onClick={() => readAllMutation.mutate()}
              >
                Отметить всё
              </button>
            )}
          </header>
          {notifications.isLoading ? (
            <LoadingState />
          ) : notifications.error ? (
            <ErrorState
              message={(notifications.error as Error).message}
              retry={() => void notifications.refetch()}
            />
          ) : !notifications.data?.length ? (
            <EmptyState
              title="Уведомлений пока нет"
              text="Здесь появятся напоминания и важные изменения от тренера."
            />
          ) : (
            <div className="notification-list">
              {notifications.data.map((item) => {
                const canOpen = navigableCategories.has(item.category);
                const copy = (
                  <>
                    <span className="notification-row__meta">
                      {categoryLabels[item.category] ?? 'Событие'}
                      {!item.read_at && <span>Новое</span>}
                    </span>
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                    <span className="muted">
                      {item.event_kind === 'reminder' ? 'Запланировано' : 'Создано'}:{' '}
                      {formatWallTime(item.scheduled_for)}
                    </span>
                  </>
                );
                return (
                  <article
                    className={`notification-row ${item.read_at ? '' : 'notification-row--unread'}`}
                    key={item.id}
                  >
                    {canOpen && onNavigate ? (
                      <button
                        type="button"
                        className="notification-row__main text-button notification-action"
                        aria-label={`Открыть: ${item.title}`}
                        disabled={openMutation.isPending}
                        onClick={() => openMutation.mutate(item.id)}
                      >
                        {copy}
                      </button>
                    ) : (
                      <div className="notification-row__main">{copy}</div>
                    )}
                    <button
                      type="button"
                      className="notification-row__delete"
                      onClick={async () => {
                        if (
                          await confirm({
                            title: 'Удалить уведомление?',
                            message: item.title,
                            confirmText: 'Удалить',
                          })
                        ) {
                          listMutation.mutate({
                            path: `/api/v1/notifications/${item.id}`,
                            method: 'DELETE',
                          });
                        }
                      }}
                    >
                      Удалить
                    </button>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </details>

      <details className="notification-personal profile-disclosure">
        <summary>
          <span>
            <strong>Личное напоминание</strong>
            <small>Свободный текст остаётся внутри приложения</small>
          </span>
          <DisclosureIcon />
        </summary>
        <div className="profile-disclosure__body">
          <p className="muted">
            В Telegram придёт только нейтральная фраза без текста напоминания.
          </p>
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault();
              listMutation.mutate({
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
                  onChange={(event) =>
                    setNotificationDraft({ ...notificationDraft, title: event.target.value })
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
                  onChange={(event) =>
                    setNotificationDraft({
                      ...notificationDraft,
                      scheduledDate: event.target.value,
                    })
                  }
                  required
                />
                <small className="field-hint">
                  Отправка в {String(settings.data?.reminder_hour ?? 9).padStart(2, '0')}:00
                </small>
              </label>
            </div>
            <label className="field">
              <span>Текст внутри приложения</span>
              <textarea
                value={notificationDraft.body}
                maxLength={2000}
                onChange={(event) =>
                  setNotificationDraft({ ...notificationDraft, body: event.target.value })
                }
                required
              />
            </label>
            <button className="secondary" disabled={listMutation.isPending}>
              {listMutation.isPending ? 'Создаём…' : 'Создать напоминание'}
            </button>
          </form>
        </div>
      </details>
    </div>
  );
}
