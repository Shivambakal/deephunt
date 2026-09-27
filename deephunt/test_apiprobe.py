"""Tests for deephunt/apiprobe.py — LOCAL fake HTTP server only. No external traffic."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apiprobe

SPEC_DOC = {"openapi": "3.0.0",
            "paths": {"/projects": {"get": {"parameters": [{"name": "limit"}],
                                            "security": [{}]}},
                      "/projects/{id}": {"get": {"parameters": []}}}}


class FakeAPI(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/openapi.json":
            self._send(200, SPEC_DOC)
        elif self.path.startswith("/graphql?query="):
            q = self.path.split("query=", 1)[1]
            if "__schema" in q:
                self._send(200, {"data": {"__schema": {}}})
            elif "__type" in q:
                self._send(200, {"data": {"__type": {"fields": []}}})
            else:
                self._send(400, {"errors": []})
        else:
            self._send(404, {})

    def do_POST(self):
        if self.path == "/graphql":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            if "__schema" in body:
                self._send(200, {"data": {"__schema": {}}})
            else:
                self._send(400, {"errors": []})
        else:
            self._send(404, {})


def _server():
    srv = HTTPServer(("127.0.0.1", 0), FakeAPI)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


def test_discover_specs():
    srv, base = _server()
    try:
        found = apiprobe.discover_specs(base)
        assert len(found) == 1, found
        assert found[0]["kind"] == "openapi3"
        assert found[0]["paths"] == 2
    finally:
        srv.shutdown()
    print("PASS test_discover_specs")


def test_graphql_post_introspection():
    srv, base = _server()
    try:
        res = apiprobe.probe_graphql(base)
        hit = [r for r in res if r["url"] == base + "/graphql"]
        assert hit and hit[0]["introspection"] is True
        assert hit[0]["method"] == "POST"
    finally:
        srv.shutdown()
    print("PASS test_graphql_post_introspection")


def test_extract_endpoints():
    srv, base = _server()
    try:
        eps = apiprobe.extract_endpoints_from_spec(base + "/openapi.json")
        assert len(eps) == 2, eps
        proj = [e for e in eps if e["path"] == "/projects"][0]
        assert proj["method"] == "GET" and proj["params"] == ["limit"]
        assert proj["auth"] is True
    finally:
        srv.shutdown()
    print("PASS test_extract_endpoints")


def test_no_false_positives():
    srv, base = _server()
    try:
        # /api/graphql does not exist on the fake server -> no hit
        res = apiprobe.probe_graphql(base)
        urls = [r["url"] for r in res]
        assert base + "/api/graphql" not in urls, urls
    finally:
        srv.shutdown()
    print("PASS test_no_false_positives")


if __name__ == "__main__":
    test_discover_specs()
    test_graphql_post_introspection()
    test_extract_endpoints()
    test_no_false_positives()
    print("apiprobe: 4/4 pass")
