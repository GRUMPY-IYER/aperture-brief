#!/usr/bin/env python3
"""
Push one day's content JSON to GitHub via the Contents API.

Why an API call instead of `git push`: this folder is mounted read-only for
deletes, and every `git commit` must delete .git/index.lock. So local git can
never complete here. One HTTPS request has no such problem — and it is what
lets the daily task stay tiny.

Usage: python3 push_content.py [YYYY-MM-DD]
"""
import base64, datetime, json, pathlib, sys, urllib.request, urllib.error

ROOT  = pathlib.Path(__file__).resolve().parent
REPO  = "GRUMPY-IYER/aperture-brief"
BRANCH = "main"

def api(method, path, token, payload=None):
    req = urllib.request.Request(
        f"https://api.github.com{path}", method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "aperture-publisher"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

def put_file(local: pathlib.Path, remote: str, token, message):
    status, existing = api("GET", f"/repos/{REPO}/contents/{remote}?ref={BRANCH}", token)
    payload = {"message": message, "branch": BRANCH,
               "content": base64.b64encode(local.read_bytes()).decode()}
    if status == 200 and isinstance(existing, dict) and existing.get("sha"):
        payload["sha"] = existing["sha"]          # update in place
    status, body = api("PUT", f"/repos/{REPO}/contents/{remote}", token, payload)
    if status not in (200, 201):
        sys.exit(f"ERROR pushing {remote}: HTTP {status} — {body.get('message')}")
    return body["commit"]["sha"][:7], ("updated" if "sha" in payload else "created")

def main():
    token_file = ROOT / ".aperture-token"
    if not token_file.exists():
        sys.exit("ERROR: .aperture-token missing")
    token = token_file.read_text().strip()
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    local = ROOT / "content" / f"{date}.json"
    if not local.exists():
        sys.exit(f"ERROR: content/{date}.json not found")
    sha, action = put_file(local, f"content/{date}.json", token, f"Content for {date}")
    print(f"  {action} content/{date}.json — commit {sha}")
    print(f"  GitHub Actions will now build and publish the edition.")

if __name__ == "__main__":
    main()
