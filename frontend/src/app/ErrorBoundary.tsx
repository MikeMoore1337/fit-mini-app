import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled application error', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main className="container" role="alert">
        <section className="card error-state fatal-error">
          <h1>Приложение не смогло продолжить работу</h1>
          <p className="muted">
            Обновите экран. Несохранённые черновики форм останутся на устройстве.
          </p>
          <button type="button" onClick={() => window.location.reload()}>
            Обновить приложение
          </button>
        </section>
      </main>
    );
  }
}
