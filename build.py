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

SECTIONS_WITH_COLS = ["politics", "india", "geo", "sports", "entertainment"]


# ---- height estimation ------------------------------------------------------
# Approximates rendered pixel height so we can tell when a more-col will leave
# a white gap. Rough by design: we only need "is this column much shorter?".
def _lines(text, chars_per_line):
    return max(1, -(-len(text or "") // chars_per_line))

def est_top(it):
    h = 26                                    # margins + divider
    h += 15                                   # source line
    h += _lines(it.get("headline"), 39) * 21  # 17px headline
    h += _lines(it.get("blurb"), 52) * 20     # 13.5px blurb
    if it.get("pm_note"):
        h += _lines(it["pm_note"], 55) * 19
    return h

def est_more(it):
    chars = 36 if it.get("image") else 46
    h = 11
    h += 13
    h += _lines(it.get("headline"), chars) * 18
    h += _lines(it.get("blurb"), chars + 8) * 16
    return max(h, 84 if it.get("image") else h)

def est_apu(it):
    chars = 34 if it.get("image") else 44
    h = 10 + 13
    h += _lines(it.get("headline"), chars) * 17
    h += _lines(it.get("blurb"), chars + 8) * 15
    return max(h, 84 if it.get("image") else h)


def pick_fillers(s, wildlife, recent_files):
    """Return {section_id: filename} for more-cols that will look short."""
    pool = [w for w in wildlife if w not in recent_files] or list(wildlife)
    random.shuffle(pool)
    fill, used = {}, 0
    plans = []
    for sid in SECTIONS_WITH_COLS:
        sec = s.get(sid) or {}
        top, more = sec.get("top") or [], sec.get("more") or []
        if not more:
            continue                       # single column: never fill
        left = sum(est_top(i) for i in top)
        right = sum(est_more(i) for i in more)
        if sid == "india":                 # bengal/travel/happy continue this column
            right += 26
            right += sum(est_apu(i) for i in s.get("bengal") or [])
            right += sum(est_apu(i) for i in s.get("travel") or [])
            if s.get("happy"):
                right += est_apu(s["happy"]) + 20
        plans.append((sid, left, right, left - right))
    for sid, left, right, gap in plans:
        key = "apu" if sid == "india" else sid
        if gap > 150 and used < len(pool):
            fill[key] = pool[used]; used += 1
    return fill, plans


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
    n_top = sum(1 for b, _ in iter_items(s)
                if b.endswith(".top") or b.endswith(".more") or b == "tech_top" or b == "tech_more")
    if n_top >= MAX_TOP_STORIES + 10:
        warnings.append(f"{n_top} counted stories — sanity-check against the 20-top-story rule")
    # 6. required shapes
    if len(s.get("travel") or []) != 2:
        warnings.append(f"travel has {len(s.get('travel') or [])} items (expected exactly 2)")
    if not s.get("happy"):
        warnings.append("no Happy Story")
    if not s.get("bengal"):
        warnings.append("no Bengal items")
    return errors, warnings


# ---- render -----------------------------------------------------------------
def render(date, s, fill, wildlife):
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                      trim_blocks=False, lstrip_blocks=False)
    tpl = env.get_template("aperture.html.j2")
    d = datetime.date.fromisoformat(date)
    ctx = dict(date=date,
               date_long=d.strftime("%A, %B %-d, %Y"),
               archive_min=ARCHIVE_MIN,
               s=s, fill=fill)
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
    fill, plans = pick_fillers(s, wildlife, recent)

    front, arch = render(date, s, fill, wildlife)
    (ROOT / "index.html").write_text(front)
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "archive" / f"{date}.html").write_text(arch)

    print(f"\nBuilt {date}")
    for sid, left, right, gap in plans:
        mark = "filler added" if fill.get("apu" if sid == "india" else sid) else "ok"
        print(f"  {sid:<14} left~{left:>4}px  right~{right:>4}px  gap {gap:>5}px  {mark}")
    print(f"  index.html + archive/{date}.html written")


if __name__ == "__main__":
    main()
