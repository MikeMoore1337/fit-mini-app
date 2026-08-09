import type { KeyboardEvent } from 'react';

export function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>): void {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const tabs = [
    ...(event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(
      '[role="tab"]:not([disabled])',
    ) ?? []),
  ];
  const currentIndex = tabs.indexOf(event.currentTarget);
  if (currentIndex < 0 || !tabs.length) return;
  event.preventDefault();
  let nextIndex = currentIndex;
  if (event.key === 'Home') nextIndex = 0;
  if (event.key === 'End') nextIndex = tabs.length - 1;
  if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
  if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
  tabs[nextIndex]?.focus();
  tabs[nextIndex]?.click();
}
