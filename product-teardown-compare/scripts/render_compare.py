#!/usr/bin/env python3
"""Render a comparison compare.json into a self-contained HTML capability matrix."""
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "compare-template.html"
PLACEHOLDER = "/*__COMPARE_JSON__*/"
STATUSES = ("yes", "partial", "no", "unknown")


def fail(msg):
    print(f"render_compare.py: {msg}", file=sys.stderr)
    sys.exit(1)


def _obj(v, where):
    if not isinstance(v, dict):
        fail(f"{where} must be an object")
    return v


def _nonempty_list(container, key, where):
    val = container.get(key)
    if not isinstance(val, list) or not val:
        fail(f"{where}{key} must be a non-empty array")
    return val


def _require(container, keys, where, str_keys=()):
    if not isinstance(container, dict):
        fail(f"{where.rstrip('.') or 'top-level'} must be an object")
    for key in keys:
        if key not in container:
            fail(f"missing required key: {where}{key}")
    for key in str_keys:
        if not isinstance(container.get(key), str) or not container[key].strip():
            fail(f"{where}{key} must be a non-empty string")


def validate(data):
    _require(data, ("companies", "themes"), "")
    companies = data["companies"]
    if not isinstance(companies, list) or not (2 <= len(companies) <= 5):
        fail("companies must be an array of 2 to 5 entries")
    names = []
    for i, c in enumerate(companies):
        _require(c, ("name",), f"companies[{i}].", str_keys=("name",))
        names.append(c["name"])
    if len(set(names)) != len(names):
        fail("company names must be unique")

    themes = _nonempty_list(data, "themes", "")
    for ti, t in enumerate(themes):
        tw = f"themes[{ti}]."
        _require(t, ("name", "capabilities"), tw, str_keys=("name",))
        caps = _nonempty_list(t, "capabilities", tw)
        for ci, cap in enumerate(caps):
            cw = f"themes[{ti}].capabilities[{ci}]."
            _require(cap, ("name", "cells"), cw, str_keys=("name",))
            cells = _obj(cap["cells"], cw + "cells")
            for n in names:
                if n not in cells:
                    fail(f'{cw}cells: missing cell for company "{n}"')
                cell = _obj(cells[n], f'{cw}cells["{n}"]')
                if cell.get("status") not in STATUSES:
                    fail(f'{cw}cells["{n}"].status must be one of ' + ", ".join(STATUSES))
            for extra in cells:
                if extra not in names:
                    fail(f'{cw}cells: "{extra}" is not a listed company')


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s or "comparison"


def main(argv):
    if not (2 <= len(argv) <= 3):
        fail("usage: render_compare.py <compare.json> [output.html]")
    src = Path(argv[1])
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"input not found: {src}")
    except json.JSONDecodeError as e:
        fail(f"invalid JSON: {e}")

    validate(data)

    if len(argv) == 3:
        out = Path(argv[2])
    else:
        base = data.get("title") or "-vs-".join(c["name"] for c in data["companies"])
        slug = slugify(base)[:80].rstrip("-") or "comparison"
        out = Path.cwd() / f"{slug}-compare.html"

    try:
        template = TEMPLATE.read_text(encoding="utf-8")
    except OSError as e:
        fail(f"cannot read template: {e}")
    if PLACEHOLDER not in template:
        fail(f"template missing placeholder {PLACEHOLDER}")

    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c")
    html = template.replace(PLACEHOLDER, blob)
    try:
        out.write_text(html, encoding="utf-8")
    except OSError as e:
        fail(f"cannot write {out}: {e}")
    print(out.resolve())


if __name__ == "__main__":
    main(sys.argv)
