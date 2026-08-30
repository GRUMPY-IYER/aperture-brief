#!/usr/bin/env python3
"""
The Aperture — static site builder.

Reads one day's editorial content (content/YYYY-MM-DD.json) and renders:
  index.html                 (front page, links archive/<date>.html)
  archive/YYYY-MM-DD.html    (permanent copy)

Everything mechanical lives here so the daily prompt never has to remember it:
dates, relative paths, archive-picker bounds, empty-section collapse,
wildlife filler placement, and the editorial guardrails in check().

Usage:
  python3 build.py 2026-08-29        build that edition
  python3 build.py                   build today's edition
  python3 build.py --check-only DATE validate without writing files
"""
import json, sys, re, random, datetime, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent
ARCHIVE_MIN = "2026-08-01"

# ---- editorial guardrails (mirrors EDITORIAL.md) ----------------------------
MAX_PER_OUTLET = 3            # across the whole edition
MAX_INDIA_ITEMS = 7           # india top + more combined
MAX_TOP_STORIES = 20          # excludes philosophy, bengal, travel, happy
DEDUPE_DAYS = 3               # don't reuse a URL from the last N editions
HARD_PAYWALL = ["nytimes.com", "wsj.com", "ft.com", "nature.com/articles",
                "economist.com", "variety.com", "hollywoodreporter.com",
                "theathletic.com", "theinformation.com"]
# URLs that are section fronts / tag pages rather than a specific article
HUB_PATTERNS = [r"/tag/", r"/topics?/$", r"/category/", r"wikipedia\.org",
                r"^https?://[^/]+/?$"]

# Sections whose JSON carries the top/more shape (drives validation coverage).
SECTIONS_WITH_COLS = ["politics", "india", "geo", "sports", "entertainment"]
# Of those, the ones rendered in the main column's two-column flow. Entertainment
# now lives in the side column, rendered flat like the tech sections, so it has
# no flow and no lede.
FLOW_SECTIONS = ["politics", "india", "geo", "sports"]


# ---- layout decisions -------------------------------------------------------
# The old code estimated rendered column heights to decide where to drop a
# filler photo. CSS now balances the columns itself, so none of that is needed:
# what is left is one editorial question the layout asks of each section.

MIN_ITEMS_FOR_LEDE = 4     # below this a section is too thin to carry a lede
SHOWCASE_COUNT = 5         # photographs in the From the Field strip
VISIBLE_AFTER_LEDE = 3     # stories shown before the "show more" fold
# Science is now its own section, separate from Philosophy. These kinds are
# expected in every edition, tagged per item as {"kind": "..."} in the JSON,
# so the desk can't quietly collapse back into consciousness studies.
REQUIRED_SCIENCE_KINDS = ["chemistry", "space"]


def pick_lede(s):
    """Which sections promote their first top story to full width.

    A lede needs a section with enough behind it; on a thin day a promoted
    middling story reads as overclaiming, so those sections stay flat.
    """
    out = {}
    for sid in FLOW_SECTIONS:
        sec = s.get(sid) or {}
        top, more = sec.get("top") or [], sec.get("more") or []
        out[sid] = bool(top) and (len(top) + len(more)) >= MIN_ITEMS_FOR_LEDE
    return out


def jpeg_size(path):
    """Width and height of a JPEG, using only the standard library.

    Walks the segment markers to the start-of-frame header, which carries the
    dimensions. Twenty lines instead of a Pillow dependency the build would
    otherwise have to install on every CI run.
    """
    with open(path, "rb") as f:
        if f.read(2) != b"\xff\xd8":
            raise ValueError(f"{path} is not a JPEG")
        while True:
            b = f.read(1)
            while b and b != b"\xff":            # scan to the next marker
                b = f.read(1)
            marker = f.read(1)
            while marker == b"\xff":             # skip fill bytes
                marker = f.read(1)
            if not marker:
                raise ValueError(f"no size header found in {path}")
            m = marker[0]
            # SOF0-SOF15 carry the frame size; C4/C8/CC are other tables.
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                f.read(3)                        # segment length + precision
                h = int.from_bytes(f.read(2), "big")
                w = int.from_bytes(f.read(2), "big")
                return w, h
            length = int.from_bytes(f.read(2), "big")
            f.seek(length - 2, 1)


