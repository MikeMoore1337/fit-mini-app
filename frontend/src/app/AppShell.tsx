import { useState } from 'react';
import { AppLink, useNavigation } from '../shared/navigation/router';
import { AppThemeToggle } from '../shared/ui/AppThemeToggle';
import { useAuth } from './AuthProvider';

const AVATAR_EMOJIS = ['🏋️', '💪', '🏃', '🚴', '🥗', '⚡', '🎯', '🔥'] as const;

function avatarFallback(name: string): string {
  const hash = Array.from(name.trim()).reduce(
    (value, character) => (value * 31 + (character.codePointAt(0) ?? 0)) >>> 0,
    0,
  );
  return AVATAR_EMOJIS[hash % AVATAR_EMOJIS.length] ?? AVATAR_EMOJIS[0];
}

function Avatar({ name, photoUrl }: { name: string; photoUrl?: string | null }) {
  const [failedPhotoUrl, setFailedPhotoUrl] = useState<string | null>(null);
  const photoFailed = Boolean(photoUrl && failedPhotoUrl === photoUrl);

  return (
    <span className="app-bottom-nav__avatar" aria-hidden="true">
      {photoUrl && !photoFailed ? (
        <img
          src={photoUrl}
          alt=""
          referrerPolicy="no-referrer"
          onError={() => setFailedPhotoUrl(photoUrl)}
        />
      ) : (
        avatarFallback(name)
      )}
    </span>
  );
}

export function AppShell({
  children,
  narrow = false,
}: {
  children: React.ReactNode;
  narrow?: boolean;
}) {
  const { user, logout } = useAuth();
  const { path } = useNavigation();
  const displayName =
    user?.profile?.full_name || user?.first_name || user?.username || 'Пользователь';
  return (
    <>
      <main className={`container${narrow ? ' narrow' : ''}`}>{children}</main>
      {user && (
        <nav id="appBottomNav" className="app-bottom-nav" aria-label="Основная навигация">
          <div className="app-bottom-nav__brand" aria-hidden="true">
            <img
              className="app-bottom-nav__brand-mark"
              src="/assets/brand/fitness-logo-v2.png"
              alt=""
            />
            <strong>Your Fitness Coach</strong>
          </div>
          <AppLink
            to="/app"
            className={`app-bottom-nav__btn${path === '/app' ? ' is-active' : ''}`}
            aria-current={path === '/app' ? 'page' : undefined}
          >
            <span className="app-bottom-nav__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M3 11.5 12 4l9 7.5" />
                <path d="M5.5 10.5V20h13v-9.5M9 20v-6h6v6" />
              </svg>
            </span>
            <span className="app-bottom-nav__label">Главная</span>
          </AppLink>
          {(user.is_coach || user.is_admin) && (
            <AppLink
              to="/coach"
              className={`app-bottom-nav__btn${path === '/coach' ? ' is-active' : ''}`}
              aria-current={path === '/coach' ? 'page' : undefined}
            >
              <span className="app-bottom-nav__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <circle cx="9" cy="8" r="3" />
                  <path d="M3.5 20v-2.5A4.5 4.5 0 0 1 8 13h2a4.5 4.5 0 0 1 4.5 4.5V20M16 8h5M18.5 5.5v5" />
                </svg>
              </span>
              <span className="app-bottom-nav__label">Тренер</span>
            </AppLink>
          )}
          {user.is_admin && (
            <AppLink
              to="/admin"
              className={`app-bottom-nav__btn${path === '/admin' ? ' is-active' : ''}`}
              aria-current={path === '/admin' ? 'page' : undefined}
            >
              <span className="app-bottom-nav__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6" />
                </svg>
              </span>
              <span className="app-bottom-nav__label">Админ</span>
            </AppLink>
          )}
          <AppThemeToggle navigation />
          <div className="app-bottom-nav__account">
            <Avatar name={displayName} photoUrl={user.photo_url} />
            <span className="app-bottom-nav__account-copy">
              <strong>{displayName}</strong>
              <small>{user.is_admin ? 'Администратор' : user.is_coach ? 'Тренер' : 'Клиент'}</small>
            </span>
            <button
              type="button"
              className="app-bottom-nav__logout"
              onClick={() => void logout()}
              aria-label="Выйти из аккаунта"
              title="Выйти"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />
              </svg>
            </button>
          </div>
        </nav>
      )}
    </>
  );
}
