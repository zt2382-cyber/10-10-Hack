# Closeness: requirements (addition to Counselor Copilot, branch `alex`)

Read `CONTRACT.md` and `README.md` first. Every hard rule there still applies. This file adds one new part,
"Closeness", and three pictures. It changes no existing label, count or rule.

## What it adds

For each college on the list, answer: **does this student look more like the people who were admitted there, or
more like the people who were denied?** Show which group, which kind of admitted student they are nearest to,
what would bring them closer, and pictures of all of it.

## Rules carried over from CONTRACT.md (do not break these)

- Python 3.12, **standard library only**. No numpy, no scikit-learn, no embeddings. Page is plain HTML/CSS/JS, no
  chart library, no build step. Draw with inline SVG like `renderPicture` does.
- **No personal probability.** Closeness is a distance, never a percentage of admission. The words "chance",
  "probab" and "odds" must not appear in any string (see `_FORBIDDEN` in `engine/cases.py`).
- Code sets every number. No model call anywhere in this part.
- Two pools never merged: `national` (self-reported) and `own` (the school's, SYNTHETIC today).
- "Not sure" is a normal answer: `not_enough`, `cant_say`, `none`.
- The reach / target / likely label stays exactly as `labels.py` sets it. 60 of 60 acceptance and all 177 tests
  must still pass.
- Hooks, race, gender and income are never suggested as things to change.

## The data that exists (measured on this branch)

`data/cases/applicants_wide.csv`: 2,247 people. `decisions_long.csv`: 20,966 decisions at 58 colleges, every one
with 30 or more cases (largest: UPENN 894).

| Field | Usable for distance | Gaps |
|---|---|---|
| SAT, ACT | yes (ACT via `colleges.act_to_sat`) | SAT missing in 763 rows, ACT in 1,390; value -1 means missing |
| EC-AWARDS (0 to 10, self-rated) | yes | 9 missing |
| Rank% | optional | 1,429 missing |
| Major, Hooks, Residence | yes | Major "-1" in 185 |
| ESSAY-LOR-INTERVIEW (0 to 10, self-rated) | no: the student has no matching number | |
| GPA, activity text, essay text | not in the national file | own-school cases have `gpa`, `activities_note`, `essay_theme` |

Reuse the loaders in `engine/cases.py` (`_national()`, `_own_rows()`, `_score`, `_case_major_group`,
`_hooks_from_case`, `major_group_for`) and `colleges.case_name_for`. Do not re-parse the CSVs.

## R1. Distance between the student and one past case

Each part is 0 (same) to 1 (far). Total = weighted mean of the parts both sides have. A part missing on either
side is skipped and named in `not_used`.

| Part | Weight | Distance | Notes |
|---|---|---|---|
| `score` | 0.45 | abs(SAT difference) / 400, capped at 1 | Required. No score on the student: `cant_say`. Cases without a score are left out. |
| `activities` | 0.20 | abs(rating difference) / 10 | Student side is a new optional input `activities_rating` (0 to 10, the counselor's own rating). National: `EC-AWARDS`. |
| `major` | 0.15 | 0 same major group, 1 different | Use reader tag `major_group` when the student gave none and the two models agreed. |
| `hooks` | 0.10 | 0 same hook status, 1 different | Matched on, never suggested. |
| `residency` | 0.10 | 0 if both in-state or both out-of-state for this college, else 1 | Public colleges only. |
| `gpa` | 0.20 | abs(GPA difference) / 1.0, capped | Own-school pool only. |

Weights live in one table at the top of the module. They are starting values, not tuned.

## R2. Closeness to each college's two groups

Per college and per pool, split scored cases into admitted and denied. Waitlisted are counted and shown, in
neither group.

- `d_admitted` = mean distance to the 7 nearest admitted cases. `d_denied` = the same for denied.
- `gap` = `d_denied` minus `d_admitted`.
- `lean`: `closer_to_admitted` when gap >= 0.03; `closer_to_denied` when gap <= -0.03; else `in_between`.
- `status`: `ok` when both groups have 15 or more scored cases; `not_enough` when either has 1 to 14 (still show
  counts, set `lean` to null); `none` when a group is empty or the college has no cases; `cant_say` with no score.
- **Steady test** (same idea as the label edge test): recompute with 5 and 10 neighbours and with the score 30
  points lower and higher. `steady` is true when `lean` never changes; otherwise list each change in `flips`.
- `parts`: mean distance per part to the 7 nearest admitted, so the screen can say "close on score, far on
  activities".
- `nearest_admitted` and `nearest_denied`: up to 3 case ids each, with per-part distances. Same example shape as
  `cases._example`.

## R3. Kinds of admitted student (clusters)

Per college, national pool, when 30 or more admitted cases are scored: group them into 3 kinds with k-medoids
(pure Python, fixed seed, at most 20 rounds, at most 300 cases; sample with the seed if more). A medoid is a real
case, so each kind is described by counting, in code: median score, median activities rating, most common major
group, size. Name each kind from those facts only, e.g. "High score, CS, activities 7". Report which kind the
student is nearest to and the distance. Fewer than 30: `kinds: []`.

## R4. What would bring the student closer

For each college with `status: ok`, try each change alone, recompute `gap`, keep the ones that raise it by 0.02
or more, return up to 3, largest first:

- score 30, 60 and 100 points higher (cap 1600)
- activities rating 1 and 2 higher (cap 10), worded "deeper involvement in the activities already listed"
- each other major group the student has named as an interest (only if more than one is given)

Each item: `{"change", "gap_before", "gap_after", "lean_after", "because": [case ids]}`. Never vary hooks, home
state, GPA, or anything about who the student is. Never word a change as inventing or inflating anything. If
nothing helps: one plain line, "Nothing we can measure here would move this."

## R5. How well it holds up (small, secondary)

`python -m engine.similarity --check`: for a seeded sample of 400 real national decisions, hide that person, compute
`lean` for that college, and print a table: for each lean, how many were in fact admitted and denied. Save it to
`docs/closeness_check.json`; show it under "How this was made" as counts, with the self-reported caveat. National
pool only. Never SYNTHETIC rows.

## R6. Pictures (plain SVG, in `web/app.js`)

1. **Rings** (first view, beside "Where this student stands"): student at the centre, one dot per college, distance
   from the centre = `d_admitted` scaled, dot shape and colour = the existing label badge, hollow dot when
   `not_enough`. Pressing a dot opens that college.
2. **Mind map** (first view, toggle with Rings): student in the middle, three branches for reach, target and likely,
   a node per college, and under each college its nearest kind and its 3 nearest admitted cases. Simple radial
   layout computed in JS; no library.
3. **Fifth tab in the drill-in, "Who they resemble"**: a scatter of that college's cases, score across and
   activities rating up, admitted and denied as different shapes (not colour alone), the three kinds' medoids
   marked, the student as a star; under it, a bar per part (close to far), the nearest admitted and denied cases
   in the existing cases table, and the R4 list.

Every picture needs a text equivalent (`aria-label` or a short sentence), like the existing ones.

## Contract addition: `closeness` on each college in Result

```json
"closeness": {
  "needed": 15, "neighbours": 7,
  "national": {
    "source": "Self-reported public posts (r/collegeresults)", "verified": false, "status": "ok",
    "n_admitted": 212, "n_denied": 480, "n_waitlisted": 61,
    "d_admitted": 0.18, "d_denied": 0.24, "gap": 0.06, "lean": "closer_to_admitted",
    "text": "Looks more like the people admitted here than the people denied.",
    "steady": false, "flips": [{"cause": "score 30 points lower", "to": "in_between"}],
    "parts": [{"part": "score", "distance": 0.05, "text": "close"}, {"part": "activities", "distance": 0.4, "text": "far"}],
    "not_used": ["GPA", "essay", "activity descriptions"],
    "nearest_admitted": [], "nearest_denied": [],
    "kinds": [{"kind_id": "K1", "name": "High score, CS, activities 7", "size": 88, "median_sat": 1540,
               "median_activities": 7, "top_major": "CS", "medoid_case_id": "N-1042", "distance": 0.12, "nearest": true}],
    "changes": [{"change": "Score 60 points higher", "gap_before": 0.06, "gap_after": 0.11,
                 "lean_after": "closer_to_admitted", "because": ["N-88", "N-1042"]}],
    "points": [{"case_id": "N-1042", "sat": 1460, "activities": 6.5, "outcome": "admitted", "kind_id": "K1"}]
  },
  "own": {"source": "Your school's own finished cases", "verified": true, "status": "not_enough", "n_admitted": 1, "n_denied": 3},
  "caveat": "Closeness compares this student with people who chose to post their results. It is not a forecast."
}
```

`points` is capped at 300 per college. Top level of Result gains `"closeness_check"` (R5 table, or null).
`StudentInput` gains optional `activities_rating` (0 to 10) and `major_interests` (list).

## Done means

- `python -m unittest discover -s tests -t .` passes, including new `tests/test_similarity.py`.
- `python tests/acceptance/run_acceptance.py` still 60 of 60.
- `python server.py`: a demo student builds in about the same time as before (closeness adds under 1 second for
  10 colleges; cache per-college groups and kinds with `lru_cache`).
- The screen still works when `closeness` is missing (old fixture, `?fixture=1`, static build).
- `tools/make_static.py` output includes the new pictures.

## Not today

Text embeddings, 2D projection of all parts (the scatter uses two real axes instead), learned weights, a list
optimiser, PDF changes.
