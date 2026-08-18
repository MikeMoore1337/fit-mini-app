# Demo Mode integration notes

Demo Mode is implemented as tasks `62-68`.

It is located:
- after the complete non-AI core product;
- before Telegram final polish;
- before premium landing refresh;
- before cross-product accessibility/performance/final regression.

This allows the project to:
- demonstrate the factual product;
- keep real AI UI/API/provider calls disabled in demo;
- avoid polishing Telegram twice;
- give the landing task a working demo CTA.

AI Coach in demo is fully disabled. A non-interactive teaser is acceptable.

Original decomposed demo package: `masters/demo-mode/`.
Working tasks `62-68` are adapted to the current backlog and should be used instead of reading the full master package by default.

## Training expansion
Demo may use synthetic/ephemeral program recommendation, RIR, expanded exercise guide and one trainer contextual comment, with no real side effects.
