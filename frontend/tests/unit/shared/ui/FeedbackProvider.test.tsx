import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { FeedbackProvider, useFeedback } from '../../../../src/shared/ui/FeedbackProvider';

function ToastTrigger() {
  const { toast } = useFeedback();
  return (
    <button type="button" onClick={() => toast('Дневник обновлён')}>
      Показать сообщение
    </button>
  );
}

describe('FeedbackProvider motion lifecycle', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', () => ({
      addEventListener: vi.fn(),
      matches: false,
      removeEventListener: vi.fn(),
    }));
  });

  it('keeps toast content through an interruptible exit and then removes it', () => {
    vi.useFakeTimers();
    render(
      <FeedbackProvider>
        <ToastTrigger />
      </FeedbackProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Показать сообщение' }));
    const toast = screen.getByRole('status');
    expect(toast).toHaveAttribute('data-motion-phase', 'opening');

    fireEvent.click(screen.getByRole('button', { name: 'Закрыть сообщение' }));
    expect(toast).toHaveAttribute('data-motion-phase', 'closing');
    expect(toast).toHaveAttribute('aria-hidden', 'true');

    act(() => vi.advanceTimersByTime(261));
    expect(screen.queryByText('Дневник обновлён')).not.toBeInTheDocument();
    vi.useRealTimers();
  });
});
