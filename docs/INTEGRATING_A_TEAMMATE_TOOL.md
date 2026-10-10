# Plugging a teammate's tool into Counselor Copilot

Written 1:35 PM, October 10. The quickest path for each kind of tool, so nothing has to be rewritten.

## A similarity checker (deciding which past students are "like this one")

There is one seam, `engine/similarity_plugin.py`. Connect a tool in either way:

| Your tool is | Set this before starting the server | What we send | What we need back |
|---|---|---|---|
| A Python function | `SIMILARITY_PLUGIN="your_module:your_function"` (the module must be importable from the repo root) | `(student, cases, college)` | a dict, see below |
| Anything else (Node, a notebook, a service) | `SIMILARITY_URL="http://localhost:9000/rank"` | `POST` JSON `{"student": {...}, "college": {...}, "cases": [...]}` | the same dict as JSON, within 3 seconds |

**What you receive**
- `student`: `sat`, `act`, `gpa`, `home_state`, `intended_major`, `hooks`, `activities` (already masked), and
  `major_group` when known. No essay text and no name, ever.
- `college`: `id`, `name`, `state`, `control`, `admit_rate`, `sat25`, `sat75`.
- `cases`: a list of finished cases at that college, each with `case_id`, `sat`, `act`, `major`, `hooks`,
  `home_state`, `outcome` (admitted / denied / waitlisted). Cases from the school's own pool also carry
  `activities_note` and `essay_theme`.

**What you return**
```json
{"ranked": [{"case_id": "N-1042", "score": 0.91, "reasons": ["same major group", "score within 20 points"], "similar": true}],
 "rule": "one plain sentence saying how similarity was judged"}
```
- `score` is 0 to 1, higher means more alike. It is a similarity, never a chance of admission.
- `reasons` are short plain phrases shown to the counselor. Anything mentioning chance, odds, probability or a
  percentage is dropped.
- `similar` is only read in filter mode (below).

**Two modes** (`SIMILARITY_MODE`):
- `rank` (default): our written rule still decides which cases count and how many there are. Your tool orders the
  examples and supplies the "why similar" reasons. Safe to turn on at any time.
- `filter`: your tool decides which cases are similar. The count `n` then follows your tool, and your `rule`
  sentence is shown on screen in place of ours. The "not enough cases: fewer than 15" rule still applies.

**It cannot break a run.** If the plug-in is missing, slow, throws, or returns something malformed, the built-in
matching is used and the result says why. There is a working example to copy: `example_plugin` in
`engine/similarity_plugin.py`. Try it with `SIMILARITY_PLUGIN="engine.similarity_plugin:example_plugin"`.

**Ground rules that keep the product honest** (the judges test these)
1. Same input, same output. No randomness.
2. No network calls with student data unless it has been through `engine/privacy.py`.
3. Never output a probability or a percentage for the student.
4. Say plainly when you cannot tell. Returning fewer cases is fine.

## Any other tool
- **New data about colleges**: add a loader beside `engine/colleges.py` and a claim builder like `engine/claims.py`;
  every statement needs a source and passes `claims.check_sentence`.
- **A new step in the run**: `engine/pipeline.py` is the only place steps are joined. Each part is imported with
  `_part("name")` and may be absent; follow that pattern so a missing part turns into a plain note, not a crash.
- **A new panel on the screen**: the screen reads one JSON result. Add your field to the result in the pipeline,
  then render it in `web/app.js` (escape everything with the existing helper before it reaches the page).
- **Tests**: `python -m unittest discover -s tests -t .` and `python tests/acceptance/run_acceptance.py` must stay
  green. Add a `tests/test_<yourpart>.py`.

The shape of the result and of every part is in `CONTRACT.md`.
