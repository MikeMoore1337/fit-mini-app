import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
} from 'react';

interface NavigationContextValue {
  path: string;
  search: string;
  navigate(to: string, replace?: boolean): void;
}

const NavigationContext = createContext<NavigationContextValue | null>(null);

function focusedContextReturn(search: string): string | null {
  const params = new URLSearchParams(search);
  const workoutId = params.get('workout_id');
  if (workoutId && /^\d+$/.test(workoutId) && Number(workoutId) > 0) {
    return '/app?section=progress';
  }
  if (params.get('weekly_review') === '1') return '/app';
  return null;
}

export function NavigationProvider({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useState(() => ({
    path: window.location.pathname,
    search: window.location.search,
  }));

  useEffect(() => {
    const onPopState = () =>
      setLocation({ path: window.location.pathname, search: window.location.search });
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = useCallback((to: string, replace = false) => {
    if (replace) window.history.replaceState({}, '', to);
    else window.history.pushState({}, '', to);
    setLocation({ path: window.location.pathname, search: window.location.search });
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);

  useEffect(() => {
    const backButton = window.Telegram?.WebApp?.BackButton;
    if (!backButton) return;
    const focusedReturn = location.path === '/app' ? focusedContextReturn(location.search) : null;
    if (
      (location.path === '/app' && !focusedReturn) ||
      location.path === '/onboarding' ||
      location.path === '/'
    ) {
      backButton.hide();
      return;
    }
    const goBack = () => navigate(focusedReturn ?? '/app', Boolean(focusedReturn));
    backButton.onClick(goBack);
    backButton.show();
    return () => {
      backButton.offClick(goBack);
      backButton.hide();
    };
  }, [navigate, location.path, location.search]);

  const value = useMemo(
    () => ({ path: location.path, search: location.search, navigate }),
    [location.path, location.search, navigate],
  );
  return <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>;
}

export function useNavigation(): NavigationContextValue {
  const value = useContext(NavigationContext);
  if (!value) throw new Error('useNavigation must be used inside NavigationProvider');
  return value;
}

export function AppLink({
  to,
  className,
  children,
  onClick,
  ...anchorAttributes
}: {
  to: string;
  children: React.ReactNode;
} & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'>) {
  const { navigate } = useNavigation();
  return (
    <a
      href={to}
      className={className}
      {...anchorAttributes}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented) return;
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
          return;
        event.preventDefault();
        navigate(to);
      }}
    >
      {children}
    </a>
  );
}

export function Redirect({ to }: { to: string }) {
  const { navigate } = useNavigation();
  useEffect(() => navigate(to, true), [navigate, to]);
  return null;
}
