import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { Diary } from '../../features/diary/Diary';
import { ExerciseCatalog } from '../../features/exercises/ExerciseCatalog';
import { NutritionForm } from '../../features/nutrition/NutritionForm';
import { ProgramBuilder } from '../../features/programs/ProgramBuilder';
import { api } from '../../shared/api/client';
import type { Client, CoachAssignedProgram, InviteLink } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { Redirect } from '../../shared/navigation/router';

type CoachTab = 'clients' | 'programs' | 'catalog';

function ClientProfileEditor({ client }: { client: Client }) {
  const queryClient = useQueryClient();
  const { toast } = useFeedback();
  const [form, setForm] = useState(client);
  const mutation = useMutation({
    mutationFn: () =>
      api(`/api/v1/coach/clients/${client.id}/profile`, {
        method: 'PATCH',
        body: {
          full_name: form.full_name,
          goal: form.goal || null,
          level: form.level || null,
          height_cm: form.height_cm || null,
          weight_kg: form.weight_kg || null,
          workouts_per_week: form.workouts_per_week || null,
          cardio_trainings_per_week: form.cardio_trainings_per_week || null,
        },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach', 'clients'] });
      toast('Профиль клиента сохранён');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  return (
    <Card title="Профиль клиента">
      <form
        className="stack top-gap"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="form-grid">
          <label className="field">
            <span>Имя</span>
            <input
              value={form.full_name || ''}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </label>
          <label className="field">
            <span>Цель</span>
            <select
              value={form.goal || ''}
              onChange={(e) => setForm({ ...form, goal: e.target.value })}
            >
              <option value="">Не указана</option>
              <option value="fat_loss">Похудение</option>
              <option value="muscle_gain">Набор</option>
              <option value="maintenance">Поддержание</option>
              <option value="recomposition">Рекомпозиция</option>
            </select>
          </label>
          <label className="field">
            <span>Уровень</span>
            <select
              value={form.level || ''}
              onChange={(e) => setForm({ ...form, level: e.target.value })}
            >
              <option value="">Не указан</option>
              <option value="beginner">Начальный</option>
              <option value="intermediate">Средний</option>
              <option value="advanced">Продвинутый</option>
            </select>
          </label>
          <label className="field">
            <span>Рост</span>
            <input
              type="number"
              value={form.height_cm || ''}
              onChange={(e) => setForm({ ...form, height_cm: Number(e.target.value) || null })}
            />
          </label>
          <label className="field">
            <span>Вес</span>
            <input
              type="number"
              step=".1"
              value={form.weight_kg || ''}
              onChange={(e) => setForm({ ...form, weight_kg: Number(e.target.value) || null })}
            />
          </label>
          <label className="field">
            <span>Тренировок</span>
            <input
              type="number"
              value={form.workouts_per_week || ''}
              onChange={(e) =>
                setForm({ ...form, workouts_per_week: Number(e.target.value) || null })
              }
            />
          </label>
        </div>
        <button disabled={mutation.isPending}>Сохранить профиль</button>
      </form>
    </Card>
  );
}

export default function CoachPage() {
  const { user } = useAuth();
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<CoachTab>('clients');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [clientInput, setClientInput] = useState('');
  const [clientMode, setClientMode] = useState<'client_code' | 'username' | 'telegram_id'>(
    'client_code',
  );
  const [programSearch, setProgramSearch] = useState('');
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const clients = useQuery({
    queryKey: ['coach', 'clients'],
    queryFn: () => api<Client[]>('/api/v1/coach/clients'),
  });
  const programs = useQuery({
    queryKey: ['coach', 'programs'],
    queryFn: () => api<CoachAssignedProgram[]>('/api/v1/coach/assigned-programs'),
    enabled: tab === 'programs',
  });
  const selected =
    clients.data?.find((item) => item.id === selectedId) ??
    clients.data?.find((item) => item.status === 'active') ??
    null;
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach'] });
      toast('Данные тренера обновлены');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const filteredPrograms = useMemo(() => {
    const q = programSearch.toLowerCase();
    return (programs.data ?? []).filter(
      (item) =>
        !q ||
        `${item.title} ${item.client_full_name} ${item.client_username}`.toLowerCase().includes(q),
    );
  }, [programs.data, programSearch]);
  if (!user?.is_coach && !user?.is_admin) return <Redirect to="/app" />;
  const addClient = () => {
    const body =
      clientMode === 'client_code'
        ? { client_code: clientInput, source: 'client_code' }
        : clientMode === 'username'
          ? { username: clientInput.replace(/^@/, ''), source: 'username_search' }
          : { telegram_user_id: Number(clientInput) };
    mutation.mutate({ path: '/api/v1/coach/clients', method: 'POST', body });
    setClientInput('');
  };
  const createInvite = async () => {
    try {
      const result = await api<InviteLink>('/api/v1/coach/invite-links', {
        method: 'POST',
        body: {},
      });
      const value = result.url || result.start_param;
      setInviteLink(value);
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(value);
        toast('Ссылка приглашения скопирована');
      } else {
        toast('Приглашение создано');
      }
    } catch (reason) {
      toast((reason as Error).message, 'error');
    }
  };

  return (
    <AppShell narrow>
      <div className="page-stack">
        <header className="card hero-card">
          <div>
            <span className="eyebrow">Рабочее пространство</span>
            <h1>Кабинет тренера</h1>
            <p className="muted">Клиенты, прогресс и назначения — в одном месте.</p>
          </div>
          <Badge>Тренер</Badge>
        </header>
        <div className="react-tabs react-tabs--coach" role="tablist" aria-label="Разделы тренера">
          {(
            [
              ['clients', 'Клиенты'],
              ['programs', 'Назначенные программы'],
              ['catalog', 'Упражнения'],
            ] as const
          ).map(([key, label]) => (
            <button
              type="button"
              role="tab"
              aria-selected={tab === key}
              className={tab === key ? 'is-active' : 'secondary'}
              onClick={() => setTab(key)}
              key={key}
            >
              {label}
            </button>
          ))}
        </div>
        {tab === 'clients' && (
          <>
            <Card
              title="Добавить клиента"
              actions={
                <button className="secondary" onClick={() => void createInvite()}>
                  Ссылка-приглашение
                </button>
              }
            >
              <form
                className="toolbar wrap top-gap"
                onSubmit={(e) => {
                  e.preventDefault();
                  addClient();
                }}
              >
                <select
                  value={clientMode}
                  onChange={(e) => setClientMode(e.target.value as typeof clientMode)}
                >
                  <option value="client_code">По коду</option>
                  <option value="username">По username</option>
                  <option value="telegram_id">По Telegram ID</option>
                </select>
                <input
                  value={clientInput}
                  onChange={(e) => setClientInput(e.target.value)}
                  placeholder={
                    clientMode === 'client_code'
                      ? 'Код клиента'
                      : clientMode === 'username'
                        ? '@username'
                        : 'Telegram ID'
                  }
                  required
                />
                <button disabled={mutation.isPending}>Добавить</button>
              </form>
              {inviteLink && (
                <label className="field top-gap">
                  <span>Последнее приглашение</span>
                  <input
                    readOnly
                    value={inviteLink}
                    onFocus={(event) => event.currentTarget.select()}
                  />
                </label>
              )}
            </Card>
            <Card title="Клиенты">
              {clients.isLoading ? (
                <LoadingState />
              ) : clients.error ? (
                <ErrorState message={(clients.error as Error).message} />
              ) : !clients.data?.length ? (
                <EmptyState title="Клиентов пока нет" />
              ) : (
                <div className="list-grid top-gap">
                  {clients.data.map((client) => (
                    <article
                      className={`list-row${selected?.id === client.id ? ' selected' : ''}`}
                      key={client.id || `invite-${client.invite_id}`}
                    >
                      <button
                        className="list-row__main text-button"
                        onClick={() => client.id && setSelectedId(client.id)}
                      >
                        <strong>
                          {client.full_name ||
                            client.username ||
                            client.telegram_user_id ||
                            'Приглашённый клиент'}
                        </strong>
                        <span className="muted">
                          {client.username ? `@${client.username}` : ''}{' '}
                          {client.telegram_user_id ? `· ${client.telegram_user_id}` : ''}
                        </span>
                        <Badge>{client.status === 'active' ? 'Активен' : 'Ожидает входа'}</Badge>
                      </button>
                      <button
                        className="btn-danger"
                        onClick={async () => {
                          if (
                            await confirm({
                              title: 'Удалить клиента?',
                              message: client.full_name || client.username || 'Приглашение',
                              confirmText: 'Удалить',
                            })
                          )
                            mutation.mutate({
                              path: client.id
                                ? `/api/v1/coach/clients/${client.id}`
                                : `/api/v1/coach/client-invites/id/${client.invite_id}`,
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
            </Card>
            {selected?.id && selected.status === 'active' && (
              <>
                <ClientProfileEditor key={`profile-${selected.id}`} client={selected} />
                <Diary clientId={selected.id} />
                <NutritionForm
                  key={`nutrition-${selected.id}`}
                  targetTelegramId={selected.telegram_user_id}
                  initial={selected.kbju}
                  onSaved={() => void clients.refetch()}
                />
                <ProgramBuilder
                  key={`program-${selected.id}`}
                  targetTelegramId={selected.telegram_user_id}
                  targetName={selected.full_name || selected.username}
                />
              </>
            )}
          </>
        )}
        {tab === 'programs' && (
          <Card title="Назначенные программы">
            <label className="field top-gap">
              <span>Поиск</span>
              <input
                type="search"
                value={programSearch}
                onChange={(e) => setProgramSearch(e.target.value)}
              />
            </label>
            {programs.isLoading ? (
              <LoadingState />
            ) : programs.error ? (
              <ErrorState message={(programs.error as Error).message} />
            ) : !filteredPrograms.length ? (
              <EmptyState title="Назначений не найдено" />
            ) : (
              <div className="list-grid top-gap">
                {filteredPrograms.map((item) => (
                  <article className="list-row" key={item.id}>
                    <div>
                      <strong>{item.title}</strong>
                      <p className="muted">
                        {item.client_full_name ||
                          item.client_username ||
                          item.client_telegram_user_id}{' '}
                        · {new Date(item.assigned_at).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                    <div>
                      <Badge>{item.is_active ? 'Активна' : 'Архив'}</Badge>
                      <p>
                        {item.workouts_completed}/{item.workouts_total} тренировок
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </Card>
        )}
        {tab === 'catalog' && (
          <ExerciseCatalog canCreate targetTelegramId={selected?.telegram_user_id} />
        )}
      </div>
    </AppShell>
  );
}
