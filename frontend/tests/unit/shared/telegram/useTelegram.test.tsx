import { cleanup, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useTelegram } from '../../../../src/shared/telegram/useTelegram';
import type { TelegramWebApp } from '../../../../src/shared/telegram/types';
import { APP_THEME_STORAGE_KEY } from '../../../../src/shared/theme';

function TelegramThemeProbe() {
  useTelegram();
  return null;
}

describe('useTelegram theme', () => {
  afterEach(() => {
    cleanup();
    delete window.Telegram;
    document.documentElement.removeAttribute('style');
    delete document.documentElement.dataset.colorScheme;
    delete document.documentElement.dataset.appSurface;
    localStorage.clear();
  });

  it.each(['light', 'dark'] as const)(
    'uses Telegram surfaces and interaction colors in %s mode',
    async (colorScheme) => {
      const telegram = {
        initData: 'signed',
        colorScheme,
        themeParams: {
          bg_color: colorScheme === 'dark' ? '#101010' : '#fafafa',
          secondary_bg_color: colorScheme === 'dark' ? '#181818' : '#f0f0f0',
          section_bg_color: colorScheme === 'dark' ? '#202020' : '#ffffff',
          section_separator_color: colorScheme === 'dark' ? '#303030' : '#dddddd',
          text_color: colorScheme === 'dark' ? '#ffffff' : '#111111',
          hint_color: colorScheme === 'dark' ? '#aaaaaa' : '#777777',
          button_color: '#2481cc',
          button_text_color: '#ffffff',
          link_color: '#168acd',
          destructive_text_color: '#d14e4e',
          bottom_bar_bg_color: colorScheme === 'dark' ? '#151515' : '#f7f7f7',
        },
        ready: vi.fn(),
        expand: vi.fn(),
        onEvent: vi.fn(),
        offEvent: vi.fn(),
        setHeaderColor: vi.fn(),
        setBackgroundColor: vi.fn(),
        setBottomBarColor: vi.fn(),
      } satisfies TelegramWebApp;
      window.Telegram = { WebApp: telegram };

      render(<TelegramThemeProbe />);

      await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe(colorScheme));
      expect(document.documentElement.dataset.appSurface).toBe('telegram');
      expect(document.documentElement.style.getPropertyValue('--bg')).toBe(
        telegram.themeParams.bg_color,
      );
      expect(document.documentElement.style.getPropertyValue('--card')).toBe(
        telegram.themeParams.section_bg_color,
      );
      expect(document.documentElement.style.getPropertyValue('--text')).toBe(
        telegram.themeParams.text_color,
      );
      expect(document.documentElement.style.getPropertyValue('--accent')).toBe(
        telegram.themeParams.button_color,
      );
      expect(document.documentElement.style.getPropertyValue('--button-text')).toBe(
        telegram.themeParams.button_text_color,
      );
      expect(document.documentElement.style.getPropertyValue('--link-color')).toBe(
        telegram.themeParams.link_color,
      );
      expect(document.documentElement.style.getPropertyValue('--nav-bg')).toBe(
        telegram.themeParams.bottom_bar_bg_color,
      );
      expect(telegram.setHeaderColor).toHaveBeenCalledWith(telegram.themeParams.bg_color);
      expect(telegram.setBackgroundColor).toHaveBeenCalledWith(telegram.themeParams.bg_color);
      expect(telegram.setBottomBarColor).toHaveBeenCalledWith(
        telegram.themeParams.bottom_bar_bg_color,
      );
    },
  );

  it('removes Telegram overrides and keeps the branded web theme outside Mini App', async () => {
    localStorage.setItem(APP_THEME_STORAGE_KEY, 'light');
    document.documentElement.dataset.appSurface = 'telegram';
    document.documentElement.style.setProperty('--accent', '#2481cc');
    window.Telegram = {
      WebApp: {
        initData: '',
        colorScheme: 'dark',
        themeParams: { button_color: '#2481cc' },
        ready: vi.fn(),
        expand: vi.fn(),
        onEvent: vi.fn(),
        offEvent: vi.fn(),
        setHeaderColor: vi.fn(),
        setBackgroundColor: vi.fn(),
        setBottomBarColor: vi.fn(),
      },
    };

    render(<TelegramThemeProbe />);

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('light'));
    expect(document.documentElement.dataset.appSurface).toBeUndefined();
    expect(document.documentElement.style.getPropertyValue('--accent')).toBe('');
  });

  it('updates the palette when Telegram emits themeChanged', async () => {
    let onThemeChanged: (() => void) | undefined;
    const telegram: TelegramWebApp = {
      initData: 'signed',
      colorScheme: 'light',
      themeParams: {
        bg_color: '#ffffff',
        text_color: '#111111',
        button_color: '#2481cc',
      },
      ready: vi.fn(),
      expand: vi.fn(),
      onEvent: vi.fn((event: string, callback: () => void) => {
        if (event === 'themeChanged') onThemeChanged = callback;
      }),
      offEvent: vi.fn(),
      setHeaderColor: vi.fn(),
      setBackgroundColor: vi.fn(),
      setBottomBarColor: vi.fn(),
    };
    window.Telegram = { WebApp: telegram };

    render(<TelegramThemeProbe />);
    await waitFor(() => expect(onThemeChanged).toBeTypeOf('function'));

    telegram.colorScheme = 'dark';
    telegram.themeParams!.bg_color = '#17212b';
    telegram.themeParams!.text_color = '#f5f5f5';
    telegram.themeParams!.button_color = '#6ab2f2';
    onThemeChanged?.();

    await waitFor(() => expect(document.documentElement.dataset.colorScheme).toBe('dark'));
    expect(document.documentElement.style.getPropertyValue('--bg')).toBe('#17212b');
    expect(document.documentElement.style.getPropertyValue('--accent')).toBe('#6ab2f2');
  });
});
