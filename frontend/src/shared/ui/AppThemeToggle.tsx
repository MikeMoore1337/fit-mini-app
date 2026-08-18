import type { ChangeEvent } from 'react';
import type { ThemePreference } from '../theme';
import { useWebTheme } from '../useWebTheme';
import { ThemeIcon } from './ThemeIcon';

const THEME_LABELS: Record<ThemePreference, string> = {
  system: 'Системная',
  light: 'Светлая',
  dark: 'Тёмная',
};

function WebThemeControl({ landing, navigation }: { landing: boolean; navigation: boolean }) {
  const { colorScheme, preference, setPreference } = useWebTheme();
  const className = landing
    ? 'landing-theme-toggle app-theme-control--landing'
    : navigation
      ? 'app-bottom-nav__btn app-theme-toggle--nav'
      : 'app-theme-toggle';
  const onChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setPreference(event.currentTarget.value as ThemePreference);
  };

  return (
    <span className={className} title={`Тема: ${THEME_LABELS[preference].toLowerCase()}`}>
      <span
        className={navigation ? 'app-bottom-nav__icon' : 'app-theme-toggle__icon'}
        aria-hidden="true"
      >
        <ThemeIcon theme={colorScheme} />
      </span>
      {navigation && <span className="app-bottom-nav__label">{THEME_LABELS[preference]}</span>}
      <select
        className="app-theme-control__select"
        aria-label="Тема оформления"
        value={preference}
        onChange={onChange}
      >
        <option value="system">Системная</option>
        <option value="light">Светлая</option>
        <option value="dark">Тёмная</option>
      </select>
    </span>
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
