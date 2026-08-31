import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from '../../../src/app/AppShell';

const logout = vi.fn();
function finishAnimation(element: Element, animationName: string) {
  const event = new Event('animationend', { bubbles: true });
  Object.defineProperty(event, 'animationName', { value: animationName });
  fireEvent(element, event);
}
const { authState, navigation, user } = vi.hoisted(() => ({
  authState: { missing: false },
  navigation: { path: '/coach', search: '' },
  user: {
    id: 1,
    username: 'mikhail',
    first_name: 'Михаил',
    is_coach: true,
    is_root: false,
    photo_url: null as string | null,
  },
}));

vi.mock('../../../src/app/AuthProvider', () => ({
  useOptionalAuth: () => (authState.missing ? null : { user, logout }),
}));

vi.mock('../../../src/shared/navigation/router', () => ({
  useNavigation: () => navigation,
  AppLink: ({ to, className, children, ...props }: React.ComponentProps<'a'> & { to: string }) => (
    <a href={to} className={className} {...props}>
      {children}
    </a>
  ),
}));

describe('AppShell', () => {
  beforeEach(() => {
    cleanup();
    authState.missing = false;
    user.photo_url = null;
    user.is_root = false;
    navigation.path = '/coach';
    navigation.search = '';
    logout.mockClear();
    vi.unstubAllGlobals();
    delete window.Telegram;
  });

  it('показывает основные направления и отделяет рабочее пространство тренера', () => {
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Сегодня' })).toHaveAttribute(
      'href',
      '/app?section=today',
    );
    expect(screen.getByRole('link', { name: 'Программа' })).toHaveAttribute(
      'href',
      '/app?section=programs',
    );
    expect(
      Array.from(document.querySelectorAll('.app-bottom-nav__primary > a')).map(
        (link) => link.textContent,
      ),
    ).toEqual(['Сегодня', 'Программа', 'Питание', 'Прогресс']);
    expect(screen.queryByRole('button', { name: 'Ещё' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Тренер' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'Админ-панель' })).not.toBeInTheDocument();
    expect(screen.getByText('Михаил')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Выйти из аккаунта' }));
    expect(logout).toHaveBeenCalledOnce();
  });

  it('сохраняет active state для каждого прямого core route', () => {
    navigation.path = '/app';
    for (const [section, label] of [
      ['today', 'Сегодня'],
      ['programs', 'Программа'],
      ['nutrition', 'Питание'],
      ['progress', 'Прогресс'],
    ] as const) {
      const view = render(<AppShell section={section}>Содержимое</AppShell>);
      expect(screen.getByRole('link', { name: label })).toHaveAttribute('aria-current', 'page');
      view.unmount();
    }
  });

  it('открывает доступное mobile-меню с secondary navigation и завершает exit после возврата фокуса', async () => {
    navigation.path = '/app';
    render(<AppShell section="profile">Содержимое</AppShell>);

    const more = screen.getByRole('button', { name: 'Открыть профиль и настройки' });
    expect(more).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(more);

    expect(more).toHaveAttribute('aria-expanded', 'true');
    const dialog = screen.getByRole('dialog', { name: 'Профиль и настройки' });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByRole('link', { name: 'Профиль и настройки' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(within(dialog).queryByRole('link', { name: 'База знаний' })).not.toBeInTheDocument();

    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(more).toHaveFocus();
    const closingLayer = document.querySelector<HTMLElement>(
      '.app-more-layer[data-motion-phase="closing"]',
    );
    expect(closingLayer).toBeInTheDocument();
    finishAnimation(closingLayer!, 'app-more-backdrop-out');
    await waitFor(() => expect(document.querySelector('.app-more-layer')).not.toBeInTheDocument());
  });

  it('показывает admin entry только аккаунту с соответствующей capability', () => {
    user.is_root = true;
    navigation.path = '/admin';
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('link', { name: 'Админ-панель' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it('открывает и закрывает mobile-меню сразу при reduced motion', () => {
    vi.stubGlobal('matchMedia', () => ({
      addEventListener: vi.fn(),
      matches: true,
      removeEventListener: vi.fn(),
    }));
    navigation.path = '/app';
    render(<AppShell section="today">Содержимое</AppShell>);

    const more = screen.getByRole('button', { name: 'Открыть профиль и настройки' });
    fireEvent.click(more);
    const dialog = screen.getByRole('dialog', { name: 'Профиль и настройки' });
    expect(dialog).toBeInTheDocument();

    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(document.querySelector('.app-more-layer')).not.toBeInTheDocument();
    expect(more).toHaveFocus();
  });

  it('сохраняет обязательный AuthProvider для обычного production shell', () => {
    authState.missing = true;

    expect(() => render(<AppShell>Содержимое</AppShell>)).toThrow(
      'AppShell must be used inside AuthProvider unless demo config is provided',
    );
  });

  it('использует короткое описание отдельной demo-сессии в rail и mobile menu', () => {
    authState.missing = true;
    render(
      <AppShell
        demo={{
          activeSection: 'today',
          brandTo: '/demo?cabinet=1',
          destinations: [{ key: 'today', label: 'Сегодня', icon: 'today', to: '/demo?cabinet=1' }],
          displayName: 'Демо-кабинет',
          exitTo: '/demo',
          moreLinks: [],
          onReset: vi.fn(),
        }}
      >
        Демо-содержимое
      </AppShell>,
    );

    expect(screen.getByText('Отдельная сессия')).toBeInTheDocument();
    expect(screen.queryByText('Изолированная сессия')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Сценарии' }));
    const dialog = screen.getByRole('dialog', { name: 'Демо-кабинет' });
    expect(within(dialog).getByText('Отдельная сессия')).toBeInTheDocument();
  });

  it('не показывает библиотеку знаний в Web или Telegram Mini App navigation', () => {
    navigation.path = '/app';
    const web = render(<AppShell section="today">Содержимое</AppShell>);

    expect(screen.queryByRole('link', { name: 'База знаний' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Открыть профиль и настройки' }));
    expect(
      within(screen.getByRole('dialog')).queryByRole('link', { name: 'База знаний' }),
    ).not.toBeInTheDocument();

    web.unmount();
    window.Telegram = { WebApp: { initData: 'signed-init-data' } };
    render(<AppShell section="today">Содержимое</AppShell>);
    expect(screen.queryByRole('link', { name: 'База знаний' })).not.toBeInTheDocument();
  });

  it('показывает тематическую заглушку, если аватар отсутствует или не загрузился', () => {
    const { container, rerender } = render(<AppShell>Содержимое</AppShell>);
    const avatar = container.querySelector('.app-bottom-nav__avatar');

    expect(avatar).toHaveTextContent(/🏋️|💪|🏃|🚴|🥗|⚡|🎯|🔥/);

    user.photo_url = 'https://t.me/i/userpic/broken.jpg';
    rerender(<AppShell>Содержимое</AppShell>);
    const image = avatar?.querySelector('img');
    expect(image).toHaveAttribute('src', user.photo_url);

    fireEvent.error(image!);
    expect(avatar?.querySelector('img')).not.toBeInTheDocument();
    expect(avatar).toHaveTextContent(/🏋️|💪|🏃|🚴|🥗|⚡|🎯|🔥/);
  });
});
