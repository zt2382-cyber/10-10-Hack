# Counselor Copilot

**We turn a student's college list into a checkable reach, target and likely picture grounded in real outcomes,
and we flag what we do not know.**

Counselor Copilot is a meeting tool for college counselors. You load a student and their list, and it labels each
school reach, target or likely using the college's published admit rate and score band, then shows what happened to
similar finished cases. It never invents a personal chance of admission. If the evidence is thin, the list has no
likely school, or a result comes from a biased public pool, it says so. Essays are read only for themes after
personal details are masked, and an essay never moves a label. A counselor can check every claim against the case
counts and the Common Data Set in the room, without a walkthrough.

Built in one day at the Get Hired Hack (Columbia Startup Lab, October 10, 2026) for the track *The Counselor
Copilot*. Theme: "AI You Can Trust."

**Demo video:** [docs/video/counselor_copilot_demo.mp4](docs/video/counselor_copilot_demo.mp4)

| | |
|---|---|
| ![Who you are: the student's own words come first](docs/screens/1_who_you_are.jpg) | ![Where you stand: each college as a distance from the student's score](docs/screens/2_where_you_stand.jpg) |
| ![What is in your hands: the list, the score, what colleges look for](docs/screens/3_in_your_hands.jpg) | ![Your plan: five things to do this month](docs/screens/4_your_plan.jpg) |

## What a counselor sees

One story in four chapters, each ending in one obvious next step.

1. **Who you are.** What stands out in the student: their activities, the themes of their essay, and two
   sentences in their own words.
2. **Where you stand.** One picture of the whole list. The student is a line; each college is a bar showing where
   the middle half of its students scored, with the distance written on it ("70 points above your score") and a
   reach, target or likely label. The same list can be viewed as rings or as a map.
3. **What is in your hands.** Colleges that would balance the list, a "what if the score were..." slider that
   re-labels the list as it moves, and what each college says it looks for beside what is in the profile.
4. **Your plan.** Five things to do this month, a sheet to print for the family, and a status for each college.
   When a result comes in, it becomes a finished case for next year's students, with no names.

Pressing a college opens the detail:

- **How we got this:** the rule and the published numbers behind the label.
- **Who you resemble:** whether the student sits closer to the people admitted there or the people who were not,
  part by part, beside the nearest cases of each. The counselor's own school and public posts are kept apart.
- **What could change it,** and **what the college says** in its own Common Data Set.

One switch, **Show the working**, reveals every source, rule, check and step for the counselor or anyone
auditing the result.

## Why there is no percentage

Public outcome data comes from people who chose to post their results. We measured it: across the colleges in
that data, posters reported being admitted a median of about 2.8 times as often as applicants really are. A tool
that turned that pool into "your chance" would be telling a hopeful family something untrue.

So the product holds to three rules:

- **Code sets every label, count and number. A model only reads.** The single model call reads the essay and
  returns themes and notes. Each note must carry a word-for-word quote, and code drops any note whose quote is not
  in the essay.
- **"Not sure" is a normal answer.** "Can't say" when a college publishes no score range. "Too few cases to say
  anything yet" under 15 cases. "Outside our data" for a college not in the file. "This one is close" when 30
  points would change a label.
- **Cases are shown as cases.** Counts of admitted, not admitted and waitlisted, always with how many, always
  beside the official admit rate, and always with a note on who posts.

## How it works

```mermaid
flowchart LR
  S[Student and college list] --> P[Privacy screen]
  P --> R[Essay reader]
  S --> L[Label rule]
  F[(College facts)] --> L
  C[(Finished cases)] --> M[Similar cases and closeness]
  S --> M
  R --> M
  L --> B[List balance and levers]
  M --> U[Counselor's screen]
  B --> U
  R --> U
  P -. guardrail .-> X[PRISM]
  F -. statements checked .-> X
  U -. run record .-> X
```

