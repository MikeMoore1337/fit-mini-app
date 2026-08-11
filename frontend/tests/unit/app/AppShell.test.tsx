import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AppShell } from '../../../src/app/AppShell';

const logout = vi.fn();

vi.mock('../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      username: 'mikhail',
      first_name: 'Михаил',
      is_coach: true,
      is_admin: false,
    },
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
  it('показывает адаптивную навигацию и данные аккаунта', () => {
    render(<AppShell>Содержимое</AppShell>);

    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Тренер' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'Админ' })).not.toBeInTheDocument();
    expect(screen.getByText('Михаил')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Выйти из аккаунта' }));
    expect(logout).toHaveBeenCalledOnce();
  });
});
