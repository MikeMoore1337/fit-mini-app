# Organic growth and distribution playbook

This playbook is the operating contract for zero/low-cost organic acquisition. It builds on the
[public content architecture](public-content.md) and the
[Search Console/Yandex Webmaster runbook](search-console-yandex-webmaster.md). It does not include
paid media, cold outreach, hidden tracking, or ranking promises.

The external guidance below was reviewed on **2026-08-18**. The durable rule is to re-check the
linked official documentation before changing search-facing behavior rather than relying on this
date indefinitely.

## Principles and boundaries

- Help a specific reader complete a real task. Search visibility is distribution of useful work,
  not the reason to manufacture a page.
- Treat independent users and personal trainers as different audiences with different activation
  paths. Do not hide trainer intent inside generic consumer copy.
- Publish cornerstone pages and first-hand product knowledge before expanding topic count. There
  is no publishing quota or target word count.
- Keep one stable, canonical URL per resource. UTM parameters may be attached to outbound campaign
  links, but never create a second social, campaign, or search page.
- Keep public material factual and separate from private workouts, profiles, client records,
  trainer notes, Coach/Admin data, and authenticated application state.
- AI may assist research organization, outlining, drafting, translation, or copy-editing. A human
  remains accountable for usefulness, claims, sources, product truth, and publication. Scaled
  low-value generation and query-fanout pages are prohibited.
- Never buy links, use a PBN or link farm, conceal links, create fake accounts/reviews, spam
  communities, or automate mass outreach.
- Organic work does not install analytics. Measurement expands only through an explicitly approved
  privacy-safe telemetry decision.

## Audiences and desired outcomes

| Audience                 | Situation and need                                                                                                     | Useful public promise                                                       | Product CTA                                                            | Candidate meaningful activation                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Independent fitness user | Wants a repeatable plan, a simple workout record, understandable nutrition estimates, or evidence of personal progress | Explain the next step and the product's limits in beginner-friendly Russian | Open the app; later, start a truthful Demo flow when it exists         | First completed workout or another separately approved core action; not currently attributed |
| Personal trainer         | Wants a practical way to assign programs and review client progress without a generic messenger or marketplace         | Show the real trainer workflow, decision support, and boundaries            | Open the trainer product path and follow the existing application flow | First real program assignment to an accepted client; not currently attributed                |

Candidate activations are measurement definitions, not events implemented by this task. They must
be revalidated against the product state before telemetry is approved.

## Channel strategy

| Channel                          | Independent users                                                                      | Personal trainers                                                                           | Operating approach                                                                                             | Available evidence                                                              |
| -------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Google organic                   | Product explainers, beginner guides, progress and nutrition interpretation             | Trainer workflow and methodology pages                                                      | Maintain crawlable, canonical, internally linked, people-first pages; inspect real queries before expanding    | Search Console impressions, clicks, CTR, pages, queries                         |
| Yandex organic                   | Same needs in clear Russian with no keyword variants                                   | Same trainer intent, with a distinct `/for-trainers` path                                   | Use the same canonical corpus; monitor indexation, diagnostics, and query statistics                           | Yandex Webmaster impressions, clicks, CTR, searchable pages                     |
| Telegram organic                 | Share concise answers and useful guide links in owned channels or relevant discussions | Share trainer methods in professional groups only where participation and links are welcome | Native post with a useful summary; one contextual link; answer follow-up questions; no bulk DMs                | Platform-visible post/reaction data; UTM only after approved attribution exists |
| VK and communities               | Educational excerpts, release explanations, useful checklists                          | Practitioner discussion and workflow examples                                               | Adapt the framing to the community instead of cross-posting an ad; respect rules and disclose affiliation      | Platform-visible engagement; UTM only after approved attribution exists         |
| Expert publications and mentions | Evidence-based explainers or commentary where YFC adds first-hand product experience   | Method articles, interviews, and practical trainer workflow examples                        | Pitch an editorial contribution because it helps that publication's readers; editor retains control            | Published mentions/referrals visible to the owner or webmaster tools            |
| Earned backlinks                 | Original guides and genuinely public tools                                             | Trainer methods and safe aggregate insights                                                 | Make the resource worth citing, then inform a small relevant set of people; never request ranking manipulation | Referring pages/links in webmaster tools                                        |
| Direct/referral                  | Bookmarks, personal recommendations, untagged shares                                   | Peer recommendations and client/trainer referrals                                           | Preserve stable human-readable URLs and useful previews                                                        | Not reliably separable without approved telemetry; report as unknown            |

