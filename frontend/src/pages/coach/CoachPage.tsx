import { useMemo, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { Diary } from '../../features/diary/Diary';
import { ClientAnalytics } from '../../features/coach/ClientAnalytics';
import { ExerciseCatalog } from '../../features/exercises/ExerciseCatalog';
import { NutritionForm } from '../../features/nutrition/NutritionForm';
import { ProgramBuilder } from '../../features/programs/ProgramBuilder';
import { api } from '../../shared/api/client';
import type { Client, CoachAssignedProgram, InviteLink } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { Redirect } from '../../shared/navigation/router';
import { LIVE_DATA_REFETCH_INTERVAL_MS } from '../../shared/sync';
import { usePersistentState } from '../../shared/storage';
import { handleTabKeyDown } from '../../shared/ui/tabs';

type CoachTab = 'clients' | 'programs' | 'catalog';

function clientProfileKey(client: Client): string {
  return JSON.stringify([
    client.id,
    client.full_name,
    client.goal,
    client.level,
    client.height_cm,
    client.weight_kg,
    client.workouts_per_week,
    client.cardio_trainings_per_week,
  ]);
}

function ClientDataSection({
  title,
  description,
  children,
  open = false,
}: {
  title: string;
  description: string;
  children: ReactNode;
  open?: boolean;
}) {
  const [expanded, setExpanded] = useState(open);
  return (
    <details
      className="coach-data-disclosure"
      open={expanded}
      onToggle={(event) => setExpanded(event.currentTarget.open)}
    >
      <summary>
        <span>
          <strong>{title}</strong>
          <small>{description}</small>
        </span>
      </summary>
      {expanded && <div className="coach-data-disclosure__body">{children}</div>}
    </details>
  );
}

function ClientProfileEditor({ client }: { client: Client }) {
  const queryClient = useQueryClient();
  const { toast } = useFeedback();
  const [form, setForm, clearDraft] = usePersistentState(
    `fit_coach_client_profile_draft_${client.id}`,
    client,
  );
  const mutation = useMutation({
    mutationFn: () =>
      api<Client>(`/api/v1/coach/clients/${client.id}/profile`, {
        method: 'PATCH',
        body: {
          full_name: form.full_name,
          goal: form.goal || null,
          level: form.level || null,
          height_cm: form.height_cm ?? null,
          weight_kg: form.weight_kg ?? null,
          workouts_per_week: form.workouts_per_week ?? null,
          cardio_trainings_per_week: form.cardio_trainings_per_week ?? null,
        },
      }),
    onSuccess: async (updatedClient) => {
      clearDraft();
      queryClient.setQueryData<Client[]>(['coach', 'clients'], (clients) =>
        clients?.map((item) => (item.id === updatedClient.id ? updatedClient : item)),
      );
      await queryClient.invalidateQueries({ queryKey: ['coach', 'clients'] });
      toast('Профиль клиента сохранён');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const numberValue = (value: string) => (value === '' ? null : Number(value));
  return (
    <form
      className="stack"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <div className="form-grid">
        <label className="field">
          <span>Имя у тренера</span>
          <input
            value={form.full_name || ''}
            maxLength={128}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
          <small className="field-hint">Это имя видите только вы.</small>
        </label>
        <label className="field">
          <span>Цель</span>
          <select
            value={form.goal || ''}
            required
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
          >
            <option value="" disabled>
              Выберите цель
            </option>
            <option value="fat_loss">Похудение</option>
            <option value="muscle_gain">Набор мышц</option>
            <option value="maintenance">Поддержание</option>
            <option value="recomposition">Рекомпозиция</option>
          </select>
        </label>
        <label className="field">
          <span>Уровень</span>
          <select
            value={form.level || ''}
            required
            onChange={(e) => setForm({ ...form, level: e.target.value })}
          >
            <option value="" disabled>
              Выберите уровень
            </option>
            <option value="beginner">Начальный</option>
            <option value="intermediate">Средний</option>
            <option value="advanced">Продвинутый</option>
          </select>
        </label>
        <label className="field">
          <span>Рост, см</span>
          <input
            type="number"
            min="100"
            max="250"
            value={form.height_cm ?? ''}
            onChange={(e) => setForm({ ...form, height_cm: numberValue(e.target.value) })}
          />
        </label>
        <label className="field">
          <span>Вес, кг</span>
          <input
            type="number"
            min="20"
            max="350"
            step="0.1"
            value={form.weight_kg ?? ''}
            onChange={(e) => setForm({ ...form, weight_kg: numberValue(e.target.value) })}
          />
        </label>
        <label className="field">
          <span>Силовых в неделю</span>
          <input
            type="number"
            min="0"
            max="14"
            value={form.workouts_per_week ?? ''}
            onChange={(e) => setForm({ ...form, workouts_per_week: numberValue(e.target.value) })}
          />
        </label>
        <label className="field">
          <span>Кардио в неделю</span>
          <input
            type="number"
            min="0"
            max="14"
            value={form.cardio_trainings_per_week ?? ''}
            onChange={(e) =>
              setForm({ ...form, cardio_trainings_per_week: numberValue(e.target.value) })
            }
          />
        </label>
      </div>
      <button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Сохраняем…' : 'Сохранить профиль'}
      </button>
    </form>
  );
}

export default function CoachPage() {
  const { user } = useAuth();
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<CoachTab>('clients');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [programSearch, setProgramSearch] = useState('');
  const [inviteLink, setInviteLink] = useState<InviteLink | null>(null);
  const [inviteCreating, setInviteCreating] = useState(false);
  const clients = useQuery({
    queryKey: ['coach', 'clients'],
    queryFn: () => api<Client[]>('/api/v1/coach/clients'),
    refetchInterval: LIVE_DATA_REFETCH_INTERVAL_MS,
    refetchOnWindowFocus: true,
  });
  const programs = useQuery({
    queryKey: ['coach', 'programs'],
    queryFn: () => api<CoachAssignedProgram[]>('/api/v1/coach/assigned-programs'),
    enabled: tab === 'programs',
    refetchInterval: tab === 'programs' ? LIVE_DATA_REFETCH_INTERVAL_MS : false,
    refetchOnWindowFocus: true,
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
  const copyInvite = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      toast('Приглашение скопировано');
    } catch {
      toast('Не удалось скопировать автоматически — выделите значение вручную.', 'error');
    }
  };
  const createInvite = async () => {
    setInviteCreating(true);
    try {
      const result = await api<InviteLink>('/api/v1/coach/invite-links', {
        method: 'POST',
      });
      setInviteLink(result);
      if (result.url) await copyInvite(result.url);
      else toast('Приглашение создано');
    } catch (reason) {
      toast((reason as Error).message, 'error');
    } finally {
      setInviteCreating(false);
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
              id={`coach-tab-${key}`}
              aria-controls={`coach-panel-${key}`}
              tabIndex={tab === key ? 0 : -1}
              className={tab === key ? 'is-active' : 'secondary'}
              onClick={() => setTab(key)}
              onKeyDown={handleTabKeyDown}
              key={key}
            >
              {label}
            </button>
          ))}
        </div>
        <section
          className="page-stack"
          role="tabpanel"
          id={`coach-panel-${tab}`}
          aria-labelledby={`coach-tab-${tab}`}
        >
          {tab === 'clients' && (
            <>
              <Card
                title="Пригласить клиента"
                description="Отправьте персональную ссылку. Клиент сначала увидит ваше имя и сам подтвердит подключение."
                actions={
                  <button
                    className="secondary"
                    disabled={inviteCreating}
                    onClick={() => void createInvite()}
                  >
                    {inviteCreating ? 'Создаём…' : 'Создать приглашение'}
                  </button>
                }
              >
                {inviteLink && (
                  <div className="auth-notice stack top-gap">
                    {inviteLink.url && (
                      <label className="field">
                        <span>Ссылка</span>
                        <input
                          readOnly
                          value={inviteLink.url}
                          onFocus={(event) => event.currentTarget.select()}
                        />
                      </label>
                    )}
                    {inviteLink.code && (
                      <label className="field">
                        <span>Код приглашения — если ссылка не открывается</span>
                        <input
                          readOnly
                          value={inviteLink.code}
                          onFocus={(event) => event.currentTarget.select()}
                        />
                      </label>
                    )}
                    <p className="muted">
                      Действует до {new Date(inviteLink.expires_at).toLocaleString('ru-RU')}.
                    </p>
                    <div className="toolbar wrap">
                      <button
                        type="button"
                        onClick={() =>
                          void copyInvite(
                            inviteLink.url || inviteLink.code || inviteLink.start_param,
                          )
                        }
                      >
                        Копировать
                      </button>
                      {inviteLink.url && typeof navigator.share === 'function' && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() =>
                            void navigator
                              .share({
                                title: 'Приглашение тренера',
                                text: 'Откройте FitMiniApp и подтвердите подключение к тренеру.',
                                url: inviteLink.url ?? undefined,
                              })
                              .catch(() => undefined)
                          }
                        >
                          Поделиться
                        </button>
                      )}
                    </div>
                  </div>
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
                        className={`list-row coach-client-row${selected?.id === client.id ? ' selected' : ''}`}
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
                  <ClientDataSection
                    title="Профиль клиента"
                    description="Анкета, цель и параметры"
                    open
                  >
                    <ClientProfileEditor key={clientProfileKey(selected)} client={selected} />
                  </ClientDataSection>
                  <ClientDataSection
                    title="Прогресс и замеры"
                    description="Соблюдение плана, рекорды и лента тренировок"
                  >
                    <ClientAnalytics clientId={selected.id} />
                    <Diary key={`diary-${selected.id}`} clientId={selected.id} />
                  </ClientDataSection>
                  <ClientDataSection title="Питание" description="Расчёт и целевые КБЖУ">
                    <NutritionForm
                      key={JSON.stringify([selected.id, selected.kbju])}
                      targetTelegramId={selected.telegram_user_id}
                      initial={selected.kbju}
                      onSaved={() => void clients.refetch()}
                    />
                  </ClientDataSection>
                  <ClientDataSection
                    title="Программа тренировок"
                    description="Создание и назначение программы"
                  >
                    <ProgramBuilder
                      key={`program-${selected.id}`}
                      targetTelegramId={selected.telegram_user_id}
                      targetName={selected.full_name || selected.username}
                    />
                  </ClientDataSection>
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
            <ExerciseCatalog canCreate canAssign targetTelegramId={selected?.telegram_user_id} />
          )}
        </section>
      </div>
    </AppShell>
  );
}
