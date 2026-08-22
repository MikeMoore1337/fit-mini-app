import { afterEach, describe, expect, it } from 'vitest';
import { enableDesignPilot49e } from '../../../src/dev/designPilot49e';

function clearPilot(): void {
  document.documentElement.removeAttribute('data-design-pilot');
  document.documentElement.removeAttribute('data-pilot-surface');
  document.documentElement.removeAttribute('data-pilot-back-button');
  document.documentElement.removeAttribute('data-pilot-telegram-active');
  document.documentElement.removeAttribute('data-pilot-telegram-ready');
  document.documentElement.removeAttribute('data-pilot-telegram-expanded');
  document.documentElement.removeAttribute('data-pilot-keyboard');
  document.documentElement.removeAttribute('data-pilot-evidence');
  document.documentElement.removeAttribute('style');
  delete window.Telegram;
  delete window.__YFC_DESIGN_PILOT_49E__;
  window.history.replaceState({}, '', '/');
}

afterEach(clearPilot);

describe('49E development-only design pilot', () => {
  it('does nothing without the explicit pilot flag', async () => {
    expect(await enableDesignPilot49e()).toBe(false);
    expect(document.documentElement.dataset.designPilot).toBeUndefined();
  });

  it('installs a bounded Telegram mock with official safe-area and viewport fields', async () => {
    window.history.replaceState(
      {},
      '',
      '/app?design_pilot=49e&pilot_surface=tma&pilot_theme=dark&pilot_safe_top=28&pilot_content_safe_bottom=16',
    );

    expect(await enableDesignPilot49e()).toBe(true);
    const telegram = window.Telegram?.WebApp as
      | (NonNullable<typeof window.Telegram>['WebApp'] & {
          viewportStableHeight: number;
          safeAreaInset: { top: number };
          contentSafeAreaInset: { bottom: number };
        })
      | undefined;

    expect(document.documentElement.dataset.designPilot).toBe('49e');
    expect(document.documentElement.dataset.pilotSurface).toBe('tma-mock');
    expect(telegram?.colorScheme).toBe('dark');
    expect(telegram?.safeAreaInset.top).toBe(28);
    expect(telegram?.contentSafeAreaInset.bottom).toBe(16);
    expect(telegram?.viewportStableHeight).toBe(window.innerHeight);
    expect(document.documentElement.style.getPropertyValue('--tg-safe-area-inset-top')).toBe(
      '28px',
    );

    telegram?.BackButton?.show();
    expect(document.documentElement.dataset.pilotBackButton).toBe('visible');
    telegram?.BackButton?.hide();
    expect(document.documentElement.dataset.pilotBackButton).toBe('hidden');

    window.__YFC_DESIGN_PILOT_49E__?.setViewport(560, 720);
    expect(document.documentElement.dataset.pilotKeyboard).toBe('visible');
    expect(document.documentElement.style.getPropertyValue('--tg-viewport-height')).toBe('560px');
    expect(document.documentElement.style.getPropertyValue('--tg-viewport-stable-height')).toBe(
      '720px',
    );
  });
});
