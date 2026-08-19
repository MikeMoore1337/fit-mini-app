import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  api,
  clearAccessToken,
  getAccessToken,
  refreshAccessToken,
  setAccessToken,
} from '../../../../src/shared/api/client';

describe('api client', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    vi.restoreAllMocks();
  });
  afterEach(() => clearAccessToken());

  it('stores access tokens only in sessionStorage', () => {
    setAccessToken('secret');
    expect(getAccessToken()).toBe('secret');
    expect(localStorage.getItem('fit_access_token')).toBeNull();
  });

  it('refreshes once after 401 and retries with the new token', async () => {
    setAccessToken('old');
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{"detail":"expired"}', { status: 401 }))
      .mockResolvedValueOnce(new Response('{"access_token":"new"}', { status: 200 }))
      .mockResolvedValueOnce(new Response('{"ok":true}', { status: 200 }));
    await expect(api<{ ok: boolean }>('/api/v1/me')).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(getAccessToken()).toBe('new');
  });

  it('reuses a token refreshed by another tab while waiting for the browser lock', async () => {
    setAccessToken('old');
    const fetchMock = vi.spyOn(globalThis, 'fetch');
    const request = vi.fn(async (_name: string, callback: () => Promise<boolean>) => {
      setAccessToken('from-another-tab');
      return callback();
    });
    const originalLocks = navigator.locks;
    Object.defineProperty(navigator, 'locks', {
      configurable: true,
      value: { request },
    });

    try {
      await expect(refreshAccessToken()).resolves.toBe(true);
      expect(request).toHaveBeenCalledWith('fit-auth-refresh', expect.any(Function));
      expect(fetchMock).not.toHaveBeenCalled();
      expect(getAccessToken()).toBe('from-another-tab');
    } finally {
      Object.defineProperty(navigator, 'locks', {
        configurable: true,
        value: originalLocks,
      });
    }
  });

  it('turns a fetch failure into a readable offline error', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(api('/api/v1/me')).rejects.toMatchObject({
      status: 0,
      message: 'Нет соединения с сервером. Проверьте интернет и попробуйте снова.',
    });
  });

  it('forwards caller cancellation without presenting it as a timeout', async () => {
    const controller = new AbortController();
    vi.spyOn(globalThis, 'fetch').mockImplementationOnce((_input, init) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          reject(new DOMException('Cancelled', 'AbortError'));
        });
      });
    });

    const request = api('/api/v1/nutrition/foods/search?q=test', {
      signal: controller.signal,
    });
    controller.abort();

    await expect(request).rejects.toMatchObject({ name: 'AbortError' });
  });
});
