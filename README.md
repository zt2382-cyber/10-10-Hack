# Applicant evidence prototype

A Python 3.11+ and SQLite prototype with a dependency-free structured retrieval core for importing application-time profiles and retrieving comparable past applicants with outcome provenance. All bundled examples are synthetic.

## Run

From this directory:

```sh
python3 -m admissions.cli --db /tmp/applicant-demo.db init
python3 -m admissions.cli --db /tmp/applicant-demo.db import examples/synthetic.json
python3 -m admissions.cli --db /tmp/applicant-demo.db search examples/query.json --college demo-university --cycle 2026 --round RD --program engineering --residency domestic --include-synthetic
python3 -m unittest discover -s tests -v
```

Import the example once into a fresh database. Duplicate IDs reject an import rather than overwrite historical records. Imports are transactional. Foreign keys enforce record relationships.

## Data contract

`examples/synthetic.json` is the canonical v1 import example. A bundle contains sources, snapshots, applications, and outcome events. Student records are created from snapshot IDs. Sources record consent, synthetic status, kind, and reference. Snapshots preserve the submitted profile and capture date. Outcome sources can differ from profile sources. IDs should be stable, pseudonymous identifiers; use canonical college and program IDs consistently.

GPA includes its original scale and explicit weighting. `sat_submitted` is the submitted SAT score, or null; an unavailable score and a deliberately withheld score require additional collection metadata before they can be distinguished. Rigor, activities, and interests currently use controlled string tags. Omitted/null fields are unknown. Empty tag lists provide no similarity evidence. Essays are stored in profiles and can be indexed for the separate `essay-search` command. They do not affect the structured `search` score.

Snapshot records are append-only through this CLI. Before importing real data, review consent, remove identifying information, and verify the profile reflects information available at application time. The prototype records consent assertions; it does not independently verify them or provide production access controls.

## Retrieval

The comparison pool uses the exact college, program, round, and residency and the three preceding cycles. It excludes the requested cycle and future cycles. Synthetic profile and outcome evidence is excluded by default. Pass `--exclude-student-id` when querying an existing student.

Similarity uses GPA (35%), submitted SAT (25%), rigor tags (20%), activity tags (15%), and interest tags (5%). GPA comparisons require matching scale and weighting. Tag similarity uses Jaccard overlap. Numeric distances and weights are provisional engineering heuristics, not empirically validated admission factors. Results expose each component and missing field.

The similarity score averages available components; coverage reports how much of the total feature weight is comparable. Ranking multiplies similarity by coverage so a sparse profile cannot receive a top rank based on a single matching field. Results include at most one application per student, ordered deterministically. Exact cohort matching may produce no results; this version does not silently broaden the pool.

Outcome events preserve waitlist/defer transitions and verification status. Missing outcomes remain unknown. Retrieval does not estimate admission probability or issue reach/target/likely labels: the category is explicitly `insufficient evidence` pending calibration with real data.

## Next development milestones

1. Collect a consented pilot cohort including unsuccessful and unknown outcomes; define collection and verification procedures.
2. Expand structured activities (duration, hours, role, achievement), course records, school context, test submission status, and field-level source evidence. Add college-cycle policy records.
3. Add document extraction into a staging format with source spans, confidence, contradiction checks, and human approval before canonical import.
4. Evaluate the new essay retrieval with counselor-reviewed examples; add structured themes and activity embeddings if they improve relevance.
5. Validate recommendations on later cycles with student-grouped splits, calibration, coverage reporting, and explicit abstention. Keep affordability as a separate requirement.

No external data has been downloaded. This repository is a local retrieval foundation, not a finished recommendation agent.

## Essay embeddings and retrieval

