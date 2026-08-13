import type { ReactNode } from 'react';

export function Card({
  title,
  description,
  actions,
  children,
  className = '',
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className}`.trim()}>
      {(title || description || actions) && (
        <div className="section-head">
          <div>
            {title && <h2>{title}</h2>}
            {description && <p className="muted top-gap">{description}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function LoadingState({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="empty-state" aria-busy="true">
      <span className="spinner" />
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({ title, text }: { title: string; text?: string }) {
  return (
    <div className="empty-state">
      <p className="empty-state__title">{title}</p>
      {text && <p className="empty-state__text muted">{text}</p>}
    </div>
  );
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="empty-state error-state">
      <p className="empty-state__title">Не удалось загрузить данные</p>
      <p className="muted">{message}</p>
      {retry && (
        <button type="button" className="secondary" onClick={retry}>
          Повторить
        </button>
      )}
    </div>
  );
}

export function Badge({ children, tone = '' }: { children: ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`.trim()}>{children}</span>;
}

export function DisclosureIcon() {
  return (
    <span className="disclosure-icon" aria-hidden="true">
      <svg viewBox="0 0 16 16" focusable="false">
        <path d="M3.5 8h9" />
        <path className="disclosure-icon__vertical" d="M8 3.5v9" />
      </svg>
    </span>
  );
}
