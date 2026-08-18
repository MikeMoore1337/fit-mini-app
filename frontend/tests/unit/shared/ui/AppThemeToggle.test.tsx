import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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

  it('defaults to system, follows runtime OS changes and persists an explicit choice', () => {
    const system = mockColorScheme(true);
    render(<AppThemeToggle />);

    const selector = screen.getByRole('combobox', { name: 'Тема оформления' });
    expect(selector).toHaveValue('system');
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    system.setDark(false);
    expect(document.documentElement.dataset.colorScheme).toBe('light');

    fireEvent.change(selector, { target: { value: 'dark' } });
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('dark');
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    system.setDark(false);
    expect(document.documentElement.dataset.colorScheme).toBe('dark');

    fireEvent.change(selector, { target: { value: 'system' } });
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('system');
    expect(document.documentElement.dataset.colorScheme).toBe('light');
  });

  it('offers all preferences with a native selected state', () => {
    mockColorScheme(false);
    render(<AppThemeToggle />);

    expect(screen.getByRole('option', { name: 'Системная' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Светлая' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Тёмная' })).toBeInTheDocument();
  });

  it('is not exposed inside a valid Telegram Mini App', () => {
    window.Telegram = { WebApp: { initData: 'signed' } };
    render(<AppThemeToggle />);
    expect(screen.queryByRole('combobox', { name: 'Тема оформления' })).not.toBeInTheDocument();
  });
});
