# Methodology

## Pinned sources

Two commits, both verified with `git rev-parse HEAD` on local
checkouts; no line number comes from a web fetch.

- postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10),
  worktree `~/workspace/postfiatd-pin-0085a1f`.
- rippled 3.1.2 `3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c`
  (2026-03-12, tag `3.1.2`), expected at
  `~/workspace/rippled-3.1.2` (override with `RIPPLED_CHECKOUT`).

The 44 verbatim excerpts in `fixtures/source-excerpts/` carry both
sides of every comparison (or a verified-absent note when the rippled
side has no such code), extracted by
`scripts/extract_excerpts.py` from those checkouts.
`fixtures/source-hashes.json` records the SHA-256, git blob SHA, and
size of every excerpt and every cited source file (34 postfiatd files,
27 rippled files).

## How the rippled reference revision was pinned

postfiatd is a fork of rippled with no fork history visible in the
pinned tree (the pinned checkout is a single commit). The reference
was determined by evidence, in three steps:

1. **Blob-SHA tree comparison.** The pinned postfiatd tree (1,783
   files) was compared against rippled release tags by git blob SHA.
   Rippled 3.1.2 matches 1,595 of 1,702 common files (93.7%), the
   highest of any tag (3.1.1/3.1.0: 1,587; 3.1.3: 1,506; 3.2.0+:
   about 39, after an upstream restructure). A 5-commit plateau
   (0e3600a1, ecc58740, 3ba3fcff, 10731f90, a92483e0) all score 1,595.
2. **Discriminating evidence bounds the base to 3.1.2 or earlier.**
   postfiatd's `features.macro` lacks the `Security3_1_3` placeholder
   amendment added 2026-04-01, and postfiatd's `MPToken_test.cpp`
   blob matches the pre-2026-04-06 version, not the 2026-04-06 one.
3. **In-tree confirmation.** `docs/upstream-merge-3.1.2-analysis.md`
   (dated 2026-03-23) states: "Current postfiatd base: 3.0.0
   (commit 46167f7c54, tag upgrade-checkpoint-3.0.0). Target: 3.1.2
   (tag 3.1.2). Total upstream commits: 21" — all 21 included.

The exact commit within the 2026-03-11–12 plateau cannot be
distinguished, because the plateau commits differ only in
`BuildInfo.cpp` version strings, which postfiatd overwrote (version
"1.0.9"). The pack therefore pins the revision as rippled 3.1.2
(commit 3ba3fcff, the tag commit), and marks fork-point-dependent
claims MODELLED or UNTESTABLE as appropriate (rules R-01, R-02, R-30;
gaps G-05; risk K-13). No exact fork point is asserted beyond what
the evidence supports.

## How the divergence inventory was built

1. The full file diff between the two pinned trees: 1,702 common
   files, 107 differ, 81 postfiatd-only, 29 rippled-only. Per-file
   unified diffs for the 52 key files were read in full (3,347 diff
   lines).
2. Every rule carries a file:line range on the postfiatd side and a
   file:line range (or a verified-absent grep) on the rippled side.
   Where the two sides are identical, the pack says so and records
   the match as a rule (R-09, R-16) or a constants-table MATCH row.
3. Absence findings were checked with `grep` over the rippled tree
   (probe I-01): no ttVALIDATOR_VOTE, no ltVALIDATOR_VOTE_STATS, no
   sfExclusionAdd, no PF_AccountExclusion, no checkedAdd, no
   ValidatorVoteTracker.
4. Matching core was verified by git blob SHA (probe J-01): TxQ.cpp,
   TxQ.h, LoadFeeTrack.cpp, LoadFeeTrack.h, and FeeEscalation.md are
   byte-identical between the two checkouts.

## How the differential simulator works

`src/cross_impl_model.py` reads `configs/scenarios.json` and applies
both implementations' rules side by side with integer arithmetic,
exactly as the C++ does: quorum is
max(ceil(UNL * pct / 100), ceil(UNL * 60 / 100)); the close-time
offset is the lower weighted median (postfiatd) or the arithmetic
mean rounded to nearest (rippled); the tie-break walks the vote bins
highest-first (postfiatd) or lowest-first (rippled) and keeps the
last bin reaching the running threshold; the genesis account follows
the network-ID rule in `Ledger.cpp`; SHAMap depths clamp (postfiatd)
or index out of range (rippled); strand sums use checked add
(postfiatd) or wrap (rippled); JSON arrays cap at 512 (postfiatd) or
have no cap (rippled); unlisted manifests cap at 1,000 (postfiatd)
or are unbounded (rippled). The probe (`scripts/probe.py`) re-derives
every run independently from the same scenario params.

## What the simulator does not do

No live node was run and no real network test was performed. The
simulator models the code's rules on stated inputs; it cannot observe
a running network, measure timings, or settle whether a mixed
postfiatd/rippled network reaches consensus (gap G-01, claim C-23).
Simulated outcomes are never presented as measured node behavior.

## Reproduction

```bash
bash scripts/run_all.sh         # exit 0 only if every check passes
bash scripts/clean_reproduce.sh # fresh-copy reproduction (run twice)
```

`run_all.sh` extracts excerpts (when both checkouts are available),
validates the model config, runs the simulator, runs the probe,
writes the run summary and manifest, and captures the full unedited
`verify_digests.sh` output into `outputs/verify-digests.log`.
`clean_reproduce.sh` copies the pack to a throwaway directory, drops
all generated outputs, re-runs from scratch twice, and compares the
fresh outputs with the shipped ones byte-for-byte
(`scripts/compare_reproduce.py`, 53/53 checks in both cycles).
