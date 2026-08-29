import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useDocumentScrollLock } from '../../../src/shared/ui/useModalA11y';

function Lock({ open }: { open: boolean }) {
  useDocumentScrollLock(open);
  return null;
}

describe('useDocumentScrollLock', () => {
  afterEach(() => {
    cleanup();
    document.documentElement.removeAttribute('style');
    document.body.removeAttribute('style');
    vi.restoreAllMocks();
  });

  it('locks the document for nested overlays and restores exact scroll position last', () => {
    Object.defineProperty(window, 'scrollX', { configurable: true, value: 12 });
    Object.defineProperty(window, 'scrollY', { configurable: true, value: 240 });
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    document.body.style.overflow = 'auto';

    const view = render(
      <>
        <Lock open />
        <Lock open />
      </>,
    );

    expect(document.documentElement.style.overflow).toBe('hidden');
    expect(document.body.style.position).toBe('fixed');
    expect(document.body.style.top).toBe('-240px');

    view.rerender(<Lock open />);
    expect(document.body.style.position).toBe('fixed');
    expect(scrollTo).not.toHaveBeenCalled();

    view.rerender(<Lock open={false} />);
    expect(document.documentElement.style.overflow).toBe('');
    expect(document.body.style.overflow).toBe('auto');
    expect(document.body.style.position).toBe('');
    expect(scrollTo).toHaveBeenCalledWith(12, 240);
  });
});
