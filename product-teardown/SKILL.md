---
name: product-teardown
description: Use when the user wants a competitive product teardown or catalog of a company's offerings — "do a product teardown of Acme", "catalog Stripe's products and features", "what products and features does X sell", "build a ChatPRD-style product breakdown for X". Researches the company's public website and produces a self-contained interactive HTML catalog of its products and features with source citations.
---

# Product Teardown

Research one company's public website and emit a single self-contained HTML file
that catalogs its products and, per product, its features grouped by category —
styled like a product-catalog console (dark theme, left product nav, feature
tables, source citations).

## When to use

The user names a company (or gives its URL) and wants its product/feature
landscape captured or compared. One company per run. If the user names several,
run the workflow once per company.

## Inputs

- A company name and/or its website URL.
- Optional: a hint about which product line to focus on.

## Workflow

1. **Resolve the official site.** If given only a name, web-search for the
   company and confirm the primary domain is first-party (their own site, not a
   directory or reseller).
2. **Research.** Read, at minimum: the homepage, `/products`, `/solutions`,
   `/platform`, individual product hub pages, `/pricing`, and the developer or
   API documentation portal if one exists. Prefer dedicated feature pages over
   the homepage for feature detail.
   - Use **first-party pages only** for the catalog itself. A third-party page
     (review site, press) may fill a specific gap — if you rely on one, keep its
     URL in that feature's `sources` and mention in the description that it is
     not first-party.
   - **Paraphrase everything.** Never copy marketing sentences verbatim.
   - Prefer web search/fetch tools for this step. If they are unavailable, drive
     a browser to open the same first-party pages and read their text — the
     first-party and paraphrase rules still apply.
3. **Build `catalog.json`** in the current working directory using the schema
   below. Caps to keep a run bounded: at most ~12 products, at most ~8 features
   per product. Prefer covering more products over exhausting one product's
   features.
   - Optional: capture the company's favicon/logo for the header. Find it from
     the homepage `<link rel="icon">` (or try `/favicon.ico`), download it,
     downsize to ~32–64px, base64-encode it, and put
     `"logo": "data:image/png;base64,<...>"` on the top level. It MUST be a
     `data:` URI (the rendered HTML makes no external requests) and stay small.
     If you can't fetch or encode it, omit `logo` — the header falls back to a
     monogram of the company name.
4. **Render.** Run the bundled render script against `catalog.json`:
   `python3 <skill-dir>/scripts/render.py catalog.json`
   where `<skill-dir>` is the directory this `SKILL.md` lives in — in Claude Code
   that is `~/.claude/skills/product-teardown`. It prints the path of the
   generated `<company-slug>-catalog.html`.
5. **Report.**
   - Give the user the path to the generated `<company-slug>-catalog.html`.
   - Offer to open it in the browser preview (serve the directory with
     `python3 -m http.server` — the Browser pane renders `file://` as a static
     snapshot).
   - If the user wants to share it as a claude.ai Artifact: do **not** pass the
     generated file directly — it is a full HTML document and the Artifact
     wrapper would nest it. Instead create an artifact whose body is only the
     `<style>` block, the `<div id="app">`, and the `<script>` block from the
     generated file, and set a per-company `title` and `description`.
   - Leave `catalog.json` next to the HTML so it can be re-rendered.

## catalog.json schema

- `company` (string, required)
- `logo` (string) — a `data:image/...;base64,` URI for the header icon; omit to
  fall back to a name monogram. Never a remote URL (no external requests).
- `theme` (string) — `"dark"` (default) or `"light"` for the initial background.
  The page also has a light/dark toggle in the header; a viewer's choice is
  remembered in that browser.
- `generatedAt` (string, `YYYY-MM-DD`) — set to today's date (kept in
  catalog.json for provenance; not shown in the rendered HTML)
- `sources` (array of URLs) — top-level pages you consulted (kept in
  catalog.json for provenance; not shown in the rendered HTML)
- `products` (array, required, non-empty), each:
  - `name` (string, required)
  - `description` (string, required) — one paraphrased paragraph
  - `url` (string) — the product's main page
  - `positioning` (string) — how the site frames the product, if stated
  - `targetAudience` (string) — who it is for, if stated
  - `pricing` (string) — free text, often "Contact sales for pricing"
  - `status` (string) — same rule as feature `status`
  - `categories` (array, required, non-empty), each:
    - `name` (string, required)
    - `features` (array, required, non-empty), each:
      - `name` (string, required)
      - `description` (string, required)
      - `points` (array of strings) — 2–4 sub-bullets
      - `sources` (array of URLs, required, non-empty)
      - `status` (string) — only if the site explicitly signals a non-GA state
        (Beta, New, Coming soon, Deprecated); otherwise omit

Do not add `status` to ordinary generally-available products or features.

## Constraints

- One company per run; no merging into a prior catalog.
- The generated HTML makes no external requests and works offline.
- `render.py` uses only the Python standard library.

## Testing the skill machinery

`python3 <skill-dir>/scripts/test_render.py -v` — exercises the render script
against `assets/sample-catalog.json`.

Manual acceptance check (render the sample, then in a browser):

- header shows the company logo (or a name monogram) and a light/dark toggle
- sidebar lists all products with per-product feature counts
- clicking a product switches the main panel and moves the active highlight
- each category has a distinct gradient icon tile; feature cards flow in a grid
- the "N sources" button on a card toggles its source links
- toggling the theme flips the background and survives a reload
- browser console shows zero errors
- network panel shows zero external requests
