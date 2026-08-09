import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AriaAttributes,
} from 'react';

interface NavigationContextValue {
  path: string;
  navigate(to: string, replace?: boolean): void;
}

const NavigationContext = createContext<NavigationContextValue | null>(null);

export function NavigationProvider({ children }: { children: React.ReactNode }) {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = useCallback((to: string, replace = false) => {
    if (replace) window.history.replaceState({}, '', to);
    else window.history.pushState({}, '', to);
    setPath(window.location.pathname);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);

  useEffect(() => {
    const backButton = window.Telegram?.WebApp?.BackButton;
    if (!backButton) return;
    if (path === '/app' || path === '/') {
      backButton.hide();
      return;
    }
    const goBack = () => navigate('/app');
    backButton.onClick(goBack);
    backButton.show();
    return () => {
      backButton.offClick(goBack);
      backButton.hide();
    };
  }, [navigate, path]);

  const value = useMemo(() => ({ path, navigate }), [navigate, path]);
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
  ...ariaAttributes
}: {
  to: string;
  className?: string;
  children: React.ReactNode;
} & AriaAttributes) {
  const { navigate } = useNavigation();
  return (
    <a
      href={to}
      className={className}
      {...ariaAttributes}
      onClick={(event) => {
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