Install the optional local embedding dependency in a Python 3.11+ environment (the bundled system Python may be older):

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[essays]'
.venv/bin/python -m admissions.cli --db /tmp/applicant-demo.db index-essays --include-synthetic
.venv/bin/python -m admissions.cli --db /tmp/applicant-demo.db essay-search examples/query.json --college demo-university --cycle 2026 --round RD --program engineering --residency domestic --include-synthetic
```

Create and import the demo database using the commands above first. The first model load downloads `sentence-transformers/all-MiniLM-L6-v2`; subsequent inference runs locally and does not send essays to an embedding API. Synthetic evidence remains opt-in at both indexing and retrieval.

The index stores token-bounded overlapping passages, normalized embeddings, original text offsets, a SHA-256 content hash, and the model's resolved repository revision. Essays are not silently truncated to the model's input limit. Pass `--revision` with the same commit on both commands for reproducible runs. A changed essay must be reindexed. Models with different revisions are never compared. This implementation supports Sentence Transformers models with a fast tokenizer exposing character offsets and a resolved model repository revision.

Essay retrieval uses the same college/program/round/residency and historical-cycle filters. By default, candidates must have academic coverage and similarity of at least 0.5; configure `--min-academic-coverage` and `--min-academic-score` to change these provisional thresholds. All qualifying applications are considered, then results are deduplicated by student after essay ranking.

For each pair of essays, compute cosine similarities between their passages. The essay score averages the best historical match for each query passage and the best query match for each historical passage, giving both directions equal weight. Output includes the strongest passage pair with exact character offsets, alongside the separate academic score, sources, and outcome events. Passage scores provide content resemblance; they do not establish essay quality, factual truth, or admission probability. The historical field is still named `essay_draft`; prompt, submission status, and essay-specific provenance remain schema work.

Exact vector scanning is intended for a small pilot. A large corpus will need a vector index. Embeddings and passages contain sensitive derived content and currently share the database's access controls.

Validation: deterministic vector fixtures cover retrieval mechanics and do not establish model semantic quality. Installation/model inference could not be exercised in the development environment because package-registry networking was unavailable. Run the commands above and evaluate paraphrases and unrelated essays before relying on results.

References: [Sentence Transformers encoding](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html) and [semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html).

## Raw intake staging and review

The staging pipeline supports explicit labeled UTF-8 intake text, one-student CSV files, and essay text. It keeps original content and SHA-256 hashes in `documents`, extracted values and evidence in `field_candidates`, audit history in `review_events`, and published field links in `profile_evidence`. `intake_batches` groups multiple documents for one student. Database schema additions are created automatically by intake commands on existing databases.

Start a synthetic batch:

```sh
python3 -m admissions.cli --db /tmp/intake-demo.db stage examples/intake.txt --kind intake-text --student-id demo-student --synthetic --consent synthetic
```

The output contains a `batch_id` and candidate IDs. Substitute these in the following commands:

```sh
python3 -m admissions.cli --db /tmp/intake-demo.db stage examples/essay.txt --kind essay --student-id demo-student --synthetic --consent synthetic --batch-id BATCH_ID
python3 -m admissions.cli --db /tmp/intake-demo.db inspect-intake BATCH_ID
python3 -m admissions.cli --db /tmp/intake-demo.db review-field CANDIDATE_ID --status accepted --reviewer REVIEWER_ID
python3 -m admissions.cli --db /tmp/intake-demo.db publish-intake BATCH_ID --snapshot-id demo-reviewed-profile --captured-at 2024-11-01
```

Review each candidate individually, accepting supported values or rejecting invalid/unwanted candidates. All candidates must be reviewed before publication. Distinct unrejected values for the same field produce a conflict. To correct a value, reject the incorrect candidate and stage another document in the same batch; the original evidence and review history remain intact. Publication is transactional, creates an application-time profile snapshot, and locks the batch through the application API. Set `captured-at` to when the profile information was available, not automatically to today's processing date. An accepted field is human-reviewed, not independently verified.

Publication creates a profile only. Import an application referencing the published snapshot ID with the existing JSON importer to make it searchable; outcome sources and events can be added separately. Essay-only profiles can be published but will not satisfy the default academic retrieval thresholds.

The parser recognizes `gpa`, `sat_submitted`, `rigor`, `activities`, `interests`, and `essay_draft`. GPA must explicitly specify value, scale, and weighting (`3.8 / 4.0 unweighted`). Tags are semicolon-delimited, trimmed, lowercased, and deduplicated. Empty CSV cells are unknown. `sat_submitted` means a submitted score, not any reported SAT score. Unsupported text lines/columns are ignored; this parser does not infer facts from narrative. CSV evidence uses a data-row number and column name; text evidence uses original character offsets. A CSV document must contain exactly one student row and unique headers.

Real documents require `--consent granted` and must not use `--synthetic`. Consent is a recorded assertion, not an independent check. A batch cannot mix students or synthetic/real documents. The local database stores raw text and does not provide encryption, authentication, PII redaction, or deletion workflows yet. See the document extraction section below for PDF/OCR adapters and supported free-form patterns. Decision-letter interpretation and LLM extraction adapters remain future work.

## PDF and free-form extraction

Stage the included synthetic application text:

```sh
python3 -m admissions.cli --db /tmp/document-demo.db stage examples/application.txt --kind freeform --student-id demo-student --synthetic --consent synthetic
```

Install optional PDF support in a Python 3.11+ environment:

```sh
.venv/bin/python -m pip install -e '.[documents]'
.venv/bin/python -m admissions.cli --db applicants.db stage application.pdf --kind pdf --student-id STUDENT_ID --consent granted
```

The PDF adapter uses pypdf layout text extraction. Add `--ocr` to process pages containing fewer than 40 non-whitespace characters with local Tesseract; this requires `pdftoppm` (Poppler), `tesseract`, and English language data installed on PATH. OCR runs per page with 60-second subprocess limits. Sparse pages are flagged in inspection output. The sparse-text heuristic does not detect every partially scanned page, and OCR accuracy requires manual review. PDFs are not sent to external services.

Original bytes are stored in `document_assets`; the document hash covers those original bytes. Extracted page text, page numbers, methods, warnings, and document-wide character offsets are preserved. Candidate evidence refers to extracted text, not binary PDF offsets. Page references locate evidence in the original PDF. Text extraction may reorder complex layouts; no table/visual reconstruction is guaranteed. Text-only and OCR adapters require optional dependencies absent in the development environment; adapter behavior is covered using test doubles, not real PDF/OCR execution.

Current deterministic extraction recognizes:

- GPA declarations with an explicit scale and weighting. Missing weighting produces a blocked candidate rather than an inferred value.
- Explicitly submitted SAT scores and labeled intended major/interests.
- Activity entries such as `Activity: Robotics Club; role: Captain; 8 hours/week; 3 years; achievement: Regional finalist`.
- Limited narrative roles, such as `I served as volunteer at Community Tutoring; 2 hours per week; 6 months`.
- Course entries such as `Course: AP Calculus AB; grade: A-; term: 2024 Fall; credits: 1.0`.
- Four-column transcript rows separated by pipes, tabs, or multiple spaces: `2024 Fall | AP Physics 1 | B+ | 1.0`.
- Essay blocks beginning with `Personal statement:` or `Essay:` on their own line, ending at a recognized section heading or the end of the document.

All candidates enter the existing review workflow. Unsupported layouts are retained as documents even when extraction produces no candidates; add explicit correction inputs to the same batch. These rules cover a limited set of patterns, not arbitrary application PDFs or resumes. No LLM is currently used.

Profiles now accept `activity_records` (name, role, hours per week, duration, achievements, original description) and `courses` (name, original grade text, term, credits, level). Unknown details stay null. Arrays can also be supplied as JSON values in explicit intake fields or through the original JSON importer. Multiple different arrays in a batch are currently treated as competing field values, not automatically merged: reject alternatives and stage a consolidated correction when combining documents. Evidence for each extracted item remains in its candidate record.

The schema is backward compatible with existing profiles. Existing retrieval still uses activity tags and rigor tags; it does not yet score the new hours, roles, achievements, or course records. AP/IB prefixes are retained as levels, and original grades are preserved without conversion across grading systems.

References: [pypdf extraction limitations](https://pypdf.readthedocs.io/en/5.4.0/user/extract-text.html), [Tesseract command-line usage](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html).

## Reproducible synthetic applicant validation

`examples/pilot/student_application.txt` is a fuller designed applicant document, including an essay, transcript rows, detailed activities, missing activity hours, an ambiguous old GPA, and a negated score submission. It is fictional and can be freely used for development.

```sh
python3 -m scripts.validate_pilot
```

The runner checks authored expected values, source evidence, review/publication, and fictional outcome retrieval. Results are saved in `examples/pilot/validation_result.json`. See VALIDATION.md for omissions and unverified paths. The automated review in this runner applies only to the synthetic expected fixture; it is not a bulk approval workflow for real documents.

## Unified retrieval (recommended)

`retrieve` integrates the structured and essay signals into one ranking. The older `search` and `essay-search` commands remain available for diagnostics.

With the optional essay dependencies installed, import historical records, index their essays, then retrieve:

```sh
.venv/bin/python -m admissions.cli --db applicants.db index-essays
.venv/bin/python -m admissions.cli --db applicants.db retrieve query.json --college COLLEGE_ID --cycle 2026 --round RD --program engineering --residency domestic
```

To use a profile produced by document review without creating another JSON file:

```sh
.venv/bin/python -m admissions.cli --db applicants.db retrieve --snapshot-id SNAPSHOT_ID --college COLLEGE_ID --cycle 2026 --round RD --program engineering --residency domestic
```

Snapshot queries automatically exclude their student from historical matches. Synthetic records require `--include-synthetic` in both indexing and retrieval. Add the same pinned `--revision` to both commands for model reproducibility. Query files must contain a profile object, not an import bundle.

Default weights:

| Component | Weight | Evidence |
|---|---:|---|
| GPA | 20% | Same scale and weighting |
| Submitted SAT | 10% | Numeric distance |
| Courses | 20% | Course name overlap, comparable grades, level, credits |
| Activities | 25% | Name, role, hours, duration, achievement wording |
| Interests | 5% | Tag overlap |
| Essay | 20% | Symmetric passage embedding similarity |

Rich course and activity records use deterministic one-to-one alignment; unmatched records reduce similarity. Letter-grade distance is an explicit heuristic. Numeric grades require the same explicit denominator; different grading scales are not converted. Course terms are retained but not compared across calendar years. Activity descriptions are retained in source evidence; this version compares structured attributes rather than embedding descriptions. Name, role, and achievement wording comparisons are lexical, so synonyms can still be missed. Achievement similarity is not an achievement prestige/quality score.

When rich records are unavailable, rigor tags provide only 30% of the course component's evidence weight, and activity tags provide only 40% of the activity component's weight. Missing subfields reduce component coverage. Empty/unknown fields do not count as negative evidence. Unmatched records in known lists count as observed differences, subject to the lists' completeness.

An academic gate uses GPA, SAT, and courses before essay fusion: default academic evidence coverage is at least 0.25 of that group's weight and available academic similarity is at least 0.4. Configure `--min-academic-coverage` and `--min-academic-score` explicitly. Exact college, program, residency, round, and the three preceding-cycle filters remain in force; outcomes never affect ranking.

The result reports each component's similarity, coverage, weight, and contribution, aligned records, unmatched records, missing components, matching essay excerpts, field-level document evidence where available, and historical outcome events. Overall similarity averages available evidence; `rank_score` is similarity multiplied by total coverage. Thus complete and sparse records are not treated as equally supported. Positive essay cosine is used as resemblance; negative cosine contributes zero.

If the query has an essay, semantic scoring is enabled by default. Missing/stale/wrong-model embeddings for a qualifying historical essay stop retrieval with an indexing instruction. A missing historical essay reduces coverage and has an explicit status; it is never silently replaced with a keyword score. `--without-essays` provides an explicit structured-only mode, recorded in output warnings. Queries without essays similarly report their missing signal. No fallback embedding model is substituted.

Use `--weights weights.json` to supply all six positive component weights (normalized automatically). Defaults, gates, and record-distance formulas are provisional and versioned as `hybrid-v1`; counselor relevance judgments and real held-out applicants are still needed to tune them. Scores are not admission probabilities. Exact cohort/vector scanning targets a small pilot rather than a production-scale corpus.

Validation covers a strong all-around match, an equally strong applicant with a different essay, an academically weak applicant with matching essay content, missing evidence, duplicate students, stale/model-incompatible indexes, and independence from outcomes. Essay tests use authored vectors; actual model inference remains unverified in this environment.

## Source-separated outcomes and stability diagnostics

`retrieve` now returns `outcome_comparison` and `stability` in addition to the unified ranking. These are description layers; admission outcomes do not enter ranking or change component weights.

Optional source fields on JSON imports:

```json
{
  "id": "counselor-source-001",
  "kind": "counselor_export",
  "synthetic": false,
  "consent": "granted",
  "reference": "Consented counselor export, batch 001",
  "evidence_pool": "counselor",
  "verification_level": "counselor_reviewed"
}
```

`evidence_pool`: `self_reported`, `counselor`, `other`, or `unclassified`. `verification_level`: `self_reported`, `document_supported`, `counselor_reviewed`, or `unverified`. Omitted metadata and existing sources remain unclassified/unverified. These are assertions supplied by the importer, not independently verified credentials. Generic intake review does not automatically establish counselor ownership or verification. Source metadata is stored in an additive table, so existing databases and source records remain compatible.

Each evidence pool is further separated by profile/outcome verification tiers. Mixed profile and decision provenance is explicitly labeled (for example, `self_reported -> counselor`). A comparison is marked verified only when both profile and latest outcome have supporting verification tiers, the outcome event has its verification flag, and none of the evidence is synthetic. Synthetic profiles or latest synthetic outcomes always go into a synthetic, unverified pool regardless of asserted verification.

The latest dated event determines the outcome; timestamps are normalized to UTC, including naive dates assumed UTC. Contradictory decisions at the same latest instant are marked conflicting. Waitlist, defer, withdraw, unknown, and conflicting records are counted but excluded from the admitted/denied comparison. The full event history remains available. This rule does not infer an admission from an earlier event or combine different applications.

For each pool, the default compares the seven nearest admitted and seven nearest denied applicants using distance `1 - rank_score`, including the existing missing-evidence penalty. It reports counts, nearest examples, sources, excerpts, and per-component means with support counts. At least 15 unique students in **each** admitted/denied group are required for an outcome direction; otherwise the result is `not_enough` (both groups present) or `none` (a group absent). A distance gap of at least 0.03 determines a direction; smaller gaps are `in_between`. Counts use every academically eligible application, not only the top results displayed. Students are deduplicated within each provenance pool after similarity ranking. The 15-case rule and 0.03 gap are inherited starting heuristics, not validated statistical guarantees. No probability is produced, including when a pool's status is `ok`.

Diagnostics report ordered top-result changes, top-k set overlap, and outcome-direction/status changes under:

- Five and ten neighbours.
- Submitted SAT 30 points lower/higher, within valid bounds.
- Essay weight multiplied by 0.8 and 1.2 when essay scoring is active.
- Essay scoring excluded when essay scoring is active.

SAT and weight scenarios rerun the academic gate and ranking; neighbourhood scenarios reuse the ranking. Query embeddings are memoized per request, so these checks do not repeat model inference for the unchanged essay. A scenario that loses sufficient evidence is recorded, not hidden. An outcome direction's stability is null when no base pool has enough evidence. Stability describes selected perturbations, not forecasting accuracy or causal admissions advice.

Use `--no-diagnostics` for a single retrieval pass. `--neighbours` and `--needed-per-group` change comparison settings explicitly; their values are included in output. Defaults retain the 7/15 rules. There is no automatic cohort relaxation or cross-pool merging.

This change adapts the outcome-group comparison, evidence-pool separation, and sensitivity-check ideas reviewed in `docs/HACK_REUSE_REVIEW.md`. It imports neither hackathon applicant data nor the hackathon's hook-based distance rules, GPA rescaling, or external model services.
