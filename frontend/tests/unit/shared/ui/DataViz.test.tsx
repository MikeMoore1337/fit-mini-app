import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  QuantitativeProgress,
  RankedBars,
  StepProgress,
  TaskProgress,
  TimeSeriesChart,
} from '../../../../src/shared/ui/DataViz';

const points = [
  { key: '2026-08-01', label: '1 авг.', value: 10, target: 12 },
  { key: '2026-08-02', label: '2 авг.', value: null, target: 12, status: 'Нет данных' },
  { key: '2026-08-03', label: '3 авг.', value: 20, target: 12, targetChanged: true },
  { key: '2026-08-04', label: '4 авг.', value: 0, target: 14, status: 'Подтверждённый ноль' },
  { key: '2026-08-05', label: '5 авг.', value: 30, target: 14 },
] as const;

describe('TimeSeriesChart', () => {
  it('keeps missing values disconnected while rendering a confirmed zero', () => {
    const { container } = render(
      <TimeSeriesChart
        includeZero
        metric="Калории"
        period="1—5 августа"
        points={points}
        unit="ккал"
      />,
    );

    expect(container.querySelectorAll('.data-viz-chart__actual')).toHaveLength(2);
    expect(screen.getByText('Подтверждённый ноль')).toBeInTheDocument();
    expect(screen.getAllByText('0 ккал').length).toBeGreaterThan(0);
    expect(screen.getByText('цель изменилась')).toBeInTheDocument();
    expect(screen.getAllByText('Нет данных').length).toBeGreaterThan(0);
    expect(
      Array.from(container.querySelectorAll('.data-viz-chart__target')).some((path) =>
        path.getAttribute('d')?.match(/L [\d.]+ [\d.]+ L [\d.]+ [\d.]+/),
      ),
    ).toBe(true);
  });

  it('supports keyboard point selection and exposes the same data in a table', () => {
    const { container } = render(
      <TimeSeriesChart metric="Масса тела" period="Август" points={points} unit="кг" />,
    );

    const navigation = within(container).getByRole('group', {
      name: 'Навигация по точкам графика',
    });
    navigation.focus();
    fireEvent.keyDown(navigation, { key: 'ArrowLeft' });

    expect(navigation).toHaveFocus();
    expect(screen.getAllByText('4 авг.').length).toBeGreaterThan(0);
    const table = within(container).getByRole('table', { name: 'Масса тела, Август' });
    expect(within(table).getAllByRole('row')).toHaveLength(points.length + 1);
  });
});

describe('progress primitives', () => {
  it('keeps quantitative, task and workflow-step progress semantically distinct', () => {
    const { container } = render(
      <>
        <QuantitativeProgress label="Калории" maximum={2100} unit="ккал" value={2030} />
        <TaskProgress completed={3} label="Подходы" total={5} />
        <StepProgress current={2} labels={['Цель', 'Опыт', 'План']} />
        <RankedBars
          items={[{ label: 'Ноги', value: 12, unit: 'подх.' }]}
          label="Нагрузка по группам"
        />
      </>,
    );

    expect(
      screen.getByRole('progressbar', { name: /Калории: 2.*030 из 2.*100 ккал/ }),
    ).toBeVisible();
    expect(screen.getByRole('progressbar', { name: 'Подходы: 3 из 5' })).toBeVisible();
    expect(screen.getByRole('list', { name: 'Шаг 2 из 3' })).toBeVisible();
    expect(screen.getByRole('list', { name: 'Нагрузка по группам' })).toHaveTextContent(
      'Ноги12 подх.',
    );
    expect(container.querySelector('[data-progress-kind="quantitative"]')).toBeInTheDocument();
    expect(container.querySelector('[data-progress-kind="task"]')).toBeInTheDocument();
  });
});
