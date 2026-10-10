# Validation results

Validated locally on 2026-10-10.

- All 25 automated tests passed.
- An actual CLI run staged `examples/application.txt`, produced seven field candidates, rejected publication before review, accepted the synthetic fixture fields, and published a snapshot.
- Published fields retained two activity records, two course records, GPA, submitted SAT, interests, activity tags, and essay text.
- A synthetic application and admission event were imported against that snapshot. Search returned the application with its outcome; synthetic evidence was excluded by default and querying the same student with exclusion returned no matches.
- Comparing the published profile with itself returned similarity 1.0 and coverage 0.8. No rigor tags were inferred from courses, so the remaining 0.2 of feature weight was unavailable. Rich activity/course records are stored but are not yet scored.

These results validate the supported text pattern and workflow, not arbitrary real documents or recommendation accuracy. No real applicant data was supplied.

## Unverified paths

The environment has Python 3.9.6, whereas packaged optional dependencies require Python 3.11+. No Python 3.11+ executable, pypdf, Sentence Transformers, Tesseract, or pdftoppm was found. Earlier package-registry requests failed due to unavailable network access. PDF/OCR adapters and essay retrieval mechanics are tested with doubles/fixture vectors; real PDF parsing, OCR output, model inference, and semantic quality remain unverified.

## How to supply inputs

Put consented documents in a local directory and pass their file paths to `stage`. Use a pseudonymous student ID. The application remains a CLI; there is no upload screen.

For free-form UTF-8 text:

```sh
python3 -m admissions.cli --db applicants.db stage inputs/application.txt --kind freeform --student-id student-001 --consent granted
```

For a plain essay:

```sh
python3 -m admissions.cli --db applicants.db stage inputs/essay.txt --kind essay --student-id student-001 --consent granted --batch-id BATCH_ID
```

For a PDF, use the Python environment with the document dependencies installed:

```sh
.venv/bin/python -m admissions.cli --db applicants.db stage inputs/application.pdf --kind pdf --student-id student-001 --consent granted
```

Add `--ocr` for sparse scanned pages after installing the OCR tools. Use `--batch-id BATCH_ID` to group additional files for the same student's same profile snapshot. Real documents require consent; bundled examples require `--synthetic --consent synthetic` instead.

Inspect the returned candidates, individually accept/reject them, and publish using the commands in README.md. Free-form extraction supports only the documented patterns, and unrecognized content requires manual correction. Application destinations and historical outcomes still use the structured JSON importer after profile publication. Avoid mixing current query students and past applicants: outcomes belong only to historical applications. Search currently accepts a query profile JSON file; a published-profile query shortcut is not implemented.

## Designed applicant document pilot

A fuller synthetic application is available at `examples/pilot/student_application.txt`, with independently authored expected fields in `examples/pilot/expected.json`. Reproduce validation with `python3 -m scripts.validate_pilot`; results and the published profile are saved to `examples/pilot/validation_result.json`.

The pilot passed: eight candidates were staged, seven accepted, and an ambiguous GPA rejected. Three activity records, four course records, submitted SAT, academic interests, GPA, and the essay section matched expected values. Source offsets and preserved original bytes were checked. Publication and fictional outcome retrieval succeeded. The retrieval check compares a profile to itself and does not establish neighbor quality.

Designing the document exposed two bugs, now covered by regression tests: a negated submitted-SAT statement was incorrectly extracted, and an essay anecdote could become a canonical activity. Covered negated submission patterns are excluded, and recognized essay sections no longer generate other profile fields. This does not constitute general natural-language negation understanding.

Known omissions: high-school context, free-form family caregiving, and honors. These are present in the original document but absent from the canonical profile. No comprehensive real-document extraction accuracy is claimed. PDF/OCR and real-model semantic inference remain unverified. All 27 automated tests passed after the fixes.

## Unified retrieval validation

All 40 automated tests passed after integrating GPA, submitted SAT, rich course records, rich activity records, interests, and essay passage similarity into `retrieve`.

Authored-vector scenarios confirm that changing essay content changes rankings between academically comparable applicants; a matching essay does not rescue an applicant below the academic gate. Tests also cover richer evidence versus tag-only records, missing essays, incompatible grade scales, stale and wrong-model indexes, one-to-one record alignment, deduplication after combined scoring, self/cohort exclusions, and independence from admission outcomes. These scenarios test ranking behavior, not the real embedding model's semantic accuracy.

An actual CLI smoke run imported the bundled three-applicant cohort and used `retrieve --without-essays`. All three candidates were returned with component explanations; the closest academic candidate ranked first. The output explicitly identified essay scoring as disabled. Actual semantic inference remains blocked by absent model dependencies and package-registry access.

Unified retrieval can query a published snapshot directly with `--snapshot-id`; the query student's records are excluded automatically. Ranking weights and minimum academic requirements remain provisional; they require evaluation with real applicants and counselor relevance judgments.

## Outcome explanation and stability integration

All 51 automated tests pass. New tests cover separate source and verification pools, synthetic evidence never becoming verified, dated outcome transitions, conflicting timezone-equivalent decisions, unknown/waitlist handling, per-pool deduplication, insufficient evidence, full-cohort counts despite a one-result display limit, old-schema metadata defaults, and outcome-direction flips. A fixture-vector essay ablation changes the top match and outcome direction while the entire diagnostic run uses only one query embedding call.

The combined retrieval remains outcome-independent. Source verification is asserted metadata rather than independently authenticated evidence. Minimum sample counts and lean thresholds are provisional. Real PDF/OCR execution and real essay-model semantic inference remain unverified.
