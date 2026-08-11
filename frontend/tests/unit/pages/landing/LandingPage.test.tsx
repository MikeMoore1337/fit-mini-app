import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import LandingPage, { appUrlForHostname } from '../../../../src/pages/landing/LandingPage';
import { NavigationProvider } from '../../../../src/shared/navigation/router';

describe('LandingPage', () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
    window.history.replaceState({}, '', '/');
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('follows the system dark theme and lets the visitor switch it', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    );

    const { container } = render(
      <NavigationProvider>
        <LandingPage />
      </NavigationProvider>,
    );

    expect(container.firstChild).toHaveClass('landing-page--dark');
    fireEvent.click(screen.getByRole('button', { name: 'Включить светлую тему' }));
    expect(container.firstChild).toHaveClass('landing-page--light');
    expect(localStorage.getItem('landing-theme')).toBe('light');
  });

  it('shows the service, features and Telegram contact without publishing tariffs', () => {
    const { container } = render(
      <NavigationProvider>
        <LandingPage />
      </NavigationProvider>,
    );

    expect(
      screen.getByRole('heading', { name: /ваш прогресс.*в фокусе тренера/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /всё необходимое/i })).toBeInTheDocument();
    expect(screen.queryByText(/тариф/i)).not.toBeInTheDocument();

    expect(screen.queryByText('@mikhail_murzaev')).not.toBeInTheDocument();
    expect(container.querySelectorAll('img[src="/assets/brand/fitness-logo-v1.png"]')).toHaveLength(
      2,
    );
    const contact = screen.getByRole('link', { name: /связаться в telegram/i });
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
    expect(appUrlForHostname('your-fitness-coach.ru')).toBe(
      'https://app.your-fitness-coach.ru/app',
    );
  });
});
