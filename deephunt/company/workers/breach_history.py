"""Worker: public breach / leak / disclosure history. Read-only, public sources.

Sources:
- HaveIBeenPwned public breach catalogue (no key needed for the list):
  https://haveibeenpwned.com/api/v3/breaches — matched by domain/name.
- Public HackerOne program page (only if the slug matches; 404 tolerated).
- Public note: GitHub code search needs auth, so leaked-secret hunting is
  documented as a follow-up for the operator, not done silently here.

No credentials are ever collected or stored — only counts, dates, and public
descriptions of historical incidents.

Independently runnable: python3 -m company.workers.breach_history "Acme" example.com
"""
from __future__ import annotations

import sys

from .base import http_get_json, http_get_text, result

WORKER = "breach_history"


def run(company_name: str, domain: str = "") -> dict:
    errors: list[str] = []
    data: dict = {"company": company_name, "domain": domain,
                  "breaches": [], "hackerone_program": None,
                  "leak_hunting_note": ""}

    breaches, err = http_get_json("https://haveibeenpwned.com/api/v3/breaches",
                                  timeout=25)
    if err:
        errors.append(f"HIBP: {err}")
    else:
        needle = [company_name.lower(), (domain or "").lower().split(".")[0]]
        for b in (breaches if isinstance(breaches, list) else []):
            hay = f"{b.get('Name', '')} {b.get('Title', '')} {b.get('Domain', '')}".lower()
            if any(n and n in hay for n in needle):
                data["breaches"].append({
                    "name": b.get("Name"), "title": b.get("Title"),
                    "date": b.get("BreachDate"),
                    "pwn_count": b.get("PwnCount"),
                    "data_classes": (b.get("DataClasses") or [])[:12],
                    "verified": b.get("IsVerified"),
                })
    data["breach_count"] = len(data["breaches"])

    # HackerOne public program page — best-effort slug guess, 404 is fine
    slug = (domain or company_name).lower().split(".")[0].replace(" ", "")
    if slug and slug != "example":
        body, _, err = http_get_text(f"https://hackerone.com/{slug}", timeout=15)
        if not err and body and "bounty" in body.lower():
            data["hackerone_program"] = {
                "url": f"https://hackerone.com/{slug}",
                "likely_program": True,
                "note": "Public program page exists. Verify scope on the "
                        "official page before any testing.",
            }

    data["leak_hunting_note"] = (
        "Follow-up for the operator (read-only, authenticated GitHub API): "
        "search code for the company domain + 'password'/'secret'/'api_key' in "
        "public repos and gists. Never store found secrets; report via the "
        "company's disclosure channel only.")
    return result(WORKER, data, errors)


if __name__ == "__main__":
    import json
    name = sys.argv[1] if len(sys.argv) > 1 else "Example"
    dom = sys.argv[2] if len(sys.argv) > 2 else "example.com"
    print(json.dumps(run(name, dom), indent=1)[:4000])
