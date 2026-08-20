import { useEffect, useState } from 'react';
import { browserAppTheme, type AppColorScheme } from '../theme';

export const brandAssetPaths = {
  favicon: {
    dark: '/assets/brand/favicon-dark.svg',
    fallback: '/assets/brand/favicon.svg',
    light: '/assets/brand/favicon-light.svg',
  },
  full: {
    dark: '/assets/brand/yfc-logo-dark.svg',
    light: '/assets/brand/yfc-logo-light.svg',
  },
  mark: {
    dark: '/assets/brand/yfc-mark-dark.svg',
    light: '/assets/brand/yfc-mark-light.svg',
  },
} as const;

type BrandLogoProps = {
  className?: string;
  decorative?: boolean;
  surface?: AppColorScheme;
  variant?: 'full' | 'mark';
  width?: number;
  height?: number;
};

function activeColorScheme(): AppColorScheme {
  const current = document.documentElement.dataset.colorScheme;
  return current === 'dark' || current === 'light' ? current : browserAppTheme();
}

function useActiveColorScheme(): AppColorScheme {
  const [colorScheme, setColorScheme] = useState(activeColorScheme);

  useEffect(() => {
    const documentElement = document.documentElement;
    const observer = new MutationObserver(() => setColorScheme(activeColorScheme()));
    observer.observe(documentElement, { attributes: true, attributeFilter: ['data-color-scheme'] });
    return () => observer.disconnect();
  }, []);

  return colorScheme;
}

export function BrandLogo({
  className,
  decorative = false,
  height,
  surface,
  variant = 'full',
  width,
}: BrandLogoProps) {
  const activeSurface = useActiveColorScheme();
  const resolvedSurface = surface ?? activeSurface;

  return (
    <img
      alt={decorative ? '' : 'Your Fitness Coach'}
      aria-hidden={decorative || undefined}
      className={className}
      height={height}
      src={brandAssetPaths[variant][resolvedSurface]}
      width={width}
    />
  );
}

export function BrandLockup({
  className = '',
  markClassName = '',
}: {
  className?: string;
  markClassName?: string;
}) {
  return (
    <span className={`yfc-lockup ${className}`.trim()}>
      <BrandLogo className={`yfc-lockup__mark ${markClassName}`.trim()} decorative variant="mark" />
      <span className="yfc-lockup__wordmark" aria-hidden="true">
        <strong>Your Fitness</strong>
        <span>Coach</span>
      </span>
    </span>
  );
}
