import { useState } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { YFC_THEME_COLORS } from '../../../../src/shared/theme';
import { useTelegram } from '../../../../src/shared/telegram/useTelegram';
import type { TelegramWebApp } from '../../../../src/shared/telegram/types';

function TelegramThemeProbe() {
  useTelegram();
  return <button type="button">Состояние экрана: 0</button>;
}

function StatefulTelegramThemeProbe() {
  useTelegram();
  const [count, setCount] = useState(0);
  return (
    <button type="button" onClick={() => setCount((value) => value + 1)}>
      Состояние экрана: {count}
    </button>
  );
}

function telegramMock(colorScheme?: 'light' | 'dark'): TelegramWebApp {
  return {
    initData: 'signed',
    colorScheme,
    themeParams: {
      bg_color: colorScheme === 'dark' ? '#050505' : '#ffffff',
      section_bg_color: '#ff00ff',
      text_color: '#00ffff',
      button_color: '#2481cc',
    },
    ready: vi.fn(),
    expand: vi.fn(),
    onEvent: vi.fn(),
    offEvent: vi.fn(),
    setHeaderColor: vi.fn(),
    setBackgroundColor: vi.fn(),
    setBottomBarColor: vi.fn(),
  };
}

describe('useTelegram theme', () => {
  afterEach(() => {
    cleanup();
    delete window.Telegram;
    document.documentElement.removeAttribute('style');
    delete document.documentElement.dataset.colorScheme;
    delete document.documentElement.dataset.appSurface;
    delete document.documentElement.dataset.themeSource;
    delete document.documentElement.dataset.themePreference;
    localStorage.clear();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it.each(['light', 'dark'] as const)(
    'maps Telegram %s to the matching branded YFC theme and shell colors',
    async (colorScheme) => {
      const telegram = telegramMock(colorScheme);
      window.Telegram = { WebApp: telegram };

      render(<TelegramThemeProbe />);

      await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe(colorScheme));
      expect(document.documentElement.dataset.appSurface).toBe('telegram');
      expect(document.documentElement.dataset.themeSource).toBe('telegram');
      expect(document.documentElement.style.getPropertyValue('--color-accent')).toBe('');
      expect(document.documentElement.style.getPropertyValue('--card')).toBe('');
      expect(telegram.setHeaderColor).toHaveBeenCalledWith(YFC_THEME_COLORS[colorScheme].header);
      expect(telegram.setBackgroundColor).toHaveBeenCalledWith(
        YFC_THEME_COLORS[colorScheme].background,
      );
      expect(telegram.setBottomBarColor).toHaveBeenCalledWith(
        YFC_THEME_COLORS[colorScheme].bottomBar,
      );
    },
  );

  it('does not let browser or stored preferences override a valid Telegram colorScheme', async () => {
    localStorage.setItem('app-theme', 'dark');
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => ({ matches: true })),
    );
    const telegram = telegramMock('light');
    window.Telegram = { WebApp: telegram };

    render(<TelegramThemeProbe />);

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('light'));
    expect(document.documentElement.dataset.themePreference).toBeUndefined();
  });

  it('updates on themeChanged without losing current screen state', async () => {
    let onThemeChanged: (() => void) | undefined;
    const telegram = telegramMock('light');
    telegram.onEvent = vi.fn((event: string, callback: () => void) => {
      if (event === 'themeChanged') onThemeChanged = callback;
    });
    window.Telegram = { WebApp: telegram };

    render(<StatefulTelegramThemeProbe />);
    fireEvent.click(screen.getByRole('button', { name: 'Состояние экрана: 0' }));
    expect(screen.getByRole('button', { name: 'Состояние экрана: 1' })).toBeInTheDocument();
    await waitFor(() => expect(onThemeChanged).toBeTypeOf('function'));

    telegram.colorScheme = 'dark';
    onThemeChanged?.();

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('dark'));
    expect(screen.getByRole('button', { name: 'Состояние экрана: 1' })).toBeInTheDocument();
  });

  it('uses themeParams only to infer a safe light/dark fallback when colorScheme is missing', async () => {
    const telegram = telegramMock();
    telegram.themeParams = { bg_color: '#101010', button_color: '#ff00ff' };
    window.Telegram = { WebApp: telegram };

    render(<TelegramThemeProbe />);

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('dark'));
    expect(document.documentElement.dataset.themeSource).toBe('telegram-fallback');
    expect(document.documentElement.style.getPropertyValue('--color-accent')).toBe('');
  });

  it('uses the persisted Web preference outside a real Mini App', async () => {
    localStorage.setItem('app-theme', 'light');
    window.Telegram = { WebApp: { ...telegramMock('dark'), initData: '' } };

    render(<TelegramThemeProbe />);

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('light'));
    expect(document.documentElement.dataset.appSurface).toBeUndefined();
    expect(document.documentElement.dataset.themeSource).toBe('web');
  });
});
