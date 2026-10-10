"""Save real runs for the six invented demo students, so the screen can be shared as plain files with no server.

    python tools/make_static.py            runs with whatever is switched on (model, PRISM) and writes dist/
    python tools/make_static.py --zip      also writes dist.zip, ready to upload

The what-if runs (a different score) are made with the model off: only the labels change, and code sets those.
"""
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import pipeline  # noqa: E402

DIST = ROOT / "dist"
SAT_STEPS = (-60, -30, 0, 30, 50, 100, 150)
# Only these fields of a demo student are published. No essay text, no activity text.
MANIFEST_FIELDS = ("label", "sat", "act", "gpa", "gpa_scale", "home_state", "intended_major", "hooks", "college_list")
ACT_STEPS = (-2, -1, 0, 1, 2, 3)


def main() -> None:
    keep = None
    if "--reuse" in sys.argv and (DIST / "static" / "manifest.json").exists():
        # keep the saved runs (they cost model calls and PRISM records); refresh only the page files
        keep = ROOT / "_static_keep"
        if keep.exists():
            shutil.rmtree(keep)
        shutil.move(str(DIST / "static"), str(keep))
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "web", DIST)
    out = DIST / "static"
    if keep:
        shutil.move(str(keep), str(out))
        mf = out / "manifest.json"  # re-strip an older manifest that may still carry essays
        data = json.loads(mf.read_text(encoding="utf-8"))
        data["students"] = [{**{k: st.get(k) for k in MANIFEST_FIELDS}, "index": st.get("index", i)}
                            for i, st in enumerate(data.get("students", []))]
        mf.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        _finish()
        return
    out.mkdir()
    students = pipeline.demo_students()
    manifest = {"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "students": [], "scores": {}}
    for i, st in enumerate(students):
        manifest["students"].append({**{k: st.get(k) for k in MANIFEST_FIELDS}, "index": i})
        base = pipeline.run(dict(st), use_model=True)
        (out / f"run-{i}.json").write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        kind = "SAT" if st.get("sat") else ("ACT" if st.get("act") else None)
        if not kind:
            manifest["scores"][str(i)] = None
            print(i, st["label"][:40], "| no score")
            continue
        key, steps, lo, hi = ("sat", SAT_STEPS, 400, 1600) if kind == "SAT" else ("act", ACT_STEPS, 1, 36)
        values = sorted({min(hi, max(lo, st[key] + d)) for d in steps})
        for v in values:
            if v == st[key]:
                continue
            r = pipeline.run({**st, key: v}, use_model=False)
            # keep the essay reader's part from the real run, so the notes do not vanish when the slider moves
            r["reader"], r["privacy"], r["prism"] = base["reader"], base["privacy"], base["prism"]
            (out / f"run-{i}-{v}.json").write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
        manifest["scores"][str(i)] = {"kind": kind, "base": st[key], "values": values}
        print(i, st["label"][:40], "|", kind, values, "| reader:", base["reader"].get("status"), "| prism:", base["prism"].get("status"))
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    _finish()


def _finish() -> None:
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print("dist:", sum(1 for p in DIST.rglob("*") if p.is_file()), "files,", round(size / 1e6, 2), "MB")
    if "--zip" in sys.argv:
        z = ROOT / "dist.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(DIST.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(DIST).as_posix())
        print("zip:", z, round(z.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
