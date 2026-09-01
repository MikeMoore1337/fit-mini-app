import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  IconButton,
  Input,
  Metric,
  SemanticCard,
  SectionHeader,
  SegmentedControl,
  Select,
  Skeleton,
  Surface,
} from '../../../../src/shared/ui/common';

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

  it('keeps a semantic summary visible and exposes the expanded state', () => {
    render(
      <Card family="training" summary="3 тренировки в неделю" title="Моя программа">
        <p>Подробный план</p>
      </Card>,
    );

    const details = screen.getByText('Моя программа').closest('details');
    const disclosure = screen.getByText('Моя программа').closest('summary');
    expect(details).toHaveAttribute('data-semantic-family', 'training');
    expect(screen.getByText('3 тренировки в неделю')).toBeVisible();
    expect(disclosure).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(disclosure!);
    expect(disclosure).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Подробный план')).toBeVisible();
  });
});

describe('design-system primitives', () => {
  it('renders controls with semantic variants and accessible labels', () => {
    render(
      <>
        <Button variant="secondary">Отменить</Button>
        <IconButton aria-label="Закрыть">×</IconButton>
        <Field hint="Укажите актуальный вес" label="Вес" labelFor="weight">
          <Input id="weight" inputMode="decimal" placeholder="72.4" />
        </Field>
        <Field error="Выберите уровень" label="Уровень" labelFor="level">
          <Select id="level">
            <option value="">Не выбран</option>
          </Select>
        </Field>
      </>,
    );

    expect(screen.getByRole('button', { name: 'Отменить' })).toHaveClass('ui-button--secondary');
    expect(screen.getByRole('button', { name: 'Закрыть' })).toHaveClass('ui-icon-button');
    expect(screen.getByLabelText('Вес')).toHaveClass('ui-input');
    expect(screen.getByText('Укажите актуальный вес')).toHaveClass('ui-field__hint');
    expect(screen.getByLabelText('Уровень')).toHaveClass('ui-select');
    expect(screen.getByRole('alert')).toHaveTextContent('Выберите уровень');
  });

  it('keeps state, metric and surface roles available for new screens', () => {
    const retry = vi.fn();
    render(
      <Surface elevated>
        <SectionHeader description="За неделю" title="Прогресс" />
        <Metric hint="относительно прошлой недели" label="Вес" value="72,4 кг" />
        <Badge tone="success">В норме</Badge>
        <Skeleton height="24px" width="100%" />
        <EmptyState title="Данных пока нет" />
        <ErrorState message="Сеть недоступна" retry={retry} />
      </Surface>,
    );

    expect(screen.getByText('Прогресс').closest('.ui-section-header')).not.toBeNull();
    expect(screen.getByText('72,4 кг')).toHaveClass('ui-metric__value');
    expect(screen.getByText('В норме')).toHaveClass('ui-badge--success');
    expect(document.querySelector('.ui-skeleton')).not.toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it('renders one reusable compact action card with an explicit family', () => {
    render(
      <SemanticCard
        action={<a href="/app?section=nutrition">Добавить</a>}
        family="nutrition"
        icon="nav-nutrition"
        summary="1 640 из 2 100 ккал"
        title="Питание"
        variant="action"
      />,
    );

    const card = screen.getByRole('article', { name: 'Питание' });
    expect(card).toHaveAttribute('data-semantic-family', 'nutrition');
    expect(card).toHaveAttribute('data-card-variant', 'action');
    expect(screen.getByRole('link', { name: 'Добавить' })).toBeVisible();
  });

  it('supports keyboard selection for segmented controls', () => {
    const onChange = vi.fn();
    render(
      <SegmentedControl
        ariaLabel="Период"
        onChange={onChange}
        options={[
          { label: 'Неделя', value: 'week' },
          { label: 'Месяц', value: 'month' },
        ]}
        value="week"
      />,
    );

    const week = screen.getByRole('tab', { name: 'Неделя' });
    fireEvent.keyDown(week, { key: 'ArrowRight' });
    expect(onChange).toHaveBeenCalledWith('month');
  });
});
