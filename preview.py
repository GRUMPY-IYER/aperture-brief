#!/usr/bin/env python3
"""
Look at the site locally, and edit it while you are there.

    python3 preview.py

Opens the browser at today's edition. Describe a photograph, hit Save, and it
writes photos.json, rebuilds, and reloads — no copying, no second step.

This is how to view the site on your own machine. Nothing here is ever
deployed: the published site stays plain static files with no server anywhere.
The page checks how it is being served and offers Save or Copy accordingly.

Binds to 127.0.0.1 only, so nothing outside this machine can reach it.
Ctrl+C to stop.
"""
import http.server, json, pathlib, socketserver, subprocess, sys, datetime
import threading, webbrowser, errno

ROOT = pathlib.Path(__file__).resolve().parent
PORT = 8765
ALLOWED = {"subject", "where", "note", "research"}     # never the EXIF fields


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        pass                                            # quiet; we print our own

    def _json(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.path != "/save-photo":
            return self._json(404, {"error": "unknown endpoint"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
            name = payload.get("file")
            fields = payload.get("fields") or {}
        except Exception as e:
            return self._json(400, {"error": f"could not read that: {e}"})

        store = ROOT / "photos.json"
        doc = json.loads(store.read_text())
        entry = doc.get("photos", {}).get(name)
        if entry is None:
            return self._json(404, {"error": f"{name} is not in photos.json"})

        for k, v in fields.items():
            if k in ALLOWED:                            # EXIF stays as read
                entry[k] = str(v).strip()
        store.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

        today = datetime.date.today().isoformat()
        r = subprocess.run([sys.executable, "build.py", today],
                           cwd=str(ROOT), capture_output=True, text=True)
        if r.returncode != 0:
            # The words are saved either way; only the rebuild failed.
            return self._json(200, {"saved": True, "rebuilt": False,
                                    "detail": (r.stdout + r.stderr).strip()[-400:]})
        print(f"  saved {name} and rebuilt {today}")
        return self._json(200, {"saved": True, "rebuilt": True})


def serve():
    """Take the first free port from 8765 upward, so a stale server from an
    earlier run is an inconvenience rather than a crash."""
    socketserver.TCPServer.allow_reuse_address = True
    for port in range(PORT, PORT + 12):
        try:
            return socketserver.TCPServer(("127.0.0.1", port), Handler), port
        except OSError as e:
            if e.errno not in (errno.EADDRINUSE, 48):
                raise
    sys.exit(f"  No free port between {PORT} and {PORT + 11}.")


if __name__ == "__main__":
    # Build first, so the browser opens on something current rather than
    # whatever the last run happened to leave behind.
    today = datetime.date.today().isoformat()
    r = subprocess.run([sys.executable, "build.py", today], cwd=str(ROOT),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  (today's edition would not build; showing the last one that did)")
        print("  " + (r.stdout + r.stderr).strip().splitlines()[-1][:120])

    srv, port = serve()
    url = f"http://localhost:{port}/"
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    with srv:
        print(f"  The Aperture is at {url} — opening it now.")
        print( "  Describe a photograph and hit Save; it writes and reloads itself.")
        print( "  Ctrl+C to stop.")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopped")
