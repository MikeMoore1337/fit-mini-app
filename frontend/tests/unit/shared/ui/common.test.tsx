import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Card } from '../../../../src/shared/ui/common';

describe('Card', () => {
  it('keeps application card content collapsed until its header is opened', () => {
    render(
      <Card title="Расписание" description="Ближайшие восемь недель">
        <p>Содержимое карточки</p>
      </Card>,
    );

    const details = screen.getByText('Расписание').closest('details');
    expect(details).not.toHaveAttribute('open');
    expect(screen.getByText('Содержимое карточки')).not.toBeVisible();

    fireEvent.click(screen.getByText('Расписание'));
    expect(details).toHaveAttribute('open');
    expect(screen.getByText('Содержимое карточки')).toBeVisible();
  });

  it('can keep an essential card expanded', () => {
    render(
      <Card collapsible={false} title="Вход">
        <p>Форма входа</p>
      </Card>,
    );

    expect(screen.queryByText('Вход')?.closest('details')).toBeNull();
    expect(screen.getByText('Форма входа')).toBeVisible();
  });
});
