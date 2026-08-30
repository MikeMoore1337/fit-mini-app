import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { OnboardingGate } from '../../../src/app/OnboardingGate';
import { NavigationProvider } from '../../../src/shared/navigation/router';

describe('OnboardingGate', () => {
  beforeEach(() => window.history.replaceState(null, '', '/app'));
  afterEach(cleanup);

  it('never blocks the authenticated product route with profile completion', () => {
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
