# Post-release validation plan

This file is NOT a pre-release implementation backlog.

After the release, observe before adding features.

## Activation
- landing -> auth/demo
- auth -> onboarding completion
- onboarding -> first meaningful action
- first food log
- first program selection
- first workout start/completion

## Ongoing value
- weekly active users
- workouts completed
- food logging consistency
- weekly check-in completion
- progress/measurement usage
- trainer-client workflows
- AI Coach opens/questions/helpfulness signal

## Reliability/support
- auth failures
- lost/duplicated workout logs
- notification failures
- export/delete failures
- provider degradation
- frontend/backend error rates

## Qualitative questions
Ask real users:
- What did you expect to happen but could not find?
- Which screen is confusing?
- Which feature do you actually use every week?
- What feels unnecessary?
- Would you keep using YFC if AI Coach disappeared?
- Does Coach make useful conclusions from your own data?
- What would make you recommend YFC to another person?

## Rule
Do not convert every request into a feature.
Prioritize repeated problems and measurable friction.
