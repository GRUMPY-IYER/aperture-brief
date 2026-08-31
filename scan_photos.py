#!/usr/bin/env python3
"""
Read camera settings out of the photographs and merge them into photos.json.

Run this by hand when you add photographs — not on every build. The settings
never change, so re-reading them daily would be waste, and it keeps the daily
build free of an image library it would otherwise have to install in CI.

It NEVER overwrites anything you wrote. Your subject, place, note and research
are yours; this only fills the technical fields and only when they are empty.

GPS is deliberately not read. Publishing where an animal was photographed can
put it at risk, and the safest way to not publish a coordinate is to never
carry it into the file in the first place.

Usage:  python3 scan_photos.py
"""
import json, pathlib, re, sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parent
YOURS = ("subject", "where", "note", "research")   # never touched


def shutter(sec):
    """0.008 -> '1/125'. Photographers read fractions, not decimals."""
    if not sec:
        return ""
    sec = float(sec)
    if sec >= 1:
        return f"{sec:g}s"
    return "1/" + str(round(1 / sec))


def read_exif(path):
    try:
        from PIL import Image, ExifTags
    except ImportError:
        sys.exit("This needs Pillow: pip3 install pillow --break-system-packages")
    with Image.open(path) as im:
        ex = im.getexif()
        tags = {ExifTags.TAGS.get(k, k): v for k, v in ex.items()}
        try:
            for k, v in ex.get_ifd(0x8769).items():      # the EXIF sub-block
                tags[ExifTags.TAGS.get(k, k)] = v
        except Exception:
            pass
    out = {}
    if tags.get("ISOSpeedRatings"):
        out["iso"] = str(tags["ISOSpeedRatings"])
    if tags.get("FNumber"):
        out["aperture"] = f"f/{float(tags['FNumber']):g}".replace("f/6.3000002", "f/6.3")
    if tags.get("ExposureTime"):
        out["shutter"] = shutter(tags["ExposureTime"])
    if tags.get("FocalLength"):
        out["focal"] = f"{float(tags['FocalLength']):g}mm"
    if tags.get("LensModel"):
        out["lens"] = str(tags["LensModel"]).strip()
    # Camera makers write the brand into BOTH Make and Model, so naively joining
    # them gives "Nikon Nikon Z 8". Use Model, and only prepend Make when Model
    # does not already carry the brand.
    make = str(tags.get("Make", "")).strip().split()[0].title() if tags.get("Make") else ""
    model = " ".join(str(tags.get("Model", "")).split()).strip()
    if model:
        pretty = model if not make or model.upper().startswith(make.upper()) else f"{make} {model}"
        out["camera"] = re.sub(r"\bNIKON\b", "Nikon", pretty, flags=re.I)
    elif make:
        out["camera"] = make
    dt = str(tags.get("DateTimeOriginal") or "")
    if dt[:4].isdigit():
        out["taken"] = dt[:10].replace(":", "-")
        out["year"] = dt[:4]
    # A caption, if the camera or your editor wrote one. Usually absent.
    for k in ("ImageDescription", "XPComment"):
        v = tags.get(k)
        if isinstance(v, bytes):
            v = v.decode("utf-16-le", "ignore")
        if v and str(v).strip():
            out["caption"] = str(v).strip().strip("\x00")
            break
    return out


def strip_gps(path):
    """Remove the GPS block, leaving the picture itself byte-identical.

    piexif rewrites only the metadata segment. Do NOT do this by loading the
    image and re-saving it: that decodes and re-encodes the JPEG and costs a
    generation of quality, even with quality="keep".
    """
    try:
        import piexif
    except ImportError:
        return None                       # nothing removed; caller warns
    try:
        ex = piexif.load(str(path))
    except Exception:
        return False
    if not ex.get("GPS"):
        return False
    ex["GPS"] = {}
    piexif.insert(piexif.dump(ex), str(path))
    return True


def main():
    store = ROOT / "photos.json"
    doc = json.loads(store.read_text()) if store.exists() else {"photos": {}}
    photos = doc.setdefault("photos", {})
    added = updated = 0

    for p in sorted((ROOT / "wildlife").glob("*.jp*g")):
        entry = photos.get(p.name)
        if entry is None:
            entry = photos[p.name] = {"subject": "", "where": "", "note": "", "research": ""}
            added += 1
        for k, v in read_exif(p).items():
            if k in YOURS:
                continue                       # your words are never overwritten
            if not (entry.get(k) or "").strip():
                entry[k] = v
                updated += 1
        for k in YOURS:
            entry.setdefault(k, "")

    # Location never reaches the published site. Strip it at the source.
    cleaned, no_tool = 0, False
    for p in sorted((ROOT / "wildlife").glob("*.jp*g")):
        r = strip_gps(p)
        if r is None:
            no_tool = True
            break
        cleaned += 1 if r else 0
    if no_tool:
        print("  WARNING: piexif not installed — GPS was not checked or removed.")
        print("           pip3 install piexif --break-system-packages")
    elif cleaned:
        print(f"  {cleaned} photographs had GPS removed")

    store.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"  {len(photos)} photographs · {added} new · {updated} technical fields filled")
    blank = [n for n, e in photos.items() if not (e.get("subject") or "").strip()]
    if blank:
        print(f"  {len(blank)} still need a subject from you:")
        for n in blank:
            print(f"      {n}")


if __name__ == "__main__":
    main()
