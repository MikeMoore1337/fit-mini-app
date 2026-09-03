# Hardened Hermes editorial worker (Task 129)

Это минимальный non-root container для одной bounded editorial job. Он принимает
source metadata/content packet из `/opt/data`, вызывает только OpenAI-compatible
`/v1/chat/completions`, проверяет structured response и отправляет подписанный
`hermes-editorial-intake-v1` в YFC. После `accepted` он отправляет только
preview-only payload в allowlisted local preview endpoint.

Worker не содержит source fetching, scheduler, database client, shell/tool dispatch,
browser, MCP, plugins, Telegram Bot API или publish endpoint. Полный Hermes monolith
не является частью image. Upstream Hermes сохраняется как provenance contract и
проверяется локальным `scripts/hermes_worker.py provenance --source-dir ...`.

Из чистого checkout с локально доступным exact Hermes source checkout:

```powershell
python scripts/hermes_worker.py verify --source-dir <exact-hermes-checkout>
```

`verify` сначала сверяет рабочую копию Hermes с commit/tag/version/license, затем выполняет
весь bounded local sequence: clean tracked build, hardening boundary, local HTTP E2E, CycloneDX и
SPDX SBOM, а также CRITICAL/HIGH gate. `--source-dir` используется только для offline Git
проверки и не копируется в image. Для SBOM/security exact Trivy image и актуальная DB должны
быть доступны локально; обычный CI от внешнего Hermes/Groq/Telegram и от этого scanner path не
зависит. Отдельные команды `provenance`, `build`, `hardening`, `e2e`, `sbom` и `security`
остаются доступны для targeted проверки.
