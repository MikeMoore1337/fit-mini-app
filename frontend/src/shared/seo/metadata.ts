import { getPublicContentPage, type PublicContentPage } from '../../content/publicContent';

export const INDEX_ROBOTS = 'index, follow';
export const NOINDEX_ROBOTS = 'noindex, nofollow';
export const SOCIAL_IMAGE_PATH = '/assets/brand/yfc-social-preview.png';
export const SOCIAL_IMAGE_ALT =
  'Your Fitness Coach — тренировки, питание и прогресс в браузере и Telegram';

function upsertMeta(
  selector: string,
  attribute: 'name' | 'property',
  value: string,
  content: string,
) {
  let element = document.head.querySelector<HTMLMetaElement>(selector);
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attribute, value);
    document.head.append(element);
  }
  element.content = content;
}

function canonicalOrigin(): string {
  return window.location.origin;
}

function absoluteUrl(path: string): string {
  return path === '/' ? `${canonicalOrigin()}/` : `${canonicalOrigin()}${path}`;
}

function removeSocialMetadata(): void {
  document.head
    .querySelectorAll('meta[property^="og:"], meta[name^="twitter:"]')
    .forEach((element) => element.remove());
}

function breadcrumbStructuredData(page: PublicContentPage): Record<string, unknown> | null {
  if (page.breadcrumbs.length < 2) return null;
  return {
    '@type': 'BreadcrumbList',
    itemListElement: page.breadcrumbs.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.label,
      item: absoluteUrl(item.path),
    })),
  };
}

export function structuredDataForPage(page: PublicContentPage): Record<string, unknown>[] {
  const url = absoluteUrl(page.path);
  if (page.kind === 'landing') {
    return [
      {
        '@context': 'https://schema.org',
        '@graph': [
          { '@type': 'Organization', name: 'Your Fitness Coach', url },
          { '@type': 'WebSite', name: 'Your Fitness Coach', url },
          {
            '@type': 'SoftwareApplication',
            name: 'Your Fitness Coach',
            applicationCategory: 'HealthApplication',
            operatingSystem: 'Web, Telegram',
            url,
            description: page.description,
          },
        ],
      },
    ];
  }

  const breadcrumb = breadcrumbStructuredData(page);
  const mainEntity: Record<string, unknown> =
    page.kind === 'guide'
      ? {
          '@type': 'Article',
          headline: page.heading,
          description: page.description,
          mainEntityOfPage: url,
          dateModified: page.updated,
          author: page.author ? { '@type': page.author.type, name: page.author.name } : undefined,
          publisher: { '@type': 'Organization', name: 'Your Fitness Coach' },
        }
      : {
          '@type': page.kind === 'knowledge-index' ? 'CollectionPage' : 'WebPage',
          name: page.heading,
          description: page.description,
          url,
          isPartOf: {
            '@type': 'WebSite',
            name: 'Your Fitness Coach',
            url: absoluteUrl('/'),
          },
        };

  return [
    {
      '@context': 'https://schema.org',
      '@graph': breadcrumb ? [mainEntity, breadcrumb] : [mainEntity],
    },
  ];
}

function replaceStructuredData(page: PublicContentPage | undefined): void {
  document.head
    .querySelectorAll('script[type="application/ld+json"]')
    .forEach((element) => element.remove());
  if (!page) return;
  for (const item of structuredDataForPage(page)) {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.dataset.publicSeo = 'true';
    script.textContent = JSON.stringify(item).replaceAll('</', '<\\/');
    document.head.append(script);
  }
}

export function applyRouteMetadata(path: string): void {
  const page = getPublicContentPage(path);
  const title = page?.title ?? 'Your Fitness Coach';
  const description = page?.description ?? 'Личный интерфейс Your Fitness Coach.';
  const robots = page ? INDEX_ROBOTS : NOINDEX_ROBOTS;

  document.title = title;
  upsertMeta('meta[name="description"]', 'name', 'description', description);
  upsertMeta('meta[name="robots"]', 'name', 'robots', robots);
  upsertMeta('meta[name="yandex"]', 'name', 'yandex', robots);

  let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (page) {
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.append(canonical);
    }
    canonical.href = absoluteUrl(page.path);
    upsertMeta('meta[property="og:title"]', 'property', 'og:title', title);
    upsertMeta('meta[property="og:description"]', 'property', 'og:description', page.ogDescription);
    upsertMeta(
      'meta[property="og:type"]',
      'property',
      'og:type',
      page.kind === 'guide' ? 'article' : 'website',
    );
    upsertMeta('meta[property="og:url"]', 'property', 'og:url', canonical.href);
    upsertMeta('meta[property="og:site_name"]', 'property', 'og:site_name', 'Your Fitness Coach');
    upsertMeta('meta[property="og:locale"]', 'property', 'og:locale', 'ru_RU');
    upsertMeta('meta[property="og:image"]', 'property', 'og:image', absoluteUrl(SOCIAL_IMAGE_PATH));
    upsertMeta('meta[property="og:image:type"]', 'property', 'og:image:type', 'image/png');
    upsertMeta('meta[property="og:image:width"]', 'property', 'og:image:width', '1200');
    upsertMeta('meta[property="og:image:height"]', 'property', 'og:image:height', '630');
    upsertMeta('meta[property="og:image:alt"]', 'property', 'og:image:alt', SOCIAL_IMAGE_ALT);
    upsertMeta('meta[name="twitter:card"]', 'name', 'twitter:card', 'summary_large_image');
    upsertMeta('meta[name="twitter:title"]', 'name', 'twitter:title', title);
    upsertMeta(
      'meta[name="twitter:description"]',
      'name',
      'twitter:description',
      page.ogDescription,
    );
    upsertMeta(
      'meta[name="twitter:image"]',
      'name',
      'twitter:image',
      absoluteUrl(SOCIAL_IMAGE_PATH),
    );
    upsertMeta('meta[name="twitter:image:alt"]', 'name', 'twitter:image:alt', SOCIAL_IMAGE_ALT);
  } else {
    canonical?.remove();
    removeSocialMetadata();
  }
  replaceStructuredData(page);
}
