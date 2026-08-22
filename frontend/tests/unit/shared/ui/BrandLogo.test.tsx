import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BrandLockup, BrandLogo, brandAssetPaths } from '../../../../src/shared/ui/BrandLogo';

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

  it('lets a lockup select the asset for its local surface independently of the page theme', () => {
    const { container } = render(<BrandLockup surface="dark" />);

    expect(container.querySelector('.yfc-lockup__mark')).toHaveAttribute(
      'src',
      brandAssetPaths.mark.dark,
    );
  });

  it('exposes theme-aware favicon variants with a legacy fallback', () => {
    expect(brandAssetPaths.favicon).toEqual({
      dark: '/assets/brand/favicon-dark.svg',
      fallback: '/assets/brand/favicon.svg',
      light: '/assets/brand/favicon-light.svg',
    });
  });
});
