import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OnboardingGate } from '../../../src/app/OnboardingGate';
import { NavigationProvider } from '../../../src/shared/navigation/router';

const useAuthMock = vi.hoisted(() => vi.fn());

vi.mock('../../../src/app/AuthProvider', () => ({ useAuth: useAuthMock }));

describe('OnboardingGate', () => {
  beforeEach(() => window.history.replaceState(null, '', '/app'));
  afterEach(cleanup);

  it('redirects only users who still need the minimum profile step', async () => {
    useAuthMock.mockReturnValue({ user: { onboarding: { status: 'required' } } });

    render(
      <NavigationProvider>
        <OnboardingGate>
          <p>Приложение</p>
        </OnboardingGate>
      </NavigationProvider>,
    );

    await waitFor(() => expect(window.location.pathname).toBe('/onboarding'));
    expect(window.location.search).toBe('?next=%2Fapp');
    expect(screen.queryByText('Приложение')).not.toBeInTheDocument();
  });

  it('keeps returning users in the requested product route', () => {
    useAuthMock.mockReturnValue({ user: { onboarding: { status: 'complete' } } });

    render(
      <NavigationProvider>
        <OnboardingGate>
          <p>Приложение</p>
        </OnboardingGate>
      </NavigationProvider>,
    );

    expect(screen.getByText('Приложение')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/app');
  });
});
