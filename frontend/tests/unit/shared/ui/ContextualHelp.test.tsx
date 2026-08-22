import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ContextualHelp } from '../../../../src/shared/ui/ContextualHelp';

describe('ContextualHelp', () => {
  afterEach(() => window.history.replaceState({}, '', '/'));

  it('keeps the short explanation inline and exposes the public article deliberately', () => {
    render(
      <ContextualHelp articlePath="/knowledge/training/repetitions-in-reserve">
        <p>Короткое объяснение</p>
      </ContextualHelp>,
    );

    const summary = screen.getByText('Что это?');
    const details = summary.closest('details');
    expect(details).not.toHaveAttribute('open');

    fireEvent.click(summary);
    expect(details).toHaveAttribute('open');
    expect(screen.getByText('Короткое объяснение')).toBeVisible();
    expect(screen.getByRole('link', { name: /подробнее на сайте/i })).toHaveAttribute(
      'href',
      '/knowledge/training/repetitions-in-reserve',
    );
    expect(screen.getByRole('link', { name: /подробнее на сайте/i })).toHaveAttribute(
      'target',
      '_blank',
    );

    summary.focus();
    fireEvent.click(summary);
    expect(details).not.toHaveAttribute('open');
    expect(summary).toHaveFocus();
  });
});
