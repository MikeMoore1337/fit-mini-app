from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from fitminiapp_api.core.config import settings

INDEX_ROBOTS = "index, follow"
NOINDEX_ROBOTS = "noindex, nofollow"
_PUBLIC_FALLBACK_PATTERN = re.compile(
    r"<!-- public-fallback-start -->.*?<!-- public-fallback-end -->",
    re.DOTALL,
)


@dataclass(frozen=True)
class SeoMetadata:
    title: str
    description: str
    robots: str
    canonical_url: str | None = None
    og_description: str | None = None
    og_type: str = "website"
    structured_data: tuple[dict[str, object], ...] = ()


def _public_content_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    configured_dist = Path(os.environ.get("FRONTEND_DIST_DIR", project_root / "frontend" / "dist"))
    candidates = (
        Path("/app/frontend-dist/publicContent.json"),
        configured_dist / "publicContent.json",
        project_root / "frontend" / "src" / "content" / "publicContent.json",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("Public content manifest is missing from the frontend build")


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Public content field {field!r} must be a non-empty string")
    return value


@lru_cache
def public_pages() -> tuple[dict[str, object], ...]:
    payload = json.loads(_public_content_path().read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("pages"), list):
        raise RuntimeError("Public content manifest must contain a pages array")
    pages: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for raw_page in payload["pages"]:
        if not isinstance(raw_page, dict):
            raise RuntimeError("Every public content page must be an object")
        page = cast(dict[str, object], raw_page)
        path = _required_string(page.get("path"), field="path")
        if not path.startswith("/") or (path != "/" and path.endswith("/")):
            raise RuntimeError(f"Public content path is not canonical: {path!r}")
        if path in seen_paths:
            raise RuntimeError(f"Duplicate public content path: {path!r}")
        for field in ("kind", "title", "description", "ogDescription", "heading", "intro"):
            _required_string(page.get(field), field=field)
        seen_paths.add(path)
        pages.append(page)
    return tuple(pages)


def public_page_paths() -> tuple[str, ...]:
    return tuple(_required_string(page["path"], field="path") for page in public_pages())


def canonical_landing_domain() -> str:
    """Return the configured public host without its non-canonical www prefix."""

    return settings.landing_domain.strip().lower().rstrip(".").removeprefix("www.")


def public_origin() -> str:
    """Return the one production origin allowed in the public search surface."""

    landing_domain = canonical_landing_domain()
    if landing_domain:
        return f"https://{landing_domain}"
    return settings.frontend_base_url.rstrip("/")


def frontend_host() -> str:
    return (urlparse(settings.frontend_base_url).hostname or "").lower().rstrip(".")


def public_page_for_path(path: str) -> dict[str, object] | None:
    return next(
        (page for page in public_pages() if _required_string(page["path"], field="path") == path),
        None,
    )


def _absolute_public_url(path: str) -> str:
    return f"{public_origin()}/" if path == "/" else f"{public_origin()}{path}"


def _breadcrumbs_schema(page: dict[str, object]) -> dict[str, object] | None:
    raw_breadcrumbs = page.get("breadcrumbs")
    if not isinstance(raw_breadcrumbs, list) or len(raw_breadcrumbs) < 2:
        return None
    items: list[dict[str, object]] = []
    for position, raw_item in enumerate(raw_breadcrumbs, start=1):
        if not isinstance(raw_item, dict):
            raise RuntimeError("Public content breadcrumbs must be objects")
        item = cast(dict[str, object], raw_item)
        item_path = _required_string(item.get("path"), field="breadcrumbs.path")
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": _required_string(item.get("label"), field="breadcrumbs.label"),
                "item": _absolute_public_url(item_path),
            }
        )
    return {"@type": "BreadcrumbList", "itemListElement": items}


