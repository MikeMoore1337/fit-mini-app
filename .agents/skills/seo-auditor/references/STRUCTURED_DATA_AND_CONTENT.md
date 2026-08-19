# Structured data and content quality

Focused reference for structured data, content quality, YMYL-like surfaces, images and page experience.

### 10. Structured data

Inventory structured data only where it matches actual page content.

Possible types include, depending on the product:

- `Organization`;
- `WebSite`;
- `WebPage`;
- `BreadcrumbList`;
- `Article`;
- `Person` / profile-related markup where supported;
- `SoftwareApplication`;
- `Product`;
- `LocalBusiness`;
- other types explicitly supported by the target engine.

Verify:

- syntax is valid;
- required properties for the intended search feature are present;
- values match visible content;
- markup is attached to the correct page type;
- URLs use the canonical origin;
- reviews/ratings are not fabricated;
- schema is not added merely because it exists in Schema.org;
- implementation follows current target-engine eligibility rules.

Validate with official structured-data/rich-results tooling when available.

Passing validation does not guarantee a rich result.

### 11. Content quality and search intent

Audit usefulness, not keyword density.

Check:

- page has a clear user purpose;
- content answers the intent suggested by title and heading;
- pages are not thin variants created mainly for query permutations;
- repeated pages provide meaningfully distinct value;
- content is not mechanically stitched, paraphrased, or generated at scale without added value;
- important factual claims are supportable;
- pages are maintained when freshness matters;
- author/reviewer information is truthful when expertise matters.

Do not recommend hundreds or thousands of near-duplicate pages just to capture long-tail queries.

AI-assisted content is not automatically a problem. Low-value scaled content created mainly to manipulate search visibility is.

### 12. High-stakes / YMYL-like content

For content that can materially affect health, safety, finances, or legal decisions, apply stricter trust standards.

Check where relevant:

- truthful authorship;
- accurate professional qualifications;
- appropriate sources for medical/scientific claims;
- honest publication/update dates;
- relevant commercial disclosures;
- clear distinction between education and individualized professional advice where appropriate;
- no unsupported certainty.

Do not invent credentials or "medical review" labels.
Do not describe E-E-A-T as a single measurable ranking score.

### 13. Images and media

Check when relevant:

- meaningful images have useful alt text;
- decorative images do not get spammy alt text;
- important media is crawlable;
- dimensions/aspect-ratio space reduce layout shift;
- lazy loading does not delay critical above-the-fold media unnecessarily;
- filenames/URLs are sensible when practical;
- image sitemaps are added only when useful;
- Open Graph/social images are correct where sharing matters.

Open Graph may improve social previews, but do not present it as a direct Google ranking factor.

### 14. Mobile and page experience

Check important public pages on mobile and desktop.

Verify:

- mobile content parity for search-critical information;
- responsive usability;
- no intrusive overlays blocking main content;
- no mobile-only accidental `noindex` or redirects;
- layout stability;
- loading behavior.

### 15. Core Web Vitals and performance

Use real field data when available.

Current thresholds must be re-checked against official sources when freshness matters.

At the time this skill was written, Google's "good" targets are:

- LCP <= 2.5 s;
- INP <= 200 ms;
- CLS <= 0.1;

evaluated at the 75th percentile for mobile and desktop separately.

Distinguish:

- field data;
- lab data;
- synthetic local runs.

Do not claim a field Core Web Vitals failure from one local Lighthouse run.

Investigate root causes such as:

- render-blocking resources;
- oversized hero/media assets;
- slow server response;
- unnecessary client JavaScript;
- hydration cost;
- third-party scripts;
- layout shifts;
- font loading;
- interaction latency.

Performance matters for users and search experience, but do not promise ranking gains from reaching a particular score.

Use `$performance-engineer` for deep runtime/performance work.
