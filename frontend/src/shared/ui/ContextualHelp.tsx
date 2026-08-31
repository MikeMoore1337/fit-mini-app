import type { ReactNode } from 'react';
import { PublicWebLink } from '../navigation/PublicWebLink';
import { Icon } from './Icon';

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
        <PublicWebLink className="contextual-help__link" path={articlePath}>
          Подробнее на сайте <Icon name="external-link" size={16} />
        </PublicWebLink>
      </div>
    </details>
  );
}
