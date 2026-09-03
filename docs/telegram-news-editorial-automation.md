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

## Hardened editorial worker: repository integration

The tracked worker is a narrow, provider-compatible editorial adapter. It is not the official
monolithic Hermes image and does not expose the general Hermes agent loop. Its upstream provenance
is recorded in `deploy/hermes-editorial-worker/hermes-provenance.json`:

```text
Hermes version: 0.21.0
tag: v2026.8.31
commit: 29112bef099274229cadff79cdff7bf7b99c4b77
source behavior patches: 0
```

The exact upstream license is kept in `deploy/hermes-editorial-worker/LICENSES/HERMES-LICENSE`.
`license_bundle.py` builds a deterministic `/opt/licenses` bundle from the pinned Python lock,
installed distribution metadata and the Alpine APK database during the image build. The image
also contains the generated Python/Alpine inventory and the upstream license; no credential or
source content is included. The build fails if the lock and declared inventory diverge.

### Reproducible local verification

Run from a clean checkout with Docker available:

```powershell
python scripts/hermes_worker.py provenance --source-dir <exact-hermes-checkout>
python scripts/hermes_worker.py verify
```

`verify` checks the exact base digest and lock, builds with `--pull=false`, runs the hardening
boundary, executes the local HTTP E2E harness, generates CycloneDX and SPDX SBOM files, and runs
the pinned Trivy CRITICAL/HIGH gate. The source checkout is used only for offline provenance
verification; it is not copied into the runtime image. Build context is the tracked
`deploy/hermes-editorial-worker` directory and its `.dockerignore`; `.artifacts/` contains only
evidence and is never a build input or commit target.

The lock contains only the worker closure and has no floating versions or provider SDK:
`httpx`, Pydantic and their exact transitive dependencies. The base is
`python:3.13-alpine@sha256:46ee549c88617e9bc8acb843a326f1a5c0fa5608d7f9703509efe6d53b55f318`.
The final image runs as UID/GID `10000:10000`, drops all capabilities, sets
`no-new-privileges`, removes the package shell/tooling surfaces, declares `/opt/data` as the only
state volume, and is tested with a read-only root filesystem. The verification budget is 0.50
CPU, 512 MiB RAM and 64 PIDs per container; these are safety bounds, not a production capacity
benchmark.

The worker accepts one bounded job, sends the source packet only to an OpenAI-compatible provider
endpoint, validates a structured response, and signs the YFC intake payload. The current tracked
configuration allows only local/mock provider, intake and preview endpoints. It has no terminal,
browser, MCP, plugin, Telegram, dashboard, database, publish or Docker-socket capability. A
request for an unsupported capability, malformed endpoint, oversized input/output, prompt
injection marker, failed provider response, invalid schema, invalid HMAC, duplicate replay or
source outside the allowlist fails closed.

The local E2E path is:

```text
tracked source fixture
  -> hardened Docker worker
  -> local OpenAI-compatible fake HTTP provider
  -> structured draft response
  -> HMAC-signed YFC intake contract
  -> local YFC FastAPI intake
  -> taxonomy/risk classification
  -> immutable draft revision, manual_required
  -> local editorial preview mock (published=false)
```

The fake provider is an HTTP server, so this verifies the actual transport/protocol path; it does
not claim real-model quality. Local tests set `HERMES_INTAKE_ENABLED=true` only inside the
test-process YFC server. They set the local news flags to false and cannot change production.

### Deployment boundary and operations

The selected production topology remains a separate Linux `x86_64` VM; it has not been created.
The current YFC host is not a placement target: the earlier read-only baseline was 1 vCPU, about
958 MiB RAM with about 163 MiB available and swap pressure, and about 4.37 GiB free disk. The
planning minimum for a dedicated VM is 2 vCPU, 4 GiB RAM and 30 GiB SSD (20 GiB is only a short,
stateless-shadow floor), with cgroup v2, default-deny host ingress/egress firewall, no public
inbound ports, no host mounts, no Docker socket and no YFC DB/Redis/SSH access. Expected external
LLM editor workload is an unbenchmarked 0.25-1.0 vCPU and 0.5-1.5 GiB RAM; confirm the budget in
an owner-approved shadow run.

Before Gate A approval the network is local-only: the test harness uses loopback and Docker's
`host.docker.internal` mapping solely for local services. No production allowlist is changed.
After a separate approval, the VM allowlist must explicitly name the approved provider API host,
the YFC intake host/path and approved source hosts; it must deny Telegram Bot API, YFC
PostgreSQL/Redis/internal services, Docker API/socket, SSH, cloud metadata, arbitrary redirects,
registries and wildcard internet egress. There are no inbound Hermes ports.

The exact variable names reserved for a later approved setup are:

```text
HERMES_INTAKE_ENABLED
HERMES_SOURCE_ALLOWLIST
HERMES_PROVIDER_BASE_URL
HERMES_PROVIDER_API_KEY
HERMES_PROVIDER_MODEL
HERMES_PROVIDER_TIMEOUT_SECONDS
HERMES_YFC_INTAKE_URL
HERMES_YFC_INTAKE_KEY_ID
HERMES_YFC_INTAKE_SHARED_SECRET
HERMES_YFC_INTAKE_TIMEOUT_SECONDS
HERMES_PREVIEW_URL
HERMES_PREVIEW_TIMEOUT_SECONDS
```

Only provider API key and YFC shared secret are secret values. No Telegram token, database
credential, user health data or host credential belongs in this worker. The pre-Gate build uses
empty local/mock secret values from `.env.example`; it does not create accounts, keys or service
identities. Source content is sent only to the local fake provider in the E2E test and is not
sent to YFC intake. A future external provider must be separately approved for retention,
training/model-improvement use, region, privacy terms, rate limits and cost before any source
content leaves the controlled environment.

The kill switch is `HERMES_INTAKE_ENABLED=false`; keep it off until Gate A. The existing
production `NEWS_INGESTION_ENABLED` and `NEWS_PUBLICATION_ENABLED` values are not changed by this
integration, and `NEWS_AUTO_PUBLISH_LOW_RISK=false` remains required. Rollback is to stop/remove
the separate worker workload, revoke only its approved intake/provider identities, remove its
egress rules, and return to the existing YFC manual/editorial path. Existing news pipeline flags
and publisher ownership are not rollback targets. Any later production rollback must use the
previously verified immutable application/image SHA and the normal release procedure; no blind
migration downgrade is permitted.

The evidence boundary is explicit: local/mock proves deterministic contracts, hardening,
idempotency, HMAC, taxonomy/risk and manual-required behavior; a shadow run requires owner approval
and a real provider; production and Telegram/channel proof require later external gates. This
repository integration grants neither Gate A nor any deployment authorization.
