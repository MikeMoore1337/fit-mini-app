import { lazy, Suspense, useEffect, useState } from 'react';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { TelegramLinkPrompt } from '../../features/account/TelegramLinkPrompt';
import { TodayWorkout } from '../../features/workouts/TodayWorkout';
import type { WorkoutNavigationTarget } from '../../features/workouts/WorkoutHistory';
import { Badge } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { handleTabKeyDown } from '../../shared/ui/tabs';

const NotificationsPanel = lazy(() =>
  import('../../features/account/NotificationsPanel').then((module) => ({
    default: module.NotificationsPanel,
  })),
);
const AccountPrivacy = lazy(() =>
  import('../../features/account/AccountPrivacy').then((module) => ({
    default: module.AccountPrivacy,
  })),
);
const Diary = lazy(() =>
  import('../../features/diary/Diary').then((module) => ({ default: module.Diary })),
);
const ExerciseCatalog = lazy(() =>
  import('../../features/exercises/ExerciseCatalog').then((module) => ({
    default: module.ExerciseCatalog,
  })),
);
const NutritionForm = lazy(() =>
  import('../../features/nutrition/NutritionForm').then((module) => ({
    default: module.NutritionForm,
  })),
);
const CoachInvites = lazy(() =>
  import('../../features/profile/CoachInvites').then((module) => ({
    default: module.CoachInvites,
  })),
);
const CoachRoleApplicationCard = lazy(() =>
  import('../../features/profile/CoachRoleApplication').then((module) => ({
    default: module.CoachRoleApplicationCard,
  })),
);
const ProfileForm = lazy(() =>
  import('../../features/profile/ProfileForm').then((module) => ({
    default: module.ProfileForm,
  })),
);
const ProgramBuilder = lazy(() =>
  import('../../features/programs/ProgramBuilder').then((module) => ({
    default: module.ProgramBuilder,
  })),
);
const TemplatesList = lazy(() =>
  import('../../features/programs/TemplatesList').then((module) => ({
    default: module.TemplatesList,
  })),
);
const ProgressSchedule = lazy(() =>
  import('../../features/workouts/ProgressSchedule').then((module) => ({
    default: module.ProgressSchedule,
  })),
);
const WorkoutHistory = lazy(() =>
  import('../../features/workouts/WorkoutHistory').then((module) => ({
    default: module.WorkoutHistory,
  })),
);

type Tab = 'today' | 'progress' | 'programs' | 'catalog' | 'nutrition' | 'profile';

const tabs: ReadonlyArray<Tab> = [
  'today',
  'progress',
  'programs',
  'catalog',
  'nutrition',
  'profile',
];

function launchInviteToken(): string | null {
  const params = new URLSearchParams(window.location.search);
  const startParam =
    window.Telegram?.WebApp?.initDataUnsafe?.start_param ||
    params.get('tgWebAppStartParam') ||
    params.get('startapp');
  return startParam?.startsWith('trainer_') ? startParam.slice('trainer_'.length) : null;
}

