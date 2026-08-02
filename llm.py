# Developed as part of coursework. Some parts were refined with assistance from a generative AI tool.

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urllib.request
import urllib.error
from urllib.parse import urlsplit


def call_mistral(prompt: str) -> str:
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set")

    url = "https://api.mistral.ai/v1/chat/completions"

    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            return parsed["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Mistral HTTPError {e.code}: {err_body}")
    except Exception as e:
        raise RuntimeError(f"Mistral request failed: {e}")


class LLMHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "llm"})
            return
        self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path != "/llm":
            self._send_json(404, {"error": "Not Found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""

        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        prompt = data.get("prompt")
        if not isinstance(prompt, str) or prompt.strip() == "":
            self._send_json(400, {"error": "Missing or invalid 'prompt'"})
            return

        try:
            output = call_mistral(prompt)
            self._send_json(200, {"output": output})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


if __name__ == "__main__":
    server_address = ("", 3000)
    httpd = HTTPServer(server_address, LLMHandler)
    print("LLM service running on port 3000...")
    httpd.serve_forever()
