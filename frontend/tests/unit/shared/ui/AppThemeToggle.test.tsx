import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { APP_THEME_STORAGE_KEY } from '../../../../src/shared/theme';
import { AppThemeToggle } from '../../../../src/shared/ui/AppThemeToggle';

function mockColorScheme(initialDark: boolean) {
  const listeners = new Set<() => void>();
  const media = {
    matches: initialDark,
    addEventListener: vi.fn((_event: string, listener: () => void) => listeners.add(listener)),
    removeEventListener: vi.fn((_event: string, listener: () => void) =>
      listeners.delete(listener),
    ),
  };
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => media),
  );
  return {
    setDark(value: boolean) {
      media.matches = value;
      listeners.forEach((listener) => listener());
    },
  };
}

describe('AppThemeToggle', () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
    delete window.Telegram;
    delete document.documentElement.dataset.colorScheme;
    delete document.documentElement.dataset.themePreference;
    delete document.documentElement.dataset.themeSource;
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('follows the system until the visitor toggles and then persists explicit choices', () => {
    const system = mockColorScheme(true);
    render(<AppThemeToggle />);

    let toggle = screen.getByRole('button', { name: 'Включить светлую тему' });
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    act(() => system.setDark(false));
    expect(document.documentElement.dataset.colorScheme).toBe('light');
    toggle = screen.getByRole('button', { name: 'Включить тёмную тему' });

    fireEvent.click(toggle);
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('dark');
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    act(() => system.setDark(false));
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    fireEvent.click(screen.getByRole('button', { name: 'Включить светлую тему' }));
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('light');
    expect(document.documentElement.dataset.colorScheme).toBe('light');
  });

  it('is a compact action with an explicit accessible label', () => {
    mockColorScheme(false);
    render(<AppThemeToggle />);

    const toggle = screen.getByRole('button', { name: 'Включить тёмную тему' });
    expect(toggle).toHaveAttribute('title', 'Включить тёмную тему');
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });

  it('is not exposed inside a valid Telegram Mini App', () => {
    window.Telegram = { WebApp: { initData: 'signed' } };
    render(<AppThemeToggle />);
    expect(screen.queryByRole('button', { name: /Включить .* тему/ })).not.toBeInTheDocument();
  });
});
