"""Copy docs/fixture_result.json into the FIXTURE block of web/app.js, so the two never drift.

    python tools/sync_fixture.py           rewrite the block
    python tools/sync_fixture.py --check   exit 1 if the block differs from the file (for a test or a hook)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "docs" / "fixture_result.json"
APP = ROOT / "web" / "app.js"
START, END = "/*FIXTURE_START*/", "/*FIXTURE_END*/"


def main() -> int:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    block = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    src = APP.read_text(encoding="utf-8")
    a, b = src.index(START) + len(START), src.index(END)
    if src[a:b] == block:
        print("app.js fixture already matches docs/fixture_result.json")
        return 0
    if "--check" in sys.argv:
        print("app.js fixture differs from docs/fixture_result.json; run python tools/sync_fixture.py")
        return 1
    APP.write_text(src[:a] + block + src[b:], encoding="utf-8")
    print("app.js fixture updated,", len(block), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