def _structured_data_for_page(page: dict[str, object]) -> tuple[dict[str, object], ...]:
    kind = _required_string(page["kind"], field="kind")
    path = _required_string(page["path"], field="path")
    canonical_url = _absolute_public_url(path)
    description = _required_string(page["description"], field="description")
    if kind == "landing":
        return (
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "Organization",
                        "name": "Your Fitness Coach",
                        "url": canonical_url,
                    },
                    {
                        "@type": "WebSite",
                        "name": "Your Fitness Coach",
                        "url": canonical_url,
                    },
                    {
                        "@type": "SoftwareApplication",
                        "name": "Your Fitness Coach",
                        "applicationCategory": "HealthApplication",
                        "operatingSystem": "Web, Telegram",
                        "url": canonical_url,
                        "description": description,
                    },
                ],
            },
        )

    if kind == "guide":
        author = page.get("author")
        author_schema: dict[str, object] | None = None
        if isinstance(author, dict):
            typed_author = cast(dict[str, object], author)
            author_schema = {
                "@type": _required_string(typed_author.get("type"), field="author.type"),
                "name": _required_string(typed_author.get("name"), field="author.name"),
            }
        main_entity: dict[str, object] = {
            "@type": "Article",
            "headline": _required_string(page["heading"], field="heading"),
            "description": description,
            "mainEntityOfPage": canonical_url,
            "publisher": {"@type": "Organization", "name": "Your Fitness Coach"},
        }
        if author_schema:
            main_entity["author"] = author_schema
        if isinstance(page.get("updated"), str):
            main_entity["dateModified"] = page["updated"]
    else:
        main_entity = {
            "@type": "CollectionPage" if kind == "knowledge-index" else "WebPage",
            "name": _required_string(page["heading"], field="heading"),
            "description": description,
            "url": canonical_url,
            "isPartOf": {
                "@type": "WebSite",
                "name": "Your Fitness Coach",
                "url": _absolute_public_url("/"),
            },
        }

    graph = [main_entity]
    breadcrumbs = _breadcrumbs_schema(page)
    if breadcrumbs:
        graph.append(breadcrumbs)
    return ({"@context": "https://schema.org", "@graph": graph},)


def metadata_for_path(path: str) -> SeoMetadata:
    """Keep indexability decisions in one place for browser and crawler responses."""

    page = public_page_for_path(path)
    if page:
        return SeoMetadata(
            title=_required_string(page["title"], field="title"),
            description=_required_string(page["description"], field="description"),
            robots=INDEX_ROBOTS,
            canonical_url=_absolute_public_url(path),
            og_description=_required_string(page["ogDescription"], field="ogDescription"),
            og_type="article" if page["kind"] == "guide" else "website",
            structured_data=_structured_data_for_page(page),
        )
    return SeoMetadata(
        title="Your Fitness Coach",
        description="Личный интерфейс Your Fitness Coach.",
        robots=NOINDEX_ROBOTS,
    )