export default function MiniAppPage() {
  const { user, logout, reloadUser } = useAuth();
  const { toast } = useFeedback();
  const [initialInviteToken] = useState(launchInviteToken);
  const [tab, setTab] = useState<Tab>(() => {
    const params = new URLSearchParams(window.location.search);
    const requestedSection = params.get('section');
    if (requestedSection && tabs.includes(requestedSection as Tab)) return requestedSection as Tab;
    return initialInviteToken || params.has('auth_linked') || params.has('auth_error')
      ? 'profile'
      : 'today';
  });
  const [focusedWorkout, setFocusedWorkout] = useState<{
    id: number;
    target: WorkoutNavigationTarget;
  } | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(initialInviteToken);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const linkedProvider = params.get('auth_linked');
    const authError = params.get('auth_error');
    if (!linkedProvider && !authError) return;

    const labels: Record<string, string> = {
      google: 'Google',
      yandex: 'Яндекс',
      vk: 'VK ID',
      apple: 'Apple',
    };
    if (linkedProvider) {
      toast(`${labels[linkedProvider] ?? linkedProvider} привязан к аккаунту`);
    } else if (authError === 'conflict') {
      toast('Этот способ входа уже привязан к другому аккаунту', 'error');
    } else if (authError === 'denied') {
      toast('Авторизация отменена или не разрешена', 'error');
    } else if (authError === 'invalid_state') {
      toast('Ссылка авторизации недействительна или устарела', 'error');
    } else if (authError === 'blocked') {
      toast('Аккаунт заблокирован', 'error');
    } else if (authError === 'unavailable') {
      toast('Этот способ входа временно недоступен', 'error');
    } else {
      toast('Не удалось связаться с сервисом авторизации', 'error');
    }

    params.delete('auth_linked');
    params.delete('auth_error');
    const query = params.toString();
    window.history.replaceState(
      null,
      '',
      `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`,
    );
  }, [toast]);
  const role = user?.is_admin ? 'Администратор' : user?.is_coach ? 'Тренер' : 'Клиент';
  const profileFormKey = JSON.stringify([
    user?.profile?.full_name,
    user?.profile?.birth_date,
    user?.profile?.goal,
    user?.profile?.level,
    user?.profile?.height_cm,
    user?.profile?.weight_kg,
    user?.profile?.workouts_per_week,
    user?.profile?.cardio_trainings_per_week,
    user?.profile?.timezone,
  ]);

  return (
    <AppShell>
      <div className="page-stack">
        <header className="card hero-card">
          <div>
            <span className="eyebrow">Your Fitness Coach</span>
            <h1>{user?.profile?.full_name || user?.first_name || 'Мой фитнес'}</h1>
            <p className="muted">Тренировки, питание и прогресс в одном месте.</p>
          </div>
          <div className="hero-card__meta">
            <Badge>{role}</Badge>
            <button className="secondary miniapp-hero-logout" onClick={() => void logout()}>
              Выйти
            </button>
          </div>
        </header>
        <TelegramLinkPrompt />
        <div className="react-tabs react-tabs--mini" role="tablist" aria-label="Разделы приложения">
          {(
            [
              ['today', 'Сегодня'],
              ['progress', 'Прогресс'],
              ['programs', 'Программы'],
              ['catalog', 'Упражнения'],
              ['nutrition', 'Питание'],
              ['profile', 'Профиль'],
            ] as const
          ).map(([key, label]) => (
            <button
              role="tab"
              aria-selected={tab === key}
              id={`mini-tab-${key}`}
              aria-controls={`mini-panel-${key}`}
              tabIndex={tab === key ? 0 : -1}
              className={tab === key ? 'is-active' : 'secondary'}
              key={key}
              onClick={() => setTab(key)}
              onKeyDown={handleTabKeyDown}
            >
              {label}
            </button>
          ))}
        </div>
        <section
          className="page-stack"
          role="tabpanel"
          id={`mini-panel-${tab}`}
          aria-labelledby={`mini-tab-${tab}`}
        >
          <Suspense
            fallback={
              <p className="muted" role="status">
                Загружаем раздел…
              </p>
            }
          >
            {tab === 'today' && <TodayWorkout />}
            {tab === 'progress' && (
              <>
                <ProgressSchedule
                  timeZone={user?.profile?.timezone}
                  focusedWorkoutId={
                    focusedWorkout?.target === 'schedule' ? focusedWorkout.id : null
                  }
                />
                <WorkoutHistory
                  timeZone={user?.profile?.timezone}
                  focusedWorkoutId={focusedWorkout?.target === 'history' ? focusedWorkout.id : null}
                  onWorkoutSelect={(id, target) => setFocusedWorkout({ id, target })}
                />
                <Diary onSaved={async () => void (await reloadUser())} />
              </>
            )}
            {tab === 'programs' && (
              <>
                <TemplatesList />
                <ProgramBuilder />
              </>
            )}
            {tab === 'catalog' && (
              <ExerciseCatalog canCreate={Boolean(user?.is_coach || user?.is_admin)} />
            )}
            {tab === 'nutrition' && (
              <NutritionForm
                key={JSON.stringify(user?.profile?.kbju ?? null)}
                initial={user?.profile?.kbju}
                onSaved={async () => void (await reloadUser())}
              />
            )}
            {tab === 'profile' && (
              <>
                <ProfileForm key={profileFormKey} />
                <CoachRoleApplicationCard />
                <CoachInvites
                  initialToken={inviteToken}
                  onInitialTokenHandled={() => setInviteToken(null)}
                />
                <NotificationsPanel
                  onNavigate={(destination) => {
                    setFocusedWorkout(null);
                    setTab(destination);
                  }}
                />
                <AccountPrivacy />
              </>
            )}
          </Suspense>
        </section>
      </div>
    </AppShell>
  );
}
