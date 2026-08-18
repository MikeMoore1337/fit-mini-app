from __future__ import annotations

from scripts.check_seo_surface import HttpResponse, SeoSmokeError, check_seo_surface


def _html(url: str) -> bytes:
    return (
        "<!doctype html><html><head>"
        "<title>Your Fitness Coach</title>"
        '<meta name="description" content="Training planning and progress." />'
        f'<link rel="canonical" href="{url}" />'
        "</head><body></body></html>"
    ).encode()


def test_seo_smoke_accepts_canonical_public_surface() -> None:
    origin = "https://your-fitness-coach.ru"
    homepage = f"{origin}/"
    training = f"{origin}/training"
    robots = f"{origin}/robots.txt"
    sitemap = f"{origin}/sitemap.xml"
    responses = {
        homepage: HttpResponse(200, _html(homepage), "text/html; charset=utf-8", "index, follow"),
        training: HttpResponse(200, _html(training), "text/html; charset=utf-8", "index, follow"),
        robots: HttpResponse(
            200, f"User-agent: *\nSitemap: {sitemap}\n".encode(), "text/plain", ""
        ),
        sitemap: HttpResponse(
            200,
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{homepage}</loc></url><url><loc>{training}</loc></url></urlset>"
            ).encode(),
            "application/xml",
            "",
        ),
    }

    assert check_seo_surface(origin, timeout=1, read=responses.__getitem__) == [homepage, training]


def test_seo_smoke_rejects_private_sitemap_url() -> None:
    origin = "https://your-fitness-coach.ru"
    homepage = f"{origin}/"
    robots = f"{origin}/robots.txt"
    sitemap = f"{origin}/sitemap.xml"
    private = f"{origin}/app"
    responses = {
        homepage: HttpResponse(200, _html(homepage), "text/html", "index, follow"),
        robots: HttpResponse(200, f"Sitemap: {sitemap}\n".encode(), "text/plain", ""),
        sitemap: HttpResponse(
            200,
            (
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{homepage}</loc></url><url><loc>{private}</loc></url></urlset>"
            ).encode(),
            "application/xml",
            "",
        ),
    }

    try:
        check_seo_surface(origin, timeout=1, read=responses.__getitem__)
    except SeoSmokeError as exc:
        assert "private URL" in str(exc)
    else:
        raise AssertionError("private sitemap URLs must fail the SEO smoke check")
