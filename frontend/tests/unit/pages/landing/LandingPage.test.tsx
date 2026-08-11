import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import LandingPage from '../../../../src/pages/landing/LandingPage';
import { NavigationProvider } from '../../../../src/shared/navigation/router';

describe('LandingPage', () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, '', '/');
  });

  it('shows the service, features and Telegram contact without publishing tariffs', () => {
    render(
      <NavigationProvider>
        <LandingPage />
      </NavigationProvider>,
    );

    expect(
      screen.getByRole('heading', { name: /ваш прогресс.*в фокусе тренера/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /всё необходимое/i })).toBeInTheDocument();
    expect(screen.queryByText(/тариф/i)).not.toBeInTheDocument();

    const contact = screen.getByRole('link', { name: /@mikhail_murzaev/i });
    expect(contact).toHaveAttribute('href', 'https://t.me/mikhail_murzaev');
    expect(contact).toHaveAttribute('target', '_blank');
  });

  it('links calls to action to the existing application route', () => {
    render(
      <NavigationProvider>
        <LandingPage />
      </NavigationProvider>,
    );

    expect(screen.getByRole('link', { name: 'Войти' })).toHaveAttribute('href', '/app');
    expect(screen.getByRole('link', { name: /открыть приложение/i })).toHaveAttribute(
      'href',
      '/app',
    );
  });
});
