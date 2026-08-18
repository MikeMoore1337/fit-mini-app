# Public content architecture

This document is the editorial and information-architecture contract for the indexable public
surface. It complements the technical crawl/indexation contract in
[`operations.md`](../operations.md) and the webmaster runbook in
[`search-console-yandex-webmaster.md`](search-console-yandex-webmaster.md). Organic acquisition,
distribution, editorial operations, and the public release gate are defined in the
[`organic-growth-playbook.md`](organic-growth-playbook.md).

## Current public information architecture

| Route                                                | Audience and intent                                                      | Why it is a separate page                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `/`                                                  | Both audiences: understand the product and choose a path                 | Product overview and primary entry point                                     |
| `/training`                                          | Independent users: understand programs and workout logging               | Covers the end-to-end training workflow, not nutrition or trainer operations |
| `/nutrition`                                         | Independent users: understand the current KБЖУ calculator and its limits | Answers calculation intent without claiming a meal diary or meal plans       |
| `/progress`                                          | Users and trainers: understand which factual results are stored          | Explains history, loads, records and measurements without an invented score  |
| `/for-trainers`                                      | Trainers: evaluate the current Coach workspace                           | Dedicated invitation, program and client-progress workflow                   |
| `/knowledge`                                         | Both audiences: find reviewed educational material                       | Editorial directory and publication policy                                   |
| `/knowledge/training/how-to-start-strength-training` | Beginners: start with a repeatable, recorded plan                        | Evergreen guide with source and safety context                               |
| `/knowledge/nutrition/kbju-as-a-reference`           | Calculator users: interpret an estimate responsibly                      | Evergreen guide separating estimates from diet quality and medical advice    |

There is deliberately no generic `/features` page: its intent would duplicate the landing and the
focused product pages. There is no public `/exercises` index yet. Public exercise pages must later
read factual names, muscles and technique metadata from the exercise domain rather than copy text
into an SEO-only content store.

Authenticated application, Coach, Admin, invitation and technical authentication routes remain
non-indexable and are not content sources for public pages.

## Maintained content source

[`publicContent.json`](../../frontend/src/content/publicContent.json) is the single repo-native
source for public page copy and the knowledge contract. It contains:

- canonical path, page kind, title, description and social description;
- H1, intro, semantic sections and factual CTA;
- breadcrumbs and contextual related links;
- knowledge category, author, optional reviewer, update date, disclaimer and sources;
- the category vocabulary `training`, `nutrition`, `cardio`, `recovery`, `exercises`.

The React public template imports the manifest directly. The backend reads the same source in local
development and the copy included in the frontend image for production. It uses the manifest to
render crawler-visible fallback HTML, route metadata, structured data and the sitemap. Task 38 can
reuse the typed frontend module for contextual App/TMA rendering without creating a second article
store.

Adding a page requires all of the following in one change:

1. a distinct people-first intent and complete manifest entry;
2. crawlable links from at least one relevant public page and contextual links back;
3. a self-canonical backend response with visible fallback content;
4. inclusion in the generated sitemap only after the route is ready for indexing;
5. targeted frontend and backend SEO-route tests.

Do not create category routes, query permutations or placeholders until they have standalone value.

## Editorial rules for fitness and nutrition

- Write for a concrete reader task, not a keyword or target word count.
- Describe only capabilities present in the current product. Do not present AI Coach, Demo Mode,
  meal logging, meal plans or future trainer/admin tools as available.
- Separate general education from individual medical, rehabilitation or dietetic advice.
- Do not promise treatment, guaranteed weight loss, a guaranteed performance result or a fixed
  result deadline.
- Cite primary or authoritative sources for material health, physiology and nutrition claims.
- Use a truthful organizational or personal byline. Never invent credentials, a medical reviewer,
  ratings, testimonials or review dates.
- Set `updated` only after a substantive review. Do not refresh dates to imply freshness.
- Leave `reviewer` empty when no qualified reviewer participated. If a topic requires specialist
  review, keep it unpublished until that review exists.
- Keep limitations and escalation guidance visible when a general guide may not fit a reader's
  health context.
- Do not copy third-party text or exercise technique descriptions. Exercise content must be owned
  or legally usable and backed by domain data.

The initial guides use current World Health Organization publications for the limited factual
claims they make. Source links remain visible on the guide pages.

## Structured data and linking contract

- The landing keeps truthful `Organization`, `WebSite` and `SoftwareApplication` data.
- Product pages use `WebPage`; the knowledge directory uses `CollectionPage`.
- A guide uses `Article` only when its visible page contains the matching headline, author, update
  date and body. No review/rating markup is generated.
- `BreadcrumbList` is emitted only for the visible hierarchy represented by breadcrumbs.
- All structured data URLs use the same canonical public origin as the page and sitemap.
- Landing, product pages, guides and CTA surfaces use normal `<a href>` links. A sitemap supplements
  this architecture; it does not replace internal linking.

## Future integration points

Later tasks may add a Demo CTA, an AI Coach page, stabilized product screenshots, richer trainer
positioning or public exercise pages only after those capabilities and factual assets exist. Until
then, do not publish indexable draft routes or synthetic screenshots as placeholders.
