import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { AppLink, useNavigation } from '../shared/navigation/router';
import { AppThemeToggle } from '../shared/ui/AppThemeToggle';
import { BrandLockup } from '../shared/ui/BrandLogo';
import { AppNavigationIcon, type AppNavigationIconName } from './AppNavigationIcon';
import { useAuth } from './AuthProvider';

export type AppSection = 'today' | 'progress' | 'programs' | 'catalog' | 'nutrition' | 'profile';

const AVATAR_EMOJIS = ['🏋️', '💪', '🏃', '🚴', '🥗', '⚡', '🎯', '🔥'] as const;

const APP_DESTINATIONS: ReadonlyArray<{
  section: AppSection;
  label: string;
  icon: AppNavigationIconName;
}> = [
  { section: 'today', label: 'Сегодня', icon: 'today' },
  { section: 'programs', label: 'План', icon: 'plan' },
  { section: 'progress', label: 'Прогресс', icon: 'progress' },
  { section: 'nutrition', label: 'Питание', icon: 'nutrition' },
];

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

function accountRole(isAdmin: boolean, isCoach: boolean): string {
  if (isAdmin) return 'Администратор';
  if (isCoach) return 'Тренер';
  return 'Клиент';
}

export function AppShell({
  children,
  narrow = false,
  section,
}: {
  children: React.ReactNode;
  narrow?: boolean;
  section?: AppSection;
}) {
  const { user, logout } = useAuth();
  const { path } = useNavigation();
  const [moreOpen, setMoreOpen] = useState(false);
  const morePanelRef = useRef<HTMLDivElement>(null);
  const displayName =
    user?.profile?.full_name || user?.first_name || user?.username || 'Пользователь';
  const secondaryActive = section === 'catalog' || section === 'profile';

  const closeMore = (restoreFocus = false) => {
    setMoreOpen(false);
    if (restoreFocus) document.getElementById('appMoreButton')?.focus();
  };

  useEffect(() => {
    if (!moreOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    morePanelRef.current?.querySelector<HTMLElement>('button, a')?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [moreOpen]);

  const handleMoreKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      closeMore(true);
      return;
    }
    if (event.key !== 'Tab') return;
    const focusable = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>('a[href], button:not([disabled])'),
    ).filter((element) => element.offsetParent !== null);
    const first = focusable[0];
    const last = focusable.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="app-shell app-shell--design-v2">
      <main id="appContent" className={`container app-shell__content${narrow ? ' narrow' : ''}`}>
        {children}
      </main>
      {user && (
        <>
          <nav id="appBottomNav" className="app-bottom-nav" aria-label="Основная навигация">
            <AppLink
              className="app-bottom-nav__brand"
              to="/app?section=today"
              aria-label="Your Fitness Coach — сегодня"
            >
              <BrandLockup markClassName="app-bottom-nav__brand-mark" />
            </AppLink>

            <div className="app-bottom-nav__primary">
              {APP_DESTINATIONS.map((destination) => {
                const active = path === '/app' && section === destination.section;
                return (
                  <AppLink
                    key={destination.section}
                    to={`/app?section=${destination.section}`}
                    className={`app-bottom-nav__btn${active ? ' is-active' : ''}`}
                    aria-current={active ? 'page' : undefined}
                  >
                    <AppNavigationIcon name={destination.icon} />
                    <span className="app-bottom-nav__label">{destination.label}</span>
                  </AppLink>
                );
              })}
              <button
                id="appMoreButton"
                type="button"
                className={`app-bottom-nav__btn app-bottom-nav__more${secondaryActive || path === '/coach' || path === '/admin' ? ' is-active' : ''}`}
                aria-expanded={moreOpen}
                aria-controls="appMorePanel"
                onClick={() => setMoreOpen((open) => !open)}
              >
                <AppNavigationIcon name="more" />
                <span className="app-bottom-nav__label">Ещё</span>
              </button>
            </div>

            <div
              className="app-bottom-nav__secondary"
              role="group"
              aria-label="Дополнительные разделы"
            >
              <p className="app-bottom-nav__group-label">Мои данные</p>
              <AppLink
                to="/app?section=catalog"
                className={`app-bottom-nav__btn${path === '/app' && section === 'catalog' ? ' is-active' : ''}`}
                aria-current={path === '/app' && section === 'catalog' ? 'page' : undefined}
              >
                <AppNavigationIcon name="catalog" />
                <span className="app-bottom-nav__label">Упражнения</span>
              </AppLink>
              <AppLink
                to="/app?section=profile"
                className={`app-bottom-nav__btn${path === '/app' && section === 'profile' ? ' is-active' : ''}`}
                aria-current={path === '/app' && section === 'profile' ? 'page' : undefined}
              >
                <AppNavigationIcon name="profile" />
                <span className="app-bottom-nav__label">Профиль</span>
              </AppLink>
              <AppLink to="/knowledge" className="app-bottom-nav__btn">
                <AppNavigationIcon name="knowledge" />
                <span className="app-bottom-nav__label">База знаний</span>
              </AppLink>

              {user.is_coach && (
                <>
                  <p className="app-bottom-nav__group-label">Рабочие пространства</p>
                  <AppLink
                    to="/coach"
                    className={`app-bottom-nav__btn${path === '/coach' ? ' is-active' : ''}`}
                    aria-current={path === '/coach' ? 'page' : undefined}
                  >
                    <AppNavigationIcon name="coach" />
                    <span className="app-bottom-nav__label">Тренер</span>
                  </AppLink>
                </>
              )}
              {user.is_admin && (
                <AppLink
                  to="/admin"
                  className={`app-bottom-nav__btn${path === '/admin' ? ' is-active' : ''}`}
                  aria-current={path === '/admin' ? 'page' : undefined}
                >
                  <AppNavigationIcon name="admin" />
                  <span className="app-bottom-nav__label">Администрирование</span>
                </AppLink>
              )}
            </div>

            <div className="app-bottom-nav__utility">
              <AppThemeToggle navigation />
              <div className="app-bottom-nav__account">
                <Avatar name={displayName} photoUrl={user.photo_url} />
                <span className="app-bottom-nav__account-copy">
                  <strong>{displayName}</strong>
                  <small>{accountRole(user.is_admin, user.is_coach)}</small>
                </span>
                <button
                  type="button"
                  className="app-bottom-nav__logout"
                  onClick={() => void logout()}
                  aria-label="Выйти из аккаунта"
                  title="Выйти"
                >
                  <AppNavigationIcon name="logout" />
                </button>
              </div>
            </div>
          </nav>

          {moreOpen && (
            <div
              className="app-more-layer"
              onMouseDown={(event) => {
                if (event.target === event.currentTarget) closeMore(true);
              }}
            >
              <div
                id="appMorePanel"
                className="app-more-panel"
                ref={morePanelRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="appMoreTitle"
                onKeyDown={handleMoreKeyDown}
              >
                <header className="app-more-panel__header">
                  <div className="app-more-panel__account">
                    <Avatar name={displayName} photoUrl={user.photo_url} />
                    <span>
                      <strong id="appMoreTitle">{displayName}</strong>
                      <small>{accountRole(user.is_admin, user.is_coach)}</small>
                    </span>
                  </div>
                  <button
                    type="button"
                    className="app-more-panel__close"
                    onClick={() => closeMore(true)}
                    aria-label="Закрыть меню"
                  >
                    <AppNavigationIcon name="close" />
                  </button>
                </header>

                <nav className="app-more-panel__nav" aria-label="Дополнительная навигация">
                  <AppLink
                    to="/app?section=catalog"
                    className="app-more-panel__item"
                    aria-current={path === '/app' && section === 'catalog' ? 'page' : undefined}
                    onClick={() => closeMore()}
                  >
                    <AppNavigationIcon name="catalog" />
                    <span>Упражнения</span>
                  </AppLink>
                  <AppLink
                    to="/app?section=profile"
                    className="app-more-panel__item"
                    aria-current={path === '/app' && section === 'profile' ? 'page' : undefined}
                    onClick={() => closeMore()}
                  >
                    <AppNavigationIcon name="profile" />
                    <span>Профиль и настройки</span>
                  </AppLink>
                  <AppLink
                    to="/knowledge"
                    className="app-more-panel__item"
                    onClick={() => closeMore()}
                  >
                    <AppNavigationIcon name="knowledge" />
                    <span>База знаний</span>
                  </AppLink>
                  {user.is_coach && (
                    <AppLink
                      to="/coach"
                      className="app-more-panel__item"
                      aria-current={path === '/coach' ? 'page' : undefined}
                      onClick={() => closeMore()}
                    >
                      <AppNavigationIcon name="coach" />
                      <span>Кабинет тренера</span>
                    </AppLink>
                  )}
                  {user.is_admin && (
                    <AppLink
                      to="/admin"
                      className="app-more-panel__item"
                      aria-current={path === '/admin' ? 'page' : undefined}
                      onClick={() => closeMore()}
                    >
                      <AppNavigationIcon name="admin" />
                      <span>Администрирование</span>
                    </AppLink>
                  )}
                </nav>

                <div className="app-more-panel__actions">
                  <AppThemeToggle navigation />
                  <button
                    type="button"
                    className="app-more-panel__item app-more-panel__logout"
                    onClick={() => void logout()}
                  >
                    <AppNavigationIcon name="logout" />
                    <span>Выйти из аккаунта</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