Channel fit is more important than simultaneous distribution. A trainer-method article can go to a
trainer community; a beginner KБЖУ explainer should not be pushed there merely to complete a list.

## Prioritized content roadmap

Statuses are `published`, `improve`, `ready for brief`, or `blocked`. `Blocked` means the page must
not be published until the named product/data/editorial prerequisite exists. Priorities express
sequence, not expected search volume; no keyword-volume data was used.

### Independent-user and shared cornerstone work

| Priority | Audience                       | Intent                | User problem                                                                         | Unique angle / useful addition                                                                                        | Target public page or guide                                     | Internal-link destination                                         | Product CTA                                          | Evidence/review requirement                                                                                              | Status                                          |
| -------- | ------------------------------ | --------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------- |
| P0       | Independent users              | Commercial/product    | Understand whether the service supports a repeatable training workflow               | A truthful path from program to today's workout and recorded sets across Web and Telegram                             | `/training`                                                     | `/knowledge/training/how-to-start-strength-training`, `/progress` | Open the app                                         | Product-owner verification after workflow changes; real screenshots only when stable                                     | published; improve from real questions          |
| P0       | Independent users              | Informational         | Start strength training without losing the plan after the first session              | Connect a conservative beginner process to an actual repeatable log, with explicit safety limits                      | `/knowledge/training/how-to-start-strength-training`            | `/training`, `/progress`                                          | Open the app                                         | Current authoritative training/safety sources; substantive fact check; specialist review if claims expand                | published                                       |
| P0       | Independent users              | Informational/product | Understand what a KБЖУ estimate can and cannot tell them                             | Explain the estimate as a starting reference and connect it to the current calculator without a diet-quality promise  | `/knowledge/nutrition/kbju-as-a-reference`                      | `/nutrition`                                                      | Open the app                                         | Current authoritative nutrition sources; nutrition-qualified review before individualized or clinical claims             | published                                       |
| P1       | Independent users              | Informational         | Know what to write down during a workout and why                                     | Beginner-first checklist using the product's actual weight, repetitions, set completion, and optional advanced fields | `/knowledge/training/what-to-record-in-a-workout`               | `/training`, `/progress`                                          | Record the next workout                              | Verify every field against the current product; cite claims about monitoring/progression                                 | ready for brief                                 |
| P1       | Independent users              | Informational         | Increase training load without treating every session as a test                      | Explain small, observable progression choices using logged history and no invented readiness score                    | `/knowledge/training/how-to-progress-training-load`             | `/training`, `/progress`                                          | Review the program and log a workout                 | Training-source review; qualified review for safety/loading claims; no deterministic prescription presented as universal | ready for brief                                 |
| P1       | Independent users              | Informational         | Interpret workout history, records, weight, and measurements without false certainty | Separate observed change from possible explanations and compare the user mainly with their own history                | `/knowledge/progress/how-to-read-training-progress`             | `/progress`, `/training`                                          | Open progress after recording workouts               | Product analytics/formula review plus factual fitness review; document sparse-data limits                                | ready for brief                                 |
| P2       | Independent users              | Informational         | Resume a routine after an ordinary break without an all-or-nothing plan              | A conservative return checklist tied to planning and logging, with clear medical escalation boundaries                | `/knowledge/recovery/how-to-return-after-a-break`               | `/training`, `/knowledge`                                         | Choose or adjust a plan                              | Qualified safety review; no injury rehabilitation or medical advice                                                      | ready for brief                                 |
| P2       | Independent users and trainers | Informational         | Find accurate technique information connected to the exercise catalog                | Public pages generated from reviewed domain facts and owned/legal media, not copied SEO text                          | Future `/exercises/` hub and selected `/exercises/{slug}` pages | `/training`, relevant guides                                      | Open the app at the exercise workflow when supported | Exercise-domain source of truth, legal media provenance, technique reviewer, duplicate/thin-page gate                    | blocked until public exercise foundation exists |

