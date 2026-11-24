# Evidence index

Where every piece of evidence in this pack lives, and how to check it.

## Pinned sources

- postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10) — 34 source files cited.
- rippled 3.1.2 `3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c` (2026-03-12, tag `3.1.2`) — 27 source files
  cited with reference excerpts, plus 7 files verified absent by grep.

## Rules and scenarios

- `configs/cross-impl-rules.json` — 45 rules (VERIFIED 38, SPECIFIED 4,
  MODELLED 2, UNTESTABLE 1), each with a postfiatd file:line source
  and a rippled reference range (or a verified-absent grep), an
  excerpt id, or an external documentation quote.
- `configs/scenarios.json` — 13 scenarios, 18 runs, with the pinned
  constants (67% vs 80% quorum and amendment majority, 60%
  absolute-minimum quorum, 1,000 untrusted manifest cap, 100-address
  exclusion cap, 512-element JSON array cap, 64 JSON depth cap,
  918,744 VL maximum, 2,000 malformed-data charge, earliest sequence
  1 vs 32,570, SHAMap leaf depth 64, validator-vote type 1501).

## Excerpts

- `fixtures/source-excerpts/E01.txt` … `E44.txt` — verbatim excerpts
  carrying both sides (postfiatd chunk + rippled 3.1.2 chunk, or a
  verified-absent note). Each file is headed with repos, commits,
  files, lines, source SHA-256, git blob SHA, and size. See
  `docs/excerpts.md` for the per-excerpt digest table.
- `fixtures/source-hashes.json` — SHA-256, git blob SHA, line count,
  and size for every excerpt and every cited source file (34 postfiatd
  files, 27 rippled files).
- `fixtures/excerpts-manifest.json` — the extraction manifest
  (postfiatd ranges + rippled references + absent patterns).

## Simulator and probe

- `src/cross_impl_model.py` — deterministic differential simulator
  (reads `configs/scenarios.json`, writes
  `outputs/derived/cross-impl-results.json` and
  `outputs/derived/scenario-matrix.json`).
- `scripts/probe.py` — 13/13 independent re-verification checks
  (both checkout HEADs, rule anchors on both sides, scenario
  arithmetic, threshold and constants tables, token lines on both
  sides, counts, determinism, excerpt integrity, absence greps,
  matching-core blob SHAs, pin evidence).
- `scripts/run_all.sh` — full suite (extract, validate, simulate,
  probe, manifest, digests). `scripts/clean_reproduce.sh` — fresh-copy
  reproduction, run twice. `scripts/compare_reproduce.py` — 53/53
  comparison checks per cycle.

## Postfiatd source files cited (34)

- `include/xrpl/basics/MathUtilities.h`
- `include/xrpl/protocol/Protocol.h`
- `include/xrpl/protocol/STParsedJSON.h`
- `include/xrpl/protocol/STValidation.h`
- `include/xrpl/protocol/SystemParameters.h`
- `include/xrpl/protocol/detail/features.macro`
- `include/xrpl/protocol/detail/ledger_entries.macro`
- `include/xrpl/protocol/detail/sfields.macro`
- `include/xrpl/protocol/detail/transactions.macro`
- `src/libxrpl/ledger/View.cpp`
- `src/libxrpl/protocol/STObject.cpp`
- `src/libxrpl/protocol/STValidation.cpp`
- `src/libxrpl/protocol/Serializer.cpp`
- `src/xrpld/app/consensus/RCLConsensus.cpp`
- `src/xrpld/app/consensus/RCLValidations.cpp`
- `src/xrpld/app/ledger/ConsensusTransSetSF.cpp`
- `src/xrpld/app/ledger/Ledger.cpp`
- `src/xrpld/app/ledger/detail/LedgerMaster.cpp`
- `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.cpp`
- `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.h`
- `src/xrpld/app/main/Application.cpp`
- `src/xrpld/app/misc/Manifest.h`
- `src/xrpld/app/misc/SHAMapStoreImp.cpp`
- `src/xrpld/app/misc/ValidatorList.h`
- `src/xrpld/app/misc/detail/ValidatorList.cpp`
- `src/xrpld/app/paths/detail/Steps.h`
- `src/xrpld/app/tx/detail/Change.cpp`
- `src/xrpld/app/tx/detail/InvariantCheck.cpp`
- `src/xrpld/app/tx/detail/InvariantCheck.h`
- `src/xrpld/app/tx/detail/Transactor.cpp`
- `src/xrpld/consensus/Consensus.h`
- `src/xrpld/consensus/ConsensusParms.h`
- `src/xrpld/consensus/DisputedTx.h`
- `src/xrpld/shamap/detail/SHAMapNodeID.cpp`

## Rippled 3.1.2 source files cited (27)

- `include/xrpl/protocol/STParsedJSON.h`
- `include/xrpl/protocol/STValidation.h`
- `include/xrpl/protocol/SystemParameters.h`
- `include/xrpl/protocol/detail/features.macro`
- `include/xrpl/protocol/detail/ledger_entries.macro`
- `src/libxrpl/ledger/View.cpp`
- `src/libxrpl/protocol/STObject.cpp`
- `src/libxrpl/protocol/STValidation.cpp`
- `src/libxrpl/protocol/Serializer.cpp`
- `src/xrpld/app/consensus/RCLConsensus.cpp`
- `src/xrpld/app/consensus/RCLValidations.cpp`
- `src/xrpld/app/ledger/ConsensusTransSetSF.cpp`
- `src/xrpld/app/ledger/Ledger.cpp`
- `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.cpp`
- `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.h`
- `src/xrpld/app/misc/Manifest.h`
- `src/xrpld/app/misc/SHAMapStoreImp.cpp`
- `src/xrpld/app/misc/ValidatorList.h`
- `src/xrpld/app/misc/detail/ValidatorList.cpp`
- `src/xrpld/app/tx/detail/Change.cpp`
- `src/xrpld/app/tx/detail/InvariantCheck.cpp`
- `src/xrpld/app/tx/detail/InvariantCheck.h`
- `src/xrpld/app/tx/detail/Transactor.cpp`
- `src/xrpld/consensus/Consensus.h`
- `src/xrpld/consensus/ConsensusParms.h`
- `src/xrpld/consensus/DisputedTx.h`
- `src/xrpld/shamap/detail/SHAMapNodeID.cpp`

## Findings, claims, risks, gaps

- `findings.json` — 12 findings (HIGH 3, MEDIUM 6, LOW 3).
- `docs/claim-index.md` — 24 claims (VERIFIED 16, SPECIFIED 2,
  MODELLED 4, UNTESTABLE 2).
- `docs/risk-register.md` — 14 risks (HIGH 3, MEDIUM 8, LOW 3).
- `docs/gap-register.md` — 8 gaps.
- `docs/decision-memo.md` — operator decision memo.
- `docs/methodology.md` — pin method, diff inventory, simulator.
- `docs/citations.md` — the 4 SPECIFIED rules with verbatim quotes.
- `docs/scenario-matrix.md` — the 18-run matrix, quorum threshold
  table, and constants comparison table.