| Part | What it does | Where |
|---|---|---|
| Label rule | Reach, target or likely from the college's admit rate and score band; re-run at 30 points either way to say when a label is close | `engine/labels.py` |
| Similar cases | Finished cases like this student, counted by a written rule, in two pools that are never merged | `engine/cases.py`, `engine/caselog.py` |
| Closeness | How much the student resembles the admitted and the not-admitted group at each college, part by part, with a check of how that held up on 400 past cases | `engine/similarity.py`, `docs/req/` |
| Applicant evidence | A store for applicant records with provenance and consent, intake from messy files, and a weighted similarity score that reports how much of a profile could be compared. Its scorer orders the example cases | `admissions/`, `engine/evidence_adapter.py` |
| List balance and levers | Warnings for a lopsided list, suggested colleges, the score at which each label changes, what each college says it reads | `engine/balance.py`, `engine/pipeline.py` |
| Privacy screen | Masks names, addresses, phone numbers and schools; stops text written to steer an AI; if the check cannot run, the essay is not read | `engine/privacy.py` |
| Essay reader | Themes and quoted notes from the masked essay, through the Nicrron gateway | `engine/reader.py`, `engine/nicrron.py` |
| College statements | What each college says it weighs, with a source for every sentence | `engine/claims.py` |
| Record and checks | Guardrail, knowledge-base check and run record through PRISM | `engine/prism.py` |
| Screen | Plain HTML, CSS and JavaScript with inline SVG; no framework and no build step | `web/` |

The shape of the result every part reads and writes is in [`CONTRACT.md`](CONTRACT.md).

### What it does, feature by feature
<!-- FEATURES_START -->
Generated from `docs/features.json` by `tools/sync_features.py`; the About page shows the same list. 30 of 33 work today.

