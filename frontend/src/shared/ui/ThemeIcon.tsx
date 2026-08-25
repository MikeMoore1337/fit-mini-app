import type { AppColorScheme } from '../theme';
import { Icon } from './Icon';

export function ThemeIcon({ theme }: { theme: AppColorScheme }) {
  return <Icon name={theme === 'dark' ? 'theme-moon' : 'theme-sun'} />;
}