### Trainer cornerstone work

| Priority | Audience          | Intent                     | User problem                                                                        | Unique angle / useful addition                                                                                                             | Target public page or guide                             | Internal-link destination                  | Product CTA                                  | Evidence/review requirement                                                                          | Status                                                 |
| -------- | ----------------- | -------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------ | -------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| P0       | Personal trainers | Commercial/professional    | Decide whether the current workspace fits program and client-progress work          | Show the real invitation, assignment, correction, and progress-review workflow without marketplace or messenger claims                     | `/for-trainers`                                         | `/training`, `/progress`                   | Follow the existing trainer application path | Product-owner verification; real workflow screenshots only after stabilization; no invented outcomes | published; improve from trainer interviews             |
| P1       | Personal trainers | Professional/informational | Turn an intake conversation into a clear program brief                              | A reusable briefing checklist aligned with fields and constraints the product actually supports                                            | `/knowledge/trainers/program-brief-checklist`           | `/for-trainers`, `/training`               | Open the trainer workspace                   | Trainer practitioner byline or review; product-field verification; no medical screening claims       | ready for brief                                        |
| P1       | Personal trainers | Professional/informational | Review a client's logged session and give specific feedback                         | A contextual review method based on plan versus completed work, not a generic chat or invented adherence score                             | `/knowledge/trainers/review-a-client-workout`           | `/for-trainers`, `/progress`               | Review a client in the trainer workspace     | Trainer review; privacy examples must be synthetic; align terminology with actual analytics          | ready for brief                                        |
| P1       | Personal trainers | Professional/informational | Discuss progress when records are incomplete or mixed                               | A factual conversation guide that states coverage and limitations instead of producing a magic confidence score                            | `/knowledge/trainers/progress-review-with-limited-data` | `/for-trainers`, `/progress`               | Open client progress                         | Trainer and analytics-domain review; synthetic examples only; no client data or health diagnosis     | ready for brief                                        |
| P2       | Personal trainers | Research summary           | Understand a relevant training recommendation without reading commodity paraphrases | Narrow synthesis that compares authoritative sources, explains uncertainty, and shows where the product does or does not operationalize it | A specific future guide under `/knowledge/training/`    | Relevant trainer guide and `/for-trainers` | Use the applicable product workflow          | Primary/authoritative sources, named accountable author, qualified reviewer, material update trigger | blocked until a concrete trainer question justifies it |

Before promoting a new idea from `ready for brief`, use real Search Console/Yandex query evidence,
support questions, trainer interviews, or observed product confusion. Merge overlapping ideas. Do
not split a guide by synonyms, city, audience adjective, or question wording.

## Expert-led editorial model

### Roles and visible fields

- **Author/byline:** required for a guide when accountability adds context. Use a real person or the
  truthful `Редакция Your Fitness Coach` organization byline; never invent a person or credential.
- **Reviewer:** required when claims depend on specialist fitness, nutrition, medical, or other
  professional judgment. The reviewer checks only within their competence. If no qualified review
  happened, leave the field empty rather than implying it.
- **Product verifier:** confirms screenshots, UI labels, CTA, and capability claims against the
  released product.
- **Editor/fact checker:** checks that every material factual claim is supported, accurately
  paraphrased, scoped, and linked to the strongest practical source.
- **Last updated:** changes only after a substantive review or factual update, not to simulate
  freshness.

### Evidence hierarchy

Prefer primary research, consensus guidelines, government/intergovernmental health sources, and
official product documentation. Secondary sources may help explain context but must not replace a
primary or authoritative source for a consequential claim. Link to the source a reader can inspect;
record access/update dates in the editorial brief when freshness matters.

Do not infer a universal prescription from one study, imply causation from product logs, or turn a
measurement into a single-muscle/ideal-body score. General education must state where individual
medical, rehabilitation, or dietetic advice begins.

### Publication workflow

