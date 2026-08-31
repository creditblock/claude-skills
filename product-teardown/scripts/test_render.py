import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RENDER = SKILL / "scripts" / "render.py"
SAMPLE = SKILL / "assets" / "sample-catalog.json"


def run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(RENDER), *args],
        capture_output=True, text=True, cwd=cwd,
    )


class RenderTests(unittest.TestCase):
    def test_sample_renders_and_replaces_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.html"
            r = run([str(SAMPLE), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            self.assertNotIn("/*__CATALOG_JSON__*/", html)
            self.assertIn('id="app"', html)
            data = json.loads(SAMPLE.read_text(encoding="utf-8"))
            self.assertIn(data["company"], html)
            for p in data["products"]:
                self.assertIn(p["name"], html)

    def test_single_closing_script_tag(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.html"
            r = run([str(SAMPLE), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            self.assertEqual(html.count("</script>"), 1)

    def test_closing_script_tag_in_prose_is_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "cat.json"
            cat.write_text(json.dumps({
                "company": "Acme",
                "products": [{
                    "name": "Widget",
                    "description": "Handles latency < 100ms and never emits </script> markup",
                    "categories": [{
                        "name": "Core",
                        "features": [{
                            "name": "Parser",
                            "description": "Rejects a raw </script> in <input> without breaking out",
                            "sources": ["https://example.com/doc"],
                        }],
                    }],
                }],
            }), encoding="utf-8")
            out = Path(d) / "out.html"
            r = run([str(cat), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            # Only the template's real closing tag survives; escaped ones do not.
            self.assertEqual(html.count("</script>"), 1)
            self.assertIn("\\u003c", html)
            # Embedded JSON blob is still valid JSON after escaping.
            m = re.search(r"const DATA\s*=\s*(.+?);\s*\n", html, re.S)
            self.assertIsNotNone(m, "could not locate DATA blob")
            blob = m.group(1)
            data = json.loads(blob)
            self.assertEqual(data["company"], "Acme")
            self.assertIn("</script>", data["products"][0]["description"])

    def test_missing_required_key_fails(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text('{"products": []}', encoding="utf-8")
            r = run([str(bad)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("company", r.stderr)

    def test_missing_feature_sources_fails(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text(json.dumps({
                "company": "X",
                "products": [{
                    "name": "P", "description": "d",
                    "categories": [{
                        "name": "C",
                        "features": [{"name": "F", "description": "d", "sources": []}],
                    }],
                }],
            }), encoding="utf-8")
            r = run([str(bad)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("sources", r.stderr)

    def test_status_field_survives_into_blob(self):
        with tempfile.TemporaryDirectory() as d:
            cat = Path(d) / "cat.json"
            cat.write_text(json.dumps({
                "company": "Acme",
                "products": [{
                    "name": "Widget", "description": "d", "status": "Beta",
                    "categories": [{
                        "name": "Core",
                        "features": [{
                            "name": "Parser", "description": "d",
                            "status": "Coming soon",
                            "sources": ["https://example.com/doc"],
                        }],
                    }],
                }],
            }), encoding="utf-8")
            out = Path(d) / "out.html"
            r = run([str(cat), str(out)])
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding="utf-8")
            m = re.search(r"const DATA\s*=\s*(.+?);\s*\n", html, re.S)
            self.assertIsNotNone(m, "could not locate DATA blob")
            data = json.loads(m.group(1))
            self.assertEqual(data["products"][0]["status"], "Beta")
            self.assertEqual(
                data["products"][0]["categories"][0]["features"][0]["status"],
                "Coming soon")

    def test_default_output_filename_from_slug(self):
        with tempfile.TemporaryDirectory() as d:
            r = run([str(SAMPLE)], cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            produced = Path(r.stdout.strip())
            self.assertTrue(produced.exists())
            self.assertEqual(produced.name, "equifax-catalog.html")


if __name__ == "__main__":
    unittest.main()
