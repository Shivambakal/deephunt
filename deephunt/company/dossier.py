"""Dossier assembly: worker outputs + plan -> structured dict + markdown."""
from __future__ import annotations

from datetime import datetime, timezone

DOSSIER_TEMPLATE = """# Company Dossier: {company} ({domain})

_Generated {ts} by DEEPHUNT Company Hunter. Passive recon only — no active
testing was performed. People section: public data only, no contact._

## At a glance
- Subdomains found: {subdomain_count} ({live_typos} live typo-squat candidates)
- Resolved IPs: {ips}
- Technologies: {tech}
- Public breach records matched: {breach_count}
- News items (30d): {news_count} {surface_signals}
- Employees (public GitHub): {person_count} profiles, {repo_count} repos

## Domain footprint
Top subdomains: {top_subs}
DNS: A={a} MX={mx}
Email posture: SPF={spf} DMARC-hint={dmarc}

## Technology stack
Detected: {tech_list}
Versions: {versions}
Third-party hosts: {third_party}
Security-relevant headers: {headers}
Public files found: {pubfiles}

## Breach / disclosure history
{breaches}

## News (surface-changing first)
{news_items}

## People (public data only — DO NOT CONTACT)
{people}

## Suspicious changes since last run
{changes}

## Ranked attack plan (top {plan_n})
{plan_items}

## Follow-ups
{followups}

## Active-testing handoff
{active_handoff}

---
*Boundaries: passive recon only. Nothing here authorizes active testing.
Active work requires confirmed bug-bounty scope and goes through the
ResearchSession enforced loop (propose_test + TestAuthorization).*
"""


def _w(dossier: dict, name: str) -> dict:
    return (dossier.get("workers", {}).get(name, {}).get("data", {}) or {})


def assemble(company: str, domain: str, workers: dict, plan: list[dict],
             changes: dict, followups: list[str], active_handoff: str) -> dict:
    return {
        "company": company, "domain": domain,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workers": workers, "attack_plan": plan,
        "changes": changes, "followups": followups,
        "active_handoff": active_handoff,
        "mode": "passive",
    }


def render_markdown(dossier: dict) -> str:
    dom, tech = _w(dossier, "domains"), _w(dossier, "techstack")
    br, news = _w(dossier, "breach_history"), _w(dossier, "news")
    emp = _w(dossier, "employees")
    plan = dossier.get("attack_plan", [])

    breaches = "\n".join(
        f"- {b['name']} ({b['date']}): {b['title']} — {b['pwn_count']} accounts"
        for b in br.get("breaches", [])) or "None matched in HIBP catalogue."
    news_items = "\n".join(
        f"- [{n['category']}] {n['title']} ({n['published'][:16]})"
        for n in news.get("items", [])[:12]) or "No items."
    people = "\n".join(
        f"- {p.get('name') or p['github']} (@{p['github']}): "
        f"{(p.get('bio') or '')[:100]} {p.get('profile_url', '')}"
        for p in emp.get("people", [])[:12]) or "None found via public GitHub."
    plan_items = "\n".join(
        f"{i+1}. **{p['card_id']} {p['name']}** (score {p['score']}) — "
        f"{'; '.join(p['reasons'][:2])}\n   Hypothesis: {p['hypothesis'][:160]}"
        for i, p in enumerate(plan)) or "No plan generated."
    changes = "\n".join(f"- {c}" for c in
                        dossier.get("changes", {}).get("items", [])) or "None."
    followups = "\n".join(f"- {f}" for f in dossier.get("followups", [])) or "None."

    dns = dom.get("dns", {})
    return DOSSIER_TEMPLATE.format(
        company=dossier["company"], domain=dossier["domain"],
        ts=dossier["generated_at"][:19] + "Z",
        subdomain_count=dom.get("subdomain_count", 0),
        live_typos=len(dom.get("live_typo_candidates", [])),
        ips=", ".join(dom.get("resolved_ips", [])[:5]) or "none",
        tech=", ".join(tech.get("detected", [])[:8]) or "none",
        breach_count=br.get("breach_count", 0),
        news_count=len(news.get("items", [])),
        surface_signals="(surface signals: " + ", ".join(news.get("surface_signals", [])) + ")"
        if news.get("surface_signals") else "",
        person_count=emp.get("person_count", 0), repo_count=emp.get("repo_count", 0),
        top_subs=", ".join(dom.get("subdomains", [])[:15]) or "none",
        a=", ".join(dns.get("A", [])[:3]), mx=", ".join(dns.get("MX", [])[:2]),
        spf=dom.get("email_posture", {}).get("spf"),
        dmarc=dom.get("email_posture", {}).get("dmarc_hint"),
        tech_list=", ".join(tech.get("detected", [])[:12]) or "none",
        versions=", ".join(f"{k}={v}" for k, v in tech.get("versions", {}).items()) or "none",
        third_party=", ".join(tech.get("third_party_hosts", [])[:10]) or "none",
        headers=", ".join(tech.get("headers_of_note", {}).keys()) or "none",
        pubfiles=", ".join(tech.get("public_files", {}).keys()) or "none",
        breaches=breaches, news_items=news_items, people=people,
        changes=changes, plan_n=len(plan), plan_items=plan_items,
        followups=followups, active_handoff=dossier.get("active_handoff", "none"),
    )
