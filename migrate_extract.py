#!/usr/bin/env python3
"""ONE-TIME migration: turn an existing hand-written edition into content JSON."""
import sys, json, re, pathlib
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent

def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""

def item(div, blurb_sel):
    a = div.find("a", href=True)
    src = div.select_one(".source")
    src_txt = txt(src)
    inv = bool(src and src.select_one(".investigative-flag"))
    if inv:
        src_txt = re.sub(r"\s*Investigative\s*$", "", src_txt, flags=re.I).strip()
    img = div.find("img")
    out = {"headline": txt(a), "url": a["href"] if a else "",
           "source": src_txt, "blurb": txt(div.select_one(blurb_sel))}
    if img and img.get("src"):
        out["image"] = img["src"]
    if inv:
        out["investigative"] = True
    pm = div.select_one(".pm-note")
    if pm:
        out["pm_note"] = re.sub(r"^Why it matters for you:\s*", "", txt(pm))
    return out

def tops(sec):   return [item(d, ".blurb") for d in sec.select(".top-item")]
def mores(sec):  return [item(d, "p") for d in sec.select(".more-item")]
def primers(sec):
    return [{"term": txt(p.select_one(".term")), "text": txt(p.find("p"))}
            for p in sec.select(".primer-item")]

def main(path, date):
    soup = BeautifulSoup(pathlib.Path(path).read_text(), "html.parser")
    main_secs = soup.select_one(".main-col").find_all("section", recursive=False)
    side_secs = soup.select_one(".side-col").find_all("section", recursive=False)
    by = {s.get("class")[0]: s for s in main_secs}
    s = {}
    for key, cls in [("politics","politics"),("geo","geo"),("sports","sports"),("entertainment","entertainment")]:
        sec = by.get(cls)
        s[key] = {"top": tops(sec) if sec else [], "more": mores(sec) if sec else []}
    apu = by.get("apu-corner-section")
    s["india"] = {"top": tops(apu), "more": mores(apu)}
    # apu-items are grouped by the .apu-sub label that precedes them
    bucket, groups = None, {"Bengal": [], "Travel": [], "Happy": []}
    for el in apu.select(".apu-corner *"):
        cls = el.get("class") or []
        if "apu-sub" in cls:
            t = txt(el).lower()
            bucket = "Bengal" if "bengal" in t else "Travel" if "travel" in t else "Happy" if "happy" in t else None
        elif "apu-item" in cls and bucket:
            groups[bucket].append(item(el, "p"))
    s["bengal"], s["travel"] = groups["Bengal"], groups["Travel"]
    s["happy"] = groups["Happy"][0] if groups["Happy"] else None
    # side column, in document order
    s["tech_top"]  = tops(side_secs[0])
    s["tech_more"] = mores(side_secs[1])
    s["tech_101"]  = primers(side_secs[2])
    s["philosophy"]     = tops(side_secs[3])
    s["philosophy_101"] = primers(side_secs[4])
    out = ROOT / "content" / f"{date}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"date": date, "sections": s}, indent=2, ensure_ascii=False))
    n = sum(len(v) if isinstance(v, list) else len(v.get("top",[]))+len(v.get("more",[])) if isinstance(v, dict) else 1
            for v in s.values() if v)
    print(f"wrote {out.relative_to(ROOT)} — {out.stat().st_size} bytes, ~{n} items")

main(sys.argv[1], sys.argv[2])
