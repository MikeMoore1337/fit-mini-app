import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from '../../../src/app/AppShell';

const logout = vi.fn();
const { authState, navigation, user } = vi.hoisted(() => ({
  authState: { missing: false },
  navigation: { path: '/coach', search: '' },
  user: {
    id: 1,
    username: 'mikhail',
    first_name: 'Михаил',
    is_coach: true,
    is_admin: false,
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
    user.is_admin = false;
    navigation.path = '/coach';
    navigation.search = '';
    logout.mockClear();
    delete window.Telegram;
  });

  it('показывает основные направления и отделяет рабочее пространство тренера', () => {
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Сегодня' })).toHaveAttribute(
      'href',
      '/app?section=today',
    );
    expect(screen.getByRole('link', { name: 'План' })).toHaveAttribute(
      'href',
      '/app?section=programs',
    );
    expect(screen.getByRole('link', { name: 'Тренер' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'Админ-панель' })).not.toBeInTheDocument();
    expect(screen.getByText('Михаил')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Выйти из аккаунта' }));
    expect(logout).toHaveBeenCalledOnce();
  });

  it('открывает доступное mobile-меню с secondary navigation', () => {
    navigation.path = '/app';
    render(<AppShell section="profile">Содержимое</AppShell>);

    const more = screen.getByRole('button', { name: 'Ещё' });
    expect(more).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(more);

    expect(more).toHaveAttribute('aria-expanded', 'true');
    const dialog = screen.getByRole('dialog', { name: 'Михаил' });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByRole('link', { name: 'Профиль и настройки' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(within(dialog).getByRole('link', { name: 'База знаний' })).toHaveAttribute(
      'href',
      '/knowledge',
    );

    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('показывает admin entry только аккаунту с соответствующей capability', () => {
    user.is_admin = true;
    navigation.path = '/admin';
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('link', { name: 'Админ-панель' })).toHaveAttribute(
      'aria-current',
      'page',
    );
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

  it('не показывает библиотеку знаний в Telegram Mini App navigation', () => {
    window.Telegram = { WebApp: { initData: 'signed-init-data' } };
    navigation.path = '/app';
    render(<AppShell section="today">Содержимое</AppShell>);

    expect(screen.queryByRole('link', { name: 'База знаний' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Ещё' }));
    expect(
      within(screen.getByRole('dialog')).queryByRole('link', { name: 'База знаний' }),
    ).not.toBeInTheDocument();
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
