# Click2Shell — WordPress Pre-Auth RCE Chain
Source: https://pwn.ai/blog/click2shell
Date saved: 2026-09-26

## Summary
- pwn.ai's second WordPress Core pre-auth RCE chain (after XSS2Shell): a crafted theme-preview URL forces an admin's browser to auto-install an attacker-chosen theme from the WordPress.org catalog — no clicks by the victim beyond visiting a link.
- Root cause: one route value interpreted twice — the WordPress.org Themes API canonicalizes it to a plain slug (returns genuine theme), while `wp-admin/js/theme.js` drops the raw value into a jQuery selector, where injected quotes/combinators walk the selector into the real "Install" control. Attacker reuses the victim admin's nonce + capabilities.
- Chained with a pre-activation flaw: WordPress loads an installed-but-inactive theme's PHP during Customizer previews, and the `mobile-repair-zone` 2.5.4 theme exposed a nonce-less, capability-less AJAX handler that fetched/unpacked an arbitrary plugin ZIP and executed its PHP.
- Fixed in WordPress 7.1.1 (changeset 63664): selector constrained to `div.theme` cards + slug escaped before entering selector syntax. Affects all versions before 7.1.1; max bounty paid; CVE pending at write time.

## Agent relevance
- WordPress is squarely in Shivam's lane (fastest-first-rupee gig lane): add "one value, two interpretations" as a first-class bug pattern — any input consumed by two parsers (server API + client JS) with different canonicalization is a prime injection candidate.
- Detection checklist for WP targets: fingerprint version (< 7.1.1 = Click2Shell-affected), audit theme-preview/customizer routes, look for AJAX handlers missing `check_ajax_referer`/capability checks, test whether inactive themes' PHP loads in preview contexts.
- Generalize: jQuery/CSS selector injection is an under-tested sink — add selector-context injection probes wherever URL params flow into `$()` selectors.
- Only test on owned/authorized WP installs; this chain is one-click RCE — never probe on live third-party sites.
