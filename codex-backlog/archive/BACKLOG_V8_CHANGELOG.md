# Backlog v8 changelog - mobile/TMA-first

- User-confirmed completed scope fixed at tasks `00-49`; no narrow rework exception remains.
- Added task `50A` before task `50`: shared Mobile Web/TMA contract, platform adapter baseline, reusable Playwright fixtures and continuous `tma-smoke` gate.
- Added `MOBILE_TMA_FIRST_CONTRACT.md` as the product-level source of truth for smartphone-first client flows.
- Pending client-facing tasks `50-70` now require feature-specific Mobile Web/TMA acceptance instead of deferring it to task `72`.
- Task `71` is explicitly desktop-first and absent from TMA; task `72` remains final platform hardening rather than the first Telegram pass.
- Tasks `73-79` now include mobile/TMA evidence where relevant.
- Updated skill assignments to `.agents v4`; `$mobile-engineer` now owns Mobile Web/TMA runtime and acceptance, while `$telegram-engineer` owns Telegram-specific APIs and trust boundaries.
- Updated execution status, order, dependency graph, completion checklist, model guidance, source coverage and manifests.
- No completed task file `00-49` was modified.
