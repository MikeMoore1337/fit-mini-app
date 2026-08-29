import { api } from '../../shared/api/client';
import type { ProgressReportDownloadLink } from '../../shared/api/types';

export type ProgressReportDownloadResult =
  | { status: 'accepted'; url: string }
  | { status: 'cancelled'; url: string }
  | { status: 'fallback'; url: string };

export async function downloadProgressReport(
  downloadLinkPath: string,
): Promise<ProgressReportDownloadResult> {
  const link = await api<ProgressReportDownloadLink>(downloadLinkPath, {
    method: 'POST',
    body: {},
  });
  const telegram = window.Telegram?.WebApp;
  if (telegram?.downloadFile) {
    try {
      const accepted = await new Promise<boolean>((resolve, reject) => {
        try {
          telegram.downloadFile?.({ url: link.url, file_name: link.filename }, resolve);
        } catch (reason) {
          reject(reason);
        }
      });
      return { status: accepted ? 'accepted' : 'cancelled', url: link.url };
    } catch (reason) {
      if (!telegram.openLink) throw reason;
    }
  }
  if (telegram?.openLink) {
    telegram.openLink(link.url, { try_instant_view: false });
    return { status: 'accepted', url: link.url };
  }
  return { status: 'fallback', url: link.url };
}
