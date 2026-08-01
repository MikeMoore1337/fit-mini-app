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
        <nav className="app-bottom-nav" aria-label="Основная навигация">
          <AppLink
            to="/app"
            className={`app-bottom-nav__btn${path === '/app' ? ' is-active' : ''}`}
          >
            <span className="app-bottom-nav__label">Mini App</span>
          </AppLink>
          {(user.is_coach || user.is_admin) && (
            <AppLink
              to="/coach"
              className={`app-bottom-nav__btn${path === '/coach' ? ' is-active' : ''}`}
            >
              <span className="app-bottom-nav__label">Тренер</span>
            </AppLink>
          )}
          {user.is_admin && (
            <AppLink
              to="/admin"
              className={`app-bottom-nav__btn${path === '/admin' ? ' is-active' : ''}`}
            >
              <span className="app-bottom-nav__label">Админ</span>
            </AppLink>
          )}
        </nav>
      )}
    </>
  );
}
