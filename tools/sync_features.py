"""Copy docs/features.json into the FEATURES block of web/app.js and the marked section of README.md.

One list, three readers: the About page, the README, and anyone opening the JSON.

    python tools/sync_features.py           rewrite both
    python tools/sync_features.py --check   exit 1 if either copy differs from the JSON (the test suite runs this)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ROOT / "docs" / "features.json"
APP = ROOT / "web" / "app.js"
README = ROOT / "README.md"
JS_START, JS_END = "/*FEATURES_START*/", "/*FEATURES_END*/"
MD_START, MD_END = "<!-- FEATURES_START -->", "<!-- FEATURES_END -->"
STATUS_WORD = {"works": "Works", "works with a key": "Works with a key", "thin": "Thin", "not done": "Not done"}


def readme_section(features) -> str:
    rows = ["| Feature | What it does | Where | Status |", "|---|---|---|---|"]
    for f in features:
        where = f.get("where") or ""
        if where.startswith("python "):
            where = f"`{where}`"
        rows.append(f"| **{f['name']}** | {f['what']} | {where} | {STATUS_WORD.get(f['status'], f['status'])} |")
    n_done = sum(1 for f in features if f["status"].startswith("works"))
    head = (f"\nGenerated from `docs/features.json` by `tools/sync_features.py`; the About page shows the same list. "
            f"{n_done} of {len(features)} work today.\n\n")
    return head + "\n".join(rows) + "\n"


def splice(src: str, start: str, end: str, body: str) -> str:
    a, b = src.index(start) + len(start), src.index(end)
    return src[:a] + body + src[b:]


def main() -> int:
    features = json.loads(FEATURES.read_text(encoding="utf-8"))
    js_body = json.dumps(features, ensure_ascii=False, separators=(",", ":"))
    md_body = readme_section(features)
    app, readme = APP.read_text(encoding="utf-8"), README.read_text(encoding="utf-8")
    new_app, new_readme = splice(app, JS_START, JS_END, js_body), splice(readme, MD_START, MD_END, md_body)
    changed = [name for name, old, new in (("web/app.js", app, new_app), ("README.md", readme, new_readme)) if old != new]
    if not changed:
        print("app.js and README.md already match docs/features.json")
        return 0
    if "--check" in sys.argv:
        print("out of date with docs/features.json:", ", ".join(changed), "; run python tools/sync_features.py")
        return 1
    APP.write_text(new_app, encoding="utf-8")
    README.write_text(new_readme, encoding="utf-8")
    print("updated:", ", ".join(changed), f"({len(features)} features)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
