# SEO regression and myths

Use when fixing confirmed SEO issues or protecting them with automated checks.

## Common SEO myths to reject

Do not recommend work solely because of myths such as:

- every page must have exactly one H1 or Google will penalize it;
- `meta keywords` are required;
- keyword density must hit a fixed percentage;
- longer content automatically ranks better;
- every page needs structured data;
- a perfect Lighthouse score guarantees rankings;
- submitting a sitemap guarantees indexing;
- canonical is a guaranteed directive;
- `robots.txt` removes a URL from the index;
- `noindex` protects private data;
- AI-generated text is automatically penalized;
- more indexed pages always means better SEO;
- hidden keyword text is acceptable;
- buying backlinks is a safe technical SEO fix.

If a recommendation cannot be tied to a real user/search-engine problem or reliable current guidance, do not present it as required SEO work.


## Regression tests

Prefer automated coverage for deterministic, important SEO rules.

Useful tests may include:

- canonical origin is production-safe;
- public pages do not emit accidental `noindex`;
- private/public route policy is enforced;
- sitemap excludes authenticated/admin routes;
- sitemap URLs are canonical;
- sitemap contains no duplicate URLs;
- important public routes return correct status;
- redirects do not loop;
- metadata exists for important templates;
- structured-data JSON is syntactically valid;
- environment config cannot publish localhost/staging canonicals;
- 404 routes return intended status where the framework/deployment allows it.

Do not create brittle tests that assert exact marketing copy unless exact wording is a real contract.
