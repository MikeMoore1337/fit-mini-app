import { useEffect, useMemo } from 'react';
import {
  APP_THEME_CHANGE_EVENT,
  APP_THEME_STORAGE_KEY,
  LEGACY_LANDING_THEME_STORAGE_KEY,
  YFC_THEME_COLORS,
  applyColorScheme,
  applyWebTheme,
  browserAppTheme,
  type AppColorScheme,
} from '../theme';
import type { TelegramThemeParams, TelegramWebApp } from './types';
import { installMobileLayoutAdapter } from './layout';

function hexLuminance(color: string | undefined): number | null {
  if (!color || !/^#[\da-f]{6}$/i.test(color)) return null;
  const channels = [1, 3, 5].map((offset) => Number.parseInt(color.slice(offset, offset + 2), 16));
  const [red = 0, green = 0, blue = 0] = channels.map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return red * 0.2126 + green * 0.7152 + blue * 0.0722;
}

function fallbackTelegramColorScheme(themeParams: TelegramThemeParams | undefined): AppColorScheme {
  const luminance = hexLuminance(themeParams?.bg_color ?? themeParams?.secondary_bg_color);
  if (luminance !== null) return luminance < 0.35 ? 'dark' : 'light';
  return browserAppTheme('system');
}

export function telegramColorScheme(telegram: TelegramWebApp): {
  colorScheme: AppColorScheme;
  fallback: boolean;
} {
  if (telegram.colorScheme === 'light' || telegram.colorScheme === 'dark') {
    return { colorScheme: telegram.colorScheme, fallback: false };
  }
  return {
    colorScheme: fallbackTelegramColorScheme(telegram.themeParams),
    fallback: true,
  };
}

function callShellColor(
  telegram: TelegramWebApp,
  method: 'setHeaderColor' | 'setBackgroundColor' | 'setBottomBarColor',
  color: string,
): void {
  try {
    telegram[method]?.call(telegram, color);
  } catch {
    // Older Telegram clients may reject unsupported methods or arbitrary RGB colors.
  }
}

export function applyPlatformTheme(telegram: TelegramWebApp | null): AppColorScheme {
  if (!telegram?.initData) {
    delete document.documentElement.dataset.appSurface;
    return applyWebTheme();
  }

  const { colorScheme, fallback } = telegramColorScheme(telegram);
  const shell = YFC_THEME_COLORS[colorScheme];
  document.documentElement.dataset.appSurface = 'telegram';
  applyColorScheme(colorScheme, fallback ? 'telegram-fallback' : 'telegram');

  callShellColor(telegram, 'setHeaderColor', shell.header);
  callShellColor(telegram, 'setBackgroundColor', shell.background);
  callShellColor(telegram, 'setBottomBarColor', shell.bottomBar);
  return colorScheme;
}

export function useTelegram(): TelegramWebApp | null {
  const telegram = useMemo(() => window.Telegram?.WebApp ?? null, []);
  useEffect(() => {
    const isMiniApp = Boolean(telegram?.initData);
    const onTheme = () => applyPlatformTheme(telegram);
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const onStorage = (event: StorageEvent) => {
      if (
        event.key === APP_THEME_STORAGE_KEY ||
        event.key === LEGACY_LANDING_THEME_STORAGE_KEY ||
        event.key === null
      ) {
        onTheme();
      }
    };
    const cleanupLayout = installMobileLayoutAdapter(telegram);

    onTheme();
    if (isMiniApp) {
      telegram?.onEvent?.('themeChanged', onTheme);
    } else {
      media?.addEventListener?.('change', onTheme);
      window.addEventListener('storage', onStorage);
      window.addEventListener(APP_THEME_CHANGE_EVENT, onTheme);
    }
    if (isMiniApp) {
      telegram?.ready?.();
      telegram?.expand?.();
    }
    return () => {
      cleanupLayout();
      if (isMiniApp) telegram?.offEvent?.('themeChanged', onTheme);
      else {
        media?.removeEventListener?.('change', onTheme);
        window.removeEventListener('storage', onStorage);
        window.removeEventListener(APP_THEME_CHANGE_EVENT, onTheme);
      }
    };
  }, [telegram]);
  return telegram;
}

export function haptic(type: 'success' | 'error' | 'warning' = 'success'): void {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  } catch {
    // Haptics are optional outside Telegram.
  }
}
