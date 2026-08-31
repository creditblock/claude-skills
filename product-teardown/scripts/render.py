#!/usr/bin/env python3
"""Render a product-teardown catalog.json into a self-contained HTML file."""
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
PLACEHOLDER = "/*__CATALOG_JSON__*/"


def fail(msg):
    print(f"render.py: {msg}", file=sys.stderr)
    sys.exit(1)


def _require(container, keys, where, str_keys=()):
    if not isinstance(container, dict):
        fail(f"{where.rstrip('.') or 'top-level'} must be an object")
    for key in keys:
        if key not in container:
            fail(f"missing required key: {where}{key}")
    for key in str_keys:
        if not isinstance(container.get(key), str):
            fail(f"{where}{key} must be a string")


def _nonempty_list(container, key, where):
    val = container.get(key)
    if not isinstance(val, list) or not val:
        fail(f"{where}{key} must be a non-empty array")
    return val


def validate(data):
    if not isinstance(data, dict):
        fail("top-level JSON must be an object")
    _require(data, ("company", "products"), "", str_keys=("company",))
    products = _nonempty_list(data, "products", "")
    for i, p in enumerate(products):
        pw = f"products[{i}]."
        _require(p, ("name", "description", "categories"), pw, str_keys=("name", "description"))
        cats = _nonempty_list(p, "categories", pw)
        for j, c in enumerate(cats):
            cw = f"products[{i}].categories[{j}]."
            _require(c, ("name", "features"), cw, str_keys=("name",))
            feats = _nonempty_list(c, "features", cw)
            for k, f in enumerate(feats):
                fw = f"products[{i}].categories[{j}].features[{k}]."
                _require(f, ("name", "description", "sources"), fw, str_keys=("name", "description"))
                _nonempty_list(f, "sources", fw)


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return s or "company"


def main(argv):
    if not (2 <= len(argv) <= 3):
        fail("usage: render.py <catalog.json> [output.html]")
    src = Path(argv[1])
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"input not found: {src}")
    except json.JSONDecodeError as e:
        fail(f"invalid JSON: {e}")

    validate(data)

    out = (Path(argv[2]) if len(argv) == 3
           else Path.cwd() / f"{slugify(data['company'])}-catalog.html")

    try:
        template = TEMPLATE.read_text(encoding="utf-8")
    except OSError as e:
        fail(f"cannot read template: {e}")
    if PLACEHOLDER not in template:
        fail(f"template missing placeholder {PLACEHOLDER}")

    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    blob = blob.replace("<", "\\u003c")  # keep "</script>" from closing the tag
    html = template.replace(PLACEHOLDER, blob)
    try:
        out.write_text(html, encoding="utf-8")
    except OSError as e:
        fail(f"cannot write {out}: {e}")
    print(out.resolve())


if __name__ == "__main__":
    main(sys.argv)
