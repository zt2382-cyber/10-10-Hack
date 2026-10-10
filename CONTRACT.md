# Build contract: Counselor Copilot

Written 2026-10-10 12:30 EDT, during the hackathon window. Everything in this repository is built today.
This file is the agreement between the parts. If it is wrong, say so in your report; do not quietly work around it.

## What we are building
For a college counselor in a meeting with a family. The counselor enters one student and the colleges under
discussion. The screen shows, per college: a reach / target / likely label set by code from published numbers; real
finished cases like this student (admitted, denied, waitlisted) with how many there are and where they came from;
what the college itself says it weighs; and a plain statement whenever the evidence runs out. Above the list: whether
the list is balanced, and suggested fills. It never gives a personal chance of admission.

The company is Nerd Apply (real, de-identified case studies for counselors; privacy is a selling point for them).
The theme is "AI You Can Trust". Judges test accuracy first, then how easy it is to check the AI's work.

## The twelve needs this must meet (from the team)
1. Proof to show in a parent meeting. 2. A deliverable reach / target / likely list. 3. Per-college outcomes among
k similar students, with n. 4. Explicit uncertainty: small n, no local cases, no bluffing. 5. List warnings:
reach-heavy, no likelies, prestige pile-on. 6. Verified de-identified cases kept apart from self-reported posts.
7. The counselor's own cases and a national pool in one flow. 8. Whole profile: grades, activities, essay themes.
9. Sentences only from retrieved cases and published data; say when evidence is missing. 10. Helps the counselor,
who still decides. 11. Suggest strong matches beyond the same ultra-selective colleges. 12. Traceable steps:
retrieve, score, bucket, explain, log.

## Hard rules for every part
- **Code sets every label, count and number. A model only reads text and returns quotes and tags.** No model output
  is shown unless code has checked it.
- **Never output a personal probability or "chance".** A count such as "8 of 23 similar cases were admitted" is
  allowed only with n, the source of the cases, and the college's official admit rate beside it.
- **Uncertainty is a normal answer:** `cant_say`, `not_enough`, `none`, `outside_data` are first-class states.
- Python 3.12, **standard library only** (no pip installs). The page is plain HTML, CSS and JavaScript, no build step.
- No keys, tokens or coupon codes in any file. Keys come from environment variables (named below).
- No real student data. Demo students and school cases are invented and every one is stamped `SYNTHETIC`.
  The self-reported pool is real public posts, already without names; label it "self-reported" everywhere.
- Plain language in every string a person reads. Say what a thing is before using a short name for it.
- **Write only the files listed as yours.** Do not edit `CONTRACT.md`, `engine/colleges.py`, `docs/fixture_result.json`,
  or another part's files. Each module must import cleanly even when the others are absent.
- Each module has a `python -m engine.<name>` self-check that prints something readable, and a
  `tests/test_<name>.py` (unittest) that passes with `python -m unittest tests.test_<name>` from the repo root.
- No network calls in tests. Network code takes a timeout and returns a status instead of raising.

## Files and owners
| Files | Part |
|---|---|
| `engine/colleges.py` (done), `engine/pipeline.py`, `server.py`, `CONTRACT.md`, `docs/fixture_result.json` | Integration |
| `engine/labels.py`, `tests/test_labels.py` | Labels |
| `engine/cases.py`, `engine/caselog.py`, `data/synthetic/SYNTHETIC_school_cases.csv`, `tests/test_cases.py`, `tests/test_caselog.py` | Cases |
| `engine/balance.py`, `tests/test_balance.py` | Balance |
| `engine/privacy.py`, `engine/nicrron.py`, `engine/reader.py`, `tests/test_privacy.py`, `tests/test_reader.py` | Reader |
| `engine/prism.py`, `tests/test_prism.py`, `docs/PRISM_SETUP.md` | PRISM |
| `engine/claims.py`, `tests/test_claims.py` | Claims |
| `web/index.html`, `web/app.js`, `web/style.css` | Screen |
| `tests/acceptance/answer_sheet.csv`, `tests/acceptance/run_acceptance.py`, `tests/acceptance/README.md` | Acceptance |
| `engine/similarity.py`, `tests/test_similarity.py`, `docs/closeness_check.json`, `tools/sync_fixture.py`, `docs/req/` | Closeness (added 2026-10-10 afternoon) |