| Feature | What it does | Where | Status |
|---|---|---|---|
| **One story in four chapters** | Who you are, where you stand, what is in your hands, your plan. Each chapter ends in one obvious next step; a waypoint bar tracks where the reader is. | The whole screen after "Show where they stand". | Works |
| **Reach / target / likely label** | Each college gets a label from a written rule in code, from its published admit rate and middle score range. Never from a model. | Chapter 2; tap a college, "How we got this". | Works |
| **This one is close, and publishers disagree** | Every label is rerun with the score 30 points either way and the admit rate 5 points lower; a label that flips is marked. Five published rulebooks are run on the same score and any disagreement is shown. | Chapter 2 and "How we got this". | Works |
| **Where you stand: the trail map** | Every college's middle score band on one line, the distance to the student's score written on each bar, and a label beside it. | Chapter 2. | Works |
| **Example cases, two pools kept apart** | Counts of admitted, not admitted and waitlisted among finished cases like this student, with n and the official admit rate beside them. The school's own cases and the public self-reported pool are never added together, and the public pool's over-count is stated. | Tap a college, "Who you resemble". | Works |
| **Who you resemble: closer to the admitted or the not admitted** | Per college, the distance from the student to the 7 nearest admitted and the 7 nearest not-admitted cases, over score, activities rating, major group, hooks and residency. A lean, a steady test, the parts that are close or far, and the nearest cases of each. A distance, never a percentage; the label is untouched. | Tap a college, "Who you resemble". | Works |
| **Rings picture** | The student at the centre, one dot per college as far out as the student is from the people admitted there. Hollow when there are too few cases; on an outer ring when it cannot be placed. | Chapter 2, "Other pictures: Rings". | Works |
| **Map picture** | The student in the middle, a branch per label, a node per college, and under each college its nearest kind of admitted student (only when the kinds pass their check) and its three nearest admitted cases. | Chapter 2, "Other pictures: Map". | Works |
| **Clusters picture** | For one college, a 3 by 3 grid of rule-defined clusters of past applicants (score below, inside or above the published range; activities rating low, middle or high), each with its real finished cases as dots and counts, and the student's own cluster outlined. A cluster grows when pressed and lists its cases. Beside it, a three-number check on the computer-made kinds; kind names appear anywhere on the screen only when that check passes. | Chapter 2, "Other pictures: Clusters". | Works |
| **Scatter, part bars, kinds and changes** | A scatter of that college's cases by score and activities rating with the student as a star and the three kinds' medoids ringed; a bar per part; three kinds of admitted student found by k-medoids and named from counts, shown only when they pass a separation, shuffle and stability check; and what would bring the student closer (score, activities, a named major; never hooks, home state or GPA). | Tap a college, "Who you resemble". | Works |
| **Essay and activity text in closeness** | With a model key, masked essay and activity text are embedded and become two more parts of the distance, compared only where both profiles have text. Vectors stay in memory. Without a key the structured parts carry the comparison. | Tap a college, "Who you resemble", with the working shown. | Works with a key |
| **Activities rating input** | A 0 to 10 dial for the counselor's own rating of the student's activities, used only by closeness. | Counselor tools, "Change the details". | Works |
| **What the college says it weighs** | Statements from each college's own Common Data Set form, each with its field, year and source link, checked in code and confirmed against a knowledge base. Common beliefs are checked against the form. | Tap a college, "What the college says". | Works |
| **What the college looks for, beside the profile** | For each factor the college says it reads, whether it is in this profile, not yet, or cannot be seen here. Three neutral states and no total: it is not a score. | Chapter 3. | Works |
| **List balance and suggested fills** | Warnings when a list is reach-heavy, has no likely or no target, piles onto very selective colleges, or is short. Suggested colleges that would be likely or target, preferring the home state. | Chapter 2 headline and caution; chapter 3. | Works |
| **"What if the score were…" slider** | Moves the student's score and re-labels the whole list as it moves, saying which colleges change at which score. Labels only; nothing else is re-run. | Chapter 3. | Works |
| **Cost: sticker price and what families paid** | The published sticker cost beside the federal average paid after grants, by income band when given. One family's price can differ, and the screen says so. | Chapter 3 and each college. | Works |
| **Your plan, and a sheet to print** | Five things to do this month from the list and its gaps, and a one-page print layout for the family in plain words. | Chapter 4. | Works |
| **Keep track, and pay it forward** | A status for each college (considering, applying, submitted, result). When a result comes in it becomes a finished case for next year's students, with no names. | Chapter 4. | Works |
| **Essay notes with quotes, after masking** | Names, addresses, phones and dates are masked, then one model reads the essay and returns observations with word-for-word quotes; code drops any note whose quote is not in the essay. A second model tags the major independently. An essay with instructions aimed at an AI is stopped twice. | Chapter 1; Counselor tools, "Questions to ask". | Works with a key |
| **Show the working** | One switch reveals every source, rule, check and step behind the screen: the five steps, what code did and what a model did, sentences hidden by checks, the privacy record, and the closeness check table. | The switch in the header. | Works |
| **About, and How we worked this out** | A tour with live buttons; the parts and weights, the algorithm as a diagram, the libraries, the choices made, every data source with what was taken from it, and this feature list. Weights and thresholds are read from the engine, not typed into the page. | "About" in the header; Counselor tools, "How we worked this out". | Works |
| **Add a finished case** | A counselor records a finished case for the school's own pool. Anything that looks like a name, email, phone or date of birth is refused. | Counselor tools, "Add a finished case". | Works |
| **No personal chance of admission** | The screen never shows a percentage for the student. Asking why gets the measured over-count of the public pool and a pointer to the evidence instead. | "Why there is no percentage" in chapter 2; every count sits beside the official admit rate. | Works |
| **Holds-up check for closeness** | 400 past posters, each hidden in turn, their lean computed and their real outcome counted. Shown as counts with the caveat about self-reporting. | Show the working; python -m engine.similarity --check | Works |
| **Applicant-evidence package** | A store for applicant records with provenance and consent, intake from messy files, and a weighted similarity score that reports how much of a profile could be compared. Its scorer orders the example cases. | Behind the example cases; admissions/README.md | Works |
| **1,339 colleges from the federal file** | The full Scorecard institution file with cost and net price, and a "did you mean" for a college typed slightly wrong. | Everywhere a college is named. | Works |
| **Shared preview with no server** | Saved runs for the demo students, with the what-if scores, as plain files that open from a folder or a zip. | `python tools/make_static.py --zip` | Works |
| **Tests and the acceptance sheet** | Automated tests with no network, including one that fails if the fixture or this feature list drifts from its copies. 60 labels worked out by hand from the published rows, separately from the label code: 60 of 60 match. | `python -m unittest discover -s tests -t . ; python tests/acceptance/run_acceptance.py` | Works |
| **Parser for raw public posts** | Turns raw r/collegeresults posts into a wider pool (654 colleges in our run). Not wired in; its output stays out of the repository because it holds snippets of people's posts. |  | Thin |
| **PRISM Evaluator on the essay notes** | The run's score is read back in code instead. |  | Not done |
| **Several intended majors in the form** | Closeness can try another major the student named, but the form sends only one; the API accepts major_interests. |  | Not done |
| **Essay baseline search and activity text comparison** | A student draft searches a standalone reference bank using embeddings when available and local text similarity otherwise. Undergraduate samples are original synthetic essays; licensed graduate references come from OpenEssays with attribution. Missing applicant essay text is omitted from outcome comparisons. | Essay search in the header; input and similar references displayed side by side. | Works |
<!-- FEATURES_END -->

