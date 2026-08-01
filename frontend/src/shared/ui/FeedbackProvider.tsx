import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  danger?: boolean;
}

interface FeedbackValue {
  toast(message: string, type?: 'success' | 'error'): void;
  confirm(options: ConfirmOptions): Promise<boolean>;
}

interface ConfirmState extends ConfirmOptions {
  resolve(value: boolean): void;
}

const FeedbackContext = createContext<FeedbackValue | null>(null);

export function FeedbackProvider({ children }: { children: React.ReactNode }) {
  const [toastState, setToastState] = useState<{ message: string; type: string } | null>(null);
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);
  const toastTimer = useRef<number | null>(null);

  const toast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    setToastState({ message, type });
    toastTimer.current = window.setTimeout(() => setToastState(null), 3200);
  }, []);

  const confirm = useCallback(
    (options: ConfirmOptions) =>
      new Promise<boolean>((resolve) => setConfirmState({ ...options, resolve })),
    [],
  );

  const finishConfirm = (value: boolean) => {
    confirmState?.resolve(value);
    setConfirmState(null);
  };

  const value = useMemo(() => ({ toast, confirm }), [toast, confirm]);
  return (
    <FeedbackContext.Provider value={value}>
      {children}
      {toastState && (
        <div className={`toast${toastState.type === 'error' ? ' error' : ''}`} role="status">
          {toastState.message}
        </div>
      )}
      {confirmState && (
        <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
          <button
            className="modal__backdrop"
            aria-label="Закрыть"
            onClick={() => finishConfirm(false)}
          />
          <div className="modal__panel card">
            <h3 id="confirm-title" className="modal__title">
              {confirmState.title}
            </h3>
            <p className="modal__body muted">{confirmState.message}</p>
            <div className="modal__actions toolbar wrap">
              <button type="button" className="secondary" onClick={() => finishConfirm(false)}>
                Отмена
              </button>
              <button
                type="button"
                className={confirmState.danger === false ? '' : 'btn-danger'}
                onClick={() => finishConfirm(true)}
              >
                {confirmState.confirmText ?? 'Подтвердить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </FeedbackContext.Provider>
  );
}

export function useFeedback(): FeedbackValue {
  const value = useContext(FeedbackContext);
  if (!value) throw new Error('useFeedback must be used inside FeedbackProvider');
  return value;
}
