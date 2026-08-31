import { describe, expect, it } from 'vitest';
import { isTelegramLaunch } from '../../../../src/shared/telegram/launch';

describe('isTelegramLaunch', () => {
  it('does not block ordinary browser routes on the Telegram SDK', () => {
    expect(isTelegramLaunch({ pathname: '/app', search: '', hash: '' })).toBe(false);
    expect(isTelegramLaunch({ pathname: '/', search: '?tgWebAppPlatform=web', hash: '' })).toBe(
      false,
    );
    expect(
      isTelegramLaunch({ pathname: '/knowledgeable', search: '?tgWebAppPlatform=web', hash: '' }),
    ).toBe(false);
    expect(
      isTelegramLaunch({
        pathname: '/app/knowledgeable',
        search: '?tgWebAppPlatform=web',
        hash: '',
      }),
    ).toBe(false);
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
    expect(
      isTelegramLaunch({ pathname: '/demo', search: '?tgWebAppPlatform=android', hash: '' }),
    ).toBe(true);
    expect(
      isTelegramLaunch({
        pathname: '/knowledge/training/repetitions-in-reserve',
        search: '?tgWebAppData=signed-data',
        hash: '',
      }),
    ).toBe(true);
    expect(
      isTelegramLaunch({
        pathname: '/app/knowledge/progress/how-to-read-progress',
        search: '',
        hash: '#tgWebAppPlatform=ios',
      }),
    ).toBe(true);
  });
});
