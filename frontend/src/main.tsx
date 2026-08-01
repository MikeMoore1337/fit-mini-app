import { StrictMode, lazy, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './app/AuthProvider';
import { AuthGate } from './app/AuthGate';
import { FeedbackProvider } from './shared/ui/FeedbackProvider';
import { LoadingState } from './shared/ui/common';
import { useTelegram } from './shared/telegram/useTelegram';
import { NavigationProvider, Redirect, useNavigation } from './shared/navigation/router';
import './styles/legacy.css';
import './styles/react.css';

const MiniAppPage = lazy(() => import('./pages/miniapp/MiniAppPage'));
const CoachPage = lazy(() => import('./pages/coach/CoachPage'));
const AdminPage = lazy(() => import('./pages/admin/AdminPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
    mutations: { retry: 0 },
  },
});

function AppRoutes() {
  const { path } = useNavigation();
  if (path === '/') return <Redirect to="/app" />;
  if (path === '/app')
    return (
      <AuthGate>
        <MiniAppPage />
      </AuthGate>
    );
  if (path === '/coach')
    return (
      <AuthGate>
        <CoachPage />
      </AuthGate>
    );
  if (path === '/admin')
    return (
      <AuthGate>
        <AdminPage />
      </AuthGate>
    );
  return <NotFoundPage />;
}

function Root() {
  useTelegram();
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <FeedbackProvider>
          <NavigationProvider>
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
      </AuthProvider>
    </QueryClientProvider>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
