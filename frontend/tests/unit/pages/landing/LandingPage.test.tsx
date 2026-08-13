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
    expect(screen.getByText(/веб-приложение для тренировок и прогресса/i)).toBeInTheDocument();
    expect(
      screen.getByText(/тренируйтесь самостоятельно или работайте вместе с тренером/i),
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
      screen.getByRole('heading', {
        name: /открывайте на компьютере или смартфоне.*telegram.*когда удобнее/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', {
        name: /^открывайте на компьютере или смартфоне$/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /продолжайте в telegram mini app/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/для самостоятельных тренировок telegram не нужен/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/общение с тренером происходит в telegram/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Данные синхронизируются')).toBeInTheDocument();
    expect(screen.getByText(/занимаетесь самостоятельно/i)).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /тренируйтесь по понятному плану/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/вы тренер/i)).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /подайте заявку и откройте кабинет тренера/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/нажмите «стать тренером» в профиле/i)).toBeInTheDocument();
    expect(screen.getByText(/писать администратору отдельно не нужно/i)).toBeInTheDocument();
    expect(
      screen.getByText(/доступно в браузере на компьютере или смартфоне/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/работает прямо в браузере/i)).toBeInTheDocument();
    expect(screen.queryByText(/современн.*браузер/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/тариф/i)).not.toBeInTheDocument();
    expect(screen.queryByText('+18%')).not.toBeInTheDocument();
    expect(screen.queryByText('12', { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByText('4 недели', { exact: true })).not.toBeInTheDocument();

    expect(screen.queryByText('@mikhail_murzaev')).not.toBeInTheDocument();
    expect(container.querySelectorAll('img[src="/assets/brand/fitness-logo-v2.png"]')).toHaveLength(
      2,
    );
    const contact = screen.getByRole('link', { name: /задать вопрос в telegram/i });
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
    expect(screen.getByRole('link', { name: /начать самостоятельно/i })).toHaveAttribute(
      'href',
      '/app',
    );
    expect(screen.getByRole('link', { name: /войти и подать заявку/i })).toHaveAttribute(
      'href',
      '/app',
    );
    expect(screen.getByRole('link', { name: /перейти в веб-приложение/i })).toHaveAttribute(
      'href',
      '/app',
    );
    expect(appUrlForHostname('your-fitness-coach.ru')).toBe(
      'https://app.your-fitness-coach.ru/app',
    );
  });

  it('publishes useful metadata and a keyboard skip link', () => {
    const description = document.createElement('meta');
    description.name = 'description';
    document.head.append(description);
    const ogTitle = document.createElement('meta');
    ogTitle.setAttribute('property', 'og:title');
    document.head.append(ogTitle);
    const ogDescription = document.createElement('meta');
    ogDescription.setAttribute('property', 'og:description');
    document.head.append(ogDescription);
    const ogType = document.createElement('meta');
    ogType.setAttribute('property', 'og:type');
    document.head.append(ogType);

    const { unmount } = render(
      <NavigationProvider>
        <LandingPage />
      </NavigationProvider>,
    );

    expect(document.title).toMatch(/тренировки, питание и прогресс в браузере и telegram/i);
    expect(description.content).toMatch(/фиксировать результаты.*ориентиры кбжу/i);
    expect(ogTitle.content).toMatch(/в браузере и telegram/i);
    expect(ogDescription.content).toMatch(/компьютере или смартфоне.*telegram mini app/i);
    expect(ogType.content).toBe('website');
    expect(screen.getByRole('link', { name: 'К содержимому' })).toHaveAttribute(
      'href',
      '#landing-content',
    );
    expect(document.querySelector('#landing-content')).toHaveAttribute('tabindex', '-1');

    unmount();
    description.remove();
    ogTitle.remove();
    ogDescription.remove();
    ogType.remove();
  });
});
