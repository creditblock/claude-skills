---
name: product-teardown-compare
description: Use when the user wants to compare two to five companies' products and features side by side — "compare Secoda, Atlan and Collibra", "competitive comparison of X and Y", "capability matrix for these vendors", "how do A and B stack up on features". Researches every company's public site and produces a self-contained interactive HTML capability matrix with a cited status per company.
---

# Product Teardown — Compare

Research 2–5 companies and emit one self-contained HTML **capability matrix**:
capabilities as rows (grouped into themes), companies as columns, each cell a
status (yes / partial / no / unknown) plus a one-line note and a source URL.

Sibling to the `product-teardown` skill, which catalogs a single company in
depth. Use that one for a per-company teardown; use this one to compare a set.

## When to use

The user names 2–5 companies (or gives their URLs) and wants them compared, or
asks for a capability / feature matrix across vendors. One comparison per run.

## Inputs

- 2 to 5 company names and/or website URLs.
- Optional: a scope hint (e.g. "just their data-governance products").

## Workflow

1. **Resolve each official site.** Web-search any bare names; confirm each
   primary domain is first-party (their own site, not a directory or reseller).
2. **Research every company.** Read each one's homepage, `/products`,
   `/solutions`, `/platform`, individual product pages, `/pricing`, and
   developer docs.
   - First-party pages only for the matrix. Paraphrase everything; never copy
     marketing sentences verbatim.
   - Prefer web search/fetch tools; if unavailable, drive a browser over the
     same first-party pages.
3. **Synthesize one shared capability taxonomy** that fairly covers the whole
   set — do not privilege any single company's product names or framing. Group
   capabilities under 4–8 theme headers, 3–6 capabilities per theme (roughly
   15–35 rows total).
4. **Score every company on every capability:**
   - `yes` — clearly offered, with a first-party page to cite.
   - `partial` — limited form, add-on, preview, or only adjacent to it.
   - `no` — the company's own materials indicate it is not offered.
   - `unknown` — not determinable from first-party sources. Use this rather
     than guessing.
   Give each cell a short `note` naming *how* the company does it (or why it is
   partial) and a `source` URL that supports the status. Be even-handed: a
   status you cannot defend from a cited first-party page is `unknown`.
5. **Optional:** add a small `data:` URI `logo` per company (homepage
   `<link rel="icon">` or `/favicon.ico`; downsize to ~32–64px; base64). Omit on
   failure — the column header falls back to a name monogram.
6. **Build `compare.json`** in the current working directory using the schema
   below.
7. **Render.** Run:
   `python3 <skill-dir>/scripts/render_compare.py compare.json`
   where `<skill-dir>` is the directory this `SKILL.md` lives in — in Claude
   Code that is `~/.claude/skills/product-teardown-compare`. It prints the path
   of the generated `<slug>-compare.html`.
8. **Report.** Give the user the path. Offer to open it in the browser preview
   (serve the directory with `python3 -m http.server`). For a claude.ai
   Artifact, pass only the `<style>` / `<div id="app">` / `<script>` blocks with
   a per-comparison title and description, not the whole document. Leave
   `compare.json` next to the HTML for re-rendering.
   - For a PDF, the page has a print stylesheet: opening it and printing to PDF
     in landscape gives a paginated light-theme report with every cell's note
     and source expanded and the company header repeated on each page. Headless
     Chrome works too: `chrome --headless --no-pdf-header-footer
     --print-to-pdf=out.pdf file://<path>`.

## compare.json schema

- `title` (string) — optional name for the comparison; omit and it is built
  from the company names.
- `theme` (string) — `"dark"` (default) or `"light"` for the initial
  background. The page also has a light/dark toggle in the header; a viewer's
  choice is remembered in that browser.
- `generatedAt` (string, `YYYY-MM-DD`) — optional, provenance only.
- `companies` (array, required, 2–5). Array order is column order. Each:
  - `name` (string, required, unique) — also the key used in every `cells`
    object.
  - `url` (string) — optional.
  - `logo` (string) — optional `data:image/...;base64,` URI; never a remote
    URL. Omit for a name monogram.
  - `note` (string) — optional one-liner shown under the column header.
- `themes` (array, required, non-empty; target 4–8). Each:
  - `name` (string, required).
  - `capabilities` (array, required, non-empty; target 3–6). Each:
    - `name` (string, required).
    - `description` (string) — optional one-line hint under the row name.
    - `cells` (object, required) — one entry for **every** company `name`. Each
      entry:
      - `status` (string, required) — `yes` | `partial` | `no` | `unknown`.
      - `note` (string) — short phrase; expected for `yes` and `partial`.
      - `source` (string) — first-party URL supporting the status; expected for
        `yes` and `partial`.

A missing cell, an extra cell key, or an invalid status is a hard render error —
the matrix is always complete.

## Constraints

- One comparison per run; no merging into a prior matrix.
- The generated HTML makes no external requests and works offline.
- `render_compare.py` uses only the Python standard library.
- Status must be defensible from a cited first-party page; otherwise `unknown`.

## Testing the skill machinery

`python3 <skill-dir>/scripts/test_render_compare.py -v` — exercises the render
script against `assets/sample-compare.json`.

Manual acceptance check (render the sample, then in a browser):

- the score header sticks to the top on scroll and shows each company's yes /
  partial counts
- "Differences only" hides rows where every company has the same status, and a
  theme whose rows all vanish
- clicking a cell reveals its full note and source link; "Expand all" opens
  every cell
- a theme header collapses its rows; the theme-jump menu scrolls to a group
- the dark/light toggle flips the page and survives a reload
- the matrix scrolls sideways without the page scrolling sideways
- browser console shows zero errors; network panel shows zero external requests
