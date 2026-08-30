import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NavigationProvider } from '../../../../src/shared/navigation/router';
import DemoPage from '../../../../src/pages/demo/DemoPage';
import {
  DemoApiError,
  type DemoSelfTrainingState,
  type DemoSessionSnapshot,
} from '../../../../src/features/demo/demoApi';

const mocks = vi.hoisted(() => ({
  apply: vi.fn(),
  clearAll: vi.fn(),
  clear: vi.fn(),
  load: vi.fn(),
  reset: vi.fn(),
  start: vi.fn(),
  track: vi.fn(),
}));

vi.mock('../../../../src/features/demo/demoApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../../src/features/demo/demoApi')>();
  return {
    ...actual,
    applyDemoAction: mocks.apply,
    clearAllDemoSessions: mocks.clearAll,
    clearDemoSession: mocks.clear,
    loadDemoSession: mocks.load,
    resetDemoSession: mocks.reset,
    startDemoSession: mocks.start,
  };
});

vi.mock('../../../../src/shared/analytics/productEvents', () => ({
  productEventSurface: () => 'mobile_web',
  trackProductEvent: mocks.track,
}));

Object.defineProperty(Element.prototype, 'scrollIntoView', {
  configurable: true,
  value: vi.fn(),
});
Object.defineProperty(window, 'scrollTo', {
  configurable: true,
  value: vi.fn(),
});

const trainingSnapshot: DemoSessionSnapshot = {
  capability: 'demo',
  scenario: 'self_training',
  fixture_version: 'demo-curated-v1',
  revision: 1,
  expires_at: '2026-08-24T12:30:00Z',
  cabinet: {
    today: {
      title: 'Верх тела · уверенный старт',
      summary: 'Подготовленная тренировка на сегодня',
      status_label: 'Остался один подход',
      completed_days: 2,
      planned_days: 4,
    },
    nutrition: {
      calories: 1580,
      calorie_target: 2150,
      protein_g: 104,
      protein_target_g: 145,
      meals_logged: 3,
      item_added: true,
      recent_item: { name: 'Творог с ягодами', serving: '220 г', calories: 286, protein_g: 31 },
    },
    progress: {
      workouts_completed: 11,
      latest_volume_kg: 6220,
      volume_change_percent: 4.2,
      nutrition_days_logged: 5,
      nutrition_completion_percent: 73,
      summary: 'Динамика обновится после завершения тренировки.',
    },
    trainer: null,
    meaningful_action_completed: false,
    conversion_title: 'Сохраните историю тренировок',
  },
  state: {
    kind: 'self_training',
    screen: 'today',
    workout_title: 'Верх тела · уверенный старт',
    workout_subtitle: 'Подготовленная тренировка на сегодня',
    completed_sets: 2,
    total_sets: 3,
    exercises: [
      {
        name: 'Жим гантелей лёжа с контролируемой паузой',
        prescription: '3 × 10',
        status: 'current',
      },
    ],
    duration_minutes: 0,
    total_volume_kg: 0,
    progress_change_percent: 0,
  },
};

function renderPage(path = '/demo') {
  window.history.replaceState({}, '', path);
  return render(
    <NavigationProvider>
      <DemoPage />
    </NavigationProvider>,
  );
}

