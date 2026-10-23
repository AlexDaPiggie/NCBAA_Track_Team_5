"""Serve the local CrewPilot demo page and read-only plan data."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DATA = ROOT / "data" / "processed"
APPROVAL_LOG = DATA / "approval_log.csv"
APPROVAL_LOCK = threading.Lock()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_demo_data() -> dict[str, list[dict[str, str]]]:
    return {
        "metrics": _read_csv(DATA / "schedule_metrics.csv"),
        "shifts": _read_csv(DATA / "schedule_comparison.csv"),
        "workers": _read_csv(DATA / "worker_profiles.csv"),
    }


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        if self.path == "/api/data":
            body = json.dumps(load_demo_data()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/approvals":
            body = json.dumps(_read_csv(APPROVAL_LOG)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/approval":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2048:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(length))
            scenario = payload.get("scenario")
            disruption = payload.get("disruption")
            decision = payload.get("decision")
            allowed = {("ordinary", "none"), ("event_low", "none"), ("event_medium", "none"),
                       ("event_high", "none"), ("event_medium", "two_callouts"),
                       ("event_medium", "four_arrival_surge")}
            if (scenario, disruption) not in allowed or decision not in {"approved", "rejected"}:
                self.send_error(400, "Invalid scenario, disruption, or decision.")
                return
        except (ValueError, TypeError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON request.")
            return

        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with APPROVAL_LOCK:
            exists = APPROVAL_LOG.exists()
            with APPROVAL_LOG.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not exists:
                    writer.writerow(("timestamp_utc", "scenario", "disruption", "decision"))
                writer.writerow((timestamp, scenario, disruption, decision))
        body = json.dumps({"timestamp": timestamp, "decision": decision}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    address = ("127.0.0.1", 8000)
    handler = partial(DemoHandler)
    server = ThreadingHTTPServer(address, handler)
    print("CrewPilot demo is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping CrewPilot demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
