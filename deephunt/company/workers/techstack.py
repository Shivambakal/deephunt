"""Worker: technology fingerprinting. Passive only.

Fetches the company's PUBLIC homepage HTML (one plain GET, like a visitor)
plus public /.well-known/security.txt and /robots.txt, then fingerprints
server/framework/JS/cloud/third-party markers with a built-in signature set.
No crawling, no fuzzing, no probing of non-public paths.

Independently runnable: python3 -m company.workers.techstack example.com
"""
from __future__ import annotations

import re
import sys

from .base import http_get_text, result

WORKER = "techstack"

# (token, label, where to look)
SIGNATURES = [
    # servers / infra
    ("cloudflare", "Cloudflare", "headers"), ("akamai", "Akamai", "headers"),
    ("fastly", "Fastly", "headers"), ("awselb", "AWS ELB/ALB", "headers"),
    ("nginx", "nginx", "headers"), ("apache", "Apache", "headers"),
    ("vercel", "Vercel", "headers"), ("netlify", "Netlify", "headers"),
    ("cloudfront", "CloudFront", "headers"),
    # frameworks (html markers)
    ("__next_data__", "Next.js", "html"), ("__NEXT_DATA__", "Next.js", "html"),
    ("nuxt", "Nuxt.js", "html"), ("gatsby", "Gatsby", "html"),
    ("wp-content", "WordPress", "html"), ("wp-json", "WordPress", "html"),
    ("drupal", "Drupal", "html"), ("shopify", "Shopify", "html"),
    ("webflow", "Webflow", "html"), ("wix.com", "Wix", "html"),
    ("squarespace", "Squarespace", "html"),
    # js libraries
    ("react", "React", "html"), ("vue", "Vue.js", "html"),
    ("angular", "Angular", "html"), ("jquery", "jQuery", "html"),
    ("backbone", "Backbone.js", "html"), ("ember", "Ember.js", "html"),
    ("svelte", "Svelte", "html"),
    # auth / api markers
    ("auth0", "Auth0", "html"), ("okta", "Okta", "html"),
    ("firebase", "Firebase", "html"), ("stripe", "Stripe", "html"),
    ("graphql", "GraphQL", "html"), ("/api/", "REST API paths", "html"),
    # trackers / third parties
    ("googletagmanager", "Google Tag Manager", "html"),
    ("google-analytics", "Google Analytics", "html"),
    ("hotjar", "Hotjar", "html"), ("segment", "Segment", "html"),
    ("intercom", "Intercom", "html"), ("hubspot", "HubSpot", "html"),
    ("salesforce", "Salesforce", "html"), ("marketo", "Marketo", "html"),
]

VERSION_RES = [
    (r"jquery[.-](\d+\.\d+[\.\d]*)", "jQuery"),
    (r"react[.-](\d+\.\d+[\.\d]*)", "React"),
    (r"wp-includes.*?ver=(\d+\.\d+[\.\d]*)", "WordPress"),
    (r"bootstrap[.-](\d+\.\d+[\.\d]*)", "Bootstrap"),
]


def run(domain: str) -> dict:
    domain = domain.strip().lower().rstrip(".")
    errors: list[str] = []
    data: dict = {"domain": domain, "detected": [], "versions": {},
                  "third_party_hosts": [], "headers_of_note": {},
                  "public_files": {}}

    body, headers, err = http_get_text(f"https://{domain}/", timeout=25)
    if err:
        errors.append(f"homepage: {err}")
        return result(WORKER, data, errors)

    low = (body or "").lower()
    for token, label, where in SIGNATURES:
        if where == "html" and token in low:
            data["detected"].append(label)
        elif where == "headers":
            blob = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
            if token in blob:
                data["detected"].append(label)

    for pat, label in VERSION_RES:
        m = re.search(pat, low)
        if m:
            data["versions"][label] = m.group(1).rstrip(".")

    for h in ("server", "x-powered-by", "x-aspnet-version", "via",
              "x-cache", "cf-ray", "strict-transport-security",
              "content-security-policy", "x-frame-options"):
        for k, v in headers.items():
            if k.lower() == h:
                data["headers_of_note"][k] = v[:200]

    hosts = set(re.findall(r'https?://([a-z0-9.-]+\.[a-z]{2,})', low))
    hosts.discard(domain)
    data["third_party_hosts"] = sorted(hosts)[:30]

    for path in ("/.well-known/security.txt", "/robots.txt", "/sitemap.xml"):
        b2, _, _ = http_get_text(f"https://{domain}{path}", timeout=15)
        if b2 and len(b2.strip()) > 10:
            data["public_files"][path] = b2[:1500]

    # generator meta tag
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)',
                  body or "", re.I)
    if m:
        data["detected"].append(f"generator:{m.group(1)[:80]}")

    data["detected"] = sorted(set(data["detected"]))
    return result(WORKER, data, errors)


if __name__ == "__main__":
    import json
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"),
                     indent=1)[:6000])
