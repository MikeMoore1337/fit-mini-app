import { useEffect, useRef } from 'react';

export function useTelegramOverlayBackButton(open: boolean, onBack: () => void): void {
  const onBackRef = useRef(onBack);

  useEffect(() => {
    onBackRef.current = onBack;
  }, [onBack]);

  useEffect(() => {
    if (!open) return;
    const telegram = window.Telegram?.WebApp;
    const backButton = telegram?.initData ? telegram.BackButton : undefined;
    if (!backButton) return;

    const closeOverlay = () => onBackRef.current();
    backButton.onClick(closeOverlay);
    backButton.show();
    return () => {
      backButton.offClick(closeOverlay);
      backButton.hide();
    };
  }, [open]);
}
