import { useWebTheme } from '../useWebTheme';
import { ThemeIcon } from './ThemeIcon';

function WebThemeControl({ landing, navigation }: { landing: boolean; navigation: boolean }) {
  const { colorScheme, setPreference } = useWebTheme();
  const nextTheme = colorScheme === 'dark' ? 'light' : 'dark';
  const actionLabel = nextTheme === 'dark' ? 'Включить тёмную тему' : 'Включить светлую тему';
  const className = landing
    ? 'landing-theme-toggle app-theme-control--landing'
    : navigation
      ? 'app-bottom-nav__btn app-theme-toggle--nav'
      : 'app-theme-toggle';

  return (
    <button
      type="button"
      className={className}
      aria-label={actionLabel}
      title={actionLabel}
      onClick={() => setPreference(nextTheme)}
    >
      <span
        className={navigation ? 'app-bottom-nav__icon' : 'app-theme-toggle__icon'}
        aria-hidden="true"
      >
        <ThemeIcon theme={nextTheme} />
      </span>
      {navigation && <span className="app-bottom-nav__label">Тема</span>}
    </button>
  );
}

export function AppThemeToggle({
  landing = false,
  navigation = false,
}: {
  landing?: boolean;
  navigation?: boolean;
}) {
  if (window.Telegram?.WebApp?.initData) return null;
  return <WebThemeControl landing={landing} navigation={navigation} />;
}
