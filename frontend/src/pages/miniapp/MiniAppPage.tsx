import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AppShell } from '../../app/AppShell';
import { useAuth } from '../../app/AuthProvider';
import { BillingPanel, NotificationsPanel } from '../../features/account/NotificationsBilling';
import { Diary } from '../../features/diary/Diary';
import { ExerciseCatalog } from '../../features/exercises/ExerciseCatalog';
import { NutritionForm } from '../../features/nutrition/NutritionForm';
import { CoachInvites } from '../../features/profile/CoachInvites';
import { ProfileForm } from '../../features/profile/ProfileForm';
import { ProgramBuilder } from '../../features/programs/ProgramBuilder';
import { TemplatesList } from '../../features/programs/TemplatesList';
import { TodayWorkout } from '../../features/workouts/TodayWorkout';
import { WorkoutHistory } from '../../features/workouts/WorkoutHistory';
import { api } from '../../shared/api/client';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card } from '../../shared/ui/common';

type Tab = 'today' | 'progress' | 'programs' | 'catalog' | 'nutrition' | 'profile';

export default function MiniAppPage() {
  const { user, logout } = useAuth();
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>('today');
  const launchActionsStarted = useRef(false);
  const role = user?.is_admin ? 'Администратор' : user?.is_coach ? 'Тренер' : 'Клиент';
  const profileReady = Boolean(
    user?.profile?.full_name && user.profile.goal && user.profile.level && user.profile.weight_kg,
  );

  useEffect(() => {
    if (!user || launchActionsStarted.current) return;
    launchActionsStarted.current = true;
    void (async () => {
      const params = new URLSearchParams(window.location.search);
      const startParam =
        window.Telegram?.WebApp?.initDataUnsafe?.start_param ||
        params.get('tgWebAppStartParam') ||
        params.get('startapp');
      if (startParam?.startsWith('trainer_')) {
        const consumedKey = `fit_claimed_${startParam}`;
        if (!sessionStorage.getItem(consumedKey)) {
          try {
            await api(
              `/api/v1/me/coach-invites/link/${encodeURIComponent(startParam.slice('trainer_'.length))}/claim`,
              { method: 'POST' },
            );
            sessionStorage.setItem(consumedKey, '1');
            await queryClient.invalidateQueries({ queryKey: ['coach-invites'] });
            setTab('profile');
            toast('Приглашение тренера открыто — подтвердите его в профиле');
          } catch (reason) {
            toast((reason as Error).message, 'error');
          }
        }
      }

      const checkoutId = params.get('checkout_id');
      if (checkoutId) {
        try {
          await api(`/api/v1/billing/mock/complete/${encodeURIComponent(checkoutId)}`, {
            method: 'POST',
          });
          params.delete('checkout_id');
          const query = params.toString();
          window.history.replaceState(
            {},
            '',
            `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`,
          );
          await queryClient.invalidateQueries({ queryKey: ['billing'] });
          setTab('nutrition');
          toast('Подписка активирована');
        } catch (reason) {
          toast((reason as Error).message, 'error');
        }
      }
    })();
  }, [queryClient, toast, user]);
  return (
    <AppShell>
      <div className="page-stack">
        <header className="card hero-card">
          <div>
            <span className="eyebrow">FitMiniApp</span>
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
            <div className="list-grid top-gap">
              <button className="list-row text-button" onClick={() => setTab('profile')}>
                <span>
                  <strong>{profileReady ? '✓' : '1.'} Заполнить профиль</strong>
                  <span className="muted">Цель, уровень и текущий вес</span>
                </span>
              </button>
              <button className="list-row text-button" onClick={() => setTab('programs')}>
                <span>
                  <strong>{user?.has_active_program ? '✓' : '2.'} Выбрать программу</strong>
                  <span className="muted">Создайте свою или назначьте шаблон</span>
                </span>
              </button>
              <button className="list-row text-button" onClick={() => setTab('today')}>
                <span>
                  <strong>{user?.has_workout_history ? '✓' : '3.'} Завершить тренировку</strong>
                  <span className="muted">Результат появится в разделе прогресса</span>
                </span>
              </button>
            </div>
          </Card>
        )}
        <div className="react-tabs" role="tablist">
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
              className={tab === key ? 'is-active' : 'secondary'}
              key={key}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
        {tab === 'today' && <TodayWorkout />}
        {tab === 'progress' && (
          <>
            <WorkoutHistory />
            <Diary />
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
          <>
            <NutritionForm initial={user?.profile?.kbju} />
            <NotificationsPanel />
            <BillingPanel />
          </>
        )}
        {tab === 'profile' && (
          <>
            <ProfileForm />
            <CoachInvites />
          </>
        )}
      </div>
    </AppShell>
  );
}
