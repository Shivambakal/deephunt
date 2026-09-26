"""
Burp-Suite-equivalent traffic logger for mitmproxy.

Logs every request/response as JSONL to logs/<date>/traffic.jsonl with:
  method, url, headers (secrets redacted), status, timing, sizes.

Redaction: Authorization, Cookie, Set-Cookie, Proxy-Authorization,
X-Api-Key and any header whose name contains token/secret/key/password
have their VALUES replaced with [REDACTED]. Query params are kept but any
param named like *token* *secret* *key* *password* *auth* is redacted too.
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qsl

from mitmproxy import http

REDACTED = "[REDACTED]"
# header names whose values are never logged
SECRET_HEADER_NAMES = {
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "x-auth-token", "x-access-token",
}
SECRET_NAME_RE = re.compile(r"(token|secret|passwd|password|apikey|api_key|auth|sessionid|csrftoken)", re.I)
# query params whose values are redacted
SECRET_PARAM_RE = re.compile(r"(token|secret|passwd|password|apikey|api_key|auth|code|session)", re.I)
# body params (form) whose values are redacted
SECRET_BODY_RE = SECRET_PARAM_RE
# never log raw request/response bodies containing likely credential material
CREDENTIAL_BODY_RE = re.compile(r"(password|passwd|secret|client_secret|private_key)", re.I)


def redact_headers(headers: http.Headers) -> dict:
    out = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in SECRET_HEADER_NAMES or SECRET_NAME_RE.search(lk):
            out[k] = REDACTED
        else:
            out[k] = v
    return out


def redact_url(url: str) -> str:
    """Keep URL but redact secret-looking query param values."""
    try:
        parts = urlparse(url)
        if not parts.query:
            return url
        pairs = parse_qsl(parts.query, keep_blank_values=True)
        clean = [
            (k, REDACTED if SECRET_PARAM_RE.search(k) else v)
            for k, v in pairs
        ]
        from urllib.parse import urlencode
        new_q = urlencode(clean)
        return parts._replace(query=new_q).geturl()
    except Exception:
        return url


def safe_body_preview(content: bytes, limit: int = 2048) -> str | None:
    """Text preview of body, None if binary or contains credential material."""
    if not content:
        return ""
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "<binary>"
    if CREDENTIAL_BODY_RE.search(text):
        return "<redacted: credential material>"
    return text[:limit] + ("..." if len(text) > limit else "")


class TrafficLogger:
    def __init__(self):
        self.log_dir = os.environ.get(
            "PROXY_LOG_DIR",
            os.path.join(os.path.dirname(__file__), "..", "logs"),
        )
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.dir = os.path.join(self.log_dir, day)
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "traffic.jsonl")
        self._fh = open(self.path, "a", encoding="utf-8")
        self._seq = 0

    def _write(self, record: dict):
        record["seq"] = self._seq
        self._seq += 1
        self._fh.write(json.dumps(record, default=str) + "\n")
        self._fh.flush()

    def request(self, flow: http.HTTPFlow):
        req = flow.request
        flow.metadata["logger_t0"] = time.time()
        self._write({
            "type": "request",
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": req.method,
            "url": redact_url(req.pretty_url),
            "http_version": req.http_version,
            "headers": redact_headers(req.headers),
            "body_preview": safe_body_preview(req.content),
            "body_len": len(req.content or b""),
        })

    def response(self, flow: http.HTTPFlow):
        req = flow.request
        resp = flow.response
        t0 = flow.metadata.get("logger_t0", time.time())
        self._write({
            "type": "response",
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": req.method,
            "url": redact_url(req.pretty_url),
            "status": resp.status_code,
            "reason": resp.reason,
            "headers": redact_headers(resp.headers),
            "body_preview": safe_body_preview(resp.content),
            "body_len": len(resp.content or b""),
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })

    def done(self):
        try:
            self._fh.close()
        except Exception:
            pass


addons = [TrafficLogger()]
