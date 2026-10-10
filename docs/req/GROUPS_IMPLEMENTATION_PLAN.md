# Groups view: implementation plan (about 60 minutes)

Read `GROUPS_REQUIREMENTS.md` first. Work on `yuri`. Commit after each stage's check passes. Cut order is at the end.

## Files

| File | Change |
|---|---|
| `docs/req/groups_prototype.html` | add (reference only, not served) |
| `engine/similarity.py` | `_groups_grid`, `_kinds_check`, wire into `_pool`, extend `method()` |
| `tests/test_similarity.py` | new tests |
| `web/app.js` | `renderGroups`, toggle button, cell click, kinds gating |
| `web/style.css` | grid, dots, hatch (copy from the prototype's `<style>`; it already uses this app's tokens) |
| `docs/fixture_result.json`, `web/app.js` fixture block | regenerate, then `python tools/sync_fixture.py` |
| `CONTRACT.md`, `README.md` | append the contract addition; two lines in the README |

Do not touch `labels.py`, `cases.py`, `balance.py`, `claims.py`, `reader.py`, `prism.py`. `pipeline.py` needs no
change: `groups` and `kinds_check` ride inside the existing `closeness` block.

## Stage 1. Engine: the grid (15 min)

In `engine/similarity.py`:

- Constants `ACT_MID, ACT_HIGH, GROUP_MIN, GROUP_FEW, GROUPS_CAP = 900` beside the other thresholds.
- `_score_band(score, sat25, sat75)`, `_act_band(rating)`.
- `_groups_grid(sv, groups, college, own)`:
  - `groups` is what `_national_groups` / `_own_groups` already return (admitted, denied, waitlisted views). Check
    the exact shape of those views first; use the same score and activities fields `part_distances` reads.
  - return the contract block; nine cells in fixed order; `left_out` from cases missing score or rating.
  - `is_student` from `sv["score"]` and `sv["activities"]`; fill `student_note` when either is missing.
  - own pool or no published range: `status: "cant_say"` with the reason.
- In `_pool`, add `"groups": _groups_grid(...)`.
- Check (tests): nine cells always; a case at exactly `sat25` is `inside`; rating 6 is `mid`, 8 is `high`;
  n of 4 gives `not_enough`; UCLA (no range) gives `cant_say`; no activities rating gives no `is_student` and a
  note; cell counts add up to total cases minus `left_out`.

## Stage 2. Engine: the kinds check (15 min)

- `_silhouette(ids, label_of, dist)`: for each case, a = mean distance to its own kind, b = lowest mean distance
  to another kind, s = (b - a) / max(a, b); a kind of one scores 0; return the mean.
- `_jaccard(a, b)` on sets of case ids.
- `@lru_cache` `_kinds_check(case_name)`:
  - reuse the exact case sample and distance (`_kind_distance`) that `_kinds` uses; if `_kinds` does not expose
    its assignments, refactor it into `_kinds_fit(views, seed) -> (medoids, label_of)` and call that from both.
  - `separation` on the real fit; `shuffled`: shuffle each of `KIND_PARTS` across cases with
    `random.Random(KINDS_SEED)`, refit, silhouette; `stability`: 8 subsamples of 80% with seeds
    `KINDS_SEED + 1..8`, refit each, per original kind the best Jaccard against the refit (restricted to the
    subsample), mean per kind, report the minimum.
  - `verdict` and `text` per G4. Thresholds as named constants.
- Attach as `"kinds_check"` in `_pool`; null when `kinds` is empty.
- Run `python -m engine.similarity --spread` style loop once to print the verdict for all 58 colleges and note
  the tally in a comment. Expect mostly `none`.
- Check (tests): two well-separated synthetic blobs give `clear`; one uniform blob gives `none`; same input twice
  gives the same numbers; runs in under 2 seconds for a 300-case college.

## Stage 3. Screen: the view (20 min)

Port from the prototype's script; it is already written in this app's style (string-building pure functions).

- `renderGroups(result, state)` in Part 1 of `app.js`: college chips, column and row headers, nine cell buttons,
  legend, left-out line, caveat, then `renderKindsCheck(check)`.
- Dots are plain `<i>` elements in a flex-wrap box (see `.dots`, `.d` in the prototype), not SVG: they reflow at
  phone width for free.
- Major filter: recount cells in JS from `cases`, using `min_n` and `few_n` from the result.
- What-if slider: recompute the student's cell in JS from the slider score and `sat25`/`sat75`.
- Events through the existing `data-act` delegation: `data-act="groups-college"`, `"groups-cell"`.
- Add the fourth toggle button; hide it when no college has `closeness.national.groups`.
- Cases under the grid: reuse `examplesTable` if its row shape fits, else a small table like the prototype's.

## Stage 4. Gate the kinds everywhere (5 min)

- One helper `kindsShown(pool)` returning `clear`, `loose` or `none` from `kinds_check.verdict` (treat a missing
  check as `none`).
- Use it in the drill-in tab, the mind-map leaves and the scatter medoid rings: `none` hides names and shows the
  verdict text; `loose` adds "loose grouping".

## Stage 5. Freeze (5 min)

- All tests, acceptance sheet, six demo students by hand, one with an activities rating set.
- Regenerate the fixture, `python tools/sync_fixture.py`, `python tools/make_static.py --zip`.
- Contract addition into `CONTRACT.md`; README: what Groups shows, and that kinds are shown only when they pass
  the check.

## If behind, cut in this order

Major filter, then the own-pool grid (leave it `cant_say`), then Stage 4's mind-map and scatter gating (keep the
drill-in), then the `shuffled` number (verdict from the other two, say so on screen).
Keep: the grid with counts and the student's cell, the caveat, and the verdict sentence.
