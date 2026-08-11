import { useState } from 'react';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { NotificationsPanel } from '../../features/account/NotificationsPanel';
import { AccountPrivacy } from '../../features/account/AccountPrivacy';
import { Diary } from '../../features/diary/Diary';
import { ExerciseCatalog } from '../../features/exercises/ExerciseCatalog';
import { NutritionForm } from '../../features/nutrition/NutritionForm';
import { CoachInvites } from '../../features/profile/CoachInvites';
import { ProfileForm } from '../../features/profile/ProfileForm';
import { ProgramBuilder } from '../../features/programs/ProgramBuilder';
import { TemplatesList } from '../../features/programs/TemplatesList';
import { TodayWorkout } from '../../features/workouts/TodayWorkout';
import { ProgressSchedule } from '../../features/workouts/ProgressSchedule';
import {
  WorkoutHistory,
  type WorkoutNavigationTarget,
} from '../../features/workouts/WorkoutHistory';
import { Badge, Card } from '../../shared/ui/common';
import { handleTabKeyDown } from '../../shared/ui/tabs';

type Tab = 'today' | 'progress' | 'programs' | 'catalog' | 'nutrition' | 'profile';

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
  const [initialInviteToken] = useState(launchInviteToken);
  const [tab, setTab] = useState<Tab>(initialInviteToken ? 'profile' : 'today');
  const [focusedWorkout, setFocusedWorkout] = useState<{
    id: number;
    target: WorkoutNavigationTarget;
  } | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(initialInviteToken);
  const role = user?.is_admin ? 'Администратор' : user?.is_coach ? 'Тренер' : 'Клиент';
  const profileReady = Boolean(
    user?.profile?.full_name &&
    user.profile.birth_date &&
    user.profile.goal &&
    user.profile.level &&
    user.profile.weight_kg,
  );
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
            <button className="secondary" onClick={() => void logout()}>
              Выйти
            </button>
          </div>
        </header>
        {(!profileReady || !user?.has_active_program || !user?.has_workout_history) && (
          <Card title="План запуска" description="Три шага до регулярных тренировок">
            <div className="onboarding-actions top-gap">
              <button className="onboarding-action" onClick={() => setTab('profile')}>
                <span className={`onboarding-action__mark${profileReady ? ' is-done' : ''}`}>
                  {profileReady ? '✓' : '1'}
                </span>
                <span className="onboarding-action__copy">
                  <strong>Заполнить профиль</strong>
                  <span>Дата рождения, цель, уровень и текущий вес</span>
                </span>
                <span className="onboarding-action__arrow" aria-hidden="true">
                  ›
                </span>
              </button>
              <button className="onboarding-action" onClick={() => setTab('programs')}>
                <span
                  className={`onboarding-action__mark${user?.has_active_program ? ' is-done' : ''}`}
                >
                  {user?.has_active_program ? '✓' : '2'}
                </span>
                <span className="onboarding-action__copy">
                  <strong>Выбрать программу</strong>
                  <span>Создайте свою или назначьте шаблон</span>
                </span>
                <span className="onboarding-action__arrow" aria-hidden="true">
                  ›
                </span>
              </button>
              <button className="onboarding-action" onClick={() => setTab('today')}>
                <span
                  className={`onboarding-action__mark${user?.has_workout_history ? ' is-done' : ''}`}
                >
                  {user?.has_workout_history ? '✓' : '3'}
                </span>
                <span className="onboarding-action__copy">
                  <strong>Завершить тренировку</strong>
                  <span>Результат появится в разделе прогресса</span>
                </span>
                <span className="onboarding-action__arrow" aria-hidden="true">
                  ›
                </span>
              </button>
            </div>
          </Card>
        )}
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
          {tab === 'today' && <TodayWorkout />}
          {tab === 'progress' && (
            <>
              <ProgressSchedule
                timeZone={user?.profile?.timezone}
                focusedWorkoutId={focusedWorkout?.target === 'schedule' ? focusedWorkout.id : null}
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
        </section>
      </div>
    </AppShell>
  );
}
