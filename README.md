# claud-skills

Claude Code skills.

## Skills

### product-teardown

Researches a company's public website and produces a single self-contained,
interactive HTML catalog of its products and features, grouped by category, with
source citations — styled like a product-catalog console.

**Install:** copy the `product-teardown/` directory into `~/.claude/skills/`.

**Use:** ask Claude for a teardown of a company, e.g. *"do a product teardown of
Stripe"*. Claude researches first-party pages, writes a `catalog.json` in the
working directory, runs the render script, and returns the generated
`<company-slug>-catalog.html`. One company per run.

**Layout:**

```
product-teardown/
  SKILL.md                     # trigger, research methodology, workflow, schema
  scripts/render.py            # catalog.json -> <slug>-catalog.html (stdlib only)
  scripts/test_render.py       # test suite for the render script
  assets/template.html         # dark-theme self-rendering page, JSON placeholder
  assets/sample-catalog.json   # fixture used by the tests
```

**Test:** `python3 product-teardown/scripts/test_render.py -v`
