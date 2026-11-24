#!/usr/bin/env python3
"""extract_excerpts.py — pull verbatim pinned-source excerpts into fixtures/.

Usage:
    python3 scripts/extract_excerpts.py [PACK_ROOT] [MANIFEST]
    PINNED_CHECKOUT=<path>   (default ~/workspace/postfiatd-pin-0085a1f)
    RIPPLED_CHECKOUT=<path>  (default ~/workspace/rippled-3.1.2)

The manifest (default fixtures/excerpts-manifest.json) is a JSON object:
    {"pinned_commit": "<40-hex>", "repo": "postfiatd",
     "rippled_commit": "<40-hex>", "rippled_repo": "rippled",
     "rippled_tag": "3.1.2",
     "excerpts": [{"id": "<file-stem>", "file": "<repo-relative path>",
                   "start_line": <int>, "end_line": <int>,
                   "anchor": "<text expected inside the range, optional>",
                   "reference": {"repo": "rippled", "file": "<path>",
                                 "start_line": <int>, "end_line": <int>,
                                 "anchor": "<text, optional>"},
                   "reference_absent": {"repo": "rippled", "file": "<path>",
                                        "pattern": "<grep pattern that must have 0 hits>"},
                   "blob_sha": "<git blob SHA, optional>",
                   "blob_size": <bytes, optional>}, ...]}

Each excerpt carries both sides: the postfiatd chunk and the rippled
reference chunk (or a verified-absent note when the rippled side has
no such code: the script greps the rippled file for the pattern and
requires 0 hits). The script verifies `git rev-parse HEAD` in both
checkouts equals the pinned commits and refuses to run otherwise. For
each entry it checks the line ranges are in bounds, the anchors are
inside the ranges, and the manifest blob SHA/size (when given) match
the checkout files. It writes fixtures/source-excerpts/<id>.txt with
headers giving repos, commits, files, lines, plus blob SHAs/sizes, and
writes fixtures/source-hashes.json with SHA-256 digests and git blob
SHAs per excerpt and per source file (separate postfiatd / rippled
sections).

Line numbers are never taken from a web fetch: they come from the
local checkouts of the pinned commits.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
MANIFEST = Path(sys.argv[2]) if len(sys.argv) > 2 else PACK_ROOT / "fixtures" / "excerpts-manifest.json"
PIN = Path(os.environ.get("PINNED_CHECKOUT", "~/workspace/postfiatd-pin-0085a1f")).expanduser()
RIP = Path(os.environ.get("RIPPLED_CHECKOUT", "~/workspace/rippled-3.1.2")).expanduser()
COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
RIPPLED_COMMIT = "3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c"
RIPPLED_TAG = "3.1.2"
REPO = "postfiatd"
RIPPLED_REPO = "rippled"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(checkout, relpath):
    out = subprocess.run(["git", "-C", str(checkout), "hash-object", "--", relpath],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def grep_hits(checkout, pattern, relpath):
    proc = subprocess.run(["grep", "-rn", pattern, str(checkout / relpath)],
                          capture_output=True, text=True)
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def check_head(checkout, expected, label):
    if not checkout.is_dir():
        fail(f"{label} checkout not found: {checkout}")
    try:
        head = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError as exc:
        fail(f"git rev-parse HEAD failed in {checkout}: {exc.stderr.strip()}")
    if head != expected:
        fail(f"{label} checkout HEAD {head} != {expected} ({checkout})")
    print(f"{label} checkout verified: {head}")


def fail(msg):
    print(f"extract_excerpts: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def extract_side(checkout, relpath, first, last, anchor, label, ex_id):
    src = checkout / relpath
    if not src.is_file():
        fail(f"excerpt {ex_id}: file not in {label} checkout: {relpath}")
    lines = src.read_text().splitlines()
    if first < 1 or last < first or last > len(lines):
        fail(f"excerpt {ex_id}: range {first}-{last} out of bounds "
             f"for {label} {relpath} ({len(lines)} lines)")
    chunk = lines[first - 1:last]
    if anchor and not any(anchor in ln for ln in chunk):
        fail(f"excerpt {ex_id}: anchor {anchor!r} not in "
             f"{label} {relpath}:{first}-{last}")
    size = src.stat().st_size
    blob = git_blob_sha(checkout, relpath)
    return chunk, {"sha256": sha256_file(src), "git_blob_sha": blob,
                   "lines": len(lines), "size_bytes": size}


def main():
    check_head(PIN, COMMIT, "postfiatd")
    check_head(RIP, RIPPLED_COMMIT, "rippled")

    if not MANIFEST.is_file():
        fail(f"excerpts manifest not found: {MANIFEST}")
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("pinned_commit") and manifest["pinned_commit"] != COMMIT:
        fail(f"manifest pinned_commit {manifest['pinned_commit']} != {COMMIT}")
    if manifest.get("rippled_commit") and manifest["rippled_commit"] != RIPPLED_COMMIT:
        fail(f"manifest rippled_commit {manifest['rippled_commit']} != {RIPPLED_COMMIT}")
    entries = manifest.get("excerpts")
    if not isinstance(entries, list) or not entries:
        fail(f"manifest {MANIFEST} has no non-empty \"excerpts\" list")

    outdir = PACK_ROOT / "fixtures" / "source-excerpts"
    outdir.mkdir(parents=True, exist_ok=True)
    hashes = {"pinned_commit": COMMIT, "repo": REPO,
              "rippled_commit": RIPPLED_COMMIT, "rippled_repo": RIPPLED_REPO,
              "rippled_tag": RIPPLED_TAG,
              "files": {"postfiatd": {}, "rippled": {}}, "excerpts": {}}

    for entry in entries:
        ex_id = entry.get("id")
        relpath = entry.get("file")
        first = entry.get("start_line")
        last = entry.get("end_line")
        if not ex_id or not ID_RE.match(str(ex_id)):
            fail(f"bad excerpt id: {ex_id!r} (must match {ID_RE.pattern})")
        if not relpath or not isinstance(first, int) or not isinstance(last, int):
            fail(f"excerpt {ex_id}: need file, start_line, end_line")
        chunk, frec = extract_side(PIN, relpath, first, last,
                                   entry.get("anchor"), "postfiatd", ex_id)
        if entry.get("blob_sha") and entry["blob_sha"] != frec["git_blob_sha"]:
            fail(f"excerpt {ex_id}: manifest blob_sha {entry['blob_sha']} "
                 f"!= checkout blob {frec['git_blob_sha']} for {relpath}")
        if entry.get("blob_size") is not None and entry["blob_size"] != frec["size_bytes"]:
            fail(f"excerpt {ex_id}: manifest blob_size {entry['blob_size']} "
                 f"!= checkout size {frec['size_bytes']} for {relpath}")
        hashes["files"]["postfiatd"].setdefault(relpath, frec)

        ref = entry.get("reference")
        ref_absent = entry.get("reference_absent")
        if ref and ref_absent:
            fail(f"excerpt {ex_id}: reference and reference_absent are exclusive")
        if not ref and not ref_absent:
            fail(f"excerpt {ex_id}: need reference or reference_absent")
        ref_rec = None
        ref_text = ""
        if ref:
            rchunk, rrec = extract_side(
                RIP, ref["file"], ref["start_line"], ref["end_line"],
                ref.get("anchor"), "rippled", ex_id)
            hashes["files"]["rippled"].setdefault(ref["file"], rrec)
            ref_rec = {"file": ref["file"],
                       "lines": f"{ref['start_line']}-{ref['end_line']}",
                       "blob_sha": rrec["git_blob_sha"],
                       "blob_size": rrec["size_bytes"]}
            ref_text = (
                f"# --- rippled 3.1.2 ({RIPPLED_COMMIT}) ---\n"
                f"# File: {ref['file']}, lines {ref['start_line']}-{ref['end_line']}.\n"
                f"# Source file SHA-256: {rrec['sha256']}\n"
                f"# Source file git blob SHA: {rrec['git_blob_sha']}\n"
                f"# Source file size: {rrec['size_bytes']} bytes\n\n"
                f"# --- {ref['file']} lines {ref['start_line']}-{ref['end_line']} ---\n"
                + "\n".join(rchunk) + "\n")
        else:
            rfile = ref_absent["file"]
            pattern = ref_absent["pattern"]
            hits = grep_hits(RIP, pattern, rfile)
            if hits:
                fail(f"excerpt {ex_id}: pattern {pattern!r} found in rippled "
                     f"{rfile} ({len(hits)} hits); reference is not absent")
            ref_rec = {"file": rfile, "absent_pattern": pattern, "hits": 0}
            ref_text = (
                f"# --- rippled 3.1.2 ({RIPPLED_COMMIT}) ---\n"
                f"# No corresponding code in rippled 3.1.2: grep for "
                f"{pattern!r} in {rfile} returns 0 hits.\n")

        text = (f"# Source excerpt {ex_id} — {REPO} {COMMIT} vs {RIPPLED_REPO} {RIPPLED_TAG} ({RIPPLED_COMMIT}).\n"
                f"# File: {relpath}, lines {first}-{last}.\n"
                f"# Line numbers verified with grep -n on local checkouts "
                f"of the pinned commits.\n"
                f"# Source file SHA-256: {frec['sha256']}\n"
                f"# Source file git blob SHA: {frec['git_blob_sha']}\n"
                f"# Source file size: {frec['size_bytes']} bytes\n\n"
                f"# --- {relpath} lines {first}-{last} ---\n"
                + "\n".join(chunk) + "\n\n"
                + ref_text)
        (outdir / f"{ex_id}.txt").write_text(text)
        hashes["excerpts"][ex_id] = {
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "file": relpath,
            "lines": f"{first}-{last}",
            "blob_sha": frec["git_blob_sha"],
            "blob_size": frec["size_bytes"],
            "reference": ref_rec,
        }
        print(f"wrote fixtures/source-excerpts/{ex_id}.txt")

    with open(PACK_ROOT / "fixtures" / "source-hashes.json", "w") as fh:
        json.dump(hashes, fh, indent=1)
        fh.write("\n")
    print("wrote fixtures/source-hashes.json")


if __name__ == "__main__":
    main()
