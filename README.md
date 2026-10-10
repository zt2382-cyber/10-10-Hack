# Counselor Copilot

Built on October 10, 2026 at the Get Hired Hack (Columbia Startup Lab), for the track **The Counselor Copilot**.
Theme: "AI You Can Trust."

A screen for a college counselor in a meeting with a family. Enter one student and the colleges under discussion.
It answers four questions:

1. **What do the published numbers say?** Each college gets a reach, target or likely label, set by a written rule
   in code, never by a model.
2. **What happened to students like this one?** Real finished cases (admitted, denied, waitlisted), with how many
   there are and where they came from. Two pools are kept apart: the counselor's own verified cases, and a national
   pool of self-reported results.
3. **What does the college itself say it weighs?** Statements from each college's own published form, each
   confirmed against a knowledge base.
4. **Is the list balanced, and what could change it?** Warnings when a list is lopsided, suggested fills beyond the
   usual very selective colleges, and a "what if the score were..." slider.
5. **Who does this student resemble?** Per college, whether the student sits closer to the people admitted there or
   the people denied, as a distance over score, activities rating, major group, hooks and residency only. Shown as
   rings and a mind map on the first view and a "Who they resemble" tab per college. It never reads the essay or
   the activity text, and it is not a forecast (`docs/req/REQUIREMENTS.md`).

It never gives a personal chance of admission.

![The first view: one picture of the whole list, three counters, and three levers](docs/screens/first_view.jpg)

