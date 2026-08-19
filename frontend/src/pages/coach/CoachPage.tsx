import { useMemo, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { Diary } from '../../features/diary/Diary';
import { ClientAnalytics } from '../../features/coach/ClientAnalytics';
import { ExerciseCatalog } from '../../features/exercises/ExerciseCatalog';
import { NutritionForm } from '../../features/nutrition/NutritionForm';
import { ProgramBuilder } from '../../features/programs/ProgramBuilder';
import { AssignedProgramDetails } from '../../features/programs/AssignedProgramDetails';
import { api } from '../../shared/api/client';
import type { ApiSchemas, Client, CoachAssignedProgram, InviteLink } from '../../shared/api/types';
import { queryKeys } from '../../shared/queryKeys';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import {
  Badge,
  Card,
  DisclosureIcon,
  EmptyState,
  ErrorState,
  LoadingState,
} from '../../shared/ui/common';
import { AppLink, Redirect } from '../../shared/navigation/router';
import { LIVE_DATA_REFETCH_INTERVAL_MS } from '../../shared/sync';
import { usePersistentState } from '../../shared/storage';
import { coachClientProfileDraftStorageKey } from '../../shared/userScopedStorage';
import { handleTabKeyDown } from '../../shared/ui/tabs';
import { DateInput } from '../../shared/ui/PickerInput';
import {
  BodyPriorityPicker,
  isBodyPriorityComplete,
} from '../../features/profile/BodyPriorityPicker';

type CoachTab = 'clients' | 'programs' | 'catalog';

type ClientProfileDraft = Pick<
  Client,
  | 'full_name'
  | 'birth_date'
  | 'goal'
  | 'level'
  | 'height_cm'
  | 'weight_kg'
  | 'workouts_per_week'
  | 'cardio_trainings_per_week'
  | 'resting_heart_rate'
  | 'body_priority'
>;

function clientProfileDraft(client: Client): ClientProfileDraft {
  return {
    full_name: client.full_name,
    birth_date: client.birth_date,
    goal: client.goal,
    level: client.level,
    height_cm: client.height_cm,
    weight_kg: client.weight_kg,
    workouts_per_week: client.workouts_per_week,
    cardio_trainings_per_week: client.cardio_trainings_per_week,
    resting_heart_rate: client.resting_heart_rate,
    body_priority: client.body_priority,
  };
}

function clientProfileKey(client: Client): string {
  return JSON.stringify([
    client.id,
    client.full_name,
    client.birth_date,
    client.goal,
    client.level,
    client.height_cm,
    client.weight_kg,
    client.workouts_per_week,
    client.cardio_trainings_per_week,
    client.resting_heart_rate,
    client.body_priority,
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
        <DisclosureIcon />
      </summary>
      {expanded && <div className="coach-data-disclosure__body">{children}</div>}
    </details>
  );
}

function ClientProfileEditor({ client }: { client: Client }) {
  const queryClient = useQueryClient();
  const { toast } = useFeedback();
  const [form, setForm, clearDraft] = usePersistentState<ClientProfileDraft>(
    coachClientProfileDraftStorageKey(client.id),
    () => clientProfileDraft(client),
  );
  const validBirthDate = /^\d{4}-\d{2}-\d{2}$/.test(form.birth_date ?? '');
  const validRestingHeartRate =
    form.resting_heart_rate == null ||
    (form.resting_heart_rate >= 30 && form.resting_heart_rate <= 120);
  const heartRatePreview = useQuery({
    queryKey: [
      'heart-rate-preview',
      form.birth_date,
      form.resting_heart_rate,
      form.goal,
      'coach-client',
      client.id,
    ],
    queryFn: () =>
      api<ApiSchemas['HeartRatePreviewResponse']>('/api/v1/me/profile/heart-rates/preview', {
        method: 'POST',
        body: {
          birth_date: form.birth_date,
          resting_heart_rate: form.resting_heart_rate,
          goal: form.goal || null,
        },
      }),
    enabled: validBirthDate && validRestingHeartRate,
    retry: false,
  });
  const heartRate = heartRatePreview.data;
  const mutation = useMutation({
    mutationFn: () =>
      api<Client>(`/api/v1/coach/clients/${client.id}/profile`, {
        method: 'PATCH',
        body: {
          full_name: form.full_name,
          birth_date: form.birth_date ?? null,
          goal: form.goal || null,
          level: form.level || null,
          height_cm: form.height_cm ?? null,
          weight_kg: form.weight_kg ?? null,
          workouts_per_week: form.workouts_per_week ?? null,
          cardio_trainings_per_week: form.cardio_trainings_per_week ?? null,
          resting_heart_rate: form.resting_heart_rate ?? null,
          body_priority: form.body_priority ?? null,
        },
      }),
    onSuccess: async (updatedClient) => {
      clearDraft();
      queryClient.setQueryData<Client[]>(queryKeys.trainer.clients, (clients) =>
        clients?.map((item) => (item.id === updatedClient.id ? updatedClient : item)),
      );
      await queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clients });
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
        if (!isBodyPriorityComplete(form.body_priority)) {
          toast('Выберите хотя бы одну приоритетную мышечную группу', 'error');
          return;
        }
        mutation.mutate();
      }}
    >
      <div className="form-grid profile-form-grid">
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
          <span>Дата рождения</span>
          <DateInput
            controlClassName="coach-client-birth-date-control"
            value={form.birth_date ?? ''}
            onChange={(event) => setForm({ ...form, birth_date: event.target.value || null })}
          />
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
        <label className="field">
          <span>Средний пульс в покое, уд/мин</span>
          <input
            type="number"
            min="30"
            max="120"
            step="1"
            value={form.resting_heart_rate ?? ''}
            onChange={(e) => setForm({ ...form, resting_heart_rate: numberValue(e.target.value) })}
          />
        </label>
      </div>
      <BodyPriorityPicker
        value={form.body_priority}
        onChange={(body_priority) => setForm({ ...form, body_priority })}
      />
      {heartRate && (
        <div className="auth-notice stack">
          <strong>Пульсовые зоны · максимум {heartRate.estimated_max_heart_rate} уд/мин</strong>
          {heartRate.recommended_cardio_range && (
            <span>
              Рекомендация для кардио: {heartRate.recommended_cardio_range.min_bpm}–
              {heartRate.recommended_cardio_range.max_bpm} уд/мин
            </span>
          )}
          <div className="toolbar wrap">
            {heartRate.heart_rate_zones.map((zone) => (
              <Badge key={zone.zone}>
                Z{zone.zone}: {zone.min_bpm}–{zone.max_bpm}
              </Badge>
            ))}
          </div>
        </div>
      )}
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
  const [focusedProgramId, setFocusedProgramId] = useState<number | null>(null);
  const [inviteLink, setInviteLink] = useState<InviteLink | null>(null);
  const [inviteCreating, setInviteCreating] = useState(false);
  const clients = useQuery({
    queryKey: queryKeys.trainer.clients,
    queryFn: () => api<Client[]>('/api/v1/coach/clients'),
    refetchInterval: LIVE_DATA_REFETCH_INTERVAL_MS,
    refetchOnWindowFocus: true,
  });
  const programs = useQuery({
    queryKey: ['coach', 'programs'],
    queryFn: () => api<CoachAssignedProgram[]>('/api/v1/coach/assigned-programs'),
    enabled: true,
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
  const selectedPrograms = useMemo(
    () => (programs.data ?? []).filter((item) => item.client_id === selected?.id),
    [programs.data, selected?.id],
  );
  if (!user?.is_coach) return <Redirect to="/app" />;
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
      if (result.web_url || result.url) await copyInvite(result.web_url || result.url || '');
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
                    {inviteLink.web_url && (
                      <label className="field">
                        <span>Универсальная ссылка — для браузера и Telegram</span>
                        <input
                          readOnly
                          value={inviteLink.web_url}
                          onFocus={(event) => event.currentTarget.select()}
                        />
                      </label>
                    )}
                    {inviteLink.telegram_url && (
                      <label className="field">
                        <span>Открыть сразу внутри Telegram</span>
                        <input
                          readOnly
                          value={inviteLink.telegram_url}
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
                            inviteLink.web_url ||
                              inviteLink.url ||
                              inviteLink.code ||
                              inviteLink.start_param,
                          )
                        }
                      >
                        Копировать
                      </button>
                      {inviteLink.web_url && typeof navigator.share === 'function' && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() =>
                            void navigator
                              .share({
                                title: 'Приглашение тренера',
                                text: 'Откройте Your Fitness Coach и подтвердите подключение к тренеру.',
                                url: inviteLink.web_url,
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
                    <Diary
                      key={`diary-${selected.id}`}
                      clientId={selected.id}
                      timeZone={selected.timezone}
                    />
                  </ClientDataSection>
                  <ClientDataSection title="Питание" description="Расчёт и целевые КБЖУ">
                    <NutritionForm
                      key={JSON.stringify([selected.id, selected.kbju])}
                      clientId={selected.id}
                      targetTelegramId={selected.telegram_user_id}
                      initial={selected.kbju}
                    />
                  </ClientDataSection>
                  <ClientDataSection
                    key={`program-${selected.id}-${focusedProgramId ?? 'none'}`}
                    title="Программа тренировок"
                    description="Текущий план клиента и новое назначение"
                    open={selectedPrograms.some((item) => item.id === focusedProgramId)}
                  >
                    <div className="coach-client-programs">
                      <div className="coach-client-programs__head">
                        <div>
                          <strong>Программы клиента</strong>
                          <span>Контекст клиента сохраняется при переходе к каталогу.</span>
                        </div>
                        {!!selectedPrograms.some((item) => item.is_active) && (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => setTab('catalog')}
                          >
                            Добавить упражнение
                          </button>
                        )}
                      </div>
                      {!selectedPrograms.length ? (
                        <EmptyState
                          title="У клиента ещё нет назначенной вами программы"
                          text="Создайте и назначьте её в форме ниже."
                        />
                      ) : (
                        selectedPrograms.map((program) => (
                          <article
                            className={`coach-client-program${program.id === focusedProgramId ? ' is-focused' : ''}`}
                            key={program.id}
                          >
                            <div>
                              <span className="eyebrow">
                                {program.is_active ? 'Текущая программа клиента' : 'Архив клиента'}
                              </span>
                              <strong>{program.title}</strong>
                              <small>
                                {program.workouts_completed} из {program.workouts_total} тренировок
                                выполнено
                              </small>
                            </div>
                            <Badge tone={program.is_active ? 'success' : 'neutral'}>
                              {program.is_active ? 'Активна' : 'Архив'}
                            </Badge>
                            {program.is_active && (
                              <AssignedProgramDetails
                                programId={program.id}
                                currentRevisionNumber={program.current_revision_number}
                                startDate={program.start_date}
                                durationWeeks={program.duration_weeks}
                              />
                            )}
                          </article>
                        ))
                      )}
                    </div>
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
            <Card
              title="Программы клиентов"
              description="Здесь только назначения вашим клиентам. Собственные программы хранятся в личном плане."
              actions={
                <AppLink className="button-link secondary-link" to="/app?section=programs">
                  Мои программы
                </AppLink>
              }
            >
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
                    <article className="coach-program-row" key={item.id}>
                      <div className="coach-program-row__main">
                        <span className="eyebrow">Программа клиента</span>
                        <strong>{item.title}</strong>
                        <p>
                          {item.client_full_name ||
                            item.client_username ||
                            item.client_telegram_user_id}
                        </p>
                        <small>
                          Назначена {new Date(item.assigned_at).toLocaleDateString('ru-RU')}
                          {item.next_workout_date
                            ? ` · следующая ${new Date(`${item.next_workout_date}T12:00:00`).toLocaleDateString('ru-RU')}`
                            : ''}
                        </small>
                      </div>
                      <div className="coach-program-row__progress">
                        <Badge tone={item.is_active ? 'success' : 'neutral'}>
                          {item.is_active ? 'Активна' : 'Архив'}
                        </Badge>
                        <strong>
                          {item.workouts_completed} / {item.workouts_total}
                        </strong>
                        <span>тренировок выполнено</span>
                      </div>
                      <div className="coach-program-row__actions">
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedId(item.client_id);
                            setFocusedProgramId(item.id);
                            setTab('clients');
                          }}
                        >
                          Открыть клиента
                        </button>
                        {item.is_active && (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => {
                              setSelectedId(item.client_id);
                              setTab('catalog');
                            }}
                          >
                            Добавить упражнение
                          </button>
                        )}
                      </div>
                      {item.is_active && (
                        <AssignedProgramDetails
                          programId={item.id}
                          currentRevisionNumber={item.current_revision_number}
                          startDate={item.start_date}
                          durationWeeks={item.duration_weeks}
                        />
                      )}
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
