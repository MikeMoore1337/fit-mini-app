import { StrictMode, lazy, Suspense, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './app/AuthProvider';
import { AuthGate } from './app/AuthGate';
import { OnboardingGate } from './app/OnboardingGate';
import { ErrorBoundary } from './app/ErrorBoundary';
import { FeedbackProvider } from './shared/ui/FeedbackProvider';
import { OnlineStatus } from './shared/ui/OnlineStatus';
import { LoadingState } from './shared/ui/common';
import { isTelegramLaunch } from './shared/telegram/launch';
import { applyPlatformTheme, useTelegram } from './shared/telegram/useTelegram';
import { NavigationProvider, Redirect, useNavigation } from './shared/navigation/router';
import { applyRouteMetadata } from './shared/seo/metadata';
import { isPublicContentPath } from './content/publicContent';
import { clearAllDemoSessions } from './features/demo/demoApi';
import './styles/legacy.css';
import './styles/react.css';
import './styles/design-system.css';
import './styles/design-v2.css';
import './styles/data-viz.css';

const MiniAppPage = lazy(() => import('./pages/miniapp/MiniAppPage'));
const ProgressReportPage = lazy(() => import('./pages/reports/ProgressReportPage'));
const CoachPage = lazy(() => import('./pages/coach/CoachPage'));
const AdminPage = lazy(() => import('./pages/admin/AdminPage'));
const LandingPage = lazy(() => import('./pages/landing/LandingPage'));
const DemoPage = lazy(() => import('./pages/demo/DemoPage'));
const PublicContentPage = lazy(() => import('./pages/public/PublicContentPage'));
const VerifyEmailPage = lazy(() => import('./pages/auth/VerifyEmailPage'));
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const JoinCoachPage = lazy(() => import('./pages/join/JoinCoachPage'));
const OnboardingPage = lazy(() => import('./pages/onboarding/OnboardingPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
function loadTelegramSdk(): Promise<void> {
  if (!isTelegramLaunch(window.location) || window.Telegram?.WebApp) {
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-web-app.js';
    script.async = true;
    script.addEventListener('load', () => resolve(), { once: true });
    script.addEventListener('error', () => resolve(), { once: true });
    document.head.append(script);
  });
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
    mutations: { retry: 0 },
  },
});

function AuthenticatedRoute({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthGate>{children}</AuthGate>
    </AuthProvider>
  );
}

function AppRoutes() {
  const { path } = useNavigation();
  useEffect(() => applyRouteMetadata(path), [path]);
  if (path === '/') return <LandingPage />;
  if (path === '/demo') {
    if (isTelegramLaunch(window.location)) return <Redirect to="/app" />;
    return <DemoPage />;
  }
  if (isPublicContentPath(path)) {
    if (window.Telegram?.WebApp?.initData) return <Redirect to="/app" />;
    return <PublicContentPage />;
  }
  if (path === '/login')
    return (
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    );
  if (path === '/verify-email')
    return (
      <AuthProvider>
        <VerifyEmailPage />
      </AuthProvider>
    );
  if (path === '/reset-password')
    return (
      <AuthProvider>
        <ResetPasswordPage />
      </AuthProvider>
    );
  if (path.startsWith('/join/')) {
    const token = path.slice('/join/'.length);
    if (/^[A-Za-z0-9_-]{20,128}$/.test(token)) {
      return (
        <AuthenticatedRoute>
          <JoinCoachPage token={token} />
        </AuthenticatedRoute>
      );
    }
  }
  if (path === '/app')
    return (
      <AuthenticatedRoute>
        <OnboardingGate>
          <MiniAppPage />
        </OnboardingGate>
      </AuthenticatedRoute>
    );
  if (path === '/app/report')
    return (
      <AuthenticatedRoute>
        <OnboardingGate>
          <ProgressReportPage />
        </OnboardingGate>
      </AuthenticatedRoute>
    );
  if (path === '/onboarding')
    return (
      <AuthenticatedRoute>
        <OnboardingPage />
      </AuthenticatedRoute>
    );
  if (path === '/coach')
    return (
      <AuthenticatedRoute>
        <CoachPage />
      </AuthenticatedRoute>
    );
  if (path === '/admin')
    return (
      <AuthenticatedRoute>
        <AdminPage />
      </AuthenticatedRoute>
    );
  return <NotFoundPage />;
}

function Root() {
  useTelegram();
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <FeedbackProvider>
          <NavigationProvider>
            <OnlineStatus />
            <Suspense
              fallback={
                <main className="container">
                  <LoadingState />
                </main>
              }
            >
              <AppRoutes />
            </Suspense>
          </NavigationProvider>
        </FeedbackProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

function renderApp(): void {
  applyPlatformTheme(window.Telegram?.WebApp ?? null);
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Root />
    </StrictMode>,
  );
}

async function bootstrap(): Promise<void> {
  if (isTelegramLaunch(window.location)) {
    await loadTelegramSdk();
  }
  if (window.location.pathname === '/demo' && isTelegramLaunch(window.location)) {
    clearAllDemoSessions();
  }
  renderApp();
}

void bootstrap();
