# PRISM setup (one page)

PRISM, by Block Convey, is a required sponsor tool. It records what an AI did and checks it. In this build it
watches the essay reader. It never touches a label: if PRISM is off, slow, or down, the page works the same.

## Do once (one person)
1. Sign up at prism.blockconvey.com/signup. That creates the organisation and the first project.
2. Apply the event coupon under Settings, Billing. Enter it there only; it is not written in this repository.
3. Name the project after the team (Counselor Copilot).
4. Settings, Project: copy the Project ID (a long UUID). Use the ID, not the name; PRISM refuses a name.
5. Make an API key with purpose "custom" (one key can send and read). It is shown once. Save it in a file
   OUTSIDE the repository, one key on one line.
6. In your shell set `PRISM_KEY_FILE` (path to that file) and `PRISM_PROJECT_ID`. Set `PRISM_SEND=1` only for
   the test run and the demo. With it unset nothing is sent, which protects the 200 scored records a day.
7. Check: `python -m engine.prism` (it sends one test trace, uploads one small file, runs one search).
8. For the guardrail (rule 1) also set `ANTHROPIC_KEY_FILE` (same idea, one key on one line).

Limits the code enforces: 150 records a day by default (`PRISM_DAILY_LIMIT`), counted in `data/local/prism_count.json`;
the day resets at 00:00 UTC (8 PM New York). Every call has a 6 second timeout and never raises.

## How each of the day's three rules is met
| Rule | What this build does | What a judge sees |
|---|---|---|
| 1. A guardrail on the essay | `prism.screen(essay)` sends one tiny model call (smallest Claude model, 16 tokens) through PRISM's own proxy. The proxy is the only place a guardrail can block. In the dashboard: Guardrails, prompt injection set to block. | The essay with the hidden instruction (SYNTHETIC essay 4) is stopped, the screen says "blocked by PRISM guardrail", and the rule and the blocked call are in the PRISM dashboard. The code-side check in `privacy.py` still runs first. |
| 2. An evaluator on the essay reader's output | The reader's call is sent with `prism.trace(...)`: input, output, model, time, plus our own quote check result in metadata. The visible trail is sent with `prism.submit_steps(...)` and `prism.evaluation(id)` reads PRISM's own scorecard back. | The dashboard shows each reader trace with PRISM's automatic scores (response quality, satisfaction, flagged or not). The screen can show the scorecard numbers read back from PRISM, labelled as PRISM's. |
| 3. One claim grounded through the Knowledge Base | `prism.kb_upload` puts the three files in `data/kb/` in the project; `prism.kb_search(query)` returns the matching text and its document name for one claim. | One sentence on screen with the exact passage and document name PRISM returned. |

## Fallbacks (if a rule cannot be met live)
- Rule 1: show the code-side block (`privacy.mask` marks the essay blocked) and the dashboard guardrail rule screenshot; say plainly that PRISM's block happens only through its proxy and was not exercised live.
- Rule 2: show PRISM's automatic scores on the traces already sent (see the dashboard), and the trajectory scorecard from `evaluation()`. Say which Evaluators Hub step was not done.
- Rule 3: show the claim with its source from `claims.py` (the college's own published form) and the KB search result from a saved run; say the live search was not used.

## Seen working on 2026-10-10 (real calls, team key)
Trace stored (200). Knowledge Base upload (200, 2 pieces). Search (200; it is keyword overlap, not meaning, so
use words that are literally in the document). Trajectory stored (200) and its scorecard read back (overall 98.89,
safety 100). A proxy call went through (200). The proxy did NOT block an obvious injected instruction, because no
guardrail rule had been switched on yet; that is a dashboard step.
Trap found: a trajectory whose steps have the same input text is scored as an "infinite loop". The code gives every step its own text.

## Still UNVERIFIED SHAPE (each is marked in `engine/prism.py`) and what to ask the Block Convey people
1. `_proxy_block_reason`: what a blocked proxy call looks like (status code, body, header). Ask: "With prompt injection set to block, what status and body does `/proxy/anthropic/v1/messages` return, and is there a header I can read?"
2. `screen` headers `X-PRISMtrace-Agent-Name` and `X-PRISMtrace-Session-Id`: invented, harmless if ignored. Ask: "How do I tag a proxy call with agent and session?"
3. `_to_trajectory_steps`: which `step_type` fits code-only steps (I use tool_call for retrieve, reasoning, final_answer for log). Ask: "Is that right, and is the 'tool call as first step' note a problem?"
4. Evaluators Hub: nothing in code. Ask: "How do I attach an Evaluator to the essay reader's traces: dashboard only, or an API call?"