### Sponsor tools

- **Nicrron** carries the essay reader. One fast model reads the essay; a second model from a different maker
  independently tags the intended major, and code uses the tag only when the two agree.
- **PRISM by Block Convey** does three jobs. A guardrail on the essay: one screening call through PRISM's proxy,
  so an essay with hidden instructions is blocked before any model reads it. A Knowledge Base that every college
  statement is checked against: a false statement we planted came back "not confirmed". And a record of every
  model call and the five steps of each run (retrieve, score, bucket, explain, log). Setup notes:
  [`docs/PRISM_SETUP.md`](docs/PRISM_SETUP.md).

## Run it

Python 3.12 or later. Standard library only: nothing to install.

```bash
python server.py
```

Open http://localhost:8765/ and choose one of the nine invented demo students. With no keys set, everything works
except the essay reader.

Optional settings are read from environment variables. No key is stored in this repository.

| Variable | What it switches on |
|---|---|
| `NICRRON_API_KEY` or `NICRRON_KEY_FILE` | The essay reader |
| `PRISM_API_KEY` or `PRISM_KEY_FILE`, with `PRISM_PROJECT_ID` and `PRISM_SEND=1` | The run record, the knowledge-base check and the guardrail |
| `ANTHROPIC_API_KEY` or `ANTHROPIC_KEY_FILE` | The screening call through PRISM's proxy, which is what lets the guardrail block |
| `SIMILARITY_PLUGIN` or `SIMILARITY_URL` | A different similarity tool for ordering examples (see [`docs/INTEGRATING_A_TEAMMATE_TOOL.md`](docs/INTEGRATING_A_TEAMMATE_TOOL.md)) |
| `PORT` | The port (default 8765) |

To share the screen as plain files with no server behind it:

```bash
python tools/make_static.py --zip
```

That saves real runs for the demo students into `dist/`.

## How we know it is right

```bash
python -m unittest discover -s tests -t .
python tests/acceptance/run_acceptance.py
```

- **348 automated tests,** none of which touch the network, including one that fails if the embedded fixture or
  the feature list drifts from its source file.
- **60 of 60 on an independent answer sheet.** Sixty labels were worked out by hand from the published rows,
  separately from the label code (`tests/acceptance/`).
- **Whole-system checks** run with the answer sheet: no result contains the language of odds; a pool under 15
  cases is never called enough; labels do not change when the essay changes; an essay with a hidden instruction is
  stopped; personal details in an essay never appear in a result; the same input gives the same answer twice.
- **Outside review.** The code was attacked by reviewers from a different model family, and the screen was judged
  from screenshots by reviewers who had not seen the project. Their findings are fixed or listed below.

## Data

| Data | Real or invented | Source |
|---|---|---|
| 1,339 colleges: admit rates, score ranges, sticker cost, what families paid after grants | Real | US Department of Education, College Scorecard |
| What 24 colleges say they weigh | Real | Each college's Common Data Set, read through collegedata.fyi; fields that failed checks are skipped |
| Public case pool: about 2,250 applicants | Real, self-reported, not verified | Public r/collegeresults posts as compiled in the GitHub repository `shreybirmiwal/college-predictor`. That repository states no licence; the files are here for the demo and can be removed |
| The school's own cases | **Invented** by a seeded script, and labelled as invented on screen | `data/synthetic/SYNTHETIC_school_cases.csv` |
| Demo students and essays | **Invented,** stamped SYNTHETIC | `data/synthetic/` |

