import { cleanup, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useTelegram } from '../../../../src/shared/telegram/useTelegram';
import type { TelegramWebApp } from '../../../../src/shared/telegram/types';

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
  });

  it.each(['light', 'dark'] as const)(
    'keeps the brand interaction colors in Telegram %s mode',
    async (colorScheme) => {
      const telegram = {
        initData: 'signed',
        colorScheme,
        themeParams: {
          bg_color: colorScheme === 'dark' ? '#101010' : '#fafafa',
          text_color: colorScheme === 'dark' ? '#ffffff' : '#111111',
          button_color: '#2481cc',
          button_text_color: '#ffffff',
          link_color: '#2481cc',
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
      expect(document.documentElement.style.getPropertyValue('--bg')).toBe(
        telegram.themeParams.bg_color,
      );
      expect(document.documentElement.style.getPropertyValue('--text')).toBe(
        telegram.themeParams.text_color,
      );
      expect(document.documentElement.style.getPropertyValue('--accent')).toBe('');
      expect(document.documentElement.style.getPropertyValue('--button-text')).toBe('');
      expect(document.documentElement.style.getPropertyValue('--link-color')).toBe('');
    },
  );
});
