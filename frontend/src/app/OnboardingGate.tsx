import { useAuth } from './AuthProvider';
import { Redirect } from '../shared/navigation/router';

export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  if (user?.onboarding?.status === 'required') {
    return <Redirect to="/onboarding?next=%2Fapp" />;
  }

  return <>{children}</>;
}
