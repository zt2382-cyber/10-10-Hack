# Closeness: implementation plan (2 hours of coding)

Read `CONTRACT.md`, then `REQUIREMENTS.md` (the Closeness addition). Work on a branch off `alex`. Do the steps in
order; each has a check. Stop adding things at 1:40.

## Files

| File | Action |
|---|---|
| `engine/similarity.py` | new: all of R1 to R5 |
| `tests/test_similarity.py` | new |
| `engine/pipeline.py` | add about 10 lines: load the part, attach `closeness` per college, attach `closeness_check` |
| `web/app.js`, `web/style.css`, `web/index.html` | rings, mind map, fifth tab, one optional input |
| `docs/fixture_result.json` | regenerate, or add a `closeness` block by hand |
| `CONTRACT.md` | append the "Contract addition" section from REQUIREMENTS.md and a row in the owners table |
| `README.md` | three lines: what Closeness is, its limits |

Do not touch `labels.py`, `cases.py` (import from it only), `balance.py`, `claims.py`, `reader.py`, `prism.py`.

Three people can work in parallel after step 1: engine (steps 2 to 5), screen (steps 6 to 8 against the stub),
check and write-up (steps 9 to 10).

## Step 1. Stub and wire (0:00 to 0:15)

- `engine/similarity.py` with `closeness(student, college, tags=None) -> dict` returning a hard-coded block in the
  contract shape, plus `python -m engine.similarity` self-check that prints it.
- In `pipeline.run`: `similarity_mod = _part("similarity")`; inside the per-college loop
  `"closeness": _safe(similarity_mod.closeness, None, student, col, tags) if similarity_mod else None`; `None` for
  colleges outside the data.
- Add `closeness` to one college in `docs/fixture_result.json`.
- Check: `POST /api/run` returns `closeness` on every in-data college; all existing tests pass.

## Step 2. Distance (0:15 to 0:35)

- Rows: call `cases._national()` and `cases._own_rows(college)`; look at what each returns and adapt, do not
  re-read the CSVs. Build one normalised case dict per row: `case_id, score, activities, major_group, hooks,
  home_state, gpa, outcome`.
- `WEIGHTS` table and `part_distances(student_view, case, college) -> dict`, `total(parts) -> float | None`.
- Student view built once: score via `cases._score`, major group via `cases.major_group_for` or the reader tag,
  hook set via `cases._hooks_from_student`.
- Check (tests): distance to an identical case is 0; a 1500 student is nearer a 1480 case than a 1200 case;
  a missing part is skipped and the weights renormalise; no score gives `None`.

## Step 3. Two groups, lean, steady (0:35 to 0:55)

- `@lru_cache` `_groups(case_name)` -> admitted, denied, waitlisted lists of scored cases.
- `_nearest(student_view, group, k)` with a full sort (groups are under 1,000).
- `d_admitted`, `d_denied`, `gap`, `lean`, `status`, `parts`, `nearest_*`, `steady`, `flips`, `text`.
- All thresholds as named constants at the top: `NEIGHBOURS = 7`, `NEEDED = 15`, `LEAN_GAP = 0.03`.
- Before fixing `LEAN_GAP`, print the spread of `gap` for the six demo students across their lists. If nearly
  everything lands `in_between`, lower it; if nothing does, raise it. Write the chosen value and why in a comment.
- Check (tests): fewer than 15 in a group gives `not_enough` and `lean` None; no cases gives `none`; a student
  with a very high score at a mid-range college leans admitted; output contains none of "chance", "probab", "odds".

## Step 4. Changes (0:55 to 1:10)

- `_changes(student_view, groups, base_gap)` per R4. Reuse step 3's function; do not duplicate the maths.
- Check (tests): no change ever touches hooks, home state or GPA; at most 3; each has case ids.

## Step 5. Kinds (1:10 to 1:25)

- `@lru_cache` `_kinds(case_name)`: k-medoids, k = 3, `random.Random(20261010)`, cap 300 cases, 20 rounds.
  Distance between two cases uses the same parts (score, activities, major).
- Describe each kind with `statistics.median` and `collections.Counter`; build the name in code.
- Add `kind_id` to `points`.
- Check: same input gives the same kinds twice; under 30 admitted gives `[]`.
- If this runs past 1:25, ship `kinds: []` and move on.

## Step 6. Rings (screen, 0:15 to 0:50)

- `renderRings(result)` in Part 1 of `app.js` (pure, returns an SVG string), same conventions as `renderPicture`:
  `data-act="open-receipt"`, `data-i`, `tabindex="0"`, `role="button"`, an `aria-label` sentence per dot.
- Radius = 40 + 200 * min(d_admitted / 0.6, 1). Spread angles evenly, ordered by label then name. Three faint
  guide circles with no band meaning written on them (distance is not the label).
- Colleges with no `closeness`, or `status` other than `ok`: draw on an outer dashed ring labelled "not enough
  cases to place".
- A two-button toggle above the picture card: "Score ranges" (existing), "Rings", "Mind map".

## Step 7. Mind map (screen, 0:50 to 1:15)

- `renderMindMap(result)`: centre node, three branch nodes at fixed angles, college nodes fanned around each
  branch, then for the selected or hovered college its nearest kind and up to 3 nearest admitted case ids as leaf
  nodes. Straight lines, text labels, no physics.
- Keep it readable at 10 colleges; above 12, show leaves only for the pressed college.

## Step 8. Fifth tab (screen, 1:15 to 1:40)

- Add `['resemble', 'Who they resemble']` to `TABS`; `renderResembleTab(c)`:
  1. the lean sentence, the two counts, the caveat, and the steady or flips line;
  2. scatter from `points` (score across, activities up; circle = admitted, cross = denied; medoids ringed;
     student as a star; when the student has no `activities_rating`, draw a vertical line at their score instead);
  3. part bars from `parts`;
  4. `examplesTable(nearest_admitted)` and `examplesTable(nearest_denied)`;
  5. the changes list.
- One optional slider in the form, "Activities, your rating (0 to 10)" with a "none" toggle, sent as
  `activities_rating`. Follow the existing SAT slider markup.
- Every block must render nothing, not an error, when its data is missing.

## Step 9. Check table (1:25 to 1:40)

- `python -m engine.similarity --check` per R5; write `docs/closeness_check.json`; `pipeline.run` reads it if
  present and returns it as `closeness_check`; `renderHow` shows it as a small table of counts.

## Step 10. Freeze (1:40 to 2:00)

- Run all tests, the acceptance sheet, and each of the six demo students by hand.
- Regenerate the fixture and `python tools/make_static.py --zip`.
- Append the contract addition to `CONTRACT.md`; three lines in `README.md`, including: closeness uses score,
  activities rating, major group, hooks and residency only; it does not read the essay or activity text.

## If behind, cut in this order

Step 9, then kinds (step 5), then the mind map's leaf nodes, then the scatter (keep the bars and tables).
Keep: the lean sentence with counts, nearest admitted and denied cases, changes, rings.
