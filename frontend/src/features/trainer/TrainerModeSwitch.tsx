import { AppLink } from '../../shared/navigation/router';
import './trainer-capability.css';

export function TrainerModeSwitch({
  clientName,
  mode,
  sticky = false,
}: {
  clientName?: string;
  mode: 'personal' | 'clients';
  sticky?: boolean;
}) {
  return (
    <div className={`trainer-mode-context${sticky ? ' trainer-mode-context--sticky' : ''}`}>
      <div className="trainer-mode-context__copy">
        <span>Режим</span>
        <strong>{mode === 'clients' ? 'Клиенты' : 'Для себя'}</strong>
        {clientName && <small title={clientName}>Клиент: {clientName}</small>}
      </div>
      <nav className="trainer-mode-switch" aria-label="Режим работы">
        <AppLink
          className={mode === 'personal' ? 'is-active' : ''}
          aria-current={mode === 'personal' ? 'page' : undefined}
          to="/app?section=today"
        >
          Для себя
        </AppLink>
        <AppLink
          className={mode === 'clients' ? 'is-active' : ''}
          aria-current={mode === 'clients' ? 'page' : undefined}
          to="/coach"
        >
          Клиенты
        </AppLink>
      </nav>
    </div>
  );
}
