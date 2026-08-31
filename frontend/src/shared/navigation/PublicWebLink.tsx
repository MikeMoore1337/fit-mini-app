import type { AnchorHTMLAttributes, MouseEvent } from 'react';
import { publicUrlForHostname } from './appUrl';

function isPlainPrimaryClick(event: MouseEvent<HTMLAnchorElement>): boolean {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
}

export function tryOpenPublicUrlInTelegram(href: string): boolean {
  const telegram = window.Telegram?.WebApp;
  if (!telegram?.initData?.trim() || !telegram.openLink) return false;

  try {
    telegram.openLink(new URL(href, window.location.origin).href, { try_instant_view: false });
    return true;
  } catch {
    return false;
  }
}

export function PublicWebLink({
  path,
  onClick,
  onTelegramOpen,
  children,
  ...attributes
}: {
  path: string;
  onTelegramOpen?: () => void;
} & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href' | 'target' | 'rel'>) {
  const href = publicUrlForHostname(window.location.hostname, path);

  return (
    <a
      {...attributes}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented || !isPlainPrimaryClick(event)) return;
        if (tryOpenPublicUrlInTelegram(href)) {
          event.preventDefault();
          onTelegramOpen?.();
        }
      }}
    >
      {children}
    </a>
  );
}
