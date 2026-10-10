# Review of Desktop/10-10-hack

Reviewed requirements, contract, README, similarity/case loaders, essay reader, and spreadsheet ingestion on 2026-10-10. No source-repository files were changed. Tests ran in a temporary copy: 48 similarity/case tests passed; 60/60 acceptance labels matched and the associated whole-system checks passed.

## Requirements relevant to this project

The Counselor Copilot contract requires deterministic numbers and labels, traceable source evidence, separate national self-reported and counselor-owned pools, explicit insufficient-data states, list balancing, and statements grounded in retrieved cases and published college information. Its added Closeness requirements compare nearest admitted and denied applicants separately and describe stability and admitted-profile archetypes. That repository requires a standard-library-only implementation and explicitly excludes embeddings from Closeness. Those constraints govern its implementation; they do not override the user's authorized semantic retrieval design in nerd_apply.

## Highest-value adaptations

1. **Outcome-group evidence:** adapt `similarity._gap`, `_pool`, and `_parts_summary`. Rank using our unified features, then partition eligible records by outcome to show the nearest admitted and denied examples and per-component comparisons. Preserve waitlist/defer/unknown states rather than infer a final outcome. The source compares seven nearest records per group and requires 15 scored cases in each group before displaying a lean; both settings are provisional rather than validated sufficiency guarantees.
2. **Stability diagnostics:** adapt `_steady`. Recompute with different neighborhood sizes and small score perturbations. For our system also vary component weights and remove the essay signal to report top-k overlap and direction changes. Record perturbations; do not describe them as forecast accuracy.
3. **Separate evidence pools:** adapt `cases.find_similar`'s output architecture. Add explicit source pool, verification, and synthetic status to our sources; return independent cohorts/counts/summaries. A synthetic school record cannot become real verified evidence just because the source pool is counselor-owned.
4. **Explicit cohort relaxation:** adapt `cases._steps` as a policy pattern, not its exact hook-based rules. Broaden major groups or academic thresholds only under declared configuration, label the relaxed criteria, and retain a strict result alongside any expanded result. Never invent missing application cycles, rounds, residency, or programs, or choose relaxation to produce a preferred outcome.
5. **Taxonomy and normalization:** adapt `cases.major_group_for`, college alias mapping, ACT concordance helpers, and spreadsheet column normalization. Keep original values and mapping provenance; preserve test submission distinctions and ambiguity. Counselor activities ratings are not directly interchangeable with national self-ratings.
6. **Essay evidence checks:** adapt `reader.quote_in_essay` / `check_notes` and privacy masking if we add LLM extraction/notes. Exact quote presence establishes textual support, not the truth of a claim or the correctness of its interpretation. Independent model agreement is not verification. Keep original-to-redacted offset mappings.
7. **Optional archetypes:** adapt `_kinds`'s seeded k-medoids concept, naming groups from measured features and using actual profiles as medoids. Evaluate after retrieval relevance is demonstrated; a capped quadratic distance matrix is only appropriate for a small pool.

## Data and implementation limits

The national CSV has 2,247 applicant rows, 20,966 decision rows, and 58 college names. It has SAT/ACT, major, rank, residency, hooks, and self-rated EC-AWARDS/ESSAY-LOR-INTERVIEW. It does not have transcript/GPA records, activity descriptions, essay text, decision dates, application rounds, program-specific applications, or admissions-cycle metadata in these CSVs. Therefore it cannot validate essay embeddings and cannot directly satisfy our strict historical cohort filters. Do not fabricate absent fields or treat the combined essay/LOR/interview rating as essay text or quality.

The README says the upstream public-post dataset has no stated license. This review does not establish redistribution rights or consent for importing those rows into the current consent-gated production-style schema. A separately labeled research dataset requires a provenance/use policy first; no data was imported here.

`similarity._gpa` rescales GPA linearly to 4.0 without preserving grading-system weighting; retain our stricter scale/weighting compatibility instead. `cases._national` collapses repeated student/college outcomes using admitted > denied > waitlisted, potentially conflating programs with chronological decisions; retain our application/outcome-event model. Hook status and race-linked categories should not be copied as default ranking features. Counterfactual score/rating changes demonstrate changes in a distance formula, not causal admissions advice.

`similarity --check` is explicitly a placeholder that prints "--check is not built yet." The requirements propose a 400-decision held-out check, but it has not been implemented. Acceptance tests validate handwritten label rules and workflow conditions, not admission forecasting or semantic retrieval relevance. Our real embedding model execution remains unverified.

## Recommended next implementation

Keep the unified ranker and provenance schema. Add source-scoped admitted/denied evidence summaries with explicit uncertainty states, then ranking stability diagnostics and a counselor-reviewed retrieval evaluation set. Add normalization/taxonomy and configurable cohort expansion afterward. Do not replace semantic essay retrieval with the hackathon's test-heavy distance or import its dataset as fabricated fully specified applications.
