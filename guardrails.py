# Developed as part of coursework. Some parts were refined with assistance from a generative AI tool.

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import re
import urllib.request
import urllib.error
from urllib.parse import quote, urlsplit


def firebase_base_url() -> str:
    db = os.environ.get("FIREBASE_DB")
    if not db:
        raise RuntimeError("FIREBASE_DB is not set")
    return f"https://{db}.europe-west1.firebasedatabase.app"


def fb_get(path: str):
    url = firebase_base_url() + path
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def fb_put(path: str, payload: dict):
    url = firebase_base_url() + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="PUT", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def fb_delete(path: str):
    url = firebase_base_url() + path
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


class GuardrailsHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _path_only(self) -> str:
        return urlsplit(self.path).path

    def do_GET(self):
        path = self._path_only()

        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "guardrails"})
            return

        if path == "/guardrails":
            try:
                data = fb_get("/guardrails.json")
                if data is None:
                    self._send_json(200, [])
                    return
                ids = sorted(list(data.keys()))
                self._send_json(200, ids)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if path.startswith("/guardrails/"):
            guard_id = path.split("/", 2)[2]
            if guard_id.strip() == "":
                self._send_json(400, {"error": "Missing guardrail id"})
                return
            try:
                safe_id = quote(guard_id, safe="")
                data = fb_get(f"/guardrails/{safe_id}.json")
                if data is None:
                    self._send_json(404, {"error": "Guardrail not found"})
                    return
                self._send_json(200, data)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        self._send_json(404, {"error": "Not Found"})

    def do_PUT(self):
        path = self._path_only()

        if not path.startswith("/guardrails/"):
            self._send_json(404, {"error": "Not Found"})
            return

        guard_id = path.split("/", 2)[2]
        if guard_id.strip() == "":
            self._send_json(400, {"error": "Missing guardrail id"})
            return

        data = self._read_json_body()
        if not isinstance(data, dict):
            self._send_json(400, {"error": "Invalid JSON"})
            return

        regx = data.get("regx")
        sub = data.get("sub")
        if not isinstance(regx, str) or not isinstance(sub, str):
            self._send_json(400, {"error": "Missing or invalid 'regx' or 'sub'"})
            return

        if regx.strip() == "":
            self._send_json(400, {"error": "Invalid 'regx'"})
            return

        # Validate regex
        try:
            re.compile(regx)
        except re.error:
            self._send_json(400, {"error": "Invalid 'regx'"})
            return

        record = {"id": guard_id, "regx": regx, "sub": sub}

        try:
            safe_id = quote(guard_id, safe="")
            fb_put(f"/guardrails/{safe_id}.json", record)
            self._send_json(201, record)
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_DELETE(self):
        path = self._path_only()

        if not path.startswith("/guardrails/"):
            self._send_json(404, {"error": "Not Found"})
            return

        guard_id = path.split("/", 2)[2]
        if guard_id.strip() == "":
            self._send_json(400, {"error": "Missing guardrail id"})
            return

        try:
            safe_id = quote(guard_id, safe="")
            existing = fb_get(f"/guardrails/{safe_id}.json")
            if existing is None:
                self._send_json(404, {"error": "Guardrail not found"})
                return
            fb_delete(f"/guardrails/{safe_id}.json")
            self._send_json(200, {"deleted": guard_id})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


if __name__ == "__main__":
    server_address = ("", 3001)
    httpd = HTTPServer(server_address, GuardrailsHandler)
    print("Guardrails service running on port 3001...")
    httpd.serve_forever()
