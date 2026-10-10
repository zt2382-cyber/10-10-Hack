# Groups view: requirements (addition to Closeness, branch `yuri`)

Read `CONTRACT.md` and `docs/req/REQUIREMENTS.md` first. Every hard rule there still applies. Reference for look
and behaviour: `docs/req/groups_prototype.html` (open it in a browser; its script is the working model).

## What it adds

A fourth picture, **Groups**: for one college, a 3 by 3 grid of rule-defined groups of past applicants (score band
by activities band), each showing its real finished cases as dots with counts, and the student's own group
outlined. Plus an honest check on the computer-made "kinds" that already exist.

## Why rule-defined groups

Tested on the national pool: k-medoids kinds on score, activities and major were no better separated than the
same data with its columns shuffled at several colleges, and changed with the sample. A written rule has no seed,
cannot drift, and a counselor can recount it by hand.

## Rules carried over (do not break)

- Python standard library only; plain HTML, CSS, JS; no chart library.
- No "chance", "probab" or "odds" in any string. Counts only, always with n. Never a share or percentage of a group.
- Two pools never merged. National first; own pool shown the same way when it has cases.
- "Not enough" and "can't say" are normal answers.
- Labels (reach, target, likely) are untouched. All existing tests and the 60 of 60 acceptance sheet still pass.

## G1. The rule

For one college and one pool, take every finished case that has a score and an activities rating.

| Band | Values | Rule |
|---|---|---|
| Score | `below`, `inside`, `above` | case score against the college's published `sat25` and `sat75`: below 25th, above 75th, else inside. ACT is converted the same way Closeness does. |
| Activities | `low`, `mid`, `high` | rating under 6; 6 to under 8; 8 and over |

- Constants at the top of the module: `ACT_MID = 6`, `ACT_HIGH = 8`, `GROUP_MIN = 5`, `GROUP_FEW = 15`.
- College has no `sat25` or `sat75`: `status: "cant_say"`, with a plain reason. No grid.
- Cases without a score or rating are left out and counted in `left_out`.
- Waitlisted cases are counted and shown, unlike in the lean.
- Own pool: cases have no activities rating today, so `status: "cant_say"` with reason "the school's own cases
  carry no activities rating". Do not invent one.

## G2. Each group

`{"score_band", "activities_band", "admitted", "waitlisted", "denied", "n", "state", "is_student", "cases"}`

- `state`: `not_enough` when n < 5 (counts hidden on screen, n shown); `few` when 5 <= n < 15; `ok` otherwise.
- `cases`: every case in the group as `[case_id, score, activities, outcome_letter, major_group, hooks]`, sorted by
  distance in score from the student. Cap the whole college at 900 cases; if capped, say so in `capped`.
- `is_student`: true for the one group the student falls in. Needs the student's score and `activities_rating`.
  No rating: no group is marked, and `student_note` says "Give an activities rating to place this student."
  No score: `student_note` says so; the grid still draws.

## G3. Major filter

Done on the screen from `cases` (index 4), not in the engine. Options: all, then each major group with 30 or more
cases at that college. Counts and states are recomputed in JS with the same thresholds, read from the result
(`min_n`, `few_n`), never hard-coded twice.

## G4. The kinds check

For each college where `_kinds` produced kinds, compute three numbers in `similarity.py` and cache them:

| Number | How | Pass |
|---|---|---|
| `separation` | average silhouette width of the kinds, on the same distance `_kinds` uses | 0.51 or more |
| `shuffled` | same, after shuffling each part's values across cases with the kinds seed and re-running kinds | real must beat it by 0.05 |
| `stability` | re-run kinds on 8 seeded 80% subsamples; for each original kind take its best Jaccard match; report the lowest kind's mean | 0.75 or more |

- `verdict`: `clear` when all three pass; `loose` when separation >= 0.26 and stability >= 0.6 and it beats
  shuffled; else `none`.
- When `verdict` is `none`: the screen shows "No clear kinds at this college" and hides kind names everywhere
  (drill-in tab, mind-map leaves, scatter medoid rings). `loose`: names shown with the word "loose grouping".
- Text for each verdict lives in the engine, not the screen.

## G5. The view

- A fourth button, **Groups**, in the picture toggle (after Score ranges, Rings, Mind map).
- A row of college chips above the grid (the list's colleges, in list order, each with its label badge); the first
  college with `status: ok` is selected. Pressing a college in Rings or Mind map then switching to Groups keeps it.
- Grid: column headers with the real numbers ("under 1500", "1500 to 1570", "over 1570"); rows High, Middle, Low
  with their ranges. Each cell: dots (admitted filled circle, waitlisted ring, denied small square: shape, not
  colour alone), then "9 admitted · 4 waitlisted · 28 denied (41)". `not_enough` cells are hatched and say
  "Not enough cases (3)". The student's cell is outlined and tagged "This student".
- Pressing a cell lists its cases below in the existing `examplesTable` style, closest score first, 12 at a time.
- Under the grid, always: the legend, the left-out count, the published range and official admit rate, and the
  self-reported caveat.
- Under that: the kinds check panel (verdict sentence, three numbers with what each needs).
- The what-if score slider on the first view moves the outlined cell without a server call.
- Every cell is a `<button>` with an `aria-label` that reads the counts and "This student is here" when true.

## Contract addition

Per college, inside `closeness.national` (and `closeness.own`):

```json
"groups": {
  "status": "ok", "reason": "", "sat25": 1500, "sat75": 1570,
  "act_mid": 6, "act_high": 8, "min_n": 5, "few_n": 15,
  "left_out": 105, "capped": false, "student_note": "",
  "cells": [{"score_band": "inside", "activities_band": "mid", "admitted": 9, "waitlisted": 4, "denied": 28,
             "n": 41, "state": "ok", "is_student": true,
             "cases": [["N-1042", 1520, 6.5, "d", "CS", "NONE"]]}],
  "caveat": "People who were admitted post far more often than people who were denied, so every group looks rosier than the real applicant pool."
},
"kinds_check": {"separation": 0.38, "shuffled": 0.38, "stability": 0.92, "verdict": "none",
                "text": "No clear kinds at this college.", "needs": {"separation": 0.51, "margin": 0.05, "stability": 0.75}}
```

`cells` always has nine entries in a fixed order (rows high, mid, low; columns below, inside, above).
`kinds_check` is null when there are no kinds. `similarity.method()` gains the new constants so the About page
stays in step with the code.

## Done means

- All existing tests pass, plus new ones in `tests/test_similarity.py`; acceptance still 60 of 60.
- Groups view works from the server, from `?fixture=1`, and from the static build.
- A result without `groups` (old fixture) draws the other three pictures and hides the Groups button.
- No new string contains a forbidden word (extend the existing test that scans for them).