![Opening a college: finished cases like this student, the school's own beside the national pool](docs/screens/cases.jpg)

## The product so far (1:10 PM, October 10)

**What a counselor sees.** Pick or enter a student and press "Build the list". The first view is deliberately
small: how many colleges are reach, target and likely; the single most important warning; and one picture, "Where
this student stands", with every college's middle score range on a shared line and the student's score drawn
through all of them. Beside it are three levers: the list itself (suggested colleges that would fill the gaps), a
"what if the score were..." slider that re-labels the list as it moves, and what each college says matters.
Pressing a college opens five tabs: why this label, cases like this student, who they resemble, what could change
it, and what the college says. A footer holds the essay notes, how the answer was made, a one-page sheet to print for the family,
and "What is the student's chance?", which explains why no percentage is given and points at the evidence instead.

**What works today.**
- End to end in about six seconds with the essay reader and PRISM switched on.
- 60 of 60 labels match a hand-worked answer sheet; 216 unit tests pass.
- The essay reader runs through Nicrron with two models from different makers.
- PRISM: the guardrail stops an essay with a hidden instruction; college statements come back "confirmed" from the
  Knowledge Base and a planted false one "not confirmed"; each run and its five steps are recorded.
- A version that needs no server (`tools/make_static.py`) for sharing a link.

**What is not done.**
- PRISM's Evaluator is not attached to the essay reader's output yet.
- The school's own "verified" cases are invented demo data; real ones would come from a counselor or from Nerd Apply.
- Matching on essays and activities is thin, because the public case file has no essay text.
- Nobody outside the builders has reviewed the print sheet, dark mode or phone width.

## What it does, feature by feature
<!-- FEATURES_START -->
Generated from `docs/features.json` by `tools/sync_features.py`; the About page shows the same list. 21 of 24 work today.

| Feature | What it does | Where | Status |
|---|---|---|---|
| **Reach / target / likely label** | Each college gets a label from a written rule in code, from its published admit rate and middle score range. Never from a model. | The counters on the first view; "Why this label" tab on each college, with the rule, its inputs and what was not used. | Works |
| **On the edge, and publishers disagree** | Every label is rerun with the score 30 points either way and the admit rate 5 points lower; a label that flips is marked. Five published rulebooks are run on the same score and any disagreement is shown. | "on the edge" under a college in the picture; the "Why this label" tab. | Works |
| **Cases like this student, two pools** | Counts of admitted, denied and waitlisted among finished cases like this student, with n, the matching rules used, examples, and the official admit rate beside them. The school's own verified cases and the national self-reported pool are never added together. | "Cases like this student" tab. | Works |
| **What the college says it weighs** | Statements from each college's own Common Data Set form, each with its field, year and source link, checked in code and confirmed against a knowledge base. Common beliefs are checked against the form. | "What the college says" tab; lever 3 on the first view. | Works |
| **List balance and suggested fills** | Warnings when a list is reach-heavy, has no likely or no target, piles onto very selective colleges, or is short. Up to six suggested colleges that would be likely or target, preferring the home state. | The one warning beside the counters; lever 1, "Show suggested colleges". | Works |
| **"What if the score were…" slider** | Moves the student's score and re-labels the whole list as it moves, with a ladder of which colleges change at which score. Labels only; nothing else is re-run. | Lever 2 on the first view. | Works |
| **Where this student stands** | One picture: every college's middle score range on a shared score line, the student's score drawn through them, admits-of-10 dots and case dots per college. | The first view, "Score ranges". | Works |
| **Essay notes with quotes, after masking** | Names, addresses, phones and dates are masked, then one model reads the essay and returns observations with word-for-word quotes; code drops any note whose quote is not in the essay. A second model tags the major independently. An essay with instructions aimed at an AI is stopped twice. | "Essay notes" in the footer; the stopped banner. | Works with a key |
| **How this was made: the five steps** | Retrieve, score, bucket, explain, log: what each step did, how long it took, and whether code or a model did it. Sentences hidden by checks are counted with the reason. | "How this was made" in the footer. | Works |
| **Add a finished case** | A counselor records a finished case for the school's own pool. Anything that looks like a name, email, phone or date of birth is refused. | "Add a finished case" in the footer. | Works |
| **One-page sheet for the family** | A print layout with the list by label, the balance warnings, suggested colleges, and the caveats, in plain words. | "Print for the family" in the footer. | Works |
| **No personal chance of admission** | The screen never shows a percentage for the student. Asking for one gets an explanation and a pointer to the evidence instead. | "What is the student's chance?" in the footer; every count sits beside the official admit rate. | Works |
| **Shared preview with no server** | Saved runs for the six demo students, with the what-if scores, as plain files that open from a folder or a zip. | `python tools/make_static.py --zip` | Works |
| **Closeness: admitted or denied, which does the student resemble?** | Per college, the distance from the student to the 7 nearest admitted and the 7 nearest denied cases, over score, activities rating, major group, hooks and residency. A lean, a steady test, the parts that are close or far, and the nearest cases. A distance, never a percentage; the label is untouched. | "Who they resemble" tab on each college. | Works |
| **Rings picture** | The student at the centre, one dot per college as far out as the student is from the people admitted there. Hollow when there are too few cases; on an outer ring when it cannot be placed. | The first view, "Rings". | Works |
| **Mind map picture** | The student in the middle, a branch per label, a node per college, and under each college its nearest kind of admitted student and its three nearest admitted cases. | The first view, "Mind map". | Works |
| **Scatter, part bars, kinds and changes** | A scatter of that college's cases by score and activities rating with the student as a star and the three kinds' medoids ringed; a bar per part; three kinds of admitted student found by k-medoids and named from counts; and what would bring the student closer (score, activities, a named major; never hooks, home state or GPA). | "Who they resemble" tab. | Works |
| **Activities rating input** | A 0 to 10 dial for the counselor's own rating of the student's activities, used only by closeness. | Edit details, "Activities, your rating". | Works |
| **Holds-up check for closeness** | 400 past posters, each hidden in turn, their lean computed and their real outcome counted. Shown as counts with the caveat about self-reporting. | "How this was made", bottom; python -m engine.similarity --check | Works |
| **About, and How it was built** | A tour with live buttons; the parts and weights, the algorithm as a diagram, the libraries, the choices made, and every data source with what was taken from it. Weights and thresholds are read from the engine, not typed into the page. | The two links in the header. | Works |
| **Tests and the acceptance sheet** | 216 unit tests with no network, including one that fails if the fixture or this feature list drifts from its copies. 60 labels worked out by hand from the published rows, by a builder who did not see the label code: 60 of 60 match. | `python -m unittest discover -s tests -t . ; python tests/acceptance/run_acceptance.py` | Works |
| **PRISM Evaluator on the essay notes** | The run's score is read back in code instead. |  | Not done |
| **Several intended majors in the form** | Closeness can try another major the student named, but the form sends only one; the API accepts major_interests. |  | Not done |
| **Matching on essay and activity text** | The public case file has no essay text, so essay themes only reorder the school's own cases and closeness never reads text. |  | Thin |
<!-- FEATURES_END -->

## How it handles accuracy and uncertainty

- **Code sets every label, count and number.** The only model call reads the essay and returns themes and notes.
  Every note must carry a word-for-word quote; code drops any note whose quote is not in the essay.
- **"Not sure" is a normal answer.** The screen says "Can't say" when a college publishes no score range, "Not
  enough cases: 4 of the 15 needed" when the sample is small, "Outside our data" for a college not in the file,
  "on the edge" when 30 points would change a label, and "publishers disagree" when published rulebooks differ.
- **No odds.** Counts of similar cases are shown as counts, beside the official admit rate. People who post their
  results are admitted far more often than applicants overall (we measured a median of about 2.8 times), so the
  screen shows that over-count and tells the reader to treat the cases as examples.
- **Privacy first.** Names, addresses, phone numbers and schools are masked before any model reads an essay. An
  essay containing instructions aimed at an AI is stopped twice: by our own check, and by PRISM's guardrail.
- **Checked by an independent answer sheet.** 60 labels worked out by hand from the published rows by a builder who
  did not see the label code: 60 of 60 match. Run it: `python tests/acceptance/run_acceptance.py`.

## Run it

Python 3.12, standard library only. No installs.

```bash
python server.py
```

Then open http://localhost:8765/ . Without any keys everything except the essay reader works.

Optional settings, all read from environment variables (no key is ever stored in this repository):

| Variable | What it switches on |
|---|---|
| `NICRRON_API_KEY` or `NICRRON_KEY_FILE` | The essay reader, through the Nicrron model gateway |
| `PRISM_API_KEY` or `PRISM_KEY_FILE`, plus `PRISM_PROJECT_ID` and `PRISM_SEND=1` | Recording each run in PRISM, the knowledge base check, and the guardrail |
| `ANTHROPIC_API_KEY` or `ANTHROPIC_KEY_FILE` | The one screening call through PRISM's proxy, which lets the guardrail block |
| `PORT` | The port (default 8765) |

Tests: `python -m unittest discover -s tests -t .` (216 tests, no network).

To share the screen as plain files with no server: `python tools/make_static.py --zip` saves real runs for the six
demo students into `dist/`.

## Sponsor tools

- **Nicrron** carries the essay reader: one fast model reads the essay; a second model from a different maker
  independently tags the intended major, and code uses the tag only when the two agree.
- **PRISM by Block Convey**: a guardrail on the essay (prompt injection, through PRISM's proxy); each college
  statement is confirmed against PRISM's Knowledge Base, and a false statement comes back "not confirmed"; every
  model call and the five steps of a run (retrieve, score, bucket, explain, log) are recorded. See
  `docs/PRISM_SETUP.md`.

## What is real and what is invented

| Data | Real or invented |
|---|---|
| 300 colleges: admit rates, score ranges, cost (`data/colleges/`) | Real. US Department of Education, College Scorecard. |
| What 24 colleges say they weigh (`data/cds/`, `data/kb/`) | Real. Each college's Common Data Set, read through collegedata.fyi; fields that failed checks are skipped. |
| National case pool (`data/cases/`) | Real, self-reported. Public r/collegeresults posts as compiled in the GitHub repository shreybirmiwal/college-predictor. No names. That repository states no licence; the files are included for the demo and can be removed. |
| The school's own cases (`data/synthetic/SYNTHETIC_school_cases.csv`) | **Invented**, generated by a seeded script. Stamped SYNTHETIC. |
| Demo students and essays (`data/synthetic/`) | **Invented.** Stamped SYNTHETIC. |

## Layout

`engine/` the parts (labels, cases, balance, privacy, reader, claims, prism, pipeline) · `web/` the screen ·
`server.py` the local server · `tests/` unit tests and the acceptance sheet · `CONTRACT.md` the data shape every
part agreed to before building · `docs/` setup notes and an example result.

## Known limits

- Labels use test scores and admit rates only. The federal file has no GPA field, and the screen says so.
- Similar-case matching uses score, major group and hook status. Essay themes only reorder the school's own cases.
- Closeness uses score, activities rating, major group, hooks and residency only (GPA for the school's own cases).
  Its weights are starting values, not tuned. `python -m engine.similarity --check` counts how its lean sorted 400
  past posters (`docs/closeness_check.json`); the table is shown under "How this was made".
- College statements cover 24 of the 300 colleges.
- Cost is the sticker price. What a family would pay is not known here.
- PRISM's Evaluator is not attached yet; the run's score is read back in code instead.
