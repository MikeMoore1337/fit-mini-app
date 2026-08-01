import { AppLink, useNavigation } from '../shared/navigation/router';
import { useAuth } from './AuthProvider';

export function AppShell({
  children,
  narrow = false,
}: {
  children: React.ReactNode;
  narrow?: boolean;
}) {
  const { user } = useAuth();
  const { path } = useNavigation();
  return (
    <>
      <main className={`container${narrow ? ' narrow' : ''}`}>{children}</main>
      {user && (
        <nav id="appBottomNav" className="app-bottom-nav" aria-label="Основная навигация">
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
        </nav>
      )}
    </>
  );
}
