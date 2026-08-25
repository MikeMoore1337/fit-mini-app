import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Icon } from '../../../../src/shared/ui/Icon';

describe('Icon', () => {
  it('uses the canonical 24px currentColor contract at supported optical sizes', () => {
    const { container } = render(<Icon name="nav-progress" size={20} />);
    const icon = container.querySelector('[data-icon="nav-progress"]');

    expect(icon).toHaveAttribute('viewBox', '0 0 24 24');
    expect(icon).toHaveAttribute('stroke', 'currentColor');
    expect(icon).toHaveAttribute('width', '20');
    expect(icon).toHaveAttribute('aria-hidden', 'true');
  });

  it('keeps an explicit accessible name only when the icon carries meaning itself', () => {
    const { container } = render(<Icon label="Нет доступа" name="permission-denied" />);
    const icon = container.querySelector('[data-icon="permission-denied"]');

    expect(icon).toHaveAttribute('role', 'img');
    expect(icon).toHaveAttribute('aria-label', 'Нет доступа');
    expect(icon).not.toHaveAttribute('aria-hidden');
  });

  it('keeps the exercise catalogue glyph sparse at compact optical sizes', () => {
    const { container } = render(<Icon name="nav-exercise-catalog" size={16} />);
    const icon = container.querySelector('[data-icon="nav-exercise-catalog"]');

    expect(icon).toHaveAttribute('width', '16');
    expect(icon?.querySelectorAll('path')).toHaveLength(1);
    expect(icon?.querySelectorAll('rect')).toHaveLength(2);
    expect(icon?.querySelectorAll('line')).toHaveLength(1);
  });
});
