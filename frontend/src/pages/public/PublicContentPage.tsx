import { useEffect, useState } from 'react';
import {
  categoryForSlug,
  getPublicContentPage,
  publicContent,
  publicGuides,
  type PublicContentPage as PublicContentPageData,
} from '../../content/publicContent';
import { appUrlForHostname } from '../../shared/navigation/appUrl';
import { AppLink, useNavigation } from '../../shared/navigation/router';
import { BrandLogo } from '../../shared/ui/BrandLogo';
import { AppThemeToggle } from '../../shared/ui/AppThemeToggle';
import { useWebTheme } from '../../shared/useWebTheme';
import { applyRouteMetadata } from '../../shared/seo/metadata';
import '../landing/landing.css';
import './public-content.css';

function PublicHeader({ theme }: { theme: 'light' | 'dark' }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [menuOpen]);

  return (
    <header className="landing-header public-header">
      <AppLink className="landing-brand" to="/" aria-label="Your Fitness Coach — на главную">
        <BrandLogo
          className="landing-brand__mark"
          decorative
          surface={theme}
          variant="mark"
          width={36}
          height={36}
        />
        <span>Your Fitness Coach</span>
      </AppLink>
      <nav
        id="public-navigation"
        className={`landing-nav${menuOpen ? ' is-open' : ''}`}
        aria-label="Публичные разделы"
      >
        <AppLink to="/training" onClick={closeMenu}>
          Тренировки
        </AppLink>
        <AppLink to="/nutrition" onClick={closeMenu}>
          Питание
        </AppLink>
        <AppLink to="/progress" onClick={closeMenu}>
          Прогресс
        </AppLink>
        <AppLink to="/knowledge" onClick={closeMenu}>
          База знаний
        </AppLink>
        <AppLink to="/for-trainers" onClick={closeMenu}>
          Тренерам
        </AppLink>
      </nav>
      <div className="landing-header__actions">
        <AppThemeToggle landing />
        <a
          className="landing-button landing-button--compact"
          href={appUrlForHostname(window.location.hostname)}
        >
          Войти
        </a>
        <button
          type="button"
          className={`landing-menu-toggle${menuOpen ? ' is-open' : ''}`}
          aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={menuOpen}
          aria-controls="public-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  );
}

