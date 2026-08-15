from __future__ import annotations

import html
import json
from dataclasses import dataclass
from urllib.parse import urlparse

from fitminiapp_api.core.config import settings

INDEX_ROBOTS = "index, follow"
NOINDEX_ROBOTS = "noindex, nofollow"

LANDING_TITLE = "Your Fitness Coach — тренировки, питание и прогресс в браузере и Telegram"
LANDING_DESCRIPTION = (
    "Your Fitness Coach помогает планировать тренировки, фиксировать результаты, "
    "рассчитывать ориентиры КБЖУ и отслеживать прогресс в браузере и Telegram."
)
LANDING_OG_DESCRIPTION = (
    "Планируйте тренировки, фиксируйте результаты и отслеживайте прогресс на "
    "компьютере или смартфоне. Telegram Mini App — дополнительная возможность."
)


@dataclass(frozen=True)
class SeoMetadata:
    title: str
    description: str
    robots: str
    canonical_url: str | None = None
    structured_data: tuple[dict[str, object], ...] = ()


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


def metadata_for_path(path: str) -> SeoMetadata:
    """Keep indexability decisions in one place for browser and crawler responses."""

    if path == "/":
        canonical_url = f"{public_origin()}/"
        return SeoMetadata(
            title=LANDING_TITLE,
            description=LANDING_DESCRIPTION,
            robots=INDEX_ROBOTS,
            canonical_url=canonical_url,
            structured_data=(
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
                            "description": LANDING_DESCRIPTION,
                        },
                    ],
                },
            ),
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
    if metadata.canonical_url:
        canonical = html.escape(metadata.canonical_url, quote=True)
        tags.extend(
            [
                f'<link rel="canonical" href="{canonical}" />',
                f'<meta property="og:title" content="{html.escape(metadata.title, quote=True)}" />',
                f'<meta property="og:description" content="{html.escape(LANDING_OG_DESCRIPTION, quote=True)}" />',
                '<meta property="og:type" content="website" />',
                f'<meta property="og:url" content="{canonical}" />',
            ]
        )
    for item in metadata.structured_data:
        payload = json.dumps(item, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        tags.append(f'<script type="application/ld+json">{payload}</script>')
    return "\n    ".join(tags)


def render_frontend_document(template: str, path: str) -> tuple[str, SeoMetadata]:
    """Inject route metadata into the Vite HTML entry without creating a second app."""

    metadata = metadata_for_path(path)
    rendered = template.replace("<!-- seo-head -->", render_metadata(metadata))
    if rendered == template:
        rendered = template.replace("</head>", f"    {render_metadata(metadata)}\n  </head>")
    return rendered, metadata
