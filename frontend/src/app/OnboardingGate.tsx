export function OnboardingGate({ children }: { children: React.ReactNode }) {
  // Keep the boundary while older clients and the API still expose onboarding state.
  // Profile completion is optional and must never gate authenticated product routes.
  return <>{children}</>;
}