function Breadcrumbs({ page }: { page: PublicContentPageData }) {
  if (page.breadcrumbs.length < 2) return null;
  return (
    <nav className="public-breadcrumbs" aria-label="Хлебные крошки">
      <ol>
        {page.breadcrumbs.map((item, index) => (
          <li key={item.path}>
            {index === page.breadcrumbs.length - 1 ? (
              <span aria-current="page">{item.label}</span>
            ) : (
              <AppLink to={item.path}>{item.label}</AppLink>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

function GuideMetadata({ page }: { page: PublicContentPageData }) {
  if (page.kind !== 'guide' || !page.author || !page.updated) return null;
  const updated = new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${page.updated}T00:00:00Z`));
  return (
    <dl className="public-guide-meta">
      <div>
        <dt>Автор</dt>
        <dd>{page.author.name}</dd>
      </div>
      {page.reviewer && (
        <div>
          <dt>Проверил</dt>
          <dd>{page.reviewer.name}</dd>
        </div>
      )}
      <div>
        <dt>Обновлено</dt>
        <dd>
          <time dateTime={page.updated}>{updated}</time>
        </dd>
      </div>
    </dl>
  );
}

function KnowledgeDirectory() {
  const guides = publicGuides();
  return (
    <section className="public-directory" aria-labelledby="knowledge-directory-title">
      <div className="public-section-heading">
        <p className="landing-kicker">Опубликованные руководства</p>
        <h2 id="knowledge-directory-title">Небольшая база без пустых страниц</h2>
      </div>
      <div className="public-guide-grid">
        {guides.map((guide) => {
          const category = categoryForSlug(guide.category);
          return (
            <article className="public-guide-card" key={guide.path}>
              <p>{category?.label ?? 'Руководство'}</p>
              <h3>
                <AppLink to={guide.path}>{guide.heading}</AppLink>
              </h3>
              <p>{guide.description}</p>
              <AppLink className="public-inline-link" to={guide.path}>
                Читать руководство <span aria-hidden="true">→</span>
              </AppLink>
            </article>
          );
        })}
      </div>
      <div className="public-category-list" aria-label="Категории базы знаний">
        {publicContent.categories.map((category) => {
          const count = guides.filter((guide) => guide.category === category.slug).length;
          return (
            <div key={category.slug}>
              <strong>{category.label}</strong>
              <span>{category.description}</span>
              <small>
                {count > 0 ? `Опубликовано: ${count}` : 'Новые страницы — только после проверки'}
              </small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function RelatedContent({ page }: { page: PublicContentPageData }) {
  return (
    <section className="public-related" aria-labelledby="public-related-title">
      <div className="public-section-heading">
        <p className="landing-kicker">Продолжить</p>
        <h2 id="public-related-title">Связанные материалы и возможности</h2>
      </div>
      <div className="public-related-grid">
        {page.related.map((item) => (
          <AppLink className="public-related-card" to={item.path} key={item.path}>
            <strong>{item.label}</strong>
            {item.description && <span>{item.description}</span>}
            <small aria-hidden="true">Открыть →</small>
          </AppLink>
        ))}
      </div>
    </section>
  );
}

function PublicFooter({ theme }: { theme: 'light' | 'dark' }) {
  return (
    <footer className="landing-footer public-footer">
      <AppLink className="landing-brand" to="/">
        <BrandLogo
          className="landing-brand__mark"
          decorative
          surface={theme}
          variant="mark"
          width={36}
          height={36}
        />
        <span>Your Fitness Coach</span>
      </AppLink>
      <nav aria-label="Разделы в подвале">
        <AppLink to="/training">Тренировки</AppLink>
        <AppLink to="/nutrition">Питание</AppLink>
        <AppLink to="/knowledge">База знаний</AppLink>
        <AppLink to="/for-trainers">Тренерам</AppLink>
      </nav>
      <span>© {new Date().getFullYear()}</span>
    </footer>
  );
}

export default function PublicContentPage() {
  const { path } = useNavigation();
  const page = getPublicContentPage(path);
  const { colorScheme: theme } = useWebTheme();

  useEffect(() => {
    applyRouteMetadata(path);
    document.body.classList.add('landing-mode');
    return () => document.body.classList.remove('landing-mode');
  }, [path]);

  useEffect(() => {
    document.body.classList.toggle('landing-dark-mode', theme === 'dark');
    return () => {
      document.body.classList.remove('landing-dark-mode');
    };
  }, [theme]);

  if (!page || page.kind === 'landing') return null;

  const appUrl = appUrlForHostname(window.location.hostname);

  return (
    <div className={`landing-page landing-page--${theme} public-page`}>
      <a
        className="landing-skip-link"
        href="#public-content"
        onClick={() => document.querySelector<HTMLElement>('#public-content')?.focus()}
      >
        К содержимому
      </a>
      <PublicHeader theme={theme} />
      <main id="public-content" className="public-main" tabIndex={-1}>
        <Breadcrumbs page={page} />
        <article className={`public-article public-article--${page.kind}`}>
          <header className="public-hero">
            <div className="public-hero__copy">
              <p className="landing-kicker">{page.eyebrow}</p>
              <h1>{page.heading}</h1>
              <p className="public-hero__lead">{page.intro}</p>
              <GuideMetadata page={page} />
            </div>
            <aside className="public-hero__summary" aria-label="Коротко о странице">
              {page.highlights ? (
                <ul>
                  {page.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              ) : (
                <>
                  <span>Подход редакции</span>
                  <strong>Факты, ограничения и понятный следующий шаг</strong>
                  <p>Без гарантированных результатов, скрытой рекламы и выдуманной экспертизы.</p>
                </>
              )}
            </aside>
          </header>

          {page.disclaimer && <aside className="public-disclaimer">{page.disclaimer}</aside>}

          <div className="public-body">
            {page.sections.map((section) => (
              <section key={section.heading}>
                <h2>{section.heading}</h2>
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
                {section.points && (
                  <ul>
                    {section.points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>

          {page.kind === 'knowledge-index' && <KnowledgeDirectory />}

          {page.sources && page.sources.length > 0 && (
            <section className="public-sources" aria-labelledby="public-sources-title">
              <div className="public-section-heading">
                <p className="landing-kicker">Проверяемые утверждения</p>
                <h2 id="public-sources-title">Источники</h2>
              </div>
              <ol>
                {page.sources.map((source) => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                    <span>{source.publisher}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          <RelatedContent page={page} />

          {page.cta && (
            <section className="public-cta" aria-labelledby="public-cta-title">
              <div>
                <p className="landing-kicker">Следующий шаг</p>
                <h2 id="public-cta-title">{page.cta.label}</h2>
                <p>{page.cta.description}</p>
              </div>
              <a className="landing-button landing-action" href={appUrl}>
                {page.cta.label}
                <span className="landing-action__arrow" aria-hidden="true">
                  ↗
                </span>
              </a>
            </section>
          )}
        </article>
      </main>
      <PublicFooter theme={theme} />
    </div>
  );
}
