# Telegram editorial automation (Task 129)

## Status and ownership

The canonical source of truth remains the YFC backend.  Hermes is an optional external discovery
and drafting worker behind `POST /api/v1/hermes/editorial/intake`; it is not a publisher, source
database, Telegram bot runtime or production shell.

The intake flag is off by default:

```text
HERMES_INTAKE_ENABLED=false
NEWS_AUTO_PUBLISH_LOW_RISK=false
NEWS_INGESTION_ENABLED=false
NEWS_PUBLICATION_ENABLED=false
```

Telegram Bot API polling continues to have one owner.  No second polling process, bot token,
channel id or BotFather change is introduced by this task.

## Hermes boundary

The official Nous Research Hermes Agent repository and documentation were checked on 2026-09-03:
[repository](https://github.com/NousResearch/hermes-agent) and [official documentation index](https://hermes-agent.nousresearch.com/docs/).
The repository describes a messaging gateway with Telegram and a scheduled-job capability.  This
task does not install Hermes, connect an account, configure a provider, or make a live Telegram or
provider call.  Pinning an owner-approved Hermes release and deployment image is a separate Gate A
decision.

```text
Hermes scheduled worker
  -> HMAC-signed bounded candidate/draft intake
  -> YFC allowlist + URL validation + taxonomy + risk policy
  -> immutable NewsDraftRevision and exact YFC preview
  -> owner/manual Telegram editorial workflow
  -> existing YFC publisher and reconciliation
```

Hermes may submit source metadata, a short claim packet and a structured Russian draft proposal.
YFC recomputes source identity, taxonomy, evidence and publication risk.  Hermes cannot receive a
channel token, call `sendMessage`/`sendPhoto`, call a publish endpoint, query the database, execute
general production shell commands, or send user profile/diary/measurement/initData values.
Fetched source text is untrusted input and cannot override the editorial contract.

### Intake contract

Headers are signed as `HMAC-SHA256(secret, timestamp + "\\n" + nonce + "\\n" + raw_body)`:

```text
X-Hermes-Key-Id
X-Hermes-Timestamp       # Unix seconds, bounded clock skew
X-Hermes-Nonce           # unique replay-protection value
X-Hermes-Signature       # sha256=<lowercase hex digest>
```

The payload is `hermes-editorial-intake-v1`, with one allowlisted source packet, one structured
draft proposal and provider/model/prompt/skill provenance.  The source content hash is recomputed
by YFC.  Idempotency key and nonce are unique in `hermes_editorial_submissions`; a repeated exact
request returns the same draft as `duplicate`, while a changed payload or replayed nonce fails
closed.  Body size, source count, clock skew, replay TTL and request rate are configured by the
`HERMES_INTAKE_*` variables in `.env.example`.

Receipts retain only operational metadata and hashes, never the full submitted source or draft
payload.  Normal logs contain correlation-safe ids/reason codes only.

## Taxonomy and policy

`NewsCluster` stores versioned independent fields:

```text
primary_topic, topics[], content_type, product_class, evidence_level,
risk_level, audience, geography[], classification_version,
classification_reasons[], discovery_eligible, discovery_reasons[],
publication_policy, risk_reasons[], risk_policy_version
```

`sports_nutrition` and `dietary_supplements` are separate topics and separate product classes from
food, medicine and peptides.  Research is a `content_type` and never replaces the subject topics.
Unknown or ambiguous classification goes to manual review; it is not silently promoted to a safe
topic or auto-publication.

Discovery recall and publication eligibility are separate.  A primary/official current item with
semantic topic evidence can remain a discovery candidate even when the legacy coarse topic scorer
does not match.  Unsafe/prescriptive content still hard-blocks.  Existing counters distinguish
`duplicate`, `stale`, `below_threshold`, `rejected`, `candidate` and `eligible`; source fetch
failures remain visible on `NewsSource` as error code/time/consecutive count and are not reported as
“no news”.

The server-side policy is:

```text
blocked | manual_required | auto_eligible
```

Sensitive medical/pharmacology, peptides, AAS/SARMs, dosage/cycle/protocol, individualized
recommendations, pregnancy/minors/chronic disease/symptoms, interactions, recalls/contamination,
preliminary or conflicting evidence and any ambiguity are at least `manual_required`.  Prompt
injection, unsupported numbers and explicit unsafe/guaranteed claims are blocked.  `auto_eligible`
also requires the owner-controlled `NEWS_AUTO_PUBLISH_LOW_RISK=true`, valid source provenance,
quality checks, an exact snapshot and an active kill-switch.  The committed default is false.

The deterministic style checklist checks template/AI meta language, fake personal voice, clickbait,
invented quotes, excessive exclamation and mechanical repetition.  It does not use an AI detector,
does not promise detector evasion and does not establish authorship.

## Telegram editorial UX

Immediate publish confirmation edits only the inline markup of the original preview card.  The exact
text/caption, channel, mode, text revision, image revision and artifact hash remain bound to the
same `message_id`.  Confirm calls the existing hash-bound YFC action once; queued/already-queued
removes destructive buttons and appends a status to that card.  Cancel restores the exact revision
actions on the same card.  Stale, forbidden, quality-blocked and network-failure cases keep a
recoverable card and use a callback alert.

The confirmation path must not call `callback.message.answer` or `send_message`.  Media and text
cards use the same rule.  Scheduled input may use a temporary prompt message, but its final action
still targets the original anchor card.

## Growth and attribution

Telegram posts must have standalone value, a relevant canonical CTA and no clickbait or artificial
urgency.  Campaign values and destinations are allowlisted by `news_growth.py`; no arbitrary query
parameters, source/body text, health data, Telegram ids or PII enter attribution.

The existing provider-neutral product event contract is extended only with the constrained
`telegram_news_cta_clicked` event.  A CTA click is intent, not a lead.  The reporting definitions
are distinct:

| Metric | Meaning |
| --- | --- |
| reach/view | Aggregate platform signal, not proof of reading |
| audience growth | Aggregate channel count change |
| engagement | Aggregate reaction/share/action available from Telegram |
| CTA click | Allowlisted canonical destination click |
| qualified lead | Explicit first-party Demo/Mini App/sign-up start |
| product conversion | Server-confirmed product outcome |
| activation | Separately owner-defined product milestone |

Attribution separates Telegram/Web/TMA and test/staging/production.  Analytics outages never block
the editorial pipeline.  Numeric KPI targets are intentionally not invented before a baseline.

## Task 130 handoff

Each draft metadata contains an `article_candidate` object with a stable news cluster/revision
reference, primary topic, content type, optional already-published canonical URL and
`web_lifecycle_owner: task-130`.  No Web article body, slug, SEO schema, `/articles` route, sitemap,
indexing state, Landing block or Web publish state is created here.

## Operations, kill switch and correction

1. Keep `HERMES_INTAKE_ENABLED=false` until Gate A owner approval covers the selected Hermes version,
   deployment isolation, provider/data retention, outbound domains, auth rotation and rollback.
2. Run local/mock signed intake tests and inspect the exact preview before any external setup.
3. Keep `NEWS_AUTO_PUBLISH_LOW_RISK=false`; if later activated, first run a shadow/manual sample and
   review representative Russian corpus for clarity, usefulness and template repetition.
4. Disable intake or low-risk automation immediately by flipping the corresponding flag; no Hermes
   fallback may bypass YFC policy.
5. A materially wrong post uses the existing exact snapshot/audit trail and manual correction,
   replacement or retraction path.  The original snapshot and reason remain retained according to
   editorial retention policy.
6. Provider timeout, source outage or ambiguous Telegram result stays a normalized failure/uncertain
   state.  Retries are bounded and idempotent; no duplicate publication is inferred.

Production source coverage, live Hermes/provider behavior, real Telegram/channel sends and device
smoke are deliberately unclaimed until the owner authorizes the corresponding external gates.
