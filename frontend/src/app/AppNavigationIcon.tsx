import { Icon, type IconName } from '../shared/ui/Icon';

export type AppNavigationIconName =
  | 'today'
  | 'plan'
  | 'progress'
  | 'nutrition'
  | 'more'
  | 'catalog'
  | 'profile'
  | 'knowledge'
  | 'coach'
  | 'admin'
  | 'logout'
  | 'close';

const navigationIcons: Record<AppNavigationIconName, IconName> = {
  today: 'nav-today',
  plan: 'nav-plan',
  progress: 'nav-progress',
  nutrition: 'nav-nutrition',
  more: 'nav-more',
  catalog: 'nav-exercise-catalog',
  profile: 'nav-profile',
  knowledge: 'nav-knowledge',
  coach: 'nav-coach',
  admin: 'nav-admin',
  logout: 'logout',
  close: 'close',
};

export function AppNavigationIcon({ name }: { name: AppNavigationIconName }) {
  return (
    <span className="app-bottom-nav__icon" aria-hidden="true">
      <Icon name={navigationIcons[name]} />
    </span>
  );
}
