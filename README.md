# Cross-Implementation Compatibility: postfiatd vs rippled 3.1.2

How postfiatd at commit
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10) differs from
its upstream reference, rippled 3.1.2
(`3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c`, 2026-03-12), across
consensus, ledger application, and transaction processing — and where
the two implementations still agree.

## Headline findings

- **The quorum is 67%, not 80%.** postfiatd validates with 67 of 100
  agreeing validators where rippled needs 80, and the amendment
  majority is 67/100 instead of 80/100
  (`ConsensusParms.h:79`, `ValidatorList.cpp:1897-1900`,
  `SystemParameters.h:85`; scenario S-01).
- **Validator votes are new consensus state.** ttVALIDATOR_VOTE
  (1501) and ltVALIDATOR_VOTE_STATS (0x008A) exist only in postfiatd;
  a ledger containing them cannot be validated or replayed by rippled
  (`Change.cpp:552`; scenarios S-06/S-08, both incompatible).
- **Exclusion is a consensus-level account block.** postfiatd rejects
  transactions from or to excluded accounts at preflight; rippled
  applies them normally — the same transaction has different outcomes
  (`Transactor.cpp:190-212`; scenario S-07).
- **Close time is a median, not a mean.** One peer 120 seconds off
  moves the rippled mean 11 seconds and the postfiatd median 0
  seconds (`RCLConsensus.cpp:709-728`; scenario S-03). On an exact
  tie the earliest close time wins in postfiatd and the latest in
  rippled.
- **36 amendments flipped on by default.** A fresh postfiatd network
  enables them where a fresh rippled network does not
  (`features.macro`; 64 DefaultYes vs 28).
- **The matching core is preserved.** Fee escalation, load-fee
  tracking, the disputed-transaction stall test, and the amendment
  majority timestamp are identical — TxQ.cpp, TxQ.h, LoadFeeTrack.cpp,
  LoadFeeTrack.h, and FeeEscalation.md are byte-identical between the
  two checkouts (same git blob SHA).

## Contents

- 45 rules (VERIFIED 38, SPECIFIED 4, MODELLED 2, UNTESTABLE 1) —
  `configs/cross-impl-rules.json`, with grep-verified file:line
  ranges on both sides and verbatim dual excerpts in
  `fixtures/source-excerpts/` (44 excerpts, 34 postfiatd files, 27
  rippled files).
- Deterministic differential simulator (`src/cross_impl_model.py`) +
  scenario matrix — 13 scenarios, 18 runs: matched 5, diverged 9,
  degraded 2, incompatible 2.
- Claim-to-evidence index: 24 claims (VERIFIED 16, SPECIFIED 2,
  MODELLED 4, UNTESTABLE 2) — `docs/claim-index.md`.
- Findings: 12 (HIGH 3, MEDIUM 6, LOW 3) — `findings.json`.
- Risk register: 14 risks (HIGH 3, MEDIUM 8, LOW 3) —
  `docs/risk-register.md`. Gap register: 8 gaps —
  `docs/gap-register.md`.
- Operator decision memo — `docs/decision-memo.md`. Methodology
  (including the rippled pin method) — `docs/methodology.md`.
  Evidence index — `docs/evidence-index.md`.

## Pinned revisions

- postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10).
- rippled 3.1.2 `3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c`
  (2026-03-12, tag `3.1.2`). Pin method: blob-SHA tree comparison
  (3.1.2 matches 1,595 of 1,702 common files, the highest of any tag)
  plus the in-tree merge analysis naming 3.1.2 with 21 upstream
  commits; the exact commit within the 5-commit plateau is
  indistinguishable because postfiatd overwrote the version strings
  that differ between those commits — see `docs/methodology.md`.

## Reproduction

The probe re-verifies cited lines against both pinned checkouts, so
place them at their default paths first (or point the scripts
elsewhere with `PINNED_CHECKOUT` / `RIPPLED_CHECKOUT`):

```bash
git clone https://github.com/postfiatorg/postfiatd.git ~/workspace/postfiatd-pin-0085a1f
git -C ~/workspace/postfiatd-pin-0085a1f checkout 0085a1ff885d6a446369cf73a4430f75af22be55
git clone --depth 1 --branch 3.1.2 https://github.com/XRPLF/rippled.git ~/workspace/rippled-3.1.2
git -C ~/workspace/rippled-3.1.2 rev-parse HEAD  # 3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c
```

```bash
bash scripts/run_all.sh        # exit 0 only if every check passes
bash scripts/clean_reproduce.sh  # fresh-copy reproduction (run twice)
```

- Full suite: `run_all.sh` exits 0; probe 13/13 checks pass.
- `outputs/run.log` (unedited full-run log, 10 lines) SHA-256:
  `d1ecf48c2e2a9a94f8c770f73c80ec01620ec419a7b77d47e3e0a6cf7b4272df`
- Fresh-copy reproduction was run twice; both passed with
  byte-identical deterministic outputs. Fresh-clone run log:
  `outputs/fresh-clone-run.log` SHA-256:
  `d1ecf48c2e2a9a94f8c770f73c80ec01620ec419a7b77d47e3e0a6cf7b4272df`
  (identical to the shipped `run.log` digest — the first fresh copy
  reproduces the shipped log byte-for-byte). Second fresh-clone run
  log: `outputs/fresh-clone-2-run.log` SHA-256:
  `d1ecf48c2e2a9a94f8c770f73c80ec01620ec419a7b77d47e3e0a6cf7b4272df`
  (also identical).
- Digests: `cross-impl-results.json`
  `fb1d2e0b8a2e141fe6c74c9a4d586d95e4d7a2e7d003327f2f3059bba6f00879`;
  `scenario-matrix.json`
  `f59ec1789650bd9f94fab178bec94dc4291377ee509968317028d6435cf4771c`.
- Verify all digests: `bash scripts/verify_digests.sh`. The full
  unedited output of that check is captured in
  `outputs/verify-digests.log` (SHA-256:
  `38541af5b1e177b72a93960ab72298cbbdb2d0c13bd107e0856950c9c0e68cbc`)
  and its digest is recorded in `run-manifest.json`.

The logs are independently resolvable as raw files:

https://raw.githubusercontent.com/araupooo/postfiatd-cross-impl-compatibility/main/outputs/run.log
https://raw.githubusercontent.com/araupooo/postfiatd-cross-impl-compatibility/main/outputs/fresh-clone-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-cross-impl-compatibility/main/outputs/fresh-clone-2-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-cross-impl-compatibility/main/outputs/probe-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-cross-impl-compatibility/main/outputs/verify-digests.log

## CI

Continuous integration runs the same suite on every push; see the
workflow runs page:

https://github.com/araupooo/postfiatd-cross-impl-compatibility/actions/workflows/verify.yml
