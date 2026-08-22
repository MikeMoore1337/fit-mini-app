import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  installMobileLayoutAdapter,
  readMobileViewportSnapshot,
} from '../../../../src/shared/telegram/layout';
import type { TelegramWebApp } from '../../../../src/shared/telegram/types';

function telegramLayoutMock(): TelegramWebApp {
  return {
    initData: 'signed',
    isActive: true,
    viewportHeight: 560,
    viewportStableHeight: 844,
    safeAreaInset: { top: 28, right: 2, bottom: 20, left: 2 },
    contentSafeAreaInset: { top: 44, right: 0, bottom: 16, left: 0 },
    onEvent: vi.fn(),
    offEvent: vi.fn(),
  };
}

describe('Mobile Web/TMA layout adapter', () => {
  afterEach(() => {
    document.body.replaceChildren();
    document.documentElement.removeAttribute('style');
    delete document.documentElement.dataset.yfcKeyboard;
    delete document.documentElement.dataset.yfcLayoutSurface;
    delete document.documentElement.dataset.yfcViewportActive;
    vi.restoreAllMocks();
  });

  it('normalizes Telegram stable/current viewport and both safe-area layers', () => {
    const telegram = telegramLayoutMock();

    expect(readMobileViewportSnapshot(telegram)).toEqual({
      active: true,
      viewportHeight: 560,
      viewportStableHeight: 844,
      safeArea: { top: 28, right: 2, bottom: 20, left: 2 },
      contentSafeArea: { top: 44, right: 0, bottom: 16, left: 0 },
    });

    const cleanup = installMobileLayoutAdapter(telegram);
    const root = document.documentElement;
    expect(root.dataset.yfcLayoutSurface).toBe('telegram');
    expect(root.style.getPropertyValue('--yfc-viewport-height')).toBe('560px');
    expect(root.style.getPropertyValue('--yfc-viewport-stable-height')).toBe('844px');
    expect(root.style.getPropertyValue('--yfc-tg-safe-top')).toBe('28px');
    expect(root.style.getPropertyValue('--yfc-tg-content-safe-top')).toBe('44px');

    cleanup();
    expect(telegram.offEvent).toHaveBeenCalledTimes(5);
  });

  it('hides navigation state only while an editable control owns focus', () => {
    const telegram = telegramLayoutMock();
    const input = document.createElement('input');
    document.body.append(input);
    const cleanup = installMobileLayoutAdapter(telegram);

    input.focus();
    expect(document.documentElement.dataset.yfcKeyboard).toBe('visible');

    input.blur();
    document.body.focus();
    window.dispatchEvent(new Event('resize'));
    expect(document.documentElement.dataset.yfcKeyboard).toBe('hidden');

    cleanup();
  });

  it('updates layout values from Telegram events without recreating application state', () => {
    const telegram = telegramLayoutMock();
    const callbacks = new Map<string, () => void>();
    telegram.onEvent = vi.fn((event, callback) => callbacks.set(event, callback));
    const cleanup = installMobileLayoutAdapter(telegram);

    telegram.viewportHeight = 720;
    telegram.viewportStableHeight = 900;
    callbacks.get('viewportChanged')?.();

    expect(document.documentElement.style.getPropertyValue('--yfc-viewport-height')).toBe('720px');
    expect(document.documentElement.style.getPropertyValue('--yfc-viewport-stable-height')).toBe(
      '900px',
    );

    cleanup();
  });
});
