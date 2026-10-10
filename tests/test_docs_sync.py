"""The copies that must not drift: the fixture embedded in app.js, and the feature list in app.js and the README."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DocsSyncTests(unittest.TestCase):
    def run_tool(self, name):
        return subprocess.run([sys.executable, str(ROOT / "tools" / name), "--check"], capture_output=True, text=True, cwd=ROOT)

    def test_fixture_in_app_js_matches_docs(self):
        r = self.run_tool("sync_fixture.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_feature_list_in_app_js_and_readme_matches_docs(self):
        r = self.run_tool("sync_features.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_feature_entries_are_complete(self):
        feats = json.loads((ROOT / "docs" / "features.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(feats), 20)
        ids = [f["id"] for f in feats]
        self.assertEqual(len(ids), len(set(ids)))
        for f in feats:
            for k in ("id", "name", "status", "when", "what", "where", "files"):
                self.assertIn(k, f, f.get("id"))
            self.assertIn(f["status"], ("works", "works with a key", "thin", "not done"), f["id"])
            if f["status"].startswith("works"):
                self.assertTrue(f["where"], f["id"])
            for part in f["files"].replace(",", " ").split():
                p = ROOT / part.rstrip("/")
                self.assertTrue(p.exists() or part.endswith("/"), f"{f['id']}: {part} not found")
            low = (f["what"] + f["where"]).lower()
            for w in ("probab", "odds"):
                self.assertNotIn(w, low, f["id"])


if __name__ == "__main__":
    unittest.main()
