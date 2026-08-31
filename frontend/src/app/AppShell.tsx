import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { AppLink, useNavigation } from '../shared/navigation/router';
import { AppThemeToggle } from '../shared/ui/AppThemeToggle';
import { BrandLockup } from '../shared/ui/BrandLogo';
import { AppNavigationIcon, type AppNavigationIconName } from './AppNavigationIcon';
import { useOptionalAuth } from './AuthProvider';
import { useTelegramOverlayBackButton } from '../shared/telegram/useTelegramOverlayBackButton';
import { useDocumentScrollLock } from '../shared/ui/useModalA11y';
import { useMotionPresence } from '../shared/ui/useMotionPresence';

export type AppSection = 'today' | 'progress' | 'programs' | 'catalog' | 'nutrition' | 'profile';

const AVATAR_EMOJIS = ['🏋️', '💪', '🏃', '🚴', '🥗', '⚡', '🎯', '🔥'] as const;

const APP_DESTINATIONS: ReadonlyArray<{
  section: AppSection;
  label: string;
  icon: AppNavigationIconName;
}> = [
  { section: 'today', label: 'Сегодня', icon: 'today' },
  { section: 'programs', label: 'Программа', icon: 'plan' },
  { section: 'nutrition', label: 'Питание', icon: 'nutrition' },
  { section: 'progress', label: 'Прогресс', icon: 'progress' },
];

export interface DemoAppShellConfig {
  activeSection: string;
  brandTo: string;
  destinations: ReadonlyArray<{
    key: string;
    label: string;
    icon: AppNavigationIconName;
    to: string;
  }>;
  displayName: string;
  exitTo: string;
  menuTitle?: string;
  moreLinks: ReadonlyArray<{ label: string; to: string }>;
  onReset(): void;
  resetDisabled?: boolean;
}

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

function accountRole(isRoot: boolean, isCoach: boolean): string {
  if (isRoot) return isCoach ? 'Root · Тренер' : 'Root · Личный режим';
  if (isCoach) return 'Тренер';
  return 'Клиент';
}

