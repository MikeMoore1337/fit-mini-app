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
    expect(screen.getByRole('button').querySelector('svg')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Включить светлую тему' }));
    expect(document.documentElement.dataset.colorScheme).toBe('light');
    expect(localStorage.getItem(APP_THEME_STORAGE_KEY)).toBe('light');
  });
});
