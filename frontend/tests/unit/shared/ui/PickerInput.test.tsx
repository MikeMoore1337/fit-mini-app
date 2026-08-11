import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DateInput } from '../../../../src/shared/ui/PickerInput';

describe('DateInput', () => {
  it('одинаково оформляет поле даты и передаёт атрибуты нативному input', () => {
    render(
      <DateInput
        aria-label="Дата проверки"
        controlClassName="custom-date-control"
        min="2026-01-01"
        value="2026-08-11"
        readOnly
      />,
    );

    const input = screen.getByLabelText('Дата проверки');
    expect(input).toHaveAttribute('type', 'date');
    expect(input).toHaveAttribute('min', '2026-01-01');
    expect(input).toHaveValue('2026-08-11');
    expect(input.parentElement).toHaveClass('date-control', 'custom-date-control');
  });
});
