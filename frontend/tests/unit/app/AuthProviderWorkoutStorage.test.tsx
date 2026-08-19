import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '../../../src/app/AuthProvider';
import { clearAccessToken, setAccessToken } from '../../../src/shared/api/client';
import type { Workout } from '../../../src/shared/api/types';
import {
  activeWorkoutQueueKey,
  loadCurrentActiveWorkoutSnapshot,
  saveActiveWorkoutSnapshot,
} from '../../../src/features/workouts/activeWorkoutQueue';

const activeWorkout: Workout = {
  id: 42,
  scheduled_date: '2030-01-10',
  title: 'Тренировка A',
  status: 'in_progress',
  day_number: 1,
  week_number: 1,
  started_at: '2030-01-10T10:00:00',
  exercises: [
    {
      id: 101,
      exercise_id: 11,
      exercise_title: 'Жим штанги лежа',
      sort_order: 1,
      prescribed_sets: 1,
      prescribed_reps: '8-10',
      rest_seconds: 90,
      has_guide: false,
      sets: [{ id: 201, set_number: 1, is_completed: false, version: 1 }],
    },
  ],
};

function Harness() {
  const { user, logout, devLogin } = useAuth();
  return (
    <div>
      <span data-testid="user-id">{user?.id ?? 'none'}</span>
      <button onClick={() => void logout()}>Выйти</button>
      <button
        onClick={() =>
          void devLogin({
            telegram_user_id: 800,
            is_coach: false,
            is_admin: false,
          })
        }
      >
        Сменить аккаунт
      </button>
    </div>
  );
}

function renderProvider() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Harness />
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe('AuthProvider active workout cleanup', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    setAccessToken('initial-token');
  });

  afterEach(() => {
    cleanup();
    clearAccessToken();
    vi.restoreAllMocks();
  });

  it('очищает локальную тренировку при logout', async () => {
    const queueKey = activeWorkoutQueueKey(7, 42);
    localStorage.setItem(queueKey, '{"private":"draft"}');
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith('/public/config')) return new Response('{}', { status: 200 });
      if (path.endsWith('/me')) return new Response('{"id":7}', { status: 200 });
      if (path.endsWith('/auth/logout')) return new Response(null, { status: 204 });
      return new Response('{"detail":"unexpected"}', { status: 500 });
    });
    renderProvider();
    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('7'));

    await userEvent.click(screen.getByRole('button', { name: 'Выйти' }));

    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('none'));
    expect(localStorage.getItem(queueKey)).toBeNull();
  });

  it('очищает данные прежнего аккаунта перед account switch', async () => {
    const queueKey = activeWorkoutQueueKey(7, 42);
    localStorage.setItem(queueKey, '{"private":"draft"}');
    let meCalls = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith('/public/config')) return new Response('{}', { status: 200 });
      if (path.endsWith('/auth/dev-login')) {
        return new Response('{"access_token":"switched-token"}', { status: 200 });
      }
      if (path.endsWith('/me')) {
        meCalls += 1;
        return new Response(JSON.stringify({ id: meCalls === 1 ? 7 : 8 }), { status: 200 });
      }
      return new Response('{"detail":"unexpected"}', { status: 500 });
    });
    renderProvider();
    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('7'));

    await userEvent.click(screen.getByRole('button', { name: 'Сменить аккаунт' }));

    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('8'));
    expect(localStorage.getItem(queueKey)).toBeNull();
  });

  it('восстанавливает offline-shell после refresh только для подтверждённой auth-сессии', async () => {
    saveActiveWorkoutSnapshot(7, activeWorkout);
    const firstFetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith('/public/config')) return new Response('{}', { status: 200 });
      if (path.endsWith('/me')) return new Response('{"id":7}', { status: 200 });
      return new Response('{"detail":"unexpected"}', { status: 500 });
    });
    const first = renderProvider();
    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('7'));
    first.unmount();
    firstFetch.mockRestore();

    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));
    renderProvider();

    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('7'));
    expect(loadCurrentActiveWorkoutSnapshot(7)?.id).toBe(42);
  });

  it('не открывает private snapshot без access token', async () => {
    clearAccessToken();
    sessionStorage.setItem('fit_authenticated_user_id', '7');
    saveActiveWorkoutSnapshot(7, activeWorkout);
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));

    renderProvider();

    await waitFor(() => expect(screen.getByTestId('user-id')).toHaveTextContent('none'));
  });
});
