# 001 — Where saved stories live

**Status:** accepted · 30 August 2026
**Stage:** 1, Saving what matters

## The decision

Saved stories live in the reader's own browser (`localStorage`), not on a server.
The stored shape is designed so that stage 4 can sync it without a data migration.

## Context

Requirement 4 asks that "depending on user accessing the news site, the side panel
shows their saved stories". This needs care, because **the site has no way to know
who is reading it.** It is static HTML on GitHub Pages: no accounts, no login, no
server that could recognise anyone.

What it does have is the reader toggle in the dateline row, added in stage 0 for
section ordering. That toggle is a **label, not an identity**. It records which of
you said you were reading; anyone using that browser can switch it.

For two people in one household on their own devices, a label is sufficient — you
are not defending against each other. It is worth being precise that this is a
convenience, not access control, so nobody later assumes a privacy guarantee that
was never built.

## Options considered

**A. Browser storage (chosen).** Saves live in `localStorage`, keyed by reader.
Ships immediately, needs no server, no account, no vendor, and keeps the property
that every published page is a plain file that works forever. Cost: a save made on
the laptop does not appear on the phone, and clearing site data loses the list.

**B. A backend now.** A small API and database, with saves keyed to a reader
identity. Solves cross-device immediately. Cost: a server to run and maintain, an
identity model to design, a new failure mode where the site's features break when
something is down, and it front-loads stage 4's work into stage 1.

**C. Browser storage now, sync later (the shape we actually took).** Option A, but
with the stored data shaped for option B from the start.

## Why

At a cap of ten stories per reader, the data is tiny and the value of syncing it is
real but small — you will mostly save on the device you are reading on. A backend
bought now would be maintained for months before it is needed.

The one thing that would make deferring expensive is a migration, so we removed
that cost: every saved story carries a `saved_at` timestamp it does not currently
need. Timestamps are what a sync needs to resolve two devices disagreeing — last
write wins — and adding the field now costs nothing. When stage 4 arrives, the
existing lists upload as they are.

**The general point, worth remembering:** defer the infrastructure, but shape the
data as if you had already built it. Deferring is cheap; migrating is not.

## Consequences

- Saves are per-browser. Laptop and phone keep separate lists until stage 4.
- Clearing site data loses saves. Export exists so a list can be kept deliberately.
- The reader toggle is the identity. It is a label; treat it as one.
- Both readers' lists live in the same browser. Switching the toggle on a shared
  device shows the other person's saves — allowed deliberately, since real
  separation needs stage 4 and pretending otherwise would be theatre.
- `localStorage` throws in private windows and when site data is blocked, so every
  read and write is wrapped; the page works without saving rather than breaking.

## Also settled in grooming

- **At the cap, refuse and say so.** The eleventh save is declined with an
  explanation rather than silently dropping the oldest. The cap exists to force
  triage; deleting something you deliberately kept would defeat it.
- **Today's edition onward only.** The thirty archived editions do not get save
  buttons in this stage. Backfilling them is real work that belongs with stage 2,
  where the same extraction also produces source usage counts.
