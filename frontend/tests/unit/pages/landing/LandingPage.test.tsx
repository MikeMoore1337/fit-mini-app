import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import LandingPage, {
  appUrlForHostname,
  demoUrlForHostname,
  loginUrlForHostname,
} from '../../../../src/pages/landing/LandingPage';
import { NavigationProvider } from '../../../../src/shared/navigation/router';

function renderLanding() {
  return render(
    <NavigationProvider>
      <LandingPage />
    </NavigationProvider>,
  );
}

describe('LandingPage', () => {
  afterEach(() => {
    cleanup();
    document.head
      .querySelectorAll(
        'meta[name="description"], meta[name="robots"], meta[name="yandex"], meta[name^="twitter:"], meta[property^="og:"], link[rel="canonical"], script[type="application/ld+json"]',
      )
      .forEach((element) => element.remove());
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

    const { container } = renderLanding();

    expect(container.firstChild).toHaveClass('public-shell--dark');
    fireEvent.click(screen.getByRole('button', { name: 'Включить светлую тему' }));
    expect(container.firstChild).toHaveClass('public-shell--light');
    expect(localStorage.getItem('app-theme')).toBe('light');
  });

  it('publishes a factual product story for self-training and trainer audiences', () => {
    const { container } = renderLanding();

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Знайте, что делать сегодня.',
    );
    expect(screen.getByText(/план на сегодня.*результат.*в динамике/i)).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Основные возможности' })).toHaveTextContent(
      /тренировки.*питание.*прогресс.*тренер/i,
    );

    expect(
      screen.getByRole('heading', { name: 'Сначала — одно понятное действие.' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Ориентир рядом с фактическими записями.' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Выводы только там, где хватает данных.' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'У каждого клиента — видимый контекст.' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/режим включается сразу из профиля/i)).toBeInTheDocument();
    expect(screen.getByText(/не заменяет crm, платежи, расписание бизнеса/i)).toBeInTheDocument();
    expect(screen.getByText(/данные подготовленных демо-сценариев отделены/i)).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: /три сценария/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Пройдите тренировку' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Добавьте питание' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Посмотрите кабинет тренера' })).toBeInTheDocument();

    expect(
      screen.getByText(/telegram mini app не является отдельным приложением/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/экспорт, отвязка способов входа и удаление аккаунта/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/после одобрения заявки/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/тариф/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/искусственн.*интеллект|\bai\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/отзыв/i)).not.toBeInTheDocument();

    const support = screen.getByRole('link', { name: 'Поддержка в Telegram' });
    expect(support).toHaveAttribute('href', 'https://t.me/your_fitness_coach_bot?start=support');
    expect(support).toHaveAttribute('target', '_blank');
    expect(container.querySelectorAll('img[src*="/assets/brand/yfc-mark-"]')).toHaveLength(1);
    expect(container.querySelectorAll('img[src*="/assets/brand/yfc-logo-"]')).toHaveLength(1);
  });

  it('uses dimensioned real product proof with eager hero and lazy below-fold images', () => {
    renderLanding();

    const heroDesktop = screen.getByAltText(/экран сегодня.*недельный контекст/i);
    expect(heroDesktop).toHaveAttribute('src', '/assets/product/landing-today-desktop-light.png');
    expect(heroDesktop).toHaveAttribute('width', '1280');
    expect(heroDesktop).toHaveAttribute('height', '972');
    expect(heroDesktop).toHaveAttribute('loading', 'eager');
    expect(heroDesktop).toHaveAttribute('fetchpriority', 'high');
    expect(heroDesktop).not.toHaveClass('is-loaded');
    fireEvent.load(heroDesktop);
    expect(heroDesktop).toHaveClass('is-loaded');
    expect(heroDesktop.closest('picture')?.querySelector('source')).toHaveAttribute(
      'srcset',
      '/assets/product/landing-workout-mobile-light.png',
    );

    const mobileProof = screen.getByAltText('Экран тренировки в Mobile Web');
    expect(mobileProof).toHaveAttribute('src', '/assets/product/landing-workout-mobile-dark.png');
    expect(mobileProof).toHaveAttribute('width', '390');
    expect(mobileProof).toHaveAttribute('height', '844');
    expect(mobileProof).toHaveAttribute('loading', 'lazy');

    const trainerProof = screen.getByAltText(/кабинет тренера с результатом/i);
    expect(trainerProof).toHaveAttribute('loading', 'lazy');
    fireEvent.error(trainerProof);
    expect(screen.queryByAltText(/кабинет тренера с результатом/i)).not.toBeInTheDocument();
    expect(screen.getByText('Экран кабинета тренера временно недоступен.')).toBeInTheDocument();
  });

  it('links conversion actions to canonical app, demo and crawlable public routes', () => {
    renderLanding();

    expect(screen.getByRole('link', { name: 'Войти' })).toHaveAttribute('href', '/login');
    expect(screen.getAllByRole('link', { name: 'Открыть приложение' })[0]).toHaveAttribute(
      'href',
      '/app',
    );
    expect(screen.getByRole('link', { name: 'Попробовать демо' })).toHaveAttribute(
      'href',
      '/demo?cabinet=1&scenario=self_training&section=today',
    );
    expect(screen.getByRole('link', { name: /добавьте питание/i })).toHaveAttribute(
      'href',
      '/demo?cabinet=1&scenario=nutrition&section=nutrition',
    );
    expect(screen.getByRole('link', { name: /посмотрите кабинет тренера/i })).toHaveAttribute(
      'href',
      '/demo?cabinet=1&scenario=trainer&section=trainer',
    );
    expect(screen.getByRole('link', { name: 'Как устроены тренировки' })).toHaveAttribute(
      'href',
      '/training',
    );
    expect(screen.getByRole('link', { name: 'Подробнее о питании' })).toHaveAttribute(
      'href',
      '/nutrition',
    );
    expect(screen.getByRole('link', { name: 'Как читать прогресс' })).toHaveAttribute(
      'href',
      '/progress',
    );
    expect(screen.getByRole('link', { name: 'Возможности тренера' })).toHaveAttribute(
      'href',
      '/for-trainers',
    );
    expect(appUrlForHostname('your-fitness-coach.ru')).toBe(
      'https://app.your-fitness-coach.ru/app',
    );
    expect(loginUrlForHostname('your-fitness-coach.ru')).toBe(
      'https://app.your-fitness-coach.ru/login',
    );
    expect(demoUrlForHostname('your-fitness-coach.ru')).toBe(
      'https://app.your-fitness-coach.ru/demo',
    );
    expect(screen.getByRole('link', { name: 'Приватность и данные' })).toHaveAttribute(
      'href',
      '#privacy',
    );
    expect(document.querySelector('#privacy')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Ваши данные остаются под вашим управлением.' }),
    ).toBeInTheDocument();
  });

  it('closes mobile navigation by selection and Escape with focus restoration', () => {
    const { container } = renderLanding();
    const menuButton = container.querySelector<HTMLButtonElement>('.landing-menu-toggle')!;

    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-label', 'Закрыть меню');
    fireEvent.click(screen.getByRole('link', { name: 'Продукт' }));
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(menuButton);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(menuButton).toHaveAttribute('aria-label', 'Открыть меню');
    expect(menuButton).toHaveFocus();
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

    const { unmount } = renderLanding();

    expect(document.title).toMatch(/тренировки, питание и прогресс в браузере и telegram/i);
    expect(description.content).toMatch(/фиксировать результаты.*ориентиры кбжу/i);
    expect(ogTitle.content).toMatch(/в браузере и telegram/i);
    expect(ogDescription.content).toMatch(/компьютере или смартфоне.*telegram mini app/i);
    expect(ogType.content).toBe('website');
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      'content',
      'index, follow',
    );
    expect(document.querySelector('link[rel="canonical"]')).toHaveAttribute(
      'href',
      `${window.location.origin}/`,
    );
    expect(screen.getByRole('link', { name: 'К содержимому' })).toHaveAttribute(
      'href',
      '#landing-content',
    );
    expect(document.querySelector('#landing-content')).toHaveAttribute('tabindex', '-1');

    unmount();
  });
});
