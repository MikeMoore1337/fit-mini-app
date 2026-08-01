import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type {
  AdminNotification,
  AdminPayment,
  AdminTemplate,
  AdminUser,
} from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { Redirect } from '../../shared/navigation/router';

type AdminTab = 'users' | 'payments' | 'notifications' | 'templates';
const PAGE_SIZE = 50;

function Pagination({
  page,
  hasNext,
  onPage,
}: {
  page: number;
  hasNext: boolean;
  onPage(page: number): void;
}) {
  if (page === 0 && !hasNext) return null;
  return (
    <div className="toolbar top-gap">
      <button className="secondary" disabled={page === 0} onClick={() => onPage(page - 1)}>
        Назад
      </button>
      <span className="muted">Страница {page + 1}</span>
      <button className="secondary" disabled={!hasNext} onClick={() => onPage(page + 1)}>
        Далее
      </button>
    </div>
  );
}

function roleLabel(user: AdminUser): string {
  if (user.role === 'admin') return 'Администратор';
  if (user.role === 'coach') return 'Тренер';
  return 'Клиент';
}

export default function AdminPage() {
  const { user } = useAuth();
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<AdminTab>('users');
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [page, setPage] = useState(0);
  const offset = page * PAGE_SIZE;
  const userParams = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (search.trim()) userParams.set('search', search.trim());
  if (role) userParams.set('role', role);

  const users = useQuery({
    queryKey: ['admin', 'users', page, search, role],
    queryFn: () => api<AdminUser[]>(`/api/v1/admin/users?${userParams}`),
  });
  const payments = useQuery({
    queryKey: ['admin', 'payments', page],
    queryFn: () =>
      api<AdminPayment[]>(`/api/v1/admin/payments?limit=${PAGE_SIZE}&offset=${offset}`),
    enabled: tab === 'payments',
  });
  const notifications = useQuery({
    queryKey: ['admin', 'notifications', page],
    queryFn: () =>
      api<AdminNotification[]>(`/api/v1/admin/notifications?limit=${PAGE_SIZE}&offset=${offset}`),
    enabled: tab === 'notifications',
  });
  const templates = useQuery({
    queryKey: ['admin', 'templates', page],
    queryFn: () =>
      api<AdminTemplate[]>(`/api/v1/admin/templates?limit=${PAGE_SIZE}&offset=${offset}`),
    enabled: tab === 'templates',
  });

  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin'] });
      toast('Изменения сохранены');
    },
    onError: (reason) =>
      toast(reason instanceof Error ? reason.message : 'Не удалось сохранить', 'error'),
  });

  if (!user?.is_admin) return <Redirect to="/app" />;

  const removeUser = async (item: AdminUser) => {
    if (
      await confirm({
        title: 'Удалить пользователя?',
        message: `Будут удалены данные ${item.full_name || item.telegram_user_id}. Это действие необратимо.`,
        confirmText: 'Удалить',
      })
    ) {
      mutation.mutate({ path: `/api/v1/admin/users/${item.id}`, method: 'DELETE' });
    }
  };

  return (
    <AppShell narrow>
      <div className="page-stack">
        <header className="card hero-card">
          <div>
            <span className="eyebrow">Управление</span>
            <h1>Панель администратора</h1>
            <p className="muted">Пользователи, платежи, уведомления и шаблоны.</p>
          </div>
          <Badge>Администратор</Badge>
        </header>
        <div className="react-tabs" role="tablist">
          {(
            [
              ['users', 'Пользователи'],
              ['payments', 'Платежи'],
              ['notifications', 'Уведомления'],
              ['templates', 'Шаблоны'],
            ] as const
          ).map(([key, label]) => (
            <button
              type="button"
              className={tab === key ? 'is-active' : 'secondary'}
              onClick={() => {
                setTab(key);
                setPage(0);
              }}
              key={key}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'users' && (
          <Card
            title="Пользователи"
            actions={
              <button type="button" className="secondary" onClick={() => void users.refetch()}>
                Обновить
              </button>
            }
          >
            <div className="form-grid top-gap">
              <label className="field">
                <span>Поиск</span>
                <input
                  type="search"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(0);
                  }}
                  placeholder="Имя, username или Telegram ID"
                />
              </label>
              <label className="field">
                <span>Роль</span>
                <select
                  value={role}
                  onChange={(e) => {
                    setRole(e.target.value);
                    setPage(0);
                  }}
                >
                  <option value="">Все</option>
                  <option value="client">Клиенты</option>
                  <option value="coach">Тренеры</option>
                  <option value="admin">Администраторы</option>
                </select>
              </label>
            </div>
            {users.isLoading ? (
              <LoadingState />
            ) : users.error ? (
              <ErrorState
                message={(users.error as Error).message}
                retry={() => void users.refetch()}
              />
            ) : !users.data?.length ? (
              <EmptyState title="Пользователи не найдены" />
            ) : (
              <div className="list-grid top-gap">
                {users.data.map((item) => (
                  <article className="list-row" key={item.id}>
                    <div className="list-row__main">
                      <strong>
                        {item.full_name || item.username || `ID ${item.telegram_user_id}`}
                      </strong>
                      <span className="muted">
                        @{item.username || '—'} · Telegram {item.telegram_user_id}
                      </span>
                      <div>
                        <Badge>{roleLabel(item)}</Badge>{' '}
                        {!item.is_active && <Badge tone="badge-danger">Заблокирован</Badge>}
                      </div>
                    </div>
                    <div className="list-row__actions">
                      <select
                        aria-label="Роль"
                        value={item.role}
                        onChange={(e) =>
                          mutation.mutate({
                            path: `/api/v1/admin/users/${item.id}/role`,
                            method: 'PATCH',
                            body: { role: e.target.value },
                          })
                        }
                      >
                        <option value="client">Клиент</option>
                        <option value="coach">Тренер</option>
                        <option value="admin">Админ</option>
                      </select>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() =>
                          mutation.mutate({
                            path: `/api/v1/admin/users/${item.id}/status`,
                            method: 'PATCH',
                            body: { is_active: !item.is_active },
                          })
                        }
                      >
                        {item.is_active ? 'Заблокировать' : 'Разблокировать'}
                      </button>
                      <button
                        type="button"
                        className="btn-danger"
                        onClick={() => void removeUser(item)}
                      >
                        Удалить
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <Pagination
              page={page}
              hasNext={(users.data?.length ?? 0) === PAGE_SIZE}
              onPage={setPage}
            />
          </Card>
        )}

        {tab === 'payments' && (
          <Card title="Платежи">
            {payments.isLoading ? (
              <LoadingState />
            ) : payments.error ? (
              <ErrorState message={(payments.error as Error).message} />
            ) : !payments.data?.length ? (
              <EmptyState title="Платежей пока нет" />
            ) : (
              <div className="list-grid top-gap">
                {payments.data.map((item) => (
                  <article className="list-row" key={item.id}>
                    <div className="list-row__main">
                      <strong>{item.plan_title || item.plan_code || 'План'}</strong>
                      <span className="muted">
                        Telegram {item.telegram_user_id || '—'} ·{' '}
                        {new Date(item.created_at || '').toLocaleString('ru-RU')}
                      </span>
                    </div>
                    <div>
                      <strong>
                        {item.amount} {item.currency}
                      </strong>{' '}
                      <Badge>{item.status}</Badge>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <Pagination
              page={page}
              hasNext={(payments.data?.length ?? 0) === PAGE_SIZE}
              onPage={setPage}
            />
          </Card>
        )}

        {tab === 'notifications' && (
          <Card title="Уведомления">
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
                    <div className="list-row__main">
                      <strong>{item.title}</strong>
                      <span>{item.body}</span>
                      <span className="muted">
                        Пользователь {item.user_id} · {item.timezone}
                      </span>
                    </div>
                    <Badge>{item.status}</Badge>
                  </article>
                ))}
              </div>
            )}
            <Pagination
              page={page}
              hasNext={(notifications.data?.length ?? 0) === PAGE_SIZE}
              onPage={setPage}
            />
          </Card>
        )}

        {tab === 'templates' && (
          <Card title="Шаблоны программ">
            {templates.isLoading ? (
              <LoadingState />
            ) : templates.error ? (
              <ErrorState message={(templates.error as Error).message} />
            ) : !templates.data?.length ? (
              <EmptyState title="Шаблонов пока нет" />
            ) : (
              <div className="list-grid top-gap">
                {templates.data.map((item) => (
                  <article className="list-row" key={item.id}>
                    <div className="list-row__main">
                      <strong>{item.title}</strong>
                      <span className="muted">
                        {item.goal} · {item.level} · владелец {item.owner_user_id || 'общий'}
                      </span>
                    </div>
                    <button
                      className="btn-danger"
                      type="button"
                      onClick={async () => {
                        if (
                          await confirm({
                            title: 'Удалить шаблон?',
                            message: item.title,
                            confirmText: 'Удалить',
                          })
                        )
                          mutation.mutate({
                            path: `/api/v1/admin/templates/${item.id}`,
                            method: 'DELETE',
                          });
                      }}
                    >
                      Удалить
                    </button>
                  </article>
                ))}
              </div>
            )}
            <Pagination
              page={page}
              hasNext={(templates.data?.length ?? 0) === PAGE_SIZE}
              onPage={setPage}
            />
          </Card>
        )}
      </div>
    </AppShell>
  );
}
