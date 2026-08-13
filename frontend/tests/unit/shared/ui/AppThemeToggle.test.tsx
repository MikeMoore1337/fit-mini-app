import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { APP_THEME_STORAGE_KEY } from '../../../../src/shared/theme';
import { AppThemeToggle } from '../../../../src/shared/ui/AppThemeToggle';

describe('AppThemeToggle', () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
    delete document.documentElement.dataset.colorScheme;
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('uses the system theme and remembers a manual choice', () => {
    const themeColor = document.createElement('meta');
    themeColor.name = 'theme-color';
    document.head.append(themeColor);
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    );

    render(<AppThemeToggle />);

    expect(document.documentElement.dataset.colorScheme).toBe('dark');
    expect(document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.content).toBe(
      '#0d120f',
    );
    expect(screen.getByRole('button').querySelector('svg')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Включить светлую тему' }));
    expect(document.documentElement.dataset.colorScheme).toBe('light');
    expect(document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.content).toBe(
      '#f1f3ec',
    );
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('light');
    themeColor.remove();
  });
});