`tools/parse_reddit_posts.py` can turn raw public posts into a wider pool (654 colleges in our run). It is not
wired in, and its output is kept out of the repository because it holds snippets of people's posts.

### Clusters: rule-defined clusters of past applicants, and a check on the kinds

A fourth picture, **Clusters**, shows one college as a 3 by 3 grid: score below, inside or above the published middle
range, by activities rating low, middle or high. Each cell holds that college's real finished cases as dots with
counts, the student's own cell is outlined, and pressing a cell enlarges it and lists its cases. The rule is written
in code with no seed, so a counselor can recount it by hand (the result calls the block `groups`). Under the grid, three numbers check the computer-made
kinds of admitted student (how separate, the same on shuffled data, how stable on resampling); kind names appear
anywhere on the screen only when that check passes, which on the current file is almost nowhere.
Requirements: `docs/req/GROUPS_REQUIREMENTS.md`.

### Essay and activity text in closeness (optional, only with a key)

With a Nicrron key, a live run embeds the masked essay and activity text (`openai/text-embedding-3-small`,
through the existing gateway) and closeness gains two parts: essay content and activity descriptions, compared
only where both profiles have text (`engine/semantic.py`). The public pool has no full essays, so school cases
are compared on their brief `essay_theme` and `activities_note`, and the screen marks those as theme summaries.
Full historical essays can be joined to case ids through `data/cases/essay_corpus.json` (an array of
`{"case_id", "essay", "activities_note"}`); corpus text passes the same privacy mask and instruction check, and
blocked essays are excluded. Vectors stay in a bounded in-memory cache and are never written to disk or sent to the
browser. Without a key, or with `use_model=False`, the text parts are simply absent and the structured parts carry
the comparison. Text distance is not an essay quality score, and the labels never use it.

## Repository layout

```
engine/       the parts listed above, joined in pipeline.py
admissions/   the applicant-evidence package (its own README inside)
web/          the screen
server.py     the local server
tests/        unit tests and the acceptance sheet
tools/        scripts that build data files, the shareable copy, and the knowledge-base pages
data/         college facts, cases, college statements, invented demo data
docs/         the contract's example result, requirements for closeness, setup notes, the demo video
```

## Known limits

- Labels use test scores and admit rates only. The federal file has no GPA field, and the screen says so.
- Closeness uses score, activities rating, major group, hooks and home state (plus GPA for the school's own
  cases, and masked essay and activity text only when a model key is set). Its weights are starting values, not
  tuned. It is a resemblance, never a forecast.
- The public case pool skews toward high scorers, computer science and selective colleges. It is not a national
  sample, and the screen says so wherever it appears.
- The school's own cases are invented for the demo. Real, verified, de-identified cases are the right source.
- The applicant-evidence package's scorer is wired in; its database is not yet the product's store.
- College statements cover 24 of the 1,339 colleges.
- Cost shows the sticker price and the federal average of what families paid after grants. One family's price
  can differ.
- PRISM's Evaluator is not attached yet; the run's score is read back in code instead.
- Privacy masking is rule-based and was hardened after an outside review, but it is not a formal
  de-identification standard. Do not load real student records.

## What it does, feature by feature
<!-- FEATURES_START -->
Generated from `docs/features.json` by `tools/sync_features.py`; the About page shows the same list. 22 of 24 work today.

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
| **About, and How it was built** | A tour with live buttons; the parts and weights, the algorithm as a diagram, the libraries, the choices made, every data source with what was taken from it, and this feature list. Weights and thresholds are read from the engine, not typed into the page. | The two links in the header; the feature list is at the end of How it was built. | Works |
| **Tests and the acceptance sheet** | 216 unit tests with no network, including one that fails if the fixture or this feature list drifts from its copies. 60 labels worked out by hand from the published rows, by a builder who did not see the label code: 60 of 60 match. | `python -m unittest discover -s tests -t . ; python tests/acceptance/run_acceptance.py` | Works |
| **PRISM Evaluator on the essay notes** | The run's score is read back in code instead. |  | Not done |
| **Several intended majors in the form** | Closeness can try another major the student named, but the form sends only one; the API accepts major_interests. |  | Not done |
| **Essay baseline search and activity text comparison** | A student draft searches a standalone reference bank using embeddings when available and local text similarity otherwise. Undergraduate samples are original synthetic essays; licensed graduate references come from OpenEssays with attribution. Missing applicant essay text is omitted from outcome comparisons. | Essay search in the header; input and similar references displayed side by side. | Works |
<!-- FEATURES_END -->

