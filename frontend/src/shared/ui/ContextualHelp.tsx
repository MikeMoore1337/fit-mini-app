import type { ReactNode } from 'react';
import { publicUrlForHostname } from '../navigation/appUrl';

export function ContextualHelp({
  children,
  articlePath,
  summary = 'Что это?',
}: {
  children: ReactNode;
  articlePath: string;
  summary?: string;
}) {
  return (
    <details className="contextual-help">
      <summary>{summary}</summary>
      <div className="contextual-help__body">
        <div>{children}</div>
        <a
          className="contextual-help__link"
          href={publicUrlForHostname(window.location.hostname, articlePath)}
          target="_blank"
          rel="noreferrer"
        >
          Подробнее на сайте <span aria-hidden="true">↗</span>
        </a>
      </div>
    </details>
  );
}