def photo_meta(name):
    """Real pixel dimensions, so the page can reserve the right box.

    Emitting width/height lets the browser hold the correct space before the
    image loads (no layout shift) AND lets us size purely by width with
    height:auto — the photograph is never cropped to fit a slot.
    """
    w, h = jpeg_size(ROOT / "wildlife" / name)
    return {"file": name, "w": w, "h": h, "portrait": h > w}


def pick_showcase(date, wildlife, recent):
    """Photographs for the From the Field strip, seeded from the date.

    Seeded so a rebuild of the same edition is byte-identical, and ordered
    fresh-first so recently-published frames come round last rather than
    being excluded outright.
    """
    rng = random.Random("showcase-" + date)
    fresh = sorted(w for w in wildlife if w not in recent)
    stale = sorted(w for w in wildlife if w in recent)
    rng.shuffle(fresh); rng.shuffle(stale)
    pool = fresh + stale
    if not pool:
        return []
    return [photo_meta(pool[i % len(pool)])
            for i in range(min(SHOWCASE_COUNT, len(pool)))]


# ---- validation -------------------------------------------------------------
def iter_items(s):
    """Yield (bucket, item) for every story in the edition."""
    for sid in SECTIONS_WITH_COLS:
        sec = s.get(sid) or {}
        for it in sec.get("top") or []:
            yield f"{sid}.top", it
        for it in sec.get("more") or []:
            yield f"{sid}.more", it
    for key in ("bengal", "travel"):
        for it in s.get(key) or []:
            yield key, it
    if s.get("happy"):
        yield "happy", s["happy"]
    for it in s.get("tech_top") or []:
        yield "tech_top", it
    for it in s.get("tech_more") or []:
        yield "tech_more", it
    for it in s.get("science") or []:
        yield "science", it
    for it in s.get("philosophy") or []:
        yield "philosophy", it


def recent_urls(date, days=DEDUPE_DAYS):
    seen = {}
    d0 = datetime.date.fromisoformat(date)
    for n in range(1, days + 1):
        p = ROOT / "content" / f"{d0 - datetime.timedelta(days=n)}.json"
        if p.exists():
            prev = json.loads(p.read_text())
            for _, it in iter_items(prev.get("sections", {})):
                seen.setdefault(it.get("url"), str(p.stem))
    return seen


def check(date, s):
    errors, warnings = [], []
    # 1. structural completeness
    for bucket, it in iter_items(s):
        for field in ("headline", "url", "source", "blurb"):
            if not (it.get(field) or "").strip():
                errors.append(f"{bucket}: item missing '{field}' — {it.get('headline', '?')[:50]}")
        url = it.get("url", "")
        if url and not url.startswith("http"):
            errors.append(f"{bucket}: url is not absolute — {url}")
        for pat in HUB_PATTERNS:
            if url and re.search(pat, url):
                warnings.append(f"{bucket}: url looks like a hub/tag page, not an article — {url}")
                break
        for dom in HARD_PAYWALL:
            if dom in url:
                errors.append(f"{bucket}: hard-paywalled domain — {url}")
    # 2. source diversity
    tally = collections.Counter((it.get("source") or "?").strip().lower()
                                for _, it in iter_items(s))
    for src, n in tally.items():
        if n > MAX_PER_OUTLET:
            errors.append(f"source diversity: '{src}' used {n}x (cap {MAX_PER_OUTLET})")
    # 3. duplicate URLs within the edition
    urls = [it.get("url") for _, it in iter_items(s)]
    for u, n in collections.Counter(urls).items():
        if n > 1:
            errors.append(f"duplicate url used {n}x in this edition — {u}")
    # 4. repeats from recent editions
    prev = recent_urls(date)
    for bucket, it in iter_items(s):
        if it.get("url") in prev:
            errors.append(f"{bucket}: url already ran in {prev[it['url']]} — {it['url']}")
    # 5. caps
    india = s.get("india") or {}
    n_india = len(india.get("top") or []) + len(india.get("more") or [])
    if n_india > MAX_INDIA_ITEMS:
        errors.append(f"india has {n_india} items (cap {MAX_INDIA_ITEMS})")
    # The 20-top-story rule, now enforced rather than suggested. Counts the big
    # stories only (each section's `top` list plus Top Tech) — the shorter
    # `more` items, Bengal/Travel/Happy and Philosophy are outside it, as the
    # editorial rules have always said.
    n_top = sum(len((s.get(sid) or {}).get("top") or []) for sid in SECTIONS_WITH_COLS)
    n_top += len(s.get("tech_top") or [])
    if n_top > MAX_TOP_STORIES:
        errors.append(f"{n_top} top stories across the edition (cap {MAX_TOP_STORIES}) "
                      f"— drop the weakest, don't just move them to `more`")
    # 6. required shapes
    if len(s.get("travel") or []) != 2:
        warnings.append(f"travel has {len(s.get('travel') or [])} items (expected exactly 2)")
    if not s.get("happy"):
        warnings.append("no Happy Story")
    if not s.get("bengal"):
        warnings.append("no Bengal items")
    # Science must reach beyond brains and consciousness.
    kinds = {(i.get("kind") or "").lower() for i in (s.get("science") or [])}
    for k in REQUIRED_SCIENCE_KINDS:
        if k not in kinds:
            warnings.append(f"science: no item tagged kind=\"{k}\"")
    if not s.get("science"):
        warnings.append("no Science section — split out from Philosophy; the daily "
                        "prompt needs updating to fill it")
    return errors, warnings


