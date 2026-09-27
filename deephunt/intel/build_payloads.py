#!/usr/bin/env python3
"""Vendor PayloadsAllTheThings Intruder files into deephunt/data/payloads/.

Source: https://github.com/swisskyrepo/PayloadsAllTheThings (MIT), pinned
shallow clone at /tmp/patt. Re-run: git -C /tmp/patt pull && python3 this file.

Each class file: deduplicated payloads, one per line, no blanks/comments.
Hand-curated classes (jwt, ssrf, ssti, authz-403, graphql, hpp) are marked
in the MANIFEST as hand-curated from survey findings, not vendored.
"""
import os
import sys

PATT = "/tmp/patt"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "data", "payloads")

# class -> [(patt_dir, [intruder filenames or None for all])]
VENDOR = {
    "xss": [("XSS Injection", None)],
    "sqli": [("SQL Injection", [
        "SQLi_Polyglots.txt", "Generic_TimeBased.txt", "Generic_ErrorBased.txt",
        "Auth_Bypass.txt", "Auth_Bypass2.txt", "Generic_Fuzz.txt"])],
    "cmdi": [("Command Injection", None)],
    "traversal": [("Directory Traversal", [
        "directory_traversal.txt", "deep_traversal.txt",
        "traversals-8-deep-exotic-encoding.txt"])],
    "xxe": [("XXE Injection", None)],
    "openredirect": [("Open Redirect", [
        "Open-Redirect-payloads.txt", "openredirects.txt"])],
}

# intruder dir spelling varies per PATT topic
INTRUDER_NAMES = ["Intruder", "Intruders"]
# dotdotpwn-style mega files are noise for targeted hunting
MAX_PER_FILE = 600


def _read_clean(path):
    out = []
    with open(path, errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for klass, sources in VENDOR.items():
        seen, payloads = set(), []
        src_files = []
        for d, files in sources:
            idir = None
            for iname in INTRUDER_NAMES:
                cand = os.path.join(PATT, d, iname)
                if os.path.isdir(cand):
                    idir = cand
                    break
            if not idir:
                print(f"WARN: missing intruder dir for {d}", file=sys.stderr)
                continue
            names = files or sorted(os.listdir(idir))
            for n in names:
                p = os.path.join(idir, n)
                if not os.path.isfile(p):
                    continue
                src_files.append(f"{d}/{os.path.basename(idir)}/{n}")
                for line in _read_clean(p)[:MAX_PER_FILE]:
                    if line not in seen:
                        seen.add(line)
                        payloads.append(line)
        dest = os.path.join(OUT, f"{klass}.txt")
        with open(dest, "w") as f:
            f.write("\n".join(payloads) + "\n")
        manifest.append(f"{klass}.txt: {len(payloads)} payloads "
                        f"<- {len(src_files)} files [vendored:PATT]")
        print(f"{klass}: {len(payloads)} payloads")
    with open(os.path.join(OUT, "MANIFEST.txt"), "w") as f:
        f.write("DEEPHUNT payload corpus — build " +
                os.popen("date -u +%FT%TZ").read())
        f.write("Source: PayloadsAllTheThings (MIT) "
                "https://github.com/swisskyrepo/PayloadsAllTheThings\n")
        f.write("\n".join(manifest) + "\n")
    print("wrote", os.path.join(OUT, "MANIFEST.txt"))


if __name__ == "__main__":
    main()