1. **Brief:** name one audience, intent, user task, distinct value, target URL, internal links, CTA,
   and evidence/reviewer needs. Reject the brief if an existing page can answer it well.
2. **Evidence pack:** list the claims that need support, original sources, product screenshots/data
   provenance, and any conflicts or uncertainty.
3. **Draft:** answer the task before the CTA; use plain Russian and disclose limitations. AI-assisted
   text is treated as unverified draft material.
4. **Fact check:** trace material claims to sources, verify quotations and numbers, check product
   truth, plagiarism/copyright, medical boundaries, and visible/source consistency.
5. **Review:** obtain the required specialist review and record who approved which scope. A missing
   required reviewer blocks publication.
6. **Release check:** run the lightweight public-page checklist below, including raw HTML/rendered
   metadata and social preview checks.
7. **Maintain:** review after a material source/guideline or product change, or when user feedback
   identifies ambiguity. Do not touch the date for cosmetic edits alone.

### Corrections and updates

Corrections should be accepted through the existing public support contact. Triage safety- or
health-relevant errors first. Confirm the issue against sources, correct the page and metadata,
update `updated` only for a substantive change, re-run the targeted page checks, and redistribute a
correction when the original claim was materially misleading. Keep the Git history as the audit
trail; do not silently rewrite evidence in an external campaign copy while leaving the page stale.

## Ethical distribution workflow

Run this checklist for every meaningful guide or public product update. Skip channels that do not
fit the audience.

### Before sharing

- The canonical page is live, indexable by policy, linked internally, useful without signing in,
  and has passed editorial/product verification.
- Title, description, Open Graph image and image alt describe the page truthfully. Preview bots can
  fetch the image without authentication.
- The owner selects one primary audience and one useful takeaway. The post is not just a link or a
  generic feature announcement.
- The destination is the clean stable URL. Add one conforming UTM query only to the distributed
  link when that campaign has an approved measurement use; never publish a UTM URL as canonical.
- The community permits relevant links and the poster can disclose their YFC affiliation.

### Channel execution

- **Telegram owned channel/profile:** write a concise answer or actionable excerpt, then link to the
  complete resource. Reuse the same canonical page rather than making a Telegram-specific clone.
- **Telegram community:** participate only where the question and rules make the resource useful.
  Do not bulk-post, bulk-DM, or drop links without context.
- **VK owned profile/community:** adapt the post to the local discussion and keep the factual scope
  consistent with the page. Avoid repetitive posts across unrelated groups.
- **Trainer communities:** share practitioner methods and invite critique. Do not scrape member
  lists, automate messages, or present promotion as an independent recommendation.
- **Expert publication or direct sharing:** send a small, personalized note explaining why the
  resource helps that audience. A link or mention is optional and controlled by the recipient.

Never use fake accounts, fabricated testimonials/reviews, comment/forum spam, engagement pods, or
automated mass messaging. One useful conversation is preferable to nominal reach in an irrelevant
community.

### After sharing

- Record the publication date, canonical destination, channel, campaign labels, and post URL in the
  owner's campaign ledger. Do not put access tokens, private community data, or personal data in Git.
- Answer genuine questions and feed repeated confusion back into the existing page or roadmap.
- Capture only platform-visible aggregate results and currently approved webmaster data. Do not
  infer product conversion where no telemetry joins the stages.
- Check the social preview after first publication and after changing its image or metadata; social
  platforms may cache old cards and may require a manual refresh.

## Earned-link strategy

Create assets people would cite even if search engines did not count links:

- original, reviewed cornerstone guides that resolve a practical question;
- public calculators or tools only after they genuinely work without exposing private state;
- trainer briefing/review templates grounded in the real workflow;
- careful research summaries that add comparison, limitations, or applied interpretation;
- product insights only after a separate privacy review defines safe aggregation, minimum cohort
  handling, suppression, retention, and wording that cannot identify users or trainers.

For each candidate, ask: who would cite it, for which reader problem, and what value exists beyond a
summary of other pages? Share it with a small relevant list of editors, practitioners, or resource
maintainers. Accept editorial `nofollow`/`sponsored` decisions and disclosure requirements.

