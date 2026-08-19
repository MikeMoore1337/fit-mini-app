# International, lifecycle and deployment SEO

Focused reference for multilingual SEO, moved/deleted content, staging safety, analytics and social/search presentation.

### 16. Multilingual / multi-regional SEO

Only when applicable, check:

- stable locale-specific URLs;
- correct language content;
- canonical behavior per locale;
- reciprocal `hreflang` annotations when used;
- `x-default` only when appropriate;
- valid language/region codes;
- no search-engine-only location redirects;
- sitemap/HTML hreflang consistency;
- translations provide genuine value.

Do not add `hreflang` to a single-language site.

### 17. Deleted, moved, duplicate, and parameterized content

Check:

- permanent moves redirect coherently;
- deleted pages do not remain false `200`;
- replacement pages are genuinely relevant before redirecting;
- query parameters do not create uncontrolled duplicates;
- tracking parameters do not become canonical;
- filters/search-result pages have an explicit indexing strategy;
- pagination/infinite-scroll content remains discoverable where search visibility is intended.

Do not redirect every removed URL to the homepage.

### 18. Staging, preview, and deployment safety

Check:

- staging/preview domains are not accidentally canonicalized as production;
- production metadata does not point to localhost/preview hosts;
- staging URLs do not leak into production sitemap;
- environment-specific indexing controls are safe;
- preview deployments do not create large duplicate search surfaces.

Prefer authentication/network restrictions for non-public environments when stronger protection is required.

### 19. Analytics and webmaster tools

When in scope, verify code/configuration for:

- Google Search Console ownership path where applicable;
- Yandex Webmaster verification where applicable;
- sitemap submission readiness;
- analytics tags;
- conversion events;
- consent requirements;
- duplicate analytics loading.

Do not claim external dashboards were checked unless you actually had access.

Analytics installation is not itself a ranking factor.

If Search Console/Yandex Webmaster data is available, use it to prioritize real problems such as:

- indexed/excluded URL patterns;
- crawl/indexing errors;
- canonical disagreements;
- sitemap errors;
- search queries/pages;
- Core Web Vitals field groups.

Do not expose or commit verification secrets unnecessarily.

### 20. Search vs social presentation

Keep these distinct:

- crawling/indexing;
- ranking;
- rich-result eligibility;
- organic snippet appearance;
- social preview appearance.

Do not report social metadata as a core indexing requirement.
