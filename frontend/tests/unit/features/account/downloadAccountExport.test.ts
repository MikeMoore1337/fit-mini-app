import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { downloadAccountExport } from '../../../../src/features/account/downloadAccountExport';

const { apiFileMock, apiMock } = vi.hoisted(() => ({
  apiFileMock: vi.fn(),
  apiMock: vi.fn(),
}));

vi.mock('../../../../src/shared/api/client', () => ({
  api: apiMock,
  apiFile: apiFileMock,
}));

describe('account export download handoff', () => {
  beforeEach(() => {
    apiMock.mockReset();
    apiFileMock.mockReset();
    delete window.Telegram;
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:account-export');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('downloads through the authenticated browser request outside Telegram', async () => {
    apiFileMock.mockResolvedValue({
      blob: new Blob(['zip']),
      filename: 'server-account.zip',
    });

    await expect(downloadAccountExport('export-1', 'fallback.zip')).resolves.toBe('browser');

    expect(apiFileMock).toHaveBeenCalledWith('/api/v1/me/exports/export-1/download');
    expect(apiMock).not.toHaveBeenCalled();
  });

  it('uses the Telegram 8.0 native download prompt without storing its short token', async () => {
    const downloadFile = vi.fn(
      (_params: { url: string; file_name: string }, callback?: (accepted: boolean) => void) =>
        callback?.(true),
    );
    window.Telegram = {
      WebApp: {
        initData: 'signed-init-data',
        version: '8.0',
        downloadFile,
      },
    };
    apiMock.mockResolvedValue({
      url: 'https://app.example/api/v1/me/exports/file/short-token',
      filename: 'account.zip',
      expires_at: '2030-01-02T12:02:00',
    });

    await expect(downloadAccountExport('export-2', 'fallback.zip')).resolves.toBe('telegram');

    expect(apiMock).toHaveBeenCalledWith('/api/v1/me/exports/export-2/download-link', {
      method: 'POST',
      body: {},
    });
    expect(downloadFile).toHaveBeenCalledWith(
      {
        url: 'https://app.example/api/v1/me/exports/file/short-token',
        file_name: 'account.zip',
      },
      expect.any(Function),
    );
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it('falls back to an external open handoff on an older Telegram client', async () => {
    const openLink = vi.fn();
    window.Telegram = {
      WebApp: {
        initData: 'signed-init-data',
        version: '7.10',
        openLink,
      },
    };
    apiMock.mockResolvedValue({
      url: 'https://app.example/api/v1/me/exports/file/short-token',
      filename: 'account.zip',
      expires_at: '2030-01-02T12:02:00',
    });

    await expect(downloadAccountExport('export-3', 'fallback.zip')).resolves.toBe('telegram');
    expect(openLink).toHaveBeenCalledWith(
      'https://app.example/api/v1/me/exports/file/short-token',
      { try_instant_view: false },
    );
  });

  it('falls back when an older client exposes but rejects downloadFile', async () => {
    const openLink = vi.fn();
    window.Telegram = {
      WebApp: {
        initData: 'signed-init-data',
        version: '7.10',
        downloadFile: vi.fn(() => {
          throw new Error('WebAppMethodUnsupported');
        }),
        openLink,
      },
    };
    apiMock.mockResolvedValue({
      url: 'https://app.example/api/v1/me/exports/file/short-token',
      filename: 'account.zip',
      expires_at: '2030-01-02T12:02:00',
    });

    await expect(downloadAccountExport('export-4', 'fallback.zip')).resolves.toBe('telegram');
    expect(openLink).toHaveBeenCalledWith(
      'https://app.example/api/v1/me/exports/file/short-token',
      { try_instant_view: false },
    );
  });
});
