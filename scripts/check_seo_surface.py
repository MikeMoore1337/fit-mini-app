"""Read-only smoke check for the canonical public SEO surface."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlparse
from xml.etree import ElementTree

PRIVATE_PATH_PREFIXES = (
    "/admin",
    "/api",
    "/app",
    "/coach",
    "/join",
    "/reset-password",
    "/verify-email",
)


class SeoSmokeError(RuntimeError):
    """The deployed public search surface does not match its indexation contract."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    content_type: str
    robots: str


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        del request, fp, code, msg, headers, newurl
        return None


def _read(url: str, *, timeout: float) -> HttpResponse:
    request = urllib.request.Request(url, headers={"User-Agent": "fitminiapp-seo-smoke/1"})
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            return HttpResponse(
                status=response.status,
                body=response.read(),
                content_type=response.headers.get("content-type", ""),
                robots=response.headers.get("x-robots-tag", ""),
            )
    except urllib.error.HTTPError as error:
        return HttpResponse(
            status=error.code,
            body=error.read(),
            content_type=error.headers.get("content-type", ""),
            robots=error.headers.get("x-robots-tag", ""),
        )


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical_url: str | None = None
        self.description: str | None = None
        self.title = ""
        self._inside_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonical_url = attributes.get("href")
        elif tag == "meta" and attributes.get("name") == "description":
            self.description = attributes.get("content")
        elif tag == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self.title += data


def _canonical_origin(value: str, *, allow_http: bool) -> str:
    parsed = urlparse(value)
    allowed_schemes = {"https", "http"} if allow_http else {"https"}
    if (
        parsed.scheme not in allowed_schemes
        or not parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SeoSmokeError("canonical_public_url must be an absolute origin without a path")
    return f"{parsed.scheme}://{parsed.netloc}"


def _expect_indexable_html(url: str, response: HttpResponse) -> None:
    if response.status != 200:
        raise SeoSmokeError(f"{url} returned HTTP {response.status}, expected 200")
    if "text/html" not in response.content_type.lower():
        raise SeoSmokeError(f"{url} returned unexpected content type {response.content_type!r}")
    if response.robots.strip().lower() != "index, follow":
        raise SeoSmokeError(f"{url} has X-Robots-Tag {response.robots!r}, expected 'index, follow'")

    parser = _MetadataParser()
    parser.feed(response.body.decode("utf-8", errors="replace"))
    if parser.canonical_url != url:
        raise SeoSmokeError(f"{url} has canonical {parser.canonical_url!r}, expected itself")
    if not parser.title.strip():
        raise SeoSmokeError(f"{url} has no title")
    if not parser.description or not parser.description.strip():
        raise SeoSmokeError(f"{url} has no meta description")


def _sitemap_locations(content: bytes) -> list[str]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise SeoSmokeError(f"sitemap.xml is invalid XML: {exc}") from exc

    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    if root.tag != f"{namespace}urlset":
        raise SeoSmokeError("sitemap.xml is not a sitemap urlset")
    locations = [
        location.text.strip()
        for entry in root.findall(f"{namespace}url")
        for location in entry.findall(f"{namespace}loc")
        if location.text and location.text.strip()
    ]
    if not locations:
        raise SeoSmokeError("sitemap.xml has no URLs")
    if len(locations) != len(set(locations)):
        raise SeoSmokeError("sitemap.xml contains duplicate URLs")
    return locations


def check_seo_surface(
    canonical_public_url: str,
    *,
    timeout: float,
    allow_http: bool = False,
    read: Callable[[str], HttpResponse] | None = None,
) -> list[str]:
    """Validate crawl/indexation signals without changing deployment or external accounts."""

    origin = _canonical_origin(canonical_public_url, allow_http=allow_http)
    fetch = read or (lambda url: _read(url, timeout=timeout))
    homepage_url = f"{origin}/"
    robots_url = f"{origin}/robots.txt"
    sitemap_url = f"{origin}/sitemap.xml"

    _expect_indexable_html(homepage_url, fetch(homepage_url))

    robots = fetch(robots_url)
    if robots.status != 200:
        raise SeoSmokeError(f"{robots_url} returned HTTP {robots.status}, expected 200")
    sitemap_declaration = f"Sitemap: {sitemap_url}"
    if sitemap_declaration not in robots.body.decode("utf-8", errors="replace"):
        raise SeoSmokeError(f"{robots_url} does not declare {sitemap_url}")

    sitemap = fetch(sitemap_url)
    if sitemap.status != 200:
        raise SeoSmokeError(f"{sitemap_url} returned HTTP {sitemap.status}, expected 200")
    if "xml" not in sitemap.content_type.lower():
        raise SeoSmokeError(
            f"{sitemap_url} returned unexpected content type {sitemap.content_type!r}"
        )
    locations = _sitemap_locations(sitemap.body)
    if homepage_url not in locations:
        raise SeoSmokeError(f"{sitemap_url} does not include the canonical homepage")

    for location in locations:
        parsed = urlparse(location)
        if f"{parsed.scheme}://{parsed.netloc}" != origin:
            raise SeoSmokeError(f"{sitemap_url} contains a non-canonical origin: {location}")
        if any(
            parsed.path == prefix or parsed.path.startswith(f"{prefix}/")
            for prefix in PRIVATE_PATH_PREFIXES
        ):
            raise SeoSmokeError(f"{sitemap_url} contains a private URL: {location}")
        _expect_indexable_html(location, fetch(location))
    return locations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "canonical_public_url",
        help="canonical public origin, for example https://your-fitness-coach.ru",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="allow plain HTTP for a local/private smoke test",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    try:
        locations = check_seo_surface(
            args.canonical_public_url,
            timeout=args.timeout,
            allow_http=args.allow_http,
        )
    except (OSError, SeoSmokeError, urllib.error.URLError) as exc:
        print(f"SEO smoke check failed: {exc}", file=sys.stderr)
        return 1

    print(f"SEO surface is healthy: {args.canonical_public_url.rstrip('/')}")
    print(f"Validated canonical sitemap URLs: {len(locations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
