export const INDEX_ROBOTS = 'index, follow';
export const NOINDEX_ROBOTS = 'noindex, nofollow';

const LANDING_TITLE = 'Your Fitness Coach — тренировки, питание и прогресс в браузере и Telegram';
const LANDING_DESCRIPTION =
  'Your Fitness Coach помогает планировать тренировки, фиксировать результаты, рассчитывать ориентиры КБЖУ и отслеживать прогресс в браузере и Telegram.';
const LANDING_OG_DESCRIPTION =
  'Планируйте тренировки, фиксируйте результаты и отслеживайте прогресс на компьютере или смартфоне. Telegram Mini App — дополнительная возможность.';

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

export function applyRouteMetadata(path: string): void {
  const isPublicLanding = path === '/';
  const title = isPublicLanding ? LANDING_TITLE : 'Your Fitness Coach';
  const description = isPublicLanding
    ? LANDING_DESCRIPTION
    : 'Личный интерфейс Your Fitness Coach.';
  const robots = isPublicLanding ? INDEX_ROBOTS : NOINDEX_ROBOTS;

  document.title = title;
  upsertMeta('meta[name="description"]', 'name', 'description', description);
  upsertMeta('meta[name="robots"]', 'name', 'robots', robots);
  upsertMeta('meta[name="yandex"]', 'name', 'yandex', robots);

  let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (isPublicLanding) {
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.append(canonical);
    }
    canonical.href = `${canonicalOrigin()}/`;
    upsertMeta('meta[property="og:title"]', 'property', 'og:title', title);
    upsertMeta(
      'meta[property="og:description"]',
      'property',
      'og:description',
      LANDING_OG_DESCRIPTION,
    );
    upsertMeta('meta[property="og:type"]', 'property', 'og:type', 'website');
    upsertMeta('meta[property="og:url"]', 'property', 'og:url', canonical.href);
  } else {
    canonical?.remove();
    document.head.querySelectorAll('meta[property^="og:"]').forEach((element) => element.remove());
    document.head
      .querySelectorAll('script[type="application/ld+json"]')
      .forEach((element) => element.remove());
  }
}
