import { cleanup, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useTelegramOverlayBackButton } from '../../../../src/shared/telegram/useTelegramOverlayBackButton';
import { createTelegramMock } from '../../../helpers/telegramMock';

describe('useTelegramOverlayBackButton', () => {
  afterEach(() => {
    cleanup();
    delete window.Telegram;
  });

  it('временно передаёт native BackButton открытому overlay и снимает handler при закрытии', () => {
    const telegram = createTelegramMock();
    window.Telegram = { WebApp: telegram.webApp };
    const onBack = vi.fn();
    const { rerender } = renderHook(({ open }) => useTelegramOverlayBackButton(open, onBack), {
      initialProps: { open: true },
    });

    expect(telegram.calls.backButton.shown).toBe(1);
    telegram.clickBack();
    expect(onBack).toHaveBeenCalledTimes(1);

    rerender({ open: false });
    expect(telegram.calls.backButton.hidden).toBe(1);
    telegram.clickBack();
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('не показывает Telegram control в обычном браузере', () => {
    const telegram = createTelegramMock({ initData: '' });
    window.Telegram = { WebApp: telegram.webApp };

    renderHook(() => useTelegramOverlayBackButton(true, vi.fn()));

    expect(telegram.calls.backButton.shown).toBe(0);
    expect(telegram.calls.backButton.hidden).toBe(0);
  });
});
