import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShell } from '../../../src/app/AppShell';

const logout = vi.fn();
const { user } = vi.hoisted(() => ({
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
  useAuth: () => ({
    user,
    logout,
  }),
}));

vi.mock('../../../src/shared/navigation/router', () => ({
  useNavigation: () => ({ path: '/coach' }),
  AppLink: ({ to, className, children, ...props }: React.ComponentProps<'a'> & { to: string }) => (
    <a href={to} className={className} {...props}>
      {children}
    </a>
  ),
}));

describe('AppShell', () => {
  beforeEach(() => {
    user.photo_url = null;
    logout.mockClear();
  });

  it('показывает адаптивную навигацию и данные аккаунта', () => {
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Тренер' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'Админ' })).not.toBeInTheDocument();
    expect(screen.getByText('Михаил')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Выйти из аккаунта' }));
    expect(logout).toHaveBeenCalledOnce();
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
