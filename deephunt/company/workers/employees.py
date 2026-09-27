"""Worker: employee / people OSINT. PASSIVE COLLECTION ONLY — ABSOLUTE BOUNDARY.

What this worker does:
- Queries the PUBLIC GitHub REST API (no auth, rate-limited) for repositories
  mentioning the company, then lists PUBLIC contributors and their PUBLIC
  profile fields (name, bio, blog, company, location, twitter).
- Records only what is already public. No login, no scraping behind auth.

What this worker NEVER does (hard-coded refusal, not policy text):
- Contact, message, follow, or interact with any person in any way.
- Pretexting, phishing, impersonation, or any social engineering action.
- Access non-public data, private repos, or anything behind a login.

The output is for defensive context (who ships the code, public tech talks,
public blog posts) and for scoping — never for targeting people.

Independently runnable: python3 -m company.workers.employees "Acme Corp" example.com
"""
from __future__ import annotations

import sys

from .base import http_get_json, result

WORKER = "employees"
_GH = "https://api.github.com"


def _gh(path: str) -> tuple[object, str]:
    return http_get_json(f"{_GH}{path}", timeout=20)


def run(company_name: str, domain: str = "") -> dict:
    errors: list[str] = []
    data: dict = {
        "company": company_name, "domain": domain,
        "boundary": ("PUBLIC DATA ONLY. No contact, no pretexting, no phishing, "
                     "no social engineering. Collection only."),
        "people": [], "repos": [],
    }

    q = company_name.replace(" ", "+")
    repos, err = _gh(f"/search/repositories?q={q}+in:name,description,readme"
                     f"&per_page=8&sort=stars&order=desc")
    if err:
        errors.append(f"github repo search: {err}")
        return result(WORKER, data, errors)

    items = (repos or {}).get("items", []) if isinstance(repos, dict) else []
    seen: set[str] = set()
    for repo in items:
        full = repo.get("full_name", "")
        data["repos"].append({
            "full_name": full,
            "description": (repo.get("description") or "")[:200],
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language"),
            "url": repo.get("html_url"),
        })
        if len(data["people"]) >= 15:
            continue
        contrib, err = _gh(f"/repos/{full}/contributors?per_page=10")
        if err:
            errors.append(f"contributors {full}: {err}")
            continue
        for c in (contrib if isinstance(contrib, list) else []):
            login = c.get("login", "")
            if not login or login in seen or "[bot]" in login:
                continue
            seen.add(login)
            prof, err = _gh(f"/users/{login}")
            if err or not isinstance(prof, dict):
                continue
            # PUBLIC profile fields only
            data["people"].append({
                "github": login,
                "name": prof.get("name"),
                "bio": (prof.get("bio") or "")[:200],
                "company_field": prof.get("company"),
                "location": prof.get("location"),
                "blog": prof.get("blog"),
                "twitter": prof.get("twitter_username"),
                "public_repos": prof.get("public_repos"),
                "profile_url": prof.get("html_url"),
            })
            if len(data["people"]) >= 15:
                break

    data["person_count"] = len(data["people"])
    data["repo_count"] = len(data["repos"])
    return result(WORKER, data, errors)


if __name__ == "__main__":
    import json
    name = sys.argv[1] if len(sys.argv) > 1 else "Example"
    dom = sys.argv[2] if len(sys.argv) > 2 else "example.com"
    print(json.dumps(run(name, dom), indent=1)[:6000])
