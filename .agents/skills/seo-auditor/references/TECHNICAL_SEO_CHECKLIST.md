# Technical SEO checklist

Loaded on demand by `seo-auditor`. Preserve project-specific evidence and verify raw + rendered output.

## Audit areas

### 1. Public/private route inventory

Classify each relevant route family:

- public + should be indexable;
- public + should not be indexable;
- authenticated/private;
- admin/internal;
- preview/staging/test;
- API/static asset/technical route.

Verify implementation matches intent.

Private data must be protected by authentication/authorization, not by `robots.txt`, `noindex`, obscurity, or an unlinked URL.

For hybrid products, marketing/content pages and authenticated application pages may require intentionally different indexing behavior.

### 2. HTTP status and availability

Check representative pages for:

- `200` on valid canonical pages;
- `301`/`308` where a permanent move is intended;
- temporary redirects only when truly temporary;
- `404`/`410` for genuinely missing/removed content where appropriate;
- no redirect loops;
- no long unnecessary redirect chains;
- no blanket `200` for missing pages;
- no production 5xx on search-critical routes.

Check host/protocol normalization:

- HTTP -> HTTPS;
- preferred hostname;
- `www`/non-`www` consistency if applicable;
- trailing-slash convention if duplicates exist;
- case/path normalization where relevant.

Do not change redirect behavior without understanding deployment and application constraints.

### 3. robots.txt

Check:

- file is reachable on the intended host;
- syntax is valid enough for target crawlers;
- intended public pages are not accidentally blocked;
- technical crawl exclusions are intentional;
- sitemap location is declared when appropriate;
- preview/staging behavior is safe.

Important:

- `robots.txt` controls crawling, not access control;
- a disallowed URL may still be known through links or other signals;
- do not use `robots.txt` as the primary canonicalization mechanism;
- if a crawler cannot fetch a page, it may not see a page-level `noindex`.

Never rely on `robots.txt` to protect confidential information.

### 4. Indexing directives

Inspect:

- `<meta name="robots">`;
- `X-Robots-Tag`;
- route-level metadata generation;
- environment-specific `noindex`.

Verify:

- indexable pages are not unintentionally excluded;
- intentionally excluded public pages have coherent directives;
- staging/preview environments cannot accidentally become search competitors;
- private pages are not treated as secure merely because they use `noindex`.

### 5. Canonicalization

Verify:

- canonical pages normally have self-referential canonicals;
- duplicate variants consistently reference the intended canonical;
- canonical target is reachable and indexable;
- canonical target does not redirect unnecessarily;
- sitemap URLs agree with canonical strategy;
- redirects and canonicals do not contradict each other;
- query parameters, filters, sort states, tracking parameters, and duplicate aliases do not create uncontrolled URL families.

Do not force unrelated pages to one canonical URL.
Do not canonicalize every route to the homepage.
Treat canonical annotations as signals, not guaranteed commands.

### 6. Sitemap

Check:

- sitemap is reachable and valid;
- it contains only URLs intended for search;
- URLs use the canonical production origin;
- listed URLs are canonical and normally return `200`;
- private/auth/admin/test routes are excluded;
- redirects and errors are excluded;
- `lastmod` is truthful if used;
- large sites split/index sitemaps when necessary;
- generated sitemaps update when public routes/content change.

Do not add every reachable URL to the sitemap.
A sitemap is not a substitute for internal linking.

### 7. Crawlable internal linking and information architecture

Check:

- important pages are reachable through normal crawlable links;
- critical content is not discoverable only through JavaScript event handlers without meaningful link targets;
- key pages are not orphaned;
- hierarchy is understandable;
- excessive depth is avoided;
- breadcrumbs are useful where warranted;
- anchor text is descriptive without stuffing;
- faceted/filter/search-result pages do not create uncontrolled crawl spaces;
- generated paths cannot grow infinitely.

Prioritize user navigation first.

### 8. Titles, descriptions, headings, and metadata

For important public templates, check:

- unique and descriptive `<title>`;
- title matches actual page purpose;
- no systematic keyword stuffing;
- useful meta description where a curated snippet matters;
- heading hierarchy reflects content structure;
- visible content supports the intent implied by metadata;
- favicon/site identity configuration is correct where applicable.

Do not treat `meta keywords` as a modern Google SEO requirement.
Do not write descriptions as keyword lists.
Do not invent claims, ratings, prices, testimonials, user counts, awards, or expertise.

### 9. Search-rendered content and JavaScript

For JavaScript-heavy applications, verify what exists:

- in initial HTML;
- after hydration/render;
- when scripts fail/delay, where relevant.

Check:

- title;
- description;
- canonical;
- robots directives;
- headings;
- primary body content;
- internal links;
- structured data.

If target crawlers have limited JavaScript execution, prefer server-rendered/static HTML for public search-critical content.

Do not require a framework migration if the current stack can produce reliable indexable output.