Forbidden tactics include buying links or posts for ranking credit, PBNs, link farms, automated
link creation, hidden links, low-quality directories, mass reciprocal exchanges, required links in
unrelated partnerships, and keyword-stuffed forum signatures. Sponsorship, if ever approved outside
this organic scope, must be disclosed and appropriately qualified; it is not an earned-link tactic.

## Shareability contract

Every canonical public page uses its human-readable title and social description from
`frontend/src/content/publicContent.json`, an absolute self-canonical URL, and the shared
`/assets/brand/yfc-social-preview.png` card. The card incorporates the canonical task 07 mark; do not
redraw or fork the logo for a channel. Metadata includes Open Graph image type/dimensions/alt and a
large-image Twitter-compatible fallback. Per-page images may replace the shared card only when they
are truthful, legally usable, accessible, stable, and reviewed with the page.

The shared image is presentation metadata, not structured-data evidence and not a ranking claim.
Do not add fake screenshots, people, results, ratings, or endorsements. Built-in copy/share controls
are deferred: standard browser/Telegram sharing already preserves the stable URL, and another
control is justified only by observed user need. If added later, it must copy the clean canonical URL
by default and expose any campaign tagging explicitly.

## UTM convention

UTM fields are optional labels for owned organic distribution, not user-profile data:

```text
utm_source
utm_medium
utm_campaign
utm_content
```

Use lowercase ASCII `snake_case`; keep values stable, human-readable, and free of names, usernames,
chat IDs, account IDs, emails, invitation tokens, health/fitness data, or other personal/sensitive
content.

| Field          | Meaning                                                            | Examples                                                             |
| -------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `utm_source`   | Platform or referring publication family                           | `telegram`, `vk`, `trainer_media`                                    |
| `utm_medium`   | Distribution relationship                                          | `organic_social`, `community`, `earned_media`, `referral`            |
| `utm_campaign` | Stable initiative or content launch                                | `strength_start_guide`, `trainer_workflow_release`                   |
| `utm_content`  | Placement or creative variant, only when comparison is intentional | `channel_post`, `profile_post`, `community_answer`, `editorial_link` |

Example:

```text
https://your-fitness-coach.ru/knowledge/training/how-to-start-strength-training?utm_source=telegram&utm_medium=organic_social&utm_campaign=strength_start_guide&utm_content=channel_post
```

Rules:

- Internal links, navigation, sitemap entries, canonical tags, `og:url`, structured data, and default
  copy/share URLs always use the clean URL without UTM parameters.
- A UTM variant is never a new page, redirect target, sitemap entry, or content variant. Current
  route metadata remains self-canonical to the clean path when query parameters are present.
- Use the same `utm_campaign` for the same initiative across channels; distinguish platform with
  `utm_source` and placement with `utm_content`.
- Do not invent a unique parameter value per recipient. Do not persist UTM values into a profile or
  durable fitness record.
- There is currently no approved client-side analytics/telemetry that consumes these fields. Until
  a privacy decision exists, UTM links are a naming-ready convention and campaign-ledger aid, not a
  claimed source of product conversion data.

## Measurement and funnel

The target funnel is:

```text
search/referral impression
-> canonical public page
-> product/demo CTA
-> demo/auth
-> meaningful product activation
```

Measure only the stages available from an approved source:

| Stage                                    | Current source                                               | Current status                                           | Reporting rule                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Google search impression/click           | Google Search Console                                        | Available after owner verification and normal data delay | Report impressions, clicks, CTR, page/query; separate branded/non-branded only with recorded grouping rules |
| Yandex search impression/click           | Yandex Webmaster                                             | Available after owner verification and normal data delay | Report impressions, clicks, CTR, page/query and unexpected index exclusions                                 |
| Referral/social impression or engagement | Platform/publication native aggregate data                   | Sometimes manually available                             | Keep channel definitions separate; do not equate reactions with site visits                                 |
| Canonical public-page visit/session      | No approved site analytics                                   | Not available                                            | Mark unknown; do not estimate from impressions or server noise                                              |
| Product/demo CTA click                   | No approved telemetry; Demo is not yet an attribution source | Not available                                            | Mark unknown                                                                                                |
| Demo/auth completion                     | No approved acquisition attribution                          | Not available                                            | Mark unknown                                                                                                |
| Meaningful activation                    | No approved acquisition attribution                          | Not available                                            | Mark unknown                                                                                                |

