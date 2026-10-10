# How this tool sets reach / target / likely, and what the published numbers mean

Source: the team's own rule text in `ux/C_trust_made_visible.md` (written 2026-10-10; thresholds are the team's ASSUMED values, not an industry standard) and the Common Data Set (CDS) extracts in `outcomes_sample.csv` (collegedata.fyi, https://www.collegedata.fyi, fetched 2026-10-10).
Status: pencil, unreviewed. A person must approve the thresholds before they are shown to families.

## The labelling rule (set by code, not by the model)

Inputs: the college's admit rate (admitted divided by applied, from its CDS section C1) and the college's middle-50% SAT range for enrolled students who submitted (CDS section C9).

1. Admit rate under 0.15: the label is "Reach for everyone". No student input is used.
2. A required input is missing (admit rate, or the SAT range because the college is test-blind): the label is "Can't tell", with the reason shown.
3. Student score below the college's 25th percentile: "Reach".
4. Student score from the 25th percentile up to the 75th percentile: "Target".
5. Student score at or above the 75th percentile: "Target" if the admit rate is under 0.40, and "Likely" if it is 0.40 or higher.
6. The label is re-run with the student score 30 points lower and 30 points higher. If the label changes, both labels are shown ("Target, could be Likely").

Every threshold above (0.15, 0.40, 30 points) is an assumption of the team. This document is the place to change it.

## What the 25th-75th percentile range means

The CDS percentiles describe students who ENROLLED and SUBMITTED scores. They do not describe everyone who applied or everyone who was admitted. The share who submitted is printed beside each range and must be quoted with it.
Example, from the colleges' own 2025-26 files: at Georgia Tech 78% of enrolled first-years submitted SAT scores (https://irp.gatech.edu/sites/default/files/CDS/CDS_2025-2026_FINAL_R4_03JUN2026.pdf); at the University of Michigan 55% did (https://obp.umich.edu/wp-content/uploads/pubdata/cds/cds_2025-26_umaa.pdf); at the University of Arizona 12% did (https://uair.arizona.edu/sites/default/files/2026-06/CDS_PDF_2025-26_v02_RE-PRINT.pdf). Where few students submit, the range describes a small, self-selected group.

## What the GPA bands mean

CDS sections C11 and C12 give the share of enrolled first-year students in each GPA band and the average GPA. They describe who enrolled. They are not admit rates by GPA band, and this tool never says "students with your GPA were admitted at X percent".
Colleges use their own GPA scales. Example: the University of California computes a weighted, capped GPA from 10th and 11th grade A-G courses (https://admission.universityofcalifornia.edu/campuses-majors/first-year-admit-data.html, fetched 2026-10-10), so a UC "4.20" is not a transcript GPA.

## What "Very Important / Important / Considered / Not Considered" means

CDS section C7 is the college's own description of how it treats each factor. It tells you what the college says; it does not say how much a factor moves any decision, and it does not say an essay or an activity raised or lowered anyone's result.

## Things this tool does not know

- Anything about one student's chance of admission.
- Recruited-athlete, legacy, financial-need or major-specific effects (the CDS does not report admit rates for them).
- Whether a college's published file is correct. Extraction from PDFs fails sometimes: in the 2024-25 file for the Massachusetts Institute of Technology the extracted applicant and admit counts were internally inconsistent (admitted greater than applied), so the tool shows "not reported" for it and points to the federal figure instead (IPEDS 2023: 26,904 applicants and 1,274 admitted; https://nces.ed.gov/ipeds/datacenter/data/ADM2023.zip).
