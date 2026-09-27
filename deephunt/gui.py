#!/usr/bin/env python3
"""DEEPHUNT GUI — zero-dependency web dashboard (stdlib only).

Run:  python3 gui.py [port]   (default 5059, localhost only)
Then open http://127.0.0.1:5059 in a browser.

Pages:
  Overview   — daemon status, current target/phase, quick actions
  Targets    — scope profiles, active flags
  Identities — test accounts, statuses, signup brief generator
  Sessions   — recent ResearchSessions
  Findings   — recorded findings
  Logs       — daemon log tail

Actions (POST /api/...): start/stop daemon. Signup runs produce a brief the
agent executes via a live browser task; the GUI shows the brief + checklist.
"""
from __future__ import annotations

import glob
import html
import json
import os
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import cli  # noqa: E402  (reuse status/target parsers)
from identity import driver as idriver  # noqa: E402
from identity.manager import email_for, get as ident_get, list_all  # noqa: E402

import yaml  # noqa: E402


def _targets():
    out = []
    for path in sorted(glob.glob(os.path.join(BASE, "targets", "*.yaml"))):
        if os.path.basename(path).startswith("_"):
            continue
        d = yaml.safe_load(open(path))
        out.append({
            "name": d.get("name"),
            "program": d.get("program", "")[:90],
            "scope_hosts": len(d.get("scope_hosts", [])),
            "active": d.get("active_allowed"),
            "out_of_scope": len(d.get("out_of_scope", [])),
        })
    return out


def _sessions():
    sess_dir = os.path.join(BASE, "..", "data", "brain", "sessions")
    out = []
    for f in sorted(glob.glob(os.path.join(sess_dir, "*.json")),
                    key=os.path.getmtime, reverse=True)[:15]:
        try:
            d = json.load(open(f))
            out.append({
                "id": os.path.basename(f)[:8],
                "objective": d.get("objective", "?")[:80],
                "hypotheses": len(d.get("hypotheses", [])),
                "confirmed": len(d.get("confirmed", [])),
                "rejected": len(d.get("rejected", [])),
            })
        except Exception:
            pass
    return out


def _log_tail(n=80):
    p = os.path.join(BASE, "logs", "daemon.out")
    if not os.path.exists(p):
        return "no daemon log yet"
    with open(p, errors="replace") as f:
        return "".join(f.readlines()[-n])


PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEEPHUNT</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--txt:#e6edf3;--dim:#8b949e;
--acc:#58a6ff;--grn:#3fb950;--red:#f85149;--amb:#d29922}
*{box-sizing:border-box}body{background:var(--bg);color:var(--txt);
font-family:system-ui,-apple-system,sans-serif;margin:0;padding:0}
header{background:var(--panel);border-bottom:1px solid var(--line);
padding:14px 20px;display:flex;align-items:center;gap:14px;position:sticky;top:0}
header h1{font-size:18px;margin:0;letter-spacing:2px}
nav{display:flex;gap:4px;margin-left:12px;flex-wrap:wrap}
nav button{background:none;border:1px solid transparent;color:var(--dim);
padding:8px 14px;border-radius:6px;cursor:pointer;font-size:14px}
nav button.on,nav button:hover{color:var(--txt);border-color:var(--line);
background:#1c2128}
main{padding:20px;max-width:1100px;margin:0 auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;
padding:16px;margin-bottom:14px}
.card h3{margin:0 0 10px;font-size:15px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;
border:1px solid var(--line)}
.ok{color:var(--grn);border-color:var(--grn)}.bad{color:var(--red);
border-color:var(--red)}.warn{color:var(--amb);border-color:var(--amb)}
.dim{color:var(--dim)}.mono{font-family:ui-monospace,monospace;font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:var(--dim);font-weight:600;padding:8px;
border-bottom:1px solid var(--line)}
td{padding:8px;border-bottom:1px solid var(--line)}
.btn{background:#238636;color:#fff;border:none;padding:8px 16px;border-radius:6px;
cursor:pointer;font-size:14px;margin-right:8px}
.btn.stop{background:#a40e26}.btn.ghost{background:#21262d}
.btn:disabled{opacity:.4;cursor:default}
pre{background:#0d1117;border:1px solid var(--line);border-radius:6px;
padding:12px;overflow:auto;max-height:420px;font-size:12.5px;white-space:pre-wrap}
input,select{background:#0d1117;border:1px solid var(--line);color:var(--txt);
padding:8px 10px;border-radius:6px;font-size:14px}
.sec{display:none}.sec.on{display:block}
.kv{display:grid;grid-template-columns:150px 1fr;gap:6px;font-size:14px}
</style></head><body>
<header><h1>&#9670; DEEPHUNT</h1><nav id="nav"></nav></header>
<main id="main"></main>
<script>
const $=s=>document.querySelector(s);
const secs=["overview","targets","identities","sessions","findings","logs"];
let cur="overview";
function nav(){ $("#nav").innerHTML=secs.map(s=>
`<button data-s="${s}" class="${s===cur?'on':''}">${s[0].toUpperCase()+s.slice(1)}</button>`).join("");
document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{cur=b.dataset.s;nav();render();});}
async function api(p,o){const r=await fetch(p,{method:o?"POST":"GET",
headers:{"Content-Type":"application/json"},body:o?JSON.stringify(o):undefined});
return r.json();}
function pill(t,c){return `<span class="pill ${c}">${t}</span>`;}
async function render(){
 const m=$("#main");
 if(cur==="overview"){
  const s=await api("/api/status");
  m.innerHTML=`<div class="card"><h3>Daemon</h3><div class="row">
   ${s.running?pill("RUNNING","ok"):pill("STOPPED","bad")}
   <span class="dim mono">pid ${s.pid||"-"} &middot; up ${s.uptime||"-"}</span></div>
   <div class="kv" style="margin-top:10px">
   <span class="dim">Target</span><b>${s.target}</b>
   <span class="dim">Phase</span><span>${s.phase}</span>
   <span class="dim">Last</span><span class="mono dim">${s.last_line||""}</span></div>
   <div class="row" style="margin-top:12px">
   <button class="btn" onclick="daemon('start')" ${s.running?"disabled":""}>Start</button>
   <button class="btn stop" onclick="daemon('stop')" ${s.running?"":"disabled"}>Stop</button>
   <input id="tg" placeholder="targets (default robinhood)" style="width:260px" value="robinhood,shopify,yahoo">
   </div></div>
   <div class="card"><h3>Think &rarr; See &rarr; Execute</h3>
   <p class="dim">The daemon hunts autonomously. Use <b>Targets</b> to review scope,
   <b>Identities</b> to create test accounts, <b>Sessions</b> to see its reasoning,
   <b>Findings</b> for results. Nothing is submitted anywhere without your review.</p></div>`;
 }
 if(cur==="targets"){
  const t=await api("/api/targets");
  m.innerHTML=`<div class="card"><h3>Targets (${t.length})</h3><table>
  <tr><th>Name</th><th>Program</th><th>Scope</th><th>Active</th></tr>
  ${t.map(x=>`<tr><td><b>${x.name}</b></td><td class="dim">${x.program}</td>
  <td>${x.scope_hosts} hosts</td><td>${x.active?pill("yes","ok"):pill("no","warn")}</td></tr>`).join("")}
  </table></div>`;
 }
 if(cur==="identities"){
  const d=await api("/api/identities");
  m.innerHTML=`<div class="card"><h3>Test identities</h3><table>
  <tr><th>Target</th><th>Email</th><th>Status</th><th>Updated</th></tr>
  ${d.idents.length?d.idents.map(x=>`<tr><td><b>${x.target}</b></td>
  <td class="mono">${x.email}</td><td>${x.status}</td>
  <td class="dim">${(x.updated_at||"").slice(0,16)}</td></tr>`).join(""):
  `<tr><td colspan="4" class="dim">none registered yet</td></tr>`}</table>
  <div class="row" style="margin-top:12px"><select id="st">
  ${d.targets.map(t=>`<option>${t}</option>`).join("")}</select>
  <button class="btn" onclick="signup()">Generate signup brief</button></div>
  <p class="dim">Passwords live only in your Secure Vault &mdash; never here, never in logs.</p></div>
  <div class="card" id="brief" style="display:none"><h3>Signup brief</h3>
  <div id="pre"></div><pre id="btext"></pre></div>`;
 }
 if(cur==="sessions"){
  const s=await api("/api/sessions");
  m.innerHTML=`<div class="card"><h3>Research sessions</h3><table>
  <tr><th>ID</th><th>Objective</th><th>Hyp</th><th>Conf</th><th>Rej</th></tr>
  ${s.map(x=>`<tr><td class="mono">${x.id}</td><td>${x.objective}</td>
  <td>${x.hypotheses}</td><td>${x.confirmed}</td><td>${x.rejected}</td></tr>`).join("")}
  </table></div>`;
 }
 if(cur==="findings"){
  const f=await api("/api/findings");
  m.innerHTML=`<div class="card"><h3>Findings</h3>
  ${f.length?`<table><tr><th>File</th></tr>${f.map(x=>`<tr><td class="mono">${x}</td></tr>`).join("")}</table>`:
  `<p class="dim">No findings recorded yet. Zero is a result too.</p>`}</div>`;
 }
 if(cur==="logs"){
  const l=await api("/api/log");
  m.innerHTML=`<div class="card"><h3>Daemon log</h3><pre>${l.log.replace(/</g,"&lt;")}</pre>
  <button class="btn ghost" onclick="render()">Refresh</button></div>`;
 }
}
async function daemon(a){
 const tg=(document.querySelector("#tg")||{}).value||"robinhood";
 await api("/api/daemon",{action:a,targets:tg}); setTimeout(render,1500);}
async function signup(){
 const t=document.querySelector("#st").value;
 const r=await api("/api/signup",{target:t});
 document.querySelector("#brief").style.display="block";
 document.querySelector("#pre").innerHTML="<ul class='dim'>"+
  r.preflight.map(c=>`<li>${c}</li>`).join("")+"</ul>";
 document.querySelector("#btext").textContent=r.brief;}
nav();render();setInterval(()=>{if(cur==="overview"||cur==="logs")render();},15000);
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/status":
            s = cli.daemon_status()
            a = cli.current_activity()
            up = s.get("uptime_s", 0)
            self._json({
                "running": s["running"], "pid": s.get("pid"),
                "uptime": f"{up // 3600}h {(up % 3600) // 60}m" if s["running"] else None,
                "target": a["target"], "phase": a["phase"],
                "last_line": html.escape(a["last_line"]),
            })
            return
        if self.path == "/api/targets":
            self._json(_targets())
            return
        if self.path == "/api/identities":
            idents = [{"target": t, **i} for t, i in list_all().items()]
            self._json({"idents": idents,
                        "targets": [t["name"] for t in _targets()]})
            return
        if self.path == "/api/sessions":
            self._json(_sessions())
            return
        if self.path == "/api/findings":
            found = []
            for pat in ("state/*finding*.json", "state/*finding*.md"):
                found += [os.path.basename(f) for f in
                          glob.glob(os.path.join(BASE, pat))]
            self._json(sorted(found))
            return
        if self.path == "/api/log":
            self._json({"log": _log_tail()})
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            data = {}
        if self.path == "/api/daemon":
            action = data.get("action")
            if action == "start":
                subprocess.run([os.path.join(BASE, "deephunt.sh"), "start",
                                data.get("targets", "robinhood"), "0"],
                               check=False)
            elif action == "stop":
                subprocess.run([os.path.join(BASE, "deephunt.sh"), "stop"],
                               check=False)
            self._json({"ok": True, "action": action})
            return
        if self.path == "/api/signup":
            target = data.get("target", "")
            try:
                pre = idriver.preflight(target)
                brief = idriver.render_brief(target)
                self._json({"ok": True, "preflight": pre, "brief": brief})
            except FileNotFoundError as e:
                self._json({"ok": False, "error": str(e)})
            return
        self._json({"error": "not found"}, 404)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5059
    srv = HTTPServer(("127.0.0.1", port), Handler)
    print(f"DEEPHUNT GUI on http://127.0.0.1:{port} (localhost only)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