Search Console and Yandex Webmaster remain the source of truth for search impressions/clicks. They
do not prove downstream activation. Direct/referral cannot currently be separated reliably. Do not
join webmaster totals, social metrics, authentication records, or server logs into person-level
profiles.

If privacy-safe product telemetry is separately approved, its design must specify consent/legal
basis, exact event definitions, minimization, retention, access, deletion, bot/internal-traffic
handling, UTM capture lifetime, cross-domain behavior, and aggregate reporting. Only then calculate
stage-to-stage rates from compatible populations and time windows. Product analytics must never
contain food contents, exact measurements/macros, trainer comments, AI conversation text, tokens,
secrets, or unnecessary raw IDs.

### Operating cadence

- After each meaningful public release, run the release checklist and record its distribution plan.
- Weekly during an active launch, inspect page/query direction and indexation errors without reacting
  to normal day-to-day noise.
- Monthly, review which audience questions, pages, and channels produced useful engagement; update
  existing cornerstone content before increasing volume.
- Quarterly, prune or merge roadmap ideas that no longer have a distinct problem or product truth.
  Never delete/move a published URL without redirect/canonical migration review.

## AEO/GEO boundary

There is no separate generative-search optimization system. The same foundation applies: crawlable
content, clear headings, unique useful information, visible sources, truthful authorship/metadata,
current facts, and stable internal links. Do not mass-produce fan-out/query-variant pages, special
AI-crawler copy, hidden summaries, prompt-shaped keyword lists, or unsupported `speakable`/other
schema. AI-assisted drafting does not bypass the editorial workflow.

## Lightweight public release checklist

This gate applies to a new or materially changed **public feature/content page**, not routine private
application code.

- [ ] One audience, intent, and useful outcome are explicit; no existing page already serves them.
- [ ] Visible product claims match the released product and disclose important limits.
- [ ] Title, description, H1, social description, and CTA are human-readable and distinct.
- [ ] The route has one stable self-canonical URL; query/UTM variants do not enter sitemap or internal
      navigation.
- [ ] Index policy is intentional; only a complete canonical public page enters the sitemap.
- [ ] At least one crawlable contextual link points in and the page links to a relevant guide/product
      destination.
- [ ] Author, reviewer, sources, fact check, update date, disclaimer, and correction path are handled
      according to the editorial model.
- [ ] Structured data, when used, matches visible content and does not invent reviews, ratings,
      offers, people, or credentials.
- [ ] Open Graph/Twitter metadata resolves to the canonical page and a fetchable reviewed preview;
      preview was checked on the relevant distribution channel after deployment.
- [ ] Mobile and desktop rendered content, keyboard access, raw HTML fallback, status, canonical,
      robots directive, sitemap, and relevant tests pass.
- [ ] The measurement plan names only currently available sources; distribution uses the UTM
      convention only when there is an approved use.
- [ ] The distribution checklist names audience-appropriate channels and excludes bulk outreach,
      link schemes, fake engagement, and spam.

## Official source baseline

- Google: [people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content),
  [spam policies](https://developers.google.com/search/docs/essentials/spam-policies),
  [AI features guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide),
  [canonical URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls),
  and [Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article).
- Yandex Webmaster: [how search works](https://yandex.com/support/webmaster/en/yandex-indexing/site-indexing),
  [canonical URLs](https://yandex.com/support/webmaster/en/robot-workings/canonical),
  [site structure](https://yandex.com/support/webmaster/en/recommendations/site-structure), and
  [link guidance](https://yandex.com/support/webmaster/en/recommendations/links).
- Schema.org: [`Article`](https://schema.org/Article) and [`author`](https://schema.org/author).
- Social preview implementation: [web.dev metadata](https://web.dev/learn/html/metadata) and the
  [Open Graph protocol](https://ogp.me/).

These sources describe eligibility, discovery, and quality signals; none guarantees indexation,
rich results, generative-search citation, rankings, or traffic.
