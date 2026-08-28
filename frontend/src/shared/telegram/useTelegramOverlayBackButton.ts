import { useLayoutEffect, useRef } from 'react';
import { registerTelegramBackButton } from './backButton';

export function useTelegramOverlayBackButton(open: boolean, onBack: () => void): void {
  const onBackRef = useRef(onBack);

  useLayoutEffect(() => {
    onBackRef.current = onBack;
  }, [onBack]);

  useLayoutEffect(() => {
    if (!open) return;
    const telegram = window.Telegram?.WebApp;
    const closeOverlay = () => onBackRef.current();
    return registerTelegramBackButton(telegram, closeOverlay, 'overlay');
  }, [open]);
}
