# Task 120E: provenance и review пилота Gate A

## Exact revision

- Asset version: `120E-pilot-v0.3`.
- Source-set SHA-256: `027ebacef9b8f34d73eb4c8bfc31d8d8076f1e2b5a1c42f057bed9c4a5f37d35`.
- Derivative-set SHA-256: `95617267768f3b2c73fa4188b8f0135079d7604e08e81bea35013d476f20e93a`.
- Дата: `2026-08-31`.
- Статус: `GATE_A_OWNER_APPROVED`; владелец дал точный verdict
  `APPROVE_120E_VISUAL_DIRECTION` 2026-08-31. Pilot files находятся только в
  `.artifacts/`; production manifest использует финальную revision `120e-v1`.

## Generation lineage

- Provider/workflow: OpenAI built-in `image_gen`, text-led YFC-controlled generation.
- Model version, provider job ID и seed: интерфейс инструмента их не раскрывает;
  значение не выдумывается и фиксируется как `not_exposed_by_provider_interface`.
- Input lineage: только текстовые briefs YFC. Для второй фазы и нормализации фона
  использовался ранее созданный в том же pilot YFC asset; third-party images,
  лица, logos и trademarks не использовались.
- Prompt/brief version: `120E-style-v0.3`; нормализованный воспроизводимый brief
  хранится в `HUMAN_VISUAL_PRODUCTION_BRIEFS.md`, style constraints — в
  `HUMAN_VISUAL_STYLE_BIBLE.md`. Provider transcript не является частью Git.
- Всего на пилот выполнено 15 generation/edit calls: 6 базовых фаз и 9
  correction calls. Три попытки с имитацией checkerboard и три кадра с тёмным
  фоном отклонены; они не входят в exact revision.

## Source hashes

| Exercise / phase | SHA-256 |
|---|---|
| `independent-lever-chest-press/concentric_end` | `b816b69a56c46e4f7cdcd751f672fc9aadf46dac595efb7b6853ebfecbef6aff` |
| `independent-lever-chest-press/eccentric_end` | `f6a4d8f1e5820720d965ec6540c4d85947a740e9c1fb0ac519e8b4c1928e709a` |
| `pendulum-squat/concentric_end` | `d94d475bc22ee5b0acd188f6800627d3fb4e4516bfcc8c253c1a79ae56b5484a` |
| `pendulum-squat/eccentric_end` | `a2c7f49a3d77da69f12dab70d62950f32dfc9b024900c492dcc90e42ad045a11` |
| `smith-split-squat/concentric_end` | `80eab831922afcf90d2058a260f657aaa7625dd02e605e2fa4baa8cecb05dfb7` |
| `smith-split-squat/eccentric_end` | `fb396601b129f1417ddb0b414ed77bd182df33a552098aed3822ecd4ea94a459` |

## Legal/provenance review

На `2026-08-31` проверены официальные
[OpenAI Terms of Use](https://openai.com/policies/row-terms-of-use/),
[Services Agreement](https://openai.com/policies/services-agreement/) и
[Service Terms](https://openai.com/policies/service-terms/). Между provider и пользователем права на output передаются
пользователю, но output может быть неуникальным; пользователь отвечает за права
на input и human review. Публичное лицо/его likeness не использовано.

- `origin`: `ai_generated`;
- `author/rightsholder`: YFC-controlled user workflow, subject to provider terms;
- `commercial_use_verified`: `true_as_between_provider_and_user`;
- `redistribution_verified`: `true_as_between_provider_and_user`;
- `modification_verified`: `true_as_between_provider_and_user`;
- `model_release_status`: `not_applicable_no_real_person_input`;
- `property_release_status`: `not_applicable_no_identifiable_property_input`.

Verdict: `PASS_WITH_LIMITATIONS_FOR_GATE_A`. Workflow подходит для планируемого
commercial use/redistribution при сохранении provenance и human review, но не
даёт гарантии уникальности или исключительной copyright protectability в каждой
юрисдикции. `LEGAL_COUNSEL_REQUIRED` не активирован для этого text-only пилота;
он потребуется при стороннем reference asset, likeness или требовании гарантии
исключительных прав.

## Domain и visual review exact revision

| Pair | Identity/equipment | Anatomy/contact | Phase/same setup | Mobile light/dark | Verdict |
|---|---|---|---|---|---|
| `independent-lever-chest-press` | независимые plate-loaded рычаги и опора читаемы | хват, локти, спина и стопы видимы | press/return различимы | pass 360/390 | `PASS_FOR_GATE_A` |
| `pendulum-squat` | pivot, shoulder pads и платформа читаемы | обе стопы и контакт плеч с пэдами видимы | нижняя/верхняя позиции различимы | pass 360/390 | `PASS_FOR_GATE_A`; финальный brief сохраняет запрет на generic sled/hack substitution |
| `smith-split-squat` | гриф остаётся в направляющих Smith | разножка, обе стопы и положение грифа видимы | нижняя/верхняя позиции различимы | pass 360/390 | `PASS_FOR_GATE_A` |

Это review направления, а не approval будущих 30 изображений. Каждый final asset
получает отдельный exact-hash review перед Gate B. Novice-comprehension в Gate A:
по паре без technique text определяются setup, две позиции, движущаяся часть и
основные опоры; owner visual verdict остаётся обязательным.

## Performance evidence

- Master: PNG RGB `1536x1024`, только generation evidence, не production payload.
- Derivatives: WebP `480x320`, `768x512`, `1280x853`, quality 82/84, local same-origin.
- Mobile 480w: 11 640–14 598 bytes на фазу; максимальная pair — 28 386 bytes.
- Budget: 160 KB на фазу / 320 KB на pair — `PASS` для всех трёх пилотов.
- Полный machine-readable отчёт: `.artifacts/task-120E/pilot/derivative-report-v0.3.json`.

## Pipeline/cost expectation

После Gate A для оставшихся 15 pairs ожидаются минимум 30 core generation/edit
calls плюс bounded correction passes. Пилот показал, что equipment/phase lock и
фон требуют ручного контроля; realistic planning range — 45–60 calls и review
каждой из 30 новых фаз. Денежная стоимость не заявляется: встроенный инструмент
не раскрыл цену конкретного вызова. При повторяющемся equipment/anatomy fail
item переводится на controlled 3D/illustrator fallback, а не выпускается «почти
подходящим».
