Produce today's edition of The Aperture, a daily newspaper-style brief.

The repo is the connected folder `aperture-brief`. In your shell it is at
`$HOME/mnt/aperture-brief` — cd there; `~/Documents/aperture-brief` will NOT
work from the shell. Read `CLAUDE.md` and `EDITORIAL.md` there first: they carry
the architecture and the editorial rules and are authoritative.

Do NOT write HTML, and do not run git in this folder — commits cannot complete
here and strand lock files. Your output is one JSON file; the build renders the
page and a workflow publishes it.

## 1. Research

Research the last 24 hours per EDITORIAL.md: US Politics, India, Bengal,
Geopolitics, Cricket, Entertainment, Tech, Science, Philosophy, Travel, and one
Happy Story.

**Verifying links.** Opening all ~30 is not affordable. Triage instead: always
open anything from a metered outlet (Scroll.in, Newslaundry, The Caravan, 404
Media, Axios, The Atlantic), anything you are unsure is free, and anything whose
URL might be a section front. Reliably-free outlets (NPR, AP, Reuters, Al
Jazeera, ProPublica, BBC, Mongabay, Atlas Obscura, Aeon) can be taken on
reputation. If a source will not load at all, see EDITORIAL.md's fallbacks —
never guess at what an article says.

Read the most recent files in `content/` (there may be only one or two) to avoid
repeating a story or re-covering the same angle of a running one.

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
      "headline": "...",      required
      "url": "https://...",   required, the actual article
      "source": "NPR",        required — see the naming rule below
      "blurb": "...",         required. `top`/science/philosophy: 2-3 sentences,
                              roughly 40-60 words. `more`, bengal, travel, happy:
                              ONE sentence, roughly 20-30 words.
      "image": "https://...", optional og:image. Worth having on `more` items in
                              politics, geo, india and tech_more. Skip it rather
                              than guess a URL — a broken image is worse than none.
      "investigative": true,  optional. Tags THE PIECE as investigative work, not
                              merely the outlet's reputation.
      "pm_note": "...",       tech_top only, 1 sentence: why it matters to a PM.
      "kind": "chemistry"     science only: chemistry | space | biology | physics |
                              climate | neuroscience | medicine
    }

- Order each `top` list by importance — the first item becomes that section's
  lede, set at full width. Put the genuinely biggest story first.
- Science needs one `kind: "chemistry"` item and one `kind: "space"` item.
- `tech_101` and `philosophy_101` take one or two concepts each. Two is typical.
- `more` may be an empty list. A short honest section beats a padded one.
- **`source` naming**: one exact string per outlet, every time. Not "Scroll.in
  (Reel)" alongside "Scroll.in" — sub-brand variants split the diversity count
  and quietly evade the 3-per-outlet cap. For wire copy on a syndicating site,
  name the site you are linking to.

## 3. Build and fix

    cd $HOME/mnt/aperture-brief && python3 build.py YYYY-MM-DD

It validates before rendering. It FAILS on: a missing required field, a
hard-paywalled domain, an outlet used more than 3 times, a duplicate URL, a URL
used in the last 3 editions, more than 7 India items, or more than 20 top
stories. Fix the content and re-run until it passes. Do not work around a check —
if the story cap fails, drop the weakest stories rather than shifting them into
`more`.

It WARNS (does not block) on: a URL that looks like a section front, a missing
Science `kind`, a travel count other than 2, and a missing Bengal or Happy item.
Read each warning and decide; a warning you have considered and rejected is fine.

## 4. Publish

    python3 push_content.py YYYY-MM-DD

This pushes the JSON to GitHub, where a workflow renders and publishes the page.
If it fails, report the error rather than retrying blindly.

## 5. Report back

Reply in this session with: what led each section, anything you dropped and why,
any warnings left standing, and whether the push succeeded. Nothing to write to a
file — the reply is the report.

Send no email and run no notification script; publishing notifies automatically.
