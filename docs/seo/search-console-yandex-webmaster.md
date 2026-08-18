# Search Console and Yandex Webmaster

This runbook covers the manual, account-level work required to monitor the canonical
public SEO surface. It does not grant Codex access to Google Search Console, Yandex
Webmaster, DNS, or production deployments.

The current production indexation contract is intentionally limited to the canonical landing,
product pages, knowledge directory, and reviewed guides declared in
[`publicContent.json`](../../frontend/src/content/publicContent.json). The authenticated
application, invitations, and technical routes stay out of the sitemap and return `noindex`. The
canonical origin and its sitemap are defined in [operations.md](../operations.md).

## Ownership verification

Use the domain owner account and retain at least two trusted owners in each webmaster
tool. Verification enables access to search and indexation data, so treat its ownership
and access review as operational security work.

1. Prefer DNS TXT verification when the domain DNS is controlled by the owner. In Google
   Search Console, create a Domain property for `your-fitness-coach.ru`; Domain properties
   require DNS verification and cover protocol/subdomain variants.
2. If DNS verification cannot be used, create a URL-prefix property for the exact canonical
   URL `https://your-fitness-coach.ru/`, then use the repository-supported meta-tag fallback.
   Put only the token value, not a complete HTML tag, in the production secret store or
   deployment `.env`:

   ```dotenv
   GOOGLE_SITE_VERIFICATION=token-issued-by-google
   YANDEX_VERIFICATION=token-issued-by-yandex
   ```

   The backend renders these tags only on an indexable canonical page. Do not commit real
   tokens, add them to frontend build variables, or use them on app/private routes.

3. For Yandex Webmaster, add the exact canonical HTTPS site and verify management rights
   with DNS TXT where practical. Its meta-tag or root HTML-file methods are alternatives
   when DNS is unavailable. Keep the selected proof available: Yandex periodically checks it.
4. After deployment, run the repository smoke check before clicking **Verify**:

   ```console
   py scripts/check_seo_surface.py https://your-fitness-coach.ru
   ```

Google's property/verification model is documented in [Search Console Help](https://support.google.com/webmasters/answer/34592);
Yandex's supported verification methods and ongoing verification behavior are in
[Yandex Webmaster](https://yandex.com/support/webmaster/en/service/rights).

## Google Search Console setup

1. Add the canonical property (Domain property when DNS verification is available; otherwise
   exact canonical URL-prefix property) and verify ownership.
2. Inspect the homepage and representative future public URLs with URL Inspection. Confirm
   Google receives the canonical URL, `index, follow`, and crawler-visible content.
3. Submit `https://your-fitness-coach.ru/sitemap.xml` in the Sitemaps report. It is already
   declared in `robots.txt`; submission provides processing feedback but does not guarantee
   crawling or indexation.
4. Review Page Indexing for errors, exclusions, and canonical/duplicate disagreements. Do
   not treat every exclusion as a defect: private routes are intentionally excluded.
5. Review Core Web Vitals as field data, not as a ranking guarantee or a one-off local score.
6. Review Search performance: impressions, clicks, CTR, queries, and pages. Split branded
   and non-branded queries where the report's filters make that practical; record any manual
   grouping criteria used.
7. Configure owner notification emails and periodically review property owners/users.

For the report meanings and URL Inspection flow, use Google's [Search Console
getting-started guide](https://developers.google.com/search/docs/monitor-debug/search-console-start).

## Yandex Webmaster setup

1. Add `https://your-fitness-coach.ru` exactly; preserve HTTPS and primary-host consistency
   (`www` redirects to the apex canonical host).
2. Verify rights, then add `https://your-fitness-coach.ru/sitemap.xml` in **Indexing → Sitemap
   files** and validate it there.
3. Check indexing/searchable pages, server response, robots.txt analysis, crawl statistics,
   and URL status. Investigate only unexpected exclusions; app/private routes remain excluded
   by design.
4. Review **Website optimization → Site diagnostics**, security/violations, and notifications.
5. Validate the visible landing structured data with Yandex's Structured data validator after
   structured-data changes.
6. Review query statistics, impressions, clicks, CTR, and relevant pages; distinguish branded
   and non-branded groups where the available filters allow it.
7. Configure owner notifications and review access rights regularly.

Yandex documents sitemap processing and validation in its [Sitemap guide](https://yandex.com/support/webmaster/en/indexing-options/sitemap),
site errors in [Site diagnostics](https://yandex.com/support/webmaster/en/service/site-diagnostics),
and its available validation tools in the [tools overview](https://yandex.com/support/webmaster/en/indexing-options/tools).

## Repeating monitoring runbook

Run the read-only smoke command after every major release, public URL change, migration that
can affect rendering/routing, landing redesign, metadata change, or sitemap change. It checks
the live canonical homepage, robots.txt, sitemap, self-canonicals, statuses, indexability
headers, title/description, and that sitemap URLs do not contain known private route families.

Then review both webmaster tools after their normal data-refresh window:

- indexed and excluded pages, crawl/index errors, and duplicate/canonical conflicts;
- sitemap processing/errors and the status of newly changed public URLs;
- impressions, clicks, CTR, top queries, and top pages, with a practical brand/non-brand split;
- Search Console Core Web Vitals and Yandex diagnostics, security, and violations.

For one or a few important changed URLs, use URL Inspection / Yandex URL status and request a
re-crawl only after the canonical page is live and healthy. For a larger set of canonical URLs,
update and re-submit the sitemap in each tool. Do not automate blanket URL submission and do
not use the Google Indexing API for ordinary product pages: sitemap submission and recrawl
requests are discovery signals, not an indexation guarantee. Google's [sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
and [recrawl guidance](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
describe these limits.

## Analytics boundary

No Google Analytics, Yandex Metrica, or other client-side behavioral analytics is installed by
this repository task. Search Console and Yandex Webmaster provide the base search monitoring
without a browser tracking tag. Connecting organic acquisition to product conversions requires
a separate privacy, legal-consent, retention, and data-flow decision; do not add a tracking tag
as an SEO side effect.
