import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import PublicContentPage from '../../../../src/pages/public/PublicContentPage';
import { NavigationProvider } from '../../../../src/shared/navigation/router';
import { applyRouteMetadata } from '../../../../src/shared/seo/metadata';

function renderPath(path: string) {
  window.history.replaceState({}, '', path);
  return render(
    <NavigationProvider>
      <PublicContentPage />
    </NavigationProvider>,
  );
}

describe('PublicContentPage', () => {
  afterEach(() => {
    cleanup();
    document.head
      .querySelectorAll(
        'meta[name="description"], meta[name="robots"], meta[name="yandex"], meta[property^="og:"], link[rel="canonical"], script[type="application/ld+json"]',
      )
      .forEach((element) => element.remove());
    document.body.className = '';
    localStorage.clear();
    window.history.replaceState({}, '', '/');
  });

  it.each([
    ['/training', /план тренировки, который остаётся перед глазами/i],
    ['/nutrition', /ориентиры кбжу без обещаний/i],
    ['/progress', /прогресс, который можно проверить/i],
    ['/for-trainers', /кабинет тренера для программ/i],
    ['/knowledge', /материалы, которые помогают понять/i],
  ])('renders a distinct indexable intent for %s', (path, heading) => {
    renderPath(path);

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      'content',
      'index, follow',
    );
    expect(document.querySelector('link[rel="canonical"]')).toHaveAttribute(
      'href',
      `${window.location.origin}${path}`,
    );
    expect(screen.getByRole('navigation', { name: 'Публичные разделы' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Хлебные крошки' })).toBeInTheDocument();
  });

  it('publishes truthful article metadata and visible editorial context for a guide', () => {
    const serverStructuredData = document.createElement('script');
    serverStructuredData.type = 'application/ld+json';
    serverStructuredData.textContent = '{"@type":"WebSite"}';
    document.head.append(serverStructuredData);
    renderPath('/knowledge/training/how-to-start-strength-training');

    expect(screen.getByText('Редакция Your Fitness Coach')).toBeInTheDocument();
    expect(screen.getByText(/15 августа 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/общий образовательный характер/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Источники' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /WHO Guidelines/i })).toHaveAttribute(
      'href',
      'https://www.who.int/publications/i/item/9789240015128',
    );

    const structuredData = document.querySelector<HTMLScriptElement>(
      'script[type="application/ld+json"][data-public-seo]',
    );
    expect(document.querySelectorAll('script[type="application/ld+json"]')).toHaveLength(1);
    expect(structuredData).not.toBeNull();
    const payload = JSON.parse(structuredData?.textContent ?? '{}') as {
      '@graph': Array<{ '@type': string }>;
    };
    expect(payload['@graph'].map((item) => item['@type'])).toEqual(['Article', 'BreadcrumbList']);
    expect(document.querySelector('meta[property="og:type"]')).toHaveAttribute(
      'content',
      'article',
    );

    applyRouteMetadata('/app');
    expect(document.querySelector('script[type="application/ld+json"]')).toBeNull();
    expect(document.querySelector('link[rel="canonical"]')).toBeNull();
  });

  it('keeps all knowledge categories in one maintainable directory without empty routes', () => {
    renderPath('/knowledge');

    expect(
      screen.getByRole('heading', { name: /небольшая база без пустых страниц/i }),
    ).toBeVisible();
    expect(screen.getAllByText(/Опубликовано: 1/i)).toHaveLength(2);
    expect(screen.getAllByText(/Новые страницы — только после проверки/i)).toHaveLength(3);
    expect(
      screen.getByRole('link', { name: /как начать силовые тренировки и не потерять план/i }),
    ).toHaveAttribute('href', '/knowledge/training/how-to-start-strength-training');
    expect(screen.queryByRole('link', { name: 'Упражнения' })).not.toBeInTheDocument();
  });

  it('supports keyboard skip navigation and an accessible mobile menu', () => {
    renderPath('/progress');

    const skipLink = screen.getByRole('link', { name: 'К содержимому' });
    skipLink.focus();
    fireEvent.click(skipLink);
    expect(document.querySelector('#public-content')).toHaveFocus();

    const menu = document.querySelector<HTMLButtonElement>('.landing-menu-toggle');
    expect(menu).not.toBeNull();
    expect(menu).toHaveAttribute('aria-label', 'Открыть меню');
    if (!menu) throw new Error('Mobile menu control is missing');
    fireEvent.click(menu);
    expect(menu).toHaveAttribute('aria-expanded', 'true');
    fireEvent.click(
      within(screen.getByRole('navigation', { name: 'Публичные разделы' })).getByRole('link', {
        name: 'Питание',
      }),
    );
    expect(screen.getByRole('heading', { level: 1, name: /ориентиры кбжу/i })).toBeInTheDocument();
  });
});
