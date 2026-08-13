import { describe, expect, it } from 'vitest';
import { isTelegramLaunch } from '../../../../src/shared/telegram/launch';

describe('isTelegramLaunch', () => {
  it('does not block ordinary browser routes on the Telegram SDK', () => {
    expect(isTelegramLaunch({ pathname: '/app', search: '', hash: '' })).toBe(false);
    expect(isTelegramLaunch({ pathname: '/', search: '?tgWebAppPlatform=web', hash: '' })).toBe(
      false,
    );
  });

  it('detects Telegram launch parameters in query and hash', () => {
    expect(
      isTelegramLaunch({ pathname: '/app', search: '?tgWebAppPlatform=android', hash: '' }),
    ).toBe(true);
    expect(
      isTelegramLaunch({ pathname: '/coach', search: '', hash: '#tgWebAppData=signed-data' }),
    ).toBe(true);
    expect(
      isTelegramLaunch({ pathname: '/join/token', search: '?tgWebAppVersion=8.0', hash: '' }),
    ).toBe(true);
  });
});