## Shared helpers already written: `engine/colleges.py`
`load_colleges() -> list[College]`, `find_college(name_or_id) -> College | None`, `case_name_for(college) -> str | None`
(the short name used in the self-reported file), `act_to_sat(act) -> int | None`.

**College** (dict): `id, name, city, state, control ("public"/"private"), admit_rate (0..1 or None), sat25, sat75
(total SAT, or None), act25, act75, undergrads, cost_year (sticker cost of attendance, dollars), tuition_in,
tuition_out, pell_share, grad_rate, url, source, net_price` (average net price after grants for the college's sector, or
None), `net_price_by_income` ({"0-30k","30-48k","48-75k","75-110k","110k+"} -> dollars or None), `median_debt` (median
debt at graduation or None), `loan_share` (share of students with federal loans, 0..1, or None). Data: `data/colleges/
scorecard_colleges.csv` (built by `tools/build_college_file.py`), else the two older files. `colleges.cost_sentence(college,
home_state=None, income_band=None) -> str | None` is the one place cost wording is written.

## Input: StudentInput (dict)
```json
{"label": "Student A (SYNTHETIC)", "sat": 1450, "act": null, "gpa": 3.9, "gpa_scale": 4.0, "home_state": "NJ",
 "intended_major": "Computer Science", "hooks": ["first_gen"],
 "activities": [{"type": "Research", "role": "Student researcher", "description": "..."}],
 "essay": "full text or empty string", "college_list": ["Cornell University", "Purdue University-Main Campus"]}
```
Any field except `college_list` may be null or missing. `hooks` values: `first_gen`, `legacy`, `urm`,
`recruited_athlete`, `none`. Optional, used only by Closeness: `activities_rating` (0 to 10, the counselor's own
rating) and `major_interests` (a list of majors the student named).

## Output: Result (dict). This is the only thing the screen reads.
The full example is `docs/fixture_result.json`. Top-level keys:
`run_id, generated_at, synthetic, student, steps, privacy, reader, colleges, balance, checks, prism, refusals,
closeness_check, closeness_method` (the last two are the Closeness holds-up table from `docs/closeness_check.json`,
or null, and `similarity.method()`: the weights, spans and thresholds the About page shows, read from the code).

### `label` object: `labels.label_college(student, college_or_None) -> dict`
```json
{"state": "target", "text": "Target", "rule_id": "R4", "rule_text": "Score is inside the college's middle range.",
 "score_used": 1450, "score_kind": "SAT", "inputs": {"sat25": 1500, "sat75": 1570, "admit_rate": 0.0876},
 "not_used": ["GPA", "activities", "essay"], "caveats": ["The score range covers only students who sent scores."],
 "steady": false, "flips": [{"cause": "score 30 points lower", "to": "reach"}],
 "publishers": [{"name": "BigFuture", "label": "target"}], "publishers_disagree": true}
```
`state` is one of `outside_data, reach_for_everyone, cant_say, reach, target, likely`. First match wins:
1. **R0 outside_data:** the college is not in the 300-college file (`college is None`).
2. **R1 reach_for_everyone:** `admit_rate < 0.15`. Text: "Reach for everyone".
3. **R2 cant_say:** `admit_rate` is None; or the student has neither SAT nor ACT; or the college publishes no usable
   range for the score the student has. `rule_text` names which.
4. Score to compare: the student's SAT against `sat25/sat75` when both exist. Else the student's ACT against
   `act25/act75` when both exist. Else the student's ACT converted with `act_to_sat` against `sat25/sat75`
   (`score_kind` = "ACT converted to SAT"). A student with only SAT and a college with only an ACT range: cant_say.
5. **R3 reach:** score < 25th percentile. **R5 likely:** score >= 75th percentile and `admit_rate >= 0.40`.
   **R4 target:** everything else.
6. **Edge test:** recompute with the score 30 SAT points lower and higher (1 ACT point when comparing in ACT), and
   with `admit_rate` 5 percentage points lower. `steady` is true when nothing changes; otherwise list each change
   in `flips`. Skip the edge test for states R0, R1, R2 (`steady: true, flips: []`).
