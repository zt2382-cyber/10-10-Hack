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

- **339 automated tests,** none of which touch the network.
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
  cases). Its weights are starting values, not tuned. It is a resemblance, never a forecast.
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