## Essay retrieval and whole profile similarity

Live runs embed masked essay and activity text through the existing Nicrron gateway
(`openai/text-embedding-3-small`). The Cases panel shows nearest cases, comparison
fields and essay retrieval results. No additional dependencies are required.

Similarity combines test score, GPA, activities rating, major, hooks, public-college
residency, essay content and activity descriptions when both profiles have them.
Weights are declared in `engine/similarity.py` and renormalized over shared fields.
They are starting values, not fitted or validated admission predictors. A comparison
requires a shared academic, activity or text feature; demographics alone do not suffice.
Test scores are optional for similarity. The published-number college labels still
use their existing rules. Essay content distance is not an essay quality score.

The public dataset contains no full essays. School cases currently provide brief
`essay_theme` summaries and `activities_note` descriptions; retrieval marks summary
comparisons explicitly. To connect full historical essays, create
`data/cases/essay_corpus.json` as an array joined to existing case IDs:

```json
[
  {"case_id": "S-1", "essay": "Historical essay text", "activities_note": "Activity description"},
  {"case_id": "N-123", "essay": "Historical essay text"}
]
```

Only records for the selected colleges are embedded. Corpus text passes the same
local privacy mask and instruction check. Blocked essays are excluded. Vectors stay
in a bounded in-memory cache keyed by model and masked content hash, and are never
returned to the browser or written to disk. `use_model=False` disables embeddings.
Gateway failures omit missing vectors and expose an unavailable/partial status;
structured comparisons continue. Static demo fixtures do not perform live retrieval.

## Essay baseline search

Choose **Essay search** in the header, paste the student draft, choose undergraduate
or graduate essay type, and press **Find similar essays**. The draft stays beside
ranked references, with shared words, content similarity, full reference text, and
source/attribution links. The essay editor stays synchronized with the student form.
This search works independently of a college list or applicant outcome case IDs.

The starter bank contains four original synthetic undergraduate samples, explicitly
labelled as examples with no admission outcome. The OpenEssays bank contains 12
CC BY-NC-SA 4.0 graduate essays for noncommercial demonstration use; attribution,
original URLs and license links are retained. The local privacy check excludes
references containing model-directed instructions, so the searchable count can be
lower than the imported count. Unknown-license entries remain metadata-only in
`data/essays/openessays_catalogue.json`, including the undergraduate entries.

Refresh the imported bank with `python3 tools/import_openessays.py --limit 12`.
The importer makes public page requests; it never receives student drafts. These
licensed references are not an unrestricted commercial dataset. For commercial use,
replace them with material cleared for that use. No admission outcome is inferred
from an essay's school metadata.

Add your own permitted references in `data/essays/custom_bank.json`, an array:

```json
[{"id":"REF-1","title":"Community project","degree_level":"undergraduate",
  "essay_type":"Personal statement","text":"Full essay text...",
  "attribution":"Author credit","source_url":"https://example.com/essay",
  "license":"Permission granted","permission_confirmed":true,"synthetic":false}]
```

Only set `permission_confirmed` when reuse permission has actually been established.
Explicitly supported license identifiers are CC0, CC_BY_4_0 and CC_BY_NC_SA_4_0.
Drafts and references are masked before comparison, and blocked drafts never reach
an embedding service. Drafts are not persisted. With a configured Nicrron key,
retrieval reuses the process-local embedding cache. If the gateway fails or is not
configured, the entire ranking uses local TF-IDF cosine similarity, identified in
the UI as **local text similarity**. No embedding errors are shown in the results.
Local comparison finds shared words and may miss paraphrases; neither measure is an
essay grade or an admission prediction. `USE_MODEL=0` forces local comparison.

`POST /api/essay-search` accepts `essay`, `degree_level`, and optional `use_model`.
It returns matches and the actual comparison method, with no student draft or
vectors. Test with `python3 -m unittest tests.test_baseline`.