7. **Publishers:** run the five published rulebooks (see `data/colleges/rulebooks.json`; working code to port is in
   the team's research script) on the same score. `publishers_disagree` is true when any publisher
   that could label gives a different bucket from ours (treat our reach_for_everyone as reach).

### `cases` object: `cases.find_similar(student, college, tags=None) -> dict`
```json
{"needed": 15,
 "own": {"source": "Your school's own finished cases", "verified": true, "status": "not_enough", "n": 4,
         "admitted": 1, "denied": 3, "waitlisted": 0, "matched_on": ["SAT within 100 points"], "relaxed": [], "examples": []},
 "national": {"source": "Self-reported public posts (r/collegeresults)", "verified": false, "status": "ok", "n": 23,
         "admitted": 8, "denied": 12, "waitlisted": 3, "matched_on": ["SAT within 50 points", "same major group"],
         "relaxed": ["home state"], "examples": [{"case_id": "N-1042", "sat": 1460, "act": null, "major": "CS",
         "hooks": "NONE", "home_state": "CA", "activities_rating": 6.5, "outcome": "denied"}]},
 "official_admit_rate": 0.0876, "pool_admit_share_all": 0.251, "overcount": 2.9,
 "caveat": "People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."}
```
- Two pools, never merged: `own` (the counselor's school, from `caselog.load_cases()`; today these are SYNTHETIC)
  and `national` (the self-reported file in `data/cases/`).
- `status`: `ok` when n >= 15; `not_enough` when 1 <= n < 15; `none` when n == 0 or the college has no cases.
- Matching starts strict and relaxes in a fixed, documented order until n >= 15 or nothing is left to relax:
  SAT within 50 (ACT converted) + same major group + same hook status; then drop hook status; then drop major
  group; then widen SAT to within 100. Record what was dropped in `relaxed`. Never widen beyond 100 points.
- `tags` (from the essay reader) may supply `major_group` when the student did not state a major.
- `examples`: up to 6, closest first, and include at least one denial and one admit when both exist.
- `overcount` = the pool's admit share at this college (all its cases) divided by the official admit rate.
- **No probability, no "chance", no percentage of the similar set presented as a prediction.** Counts only.
- Case ids: `N-<applicant_id>` for national, `S-<n>` for the school's own.

`caselog`: `load_cases() -> list[dict]`, `add_case(case: dict) -> dict` (returns the stored case, or
`{"error": "..."}`), `import_csv(path) -> {"added": n, "rejected": [...]}`. A case holds: `case_id, cycle_year,
sat, act, gpa, major_group, hooks, home_state, activities_note, essay_theme, college (Scorecard name), outcome
(admitted/denied/waitlisted), verified_by ("counselor")`. It refuses any field that looks like a name, email, phone
or date of birth. Store: `data/local/school_cases.csv` (git-ignored), seeded from the SYNTHETIC file on first use.

### `closeness` object: `similarity.closeness(student, college, tags=None) -> dict` (Closeness, added in the afternoon)
On every college in `colleges`; `null` for a college outside the data. Requirements: `docs/req/REQUIREMENTS.md`.
```json
{"needed": 15, "neighbours": 7, "student": {"score": 1450, "converted": false, "activities": null},
 "national": {"source": "Self-reported public posts (r/collegeresults)", "verified": false, "status": "ok",
   "n_admitted": 184, "n_denied": 213, "n_waitlisted": 50,
   "d_admitted": 0.08, "d_denied": 0.039, "gap": -0.041, "lean": "closer_to_denied",
   "text": "Looks more like the people denied here than the people admitted.",
   "steady": false, "flips": [{"cause": "score 30 points higher", "to": "in_between"}],
   "parts": [{"part": "score", "distance": 0.05, "text": "close"}, {"part": "major", "distance": 0.0, "text": "close"}],
   "not_used": ["activities rating", "GPA", "residency (private college)", "essay", "activity descriptions"],
   "nearest_admitted": [{"case_id": "N-1296", "sat": 1450, "act": null, "major": "CS", "hooks": "FIRST-GEN", "home_state": "NY",
                         "activities_rating": 6.5, "outcome": "admitted", "distance": 0.0, "parts": {"score": 0.0, "major": 0.0, "hooks": 0.0}}],
   "nearest_denied": [],
   "kinds": [{"kind_id": "K1", "name": "Mid score, CS, activities 6.5", "size": 113, "median_sat": 1520, "median_activities": 6.5,
              "top_major": "CS", "medoid_case_id": "N-1042", "distance": 0.079, "nearest": true}],
   "changes": [{"change": "Score 100 points higher", "gap_before": -0.041, "gap_after": -0.004, "lean_after": "in_between", "because": ["N-88"]}],
   "changes_note": "",
   "points": [{"case_id": "N-1042", "sat": 1460, "activities": 6.5, "outcome": "denied", "kind_id": null}]},
 "own": {"source": "Your school's own finished cases", "verified": true, "status": "not_enough", "n_admitted": 1, "n_denied": 3, "n_waitlisted": 0,
         "d_admitted": 0.21, "d_denied": 0.3, "gap": 0.09, "lean": null, "text": "Not enough finished cases in one of the two groups to say which the student is closer to.",
         "steady": null, "flips": [], "parts": [], "not_used": [], "nearest_admitted": [], "nearest_denied": [], "kinds": [], "changes": [], "changes_note": "", "points": []},
 "caveat": "Closeness compares this student with people who chose to post their results. It is not a forecast."}
```
- A **distance**, never a probability: each part (score, activities rating, major group, hooks, residency at public
  colleges, GPA for the school's own cases) is 0 (same) to 1 (far); the total is a weighted mean over the parts both
  sides have (weights in `similarity.WEIGHTS`). Parts missing on either side are skipped and named in `not_used`.
- `d_admitted` / `d_denied`: mean distance to the 7 nearest admitted / denied cases with a score; `gap` is their
  difference; `lean` is `closer_to_admitted` when gap >= 0.03, `closer_to_denied` when gap <= -0.03, else
  `in_between`. `steady` / `flips` rerun with 5 and 10 neighbours and the score 30 points either way.
- `status`: `ok` (both groups 15 or more), `not_enough` (either group 1 to 14; counts and distances still shown,
  `lean` null), `none` (a group is empty or no cases), `cant_say` (no score). Two pools, never merged.
- `kinds`: three kinds of admitted student per college (k-medoids, seeded, national pool, 30 or more admitted),
  named only from counted facts; `[]` otherwise. `points` is capped at 300.
- `changes`: up to 3 of score +30/+60/+100, activities rating +1/+2, or another major the student named, kept only
  when the gap rises by 0.02 or more. Never hooks, home state, GPA, or anything about who the student is.
- The reach / target / likely label is untouched by any of this.

### `balance` object: `balance.assess(labelled, student) -> dict`
`labelled` is a list of `{"college": College | None, "name": str, "label": label}`.
```json
{"counts": {"reach": 4, "target": 1, "likely": 0, "cant_say": 1, "outside_data": 0},
 "warnings": [{"id": "no_likely", "text": "There is no likely college on this list."}],
 "suggestions": [{"id": "243780", "name": "Purdue University-Main Campus", "would_be": "likely", "admit_rate": 0.4995,
   "sat25": 1210, "sat75": 1470, "cost_year": 23000, "tuition_note": "In-state tuition applies",
   "why": "Score is at or above the 75th percentile and the college admits about half of applicants."}],
 "cost_notes": [{"name": "Cornell University", "text": "Sticker cost is about $88,000 a year. What this family would actually pay is not known here."}]}
```
`reach_for_everyone` counts as reach. Warnings (ids): `reach_heavy` (more than half the labelled list is reach),
`no_likely`, `no_target`, `prestige_pile` (4 or more colleges with admit rate under 15%), `short_list` (fewer than
5), `all_cant_say`. Suggestions come from the 300-college file using `labels.label_college` (import it lazily and
fall back to the same rule inline if the import fails): up to 3 that would be `likely` and up to 3 `target`, not
already on the list, admit rate 15% or higher, preferring the student's home state and larger graduation rates.
Cost is sticker price only; never claim what a family will pay.

### `privacy` and `reader`
`privacy.mask(text) -> {"text": masked, "masked": [{"kind": "email", "count": 1}], "blocked": false, "reason": ""}`.
Mask emails, phone numbers, street addresses, dates of birth, social security numbers, and names introduced by
"my name is" or similar, replacing each with a tag like `[NAME]`. `blocked` is true when the text contains
instructions aimed at an AI ("ignore previous instructions", "you are now", "system prompt", "label every college
as likely" and similar). Test with the five files `data/synthetic/SYNTHETIC_essay_*.txt`.

`nicrron.chat(messages, model=None, fallbacks=None, json_schema=None, max_tokens=900, timeout=40) ->
{"ok": bool, "text": str, "json": obj|None, "model": str, "request_id": str, "latency_ms": int, "error": str}`.
Gateway: `https://api.nicrron.ai/v1/chat/completions`, OpenAI-compatible, `Authorization: Bearer`. Key from env
`NICRRON_API_KEY`, else the file named by env `NICRRON_KEY_FILE`. No key: `ok: false, error: "no key"`; never raise.
Known traps, measured today: `anthropic/claude-sonnet-5` rejects `temperature: 0` (leave temperature out);
`openai/gpt-5.5` returns empty text when `max_tokens` is small (use 800 or more). JSON-schema output, tool calls,
streaming and a `models` fallback list all worked.

`reader.read(masked_essay, activities, intended_major=None) -> dict`:
```json
{"status": "ok", "model": "anthropic/claude-haiku-4-5", "second_model": "openai/gpt-5.5",
 "tags": {"major_group": "CS", "major_group_agreed": true, "activity_types": ["research", "music"], "essay_themes": ["family", "persistence"]},
 "notes": [{"observation": "...", "quote": "exact words from the essay", "question": "a question for the counselor to ask", "quote_found": true}],
 "dropped": 1, "latency_ms": 1800}
```
`status`: `ok, off (no key), blocked (privacy said so), empty (no essay), error`. Use a fast model for the first
read and a second model from a different maker to tag the major group independently; when the two disagree set
`major_group_agreed: false` and `major_group: null` (code then does not use it). **Quote check in code:** drop any
note whose `quote` is not found word for word in the masked essay (ignoring case and runs of spaces); count it in
`dropped`. Major groups: `CS, ENG, BIO, PREMED, BUSINESS, POLISCI, PSYCH, MATH, PHYSICS, ECON, HUMANITIES, ARTS, OTHER`.
The reader never labels a college and never rates the essay.

### `claims`: what the college itself says
`claims.college_says(college) -> list[dict]`, each
`{"claim_id": "c7_essay", "text": "Cornell rates the application essay Very Important.", "field": "CDS C7",
  "year": "2025-26", "source_url": "...", "numbers": [], "kb": null, "checked": true}`.
Source: `data/cds/cds_outcomes_sample.csv` (24 colleges; honour its sanity flags and skip flagged fields),
templates in `data/cds/claim_types.json`. A college with no row returns `[]`.
`claims.myth_checks(college) -> list[dict]`: for common beliefs (demonstrated interest counts, test scores are
required, the essay does not matter, legacy helps) say what this college's own form states, or "This college's
form does not say."
`claims.check_sentence(text, allowed_numbers, allowed_names, quotes=()) -> {"ok": bool, "reason": str}`: every
number and college name in `text` must be in the allowed sets; nothing from `data/cds/forbidden_phrases.txt`.

### `prism`
`prism.status() -> {"on": bool, "why": str}`; `prism.trace(agent_name, session_id, model, input_messages,
output_message, latency_ms, metadata=None) -> {"ok": bool, ...}`; `prism.screen(text) -> {"blocked": bool,
"how": "prism-proxy" | "off", "detail": str}`; `prism.kb_search(query, top_k=3) -> [{"text", "score", "doc"}]`;
`prism.kb_upload(path) -> {...}`; `prism.submit_steps(session_id, steps) -> {...}`; `prism.evaluation(...)`.
Key from env `PRISM_API_KEY`, else file named by `PRISM_KEY_FILE`. Project name from env `PRISM_PROJECT`.
`agent_name` on every call. **No key means every function returns an "off" result at once; PRISM never delays or
breaks a label.** A sending switch (`PRISM_SEND=1`) keeps recording off while developing: only 200 scored records
a day. Setup notes are in `docs/PRISM_SETUP.md`.

### `steps` (need 12): the visible trail
`[{"step": "retrieve", "what": "Looked up 6 colleges and 2,250 finished cases", "ms": 12, "by": "code"}, ...]`
in the order retrieve, score, bucket, explain, log. `by` is `code` or the model name.

## Server (Integration writes this)
`python server.py` serves `web/` at `http://localhost:8765/` and:
- `GET /api/students` -> the SYNTHETIC demo students
- `POST /api/run` with a StudentInput -> Result
- `GET /api/cases` and `POST /api/cases` (add a finished case)
- `GET /api/colleges?q=` -> name search over the 300
The screen must also work with no server by loading `docs/fixture_result.json` when opened with `?fixture=1`.
