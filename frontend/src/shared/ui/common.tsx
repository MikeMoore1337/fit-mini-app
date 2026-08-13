import type { ReactNode } from 'react';

export function Card({
  title,
  description,
  actions,
  children,
  className = '',
  collapsible = true,
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  /** Application cards start collapsed to keep long pages easy to scan. */
  collapsible?: boolean;
}) {
  if (collapsible && (title || description)) {
    return (
      <details className={`card card-disclosure ${className}`.trim()}>
        <summary>
          <span>
            {title && <h2>{title}</h2>}
            {description && <small>{description}</small>}
          </span>
          <DisclosureIcon />
        </summary>
        <div className="card-disclosure__body">
          {actions && <div className="card-disclosure__actions">{actions}</div>}
          {children}
        </div>
      </details>
    );
  }

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

export function CloseIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      className={`ui-icon ${className}`.trim()}
      viewBox="0 0 16 16"
      aria-hidden="true"
      focusable="false"
    >
      <path d="m4 4 8 8M12 4l-8 8" />
    </svg>
  );
}

export function ChevronIcon({
  direction = 'right',
  className = '',
}: {
  direction?: 'left' | 'right' | 'down';
  className?: string;
}) {
  const path = {
    left: 'm10 3.5-4.5 4.5 4.5 4.5',
    right: 'm6 3.5 4.5 4.5L6 12.5',
    down: 'm3.5 6 4.5 4.5L12.5 6',
  }[direction];
  return (
    <svg
      className={`ui-icon ${className}`.trim()}
      viewBox="0 0 16 16"
      aria-hidden="true"
      focusable="false"
    >
      <path d={path} />
    </svg>
  );
}

export function CheckIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      className={`ui-icon ${className}`.trim()}
      viewBox="0 0 16 16"
      aria-hidden="true"
      focusable="false"
    >
      <path d="m3.5 8 3 3 6-6" />
    </svg>
  );
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
