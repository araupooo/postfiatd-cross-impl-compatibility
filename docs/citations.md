# Citations

Public documentation consulted for the SPECIFIED rules, with verbatim
quotes. Accessed 24 Nov 2026. Each entry notes whether the code
agrees, and where it diverges the pack follows the code.

## S-01 — The rippled reference base is 3.1.2 (21 upstream commits)

Source: https://github.com/postfiatorg/postfiatd/blob/0085a1ff885d6a446369cf73a4430f75af22be55/docs/upstream-merge-3.1.2-analysis.md
(postfiatd's own upstream-merge analysis, dated 2026-03-23, in the
pinned tree.)

> "**Current postfiatd base:** 3.0.0 (commit `46167f7c54`, tag `upgrade-checkpoint-3.0.0`)"
> "**Target:** 3.1.2 (tag `3.1.2`)"
> "**Total upstream commits:** 21"

Cross-check: agrees with the blob-SHA tree comparison — rippled 3.1.2
matches 1,595 of 1,702 common files (93.7%), the highest of any tag
(probe K-01). Rule R-01.

## S-02 — Rippled 3.1.2 was released 2026-03-12

Source: https://github.com/XRPLF/rippled/releases/tag/3.1.2
(rippled 3.1.2 release tag; commit 3ba3fcff.)

> "release: Bump version to 3.1.2"

Cross-check: the local rippled checkout at the tag commit reports
HEAD `3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c`, dated 2026-03-12
15:01:01 -0400 (probe K-01). Rule R-02.

## S-03 — The XRP Ledger consensus protocol needs over 80% collusion to confirm an invalid transaction

Source: https://xrpl.org/docs/concepts/consensus-protocol
(XRPL.org consensus-protocol documentation.)

> "As long as fewer than 20% of trusted validators are faulty, consensus can continue unimpeded; and confirming an invalid transaction would require over 80% of trusted validators to collude."

Cross-check: agrees with the rippled code — minCONSENSUS_PCT 80
(`ConsensusParms.h:79`, E01) and the 80% validator quorum
(`ValidatorList.cpp:1884`, E02). postfiatd lowers both to 67%
(rules R-03, R-04); the code itself notes mainnet should revert to
80% (`ValidatorList.cpp:1899-1900`). The same page's footnote 1
confirms the earliest-ledger fact behind rule R-20: "ledgers 1
through 32569 were lost ... Thus, ledger #32570 is the earliest
ledger available anywhere." Rule R-18.

## S-04 — The validator exclusion system excludes an account only when 67% of validators agree

Source: https://github.com/postfiatorg/postfiatd/blob/0085a1ff885d6a446369cf73a4430f75af22be55/docs/Exclusions.md
(postfiatd's validator-exclusion documentation, in the pinned tree.)

> "The Validator Exclusion List system allows validators to exclude specific accounts from participating in the network. This is a consensus-based mechanism where an account is only excluded if a sufficient percentage of validators (67% by default) agree to exclude it."

Cross-check: agrees with the code — the 67% default is the consensus
quorum (R-03), the exclusion manager is initialized on the first
validated ledger (R-26, `LedgerMaster.cpp:290`), and preflight1
rejects excluded senders and destinations (R-34,
`Transactor.cpp:190-212`). Rule R-29.
