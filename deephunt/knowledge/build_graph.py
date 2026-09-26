"""Build knowledge/graph.json — the normalized security knowledge graph.

Nodes: technique cards, weakness (CWE), vulnerability class.
Edges: technique -> exploits_weakness -> CWE, technique -> in_class -> class,
       CWE -> enables -> technique (reverse lookup for hypothesis generation).

Regenerate after editing knowledge/techniques/*.yaml: python3 knowledge/build_graph.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, ".."))
import kb  # noqa: E402 — enriched cards from knowledge/techniques/*.yaml

# klass -> representative CWEs (MITRE CWE taxonomy)
CLASS_CWE = {
    "authorization": ["CWE-639", "CWE-285", "CWE-862"],
    "authentication": ["CWE-287", "CWE-307", "CWE-613"],
    "injection": ["CWE-78", "CWE-79", "CWE-89", "CWE-94"],
    "xss": ["CWE-79"],
    "ssrf": ["CWE-918"],
    "cors": ["CWE-942"],
    "csrf": ["CWE-352"],
    "idor": ["CWE-639"],
    "api": ["CWE-639", "CWE-862"],
    "graphql": ["CWE-639", "CWE-862"],
    "business-logic": ["CWE-840", "CWE-841"],
    "logic": ["CWE-840"],
    "ai-llm": ["CWE-1427", "CWE-1428"],
    "session": ["CWE-384", "CWE-613"],
    "websocket": ["CWE-1385", "CWE-352"],
    "mobile": ["CWE-312", "CWE-200", "CWE-798"],
    "cloud": ["CWE-200", "CWE-732", "CWE-918"],
    "rate-limit": ["CWE-307", "CWE-770"],
    "race": ["CWE-362", "CWE-840"],
    "business_logic": ["CWE-840", "CWE-841"],
    "cache": ["CWE-444", "CWE-200"],
    "smuggling": ["CWE-444"],
    "upload": ["CWE-434"],
    "open-redirect": ["CWE-601"],
    "secrets": ["CWE-312", "CWE-798"],
    "crypto": ["CWE-327", "CWE-312"],
    "supply-chain": ["CWE-829"],
    "takeover": ["CWE-200"],
    "fuzzing": ["CWE-119", "CWE-787"],
    "crypto": ["CWE-327", "CWE-798"],
    "rate-limit": ["CWE-307", "CWE-799"],
    "cache": ["CWE-524"],
    "takeover": ["CWE-350"],
    "open-redirect": ["CWE-601"],
    "upload": ["CWE-434"],
    "smuggling": ["CWE-444"],
    "websocket": ["CWE-1385"],
    "race": ["CWE-362"],
    "secrets": ["CWE-798", "CWE-312"],
    "cloud": ["CWE-200"],
    "supply-chain": ["CWE-829"],
    "fuzzing": ["CWE-119", "CWE-787"],
}

CWE_NAMES = {
    "CWE-639": "Authorization Bypass Through User-Controlled Key",
    "CWE-285": "Improper Authorization", "CWE-862": "Missing Authorization",
    "CWE-287": "Improper Authentication", "CWE-307": "Improper Restriction of Authentication Attempts",
    "CWE-613": "Insufficient Session Expiration", "CWE-78": "OS Command Injection",
    "CWE-79": "Cross-site Scripting", "CWE-89": "SQL Injection",
    "CWE-94": "Code Injection", "CWE-918": "Server-Side Request Forgery",
    "CWE-942": "Permissive CORS", "CWE-352": "Cross-Site Request Forgery",
    "CWE-840": "Business Logic Errors", "CWE-841": "Behavioral Workflow",
    "CWE-1427": "Reliance on HTTP Request Translation by AI Model",
    "CWE-1428": "Reliance on HTTP Responses from AI Model",
    "CWE-384": "Session Fixation", "CWE-327": "Broken Crypto",
    "CWE-798": "Hard-coded Credentials", "CWE-799": "Missing Rate Limiting",
    "CWE-524": "Cached Sensitive Data", "CWE-350": "Reliance on Reverse DNS",
    "CWE-601": "Open Redirect", "CWE-434": "Unrestricted Upload",
    "CWE-444": "HTTP Request Smuggling", "CWE-1385": "Missing Origin Validation in WebSockets",
    "CWE-362": "Race Condition", "CWE-312": "Cleartext Storage of Sensitive Info",
    "CWE-200": "Exposure of Sensitive Information", "CWE-829": "Inclusion of Functionality from Untrusted Source",
    "CWE-119": "Buffer Errors", "CWE-787": "Out-of-bounds Write",
}


def parse_cards(path):
    text = open(path).read()
    cards, cur = [], {}
    for line in text.splitlines():
        m = re.match(r"^- id: (\S+)", line)
        if m:
            if cur:
                cards.append(cur)
            cur = {"id": m.group(1)}
            continue
        m = re.match(r"^  (\w+): (.+)", line)
        if m and cur is not None:
            k, v = m.group(1), m.group(2).strip()
            if k in ("signals",):
                v = [s.strip().strip('"') for s in v.strip("[]").split(",")]
            cur[k] = v
    if cur:
        cards.append(cur)
    return cards


def build():
    cards = kb.load_techniques()
    nodes, edges = {}, []
    for c in cards:
        tid = c.get("id", "?")
        nodes[tid] = {"type": "technique", "name": c.get("name", ""),
                      "klass": c.get("klass", ""),
                      "impact": c.get("impact_hint", "")[:80]}
        klass = c.get("klass", "")
        if klass:
            cn = f"class:{klass}"
            nodes.setdefault(cn, {"type": "class", "name": klass})
            edges.append([tid, "in_class", cn])
            for cwe in CLASS_CWE.get(klass, []):
                nodes.setdefault(cwe, {"type": "weakness",
                                       "name": CWE_NAMES.get(cwe, cwe)})
                edges.append([tid, "exploits_weakness", cwe])
                edges.append([cwe, "enables", tid])
    graph = {"nodes": nodes, "edges": edges,
             "stats": {"techniques": len(cards),
                       "weaknesses": sum(1 for n in nodes.values()
                                         if n["type"] == "weakness"),
                       "classes": sum(1 for n in nodes.values()
                                      if n["type"] == "class")}}
    out = os.path.join(BASE, "graph.json")
    json.dump(graph, open(out, "w"), indent=1)
    print(f"graph: {graph['stats']} -> {out}")
    return graph


if __name__ == "__main__":
    build()