def render_metadata(metadata: SeoMetadata) -> str:
    """Render only server-controlled metadata; no user content is inserted here."""

    tags = [
        f"<title>{html.escape(metadata.title)}</title>",
        f'<meta name="description" content="{html.escape(metadata.description, quote=True)}" />',
        f'<meta name="robots" content="{metadata.robots}" />',
        f'<meta name="yandex" content="{metadata.robots}" />',
    ]
    if metadata.canonical_url and settings.google_site_verification.strip():
        tags.append(
            '<meta name="google-site-verification" content="'
            f'{html.escape(settings.google_site_verification.strip(), quote=True)}" />'
        )
    if metadata.canonical_url and settings.yandex_verification.strip():
        tags.append(
            '<meta name="yandex-verification" content="'
            f'{html.escape(settings.yandex_verification.strip(), quote=True)}" />'
        )
    if metadata.canonical_url:
        canonical = html.escape(metadata.canonical_url, quote=True)
        tags.extend(
            [
                f'<link rel="canonical" href="{canonical}" />',
                f'<meta property="og:title" content="{html.escape(metadata.title, quote=True)}" />',
                '<meta property="og:description" content="'
                f'{html.escape(metadata.og_description or metadata.description, quote=True)}" />',
                f'<meta property="og:type" content="{metadata.og_type}" />',
                f'<meta property="og:url" content="{canonical}" />',
            ]
        )
    for item in metadata.structured_data:
        payload = json.dumps(item, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        tags.append(f'<script type="application/ld+json">{payload}</script>')
    return "\n    ".join(tags)


def _link_markup(item: dict[str, object]) -> str:
    path = html.escape(_required_string(item.get("path"), field="link.path"), quote=True)
    label = html.escape(_required_string(item.get("label"), field="link.label"))
    description = item.get("description")
    detail = f"<span>{html.escape(description)}</span>" if isinstance(description, str) else ""
    return f'<li><a href="{path}">{label}</a>{detail}</li>'


def render_public_fallback(path: str) -> str:
    """Render the public page's meaningful text and links without requiring JavaScript."""

    page = public_page_for_path(path)
    if not page:
        return ""
    parts = [
        '<main class="seo-fallback">',
        '<nav aria-label="Публичные разделы"><a href="/">Главная</a> '
        '<a href="/training">Тренировки</a> <a href="/nutrition">Питание</a> '
        '<a href="/progress">Прогресс</a> <a href="/knowledge">База знаний</a> '
        '<a href="/for-trainers">Для тренеров</a></nav>',
    ]
    breadcrumbs = page.get("breadcrumbs")
    if isinstance(breadcrumbs, list) and len(breadcrumbs) >= 2:
        breadcrumb_items = "".join(
            _link_markup(cast(dict[str, object], item))
            for item in breadcrumbs
            if isinstance(item, dict)
        )
        parts.append(f'<nav aria-label="Хлебные крошки"><ol>{breadcrumb_items}</ol></nav>')
    parts.extend(
        (
            f"<h1>{html.escape(_required_string(page['heading'], field='heading'))}</h1>",
            f"<p>{html.escape(_required_string(page['intro'], field='intro'))}</p>",
        )
    )
    if isinstance(page.get("author"), dict) and isinstance(page.get("updated"), str):
        author = cast(dict[str, object], page["author"])
        parts.append(
            "<p>Автор: "
            f"{html.escape(_required_string(author.get('name'), field='author.name'))}. "
            f'<time datetime="{html.escape(cast(str, page["updated"]), quote=True)}">'
            f"Обновлено {html.escape(cast(str, page['updated']))}</time>.</p>"
        )
    if isinstance(page.get("disclaimer"), str):
        parts.append(f"<aside>{html.escape(cast(str, page['disclaimer']))}</aside>")
    raw_sections = page.get("sections")
    if isinstance(raw_sections, list):
        for raw_section in raw_sections:
            if not isinstance(raw_section, dict):
                continue
            section = cast(dict[str, object], raw_section)
            parts.append(
                f"<section><h2>{html.escape(_required_string(section.get('heading'), field='section.heading'))}</h2>"
            )
            paragraphs = section.get("paragraphs")
            if isinstance(paragraphs, list):
                parts.extend(
                    f"<p>{html.escape(paragraph)}</p>"
                    for paragraph in paragraphs
                    if isinstance(paragraph, str)
                )
            points = section.get("points")
            if isinstance(points, list):
                items = "".join(
                    f"<li>{html.escape(point)}</li>" for point in points if isinstance(point, str)
                )
                if items:
                    parts.append(f"<ul>{items}</ul>")
            parts.append("</section>")
    if page.get("kind") == "knowledge-index":
        guide_links = "".join(
            _link_markup(
                {
                    "path": guide["path"],
                    "label": guide["heading"],
                    "description": guide["description"],
                }
            )
            for guide in public_pages()
            if guide.get("kind") == "guide"
        )
        parts.append(
            f"<section><h2>Опубликованные руководства</h2><ul>{guide_links}</ul></section>"
        )
    sources = page.get("sources")
    if isinstance(sources, list) and sources:
        parts.append("<section><h2>Источники</h2><ol>")
        for raw_source in sources:
            if not isinstance(raw_source, dict):
                continue
            source = cast(dict[str, object], raw_source)
            url = html.escape(_required_string(source.get("url"), field="source.url"), quote=True)
            title = html.escape(_required_string(source.get("title"), field="source.title"))
            publisher = html.escape(
                _required_string(source.get("publisher"), field="source.publisher")
            )
            parts.append(f'<li><a href="{url}">{title}</a> — {publisher}</li>')
        parts.append("</ol></section>")
    related = page.get("related")
    if isinstance(related, list) and related:
        links = "".join(
            _link_markup(cast(dict[str, object], item))
            for item in related
            if isinstance(item, dict)
        )
        parts.append(f"<section><h2>Связанные страницы</h2><ul>{links}</ul></section>")
    cta = page.get("cta")
    if isinstance(cta, dict):
        typed_cta = cast(dict[str, object], cta)
        app_url = f"{settings.frontend_base_url.rstrip('/')}/app"
        parts.append(
            "<section><h2>"
            f"{html.escape(_required_string(typed_cta.get('label'), field='cta.label'))}"
            "</h2><p>"
            f"{html.escape(_required_string(typed_cta.get('description'), field='cta.description'))}"
            f'</p><a href="{html.escape(app_url, quote=True)}">Открыть приложение</a></section>'
        )
    parts.append("</main>")
    return "".join(parts)


def render_frontend_document(template: str, path: str) -> tuple[str, SeoMetadata]:
    """Inject route metadata and public fallback into the Vite HTML entry."""

    metadata = metadata_for_path(path)
    rendered = template.replace("<!-- seo-head -->", render_metadata(metadata))
    if rendered == template:
        rendered = template.replace("</head>", f"    {render_metadata(metadata)}\n  </head>")

    fallback = render_public_fallback(path)
    marked_fallback = f"<!-- public-fallback-start -->{fallback}<!-- public-fallback-end -->"
    if _PUBLIC_FALLBACK_PATTERN.search(rendered):
        rendered = _PUBLIC_FALLBACK_PATTERN.sub(marked_fallback, rendered, count=1)
    elif fallback:
        rendered = rendered.replace('<div id="root"></div>', f'<div id="root">{fallback}</div>')
    return rendered, metadata
