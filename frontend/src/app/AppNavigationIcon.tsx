import type { ReactNode } from 'react';

export type AppNavigationIconName =
  | 'today'
  | 'plan'
  | 'progress'
  | 'nutrition'
  | 'more'
  | 'catalog'
  | 'profile'
  | 'knowledge'
  | 'coach'
  | 'admin'
  | 'logout'
  | 'close';

export function AppNavigationIcon({ name }: { name: AppNavigationIconName }) {
  const paths: Record<AppNavigationIconName, ReactNode> = {
    today: (
      <>
        <path d="M4 10.5 12 4l8 6.5" />
        <path d="M6.5 9.5V20h11V9.5M9.5 20v-6h5v6" />
      </>
    ),
    plan: (
      <>
        <rect x="4" y="5" width="16" height="15" rx="2" />
        <path d="M8 3v4M16 3v4M8 11h8M8 15h5" />
      </>
    ),
    progress: (
      <>
        <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
        <path d="m4 7 6-4 6 5 5-4" />
      </>
    ),
    nutrition: (
      <>
        <circle cx="12" cy="12" r="6.25" />
        <path d="M3 4v5a2 2 0 0 0 2 2 2 2 0 0 0 2-2V4M5 4v17M21 4c-2 2-2 5.5 0 7.5V21" />
      </>
    ),
    more: (
      <>
        <circle cx="5" cy="12" r="1.25" fill="currentColor" stroke="none" />
        <circle cx="12" cy="12" r="1.25" fill="currentColor" stroke="none" />
        <circle cx="19" cy="12" r="1.25" fill="currentColor" stroke="none" />
      </>
    ),
    catalog: (
      <>
        <path d="M5 4h11a3 3 0 0 1 3 3v13H7a2 2 0 0 1-2-2Z" />
        <path d="M5 17a3 3 0 0 1 3-3h11M9 8h6" />
      </>
    ),
    profile: (
      <>
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 20a7 7 0 0 1 14 0" />
      </>
    ),
    knowledge: (
      <>
        <path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H12v18H7.5A3.5 3.5 0 0 0 4 23Z" />
        <path d="M20 5.5A3.5 3.5 0 0 0 16.5 2H12v18h4.5A3.5 3.5 0 0 1 20 23Z" />
      </>
    ),
    coach: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3.5 20v-2.5A4.5 4.5 0 0 1 8 13h2a4.5 4.5 0 0 1 4.5 4.5V20M16 8h5M18.5 5.5v5" />
      </>
    ),
    admin: (
      <>
        <path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6" />
      </>
    ),
    logout: <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />,
    close: <path d="m6 6 12 12M18 6 6 18" />,
  };

  return (
    <span className="app-bottom-nav__icon" aria-hidden="true">
      <svg viewBox="0 0 24 24">{paths[name]}</svg>
    </span>
  );
}
