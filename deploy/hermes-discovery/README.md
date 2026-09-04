# Hermes discovery runner и scheduler (Task 129)

`discovery_runner.py` — отдельный stdlib-only runtime для получения public RSS/JSON
Feed/HTML metadata. Он не импортирует hardened editorial worker и не имеет provider key,
YFC DB/intake secret, Telegram token, shell, browser, MCP, plugin или publish capability.
Source text всегда data: prompt/source instructions не исполняются.

Поток после отдельного Gate A:

```text
systemd timer
  -> hermes-discovery.service (source-only container)
  -> versioned YFC source definitions
  -> explicit HTTPS source hosts + DNS/redirect revalidation
  -> /var/lib/hermes/outbox/<stable-key>.json
  -> hermes-worker-drain.service (secrets только здесь)
  -> hardened editorial worker
  -> approved provider + HMAC YFC intake
```

## Source of truth

Canonical allowlist — `backend/fitminiapp_api/resources/news_sources.json`. Второго
редактируемого списка источников нет. Команда
`scripts/generate_hermes_source_definitions.py` проверяет canonical registry и рендерит
детерминированный `hermes-source-definitions-v1` с SHA-256 исходного файла и
`definitions_version=yfc-news-sources:<sha256>`. Этот файл является versioned deployment
artifact, его нельзя редактировать вручную. Перед установкой его SHA-256 должен быть подставлен
в оба systemd template как `HERMES_DISCOVERY_DEFINITIONS_SHA256`; external runtime отклоняет
файл с отсутствующим или несовпадающим digest. На VM он монтируется read-only в
`/opt/hermes/config/source-definitions.json`.

Тестовый `local_mock` envelope может содержать только loopback/`host.docker.internal` URLs и
существует исключительно в local E2E. Production/external mode принимает только HTTPS,
точные hosts из этого versioned файла, без IP literal, wildcard и arbitrary URL.

## Discovery bounds and safety

- maximum 50 definitions, production unit ограничивает run 20 sources, 4 concurrent fetches;
- per-source timeout 10 seconds in the unit, response maximum 512 KiB, maximum 20 items;
- RSS/Atom, JSON Feed и HTML metadata имеют отдельные allowlisted MIME types;
- every source URL и every redirect revalidate exact host, scheme, port и DNS result;
  external DNS must resolve only to global addresses; localhost, RFC1918, loopback,
  link-local, reserved и cloud-metadata targets fail closed;
- redirects не следуются автоматически: максимум три hop с повторной allowlist/DNS проверкой;
- нет JavaScript/browser, source URL worker самостоятельно не fetch'ит;
- parser получает bounded bytes, а systemd `RuntimeMaxSec` прерывает зависший run;
- source outage записывается в bounded state и не превращается в «нет новостей» или quota/filler.

Discovery eligibility — это только высокий recall candidate generation. Unknown topic не
отбрасывается runner'ом; `topics` — provenance source definition. Taxonomy, risk,
`manual_required`, immutable draft revision и publication eligibility пересчитывает YFC intake.
Topic vocabulary в definitions покрывает направления Task 129, но enabled/disabled coverage
определяется только текущим canonical registry; discovery не добавляет фиктивные источники или
обязательную квоту публикаций.

## State, dedupe и restart

`/var/lib/hermes/state.json` хранит только version/hash, fetch metadata, error codes и bounded
candidate metadata; полный source packet живёт в outbox только до accepted/duplicate handoff.
Outbox пишется через fsync + atomic link/rename. Stable key вычисляется из
`source_id + canonical URL + content hash + event date`; filename, job id, idempotency key и
request nonce детерминированы этим key. Повторный timer run, crash/restart или uncertain worker
state не создаёт новый idempotency key автоматически. Pending job остаётся для повторной попытки;
после accepted/duplicate drain удаляет только этот outbox packet и отмечает state.

Два lock-файла предотвращают overlap discovery и overlap drain. Stale lock восстанавливается
только после bounded age threshold. Missed timer run не replay'ится (`Persistent=false`), а
следующий запуск снова применяет dedupe без publication quota.

## Установка после approval (не выполняется этим PR)

1. Из exact release bundle сгенерировать definitions из canonical registry и зафиксировать
   SHA-256 самого deployment-файла.
2. Подставить в `*.service.template` только immutable digest discovery image, worker image и
   этот SHA-256 как `HERMES_DISCOVERY_DEFINITIONS_SHA256`; floating `latest` запрещён.
3. Создать отдельную Linux x86_64 Hermes VM и `/etc/hermes/source-definitions.json` (0444),
   `/etc/hermes/worker.env` (0600), `/var/lib/hermes` (0700). Для bind mount каталога
   container UID/GID `10000:10000` должны иметь запись в `/var/lib/hermes`; host service account
   `hermes` должен быть согласован с этим UID/GID и иметь только требуемый Docker/rootless-Docker
   доступ. VM не содержит YFC repo/runtime/DB.
4. Настроить default-deny egress firewall: exact approved source hosts для discovery, exact
   Groq host и exact YFC intake host/path для worker; deny Telegram Bot API, PostgreSQL/Redis,
   SSH, metadata, registry и arbitrary internet. Inbound Hermes ports отсутствуют.
5. Включить timer только после Gate A и owner-approved credentials. `HERMES_INTAKE_ENABLED`
   остаётся false до отдельного approval; production `NEWS_*` flags не меняются.

`hermes_worker_drain.py` — host-side launcher; secrets передаются только worker container.
Discovery service не получает ни provider key, ни YFC HMAC secret. Рабочий runtime запускается
non-root, с read-only rootfs, no-new-privileges, drop capabilities и bounded cgroup.
