# The Aperture — project context

A daily newspaper-style news brief, published to https://aperture.grumpyiyer.com
via GitHub Pages. Personal project of Ganges Bhardwaj (wildlife photographer,
brand "Grumpy Iyer"; product manager, not a professional developer).

**When explaining changes here, favour the "why" over the "how". Name the concept
being applied (data contract, idempotency, least privilege) rather than only the
syntax. Show diffs before applying them.**

## Working agreement

**The daily routine publishes editions, and that is not an exception to be
weighed — it is the whole job.** It writes `content/<date>.json`, commits it, and
runs `git push origin HEAD:main`. Nothing in this file forbids that, and a run
that declines to push because of something it read here has failed.

Everything else is Ganges's to push. When changing *source* — `build.py`, the
template, documentation, workflows, decision records — make the edit locally, say
plainly what changed and why, and leave the commit to him. No API writes, no
pushing source on his behalf.

The distinction is content versus source, not git versus not-git. Editions are
published by machine; the machinery is changed by hand.

## Architecture — content and presentation are separate

    content/YYYY-MM-DD.json   <- editorial content only. No HTML.
    templates/aperture.html.j2 <- ALL layout, CSS, section titles and order
    build.py                   <- renders one into the other, and validates
    index.html                 <- GENERATED. never hand-edit.
    archive/YYYY-MM-DD.html    <- GENERATED. never hand-edit.

Daily flow: a Claude Code **routine** (claude.ai/code/routines, 4am local,
timezone-aware) researches the news, writes `content/<date>.json`, and commits and
pushes it with plain git. The repo is attached to the routine, so the git proxy
supplies a scoped credential for the length of the run — there is no long-lived
token anywhere in the pipeline. That push triggers `.github/workflows/build.yml`,
which runs `build.py` and commits the rendered HTML. `.github/workflows/notify.yml`
then sends a web push.

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
- **No credential belongs in this pipeline.** The routine borrows a scoped git
  credential for the length of one run. Never reintroduce a personal access token,
  and never put one in a task prompt — a prompt is configuration, readable by any
  session that lists it.
- The routine still cannot modify `.github/workflows/**` on its own; workflow files
  are committed by hand. Keep it that way — automation should not be able to rewrite
  its own CI.
- **A green run status means the session exited cleanly, not that anything
  published.** Verify against `origin/main`, never against run status. The 1 Sep
  failure looked green and shipped nothing.

## Commands

    python3 preview.py                  # look at the site locally, and edit it
    python3 build.py                    # build today's edition
    python3 build.py 2026-08-29         # build a specific date
    python3 build.py --check-only DATE  # validate without writing

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

## Do not run git in this folder from a Cowork session

Not even read-only commands. `git status`, `git diff` and `git ls-files` all take
`.git/index.lock` while they refresh the index — and this folder is mounted into
Cowork sessions with deletes forbidden, so the lock is created and then cannot be
removed. The next commit from GitHub Desktop or the terminal fails with "a lock
file already exists".

Read the working tree with ordinary file tools instead: `ls`, `cat`, `find`,
`diff` against a saved copy. To compare against what is published, fetch the file
from the GitHub API rather than asking the local git.

Clearing a stranded lock is Ganges's to do, in his own terminal:

    find .git -name '*.lock' -delete

## Known gotchas

- This folder is also mounted into Claude Cowork sessions, which **cannot delete
  files**. Automated git in this folder therefore strands `.git/*.lock` and
  `objects/pack/*.keep` files. That is why the daily job never touches this folder:
  it runs in the cloud against its own fresh clone. Working here in Claude Code
  (normal Terminal access) is fine.
- Wildlife photos in `wildlife/` are the owner's own work. Caption them generically
  ("From the archive") — never assert a species or location that isn't verified.
- **`.gitignore` does not apply to files git is already tracking.** `.DS_Store` was
  listed in `.gitignore` and tracked on origin at the same time, so it reappeared in
  every commit dialog no matter how often it was unchecked. Untracking is a separate
  act: `git rm --cached <file>`. If an ignored file keeps showing up as modified,
  it is tracked — check with `git ls-files <file>` rather than re-editing `.gitignore`.
- **`index.html` and `archive/*.html` are tracked but CI-owned.** A local `build.py` or
  `preview.py` run leaves them modified in the working tree. Discard those changes
  rather than committing them; the rendered HTML on `main` should only ever come from
  the build workflow, or the two will fight.

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

- The Photography Desk: source is a Lightroom Classic publish service, not the NAS.
  See `decisions/002-photo-source.md`. Includes re-exporting the 28 photos already
  live at web size — one is 21.5MB and is being served to readers.
