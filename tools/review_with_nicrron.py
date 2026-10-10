"""Ask models from two different makers, through the Nicrron gateway, to review our core files.

    python tools/review_with_nicrron.py            (needs NICRRON_API_KEY or NICRRON_KEY_FILE)

Writes one short review per model per file to docs/reviews/. The files reviewed hold no student data.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import nicrron  # noqa: E402

FILES = ["engine/labels.py", "engine/privacy.py", "engine/balance.py"]
MODELS = ["openai/gpt-5.5", "mistral/mistral-large-3"]
ASK = ("You are reviewing one file from a tool that helps college counselors. The tool's rule is: code sets every "
       "label and number, uncertainty is stated plainly, and no personal chance of admission is ever given. Review "
       "the file for real bugs, wrong results at boundaries, and anything that could mislead a family. List at most "
       "five findings, most serious first. For each: the function, what is wrong, a concrete input that shows it, "
       "and the smallest fix. If you find nothing serious, say so in one line. Plain language. No praise.")


def one(job):
    path, model = job
    code = (ROOT / path).read_text(encoding="utf-8")
    r = nicrron.chat([{"role": "system", "content": ASK},
                      {"role": "user", "content": f"File: {path}\n\n```python\n{code}\n```"}],
                     model=model, max_tokens=1600, timeout=120)
    return path, model, r


def main():
    out = ROOT / "docs" / "reviews"
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(f, m) for f in FILES for m in MODELS]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for path, model, r in ex.map(one, jobs):
            name = f"{Path(path).stem}__{model.split('/')[-1]}.md"
            if r.get("ok") and (r.get("text") or "").strip():
                (out / name).write_text(f"# Review of `{path}` by {r.get('model') or model}, through Nicrron\n\n"
                                        f"{r['text'].strip()}\n", encoding="utf-8")
                print("ok  ", name, r.get("latency_ms"), "ms,", len(r["text"]), "chars")
            else:
                print("FAIL", name, r.get("error"))


if __name__ == "__main__":
    main()
