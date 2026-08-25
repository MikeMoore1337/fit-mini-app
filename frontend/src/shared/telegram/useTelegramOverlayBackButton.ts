import { useEffect, useRef } from 'react';
import { registerTelegramBackButton } from './backButton';

export function useTelegramOverlayBackButton(open: boolean, onBack: () => void): void {
  const onBackRef = useRef(onBack);

  useEffect(() => {
    onBackRef.current = onBack;
  }, [onBack]);

  useEffect(() => {
    if (!open) return;
    const telegram = window.Telegram?.WebApp;
    const closeOverlay = () => onBackRef.current();
    return registerTelegramBackButton(telegram, closeOverlay, 'overlay');
  }, [open]);
}
