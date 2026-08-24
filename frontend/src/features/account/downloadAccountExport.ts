import { api, apiFile } from '../../shared/api/client';
import type { AccountExportDownloadLink } from '../../shared/api/types';

export type AccountExportDownloadResult = 'browser' | 'telegram' | 'cancelled';

function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export async function downloadAccountExport(
  exportId: string,
  fallbackFilename: string,
): Promise<AccountExportDownloadResult> {
  const telegram = window.Telegram?.WebApp;
  if (telegram?.initData?.trim() && (telegram.downloadFile || telegram.openLink)) {
    const link = await api<AccountExportDownloadLink>(
      `/api/v1/me/exports/${exportId}/download-link`,
      { method: 'POST', body: {} },
    );
    if (telegram.downloadFile) {
      try {
        return await new Promise((resolve, reject) => {
          try {
            telegram.downloadFile?.(
              { url: link.url, file_name: link.filename },
              (accepted) => resolve(accepted ? 'telegram' : 'cancelled'),
            );
          } catch (reason) {
            reject(reason);
          }
        });
      } catch (reason) {
        if (!telegram.openLink) throw reason;
        telegram.openLink(link.url, { try_instant_view: false });
        return 'telegram';
      }
    }
    telegram.openLink?.(link.url, { try_instant_view: false });
    return 'telegram';
  }

  const file = await apiFile(`/api/v1/me/exports/${exportId}/download`);
  saveBlob(file.blob, file.filename ?? fallbackFilename);
  return 'browser';
}
