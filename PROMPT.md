Produce today's edition of The Aperture, a daily newspaper-style brief.

Work in ~/Documents/aperture-brief. Read CLAUDE.md and EDITORIAL.md there first —
they carry the architecture and the editorial rules, and they are authoritative.
Do NOT write HTML. Your output is one JSON file; the build renders the page.

## 1. Research

Research the last 24 hours per EDITORIAL.md: US Politics, India, Bengal,
Geopolitics, Cricket, Entertainment, Tech, Science, Philosophy, Travel, and one
Happy Story. Open every article you intend to link and confirm it is genuinely
readable without a subscription, and that the URL points at the piece itself
rather than a section front or tag page.

Read yesterday's and the day before's files in content/ to avoid repeating a
story or re-covering the same angle of a running one.

## 2. Write content/YYYY-MM-DD.json

    {
      "date": "YYYY-MM-DD",
      "sections": {
        "politics":      {"top": [item, ...], "more": [item, ...]},
        "india":         {"top": [...], "more": [...]},
        "geo":           {"top": [...], "more": [...]},
        "sports":        {"top": [...], "more": [...]},
        "entertainment": {"top": [...], "more": [...]},
        "bengal":        [item, ...],
        "travel":        [item, item],
        "happy":         item,
        "tech_top":      [item, ...],
        "tech_more":     [item, ...],
        "tech_101":      [{"term": "...", "text": "..."}],
        "science":       [item, ...],
        "philosophy":    [item, ...],
        "philosophy_101":[{"term": "...", "text": "..."}]
      }
    }

An item is:

    {
      "headline": "...",              required
      "url": "https://...",           required, the actual article
      "source": "NPR",                required, the outlet's name
      "blurb": "...",                 required — what happened AND why it matters
      "image": "https://...",         optional og:image; expected for politics,
                                      geo, india and tech `more` items
      "investigative": true,          optional, for investigative outlets
      "pm_note": "...",               tech_top only: why it matters to a PM
      "kind": "chemistry"             science only: chemistry | space | biology |
                                      physics | climate | neuroscience | medicine
    }

Order each `top` list by importance — the first item becomes that section's
lede. Science needs one `kind: "chemistry"` and one `kind: "space"` item.

## 3. Build, fix, publish

    python3 build.py YYYY-MM-DD

It validates before rendering and FAILS on: a missing field, a hard-paywalled
domain, a hub/tag URL, an outlet used more than 3 times, a duplicate URL, a URL
already used in the last 3 editions, more than 7 India items, or more than 20 top
stories across the edition. Fix the content and re-run until it passes. Do not
work around a check — if the story cap fails, drop the weakest stories rather
than moving them into `more`.

Warnings are worth heeding but do not block.

Then publish:

    python3 push_content.py YYYY-MM-DD

That pushes the JSON to GitHub, where a workflow renders and publishes the page.
Do not run git in this folder — commits cannot complete here and will strand lock
files. push_content.py exists precisely to avoid that.

## 4. Report back

Say what led each section, anything you had to drop and why, any warnings left
standing, and whether the push succeeded. If push_content.py fails, report the
error rather than retrying blindly.

Send no email and run no notification script — publishing triggers a push
notification automatically.
