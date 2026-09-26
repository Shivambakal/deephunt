# Blind search oracle → restricted-field exfiltration (ingested 2026-09-26)

Source: https://kymu.dev/article/BlindOracle/

## The pattern
A global search API (`GET /api/search?query=...`) used Lucene-style syntax and
indexed fields the low-priv user could NOT see (Notes, creator emails, attachment
names). Binary signal: HTTP 200 (item in results) = substring EXISTS in some
indexed field; HTTP 204 = does not exist. No rate limiting. Perfect blind oracle.

## Extraction algorithm (greedy bidirectional extension)
Substring oracles can't be attacked left-to-right (every char matches anywhere).
Instead: pick any matching char, extend LEFT by prepending until no char works
(left boundary found), then extend RIGHT by appending until dead end. Start finds
itself. Works for emails (anchor on `@`, build domain right, username left),
notes, filenames — any indexed value.

## Safe manual test (researcher's own accounts only)
1. With a low-priv test account, identify a field hidden from you in UI AND API.
2. Send ONE scoped search for a substring you hypothesize is in that field.
3. If result presence correlates with your hypothesis and not with visible fields,
   you have an oracle — stop, document, report. Do NOT run mass extraction
   loops against someone else's platform (request volume + other users' data).

## Why it matters for hunting
Any product with global search + granular field permissions is a candidate.
Test the boundary: search for values that should be invisible to your role.
