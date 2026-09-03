# 002 — Getting photographs from the archive to the page

**Status:** accepted · 30 August 2026, parameters settled 1 September 2026
**Stage:** 2, The Photography Desk (moved ahead of the Source Register on 31 August)
**Supersedes:** an earlier draft of this record that designed around the Synology
Photos API. That draft assumed the NAS managed the library. It does not — the NAS
is file storage; **Lightroom Classic is the library.** Recorded here because the
wrong assumption cost an hour and the correction is the useful part.

## The problem

Ten thousand photographs, managed in Lightroom Classic on the Mac, stored in a
folder on the Synology. The site publishes from the cloud at 4am. We need to
choose frames, get web-sized copies to the page, carry captions with them, and
never publish a location.

## What we are NOT doing, and why

- **Synology Photos API.** Real and capable, but it indexes a library Lightroom
  owns. Two catalogues of the same photographs is a synchronisation problem
  nobody asked for.
- **QuickConnect.** A relay built for Synology's own apps, not a stable API.
- **Backblaze B2.** The existing job is Hyper Backup ("S3 backup 1"), which writes
  a sealed, versioned archive only Synology's restore tool can read. Excellent
  backup, useless as a source. **Leave it alone** — it is the disaster-recovery
  copy of the whole archive.
- **Scripting on the NAS.** Unnecessary once Lightroom is the source.
- **The Describe modal.** Built to collect metadata that Lightroom already holds.

Each of these was a reasonable answer to "how do we reach the NAS". That was the
wrong question. The library is not on the NAS; the pixels are.

## What we are doing

Lightroom Classic has a **Hard Drive publish service** built for exactly this. It
maintains a published collection, tracks which photographs are new, which have
been edited since they were last exported, and which have been removed, and
re-exports the changed ones on one click.

1. **A publish service** in Lightroom — Hard Drive, named Aperture — exporting
   straight into `wildlife/` in the repo folder.
2. **A published collection**, "Featured". Ganges drags keepers in as they
   happen. This is the selection mechanism: no triage of ten thousand frames,
   just a collection that grows.
3. **Export settings** carry the rest:
   - **1600px on the long edge, quality 70.** Settled by measurement, not taste: the
     page is 1180px wide, the featured frame occupies at most ~700 CSS px of it, and
     the showcase thumbnails a third of that. 1600px covers the largest of those at
     2x retina with headroom. Nothing on the page can render more detail, so a bigger
     export buys file size and nothing else.
   - **Remove Location Info ticked**, which is how GPS never reaches the page
   - **a small watermark**, since the same exports are intended to feed
     grumpyiyer.com later, where they will be public
   - metadata included, so Title, Caption and Keywords travel inside the JPEG
4. **Hit Publish.** Lightroom writes the files.
5. **Commit in GitHub Desktop**, and CI publishes as it already does.

## What this fixes

**Captions come from Lightroom.** Title, Caption and Keywords are written into the
exported JPEG as IPTC. Ganges already captions and keywords there, on the machine
where he culls. The build reads the file rather than a parallel record he has to
maintain. `photos.json` shrinks to a small overlay holding only what Lightroom has
no field for — the researched natural-history note.

**GPS becomes a checkbox** rather than a script, applied at export, before the
file exists in the repo. Strip at the source, not after the fact.

**Resizing is Lightroom's job**, which it does better than any script we would
write, and with his own sharpening.

**Nothing new runs at 4am.** The daily job keeps reading files that are simply
there. Publishing from Lightroom is a deliberate act — done when he has new work,
not on a schedule — so the sleeping-laptop problem never applies to it.

## Trade-offs, honestly

- **Publishing requires the Mac and Lightroom open.** Acceptable: it is a
  photographer choosing what to show, not an automated step.
- **Photographs live in the git repo**, growing it slowly. Fine for a rotating
  pool of tens; wrong at several hundred. If the Featured collection grows past
  roughly 200 frames, revisit and move hosting to object storage — at which point
  a Cloud Sync task to B2 becomes worth its complexity.
- **Two publish steps** — Lightroom publishes, then git commits. A watcher could
  collapse these later; not worth it until the manual version proves annoying.

## Open questions

1. Export size and quality — 1600px/70 is a starting guess, his call.
2. Whether to also carry his watermark through the export, or let the byline do
   that work now that it matches.
3. How the researched note gets attached: an overlay file keyed by filename, or a
   Lightroom field we borrow for the purpose.

## Settled on 1 September 2026

Three parameters were guesses in the original record. They are now decided.

**Size: 1600px long edge, quality 70.** See the export settings above — this was
measured against the template rather than chosen by feel.

**Watermark: yes, small.** Redundant on a private site read by two people, and the
section already carries a byline. Kept anyway because these exports are meant to become
the source for grumpyiyer.com, and re-exporting a whole collection later to add a
watermark is worse than carrying one now.

**Locations: broad region only.** A caption may name a state, a country, or a large
reserve — "Kawal Tiger Reserve", "Western Ghats". It may never name a hide, a waterhole,
a nest or a den. The distinction is not privacy, it is animal safety: a precise location
is actionable information for someone who means harm, and the photographer is often the
only person who knows it.

**This rule applies to filenames as well as captions.** Filenames are published in a
public repository and are read by anyone who opens the page source. The existing archive
already carries `200725-Kawal-GBS_3098.jpeg` — a reserve, so within the rule. Anything
more specific must be renamed on export, which the publish service can do with a rename
token. GPS stripping does not help here; the filename is not metadata.

## The state this replaces

All 28 photographs currently in `wildlife/` have **empty `subject`, `where`, `note` and
`research`** in `photos.json`. Only the camera fields are populated, because those were
read from EXIF. So the page has never actually been captioned — the frames run under a
generic alt text.

This makes the re-export more than a file-size fix. It is the first time captions arrive,
and they arrive from Lightroom's Title, Caption and Keyword fields rather than from a
JSON file maintained by hand. `photos.json` shrinks to an overlay holding only the
researched natural-history note, which has no Lightroom equivalent.
