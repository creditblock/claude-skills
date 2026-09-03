import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RENDER = SKILL / "scripts" / "render_compare.py"
SAMPLE = SKILL / "assets" / "sample-compare.json"


def run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(RENDER), *args],
        capture_output=True, text=True, cwd=cwd,
    )


def blob_of(html):
    m = re.search(r"const DATA\s*=\s*(.+?);\s*\n", html, re.S)
    assert m, "could not locate DATA blob"
    return m.group(1)


class RenderCompareTests(unittest.TestCase):
    def test_sample_renders_and_replaces_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.html"
            r = run([str(SAMPLE), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            self.assertNotIn("/*__COMPARE_JSON__*/", html)
            self.assertIn('id="app"', html)
            data = json.loads(SAMPLE.read_text(encoding="utf-8"))
            for c in data["companies"]:
                self.assertIn(c["name"], html)
            for t in data["themes"]:
                self.assertIn(t["name"], html)

    def test_single_closing_script_tag(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.html"
            r = run([str(SAMPLE), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(out.read_text(encoding="utf-8").count("</script>"), 1)

    def test_closing_script_tag_in_note_is_escaped(self):
        doc = {
            "companies": [{"name": "A"}, {"name": "B"}],
            "themes": [{"name": "T", "capabilities": [{
                "name": "C", "cells": {
                    "A": {"status": "yes", "note": "handles </script> and <b> in notes", "source": "https://x.co"},
                    "B": {"status": "no"},
                }}]}],
        }
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            out = Path(d) / "o.html"
            r = run([str(src), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            self.assertEqual(html.count("</script>"), 1)
            self.assertIn("\\u003c", html)
            parsed = json.loads(blob_of(html))
            note = parsed["themes"][0]["capabilities"][0]["cells"]["A"]["note"]
            self.assertIn("</script>", note)

    def test_missing_companies_fails(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text('{"themes": []}', encoding="utf-8")
            r = run([str(src)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("companies", r.stderr)

    def test_company_count_bounds(self):
        one = {"companies": [{"name": "A"}], "themes": [{"name": "T", "capabilities": [
            {"name": "C", "cells": {"A": {"status": "yes"}}}]}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(one), encoding="utf-8")
            r = run([str(src)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("2 to 5", r.stderr)

    def test_missing_cell_for_company_fails(self):
        doc = {"companies": [{"name": "A"}, {"name": "B"}], "themes": [{"name": "T", "capabilities": [
            {"name": "C", "cells": {"A": {"status": "yes"}}}]}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            r = run([str(src)])
            self.assertEqual(r.returncode, 1)
            self.assertIn('missing cell for company "B"', r.stderr)

    def test_extra_cell_key_fails(self):
        doc = {"companies": [{"name": "A"}, {"name": "B"}], "themes": [{"name": "T", "capabilities": [
            {"name": "C", "cells": {"A": {"status": "yes"}, "B": {"status": "no"}, "Z": {"status": "yes"}}}]}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            r = run([str(src)])
            self.assertEqual(r.returncode, 1)
            self.assertIn('"Z"', r.stderr)

    def test_bad_status_fails(self):
        doc = {"companies": [{"name": "A"}, {"name": "B"}], "themes": [{"name": "T", "capabilities": [
            {"name": "C", "cells": {"A": {"status": "maybe"}, "B": {"status": "no"}}}]}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            r = run([str(src)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("status", r.stderr)

    def test_default_output_filename(self):
        with tempfile.TemporaryDirectory() as d:
            r = run([str(SAMPLE)], cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            produced = Path(r.stdout.strip())
            self.assertTrue(produced.exists())
            self.assertTrue(produced.name.endswith("-compare.html"))

    def test_directory_input_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            r = run([d])  # a directory, not a file
            self.assertEqual(r.returncode, 1)
            self.assertIn("cannot read", r.stderr)

    def test_status_survives_into_blob(self):
        doc = {"companies": [{"name": "A"}, {"name": "B"}], "themes": [{"name": "T", "capabilities": [
            {"name": "C", "cells": {"A": {"status": "partial"}, "B": {"status": "unknown"}}}]}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "c.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            out = Path(d) / "o.html"
            r = run([str(src), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            cells = json.loads(blob_of(out.read_text(encoding="utf-8")))["themes"][0]["capabilities"][0]["cells"]
            self.assertEqual(cells["A"]["status"], "partial")
            self.assertEqual(cells["B"]["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
