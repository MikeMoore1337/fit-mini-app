import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  api,
  clearAccessToken,
  getAccessToken,
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

  it('turns a fetch failure into a readable offline error', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(api('/api/v1/me')).rejects.toMatchObject({
      status: 0,
      message: 'Нет соединения с сервером. Проверьте интернет и попробуйте снова.',
    });
  });
});
