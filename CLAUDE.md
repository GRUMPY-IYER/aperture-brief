# The Aperture — project context

A daily newspaper-style news brief, published to https://aperture.grumpyiyer.com
via GitHub Pages. Personal project of Ganges Bhardwaj (wildlife photographer,
brand "Grumpy Iyer"; product manager, not a professional developer).

**When explaining changes here, favour the "why" over the "how". Name the concept
being applied (data contract, idempotency, least privilege) rather than only the
syntax. Show diffs before applying them.**

## Working agreement

Ganges reviews and pushes his own changes. Do NOT push to this repo — no
`push_content.py` for source files, no API writes, no `git push`. Make the edit
locally, say plainly what changed and why, and leave the commit to him. The one
exception is the daily edition, which the cloud scheduled task publishes on its
own.

## Architecture — content and presentation are separate

    content/YYYY-MM-DD.json   <- editorial content only. No HTML.
    templates/aperture.html.j2 <- ALL layout, CSS, section titles and order
    build.py                   <- renders one into the other, and validates
    index.html                 <- GENERATED. never hand-edit.
    archive/YYYY-MM-DD.html    <- GENERATED. never hand-edit.

Daily flow: a scheduled task researches the news, writes `content/<date>.json`,
and pushes it with `push_content.py`. That push triggers
`.github/workflows/build.yml`, which runs `build.py` and commits the rendered
HTML. `.github/workflows/notify.yml` then sends a web push.

The whole point of the split: an AI writing HTML by hand forgets things (dates in
three places, relative path prefixes, column balance). Those are now computed.

## Rules that matter

- **Never hand-edit `index.html` or `archive/*.html`.** They are build output.
  Change `templates/aperture.html.j2` and rebuild.
- **Builds must be deterministic.** Same content + same inputs = byte-identical
  output. Filler-photo choice is seeded from the date for this reason. If you add
  randomness, seed it.
- **`.nojekyll` must stay.** GitHub Pages runs legacy Jekyll, whose Liquid syntax
  collides with Jinja2's `{{ }}`. Without it the Pages build fails on the template.
- **`.aperture-token` is a real secret.** Gitignored. Never print, commit or echo it.
- The daily token deliberately lacks GitHub "Workflows" permission — automation
  cannot rewrite its own CI. Workflow files are committed by hand. Keep it that way.

## Commands

    python3 build.py                    # build today's edition
    python3 build.py 2026-08-29         # build a specific date
    python3 build.py --check-only DATE  # validate without writing
    python3 push_content.py DATE        # push content JSON -> triggers CI

## Editorial shape

Main column: US Politics, Apu's Corner (India + Bengal + Travel + Happy Story),
Geopolitics, Cricket, From the Field (photography).
Side column: Technology desk (Top Tech, More Tech, Tech 101), Science, Philosophy,
Philosophy 101, Entertainment & Culture.
Science is separate from Philosophy and must carry items tagged
`kind: "chemistry"` and `kind: "space"` — it is not a consciousness desk.
Sourcing favours independent/investigative outlets and avoids paywalls. Full rules
belong in EDITORIAL.md (to be written).

`build.py check()` enforces mechanically: required fields, hard-paywall domains,
hub/tag URLs, max 3 stories per outlet, duplicate URLs, repeats vs the last 3
editions, India cap of 7, exactly 2 travel items. Paywall *judgement* stays human/AI —
only the blocklist is mechanical.

## Known gotchas

- This folder is also mounted into Claude Cowork sessions, which **cannot delete
  files**. Automated git in this folder therefore strands `.git/*.lock` and
  `objects/pack/*.keep` files. That is why the daily task uses the GitHub API
  instead of local git. Working here in Claude Code (normal Terminal access) is fine.
- Wildlife photos in `wildlife/` are the owner's own work. Caption them generically
  ("From the archive") — never assert a species or location that isn't verified.

## Layout rules that are easy to break

- **Never crop a photograph.** No `object-fit: cover`, no fixed heights on images.
  Photos are sized by width with `height: auto`, and carry their real pixel
  dimensions as width/height attributes so the browser reserves the right box.
  The archive is 3:2, 4:3, 1:1 and portrait frames — a fixed height ruins all but one.
- **Sections are flex stacks reordered by CSS `order`**, driven by
  `body[data-reader]`. The side column is grouped into `.desk` wrappers so the
  Technology masthead travels with its sections. Adding a side-column section
  means putting it inside a desk, or it won't reorder.
- **Everything past the fold is a native `<details>`** — no JavaScript. Archived
  editions are standalone files that must keep working for years; the only JS on
  the page is the reader preference, and the page is correct without it.
- Story counts: the 20-top-story cap is a HARD build failure. `more` items,
  Bengal/Travel/Happy and Science/Philosophy sit outside it.

## Open work

- EDITORIAL.md + a slimmed-down scheduled-task prompt.
- Layout: filler photos patch a column-balance problem rather than fixing it.
  The real fix is CSS that lets the browser balance section columns.
- A photo showcase sourced from the owner's NAS library.
