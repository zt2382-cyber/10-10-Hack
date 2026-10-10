# Closeness: staged implementation plan

Source: `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md` (this folder), checked against the code on branch `yuri`
(same as `origin/alex`, commit `285faf3`). This file orders the work into stages, each with an exit check, and lists
the gaps found in the source documents.

Baseline before any change: `python -m unittest discover -s tests -t .` gives 177 tests passing;
`python tests/acceptance/run_acceptance.py` gives 60/60. Every stage must end with both still green.

## What the code check found (things the plan does not say)

| # | Finding | Effect on the plan |
|---|---|---|
| 1 | `cases._own_rows()` drops `gpa` and sets `rating: None`. | The GPA part (R1) cannot come from `_own_rows`. `cases.py` is read-only, so `similarity.py` joins `caselog.load_cases()` on `case_id` to get `gpa`. |
| 2 | `cases._national()` returns a tuple `(by_college, n_applicants, n_decisions, n_pairs)`. Rows already have `score`, `rating`, `group`, `hooks_set`, `home_state`, `outcome`. | Stage 2 needs no new parsing. It maps these field names to the R1 parts. |
| 3 | `home_state` is `None` on 1,625 national rows. | Residency is skipped for those rows (per-row renormalising, not a hard drop). |
| 4 | 49 of 58 colleges have at least 15 scored admitted and 15 scored denied cases. 54 have at least 30 scored admitted. Claremont McKenna (10 admitted), UCM (3 denied) and a few others fall short. | `ok` is the common case. Test `not_enough` against Claremont McKenna and UCM. |
| 5 | The own (SYNTHETIC) pool is a few cases per college. | Expect `own.status` to be `not_enough` or `none` almost always. The screen must look right in that case. |
| 6 | No student has `activities_rating` yet, so for every demo student the activities part is skipped. | Until the slider exists, lean depends on score, major, hooks and residency only, with score at about 56% of the weight. Choose `LEAN_GAP` (step 3) with this in mind and again once the slider sends a value. |
| 7 | The local interpreter is Python 3.11.9; the contract says 3.12. | Use nothing that needs 3.12. Run the final check on 3.12 if possible. |
| 8 | `web/app.js` holds its own copy of the fixture between `/*FIXTURE_START*/` and `/*FIXTURE_END*/`, and no tool syncs it. | Updating the fixture means editing both `docs/fixture_result.json` and that block (write a short script in the freeze stage). |
| 9 | Colleges outside the data take a separate `out.append(...)` branch in `pipeline.run`. | Add `"closeness": None` there too, not only in the in-data branch. |

## Rulings (reviewed 2026-10-10; these override the source docs where they differ)

| Topic | Ruling |
|---|---|
| Who / order | One person, engine first (Stages 1 to 5), then screen (6 to 8), then check and freeze (9 to 10). The parallel tracks below become a sequence. |
| Budget | The 2-hour cut order applies. Keep: lean sentence with counts, nearest cases, changes, rings. Cut Stage 9 first, then kinds, then mind-map leaves, then the scatter. |
| Git | Commit on `yuri` when each stage's exit check passes; push to `origin/yuri` after each stage. |
| Python | Write for 3.11; nothing 3.12-only. |
| Kind names | "High score" when the medoid's median score is 40 or more above that college's admitted median, "Lower score" when 40 or more below, else "Mid score". Activities word the same way against the admitted median rating, with a 1.0 band. Major word is the most common group. E.g. "High score, CS, activities 7". |
| Residency at private colleges | Part skipped, and listed in `not_used` as "residency (private college)" so the counselor sees it was dropped. |
| Toggle | Three buttons above the picture card: Score ranges (default, unchanged), Rings, Mind map. |
| `major_interests` absent | Fall back to `[intended_major]`. One group means no major changes are tried. The reader's tag is not treated as a second interest. |
| Form | Activities slider only today; no `major_interests` input. |
| Fixture sync | New `tools/sync_fixture.py` copies `docs/fixture_result.json` into the `FIXTURE` block of `web/app.js`. |
| Own-pool weights | GPA adds 0.20, so weights sum to 1.20 and renormalise over the parts present, the same rule as for a missing part. |
| Steady test with no score | Not run: `status: cant_say`, `steady: null`, `flips: []`. |
| Group smaller than k | Mean over the cases present; status is already `not_enough`. |

## Stages

The track letters mark what could run in parallel with a team: **E** (engine), **S** (screen), **W** (check and write-up). Under the "Who / order" ruling they run in sequence, E then S then W.
Times assume the two-hour budget in the original plan.

### Stage 1: Stub and wire (all, 0:00 to 0:15)

- `engine/similarity.py`: `closeness(student, college, tags=None)` returns the contract example hard-coded.
  `python -m engine.similarity` prints it.
- `pipeline.run`: `similarity_mod = _part("similarity")`; in-data branch gets
  `"closeness": _safe(similarity_mod.closeness, None, student, col, tags) if similarity_mod else None`;
  outside-data branch gets `"closeness": None` (finding 9).
- Add the `closeness` block to one college in `docs/fixture_result.json` and in the `FIXTURE` copy in `app.js`.
- **Exit:** `POST /api/run` shows `closeness` on every in-data college; 177 + 60/60 green. Merge, then split tracks.

### Stage 2: Distance (E, 0:15 to 0:35)

