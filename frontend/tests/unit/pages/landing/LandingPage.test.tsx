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
      screen.getByRole('heading', {
        name: /знайте, что делать сегодня.*следите, как растёт прогресс/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/тренировки в браузере и telegram/i)).toBeInTheDocument();
    expect(
      screen.getByText(/тренируйтесь самостоятельно или вместе с тренером/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/пример интерфейса тренировки на сегодня/i)).toBeInTheDocument();
    expect(screen.getByText('Жим гантелей лёжа')).toBeInTheDocument();
    expect(screen.getByText('01:24')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /тренировки не должны жить в пяти разных местах/i }),
    ).toBeInTheDocument();
    expect(screen.getByText('Когда всё разрозненно')).toBeInTheDocument();
    expect(screen.getByText('В Your Fitness Coach')).toBeInTheDocument();
    expect(screen.getByText('Один понятный план действий')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /понятные действия для спортсмена и тренера/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /откройте приложение и сразу переходите к делу/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /получите ориентиры кбжу/i })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /ведите своих клиентов в одном кабинете/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/приглашайте клиентов, назначайте и корректируйте программы/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /от цели до понятного следующего шага/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Выберите свой путь' })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /один аккаунт.*два способа открыть/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /когда нужен большой экран/i })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /когда тренировка уже началась/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Данные синхронизируются')).toBeInTheDocument();
    expect(screen.queryByText(/тариф/i)).not.toBeInTheDocument();
    expect(screen.queryByText('+18%')).not.toBeInTheDocument();
    expect(screen.queryByText('12', { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByText('4 недели', { exact: true })).not.toBeInTheDocument();

    expect(screen.queryByText('@mikhail_murzaev')).not.toBeInTheDocument();
    expect(container.querySelectorAll('img[src="/assets/brand/fitness-logo-v2.png"]')).toHaveLength(
      2,
    );
    const contact = screen.getByRole('link', { name: /связаться в telegram/i });
    expect(contact).toHaveAttribute('href', 'https://t.me/your_fitness_support_bot');
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
