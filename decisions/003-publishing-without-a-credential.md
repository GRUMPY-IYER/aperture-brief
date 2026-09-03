# 003 — Publishing without a credential

**Status:** accepted · 1 September 2026
**Stage:** 0, revisited
**Supersedes:** the token-and-API publish path described in 002's era — `push_content.py`
and `.aperture-token`, both now deleted.

## The problem

The daily job stopped publishing. On 31 August and again on 1 September it researched
the news, built a valid edition, and failed at the last step with HTTP 403. The 1
September run is the instructive one: it reported **SUCCEEDED** after fourteen minutes
and shipped nothing.

## The wrong diagnosis, and why it was wrong

The first investigation concluded that the sandbox blocks all calls to
`api.github.com` as a matter of network policy, and proposed widening an
allowed-domains list. That was read out of the documentation. It was wrong, and it
sent us after a setting that could never have worked.

One command settled it:

    git clone https://github.com/GRUMPY-IYER/aperture-brief.git   # works
    git push --dry-run                                            # 403

    remote: access denied by the git proxy: GRUMPY-IYER/aperture-brief is not in this
    session's authorized repository set, so the proxy will not inject a credential for
    it. To fix, add the repository to the session's sources.

Reads are fine. Nothing about GitHub is blocked at the network layer. Every git *write*
from a cloud session goes through a proxy that **supplies the credential itself**, and
only for repositories in the session's authorized set. A personal access token handed in
by the caller is ignored, because the proxy never asks the caller for one.

**The lesson worth keeping: a documented behaviour is a claim; the stored state is
evidence.** Two days were lost to reading docs instead of running one command.

## What we are NOT doing

- **A network allowed-domains entry.** The request is not refused for where it is going.
  It is refused for which repository it names. No domain list can change that.
- **A personal access token, in any form.** It cannot work, and it was making things
  worse: the live token sat in plaintext inside the scheduled task's own prompt, where
  `list_triggers` returned it in full to any session that looked.
- **Running the job on the Mac.** That reintroduces exactly the sleeping-laptop
  dependency stage 0 existed to remove.
- **A Cowork scheduled task at all.** These cannot hold a repository. They do not appear
  at `claude.ai/code/routines` and expose no repository picker. This was the discovery
  that forced the rebuild.

## What we are doing

A Claude Code **routine** at `claude.ai/code/routines`, with
`GRUMPY-IYER/aperture-brief` attached to it. Each run begins with a fresh clone and
credentials the proxy injects for the length of that run. Publishing is now three
ordinary commands:

    git add content/<date>.json
    git commit -m "Content for <date>"
    git push origin HEAD:main

Then it verifies, which is the part that matters:

    git fetch origin && git log origin/main -1 --name-only

## What this fixes

**Least privilege, properly.** There is no long-lived credential anywhere in the
pipeline. Nothing to leak, rotate, or leave in a prompt. The old PAT is deleted.

**Silent failure becomes loud failure.** The prompt now states that a run ending without
a confirmed push has FAILED however cleanly the session exits. A green run status means
the session did not crash — it is not evidence that anything published. `watchdog.yml`
remains the backstop, filing an issue at 12:00 UTC when the day's content is absent.

**One fewer moving part.** `push_content.py` is gone. The publish step is the same git
anyone would type by hand.

## Trade-offs, honestly

- **The job moved to a different product surface.** Routines and Cowork scheduled tasks
  are separate systems with separate configuration. Anything that referenced the old task
  by name broke — including the November daylight-saving task, which had to be rewritten.
- **Push targets `main` directly.** Accepted because Ganges is `main`'s only human author
  and the branch is unprotected. A routine's instinct is to push to a `claude/`-prefixed
  branch, which would publish nothing while appearing to succeed, so the prompt forbids it
  explicitly.
- **Daylight saving is unresolved, not solved.** The docs say routine schedules are
  timezone-aware. The stored trigger says `0 8 * * *` with no timezone field. Rather than
  believe either, a one-off task on 1 November checks what the next run actually resolves
  to in New York and corrects it only if it drifted. See the runbook.
