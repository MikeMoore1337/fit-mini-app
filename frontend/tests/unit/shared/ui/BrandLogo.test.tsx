import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BrandLogo, brandAssetPaths } from '../../../../src/shared/ui/BrandLogo';

describe('BrandLogo', () => {
  it('uses the canonical full logo variant with an accessible product name', () => {
    render(<BrandLogo surface="dark" />);

    expect(screen.getByRole('img', { name: 'Your Fitness Coach' })).toHaveAttribute(
      'src',
      brandAssetPaths.full.dark,
    );
  });

  it('keeps a repeated mark decorative and selects its explicit surface variant', () => {
    const { container } = render(<BrandLogo decorative surface="light" variant="mark" />);
    const image = container.querySelector('img');

    expect(image).toHaveAttribute('alt', '');
    expect(image).toHaveAttribute('aria-hidden', 'true');
    expect(image).toHaveAttribute('src', brandAssetPaths.mark.light);
  });
});
