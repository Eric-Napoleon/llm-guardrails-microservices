# Developed as part of coursework. Some parts were refined with assistance from a generative AI tool.

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.request
import re
from urllib.parse import urlsplit


LLM_URL = "http://127.0.0.1:3000/llm"
GUARDRAILS_URL = "http://127.0.0.1:3001/guardrails"


def http_get(url: str):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


class AubergeHandler(BaseHTTPRequestHandler):
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

    def do_POST(self):
        path = urlsplit(self.path).path
        if path != "/auberge":
            self._send_json(404, {"error": "Not Found"})
            return

        data = self._read_json_body()
        if not isinstance(data, dict):
            self._send_json(400, {"error": "Invalid JSON"})
            return

        prompt = data.get("prompt")
        if not isinstance(prompt, str) or prompt.strip() == "":
            self._send_json(400, {"error": "Missing or invalid 'prompt'"})
            return

        try:
            # Guardrails service may return either a list (spec) or {"ids": [...]} (older version).
            guards = http_get(GUARDRAILS_URL)
            if isinstance(guards, list):
                ids = guards
            elif isinstance(guards, dict):
                ids = guards.get("ids", [])
            else:
                ids = []

            ids = sorted([gid for gid in ids if isinstance(gid, str)])

            # Fetch rules once and reuse
            rules = []
            for gid in ids:
                guard = http_get(f"{GUARDRAILS_URL}/{gid}")
                regx = guard.get("regx", "")
                sub = guard.get("sub", "")
                if isinstance(regx, str) and isinstance(sub, str) and regx != "":
                    rules.append((regx, sub))

            # Apply to input
            sanitised_prompt = prompt
            for regx, sub in rules:
                sanitised_prompt = re.sub(regx, sub, sanitised_prompt)

            # Call LLM
            result = http_post(LLM_URL, {"prompt": sanitised_prompt})
            output = result.get("output", "")
            if not isinstance(output, str):
                output = str(output)

            # Apply to output
            sanitised_output = output
            for regx, sub in rules:
                sanitised_output = re.sub(regx, sub, sanitised_output)

            self._send_json(200, {"output": sanitised_output})

        except Exception as e:
            self._send_json(500, {"error": str(e)})


if __name__ == "__main__":
    server_address = ("", 3002)
    httpd = HTTPServer(server_address, AubergeHandler)
    print("Auberge service running on port 3002...")
    httpd.serve_forever()