- `WEIGHTS` table at the top. `_case_view(row, own_gpa)` maps rows from `_national()` and `_own_rows()`, plus GPA
  from `caselog` for own (finding 1).
- `_student_view(student, college, tags)`: score from `cases._score`, group from `major_group_for` or the agreed reader
  tag, hooks from `cases._hooks_from_student`, in-state flag only for `control == "public"`.
- `part_distances(sv, cv, college) -> dict`, `total(parts) -> float | None`.
- **Exit:** new `tests/test_similarity.py`: identical case gives 0; a 1500 student is nearer a 1480 case than a
  1200 case; a missing part is skipped and the weights renormalise; no score gives `None`; residency is ignored at
  a private college.

### Stage 3: Groups, lean, steady (E, 0:35 to 0:55)

- `@lru_cache _groups(case_name)`; `_nearest(sv, group, k)`; `_lean(gap)`; `_status(...)`; `parts`,
  `nearest_admitted/denied` (shape like `cases._example`), `text`.
- Steady test: k = 5 and 10, score -30 and +30, all going through one `_gap(sv, groups, k)` function.
- Constants: `NEIGHBOURS = 7`, `NEEDED = 15`, `LEAN_GAP = 0.03`. Print the spread of `gap` for the six
  `demo_students()` before fixing `LEAN_GAP`, and note the reason in a comment (finding 6).
- **Exit:** tests: Claremont McKenna gives `not_enough` and `lean` None; no cases gives `none`; a 1580 student at a
  mid-range college leans admitted; a forbidden-word scan of the whole block (`cases._FORBIDDEN`) is clean.
  Real `closeness` replaces the stub in the pipeline.

### Stage 4: Changes (E, 0:55 to 1:10)

- `_changes(sv, groups, base_gap)` per R4, reusing `_gap`. Fixed wording strings; nothing to change prints
  "Nothing we can measure here would move this."
- **Exit:** tests: never touches hooks, home state or GPA; at most 3; sorted by gain; every item has case ids;
  wording scan finds no "invent", "inflate" or forbidden words.

### Stage 5: Kinds (E, 1:10 to 1:25, first to cut)

- `@lru_cache _kinds(case_name)`: k-medoids, k = 3, `random.Random(20261010)`, at most 300 cases, at most 20 rounds.
  Distance uses score, activities and major. Names follow the "Kind names" ruling above. Add `kind_id` to `points` (capped at 300).
- **Exit:** same input gives the same kinds twice; under 30 admitted gives `[]`; 10 cold colleges add under 1 s
  in total (time it). If not done by 1:25, ship `kinds: []`.

### Stage 6: Rings and toggle (S, 0:15 to 0:50, against the stub)

- `renderRings(result)`: pure SVG string, same conventions as `renderPicture`
  (`data-act="open-receipt"`, `data-i`, `tabindex`, `role="button"`, an `aria-label` on each dot).
  r = 40 + 200 * min(d_admitted / 0.6, 1); a hollow dot for `not_enough`; colleges with no data go on an outer
  dashed ring, "not enough cases to place".
- Three-button toggle (see the "Toggle" ruling above).
- **Exit:** works with the stub fixture, with `?fixture=1`, and with `closeness` missing from every college.

### Stage 7: Mind map (S, 0:50 to 1:15)

- `renderMindMap(result)`: centre, then reach, target and likely branches at fixed angles, then colleges, then leaves
  (nearest kind and 3 nearest admitted) for the pressed college only once there are more than 12 colleges.
- **Exit:** readable at 10 colleges; every node has text.

### Stage 8: Fifth tab and input (S, 1:15 to 1:40)

- `TABS` gets `['resemble', 'Who they resemble']`. `renderResembleTab(c)`: lean sentence, counts, caveat and steady
  line; scatter (circle for admitted, cross for denied, medoids ringed, a star for the student, or a vertical line when
  there's no rating); part bars; two `examplesTable` calls; changes list.
- Form: an "Activities, your rating (0 to 10)" slider with a "none" toggle, sent as `activities_rating`. Copy the
  existing SAT slider markup.
- **Exit:** each block renders nothing when its data is missing; keyboard reaches every dot.

### Stage 9: Holds-up check (W, 1:25 to 1:40, first to cut)

- `python -m engine.similarity --check`: 400 seeded national decisions, leave-one-out, counts admitted and denied
  for each lean. Writes `docs/closeness_check.json`; `pipeline.run` reads it into `closeness_check`;
  `renderHow` shows the counts with the self-reported caveat.
- **Exit:** the file is deterministic (run twice and diff); no SYNTHETIC rows used.

### Stage 10: Freeze (all, 1:40 to 2:00)

- Full tests and the 60/60 acceptance sheet; each of the six demo students by hand; check timing against the
  baseline.
- Regenerate `docs/fixture_result.json` from a demo run and paste it into the `FIXTURE` block (finding 8);
  run `python tools/make_static.py --zip` and open the static build.
- Add the contract section to `CONTRACT.md`, along with a row in the owners table; add three lines to `README.md`
  covering what closeness uses and what it doesn't read.

## Cut order if behind

The original plan's cut order still holds: Stage 9 first, then Stage 5 (`kinds: []`), then the mind-map leaves, then
the scatter. Always keep the lean sentence with counts, the nearest admitted and denied cases, the changes, and the
rings.