describe('DemoPage', () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.load.mockResolvedValue(trainingSnapshot);
    mocks.reset.mockResolvedValue(trainingSnapshot);
    mocks.start.mockResolvedValue(trainingSnapshot);
  });

  it('не даёт переключить scenario, пока recovery response ещё не привязан к экрану', () => {
    mocks.load.mockReturnValue(new Promise(() => undefined));
    renderPage();

    expect(screen.getByRole('button', { name: /Тренировка/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Питание/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Тренеру/ })).toBeDisabled();
  });

  it('keeps a persistent demo boundary and runs the prepared training action', async () => {
    const activeSnapshot: DemoSessionSnapshot = {
      ...trainingSnapshot,
      revision: 2,
      state: {
        ...(trainingSnapshot.state as DemoSelfTrainingState),
        screen: 'active_workout',
      },
    };
    mocks.apply.mockResolvedValue(activeSnapshot);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText('Данные исчезнут после завершения сессии')).toBeVisible();
    expect(screen.getByText('Подготовленные данные не относятся к реальным людям.')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Начать тренировку' }));

    expect(mocks.apply).toHaveBeenCalledWith('self_training', 'start_workout', undefined);
    expect(await screen.findByRole('button', { name: 'Завершить текущий подход' })).toBeVisible();
  });

  it('shows an explicit expired state and starts a new isolated session on recovery', async () => {
    mocks.load.mockRejectedValue(
      new DemoApiError('Демо-сессия истекла. Начните новый сценарий.', 410),
    );
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText('Демо-сессия истекла. Начните новый сценарий.')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Повторить' }));

    await waitFor(() => expect(mocks.start).toHaveBeenCalledWith('self_training'));
    expect(mocks.clear).toHaveBeenCalledWith('self_training');
  });

  it('explains the blocked trainer invitation and saves only the contextual comment', async () => {
    const trainerSnapshot: DemoSessionSnapshot = {
      capability: 'demo',
      scenario: 'trainer',
      fixture_version: 'demo-curated-v1',
      revision: 1,
      expires_at: '2026-08-24T12:30:00Z',
      cabinet: {
        ...trainingSnapshot.cabinet,
        trainer: {
          kind: 'trainer',
          screen: 'client',
          client_name: 'Алексей Воронов — подготовленный демо-клиент',
          context_label: 'Последняя тренировка',
          workout_title: 'Ноги и корпус',
          facts: [{ label: 'Выполнено', value: '6 из 6 упражнений' }],
          comment: null,
        },
      },
      state: {
        kind: 'trainer',
        screen: 'client',
        client_name: 'Алексей Воронов — подготовленный демо-клиент',
        context_label: 'Последняя тренировка',
        workout_title: 'Ноги и корпус',
        facts: [{ label: 'Выполнено', value: '6 из 6 упражнений' }],
        comment: null,
      },
    };
    mocks.load.mockResolvedValue(trainerSnapshot);
    mocks.apply.mockResolvedValue({
      ...trainerSnapshot,
      revision: 2,
      state: { ...trainerSnapshot.state, comment: 'Техника стабильна.' },
    });
    const user = userEvent.setup();
    renderPage('/demo?scenario=trainer');

    const invitation = await screen.findByRole('button', { name: 'Пригласить нового клиента' });
    expect(invitation).toBeDisabled();
    expect(screen.getByText(/нет реальных приглашений/)).toBeVisible();
    await user.clear(screen.getByLabelText('Комментарий к этой тренировке'));
    await user.type(screen.getByLabelText('Комментарий к этой тренировке'), 'Техника стабильна.');
    await user.click(screen.getByRole('button', { name: 'Сохранить комментарий' }));

    expect(mocks.apply).toHaveBeenCalledWith('trainer', 'save_comment', 'Техника стабильна.');
    expect(await screen.findByText(/сохранён до конца демо-сессии/)).toBeVisible();
  });

  it('uses a contextual auth handoff and discards hidden demo state', async () => {
    mocks.load.mockResolvedValue({
      ...trainingSnapshot,
      state: {
        ...(trainingSnapshot.state as DemoSelfTrainingState),
        screen: 'progress',
        progress_change_percent: 6.5,
      },
    });
    const user = userEvent.setup();
    renderPage('/demo?scenario=self_training');

    expect(await screen.findByText('Начните с чистого профиля')).toBeVisible();
    expect(screen.getByText(/Демо-изменения не переносятся/)).toBeVisible();
    const handoff = screen.getByRole('link', { name: 'Войти в приложение' });
    expect(handoff).toHaveAttribute('href', '/login?next=%2Fapp&from=demo&scenario=self_training');
    await user.click(handoff);

    expect(mocks.clearAll).toHaveBeenCalledOnce();
    expect(mocks.track).toHaveBeenCalledWith(
      { name: 'demo_login_selected', surface: 'mobile_web' },
      { dedupe: 'session', dedupeKey: 'self_training' },
    );
  });
});
