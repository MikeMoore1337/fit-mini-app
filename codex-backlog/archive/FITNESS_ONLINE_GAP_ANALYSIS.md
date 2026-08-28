# Fitness Online-inspired gap analysis

Repository: MikeMoore1337/fit-mini-app
Branch inspected: feature/yfc-platform-v2
Observed branch head: 89d2f185e1275744209192edd01883058231cf6d

Re-check repository when each task executes.

## Existing exercise capability
`Exercise.primary_muscle`, equipment and difficulty already exist. `exercise_guides.py` already has technique steps, breathing, common mistakes, secondary muscle profiles, muscle functions, phase images and source/license metadata. Current guide UI renders technique/breathing/mistakes/images but does not fully expose all structured muscle data.

## Existing analytics
Current analytics already calculates adherence, streak, weight change, weekly completed workouts, weekly volume = completed reps × weight, max weight, best set volume, PR and workout timeline. New task extends rather than replaces.

## Existing programs
`ProgramTemplate` already has goal/level and template/day/exercise structure; self assignment/editing exist. Recommender ranks real templates instead of creating a second system.

## Gaps observed
No RIR in `UserWorkoutSet`; no normalized muscle relation for analytics; no dedicated deterministic recommender/wizard found; no contextual trainer workout/exercise comment model found; no dedicated `/knowledge` routes found; media is primarily static phases and needs explicit cross-platform pipeline.

## Product direction
Your Fitness Coach = питание + тренировки + вес/замеры + adherence + trainer + единая аналитика + знания.