# ---- render -----------------------------------------------------------------
def render(date, s, lede, showcase):
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                      trim_blocks=False, lstrip_blocks=False)
    tpl = env.get_template("aperture.html.j2")
    d = datetime.date.fromisoformat(date)
    ctx = dict(date=date,
               date_long=d.strftime("%A, %B %-d, %Y"),
               archive_min=ARCHIVE_MIN,
               s=s, lede=lede, showcase=showcase,
               visible_after_lede=VISIBLE_AFTER_LEDE)
    front = tpl.render(**ctx, icon_prefix="", archive_prefix="archive/")
    arch = tpl.render(**ctx, icon_prefix="../", archive_prefix="")
    return front, arch


def main():
    args = [a for a in sys.argv[1:]]
    check_only = "--check-only" in args
    args = [a for a in args if not a.startswith("--")]
    date = args[0] if args else datetime.date.today().isoformat()

    src = ROOT / "content" / f"{date}.json"
    if not src.exists():
        sys.exit(f"ERROR: no content file at content/{date}.json")
    data = json.loads(src.read_text())
    if data.get("date") != date:
        sys.exit(f"ERROR: content/{date}.json has date field '{data.get('date')}'")
    s = data.get("sections", {})

    errors, warnings = check(date, s)
    for w in warnings:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    if errors:
        sys.exit(f"\n{len(errors)} validation error(s) — fix content/{date}.json and re-run.")
    if check_only:
        print(f"\nOK — {date} passes validation ({len(warnings)} warning(s)).")
        return

    wildlife = sorted(p.name for p in (ROOT / "wildlife").glob("*.jpeg"))
    recent = set()
    for n in (1, 2):
        p = ROOT / "archive" / f"{datetime.date.fromisoformat(date) - datetime.timedelta(days=n)}.html"
        if p.exists():
            recent |= set(re.findall(r"wildlife/([^\"']+)", p.read_text()))
    lede = pick_lede(s)
    showcase = pick_showcase(date, wildlife, recent)

    front, arch = render(date, s, lede, showcase)
    (ROOT / "index.html").write_text(front)
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "archive" / f"{date}.html").write_text(arch)

    print(f"\nBuilt {date}")
    for sid in FLOW_SECTIONS:
        sec = s.get(sid) or {}
        n = len(sec.get("top") or []) + len(sec.get("more") or [])
        print(f"  {sid:<14} {n:>2} stories   {'lede promoted' if lede.get(sid) else 'flat (thin section)'}")
    ent = s.get("entertainment") or {}
    print(f"  entertainment  {len(ent.get('top') or []) + len(ent.get('more') or []):>2} stories   side column")
    print(f"  showcase       {len(showcase)} photographs")
    print(f"  index.html + archive/{date}.html written")


if __name__ == "__main__":
    main()
