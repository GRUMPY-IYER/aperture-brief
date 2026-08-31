# 002 — Getting photographs from the archive to the page

**Status:** proposed · 30 August 2026
**Stage:** 3, The Photography Desk
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
   - resize to about 1600px on the long edge, quality around 70 — web-sized
   - **Remove Location Info ticked**, which is how GPS never reaches the page
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