export function AppShell({
  children,
  demo,
  narrow = false,
  section,
}: {
  children: React.ReactNode;
  demo?: DemoAppShellConfig;
  narrow?: boolean;
  section?: AppSection;
}) {
  const auth = useOptionalAuth();
  const user = auth?.user ?? null;
  const logout = auth?.logout;
  const { path } = useNavigation();
  const [moreOpen, setMoreOpen] = useState(false);
  const morePresence = useMotionPresence({
    closingAnimationName: 'app-more-backdrop-out',
    openingAnimationName: 'app-more-panel-in',
  });
  const morePanelRef = useRef<HTMLDivElement>(null);
  const moreTriggerRef = useRef<HTMLElement | null>(null);
  const displayName =
    demo?.displayName ||
    user?.profile?.full_name ||
    user?.first_name ||
    user?.username ||
    'Пользователь';
  const secondaryActive = section === 'catalog' || section === 'profile';
  const isMiniApp = Boolean(window.Telegram?.WebApp?.initData);
  const shellDestinations = demo?.destinations ?? APP_DESTINATIONS;
  const brandTo = demo?.brandTo ?? '/app?section=today';
  const shellVisible = Boolean(user || demo);
  const morePresent = moreOpen || morePresence.present;
  const morePhase = moreOpen && morePresence.phase === 'closed' ? 'open' : morePresence.phase;

  const closeMore = (restoreFocus = false) => {
    setMoreOpen(false);
    morePresence.hide();
    if (restoreFocus) moreTriggerRef.current?.focus();
  };
  const openMore = (trigger?: HTMLElement) => {
    if (trigger) moreTriggerRef.current = trigger;
    setMoreOpen(true);
    morePresence.show();
  };
  useTelegramOverlayBackButton(morePresent, () => closeMore(true));

  useDocumentScrollLock(morePresent);

  useEffect(() => {
    if (moreOpen) {
      morePanelRef.current?.querySelector<HTMLElement>('button, a')?.focus();
    }
  }, [moreOpen]);

  if (!demo && !auth) {
    throw new Error('AppShell must be used inside AuthProvider unless demo config is provided');
  }

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
      {!demo && shellVisible && (
        <header className="app-mobile-header">
          <AppLink
            className="app-mobile-header__brand"
            to={brandTo}
            aria-label="Your Fitness Coach — сегодня"
          >
            <BrandLockup markClassName="app-mobile-header__brand-mark" />
          </AppLink>
          <button
            id="appProfileButton"
            type="button"
            className={`app-mobile-header__profile${moreOpen || secondaryActive ? ' is-active' : ''}`}
            aria-expanded={moreOpen}
            aria-controls="appMorePanel"
            aria-label="Открыть профиль и настройки"
            onClick={(event) => (moreOpen ? closeMore() : openMore(event.currentTarget))}
          >
            <Avatar name={displayName} photoUrl={user?.photo_url} />
          </button>
        </header>
      )}
      <main id="appContent" className={`container app-shell__content${narrow ? ' narrow' : ''}`}>
        {children}
      </main>
      {shellVisible && (
        <>
          <nav
            id="appBottomNav"
            className={`app-bottom-nav${demo ? ' app-bottom-nav--demo' : ''}`}
            aria-label="Основная навигация"
          >
            <AppLink
              className="app-bottom-nav__brand"
              to={brandTo}
              aria-label={demo ? 'Your Fitness Coach — демо' : 'Your Fitness Coach — сегодня'}
            >
              <BrandLockup markClassName="app-bottom-nav__brand-mark" />
            </AppLink>

            <div className="app-bottom-nav__primary">
              {shellDestinations.map((destination) => {
                const destinationKey =
                  'section' in destination ? destination.section : destination.key;
                const active = demo
                  ? demo.activeSection === destinationKey
                  : path === '/app' && section === destinationKey;
                return (
                  <AppLink
                    key={destinationKey}
                    to={
                      'to' in destination ? destination.to : `/app?section=${destination.section}`
                    }
                    className={`app-bottom-nav__btn${active ? ' is-active' : ''}`}
                    aria-current={active ? 'page' : undefined}
                  >
                    <AppNavigationIcon name={destination.icon} />
                    <span className="app-bottom-nav__label">{destination.label}</span>
                  </AppLink>
                );
              })}
              {demo && (
                <button
                  id="appMoreButton"
                  type="button"
                  className={`app-bottom-nav__btn app-bottom-nav__more${moreOpen ? ' is-active' : ''}`}
                  aria-expanded={moreOpen}
                  aria-controls="appMorePanel"
                  onClick={(event) => (moreOpen ? closeMore() : openMore(event.currentTarget))}
                >
                  <AppNavigationIcon name="more" />
                  <span className="app-bottom-nav__label">Сценарии</span>
                </button>
              )}
            </div>

            {!demo && (
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
                {user?.is_coach && (
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
                {user?.is_root && !isMiniApp && (
                  <AppLink
                    to="/admin"
                    className={`app-bottom-nav__btn${path === '/admin' ? ' is-active' : ''}`}
                    aria-current={path === '/admin' ? 'page' : undefined}
                    title="Администрирование"
                  >
                    <AppNavigationIcon name="admin" />
                    <span className="app-bottom-nav__label">Админ-панель</span>
                  </AppLink>
                )}
              </div>
            )}

            <div className="app-bottom-nav__utility">
              <AppThemeToggle navigation />
              <div className="app-bottom-nav__account">
                {demo ? (
                  <Avatar name={displayName} photoUrl={user?.photo_url} />
                ) : (
                  <button
                    type="button"
                    className="app-bottom-nav__account-entry"
                    aria-expanded={moreOpen}
                    aria-controls="appMorePanel"
                    aria-label="Открыть меню аккаунта"
                    onClick={(event) => (moreOpen ? closeMore() : openMore(event.currentTarget))}
                  >
                    <Avatar name={displayName} photoUrl={user?.photo_url} />
                    <span>
                      <strong className="app-bottom-nav__account-name">{displayName}</strong>
                      <small className="app-bottom-nav__account-role">
                        {accountRole(Boolean(user?.is_root), Boolean(user?.is_coach))}
                      </small>
                    </span>
                  </button>
                )}
                {demo && (
                  <>
                    <strong className="app-bottom-nav__account-name">{displayName}</strong>
                    <small className="app-bottom-nav__account-role">Отдельная сессия</small>
                  </>
                )}
                {demo ? (
                  <AppLink
                    className="app-bottom-nav__logout"
                    to={demo.exitTo}
                    aria-label="Выйти из демо"
                    title="Выйти из демо"
                  >
                    <AppNavigationIcon name="logout" />
                  </AppLink>
                ) : (
                  <button
                    type="button"
                    className="app-bottom-nav__logout"
                    onClick={() => void logout?.()}
                    aria-label="Выйти из аккаунта"
                    title="Выйти"
                  >
                    <AppNavigationIcon name="logout" />
                  </button>
                )}
              </div>
            </div>
          </nav>

          {morePresent && (
            <div
              className="app-more-layer"
              data-motion-phase={morePhase}
              aria-hidden={morePhase === 'closing' || undefined}
              onAnimationEnd={morePresence.onAnimationEnd}
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
                aria-hidden={morePhase === 'closing' || undefined}
                inert={morePhase === 'closing'}
                onKeyDown={handleMoreKeyDown}
              >
                <header className="app-more-panel__header">
                  <div className="app-more-panel__account">
                    <Avatar name={displayName} photoUrl={user?.photo_url} />
                    <span>
                      <strong id="appMoreTitle">
                        {demo?.menuTitle ?? (demo ? displayName : 'Профиль и настройки')}
                      </strong>
                      <small>
                        {demo
                          ? 'Отдельная сессия'
                          : accountRole(Boolean(user?.is_root), Boolean(user?.is_coach))}
                      </small>
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
                  {demo &&
                    demo.moreLinks.map((item) => (
                      <AppLink
                        className="app-more-panel__item"
                        key={item.to}
                        onClick={() => closeMore()}
                        to={item.to}
                      >
                        <AppNavigationIcon name="plan" />
                        <span>{item.label}</span>
                      </AppLink>
                    ))}
                  {!demo && (
                    <>
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
                      {user?.is_coach && (
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
                      {user?.is_root && !isMiniApp && (
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
                    </>
                  )}
                </nav>

                <div className="app-more-panel__actions">
                  <AppThemeToggle navigation />
                  {demo ? (
                    <>
                      <button
                        type="button"
                        className="app-more-panel__item"
                        disabled={demo.resetDisabled}
                        onClick={() => {
                          demo.onReset();
                          closeMore();
                        }}
                      >
                        <AppNavigationIcon name="progress" />
                        <span>Сбросить демо</span>
                      </button>
                      <AppLink
                        className="app-more-panel__item app-more-panel__logout"
                        onClick={() => closeMore()}
                        to={demo.exitTo}
                      >
                        <AppNavigationIcon name="logout" />
                        <span>Выйти из демо</span>
                      </AppLink>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="app-more-panel__item app-more-panel__logout"
                      onClick={() => void logout?.()}
                    >
                      <AppNavigationIcon name="logout" />
                      <span>Выйти из аккаунта</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
