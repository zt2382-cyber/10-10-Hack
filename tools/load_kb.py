"""Build one short reference page per college from its own published form, and load them into PRISM's Knowledge Base.

    python tools/load_kb.py            write the pages to data/kb/colleges/
    python tools/load_kb.py --upload   also upload them (needs the PRISM settings and PRISM_SEND=1)

Each page holds only statements that passed the code checks in engine/claims.py, with the college's source link.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import claims, colleges as C  # noqa: E402

OUT = ROOT / "data" / "kb" / "colleges"


def build() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for col in C.load_colleges():
        says = claims.college_says(col)
        if not says:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", col["name"].lower()).strip("-")
        lines = [f"# What {col['name']} says in its own Common Data Set", "",
                 f"Source: {says[0].get('source_url')}  |  Year: {says[0].get('year')}",
                 "These are the college's own published statements. They say what the college reports, not how much any factor changes a decision.", ""]
        lines += [f"- {s['text']}" for s in says]
        p = OUT / f"{slug}.md"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        made.append(p)
    return made


if __name__ == "__main__":
    pages = build()
    print(len(pages), "pages written to", OUT)
    if "--upload" in sys.argv:
        from engine import prism
        for p in pages:
            r = prism.kb_upload(p)
            print(p.name, "ok" if r.get("ok") else r.get("why"), r.get("chunk_count"))
